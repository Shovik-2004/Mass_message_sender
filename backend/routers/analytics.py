from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models
from datetime import datetime, UTC

router = APIRouter()

@router.get("/track/{campaign_id}/{contact_id}")
def track_email_open(campaign_id: int, contact_id: int, db: Session = Depends(get_db)):
    """
    This endpoint is called by the tracking pixel in an email.
    It records that the email was opened.
    """
    record = db.query(models.EmailAnalytics).filter_by(
        campaign_id=campaign_id, 
        contact_id=contact_id
    ).first()

    if record and record.status == "sent":
        record.status = "opened"
        record.opened_at = datetime.now(UTC)
        db.commit()

    # Return a 1x1 transparent GIF pixel
    pixel_data = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00'
        b'\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00'
        b'\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    )
    return Response(content=pixel_data, media_type="image/gif")


@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receives status updates from the Meta WhatsApp API.
    This requires a public URL and configuration in the Meta App Dashboard.
    """
    data = await request.json()
    
    # Verify the webhook signature (important for security, omitted for brevity)
    
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            if value.get("messaging_product") == "whatsapp" and "statuses" in value:
                for status_update in value["statuses"]:
                    message_id = status_update.get("id")
                    status = status_update.get("status")
                    
                    record = db.query(models.WhatsAppAnalytics).filter_by(message_id=message_id).first()
                    if record:
                        record.status = status
                        record.status_timestamp = datetime.fromtimestamp(int(status_update.get("timestamp")), tz=UTC)
                        db.commit()

    return {"status": "ok"}
