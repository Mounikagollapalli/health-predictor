"""
crud.py
--------
Database CRUD (Create, Read, Update, Delete) operations for Patients and
HealthRecords. Keeping these as plain functions (rather than inlining
queries into the route handlers) makes the API layer thinner and the
logic easier to test in isolation.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from . import models, schemas
from .ml_model import predict_risk


# ---------- Patient CRUD ----------

def create_patient(db: Session, patient_in: schemas.PatientCreate) -> models.Patient:
    """Creates a new patient AND their first health record together,
    running the ML prediction on that first record."""
    patient = models.Patient(
        name=patient_in.name,
        dob=patient_in.dob,
        email=patient_in.email,
    )
    db.add(patient)
    db.flush()  # get patient.id without committing yet

    prediction = predict_risk(
        patient_in.glucose, patient_in.haemoglobin, patient_in.cholesterol
    )

    record = models.HealthRecord(
        patient_id=patient.id,
        glucose=patient_in.glucose,
        haemoglobin=patient_in.haemoglobin,
        cholesterol=patient_in.cholesterol,
        risk_level=prediction["risk_level"],
        risk_confidence=prediction["risk_confidence"],
    )
    db.add(record)
    db.commit()
    db.refresh(patient)
    return patient


def get_patient(db: Session, patient_id: int) -> models.Patient | None:
    return db.query(models.Patient).filter(models.Patient.id == patient_id).first()


def get_patients(db: Session, skip: int = 0, limit: int = 100) -> list[models.Patient]:
    return (
        db.query(models.Patient)
        .order_by(desc(models.Patient.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_patient(
    db: Session, patient_id: int, patient_update: schemas.PatientUpdate
) -> models.Patient | None:
    patient = get_patient(db, patient_id)
    if not patient:
        return None

    update_data = patient_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)
    return patient


def delete_patient(db: Session, patient_id: int) -> bool:
    patient = get_patient(db, patient_id)
    if not patient:
        return False
    db.delete(patient)
    db.commit()
    return True


# ---------- Health Record CRUD ----------

def add_health_record(
    db: Session, patient_id: int, record_in: schemas.HealthRecordCreate
) -> models.HealthRecord | None:
    patient = get_patient(db, patient_id)
    if not patient:
        return None

    prediction = predict_risk(
        record_in.glucose, record_in.haemoglobin, record_in.cholesterol
    )

    record = models.HealthRecord(
        patient_id=patient_id,
        glucose=record_in.glucose,
        haemoglobin=record_in.haemoglobin,
        cholesterol=record_in.cholesterol,
        risk_level=prediction["risk_level"],
        risk_confidence=prediction["risk_confidence"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_health_record(db: Session, record_id: int) -> models.HealthRecord | None:
    return (
        db.query(models.HealthRecord)
        .filter(models.HealthRecord.id == record_id)
        .first()
    )


def delete_health_record(db: Session, record_id: int) -> bool:
    record = get_health_record(db, record_id)
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


def get_patient_records(db: Session, patient_id: int) -> list[models.HealthRecord]:
    return (
        db.query(models.HealthRecord)
        .filter(models.HealthRecord.patient_id == patient_id)
        .order_by(desc(models.HealthRecord.recorded_at))
        .all()
    )
