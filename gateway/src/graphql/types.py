from datetime import datetime
from typing import List, Optional

import strawberry


@strawberry.type
class UserType:
    id: str
    email: str
    role_id: str
    is_active: bool


@strawberry.type
class LoginResponse:
    success: bool
    token: Optional[str] = None
    user_id: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class PatientType:
    id: str
    first_name: str
    last_name: str
    mrn: str
    email: Optional[str]
    is_active: bool


@strawberry.type
class AppointmentType:
    id: str
    patient_id: str
    provider_id: str
    start_time: datetime
    end_time: datetime
    status: str
    appointment_type: str
    reason: Optional[str]


@strawberry.type
class DiagnosisCodeType:
    code: str
    description: str


@strawberry.type
class EncounterType:
    id: str
    date: datetime
    patient_id: str
    provider_id: str
    diagnosis_codes: List[DiagnosisCodeType]


@strawberry.type
class AvailabilitySlotType:
    start: datetime
    end: datetime
    available: bool


@strawberry.type
class GenericResponse:
    success: bool
    id: Optional[str] = None
    error: Optional[str] = None
