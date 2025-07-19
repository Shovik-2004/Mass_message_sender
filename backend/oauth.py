# /backend/oauth.py

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv
import os
import pathlib
from sqlalchemy.orm import Session
from uuid import uuid4
from . import models, database
from backend.models import init_db
 # make sure these are defined


load_dotenv()

router = APIRouter()

# Base directory for relative paths
BASE_DIR = pathlib.Path(__file__).resolve().parent

# Load client secrets file path from environment or fallback
CLIENT_SECRETS_FILE = os.getenv(
    "CLIENT_SECRET_FILE", 
    str(BASE_DIR / "client_secret_1049923121871-cdhh4030763qphdqepqtgu28vjrefaod.apps.googleusercontent.com.json")
)

# OAuth 2.0 scopes required for sending email and accessing profile info
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
]

# Callback URL set in Google Cloud Console
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback")

# Temporary in-memory session store
# TODO: Replace with Redis or DB in production
session_store = {}

@router.get("/auth/login", response_model=None)
def login(db: Session = database.get_db()):
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )

        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )

        # Save the state and flow details in DB
        state_id = str(uuid4())
        db_state = models.OAuthState(
            state=state_id,
            code_verifier=flow.code_verifier,  # optional
            redirect_uri=REDIRECT_URI
        )
        db.add(db_state)
        db.commit()

        # Replace state in URL with our DB-tracked UUID
        return RedirectResponse(f"{authorization_url}&state={state_id}")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"OAuth init failed: {str(e)}"})

@router.get("/auth/callback")
async def oauth2callback(request: Request, db: Session = database.get_db()):
    state = request.query_params.get("state")
    code = request.query_params.get("code")

    db_state = db.query(models.OAuthState).filter_by(state=state).first()

    if not db_state:
        return JSONResponse(status_code=400, content={"error": "Invalid or missing state"})

    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=db_state.redirect_uri
        )

        flow.fetch_token(code=code)
        credentials = flow.credentials

        user_data = {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": ",".join(credentials.scopes)
        }

        # Save credentials to DB
        token = models.UserToken(
            state=state,
            **user_data
        )
        db.add(token)
        db.commit()

        return JSONResponse(content={"message": "OAuth successful", "state": state})

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Token fetch failed: {str(e)}"})
