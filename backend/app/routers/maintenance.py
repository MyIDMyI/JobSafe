from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..config import get_settings
from ..database import get_db
from ..models import Company
from ..services.checks import run_company_check
from ..services.work24 import Work24Client


router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


@router.post("/run-checks")
async def run_all_checks(
    x_cron_secret: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    if not settings.cron_secret or x_cron_secret != settings.cron_secret:
        raise HTTPException(status_code=401, detail="자동 점검 인증에 실패했습니다.")

    stmt = (
        select(Company)
        .options(selectinload(Company.checks))
        .order_by(Company.id.asc())
    )
    companies = list(db.scalars(stmt).unique().all())
    client = Work24Client()

    checked = 0
    changed = 0
    failed = 0

    for company in companies:
        check = await run_company_check(db, company, client=client)
        checked += 1
        if check.changed_fields:
            changed += 1
        if check.wage_arrears_status in {"error", "not_configured"}:
            failed += 1

    return {
        "checked": checked,
        "changed": changed,
        "failed": failed,
    }
