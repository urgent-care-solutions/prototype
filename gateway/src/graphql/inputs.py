from datetime import datetime

import strawberry


@strawberry.input
class LoginInput:
    email: str
    password: str


@strawberry.input
class CreatePatientInput:
    first_name: str
    last_name: str
    mrn: str
    email: str
    # Simplified for brevity, normally includes insurance


@strawberry.input
class CreateAppointmentInput:
    patient_id: str
    provider_id: str
    start_time: datetime
    appointment_type: str  # initial, follow_up, etc.
    reason: str
