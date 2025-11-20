import uuid
from datetime import UTC, datetime

from passlib.hash import bcrypt
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Role(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, default=dict)
    is_system_role = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(tz=UTC))
    updated_at = Column(DateTime, default=datetime.now(tz=UTC), onupdate=datetime.now(tz=UTC))

    # Relationship
    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    is_provider = Column(Boolean, default=False)
    provider_npi = Column(String(10), nullable=True)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now(tz=UTC))
    updated_at = Column(DateTime, default=datetime.now(tz=UTC), onupdate=datetime.now(tz=UTC))

    # Relationships
    role = relationship("Role", back_populates="users")
    managed_departments = relationship("Department", back_populates="manager")

    def verify_password(self, password: str) -> bool:
        return bcrypt.verify(password, self.password_hash)

    @staticmethod
    def hash_password(password: str) -> str:
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            password = password_bytes[:72].decode("utf-8", errors="ignore")
        return bcrypt.hash(password)


class Clinic(Base):
    __tablename__ = "clinics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    address = Column(JSON, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    timezone = Column(String(50), default="America/New_York")
    working_hours = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(tz=UTC))
    updated_at = Column(DateTime, default=datetime.now(tz=UTC), onupdate=datetime.now(tz=UTC))

    # Relationship
    locations = relationship("Location", back_populates="clinic")


class Location(Base):
    __tablename__ = "locations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String(36), ForeignKey("clinics.id"), nullable=True)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)
    address = Column(JSON, nullable=False)
    phone = Column(String(20), nullable=True)
    timezone = Column(String(50), default="America/New_York")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(tz=UTC))
    updated_at = Column(DateTime, default=datetime.now(tz=UTC), onupdate=datetime.now(tz=UTC))

    # Relationships
    clinic = relationship("Clinic", back_populates="locations")
    departments = relationship("Department", back_populates="location")


class Department(Base):
    __tablename__ = "departments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    location_id = Column(String(36), ForeignKey("locations.id"), nullable=True)
    name = Column(String(200), nullable=False)
    manager_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(tz=UTC))
    updated_at = Column(DateTime, default=datetime.now(tz=UTC), onupdate=datetime.now(tz=UTC))

    # Relationships
    location = relationship("Location", back_populates="departments")
    manager = relationship("User", back_populates="managed_departments")
