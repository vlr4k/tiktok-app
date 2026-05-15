import os
import secrets
import hashlib
import base64
import requests
from urllib.parse import quote  # добавили это
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

code_verifier = secrets.token_urlsafe(64)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b"=").decode()

@app.get("/")
def home():
    return {"message": "TikTok App работает!"}

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