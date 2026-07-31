from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.auth.dependencies import get_current_user
from src.api.dashboard.schemas import DashboardSummary, DailyViewResponse, DoctorWorkload, MonthlyTrend, TopDiagnoses
from src.api.dashboard.service import get_daily_view, get_dashboard_summary, get_doctor_workload, get_monthly_trend, get_top_diagnoses
from src.api.deps import get_db
from src.models.database import User, Doctor

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _resolve_doctor_id(user: User, db: Session) -> int | None:
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    return doctor.id if doctor else None


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Tổng quan: bác sĩ, BN, lượt khám, hôm nay."""
    doctor_id = _resolve_doctor_id(user, db)
    return get_dashboard_summary(db, doctor_id=doctor_id)


@router.get("/doctor-workload", response_model=DoctorWorkload)
async def doctor_workload(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Xếp hạng bác sĩ theo số lượng khám."""
    items = get_doctor_workload(db)
    return {"items": items}


@router.get("/top-diagnoses", response_model=TopDiagnoses)
async def top_diagnoses(
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Top chẩn đoán phổ biến."""
    doctor_id = _resolve_doctor_id(user, db)
    items = get_top_diagnoses(db, limit=limit, doctor_id=doctor_id)
    return {"items": items}


@router.get("/monthly-trend", response_model=MonthlyTrend)
async def monthly_trend(
    months: int = Query(6, ge=1, le=24),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Xu hướng lượt khám theo tháng."""
    doctor_id = _resolve_doctor_id(user, db)
    items = get_monthly_trend(db, months=months, doctor_id=doctor_id)
    return {"items": items}


@router.get("/daily-view", response_model=DailyViewResponse)
async def daily_view(
    date: str = Query(..., description="YYYY-MM-DD"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Xem ca làm việc + bệnh nhân theo ngày và bác sĩ."""
    doctor_id = _resolve_doctor_id(user, db)
    return get_daily_view(db, date, doctor_id=doctor_id)
