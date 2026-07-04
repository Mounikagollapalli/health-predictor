"""
schemas.py
-----------
Pydantic models used to validate request bodies and shape API responses.
Keeping these separate from the SQLAlchemy models (models.py) is good
practice: it decouples what the database stores from what the API
exposes/accepts.
"""

from pydantic import BaseModel, EmailStr, field_validator
from datetime import date, datetime
from typing import Optional, List


# ---------- Health Record ----------

class HealthRecordCreate(BaseModel):
    glucose: float
    haemoglobin: float
    cholesterol: float

    @field_validator("glucose")
    @classmethod
    def glucose_range(cls, v):
        if not (0 < v <= 1000):
            raise ValueError("Glucose must be between 0 and 1000 mg/dL")
        return v

    @field_validator("haemoglobin")
    @classmethod
    def haemoglobin_range(cls, v):
        if not (0 < v <= 30):
            raise ValueError("Haemoglobin must be between 0 and 30 g/dL")
        return v

    @field_validator("cholesterol")
    @classmethod
    def cholesterol_range(cls, v):
        if not (0 < v <= 1000):
            raise ValueError("Cholesterol must be between 0 and 1000 mg/dL")
        return v


class HealthRecordOut(BaseModel):
    id: int
    glucose: float
    haemoglobin: float
    cholesterol: float
    risk_level: Optional[str] = None
    risk_confidence: Optional[float] = None
    recorded_at: datetime

    class Config:
        from_attributes = True


# ---------- Patient ----------

class PatientBase(BaseModel):
    name: str
    dob: date
    email: EmailStr

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("dob")
    @classmethod
    def dob_not_future(cls, v):
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v


class PatientCreate(PatientBase):
    # Allow creating a patient together with their first health reading
    glucose: float
    haemoglobin: float
    cholesterol: float

    @field_validator("glucose")
    @classmethod
    def glucose_range(cls, v):
        if not (0 < v <= 1000):
            raise ValueError("Glucose must be between 0 and 1000 mg/dL")
        return v

    @field_validator("haemoglobin")
    @classmethod
    def haemoglobin_range(cls, v):
        if not (0 < v <= 30):
            raise ValueError("Haemoglobin must be between 0 and 30 g/dL")
        return v

    @field_validator("cholesterol")
    @classmethod
    def cholesterol_range(cls, v):
        if not (0 < v <= 1000):
            raise ValueError("Cholesterol must be between 0 and 1000 mg/dL")
        return v


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    dob: Optional[date] = None
    email: Optional[EmailStr] = None


class PatientOut(PatientBase):
    id: int
    created_at: datetime
    records: List[HealthRecordOut] = []

    class Config:
        from_attributes = True


class PatientSummary(PatientBase):
    """Lighter-weight version for list views: latest reading only."""
    id: int
    created_at: datetime
    latest_record: Optional[HealthRecordOut] = None

    class Config:
        from_attributes = True


class PredictionResponse(BaseModel):
    risk_level: str
    risk_confidence: float
    probabilities: dict
