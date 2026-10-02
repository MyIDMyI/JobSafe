import asyncio
import io
import re
import time
import zipfile
from xml.etree import ElementTree

import httpx

from ..config import get_settings


DART_CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"
DART_COMPANY_URL = "https://opendart.fss.or.kr/api/company.json"
CACHE_TTL_SECONDS = 12 * 60 * 60

_cache_lock = asyncio.Lock()
_corp_cache: tuple[float, list[dict]] | None = None


def _normalize_name(value: str) -> str:
    value = value.lower().strip()
    return re.sub(r"\s+", "", value)


def _format_business_number(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
    return value.strip()


async def _load_corp_codes(client: httpx.AsyncClient, key: str) -> list[dict]:
    global _corp_cache

    now = time.time()
    if _corp_cache and now - _corp_cache[0] < CACHE_TTL_SECONDS:
        return _corp_cache[1]

    async with _cache_lock:
        now = time.time()
        if _corp_cache and now - _corp_cache[0] < CACHE_TTL_SECONDS:
            return _corp_cache[1]

        response = await client.get(
            DART_CORP_CODE_URL,
            params={"crtfc_key": key},
            timeout=30,
        )
        response.raise_for_status()

        try:
            with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                xml_name = next(
                    name for name in archive.namelist()
                    if name.lower().endswith(".xml")
                )
                xml_bytes = archive.read(xml_name)
        except (zipfile.BadZipFile, StopIteration) as exc:
            raise RuntimeError("DART 기업목록 응답을 처리하지 못했습니다.") from exc

        root = ElementTree.fromstring(xml_bytes)
        rows = []
        for item in root.findall(".//list"):
            corp_code = (item.findtext("corp_code") or "").strip()
            corp_name = (item.findtext("corp_name") or "").strip()
            stock_code = (item.findtext("stock_code") or "").strip()
            modify_date = (item.findtext("modify_date") or "").strip()
            if corp_code and corp_name:
                rows.append(
                    {
                        "corp_code": corp_code,
                        "corp_name": corp_name,
                        "stock_code": stock_code,
                        "modify_date": modify_date,
                    }
                )

        _corp_cache = (time.time(), rows)
        return rows


async def _fetch_company_detail(
    client: httpx.AsyncClient,
    key: str,
    row: dict,
) -> dict:
    response = await client.get(
        DART_COMPANY_URL,
        params={"crtfc_key": key, "corp_code": row["corp_code"]},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "000":
        return {
            **row,
            "business_registration_number": "",
            "address": "",
            "homepage": "",
            "ceo_name": "",
            "can_register": False,
        }

    business_number = (data.get("bizr_no") or "").strip()
    return {
        "corp_code": row["corp_code"],
        "company_name": (data.get("corp_name") or row["corp_name"]).strip(),
        "stock_code": (data.get("stock_code") or row["stock_code"]).strip(),
        "business_registration_number": _format_business_number(business_number),
        "address": (data.get("adres") or "").strip(),
        "homepage": (data.get("hm_url") or "").strip(),
        "ceo_name": (data.get("ceo_nm") or "").strip(),
        "can_register": len("".join(ch for ch in business_number if ch.isdigit())) == 10,
    }


async def search_companies(query: str, limit: int = 8) -> dict:
    settings = get_settings()
    key = settings.dart_auth_key.strip()
    if not key:
        return {
            "status": "not_configured",
            "query": query,
            "results": [],
            "message": "OpenDART 인증키가 아직 설정되지 않았습니다.",
        }

    normalized_query = _normalize_name(query)
    if len(normalized_query) < 2:
        return {
            "status": "ok",
            "query": query,
            "results": [],
            "message": "기업명은 2글자 이상 입력해 주세요.",
        }

    async with httpx.AsyncClient(
        headers={"User-Agent": "JobSafe/1.0"}
    ) as client:
        rows = await _load_corp_codes(client, key)
        matched = [
            row for row in rows
            if normalized_query in _normalize_name(row["corp_name"])
        ]

        matched.sort(
            key=lambda row: (
                0 if _normalize_name(row["corp_name"]) == normalized_query else 1,
                len(row["corp_name"]),
                row["corp_name"],
            )
        )
        candidates = matched[:limit]

        details = await asyncio.gather(
            *[
                _fetch_company_detail(client, key, row)
                for row in candidates
            ],
            return_exceptions=True,
        )

    results = []
    for row, detail in zip(candidates, details):
        if isinstance(detail, Exception):
            results.append(
                {
                    "corp_code": row["corp_code"],
                    "company_name": row["corp_name"],
                    "stock_code": row["stock_code"],
                    "business_registration_number": "",
                    "address": "",
                    "homepage": "",
                    "ceo_name": "",
                    "can_register": False,
                }
            )
        else:
            results.append(detail)

    return {
        "status": "ok",
        "query": query,
        "results": results,
        "message": "" if results else "일치하는 DART 등록기업을 찾지 못했습니다.",
    }
