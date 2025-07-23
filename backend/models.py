from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    ForeignKey,
    DateTime,
    Boolean
)
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime, UTC

# --- User and Auth Models (remain the same) ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    google_oauth_token = relationship("GoogleOAuthToken", uselist=False, back_populates="user")
    whatsapp_account = relationship("WhatsAppAccount", uselist=False, back_populates="user")

class GoogleOAuthToken(Base):
    __tablename__ = "google_oauth_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    access_token = Column(String, nullable=False)
    refresh_token = Column(String)
    token_uri = Column(String)
    client_id = Column(String)
    client_secret = Column(String)
    scopes = Column(Text)
    user = relationship("User", back_populates="google_oauth_token")

class WhatsAppAccount(Base):
    __tablename__ = "whatsapp_accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    whatsapp_business_account_id = Column(String, nullable=False, unique=True)
    phone_number_id = Column(String, nullable=False, unique=True)
    access_token = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    user = relationship("User", back_populates="whatsapp_account")

# --- Contact and Campaign Models (remain the same) ---
class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, nullable=True)
    status = Column(String, default="Active")
    group_id = Column(Integer, ForeignKey("contact_groups.id"))
    group = relationship("ContactGroup", back_populates="contacts")

class ContactGroup(Base):
    __tablename__ = "contact_groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    contacts = relationship("Contact", back_populates="group")

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    subject = Column(String)
    body = Column(Text)
    type = Column(String)
    status = Column(String, default="Draft")
    scheduled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")

# --- NEW: Analytics Models ---

class EmailAnalytics(Base):
    """Stores the status of each individual email sent in a campaign."""
    __tablename__ = "email_analytics"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    status = Column(String, default="sent")  # e.g., sent, opened, failed
    opened_at = Column(DateTime, nullable=True)
    
    campaign = relationship("Campaign")
    contact = relationship("Contact")

class WhatsAppAnalytics(Base):
    """Stores the status of each individual WhatsApp message sent."""
    __tablename__ = "whatsapp_analytics"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    message_id = Column(String, unique=True, nullable=False) # From Meta API
    status = Column(String, default="sent") # e.g., sent, delivered, read, failed
    status_timestamp = Column(DateTime, default=lambda: datetime.now(UTC))

    campaign = relationship("Campaign")
    contact = relationship("Contact")
