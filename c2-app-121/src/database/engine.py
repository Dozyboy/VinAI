from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from src.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.log_level == "DEBUG",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_sqlite() -> None:
    inspector = inspect(engine)
    if "encounters" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("encounters")}
    if "shift_id" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE encounters ADD COLUMN shift_id INTEGER"))

    if "doctors" not in inspector.get_table_names():
        return
    doctor_columns = {col["name"] for col in inspector.get_columns("doctors")}
    if "user_id" not in doctor_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE doctors ADD COLUMN user_id INTEGER REFERENCES users(id)"))


def init_db() -> None:
    from src.database.base import Base
    from src.models.database import User, Doctor
    from src.core.security import hash_password

    Base.metadata.create_all(bind=engine)
    _migrate_sqlite()

    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            print("No users found in database. Auto-seeding default doctor accounts...")
            users = [
                User(email="bs.nguyen@hospital.vn", full_name="BS. Nguyen Van A",
                     hashed_password=hash_password("doctor123"), role="doctor", is_active=True),
                User(email="bs.tran@hospital.vn", full_name="BS. Tran Thi B",
                     hashed_password=hash_password("doctor123"), role="doctor", is_active=True),
            ]
            db.add_all(users)
            db.flush()

            doctors = [
                Doctor(full_name="BS. Nguyen Van A", specialization="Noi tong hop",
                       email="bs.nguyen@hospital.vn", phone="0901234567", user_id=users[0].id),
                Doctor(full_name="BS. Tran Thi B", specialization="San phu khoa",
                       email="bs.tran@hospital.vn", phone="0912345678", user_id=users[1].id),
            ]
            db.add_all(doctors)
            db.commit()
            print("Auto-seeding complete! Default doctors can now log in.")
    except Exception as e:
        print(f"Error during auto-seeding: {e}")
        db.rollback()
    finally:
        db.close()
