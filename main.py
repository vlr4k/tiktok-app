import os
import secrets
import hashlib
import base64
import requests
from urllib.parse import quote
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from database import Base, engine, get_db
from models import User, TikTokAccount, Video
from auth import hash_password, verify_password, create_token, get_current_user
from pydantic import BaseModel

load_dotenv()
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

code_verifier = secrets.token_urlsafe(64)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b"=").decode()

class LoginData(BaseModel):
    login: str
    password: str

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
<!DOCTYPE html>
<html>
<head>
    <title>TZ Post</title>
    <meta charset="utf-8">
    <style>
        *{box-sizing:border-box;margin:0;padding:0}
        body{background:#111113;font-family:Arial,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh}
        .card{background:#141416;border:0.5px solid #222;border-radius:12px;padding:32px;width:360px}
        .logo{font-size:22px;font-weight:700;color:#fff;text-align:center;margin-bottom:24px}
        .field{margin-bottom:14px}
        label{font-size:11px;color:#666;display:block;margin-bottom:5px;text-transform:uppercase;letter-spacing:0.5px}
        input{width:100%;background:#0e0e10;border:0.5px solid #2a2a2e;border-radius:8px;padding:10px 12px;font-size:13px;color:#ddd;outline:none;font-family:Arial}
        input:focus{border-color:#7c7cff}
        .btn{width:100%;background:#7c7cff;color:#fff;border:none;border-radius:8px;padding:11px;font-size:13px;font-weight:600;cursor:pointer;margin-top:4px}
        .btn:hover{opacity:0.9}
        .error{color:#ff4455;font-size:12px;margin-top:10px;text-align:center;display:none}
        .divider{display:flex;align-items:center;gap:10px;margin:16px 0}
        .div-line{flex:1;height:0.5px;background:#1e1e22}
        .div-text{font-size:11px;color:#333}
        .tg-btn{width:100%;background:#0e0e10;color:#5aabff;border:0.5px solid #1e3a5a;border-radius:8px;padding:10px;font-size:12px;cursor:pointer}
        .tg-btn:hover{border-color:#5aabff}
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">TZ Post</div>
        <div class="field">
            <label>Login</label>
            <input type="text" id="login" placeholder="your_login">
        </div>
        <div class="field">
            <label>Password</label>
            <input type="password" id="password" placeholder="••••••••" onkeydown="if(event.key==='Enter')doLogin()">
        </div>
        <button class="btn" onclick="doLogin()">Sign in</button>
        <div class="error" id="error">Wrong login or password</div>
        <div class="divider"><div class="div-line"></div><div class="div-text">or</div><div class="div-line"></div></div>
        <button class="tg-btn" onclick="window.location='/subscribe'">Get subscription in Telegram →</button>
    </div>
    <script>
        if(localStorage.getItem('token')) window.location='/dashboard';
        async function doLogin(){
            const login=document.getElementById('login').value;
            const password=document.getElementById('password').value;
            const res=await fetch('/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({login,password})});
            const data=await res.json();
            if(res.ok){
                localStorage.setItem('token', data.access_token);
                window.location='/dashboard';
            } else {
                document.getElementById('error').style.display='block';
            }
        }
    </script>
</body>
</html>
"""

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>TZ Post — Dashboard</title>
    <meta charset="utf-8">
    <style>
        body{background:#111113;color:#ccc;font-family:Arial,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;flex-direction:column;gap:16px}
        h1{color:#fff;font-size:20px}
        .btn{background:#7c7cff;color:#fff;border:none;border-radius:8px;padding:10px 20px;cursor:pointer;font-size:13px}
        .info{background:#141416;border:0.5px solid #222;border-radius:8px;padding:16px;font-size:13px;min-width:300px;line-height:2}
    </style>
</head>
<body>
    <h1>TZ Post Dashboard</h1>
    <div class="info" id="user-info">Loading...</div>
    <button class="btn" onclick="logout()">Logout</button>
    <script>
        const token=localStorage.getItem('token');
        if(!token) window.location='/';
        fetch('/me',{headers:{'Authorization':'Bearer '+token}})
            .then(r=>r.json())
            .then(d=>{
                if(d.detail){localStorage.removeItem('token');window.location='/';}
                document.getElementById('user-info').innerHTML='Login: '+d.login+'<br>Plan: '+d.plan;
            });
        function logout(){localStorage.removeItem('token');window.location='/';}
    </script>
</body>
</html>
"""

@app.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.login == data.login).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Wrong login or password")
    token = create_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/tiktok-auth")
def tiktok_auth():
    state = secrets.token_hex(16)
    url = (
        f"https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={CLIENT_KEY}"
        f"&response_type=code"
        f"&scope={quote('user.info.basic,video.upload,video.publish', safe='')}"
        f"&redirect_uri={quote(REDIRECT_URI, safe='')}"
        f"&state={state}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )
    return RedirectResponse(url)

@app.get("/auth/callback")
def callback(code: str, state: str):
    response = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": CLIENT_KEY,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier,
        }
    )
    return response.json()

@app.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "login": current_user.login, "plan": current_user.plan}

@app.post("/admin/create-user")
def create_user(data: LoginData, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.login == data.login).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    user = User(login=data.login, password=hash_password(data.password))
    db.add(user)
    db.commit()
    return {"message": f"User {data.login} created"}

@app.get("/admin/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "login": u.login, "plan": u.plan, "created_at": str(u.created_at)} for u in users]

@app.get("/privacy")
def privacy():
    return {"privacy_policy": "This app collects TikTok OAuth tokens to upload videos on behalf of the user. We do not store or share your data."}

@app.get("/terms")
def terms():
    return {"terms": "By using this app you agree to TikTok's Terms of Service. This app is used solely for uploading videos to TikTok."}

@app.get("/terms/{filename}")
def tiktok_verify(filename: str):
    if filename == "tiktoknR7acLM2jnWywhCPXhOcnPNqWyMjCVkk.txt":
        return PlainTextResponse("tiktok-developers-site-verification=nR7acLM2jnWywhCPXhOcnPNqWyMjCVkk")
    return PlainTextResponse("Not Found", status_code=404)

@app.get("/privacy/{filename}")
def tiktok_verify_privacy(filename: str):
    if filename == "tiktokdddvj5kJujUzUnaDntntoQfkFRSYyPMG.txt":
        return PlainTextResponse("tiktok-developers-site-verification=dddvj5kJujUzUnaDntntoQfkFRSYyPMG")
    return PlainTextResponse("Not Found", status_code=404)

@app.get("/{filename}")
def tiktok_verify_root(filename: str):
    if filename == "tiktokT1AhM3o4jpObfsp9fVqEQj0OTJFQ47AV.txt":
        return PlainTextResponse("tiktok-developers-site-verification=T1AhM3o4jpObfsp9fVqEQj0OTJFQ47AV")
    return PlainTextResponse("Not Found", status_code=404)