from sqlalchemy import Column, String, create_engine, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from .database import Base

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()

class OAuthState(Base):
    __tablename__ = "oauth_state"
    state = Column(String, primary_key=True, index=True)
    redirect_uri = Column(String)
    code_verifier = Column(String, nullable=True)

class UserToken(Base):
    __tablename__ = "user_token"
    state = Column(String, primary_key=True)
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_uri = Column(String)
    client_id = Column(String)
    client_secret = Column(String)

class OAuthToken(Base):
    __tablename__ = "oauth_tokens"
    email = Column(String, primary_key=True, index=True)
    access_token = Column(String)
    refresh_token = Column(String)
    token_uri = Column(String)
    client_id = Column(String)
    client_secret = Column(String)
    scopes = Column(String)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
