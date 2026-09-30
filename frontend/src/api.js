const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const FIELD_LABELS = {
  name: "기업명",
  business_registration_number: "사업자등록번호",
  workplace_management_number: "사업장관리번호",
  job_posting_name: "관심 채용공고명",
};

function formatErrorDetail(detail) {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const field = item?.loc?.at?.(-1);
        const label = FIELD_LABELS[field] || field || "입력값";
        return `${label}: ${item?.msg || "입력값을 확인해 주세요."}`;
      })
      .join(" / ");
  }

  return "요청을 처리하지 못했습니다.";
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(formatErrorDetail(body.detail));
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const api = {
  listCompanies: () => request("/api/companies"),
  createCompany: (payload) =>
    request("/api/companies", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  runCheck: (id) =>
    request(`/api/companies/${id}/checks`, {
      method: "POST",
    }),
  getDefaulterDetails: (id) => request(`/api/companies/${id}/defaulter-details`),
  deleteCompany: (id) =>
    request(`/api/companies/${id}`, {
      method: "DELETE",
    }),
};
