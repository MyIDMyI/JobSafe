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
    """Client for Work24's '임금체불 명단공개 사업주 여부' Open API."""

    WAGE_ARREARS_URL = (
        "https://www.work24.go.kr"
        "/cm/openapi/app-form/sa-employ-improve-form-pay-back.do"
    )

    def __init__(self) -> None:
        self.settings = get_settings()

    @staticmethod
    def _digits_only(value: str) -> str:
        return "".join(ch for ch in value if ch.isdigit())

    @staticmethod
    def _find_text(root: ElementTree.Element, tag_name: str) -> str | None:
        """Find text even if the XML response later adds a namespace."""
        for element in root.iter():
            local_name = element.tag.rsplit("}", 1)[-1]
            if local_name == tag_name:
                return element.text.strip() if element.text else None
        return None

    @classmethod
    def parse_response(cls, xml_text: str) -> Work24Result:
        try:
            root = ElementTree.fromstring(xml_text)
        except ElementTree.ParseError:
            return Work24Result(
                status="error",
                error_message="고용24 XML 응답을 해석하지 못했습니다.",
            )

        success = cls._find_text(root, "lnkSucsYn")
        judgement = cls._find_text(root, "judgReltYn")
        error_code = cls._find_text(root, "errMsgCd")
        error_message = cls._find_text(root, "errMsg")

        if success != "Y":
            detail = " / ".join(
                part for part in [error_code, error_message] if part
            )
            return Work24Result(
                status="error",
                error_message=detail or "고용24 조회에 실패했습니다.",
            )

        if judgement == "Y":
            return Work24Result(status="yes")
        if judgement == "N":
            return Work24Result(status="no")

        return Work24Result(
            status="error",
            error_message="고용24 판정 결과가 Y/N 형식이 아닙니다.",
        )

    async def check_wage_arrears(self, company: Company) -> Work24Result:
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
                response = await client.get(self.WAGE_ARREARS_URL, params=params)
                response.raise_for_status()
        except httpx.TimeoutException:
            return Work24Result(
                status="error",
                error_message="고용24 응답 시간이 초과되었습니다.",
            )
        except httpx.HTTPError as exc:
            return Work24Result(
                status="error",
                error_message=f"고용24 호출 실패: {exc}",
            )

        return self.parse_response(response.text)
