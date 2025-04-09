from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    auditor,
    ca,
    telecaller,
    login,
    user,
    password,
    leads,
    notes,
    credit_report,
    notifications,
)

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(user.router, prefix="/users", tags=["User"])
api_router.include_router(ca.router, prefix="/ca", tags=["CA"])
api_router.include_router(auditor.router, prefix="/auditor", tags=["Auditor"])
api_router.include_router(password.router, tags=["password"])
api_router.include_router(leads.router, prefix="/leads", tags=["Leads"])
api_router.include_router(notes.router, tags=["note"])
api_router.include_router(telecaller.router, tags=["telecaller"])
api_router.include_router(credit_report.router, prefix="/credit-report", tags=["Credit Report"])
api_router.include_router(notifications.router, tags=["notifications"])