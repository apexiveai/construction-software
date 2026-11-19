const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

async function readResponse(response) {
  const body = await response.text();
  if (!body) return null;

  try {
    return JSON.parse(body);
  } catch {
    return body;
  }
}

function getErrorMessage(response, body) {
  const detail = body && typeof body === "object" ? body.detail : null;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
  }
  if (typeof body === "string" && body) return body;
  return `Request failed (${response.status})`;
}

async function send(path, accessToken, options) {
  const headers = new Headers(options.headers || {});
  let body = options.body;

  if (body !== undefined && !(body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(body);
  }
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

  return fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    body,
  });
}

export async function apiRequest(path, session, options = {}) {
  let response = await send(path, session?.access_token, options);
  let data = await readResponse(response);

  if (
    response.status === 401 &&
    session?.refresh_token &&
    path !== "/auth/login" &&
    path !== "/auth/refresh"
  ) {
    const refreshResponse = await send("/auth/refresh", null, {
      method: "POST",
      body: { refresh_token: session.refresh_token },
    });
    const refreshedSession = await readResponse(refreshResponse);
    if (!refreshResponse.ok) {
      throw new Error(getErrorMessage(refreshResponse, refreshedSession));
    }

    session.onTokens?.(refreshedSession);
    response = await send(path, refreshedSession.access_token, options);
    data = await readResponse(response);
  }

  if (!response.ok) throw new Error(getErrorMessage(response, data));
  return data;
}
