import uuid
import bcrypt
from typing import Optional

from fastapi import HTTPException, status

from app.core.auth import create_access_token
from app.models.user import User, UserCreate, UserPublic, UserRole


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


async def get_user_by_email(email: str, db) -> Optional[User]:
    doc = await db["users"].find_one({"email": email})
    if doc is None:
        return None
    # Skip malformed docs that don't have hashed_password
    if not doc.get("hashed_password"):
        return None
    try:
        return User(**doc)
    except Exception:
        return None


async def register_user(user_create: UserCreate, db) -> UserPublic:
    existing = await get_user_by_email(user_create.email, db)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed = hash_password(user_create.password)
    user_id = uuid.uuid4().hex

    doc: dict = {
        "_id": user_id,
        "email": user_create.email,
        "hashed_password": hashed,
        "role": user_create.role.value,
        "is_active": True,
    }

    if user_create.role == UserRole.business:
        doc["company_name"] = user_create.company_name
        doc["industry"] = user_create.industry

    await db["users"].insert_one(doc)

    return UserPublic(
        _id=user_id,
        email=doc["email"],
        role=doc["role"],
        is_active=doc["is_active"],
        company_name=doc.get("company_name"),
        industry=doc.get("industry"),
    )


async def login_user(email: str, password: str, db) -> dict:
    user = await get_user_by_email(email, db)
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role.value,
        },
    }
