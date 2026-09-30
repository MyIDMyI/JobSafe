from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def digits_only(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    business_registration_number: str = Field(min_length=10, max_length=20)
    workplace_management_number: str = Field(default="", max_length=30)
    job_posting_name: str | None = Field(default=None, max_length=200)
    memo: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("기업명을 입력해 주세요.")
        return value

    @field_validator("business_registration_number")
    @classmethod
    def validate_business_registration_number(cls, value: str) -> str:
        value = value.strip()
        if any(not (ch.isdigit() or ch in "- ") for ch in value):
            raise ValueError("사업자등록번호는 숫자와 하이픈만 입력할 수 있습니다.")

        normalized = digits_only(value)
        if len(normalized) != 10:
            raise ValueError("사업자등록번호는 숫자 10자리여야 합니다.")
        return normalized

    @field_validator("workplace_management_number")
    @classmethod
    def validate_workplace_management_number(cls, value: str) -> str:
        value = value.strip()
        if not value:
            return ""
        if any(not (ch.isdigit() or ch in "- ") for ch in value):
            raise ValueError("사업장관리번호는 숫자와 하이픈만 입력할 수 있습니다.")
        return digits_only(value)

    @field_validator("job_posting_name", "memo")
    @classmethod
    def normalize_optional_fields(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)


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
    checks: list[CheckResultRead] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
