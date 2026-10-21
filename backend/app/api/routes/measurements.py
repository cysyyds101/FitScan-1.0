"""Measurement API routes.

- POST /api/measurements          Create measurement session
- GET  /api/measurements/{id}    Get measurement result
- GET  /api/measurements         List recent sessions
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.api.schemas import MeasurementSession, MeasurementCreate
from app.services import storage

router = APIRouter()


@router.post("/measurements", response_model=MeasurementSession, status_code=201)
def create_measurement(data: MeasurementCreate):
    """Create a new measurement session with optional coarse data from frontend."""
    session = storage.create_measurement_session(
        raw_data=data.raw_data,
        coarse_data=data.coarse_data,
    )
    return session


@router.get("/measurements/{session_id}", response_model=MeasurementSession)
def get_measurement(session_id: str):
    """Get measurement session by ID. Includes precise data once AI server finishes."""
    session = storage.get_measurement(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return session


@router.get("/measurements", response_model=list[MeasurementSession])
def list_measurements(limit: int = 20):
    """List recent measurement sessions."""
    return storage.list_measurements(limit=limit)
