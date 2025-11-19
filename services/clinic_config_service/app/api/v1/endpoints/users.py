from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import EmailStr

from app.schemas import UserCreate, UserResponse, UserUpdate, UserVerification
from app.services.user_service import UserService

router = APIRouter()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    return await UserService.create_user(user)


@router.get("/users/by-id/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: UUID):
    return await UserService.get_user(user_id)


@router.get("/users/by-email/{email}", response_model=UserResponse)
async def get_user_by_email(email: str):
    return await UserService.get_user_by_email(email)


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    organization_id: Optional[UUID] = Query(None),
    role_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    return await UserService.list_users(
        organization_id=organization_id,
        role_id=role_id,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: UUID, user: UserUpdate):
    return await UserService.update_user(user_id, user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID):
    await UserService.delete_user(user_id)
    return None


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(user_id: UUID):
    permissions = await UserService.get_user_permissions(user_id)
    return {"user_id": str(user_id), "permissions": permissions}


@router.post("/users/verify-password")
async def verify_user_pass(user_creds: UserVerification):
    user = await UserService.verify_user_password(user_creds.email, user_creds.password)
    if user is not None:
        return UserResponse.model_validate(user)

    raise HTTPException(
        status_code=404, detail="user with specified credentials not found"
    )
