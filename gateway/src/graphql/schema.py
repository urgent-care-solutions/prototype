from typing import List, Optional

import strawberry

from src.graphql.resolvers import (
    check_availability,
    create_appointment,
    create_patient,
    get_appointment,
    get_patient,
    login,
)
from src.graphql.types import (
    AppointmentType,
    AvailabilitySlotType,
    GenericResponse,
    LoginResponse,
    PatientType,
)


@strawberry.type
class Query:
    patient: Optional[PatientType] = strawberry.field(
        resolver=get_patient
    )
    appointment: Optional[AppointmentType] = strawberry.field(
        resolver=get_appointment
    )
    provider_availability: List[AvailabilitySlotType] = (
        strawberry.field(resolver=check_availability)
    )

    @strawberry.field
    def health(self) -> str:
        return "Gateway is running"


@strawberry.type
class Mutation:
    login: LoginResponse = strawberry.field(resolver=login)
    create_patient: GenericResponse = strawberry.field(
        resolver=create_patient
    )
    create_appointment: GenericResponse = strawberry.field(
        resolver=create_appointment
    )


schema = strawberry.Schema(query=Query, mutation=Mutation)
