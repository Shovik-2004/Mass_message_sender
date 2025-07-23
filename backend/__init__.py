

# backend/__init__.py

# Correctly import init_db from database.py, not models.py
from .database import init_db
if __name__ == "__main__":
    init_db()
    print("✅ Database tables created.")
