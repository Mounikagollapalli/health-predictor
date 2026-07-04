"""
models.py
----------
SQLAlchemy ORM models.

Patient        - one row per person (Name, DOB, Email)
HealthRecord    - one row per health reading (Glucose, Haemoglobin,
                  Cholesterol, predicted risk, timestamp), linked to a
                  Patient. A patient can have many HealthRecords, which
                  lets us track readings over time.
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date
from .database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    dob = Column(Date, nullable=False)
    email = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    records = relationship(
        "HealthRecord",
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="desc(HealthRecord.recorded_at)",
    )


class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    glucose = Column(Float, nullable=False)
    haemoglobin = Column(Float, nullable=False)
    cholesterol = Column(Float, nullable=False)

    risk_level = Column(String, nullable=True)       # "Low" / "Moderate" / "High"
    risk_confidence = Column(Float, nullable=True)    # model's probability for predicted class

    recorded_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="records")
