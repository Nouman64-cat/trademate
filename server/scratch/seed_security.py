from database.database import engine
from models.security_settings import SecuritySettings
from sqlmodel import Session, select

def seed_security_settings():
    with Session(engine) as session:
        existing = session.exec(select(SecuritySettings)).first()
        if not existing:
            session.add(SecuritySettings())
            session.commit()
            print("✓ Seeded security_settings")
        else:
            print("! security_settings already exists")

if __name__ == "__main__":
    seed_security_settings()
