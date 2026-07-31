from fastapi import APIRouter

from src.api.admin.router import router as admin_router
from src.api.auth.router import router as auth_router
from src.api.clinical.router import router as clinical_router
from src.api.dashboard.router import router as dashboard_router
from src.api.doctors.router import router as doctors_router
from src.api.encounters.router import router as encounters_router
from src.api.health.router import router as health_router
from src.api.patients.router import router as patients_router
from src.api.shifts.router import router as shifts_router
from src.api.users.router import router as users_router

router = APIRouter(prefix="/api/v1")

router.include_router(health_router)
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(clinical_router)
router.include_router(admin_router)
router.include_router(doctors_router)
router.include_router(patients_router)
router.include_router(shifts_router)
router.include_router(encounters_router)
router.include_router(dashboard_router)
