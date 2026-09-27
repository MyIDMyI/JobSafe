from app.services.work24 import Work24Client


def test_parse_target_result():
    xml = """
    <jdgnList>
      <lnkSucsYn>Y</lnkSucsYn>
      <judgReltYn>Y</judgReltYn>
    </jdgnList>
    """
    result = Work24Client.parse_response(xml)

    assert result.status == "yes"
    assert result.error_message is None


def test_parse_not_target_result():
    xml = """
    <jdgnList>
      <lnkSucsYn>Y</lnkSucsYn>
      <judgReltYn>N</judgReltYn>
    </jdgnList>
    """
    result = Work24Client.parse_response(xml)

    assert result.status == "no"
    assert result.error_message is None


def test_parse_api_key_error():
    xml = """
    <jdgnList>
      <lnkSucsYn>N</lnkSucsYn>
      <errMsgCd>ERR0001</errMsgCd>
      <errMsg>API KEY 오류</errMsg>
    </jdgnList>
    """
    result = Work24Client.parse_response(xml)

    assert result.status == "error"
    assert "ERR0001" in result.error_message
    assert "API KEY 오류" in result.error_message


def test_parse_missing_judgement():
    xml = """
    <jdgnList>
      <lnkSucsYn>Y</lnkSucsYn>
    </jdgnList>
    """
    result = Work24Client.parse_response(xml)

    assert result.status == "error"
    assert "Y/N" in result.error_message


def test_parse_invalid_xml():
    result = Work24Client.parse_response("<jdgnList>")

    assert result.status == "error"
    assert "XML" in result.error_message


def test_parse_namespaced_xml():
    xml = """
    <ns:jdgnList xmlns:ns="urn:jobsafe:test">
      <ns:lnkSucsYn>Y</ns:lnkSucsYn>
      <ns:judgReltYn>N</ns:judgReltYn>
    </ns:jdgnList>
    """
    result = Work24Client.parse_response(xml)

    assert result.status == "no"
