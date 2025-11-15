"""
Database initialization script.
Creates all tables if they don't exist.
"""
import time
import sys
from main import app, db

def init_database(retries=5, delay=2):
    """Initialize database with retry logic."""
    for attempt in range(retries):
        try:
            with app.app_context():
                # Try to create tables
                db.create_all()
                print("✅ Database tables created successfully!")
                return True
        except Exception as e:
            print(f"⚠️  Attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                print(f"Waiting {delay} seconds before retry...")
                time.sleep(delay)
            else:
                print("❌ Failed to initialize database after all retries")
                return False
    
    return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)