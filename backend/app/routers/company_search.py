from fastapi import APIRouter, HTTPException, Query, status

from ..services.dart_companies import search_companies


router = APIRouter(prefix="/api/company-search", tags=["company-search"])


@router.get("")
async def company_search(q: str = Query(min_length=2, max_length=60)):
    try:
        return await search_companies(q.strip())
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="기업 검색 데이터를 불러오지 못했습니다.",
        )
