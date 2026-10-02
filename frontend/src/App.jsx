import { useEffect, useMemo, useState } from "react";

import { api } from "./api";

const STATUS_LABELS = {
  yes: "임금체불 명단공개 대상",
  no: "임금체불 명단공개 미대상",
  error: "조회 실패",
  not_checked: "미점검",
  not_configured: "API 키 설정 필요",
};

function latestCheck(company) {
  return company.checks?.[0] ?? null;
}

function StatusBadge({ value }) {
  const normalized = value || "not_checked";

  return (
    <span className={`status status--${normalized}`}>
      {STATUS_LABELS[normalized] || normalized}
    </span>
  );
}

function StatusDescription({ value }) {
  if (value === "yes") {
    return (
      <p className="muted">
        고용24 OPEN API 판정값이 Y로 확인되어, 임금체불 명단공개 사업주 대상에 해당합니다.
      </p>
    );
  }

  if (value === "no") {
    return (
      <p className="muted">
        고용24 OPEN API 판정값이 N으로 확인되어, 현재 임금체불 명단공개 사업주 대상에는 해당하지 않습니다. 임금체불이 전혀 없다는 의미는 아닙니다.
      </p>
    );
  }

  if (value === "error") {
    return <p className="muted">공공데이터 조회에 실패했습니다. 오류 내용을 확인해 주세요.</p>;
  }

  if (value === "not_configured") {
    return <p className="muted">고용24 OPEN API 인증키가 설정되지 않았습니다.</p>;
  }

  return <p className="muted">아직 공공 위험정보 점검을 실행하지 않았습니다.</p>;
}

