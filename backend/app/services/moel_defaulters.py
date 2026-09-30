import asyncio
import re
import time
from dataclasses import asdict, dataclass

import httpx
from bs4 import BeautifulSoup


MOEL_DEFAULTER_URL = "https://www.moel.go.kr/info/defaulter/defaulterList.do"
CACHE_TTL_SECONDS = 6 * 60 * 60
DEFAULT_ROWS_PER_PAGE = 10


@dataclass(frozen=True)
class DefaulterRecord:
    representative_name: str
    age: str
    workplace_name: str
    owner_address: str
    workplace_address: str
    arrears_amount: str
    disclosure_round: str | None = None
    industry: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


_cache: tuple[float, list[DefaulterRecord]] | None = None
_cache_lock = asyncio.Lock()


def normalize_workplace_name(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"\(\s*주\s*\)", "", text)
    text = re.sub(r"㈜|주식회사|유한회사|합자회사|합명회사", "", text)
    text = re.sub(r"[^0-9a-z가-힣]", "", text)
    return text


def _normalized_header(value: str) -> str:
    return re.sub(r"\s+", "", value).replace("·", "")


def parse_defaulter_page(html: str) -> list[DefaulterRecord]:
    """Parse the public MOEL defaulter table without inventing unsupported fields.

    The current MOEL table exposes six columns: name, age, workplace name,
    owner address, workplace address, and arrears amount. A fallback for an
    older eight-column layout is kept so the parser remains tolerant if the
    ministry serves a legacy layout on some pages.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows: list[DefaulterRecord] = []

    target_table = None
    for table in soup.find_all("table"):
        header_text = " ".join(table.stripped_strings)
        if "사업장명" in header_text and "체불액" in header_text:
            target_table = table
            break

    if target_table is None:
        return rows

    headers = [
        _normalized_header(" ".join(cell.stripped_strings))
        for cell in target_table.select("thead th")
    ]
    header_index = {header: index for index, header in enumerate(headers)}

    def pick(cells: list[str], *names: str) -> str:
        for name in names:
            index = header_index.get(_normalized_header(name))
            if index is not None and index < len(cells):
                return cells[index]
        return ""

    for tr in target_table.select("tbody tr"):
        cells = [
            " ".join(td.stripped_strings).strip()
            for td in tr.find_all(["th", "td"])
        ]
        if not cells:
            continue

        if headers:
            representative_name = pick(cells, "성명")
            age = pick(cells, "나이")
            workplace_name = pick(cells, "사업장명", "사업장")
            owner_address = pick(cells, "주소지(사업주)", "사업주주소")
            workplace_address = pick(cells, "소재지(사업장)", "사업장소재지")
            arrears_amount = pick(cells, "체불액(원)", "체불액")
            disclosure_round = pick(cells, "구분") or None
            industry = pick(cells, "업종") or None
        elif len(cells) >= 8:
            (
                disclosure_round,
                representative_name,
                age,
                workplace_name,
                industry,
                owner_address,
                workplace_address,
                arrears_amount,
            ) = cells[:8]
        elif len(cells) >= 6:
            (
                representative_name,
                age,
                workplace_name,
                owner_address,
                workplace_address,
                arrears_amount,
            ) = cells[:6]
            disclosure_round = None
            industry = None
        else:
            continue

        if not workplace_name or not representative_name:
            continue

        rows.append(
            DefaulterRecord(
                representative_name=representative_name,
                age=age,
                workplace_name=workplace_name,
                owner_address=owner_address,
                workplace_address=workplace_address,
                arrears_amount=arrears_amount,
                disclosure_round=disclosure_round,
                industry=industry,
            )
        )

    return rows


async def _fetch_page(client: httpx.AsyncClient, page: int) -> list[DefaulterRecord]:
    response = await client.get(
        MOEL_DEFAULTER_URL,
        params={"pageIndex": page},
        headers={"User-Agent": "JobSafe/1.0 (+public-data class project)"},
    )
    response.raise_for_status()
    return parse_defaulter_page(response.text)


def parse_total_count(html: str) -> int | None:
    soup = BeautifulSoup(html, "html.parser")
    text = " ".join(soup.stripped_strings)
    match = re.search(r"전체\s*([0-9,]+)", text)
    return int(match.group(1).replace(",", "")) if match else None


async def fetch_all_defaulters() -> list[DefaulterRecord]:
    global _cache

    now = time.monotonic()
    if _cache and now - _cache[0] < CACHE_TTL_SECONDS:
        return _cache[1]

    async with _cache_lock:
        now = time.monotonic()
        if _cache and now - _cache[0] < CACHE_TTL_SECONDS:
            return _cache[1]

        limits = httpx.Limits(max_connections=6, max_keepalive_connections=6)
        timeout = httpx.Timeout(15.0, connect=10.0)

        async with httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            follow_redirects=True,
        ) as client:
            first_response = await client.get(
                MOEL_DEFAULTER_URL,
                params={"pageIndex": 1},
                headers={"User-Agent": "JobSafe/1.0 (+public-data class project)"},
            )
            first_response.raise_for_status()

            records = parse_defaulter_page(first_response.text)
            if not records:
                raise RuntimeError("고용노동부 공개명단 표 형식을 확인하지 못했습니다.")

            total_count = parse_total_count(first_response.text)
            rows_per_page = len(records) or DEFAULT_ROWS_PER_PAGE
            total_pages = max(
                1,
                ((total_count or len(records)) + rows_per_page - 1)
                // rows_per_page,
            )

            for start in range(2, total_pages + 1, 6):
                pages = range(start, min(start + 6, total_pages + 1))
                batches = await asyncio.gather(
                    *(_fetch_page(client, page) for page in pages),
                    return_exceptions=True,
                )
                for result in batches:
                    if isinstance(result, Exception):
                        continue
                    records.extend(result)

        if not records:
            raise RuntimeError("고용노동부 체불사업주 공개명단을 불러오지 못했습니다.")

        _cache = (time.monotonic(), records)
        return records


async def find_defaulter_candidates(company_name: str) -> dict:
    records = await fetch_all_defaulters()
    normalized = normalize_workplace_name(company_name)

    exact = [
        record
        for record in records
        if normalize_workplace_name(record.workplace_name) == normalized
    ]

    return {
        "query_name": company_name,
        "match_status": (
            "exact_unique"
            if len(exact) == 1
            else "multiple"
            if len(exact) > 1
            else "not_found"
        ),
        "candidate_count": len(exact),
        "candidates": [record.to_dict() for record in exact],
        "source_url": MOEL_DEFAULTER_URL,
        "identity_note": (
            "고용노동부 공개명단에는 사업자등록번호가 표시되지 않아 "
            "사업장명 기준으로 찾은 일치 후보입니다. 동일 사업장임을 "
            "사업자등록번호로 직접 대조한 결과는 아닙니다."
        ),
    }
