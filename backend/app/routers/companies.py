from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Company
from ..schemas import CompanyCreate, CompanyRead
from ..services.checks import run_company_check
from ..services.moel_defaulters import find_defaulter_candidates


router = APIRouter(prefix="/api/companies", tags=["companies"])


def _get_company_or_404(db: Session, company_id: int) -> Company:
    stmt = (
        select(Company)
        .where(Company.id == company_id)
        .options(selectinload(Company.checks))
    )
    company = db.scalar(stmt)
    if not company:
        raise HTTPException(status_code=404, detail="관심기업을 찾을 수 없습니다.")
    return company


@router.get("", response_model=list[CompanyRead])
def list_companies(db: Session = Depends(get_db)):
    stmt = (
        select(Company)
        .options(selectinload(Company.checks))
        .order_by(Company.id.desc())
    )
    return list(db.scalars(stmt).unique().all())


@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    duplicate = db.scalar(
        select(Company).where(
            Company.business_registration_number
            == payload.business_registration_number
        )
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 등록된 사업자등록번호입니다.",
        )

    company = Company(**payload.model_dump())
    db.add(company)
    db.commit()
    return _get_company_or_404(db, company.id)


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: Session = Depends(get_db)):
    return _get_company_or_404(db, company_id)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = _get_company_or_404(db, company_id)
    db.delete(company)
    db.commit()


@router.post("/{company_id}/checks", response_model=CompanyRead)
async def run_check(company_id: int, db: Session = Depends(get_db)):
    company = _get_company_or_404(db, company_id)
    await run_company_check(db, company)
    return _get_company_or_404(db, company_id)


@router.get("/{company_id}/defaulter-details")
async def get_defaulter_details(company_id: int, db: Session = Depends(get_db)):
    company = _get_company_or_404(db, company_id)
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
