from datetime import date
from typing import List, Optional

from strawberry.types import Info

# Shared Messages Imports
from shared.messages import (
    AppointmentCreate,
    AppointmentCreated,
    AppointmentRead,
    AppointmentReaded,
    AuthLoginRequest,
    AuthLoginResponse,
    AvailabilityRequest,
    AvailabilityResponse,
    PatientCreate,
    PatientCreated,
    PatientRead,
    PatientReaded,
)
from src.core.nats_client import nats_client
from src.core.security import require_permission
from src.graphql.inputs import (
    CreateAppointmentInput,
    CreatePatientInput,
    LoginInput,
)
from src.graphql.types import (
    AppointmentType,
    AvailabilitySlotType,
    GenericResponse,
    LoginResponse,
    PatientType,
)


# --- AUTH ---
async def login(input: LoginInput) -> LoginResponse:
    req = AuthLoginRequest(email=input.email, password=input.password)
    res = await nats_client.request("auth.login", req, AuthLoginResponse)

    return LoginResponse(
        success=res.success,
        token=res.token,
        user_id=str(res.user_id) if res.user_id else None,
        error=res.error,
    )


# --- PATIENTS ---
@require_permission("patients", "read")
async def get_patient(id: str, info: Info) -> Optional[PatientType]:
    req = PatientRead(patient_id=id)
    res = await nats_client.request("patient.read", req, PatientReaded)

    if not res.success:
        return None

    return PatientType(
        id=str(res.id),
        first_name=res.first_name,
        last_name=res.last_name,
        mrn=res.mrn,
        email=res.email,
        is_active=res.is_active,
    )


@require_permission("patients", "write")
async def create_patient(input: CreatePatientInput, info: Info) -> GenericResponse:
    user_id = info.context["user"].user_id

    req = PatientCreate(
        user_id=user_id,  # Creator
        first_name=input.first_name,
        last_name=input.last_name,
        mrn=input.mrn,
        email=input.email,
    )

    res = await nats_client.request("patient.create", req, PatientCreated)

    return GenericResponse(
        success=res.success,
        id=str(res.id) if res.success else None,
        error=None,  # Shared message doesn't return error text in this object, simplifed
    )


# --- APPOINTMENTS ---
@require_permission("appointments", "read")
async def get_appointment(id: str, info: Info) -> Optional[AppointmentType]:
    req = AppointmentRead(appointment_id=id)
    res = await nats_client.request("appointment.read", req, AppointmentReaded)

    if not res.success:
        return None

    return AppointmentType(
        id=str(res.id),
        patient_id=str(res.patient_id),
        provider_id=str(res.provider_id),
        start_time=res.start_time,
        end_time=res.end_time,
        status=res.status,
        appointment_type=res.appointment_type,
        reason=res.reason,
    )


@require_permission("appointments", "write")
async def create_appointment(
    input: CreateAppointmentInput, info: Info
) -> GenericResponse:
    user_id = info.context["user"].user_id

    req = AppointmentCreate(
        user_id=user_id,
        patient_id=input.patient_id,
        provider_id=input.provider_id,
        start_time=input.start_time,
        appointment_type=input.appointment_type,
        reason=input.reason,
    )

    res = await nats_client.request("appointment.create", req, AppointmentCreated)

    return GenericResponse(
        success=res.success,
        id=str(res.id) if res.success else None,
        error=res.error,
    )


@require_permission("appointments", "read")
async def check_availability(
    provider_id: str, date: date, info: Info
) -> List[AvailabilitySlotType]:
    req = AvailabilityRequest(provider_id=provider_id, date=date)
    res = await nats_client.request("availability.get", req, AvailabilityResponse)

    return [
        AvailabilitySlotType(start=s.start, end=s.end, available=s.available)
        for s in res.slots
    ]
