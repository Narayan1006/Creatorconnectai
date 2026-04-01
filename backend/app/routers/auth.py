from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.auth import get_current_user
from app.core.database import get_database
from app.models.user import UserCreate, UserPublic
from app.services.auth_service import login_user, register_user

router = APIRouter()


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    db=Depends(get_database),
) -> UserPublic:
    return await register_user(user_create, db)


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_database),
) -> dict:
    return await login_user(form_data.username, form_data.password, db)


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)) -> dict:
    return current_user
