from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator
from passlib.hash import bcrypt
from datetime import datetime
from typing import Optional


class Organization(models.Model):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=200, unique=True)
    type = fields.CharField(max_length=50, null=True)
    tax_id = fields.CharField(max_length=50, null=True)
    address = fields.JSONField(null=True)
    settings = fields.JSONField(default={})
    timezone = fields.CharField(max_length=50, default="America/New_York")
    subscription_tier = fields.CharField(max_length=50, default="standard")
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "organizations"


class Role(models.Model):
    id = fields.UUIDField(pk=True)
    organization = fields.ForeignKeyField("models.Organization", related_name="roles")
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    permissions = fields.JSONField(default={})
    is_system_role = fields.BooleanField(default=False)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "roles"
        unique_together = (("organization", "name"),)


class User(models.Model):
    id = fields.UUIDField(pk=True)
    organization = fields.ForeignKeyField("models.Organization", related_name="users")
    role = fields.ForeignKeyField("models.Role", related_name="users")
    email = fields.CharField(max_length=255, unique=True)
    password_hash = fields.CharField(max_length=255)
    first_name = fields.CharField(max_length=100)
    last_name = fields.CharField(max_length=100)
    is_provider = fields.BooleanField(default=False)
    provider_npi = fields.CharField(max_length=10, null=True)
    phone = fields.CharField(max_length=20, null=True)
    is_active = fields.BooleanField(default=True)
    last_login = fields.DatetimeField(null=True)
    failed_login_attempts = fields.IntField(default=0)
    account_locked_until = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"

    def verify_password(self, password: str) -> bool:
        return bcrypt.verify(password, self.password_hash)

    @staticmethod
    def hash_password(password: str) -> str:
        # bcrypt has 72-byte limit, truncate if necessary
        # Convert to bytes to check length, then truncate if needed
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            password = password_bytes[:72].decode("utf-8", errors="ignore")
        return bcrypt.hash(password)


class Clinic(models.Model):
    id = fields.UUIDField(pk=True)
    organization = fields.ForeignKeyField("models.Organization", related_name="clinics")
    name = fields.CharField(max_length=200)
    address = fields.JSONField(null=True)
    phone = fields.CharField(max_length=20, null=True)
    email = fields.CharField(max_length=255, null=True)
    timezone = fields.CharField(max_length=50, default="America/New_York")
    working_hours = fields.JSONField(default={})
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "clinics"


class Location(models.Model):
    id = fields.UUIDField(pk=True)
    organization = fields.ForeignKeyField(
        "models.Organization", related_name="locations"
    )
    clinic = fields.ForeignKeyField(
        "models.Clinic", related_name="locations", null=True
    )
    name = fields.CharField(max_length=200)
    type = fields.CharField(max_length=50)
    address = fields.JSONField()
    phone = fields.CharField(max_length=20, null=True)
    timezone = fields.CharField(max_length=50, default="America/New_York")
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "locations"


class Department(models.Model):
    id = fields.UUIDField(pk=True)
    organization = fields.ForeignKeyField(
        "models.Organization", related_name="departments"
    )
    location = fields.ForeignKeyField(
        "models.Location", related_name="departments", null=True
    )
    name = fields.CharField(max_length=200)
    manager = fields.ForeignKeyField(
        "models.User", related_name="managed_departments", null=True
    )
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "departments"
