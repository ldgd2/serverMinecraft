from database.connection import SessionLocal
from database.models.user import User
from app.services.auth_service import get_password_hash

def seed_users():
    db = SessionLocal()
    if not db.query(User).first():
        print("Seeding Admin User...")
        
        # Admin credentials (visible for configuration)
        username = "admin"
        password = "admin"  # <-- Change this password!
        
        # Hash the password
        hashed_password = get_password_hash(password)
        
        user = User(username=username, hashed_password=hashed_password)
        db.add(user)
        db.commit()
        print(f"Admin user seeded: {username} / {password}")
    else:
        print("Users already exist.")
    db.close()

if __name__ == "__main__":
    seed_users()
