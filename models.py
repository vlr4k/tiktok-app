from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    login = Column(String, unique=True)
    password = Column(String)
    plan = Column(String, default="free")
    created_at = Column(DateTime, default=datetime.utcnow)
    tiktok_accounts = relationship("TikTokAccount", back_populates="user")
    videos = relationship("Video", back_populates="user")

class TikTokAccount(Base):
    __tablename__ = "tiktok_accounts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    open_id = Column(String, unique=True)
    handle = Column(String)
    access_token = Column(String)
    refresh_token = Column(String)
    followers = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    user = relationship("User", back_populates="tiktok_accounts")

class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    account_id = Column(Integer, ForeignKey("tiktok_accounts.id"))
    title = Column(String)
    description = Column(String)
    status = Column(String, default="draft")
    scheduled_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    views = Column(Integer, default=0)
    is_mass = Column(Boolean, default=False)
    user = relationship("User", back_populates="videos")