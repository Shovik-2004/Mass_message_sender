from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from backend.database import init_db, DATABASE_URL
# Add the new analytics router
from backend.routers import email, whatsapp, contacts, campaigns, auth, analytics

# Initialize the database and create tables (this will now create the analytics tables)
init_db()

# ... (scheduler and app setup remains the same) ...
jobstores = {'default': SQLAlchemyJobStore(url=DATABASE_URL)}
scheduler = AsyncIOScheduler(jobstores=jobstores)
app = FastAPI(title="Synapse Send API", version="1.0.0")

@app.on_event("startup")
def start_scheduler():
    scheduler.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(contacts.router, prefix="/contacts", tags=["Contacts"])
app.include_router(email.router, prefix="/email", tags=["Email"])
app.include_router(whatsapp.router, prefix="/whatsapp", tags=["WhatsApp"])
app.include_router(campaigns.router, prefix="/campaigns", tags=["Campaigns"])
# Include the new analytics router
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])


@app.get("/", tags=["Root"])
def root():
    return {"message": "Synapse Send Backend is running"}
