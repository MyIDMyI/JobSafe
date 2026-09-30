import json

from sqlalchemy.orm import Session

from ..models import CheckResult, Company
from .work24 import Work24Client


async def run_company_check(
    db: Session,
    company: Company,
    *,
    client: Work24Client | None = None,
) -> CheckResult:
    previous = company.checks[0] if company.checks else None
    result = await (client or Work24Client()).check_wage_arrears(company)

    changed_fields: list[str] = []
    if previous and previous.wage_arrears_status != result.status:
        changed_fields.append("wage_arrears_status")

    check = CheckResult(
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
    db.add(check)
    db.commit()
    db.refresh(check)
    return check
