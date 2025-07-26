from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend import models, schemas
from backend.database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.Campaign)
def create_campaign(campaign: schemas.CampaignCreate, db: Session = Depends(get_db)):
    """
    Creates a new campaign and correctly associates it with the logged-in user.
    """
    # In a real app, you would get the user from a session token (e.g., JWT).
    # For this demonstration, we'll get the first user in the database.
    current_user = db.query(models.User).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="No user found. Please log in first.")

    # Create the campaign object from the request data
    db_campaign = models.Campaign(**campaign.dict())
    
    # FIX: Assign the current user's ID to the campaign before saving
    db_campaign.user_id = current_user.id
    
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

@router.get("/", response_model=list[schemas.Campaign])
def get_all_campaigns(db: Session = Depends(get_db)):
    return db.query(models.Campaign).all()
