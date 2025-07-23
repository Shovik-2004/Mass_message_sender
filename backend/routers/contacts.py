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
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a .xlsx file.")

    try:
        df = pd.read_excel(file.file)
        # Basic validation
        if 'name' not in df.columns or 'email' not in df.columns:
            raise HTTPException(status_code=400, detail="Excel file must contain 'name' and 'email' columns.")

        for _, row in df.iterrows():
            contact = db.query(models.Contact).filter(models.Contact.email == row['email']).first()
            if not contact:
                new_contact = models.Contact(
                    name=row['name'],
                    email=row['email'],
                    phone=str(row.get('phone', '')) # Safely get phone
                )
                db.add(new_contact)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process Excel file: {e}")

    return {"message": "Contacts imported successfully."}

@router.post("/groups", response_model=schemas.ContactGroup)
def create_contact_group(group: schemas.ContactGroupCreate, db: Session = Depends(get_db)):
    db_group = models.ContactGroup(name=group.name)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@router.get("/groups", response_model=list[schemas.ContactGroup])
def get_all_groups(db: Session = Depends(get_db)):
    return db.query(models.ContactGroup).all()