import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Log(Base):
    __tablename__ = "log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4))
    timestamp = Column(DateTime, default=datetime.now(tz=UTC))
