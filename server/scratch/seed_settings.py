from database.database import engine
from models.system_settings import SystemSettings
from sqlmodel import Session, select

def seed_settings():
    with Session(engine) as session:
        existing = session.exec(select(SystemSettings)).first()
        if not existing:
            session.add(SystemSettings())
            session.commit()
            print("✓ Seeded system_settings")
        else:
            print("! system_settings already exists")

if __name__ == "__main__":
    seed_settings()
