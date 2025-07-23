from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from .database import DATABASE_URL

# Define the jobstore using your database URL
jobstores = {
    'default': SQLAlchemyJobStore(url=DATABASE_URL)
}

# Create the single scheduler instance that the rest of the app will use
scheduler = AsyncIOScheduler(jobstores=jobstores)
