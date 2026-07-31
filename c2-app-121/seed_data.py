"""Seed data — hệ thống mới, chỉ có 2 tài khoản bác sĩ."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy.orm import Session
from src.database.engine import SessionLocal
from src.core.security import hash_password
from src.models.database import User, Doctor


def seed(db: Session) -> None:
    # ── 2 bác sĩ ──
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
    db.flush()

    db.commit()
    print("Seed data inserted successfully!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Xóa DB rồi tạo lại từ đầu")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.reset:
            from src.database.base import Base
            from src.database.engine import engine
            print("Dropping all tables...")
            Base.metadata.drop_all(bind=engine)
            print("Creating all tables...")
            Base.metadata.create_all(bind=engine)
            print("Re-creating missing columns...")
            from src.database.engine import _migrate_sqlite
            _migrate_sqlite()
        seed(db)
    finally:
        db.close()
