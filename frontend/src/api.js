const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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
    throw new Error(body.detail || "요청을 처리하지 못했습니다.");
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
  deleteCompany: (id) =>
    request(`/api/companies/${id}`, {
      method: "DELETE",
    }),
};
