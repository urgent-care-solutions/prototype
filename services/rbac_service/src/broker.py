import uuid

from faststream import FastStream
from faststream.nats import NatsBroker
from sqlalchemy import insert

from shared.messages import UserCreate, UserCreated
from src.models import User

broker = NatsBroker("nats://localhost:4222")

app = FastStream(broker, title="RBAC Service", version="0.1", description="Handles RBAC access to clinic resources")


@broker.subscriber("user.create")
@broker.publisher("user.created")
@broker.publisher("audit.log.user")
async def handle_user_create(msg: UserCreate) -> UserCreated:
    try:
        await insert(User).values(id=uuid.uuid4, role_id=msg.role_id, email=msg.email)
    except Exception:
        print("")

        return UserCreated(success=False)
    else:
        return UserCreated(success=True)
