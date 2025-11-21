from faststream import FastStream
from faststream.nats import NatsBroker

broker = NatsBroker("nats://localhost:4222")

app = FastStream(broker, title="RBAC Service", version="0.1", description="Handles RBAC access to clinic resources")
