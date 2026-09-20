from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    business_registration_number: str = Field(min_length=10, max_length=20)
    workplace_management_number: str = Field(min_length=1, max_length=30)
    job_posting_name: str | None = Field(default=None, max_length=200)
    memo: str | None = None


class CheckResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    wage_arrears_status: str
    insurance_default_status: str
    serious_accident_status: str
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
