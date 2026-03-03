from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    phone: str = Field(min_length=6)
    password: str = Field(min_length=8)
    first_name: str | None = None
    last_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr | None = None
    phone: str | None = None
    password: str = Field(min_length=8)

    def validate_identifier(self) -> None:
        if not self.email and not self.phone:
            raise ValueError("Either email or phone must be provided.")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
