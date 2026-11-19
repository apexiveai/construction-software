
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine

router = APIRouter(tags=["System Health"])


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "ApexiveAI Construction OS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready")
def readiness_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from error

    return {
        "status": "ready",
        "application": "ApexiveAI Construction OS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/version")
def version():
    return {
        "name": "ApexiveAI Construction OS",
        "version": "1.0.0",
        "api": "v1",
    }
