from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.models.base import BaseDocument


class UserRole(str, Enum):
    business = "business"
    creator = "creator"


class User(BaseDocument):
    email: EmailStr
    hashed_password: str
    role: UserRole
    is_active: bool = True


class BusinessUser(User):
    company_name: str
    industry: str


class CreatorUser(User):
    creator_id: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole
    company_name: Optional[str] = None
    industry: Optional[str] = None

    @model_validator(mode="after")
    def business_fields_required(self) -> "UserCreate":
        if self.role == UserRole.business:
            if not self.company_name:
                raise ValueError("company_name is required for business accounts")
            if not self.industry:
                raise ValueError("industry is required for business accounts")
        return self


class UserPublic(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    email: EmailStr
    role: UserRole
    is_active: bool
    company_name: Optional[str] = None
    industry: Optional[str] = None
    creator_id: Optional[str] = None

    model_config = {
        "populate_by_name": True,
    }
