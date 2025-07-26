from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    ForeignKey,
    DateTime,
    Boolean,
    UniqueConstraint  # Import UniqueConstraint
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

# ... (GoogleOAuthToken and WhatsAppAccount models remain the same) ...
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


# --- UPDATED Contact and Campaign Models ---

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True) # No longer globally unique
    phone = Column(String, nullable=True) # No longer globally unique
    status = Column(String, default="Active")
    
    # FIX: Link contacts to a user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User")

    group_id = Column(Integer, ForeignKey("contact_groups.id"), nullable=True)
    group = relationship("ContactGroup", back_populates="contacts")

    # A contact's email must be unique FOR THAT USER
    __table_args__ = (UniqueConstraint('user_id', 'email', name='_user_email_uc'),)


class ContactGroup(Base):
    __tablename__ = "contact_groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    
    # FIX: Link contact groups to a user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User")

    contacts = relationship("Contact", back_populates="group")
    
    # A group's name must be unique FOR THAT USER
    __table_args__ = (UniqueConstraint('user_id', 'name', name='_user_name_uc'),)


class Campaign(Base):
    # ... (Campaign model remains the same) ...
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

# ... (Analytics models remain the same) ...
class EmailAnalytics(Base):
    __tablename__ = "email_analytics"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    status = Column(String, default="sent")
    opened_at = Column(DateTime, nullable=True)
    campaign = relationship("Campaign")
    contact = relationship("Contact")

class WhatsAppAnalytics(Base):
    __tablename__ = "whatsapp_analytics"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    message_id = Column(String, unique=True, nullable=False)
    status = Column(String, default="sent")
    status_timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
    campaign = relationship("Campaign")
    contact = relationship("Contact")
