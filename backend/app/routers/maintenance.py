import json

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..config import get_settings
from ..database import get_db
from ..models import CheckResult, Company
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
        previous = company.checks[0] if company.checks else None
        result = await client.check_wage_arrears(company)

        changed_fields: list[str] = []
        if previous and previous.wage_arrears_status != result.status:
            changed_fields.append("wage_arrears_status")
            changed += 1

        if result.status == "error":
            failed += 1

        db.add(
            CheckResult(
                company_id=company.id,
                wage_arrears_status=result.status,
                changed_fields=(
                    json.dumps(changed_fields, ensure_ascii=False)
                    if changed_fields
                    else None
                ),
                error_message=(
                    result.error_message
                    if result.status in {"error", "not_configured"}
                    else None
                ),
            )
        )
        db.commit()
        checked += 1

    return {
        "checked": checked,
        "changed": changed,
        "failed": failed,
    }
