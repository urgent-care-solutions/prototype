from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "organizations" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(200) NOT NULL UNIQUE,
    "type" VARCHAR(50),
    "tax_id" VARCHAR(50),
    "address" JSONB,
    "settings" JSONB NOT NULL,
    "timezone" VARCHAR(50) NOT NULL DEFAULT 'America/New_York',
    "subscription_tier" VARCHAR(50) NOT NULL DEFAULT 'standard',
    "is_active" BOOL NOT NULL DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "clinics" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(200) NOT NULL,
    "address" JSONB,
    "phone" VARCHAR(20),
    "email" VARCHAR(255),
    "timezone" VARCHAR(50) NOT NULL DEFAULT 'America/New_York',
    "working_hours" JSONB NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "organization_id" UUID NOT NULL REFERENCES "organizations" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "locations" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(200) NOT NULL,
    "type" VARCHAR(50) NOT NULL,
    "address" JSONB NOT NULL,
    "phone" VARCHAR(20),
    "timezone" VARCHAR(50) NOT NULL DEFAULT 'America/New_York',
    "is_active" BOOL NOT NULL DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "clinic_id" UUID REFERENCES "clinics" ("id") ON DELETE CASCADE,
    "organization_id" UUID NOT NULL REFERENCES "organizations" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "roles" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "description" TEXT,
    "permissions" JSONB NOT NULL,
    "is_system_role" BOOL NOT NULL DEFAULT False,
    "is_active" BOOL NOT NULL DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "organization_id" UUID NOT NULL REFERENCES "organizations" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_roles_organiz_6fa377" UNIQUE ("organization_id", "name")
);
CREATE TABLE IF NOT EXISTS "users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "password_hash" VARCHAR(255) NOT NULL,
    "first_name" VARCHAR(100) NOT NULL,
    "last_name" VARCHAR(100) NOT NULL,
    "is_provider" BOOL NOT NULL DEFAULT False,
    "provider_npi" VARCHAR(10),
    "phone" VARCHAR(20),
    "is_active" BOOL NOT NULL DEFAULT True,
    "last_login" TIMESTAMPTZ,
    "failed_login_attempts" INT NOT NULL DEFAULT 0,
    "account_locked_until" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "organization_id" UUID NOT NULL REFERENCES "organizations" ("id") ON DELETE CASCADE,
    "role_id" UUID NOT NULL REFERENCES "roles" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "departments" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(200) NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "location_id" UUID REFERENCES "locations" ("id") ON DELETE CASCADE,
    "manager_id" UUID REFERENCES "users" ("id") ON DELETE CASCADE,
    "organization_id" UUID NOT NULL REFERENCES "organizations" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)
