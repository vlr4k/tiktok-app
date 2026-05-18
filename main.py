import os
import secrets
import hashlib
import base64
import requests
from urllib.parse import quote
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, PlainTextResponse, HTMLResponse
from dotenv import load_dotenv
from database import Base, engine
from models import User, TikTokAccount, Video

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI()

CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

code_verifier = secrets.token_urlsafe(64)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b"=").decode()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head><title>TikTok App</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>TikTok Video Uploader</h1>
            <p>Upload videos to TikTok using our app</p>
            <a href="/login" style="background-color: #000000; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-size: 18px;">Login with TikTok</a>
        </body>
    </html>
    """
@app.get("/login")
def login():
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
    token_data = response.json()
    return token_data  

@app.get("/privacy")
def privacy():
    return {"privacy_policy": "This app collects TikTok OAuth tokens to upload videos on behalf of the user. We do not store or share your data."}

@app.get("/terms")
def terms():
    return {"terms": "By using this app you agree to TikTok's Terms of Service. This app is used solely for uploading videos to TikTok."}

from fastapi import Request
from fastapi.responses import PlainTextResponse

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

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import hash_password, verify_password, create_token, get_current_user
from pydantic import BaseModel

class LoginData(BaseModel):
    login: str
    password: str

@app.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.login == data.login).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Wrong login or password")
    token = create_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/admin/create-user")
def create_user(data: LoginData, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.login == data.login).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    user = User(login=data.login, password=hash_password(data.password))
    db.add(user)
    db.commit()
    return {"message": f"User {data.login} created"}

@app.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "login": current_user.login, "plan": current_user.plan}

@app.get("/admin/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "login": u.login, "plan": u.plan, "created_at": str(u.created_at)} for u in users]