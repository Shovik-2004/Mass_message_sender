from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import httpx
import os
import pathlib

from backend import models
from backend.database import get_db

router = APIRouter()

# --- Google OAuth2 Configuration (remains the same) ---
BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
CLIENT_SECRETS_FILE = os.path.join(BACKEND_DIR, 'client_secret_1049923121871-cdhh4030763qphdqepqtgu28vjrefaod.apps.googleusercontent.com.json')
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.send", "openid"
]
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")

# ... (all Google OAuth endpoints remain the same) ...
@router.get("/login")
def login_google():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        raise HTTPException(status_code=500, detail=f"Google Client Secrets file not found at: {CLIENT_SECRETS_FILE}")
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=GOOGLE_SCOPES, redirect_uri=GOOGLE_REDIRECT_URI)
    authorization_url, state = flow.authorization_url(access_type="offline", prompt="consent", include_granted_scopes="true")
    return RedirectResponse(authorization_url)

@router.get("/callback")
def auth_callback(request: Request, db: Session = Depends(get_db)):
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=GOOGLE_SCOPES, redirect_uri=GOOGLE_REDIRECT_URI)
    flow.fetch_token(authorization_response=str(request.url))
    credentials = flow.credentials
    user_info_service = build('oauth2', 'v2', credentials=credentials)
    user_info = user_info_service.userinfo().get().execute()
    user_email = user_info.get('email')
    if not user_email:
        raise HTTPException(status_code=400, detail="Email not found in Google token.")
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        user = models.User(email=user_email)
        db.add(user)
        db.commit()
        db.refresh(user)
    token_record = db.query(models.GoogleOAuthToken).filter(models.GoogleOAuthToken.user_id == user.id).first()
    if not token_record:
        token_record = models.GoogleOAuthToken(user_id=user.id)
    token_record.access_token = credentials.token
    token_record.refresh_token = credentials.refresh_token
    token_record.token_uri = credentials.token_uri
    token_record.client_id = credentials.client_id
    token_record.client_secret = credentials.client_secret
    token_record.scopes = ",".join(credentials.scopes)
    db.add(token_record)
    db.commit()
    return JSONResponse(content={"message": "Google authentication successful", "user": user_email})


# --- WhatsApp Business Account Connection Flow ---
META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")
WHATSAPP_REDIRECT_URI = os.getenv("WHATSAPP_REDIRECT_URI", "http://localhost:8000/auth/whatsapp/callback")

async def get_whatsapp_details(access_token: str):
    """
    Helper function to query the Meta Graph API for WABA and Phone Number IDs.
    """
    async with httpx.AsyncClient() as client:
        # Step 1: Get the user's associated WhatsApp Business Accounts (WABAs)
        waba_url = "https://graph.facebook.com/v18.0/me/businesses"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # This part is complex and often handled by a BSP. We'll simplify.
        # A user can have multiple businesses. We'll try to find one with a WhatsApp account.
        # This is a highly simplified logic for demonstration.
        
        # A more direct (but requires more permissions) way is to get accounts:
        accounts_url = f"https://graph.facebook.com/v18.0/me/accounts?fields=whatsapp_business_account"
        response = await client.get(accounts_url, headers=headers)
        if response.status_code != 200:
            return None, None
        
        accounts_data = response.json().get("data", [])
        waba_id = None
        for account in accounts_data:
            if "whatsapp_business_account" in account:
                waba_id = account["whatsapp_business_account"]["id"]
                break
        
        if not waba_id:
            return None, None

        # Step 2: Get the phone numbers associated with that WABA
        phone_numbers_url = f"https://graph.facebook.com/v18.0/{waba_id}/phone_numbers"
        response = await client.get(phone_numbers_url, headers=headers)
        if response.status_code != 200:
            return waba_id, None

        phone_data = response.json().get("data", [])
        if not phone_data:
            return waba_id, None
            
        # For simplicity, we take the first available phone number ID
        phone_number_id = phone_data[0]["id"]
        
        return waba_id, phone_number_id

@router.get("/whatsapp/login")
def login_whatsapp():
    # ... (login_whatsapp remains the same) ...
    if not META_APP_ID:
        raise HTTPException(status_code=500, detail="META_APP_ID is not configured.")
    dialog_url = (f"https://www.facebook.com/v18.0/dialog/oauth?client_id={META_APP_ID}&redirect_uri={WHATSAPP_REDIRECT_URI}"
                  f"&scope=whatsapp_business_management,whatsapp_business_messaging,business_management"
                  f"&response_type=code&state=YOUR_SECURE_STATE_TOKEN")
    return RedirectResponse(dialog_url)


@router.get("/whatsapp/callback")
async def whatsapp_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handles the callback from Meta and fetches real WABA credentials.
    """
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not found.")

    # Exchange code for access token
    token_url = f"https://graph.facebook.com/v18.0/oauth/access_token"
    params = {"client_id": META_APP_ID, "client_secret": META_APP_SECRET, "redirect_uri": WHATSAPP_REDIRECT_URI, "code": code}
    async with httpx.AsyncClient() as client:
        response = await client.get(token_url, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to get access token: {response.text}")
        access_token = response.json().get("access_token")

    # Fetch the actual WABA ID and Phone Number ID
    waba_id, phone_id = await get_whatsapp_details(access_token)
    if not waba_id or not phone_id:
        raise HTTPException(status_code=404, detail="Could not find a valid WhatsApp Business Account and Phone Number for this user.")

    # Get the current logged-in user (assuming Google login happened first)
    current_user = db.query(models.User).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="No user found. Please log in with Google first.")

    # Save the real credentials to the database
    existing_waba = db.query(models.WhatsAppAccount).filter_by(user_id=current_user.id).first()
    if existing_waba:
        existing_waba.access_token = access_token
        existing_waba.whatsapp_business_account_id = waba_id
        existing_waba.phone_number_id = phone_id
    else:
        new_waba = models.WhatsAppAccount(
            user_id=current_user.id,
            whatsapp_business_account_id=waba_id,
            phone_number_id=phone_id,
            access_token=access_token,
        )
        db.add(new_waba)
    
    db.commit()

    return JSONResponse(content={"message": "WhatsApp Account connected successfully!", "waba_id": waba_id, "phone_id": phone_id})
