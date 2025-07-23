from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
import httpx

from backend import models, schemas
from backend.database import get_db

router = APIRouter()

async def send_whatsapp_message_background(
    phone_number_id: str, 
    access_token: str, 
    contact_phone: str, 
    message: str
):
    """
    Sends a single WhatsApp message using the specific user's credentials.
    """
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": contact_phone,
        "type": "text",
        "text": {"body": message},
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"WhatsApp message sent to {contact_phone}")
        else:
            print(f"Failed to send to {contact_phone}: {response.text}")

@router.post("/send-campaign")
async def send_whatsapp_campaign(
    campaign_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Sends a WhatsApp campaign using the credentials of the user who created it.
    """
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    # Get the user associated with the campaign
    user = campaign.user
    if not user or not user.whatsapp_account:
        raise HTTPException(status_code=403, detail="User has not connected a WhatsApp account.")
        
    # Retrieve the user's specific WhatsApp credentials
    waba_creds = user.whatsapp_account
    access_token = waba_creds.access_token # Should be decrypted here
    phone_number_id = waba_creds.phone_number_id

    contacts = db.query(models.Contact).filter(models.Contact.phone != None).all()
    for contact in contacts:
        personalized_message = campaign.body.format(name=contact.name)
        background_tasks.add_task(
            send_whatsapp_message_background,
            phone_number_id,
            access_token,
            contact.phone,
            personalized_message
        )

    return {"status": f"WhatsApp campaign '{campaign.name}' started for user {user.email}."}