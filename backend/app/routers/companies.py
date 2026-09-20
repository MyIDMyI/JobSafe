import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import CheckResult, Company
from ..schemas import CompanyCreate, CompanyRead
from ..services.work24 import Work24Client


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
    stmt = select(Company).options(selectinload(Company.checks)).order_by(Company.id.desc())
    return list(db.scalars(stmt).unique().all())


@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
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
    previous = company.checks[0] if company.checks else None

    result = await Work24Client().check_all(company)

    current_values = {
        "wage_arrears_status": result["wage_arrears"].status,
        "insurance_default_status": result["insurance_default"].status,
        "serious_accident_status": result["serious_accident"].status,
    }

    changed_fields: list[str] = []
    if previous:
        for field, value in current_values.items():
            if getattr(previous, field) != value:
                changed_fields.append(field)

    errors = [
        item.error_message
        for item in result.values()
        if item.error_message and item.status == "error"
    ]

    check = CheckResult(
        company_id=company.id,
        **current_values,
        changed_fields=json.dumps(changed_fields, ensure_ascii=False) if changed_fields else None,
        error_message=" | ".join(errors) if errors else None,
    )
    db.add(check)
    db.commit()

    return _get_company_or_404(db, company_id)
