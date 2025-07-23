# backend/schemas.py

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
import datetime

# --- Schemas for Contacts ---
class ContactBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class Contact(ContactBase):
    id: int
    status: str
    group_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

# --- Schemas for Contact Groups (CORRECTED ORDER) ---

# 1. Define the Base schema first.
class ContactGroupBase(BaseModel):
    name: str

# 2. Define the Create schema next.
class ContactGroupCreate(ContactGroupBase):
    pass

# 3. Now, you can define the main schema that uses the others.
class ContactGroup(ContactGroupBase):
    id: int
    contacts: List[Contact] = []
    model_config = ConfigDict(from_attributes=True)


# --- Schemas for Campaigns ---
class CampaignBase(BaseModel):
    name: str
    subject: Optional[str] = None
    body: str
    type: str  # 'email' or 'whatsapp'

class CampaignCreate(CampaignBase):
    pass

class Campaign(CampaignBase):
    id: int
    status: str
    scheduled_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)