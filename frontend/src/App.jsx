import { useEffect, useMemo, useState } from "react";

import { api } from "./api";

const STATUS_LABELS = {
  yes: "명단공개 대상",
  no: "명단공개 미대상",
  error: "조회 실패",
  not_checked: "미조회",
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

function CompanyCard({ company, onCheck, checking }) {
  const check = latestCheck(company);

  return (
    <article className="company-card">
      <div className="company-card__head">
        <div>
          <p className="eyebrow">관심기업</p>
          <h3>{company.name}</h3>
          <p className="muted">
            {company.job_posting_name || "채용공고명 미등록"}
          </p>
        </div>
        <button
          className="button button--secondary"
          onClick={() => onCheck(company.id)}
          disabled={checking}
        >
          {checking ? "조회 중..." : "지금 점검"}
        </button>
      </div>

      <div className="status-grid status-grid--single">
        <div>
          <span>임금체불 명단공개 사업주 여부</span>
          <StatusBadge value={check?.wage_arrears_status} />
        </div>
      </div>

      {check?.error_message && (
        <p className="inline-warning">{check.error_message}</p>
      )}

      <div className="company-card__footer">
        <span>
          마지막 점검:{" "}
          {check
            ? new Date(check.checked_at).toLocaleString("ko-KR")
            : "아직 없음"}
        </span>
        {check?.changed_fields && <strong>이전 점검과 결과가 달라졌습니다.</strong>}
      </div>
    </article>
  );
}

function App() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checkingId, setCheckingId] = useState(null);
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
      await api.createCompany(form);
      setForm({
        name: "",
        business_registration_number: "",
        workplace_management_number: "",
        job_posting_name: "",
      });
      await loadCompanies();
    } catch (error) {
      setMessage(error.message);
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

  return (
    <main className="page-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">공공데이터 기반 구직 지원</p>
          <h1>JobSafe</h1>
          <p>
            관심기업을 등록해 고용24의 임금체불 명단공개 사업주 여부를
            반복해서 확인하고, 이전 점검과 달라진 내용이 있는지 관리합니다.
          </p>
        </div>

        <div className="hero__notice">
          <strong>꼭 확인해 주세요</strong>
          <span>
            '미대상'은 현재 조회 기준으로 명단공개 대상이 아니라는 뜻이며,
            기업의 전체 근무환경이나 임금 지급 상태를 보장하는 결과는 아닙니다.
          </span>
        </div>
      </header>

      <section className="summary-grid">
        <div className="summary-card">
          <span>관심기업</span>
          <strong>{companies.length}</strong>
        </div>
        <div className="summary-card">
          <span>결과 변경</span>
          <strong>{changedCount}</strong>
        </div>
        <div className="summary-card">
          <span>화면 상태</span>
          <strong>{loading ? "불러오는 중" : "준비됨"}</strong>
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
              required
              value={form.workplace_management_number}
              onChange={(event) =>
                setForm({
                  ...form,
                  workplace_management_number: event.target.value,
                })
              }
              placeholder="고용24 조회에 필요한 번호"
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
            등록
          </button>
        </form>

        <p className="form-help">
          임금체불 명단공개 사업주 여부 API는 사업자등록번호와
          사업장관리번호를 모두 사용해 조회합니다.
        </p>

        {message && <p className="error-message">{message}</p>}
      </section>

      <section className="panel">
        <div className="panel__head">
          <div>
            <p className="eyebrow">반복 점검 대상</p>
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
              checking={checkingId === company.id}
            />
          ))}
        </div>
      </section>
    </main>
  );
}

export default App;