function CompanyCard({ company, onCheck, onDelete, checking, deleting }) {
  const [historyOpen, setHistoryOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailData, setDetailData] = useState(null);
  const [detailError, setDetailError] = useState("");
  const check = latestCheck(company);
  const hasChange = Boolean(check?.changed_fields);

  async function loadDefaulterDetails() {
    setDetailLoading(true);
    setDetailError("");
    try {
      setDetailData(await api.getDefaulterDetails(company.id));
    } catch (error) {
      setDetailData(null);
      setDetailError(error.message);
    } finally {
      setDetailLoading(false);
    }
  }

  return (
    <article className={`company-card ${hasChange ? "company-card--changed" : ""}`}>
      {hasChange && (
        <div className="change-alert">
          새로운 변경이 확인되었습니다. 이전 점검 결과와 상태가 달라졌습니다.
        </div>
      )}

      <div className="company-card__head">
        <div>
          <p className="eyebrow">관심기업</p>
          <h3>{company.name}</h3>
          <p className="muted">
            {company.job_posting_name || "채용공고명 미등록"}
          </p>
        </div>

        <div className="company-card__actions">
          <button
            className="button button--secondary"
            onClick={() => onCheck(company.id)}
            disabled={checking || deleting}
          >
            {checking ? "조회 중..." : "지금 점검"}
          </button>
          <button
            className="button button--ghost"
            onClick={() => setHistoryOpen((value) => !value)}
          >
            {historyOpen ? "이력 닫기" : `점검 이력 ${company.checks?.length || 0}`}
          </button>
          <button
            className="button button--danger"
            onClick={() => onDelete(company)}
            disabled={checking || deleting}
          >
            {deleting ? "삭제 중..." : "삭제"}
          </button>
        </div>
      </div>

      <div className="status-grid status-grid--single">
        <div>
          <span>고용24 임금체불 명단공개 사업주 여부</span>
          <StatusBadge value={check?.wage_arrears_status} />
        </div>
      </div>

      <StatusDescription value={check?.wage_arrears_status} />

      {check?.wage_arrears_status === "yes" && (
        <div className="detail-actions">
          <button
            className="button button--detail"
            onClick={loadDefaulterDetails}
            disabled={detailLoading}
          >
            {detailLoading ? "공식 명단 조회 중..." : "고용노동부 상세 공개정보 조회"}
          </button>
          <span>사업장명이 일치하는 고용노동부 공개명단 후보를 확인합니다.</span>
        </div>
      )}

      {detailError && <p className="inline-warning">{detailError}</p>}

      {detailData && (
        <div className="defaulter-panel">
          <div className="defaulter-panel__head">
            <div>
              <p className="eyebrow">고용노동부 체불사업주 명단공개</p>
              <h4>상세 공개정보 후보</h4>
            </div>
            <strong>
              {detailData.match_status === "exact_unique"
                ? "사업장명 일치 1건"
                : detailData.match_status === "multiple"
                  ? `동일 사업장명 ${detailData.candidate_count}건`
                  : "일치 후보 없음"}
            </strong>
          </div>

          {detailData.candidates?.map((item, index) => (
            <div className="defaulter-detail" key={`${item.representative_name}-${index}`}>
              <dl>
                {item.disclosure_round && (
                  <div><dt>공개 구분</dt><dd>{item.disclosure_round}</dd></div>
                )}
                <div><dt>성명</dt><dd>{item.representative_name}</dd></div>
                <div><dt>나이</dt><dd>{item.age}</dd></div>
                <div><dt>사업장명</dt><dd>{item.workplace_name}</dd></div>
                {item.industry && (
                  <div><dt>업종</dt><dd>{item.industry}</dd></div>
                )}
                <div><dt>사업장 소재지</dt><dd>{item.workplace_address}</dd></div>
                <div><dt>사업주 주소지</dt><dd>{item.owner_address}</dd></div>
                <div><dt>체불액</dt><dd>{item.arrears_amount}원</dd></div>
              </dl>
            </div>
          ))}

          {detailData.match_status === "not_found" && (
            <p className="muted">
              현재 공개명단에서 등록된 기업명과 동일한 사업장명을 찾지 못했습니다.
            </p>
          )}

          <p className="identity-note">{detailData.identity_note}</p>
          <p className="source-note">
            출처: 고용노동부 체불사업주 명단공개 · 화면에는 공식 명단에 실제 공개된 항목만 표시합니다.
          </p>
        </div>
      )}

      {check?.error_message && (
        <p className="inline-warning">{check.error_message}</p>
      )}

      <div className="source-row">
        <span>출처: 고용24 OPEN API</span>
        <span>
          마지막 점검:{" "}
          {check
            ? new Date(check.checked_at).toLocaleString("ko-KR")
            : "아직 없음"}
        </span>
      </div>

      {historyOpen && (
        <div className="history-panel">
          <h4>점검 이력</h4>
          {company.checks?.length ? (
            <div className="history-list">
              {company.checks.map((item) => (
                <div className="history-item" key={item.id}>
                  <div>
                    <strong>{new Date(item.checked_at).toLocaleString("ko-KR")}</strong>
                    {item.changed_fields && <span className="history-change">변경 발생</span>}
                  </div>
                  <StatusBadge value={item.wage_arrears_status} />
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">저장된 점검 이력이 없습니다.</p>
          )}
        </div>
      )}
    </article>
  );
}

function App() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checkingId, setCheckingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [message, setMessage] = useState("");
  const [activeTab, setActiveTab] = useState("home");
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchData, setSearchData] = useState(null);
  const [searchError, setSearchError] = useState("");
  const [form, setForm] = useState({
    name: "",
    business_registration_number: "",
    workplace_management_number: "",
    job_posting_name: "",
  });

  const changedCount = useMemo(
    () =>
      companies.filter(
        (company) => latestCheck(company)?.changed_fields,
      ).length,
    [companies],
  );

  async function loadCompanies() {
    try {
      setCompanies(await api.listCompanies());
      setMessage("");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCompanies();
  }, []);

  async function handleCompanySearch(event) {
    event.preventDefault();
    const query = searchQuery.trim();
    if (query.length < 2) {
      setSearchError("기업명은 2글자 이상 입력해 주세요.");
      return;
    }

    setSearching(true);
    setSearchError("");
    try {
      setSearchData(await api.searchCompanies(query));
    } catch (error) {
      setSearchData(null);
      setSearchError(error.message);
    } finally {
      setSearching(false);
    }
  }

  function selectSearchResult(item) {
    if (!item.can_register) return;
    setForm((current) => ({
      ...current,
      name: item.company_name,
      business_registration_number: item.business_registration_number,
    }));
    setMessage("");
    document.getElementById("company-registration-form")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");

    try {
      const company = await api.createCompany(form);
      setForm({
        name: "",
        business_registration_number: "",
        workplace_management_number: "",
        job_posting_name: "",
      });

      setCheckingId(company.id);
      await api.runCheck(company.id);
      await loadCompanies();
      setActiveTab("companies");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setCheckingId(null);
    }
  }

  async function handleCheck(id) {
    setCheckingId(id);
    setMessage("");

    try {
      await api.runCheck(id);
      await loadCompanies();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setCheckingId(null);
    }
  }

  async function handleDelete(company) {
    const confirmed = window.confirm(
      `${company.name}을(를) 관심기업에서 삭제할까요? 저장된 점검 이력도 함께 삭제됩니다.`,
    );
    if (!confirmed) return;

    setDeletingId(company.id);
    setMessage("");

    try {
      await api.deleteCompany(company.id);
      await loadCompanies();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setDeletingId(null);
    }
  }

  const recentCompanies = companies.slice(0, 3);

  return (
    <>
      <main className="page-shell app-shell">
        {activeTab === "home" && (
          <div className="app-view">
            <header className="hero">
              <div>
                <p className="eyebrow">공공데이터 기반 구직 지원</p>
                <h1>JobSafe</h1>
                <p>
                  관심기업을 등록하면 공공데이터를 바탕으로 구직 시 참고할 위험정보를
                  반복 점검하고, 이전 결과와 달라진 내용이 있는지 관리합니다.
                </p>
              </div>
              <div className="hero__notice">
                <strong>현재 점검 항목</strong>
                <span>
                  현재 MVP는 고용24의 임금체불 명단공개 여부를 조회하고, 대상 기업은 고용노동부 공식 공개명단의 상세정보 후보까지 확인합니다.
                  미대상 결과가 기업의 전체 근무환경이나 임금 지급 상태가 안전하다는 뜻은 아닙니다.
                </span>
              </div>
            </header>

            {changedCount > 0 && (
              <section className="global-alert">
                <strong>공공 위험정보 변경이 확인된 관심기업이 {changedCount}곳 있습니다.</strong>
                <span>관심기업 목록에서 최근 점검 결과를 확인해 주세요.</span>
              </section>
            )}

            <section className="summary-grid">
              <button className="summary-card summary-card--button" type="button" onClick={() => setActiveTab("companies")}>
                <span>관심기업</span>
                <strong>{companies.length}</strong>
              </button>
              <button className="summary-card summary-card--button" type="button" onClick={() => setActiveTab("companies")}>
                <span>위험정보 변경</span>
                <strong>{changedCount}</strong>
              </button>
              <div className="summary-card">
                <span>자동 점검</span>
                <strong>{loading ? "확인 중" : "연동 준비"}</strong>
              </div>
            </section>

            <section className="panel home-actions">
              <div className="panel__head">
                <div>
                  <p className="eyebrow">빠른 실행</p>
                  <h2>무엇을 할까요?</h2>
                </div>
              </div>
              <div className="quick-actions">
                <button className="quick-action" type="button" onClick={() => setActiveTab("add")}>
                  <span className="quick-action__icon">＋</span>
                  <strong>관심기업 추가</strong>
                  <small>기업을 검색하고 첫 점검을 시작합니다.</small>
                </button>
                <button className="quick-action" type="button" onClick={() => setActiveTab("companies")}>
                  <span className="quick-action__icon">✓</span>
                  <strong>관심기업 확인</strong>
                  <small>등록 기업의 상태와 점검 이력을 확인합니다.</small>
                </button>
              </div>
            </section>

            <section className="panel">
              <div className="panel__head">
                <div>
                  <p className="eyebrow">최근 관심기업</p>
                  <h2>최근 등록 기업</h2>
                </div>
                <button className="button button--ghost" type="button" onClick={() => setActiveTab("companies")}>
                  전체 보기
                </button>
              </div>
              <div className="home-company-list">
                {!loading && recentCompanies.length === 0 ? (
                  <div className="empty-state">아직 등록된 관심기업이 없습니다.</div>
                ) : (
                  recentCompanies.map((company) => {
                    const check = latestCheck(company);
                    return (
                      <button
                        type="button"
                        className="home-company-row"
                        key={company.id}
                        onClick={() => setActiveTab("companies")}
                      >
                        <div>
                          <strong>{company.name}</strong>
                          <span>{company.business_registration_number}</span>
                        </div>
                        <StatusBadge value={check?.wage_arrears_status} />
                      </button>
                    );
                  })
                )}
              </div>
            </section>
          </div>
        )}

        {activeTab === "add" && (
          <div className="app-view">
            <section className="view-heading">
              <p className="eyebrow">기업 등록</p>
              <h1>관심기업 추가</h1>
              <p>기업명을 검색해 정확한 사업자를 선택하거나 직접 입력할 수 있습니다.</p>
            </section>

            <section className="panel">
              <div className="company-search">
                <form className="company-search__bar" onSubmit={handleCompanySearch}>
                  <input
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                    placeholder="기업명 일부 입력 (예: 삼성, 카카오)"
                    aria-label="기업 검색"
                  />
                  <button className="button button--secondary" type="submit" disabled={searching}>
                    {searching ? "검색 중..." : "기업 검색"}
                  </button>
                </form>
                <p className="form-help">
                  OpenDART에 등록된 기업을 이름 일부로 검색합니다. 결과의 정식 기업명, 사업자등록번호, 대표자와 주소를 확인한 뒤 선택할 수 있습니다.
                </p>
                {searchError && <p className="error-message">{searchError}</p>}
                {searchData?.status === "not_configured" && (
                  <p className="inline-warning">기업 검색 기능을 사용하려면 서버에 OpenDART 인증키를 설정해야 합니다.</p>
                )}
                {searchData?.status === "ok" && (
                  <div className="company-search__results">
                    {searchData.results?.length ? (
                      searchData.results.map((item) => (
                        <article className="company-search__item" key={item.corp_code}>
                          <div className="company-search__info">
                            <div className="company-search__title">
                              <strong>{item.company_name}</strong>
                              {item.stock_code && <span>{item.stock_code}</span>}
                            </div>
                            <dl>
                              <div><dt>사업자등록번호</dt><dd>{item.business_registration_number || "정보 없음"}</dd></div>
                              <div><dt>대표자</dt><dd>{item.ceo_name || "정보 없음"}</dd></div>
                              <div><dt>주소</dt><dd>{item.address || "정보 없음"}</dd></div>
                            </dl>
                          </div>
                          <button className="button" type="button" onClick={() => selectSearchResult(item)} disabled={!item.can_register}>
                            {item.can_register ? "이 기업 선택" : "사업자번호 없음"}
                          </button>
                        </article>
                      ))
                    ) : (
                      <div className="empty-state">{searchData.message || "검색 결과가 없습니다."}</div>
                    )}
                  </div>
                )}
              </div>

              <form id="company-registration-form" className="company-form" onSubmit={handleSubmit}>
                <label>
                  기업명
                  <input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="예: OO테크" />
                </label>
                <label>
                  사업자등록번호
                  <input required value={form.business_registration_number} onChange={(event) => setForm({ ...form, business_registration_number: event.target.value })} placeholder="예: 123-45-67890" />
                </label>
                <label>
                  사업장관리번호
                  <input value={form.workplace_management_number} onChange={(event) => setForm({ ...form, workplace_management_number: event.target.value })} placeholder="선택 입력" />
                </label>
                <label>
                  관심 채용공고명
                  <input value={form.job_posting_name} onChange={(event) => setForm({ ...form, job_posting_name: event.target.value })} placeholder="선택 입력" />
                </label>
                <button className="button" type="submit">등록 후 첫 점검</button>
              </form>
              <p className="form-help">
                사업자등록번호는 필수이며, 사업장관리번호는 선택 입력입니다. 등록 직후 첫 점검을 실행하고 점검 결과와 이력을 저장합니다.
              </p>
              {message && <p className="error-message">{message}</p>}
            </section>
          </div>
        )}

        {activeTab === "companies" && (
          <div className="app-view">
            <section className="view-heading">
              <p className="eyebrow">공공 위험정보 점검</p>
              <h1>관심기업 목록</h1>
              <p>내가 등록한 기업의 최신 상태와 이전 점검 이력을 확인합니다.</p>
            </section>

            {changedCount > 0 && (
              <section className="global-alert">
                <strong>변경이 확인된 관심기업이 {changedCount}곳 있습니다.</strong>
                <span>강조 표시된 기업의 최근 결과를 확인해 주세요.</span>
              </section>
            )}

            <section className="panel">
              <div className="panel__head">
                <div>
                  <p className="eyebrow">내 관심기업</p>
                  <h2>{companies.length}개 등록됨</h2>
                </div>
                <button className="button button--ghost" onClick={loadCompanies}>새로고침</button>
              </div>
              {message && <p className="error-message">{message}</p>}
              <div className="company-list">
                {!loading && companies.length === 0 && (
                  <div className="empty-state empty-state--action">
                    <strong>아직 등록된 관심기업이 없습니다.</strong>
                    <button className="button" type="button" onClick={() => setActiveTab("add")}>관심기업 추가하기</button>
                  </div>
                )}
                {companies.map((company) => (
                  <CompanyCard
                    key={company.id}
                    company={company}
                    onCheck={handleCheck}
                    onDelete={handleDelete}
                    checking={checkingId === company.id}
                    deleting={deletingId === company.id}
                  />
                ))}
              </div>
            </section>
          </div>
        )}

        {activeTab === "settings" && (
          <div className="app-view">
            <section className="view-heading">
              <p className="eyebrow">환경 설정</p>
              <h1>설정</h1>
              <p>JobSafe의 저장 방식과 자동 점검 상태를 확인합니다.</p>
            </section>

            <section className="panel settings-list">
              <div className="settings-item">
                <div>
                  <strong>관심기업 저장 범위</strong>
                  <p>현재는 이 브라우저의 식별값을 기준으로 관심기업을 분리합니다.</p>
                </div>
                <span className="settings-chip">브라우저 기준</span>
              </div>
              <div className="settings-item">
                <div>
                  <strong>공공데이터 점검</strong>
                  <p>등록된 기업은 고용24 OPEN API를 통해 임금체불 명단공개 여부를 확인합니다.</p>
                </div>
                <span className="settings-chip settings-chip--active">사용 중</span>
              </div>
              <div className="settings-item">
                <div>
                  <strong>자동 점검 및 알림</strong>
                  <p>주기 설정과 변경 알림 기능은 다음 단계에서 연결할 수 있습니다.</p>
                </div>
                <span className="settings-chip">준비 중</span>
              </div>
            </section>
          </div>
        )}
      </main>

      <nav className="bottom-nav" aria-label="주 메뉴">
        <button type="button" className={activeTab === "home" ? "bottom-nav__item is-active" : "bottom-nav__item"} onClick={() => setActiveTab("home")}>
          <span className="bottom-nav__icon" aria-hidden="true">⌂</span>
          <span>메인</span>
        </button>
        <button type="button" className={activeTab === "add" ? "bottom-nav__item is-active" : "bottom-nav__item"} onClick={() => setActiveTab("add")}>
          <span className="bottom-nav__icon" aria-hidden="true">＋</span>
          <span>기업 추가</span>
        </button>
        <button type="button" className={activeTab === "companies" ? "bottom-nav__item is-active" : "bottom-nav__item"} onClick={() => setActiveTab("companies")}>
          <span className="bottom-nav__icon" aria-hidden="true">☆</span>
          <span>관심기업</span>
          {changedCount > 0 && <span className="bottom-nav__badge">{changedCount}</span>}
        </button>
        <button type="button" className={activeTab === "settings" ? "bottom-nav__item is-active" : "bottom-nav__item"} onClick={() => setActiveTab("settings")}>
          <span className="bottom-nav__icon" aria-hidden="true">⚙</span>
          <span>설정</span>
        </button>
      </nav>
    </>
  );
}

export default App;
