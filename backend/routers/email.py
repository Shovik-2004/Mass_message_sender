from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import os

from backend import models
from backend.database import get_db, SessionLocal
from backend.main import scheduler
import datetime

router = APIRouter()

# Get the base URL for the tracking pixel
# In production, this should be your actual domain
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def send_email_task(campaign_id: int, contact_id: int):
    """
    The actual task of sending a single email and creating an analytics record.
    This runs in a separate thread/process, so it needs its own DB session.
    """
    db = SessionLocal()
    try:
        campaign = db.query(models.Campaign).filter_by(id=campaign_id).first()
        contact = db.query(models.Contact).filter_by(id=contact_id).first()
        user = campaign.user

        if not all([campaign, contact, user, user.google_oauth_token]):
            return

        # --- Create the initial analytics record ---
        analytics_record = models.EmailAnalytics(
            campaign_id=campaign.id,
            contact_id=contact.id,
            status="sent"
        )
        db.add(analytics_record)
        db.commit()

        # --- Inject the tracking pixel ---
        pixel_url = f"{API_BASE_URL}/analytics/track/{campaign.id}/{contact.id}"
        email_body_html = f"""
        <html>
            <body>
                <p>{campaign.body.format(name=contact.name)}</p>
                <img src="{pixel_url}" width="1" height="1" alt="" />
            </body>
        </html>
        """

        # --- Send the email ---
        token_info = user.google_oauth_token
        creds = Credentials(
            token=token_info.access_token, refresh_token=token_info.refresh_token,
            token_uri=token_info.token_uri, client_id=token_info.client_id,
            client_secret=token_info.client_secret, scopes=token_info.scopes.split(',')
        )
        
        service = build('gmail', 'v1', credentials=creds)
        message = MIMEMultipart()
        message['to'] = contact.email
        message['from'] = user.email
        message['subject'] = campaign.subject
        message.attach(MIMEText(email_body_html, 'html'))
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        (service.users().messages().send(userId='me', body={'raw': raw_message}).execute())
        print(f"Email sent to {contact.email} for campaign {campaign.id}")

    except Exception as e:
        print(f"Failed to send email to {contact.email}: {e}")
        # Optionally update analytics record to "failed"
        if 'analytics_record' in locals():
            analytics_record.status = "failed"
            db.commit()
    finally:
        db.close()


def send_email_campaign_now(campaign_id: int):
    """Sends the entire email campaign immediately."""
    db = SessionLocal()
    try:
        campaign = db.query(models.Campaign).filter_by(id=campaign_id).first()
        if not campaign: return
        
        contacts = db.query(models.Contact).all() # Simplified
        for contact in contacts:
            # Schedule each email sending as a separate task to avoid long-running jobs
            scheduler.add_job(send_email_task, args=[campaign.id, contact.id])
    finally:
        db.close()

@router.post("/send-campaign")
def schedule_or_send_email_campaign(campaign_id: int, db: Session = Depends(get_db)):
    # ... (This endpoint logic remains largely the same) ...
    campaign = db.query(models.Campaign).filter_by(id=campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.scheduled_at and campaign.scheduled_at > datetime.datetime.now(datetime.UTC):
        job_id = f"email_campaign_{campaign.id}"
        scheduler.add_job(
            send_email_campaign_now, 'date', run_date=campaign.scheduled_at,
            args=[campaign.id], id=job_id, replace_existing=True
        )
        campaign.status = "Scheduled"
        db.commit()
        return {"status": f"Email campaign '{campaign.name}' scheduled for {campaign.scheduled_at}"}
    else:
        send_email_campaign_now(campaign.id)
        campaign.status = "Sending"
        db.commit()
        return {"status": f"Email campaign '{campaign.name}' started."}
