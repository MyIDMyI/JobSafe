from app.services.moel_defaulters import (
    normalize_workplace_name,
    parse_defaulter_page,
)


def test_normalize_workplace_name_removes_company_prefixes():
    assert normalize_workplace_name("(주)에이비씨테크") == "에이비씨테크"
    assert normalize_workplace_name("주식회사 에이비씨테크") == "에이비씨테크"
    assert normalize_workplace_name("에이비씨 테크") == "에이비씨테크"


def test_parse_defaulter_page_extracts_public_fields():
    html = """
    <table>
      <tbody>
        <tr>
          <td>2024년 1차</td>
          <td>홍요곤</td>
          <td>50</td>
          <td>(주)에이비씨테크</td>
          <td>제조업</td>
          <td>제주특별자치도 제주시</td>
          <td>제주특별자치도 제주시 은남길</td>
          <td>96,430,000</td>
        </tr>
      </tbody>
    </table>
    """
    rows = parse_defaulter_page(html)

    assert len(rows) == 1
    assert rows[0].representative_name == "홍요곤"
    assert rows[0].workplace_name == "(주)에이비씨테크"
    assert rows[0].arrears_amount == "96,430,000"
