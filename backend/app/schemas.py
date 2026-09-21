from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def digits_only(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    business_registration_number: str = Field(min_length=10, max_length=20)
    workplace_management_number: str = Field(min_length=1, max_length=30)
    job_posting_name: str | None = Field(default=None, max_length=200)
    memo: str | None = None

    @field_validator("business_registration_number")
    @classmethod
    def validate_business_registration_number(cls, value: str) -> str:
        if len(digits_only(value)) != 10:
            raise ValueError("사업자등록번호는 숫자 10자리여야 합니다.")
        return value.strip()

    @field_validator("workplace_management_number")
    @classmethod
    def validate_workplace_management_number(cls, value: str) -> str:
        if not digits_only(value):
            raise ValueError("사업장관리번호를 입력해 주세요.")
        return value.strip()


class CheckResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    wage_arrears_status: str
    changed_fields: str | None
    error_message: str | None
    checked_at: datetime


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    business_registration_number: str
    workplace_management_number: str
    job_posting_name: str | None
    memo: str | None
    created_at: datetime
    checks: list[CheckResultRead] = []


class HealthResponse(BaseModel):
    status: str
