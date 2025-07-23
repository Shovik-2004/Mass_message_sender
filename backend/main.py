from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the scheduler instance from the new file
from .scheduler import scheduler
from .database import init_db
from .routers import email, whatsapp, contacts, campaigns, auth, analytics

# Initialize the database
init_db()

app = FastAPI(
    title="Synapse Send API",
    description="Backend for the Mass WhatsApp & Email Marketing Software.",
    version="1.0.0"
)

# Start the scheduler when the app starts
@app.on_event("startup")
def start_scheduler():
    if not scheduler.running:
        scheduler.start()

# Shutdown the scheduler when the app stops
@app.on_event("shutdown")
def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()

# --- Middleware and Routers (remain the same) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(contacts.router, prefix="/contacts", tags=["Contacts"])
app.include_router(email.router, prefix="/email", tags=["Email"])
app.include_router(whatsapp.router, prefix="/whatsapp", tags=["WhatsApp"])
app.include_router(campaigns.router, prefix="/campaigns", tags=["Campaigns"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])


@app.get("/", tags=["Root"])
def root():
    return {"message": "Synapse Send Backend is running"}
