from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import ClientCompany, Company
from ..schemas import CompanyCreate, CompanyRead
from ..services.checks import run_company_check
from ..services.moel_defaulters import find_defaulter_candidates


router = APIRouter(prefix="/api/companies", tags=["companies"])


def get_client_id(
    x_client_id: Annotated[str | None, Header(alias="X-Client-Id")] = None,
) -> str:
    if not x_client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="브라우저 식별정보가 없습니다. 페이지를 새로고침해 주세요.",
        )

    try:
        return str(UUID(x_client_id.strip()))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="브라우저 식별정보가 올바르지 않습니다.",
        )


def _get_company_or_404(db: Session, company_id: int, owner_key: str) -> Company:
    stmt = (
        select(Company)
        .join(ClientCompany, ClientCompany.company_id == Company.id)
        .where(Company.id == company_id, ClientCompany.owner_key == owner_key)
        .options(selectinload(Company.checks))
    )
    company = db.scalar(stmt)
    if not company:
        raise HTTPException(status_code=404, detail="관심기업을 찾을 수 없습니다.")
    return company


@router.get("", response_model=list[CompanyRead])
def list_companies(
    owner_key: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Company)
        .join(ClientCompany, ClientCompany.company_id == Company.id)
        .where(ClientCompany.owner_key == owner_key)
        .options(selectinload(Company.checks))
        .order_by(Company.id.desc())
    )
    return list(db.scalars(stmt).unique().all())


@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    owner_key: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    duplicate = db.scalar(
        select(Company)
        .join(ClientCompany, ClientCompany.company_id == Company.id)
        .where(
            ClientCompany.owner_key == owner_key,
            Company.business_registration_number
            == payload.business_registration_number,
        )
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 등록된 사업자등록번호입니다.",
        )

    company = Company(**payload.model_dump())
    db.add(company)
    db.flush()
    db.add(ClientCompany(owner_key=owner_key, company_id=company.id))
    db.commit()
    return _get_company_or_404(db, company.id, owner_key)


@router.post("/refresh-all")
async def refresh_all_companies(
    owner_key: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Company)
        .join(ClientCompany, ClientCompany.company_id == Company.id)
        .where(ClientCompany.owner_key == owner_key)
        .options(selectinload(Company.checks))
        .order_by(Company.id.desc())
    )
    companies = list(db.scalars(stmt).unique().all())

    checked = 0
    changed = 0
    failed = 0

    for company in companies:
        previous = company.checks[0].wage_arrears_status if company.checks else None
        result = await run_company_check(db, company)
        checked += 1

        if result.wage_arrears_status in {"error", "not_configured"}:
            failed += 1

        if previous is not None and result.wage_arrears_status != previous:
            changed += 1

    return {
        "checked": checked,
        "changed": changed,
        "failed": failed,
    }


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(
    company_id: int,
    owner_key: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    return _get_company_or_404(db, company_id, owner_key)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: int,
    owner_key: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    company = _get_company_or_404(db, company_id, owner_key)
    db.delete(company)
    db.commit()


@router.post("/{company_id}/checks", response_model=CompanyRead)
async def run_check(
    company_id: int,
    owner_key: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    company = _get_company_or_404(db, company_id, owner_key)
    await run_company_check(db, company)
    return _get_company_or_404(db, company_id, owner_key)


@router.get("/{company_id}/defaulter-details")
async def get_defaulter_details(
    company_id: int,
    owner_key: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    company = _get_company_or_404(db, company_id, owner_key)
    latest = company.checks[0] if company.checks else None

    if not latest or latest.wage_arrears_status != "yes":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="고용24에서 임금체불 명단공개 대상으로 확인된 기업만 상세명단을 조회할 수 있습니다.",
        )

    try:
        return await find_defaulter_candidates(company.name)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="고용노동부 공개명단 상세정보를 불러오지 못했습니다.",
        )
