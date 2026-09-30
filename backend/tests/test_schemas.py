import pytest
from pydantic import ValidationError

from app.schemas import CompanyCreate


def test_company_create_normalizes_identifiers():
    company = CompanyCreate(
        name="  테스트 기업  ",
        business_registration_number="123-45-67890",
        workplace_management_number="123-456-78901",
        job_posting_name="  백엔드 개발자  ",
    )

    assert company.name == "테스트 기업"
    assert company.business_registration_number == "1234567890"
    assert company.workplace_management_number == "12345678901"
    assert company.job_posting_name == "백엔드 개발자"


def test_company_create_rejects_letters_in_business_number():
    with pytest.raises(ValidationError):
        CompanyCreate(
            name="테스트",
            business_registration_number="12345abc90",
        )


def test_company_create_rejects_letters_in_workplace_number():
    with pytest.raises(ValidationError):
        CompanyCreate(
            name="테스트",
            business_registration_number="1234567890",
            workplace_management_number="123abc",
        )


def test_blank_optional_fields_are_normalized():
    company = CompanyCreate(
        name="테스트",
        business_registration_number="1234567890",
        job_posting_name="   ",
        memo="   ",
    )

    assert company.job_posting_name is None
    assert company.memo is None
