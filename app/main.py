"""
main.py
--------
FastAPI application entry point. Defines all API routes (full CRUD for
patients + health records, plus a standalone prediction endpoint) and
serves the frontend (templates/index.html, static/ assets).

Run with:
    uvicorn app.main:app --reload
"""

import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError

from . import models, schemas, crud
from .database import engine, get_db
from .ml_model import predict_risk, get_model

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Create database tables on startup if they don't already exist.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Health Risk Prediction API",
    description="CRUD + ML-based health risk prediction using Glucose, "
                 "Haemoglobin, and Cholesterol readings.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@app.on_event("startup")
def warm_up_model():
    """Ensure the ML model is loaded (and trained, if missing) at startup
    rather than on the first request, so the first user doesn't wait."""
    get_model()


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

@app.get("/", tags=["Frontend"])
def serve_frontend(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


# ---------------------------------------------------------------------------
# Patient CRUD endpoints
# ---------------------------------------------------------------------------

@app.post(
    "/api/patients",
    response_model=schemas.PatientOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Patients"],
)
def create_patient(patient_in: schemas.PatientCreate, db: Session = Depends(get_db)):
    """Creates a new patient along with their first health reading, and
    returns the prediction made for that reading."""
    try:
        patient = crud.create_patient(db, patient_in)
        return patient
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not create patient.")


@app.get("/api/patients", response_model=list[schemas.PatientOut], tags=["Patients"])
def list_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_patients(db, skip=skip, limit=limit)


@app.get("/api/patients/{patient_id}", response_model=schemas.PatientOut, tags=["Patients"])
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return patient


@app.put("/api/patients/{patient_id}", response_model=schemas.PatientOut, tags=["Patients"])
def update_patient(
    patient_id: int, patient_update: schemas.PatientUpdate, db: Session = Depends(get_db)
):
    patient = crud.update_patient(db, patient_id, patient_update)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return patient


@app.delete("/api/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Patients"])
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_patient(db, patient_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return None


# ---------------------------------------------------------------------------
# Health Record CRUD endpoints (nested under a patient)
# ---------------------------------------------------------------------------

@app.post(
    "/api/patients/{patient_id}/records",
    response_model=schemas.HealthRecordOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Health Records"],
)
def add_record(
    patient_id: int, record_in: schemas.HealthRecordCreate, db: Session = Depends(get_db)
):
    record = crud.add_health_record(db, patient_id, record_in)
    if not record:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return record


@app.get(
    "/api/patients/{patient_id}/records",
    response_model=list[schemas.HealthRecordOut],
    tags=["Health Records"],
)
def list_records(patient_id: int, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return crud.get_patient_records(db, patient_id)


@app.delete(
    "/api/records/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Health Records"],
)
def delete_record(record_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_health_record(db, record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Health record not found.")
    return None


# ---------------------------------------------------------------------------
# Standalone prediction endpoint (no DB write — quick "what if" checks)
# ---------------------------------------------------------------------------

@app.post("/api/predict", response_model=schemas.PredictionResponse, tags=["Prediction"])
def predict(record_in: schemas.HealthRecordCreate):
    result = predict_risk(
        record_in.glucose, record_in.haemoglobin, record_in.cholesterol
    )
    return result


@app.get("/api/health", tags=["Misc"])
def health_check():
    return {"status": "ok"}
