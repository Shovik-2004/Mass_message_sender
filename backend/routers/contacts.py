from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import pandas as pd

from backend import models, schemas
from backend.database import get_db

router = APIRouter()

@router.post("/import-excel", status_code=201)
async def import_contacts_from_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Imports contacts from an Excel file and associates them with the logged-in user.
    """
    # Get the current user (placeholder logic for now)
    current_user = db.query(models.User).first()
    if not current_user:
        raise HTTPException(status_code=403, detail="Not authenticated. Please log in first.")

    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload an Excel file (.xlsx, .xls).")

    try:
        df = pd.read_excel(file.file)
        if 'name' not in df.columns or 'email' not in df.columns:
            raise HTTPException(status_code=400, detail="Excel file must contain 'name' and 'email' columns.")

        for _, row in df.iterrows():
            # Check if contact email already exists FOR THIS USER
            contact_exists = db.query(models.Contact).filter(
                models.Contact.email == row['email'],
                models.Contact.user_id == current_user.id
            ).first()

            if not contact_exists:
                new_contact = models.Contact(
                    name=row['name'],
                    email=row['email'],
                    phone=str(row.get('phone', '')),
                    user_id=current_user.id  # Assign the contact to the current user
                )
                db.add(new_contact)
        
        db.commit()
    except Exception as e:
        # Provide a more detailed error message during development
        raise HTTPException(status_code=500, detail=f"Failed to process Excel file: {str(e)}")

    return {"message": "Contacts imported successfully."}


@router.post("/groups", response_model=schemas.ContactGroup)
def create_contact_group(group: schemas.ContactGroupCreate, db: Session = Depends(get_db)):
    """Creates a contact group for the logged-in user."""
    current_user = db.query(models.User).first()
    if not current_user:
        raise HTTPException(status_code=403, detail="Not authenticated.")

    db_group = models.ContactGroup(name=group.name, user_id=current_user.id)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group


@router.get("/groups", response_model=list[schemas.ContactGroup])
def get_all_groups(db: Session = Depends(get_db)):
    """Gets all contact groups for the logged-in user."""
    current_user = db.query(models.User).first()
    if not current_user:
        return []
    
    return db.query(models.ContactGroup).filter(models.ContactGroup.user_id == current_user.id).all()
