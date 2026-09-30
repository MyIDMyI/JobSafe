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

  return <p className="muted">아직 공공 위험정보 점검을 실행하지 않았습니다.</p>;
}

function CompanyCard({ company, onCheck, onDelete, checking, deleting }) {
  const [historyOpen, setHistoryOpen] = useState(false);
  const check = latestCheck(company);
  const hasChange = Boolean(check?.changed_fields);

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

  return (
    <main className="page-shell">
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
            현재 MVP는 고용24의 임금체불 명단공개 정보를 활용합니다.
            '현재 공개정보 없음'은 기업의 전체 근무환경이나 임금 지급 상태가 안전하다는 뜻이 아닙니다.
          </span>
        </div>
      </header>

      {changedCount > 0 && (
        <section className="global-alert">
          <strong>공공 위험정보 변경이 확인된 관심기업이 {changedCount}곳 있습니다.</strong>
          <span>아래 강조된 기업의 최근 점검 결과를 확인해 주세요.</span>
        </section>
      )}

      <section className="summary-grid">
        <div className="summary-card">
          <span>관심기업</span>
          <strong>{companies.length}</strong>
        </div>
        <div className="summary-card">
          <span>위험정보 변경</span>
          <strong>{changedCount}</strong>
        </div>
        <div className="summary-card">
          <span>자동 점검</span>
          <strong>{loading ? "확인 중" : "연동 준비"}</strong>
        </div>
      </section>

      <section className="panel">
        <div className="panel__head">
          <div>
            <p className="eyebrow">기업 등록</p>
            <h2>관심기업 추가</h2>
          </div>
        </div>

        <form className="company-form" onSubmit={handleSubmit}>
          <label>
            기업명
            <input
              required
              value={form.name}
              onChange={(event) =>
                setForm({ ...form, name: event.target.value })
              }
              placeholder="예: OO테크"
            />
          </label>

          <label>
            사업자등록번호
            <input
              required
              value={form.business_registration_number}
              onChange={(event) =>
                setForm({
                  ...form,
                  business_registration_number: event.target.value,
                })
              }
              placeholder="예: 123-45-67890"
            />
          </label>

          <label>
            사업장관리번호
            <input
              value={form.workplace_management_number}
              onChange={(event) =>
                setForm({
                  ...form,
                  workplace_management_number: event.target.value,
                })
              }
              placeholder="선택 입력"
            />
          </label>

          <label>
            관심 채용공고명
            <input
              value={form.job_posting_name}
              onChange={(event) =>
                setForm({ ...form, job_posting_name: event.target.value })
              }
              placeholder="선택 입력"
            />
          </label>

          <button className="button" type="submit">
            등록 후 첫 점검
          </button>
        </form>

        <p className="form-help">
          사업자등록번호는 필수이며, 사업장관리번호는 선택 입력입니다. 등록 직후 첫 점검을 실행하고 점검 결과와 이력을 저장합니다.
        </p>

        {message && <p className="error-message">{message}</p>}
      </section>

      <section className="panel">
        <div className="panel__head">
          <div>
            <p className="eyebrow">공공 위험정보 점검</p>
            <h2>관심기업 목록</h2>
          </div>
          <button className="button button--ghost" onClick={loadCompanies}>
            새로고침
          </button>
        </div>

        <div className="company-list">
          {!loading && companies.length === 0 && (
            <div className="empty-state">
              아직 등록된 관심기업이 없습니다.
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
    </main>
  );
}

export default App;
