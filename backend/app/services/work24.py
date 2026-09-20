from dataclasses import dataclass
from xml.etree import ElementTree

import httpx

from ..config import get_settings
from ..models import Company


@dataclass
class Work24Result:
    status: str
    error_message: str | None = None


class Work24Client:
    BASE_URL = "https://www.work24.go.kr"
    WAGE_ARREARS_PATH = "/cm/openapi/app-form/sa-employ-improve-form-pay-back.do"
    INSURANCE_DEFAULT_PATH = "/cm/openapi/app-form/sa-employ-improve-form-insur-defult.do"

    def __init__(self) -> None:
        self.settings = get_settings()

    @staticmethod
    def _digits_only(value: str) -> str:
        return "".join(ch for ch in value if ch.isdigit())

    async def _request(self, url: str, company: Company) -> Work24Result:
        if not self.settings.work24_auth_key:
            return Work24Result(
                status="not_configured",
                error_message="WORK24_AUTH_KEY가 설정되지 않았습니다.",
            )

        params = {
            "authKey": self.settings.work24_auth_key,
            "returnType": "XML",
            "brno": self._digits_only(company.business_registration_number),
            "bzmn": self._digits_only(company.workplace_management_number),
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            return Work24Result(status="error", error_message=f"고용24 호출 실패: {exc}")

        try:
            root = ElementTree.fromstring(response.text)
        except ElementTree.ParseError:
            return Work24Result(status="error", error_message="고용24 XML 응답을 해석하지 못했습니다.")

        success = root.findtext(".//lnkSucsYn")
        judgement = root.findtext(".//judgReltYn")
        error_code = root.findtext(".//errMsgCd")
        error_message = root.findtext(".//errMsg")

        if success != "Y":
            detail = " / ".join(part for part in [error_code, error_message] if part)
            return Work24Result(status="error", error_message=detail or "고용24 심사 조회에 실패했습니다.")

        if judgement == "Y":
            return Work24Result(status="yes")
        if judgement == "N":
            return Work24Result(status="no")
        return Work24Result(status="error", error_message="판정 결과가 Y/N 형식이 아닙니다.")

    async def check_all(self, company: Company) -> dict[str, Work24Result]:
        wage_url = f"{self.BASE_URL}{self.WAGE_ARREARS_PATH}"
        insurance_url = f"{self.BASE_URL}{self.INSURANCE_DEFAULT_PATH}"

        wage = await self._request(wage_url, company)
        insurance = await self._request(insurance_url, company)

        if self.settings.work24_serious_accident_url:
            serious = await self._request(self.settings.work24_serious_accident_url, company)
        else:
            serious = Work24Result(
                status="not_configured",
                error_message="중대재해 API URL은 공식 명세 확인 후 설정하도록 분리했습니다.",
            )

        return {
            "wage_arrears": wage,
            "insurance_default": insurance,
            "serious_accident": serious,
        }
