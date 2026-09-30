from app.services.moel_defaulters import (
    normalize_workplace_name,
    parse_defaulter_page,
    parse_total_count,
)


def test_normalize_workplace_name_removes_company_prefixes():
    assert normalize_workplace_name("(주)에이비씨테크") == "에이비씨테크"
    assert normalize_workplace_name("주식회사 에이비씨테크") == "에이비씨테크"
    assert normalize_workplace_name("에이비씨 테크") == "에이비씨테크"


def test_parse_current_moel_table_extracts_only_published_fields():
    html = """
    <html>
      <body>
        <p>전체 814</p>
        <table>
          <thead>
            <tr>
              <th>성명</th>
              <th>나이</th>
              <th>사업장명</th>
              <th>주소지(사업주)</th>
              <th>소재지(사업장)</th>
              <th>체불액(원)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>홍요곤</td>
              <td>50</td>
              <td>(주)에이비씨테크</td>
              <td>제주특별자치도 제주시</td>
              <td>제주특별자치도 제주시 은남길</td>
              <td>96,430,000</td>
            </tr>
          </tbody>
        </table>
      </body>
    </html>
    """
    rows = parse_defaulter_page(html)

    assert len(rows) == 1
    assert rows[0].representative_name == "홍요곤"
    assert rows[0].workplace_name == "(주)에이비씨테크"
    assert rows[0].arrears_amount == "96,430,000"
    assert rows[0].disclosure_round is None
    assert rows[0].industry is None
    assert parse_total_count(html) == 814


def test_parser_ignores_unrelated_tables():
    html = """
    <table><tbody><tr><td>irrelevant</td></tr></tbody></table>
    """
    assert parse_defaulter_page(html) == []
