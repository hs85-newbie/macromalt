/**
 * macromalt API 클라이언트
 * openapi.yaml 계약서 기준 구현
 */

const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://macromalt-production.up.railway.app';

// ── 토큰 관리 ─────────────────────────────────────────────────

function getAccessToken() {
  return localStorage.getItem('access_token');
}

function getRefreshToken() {
  return localStorage.getItem('refresh_token');
}

function setTokens(access_token, refresh_token) {
  localStorage.setItem('access_token', access_token);
  if (refresh_token) {
    localStorage.setItem('refresh_token', refresh_token);
  }
}

function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

function redirectToLogin() {
  clearTokens();
  const isInApp = window.location.pathname.startsWith('/app/');
  if (isInApp) {
    window.location.href = '/app/login.html';
  } else {
    window.location.href = '/app/login.html';
  }
}

// ── 핵심 fetch 래퍼 ───────────────────────────────────────────

/**
 * JWT Bearer 헤더 포함 fetch
 * 401 시 자동 refresh → 실패 시 login 리다이렉트
 * refresh 성공 시 원래 요청 재시도
 */
async function apiFetch(path, options = {}) {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  // 401: 토큰 갱신 시도
  if (response.status === 401) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      // 원래 요청 재시도
      headers['Authorization'] = `Bearer ${getAccessToken()}`;
      response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
      });
    } else {
      redirectToLogin();
      throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
    }
  }

  return response;
}

async function tryRefreshToken() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const res = await fetch(`${API_BASE}/api/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

async function parseResponse(res) {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

// ── 인증 ──────────────────────────────────────────────────────

async function register(email, password, name) {
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name }),
  });
  const data = await parseResponse(res);
  if (!res.ok) {
    throw new Error(data?.detail || '회원가입에 실패했습니다.');
  }
  setTokens(data.access_token, data.refresh_token);
  return data;
}

async function login(email, password) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await parseResponse(res);
  if (!res.ok) {
    throw new Error(data?.detail || '이메일 또는 비밀번호가 올바르지 않습니다.');
  }
  setTokens(data.access_token, data.refresh_token);
  return data;
}

async function logout() {
  clearTokens();
  window.location.href = '/index.html';
}

// ── 사용자 ────────────────────────────────────────────────────

async function getMe() {
  const res = await apiFetch('/api/users/me');
  const data = await parseResponse(res);
  if (!res.ok) {
    throw new Error(data?.detail || '사용자 정보를 불러오지 못했습니다.');
  }
  return data;
}

// ── 설정: API 키 ──────────────────────────────────────────────

async function saveApiKey(provider, apiKey) {
  const res = await apiFetch('/api/settings/api-keys', {
    method: 'POST',
    body: JSON.stringify({ provider, api_key: apiKey }),
  });
  const data = await parseResponse(res);
  if (!res.ok) {
    throw new Error(data?.detail || 'API 키 저장에 실패했습니다.');
  }
  return data;
}

async function getApiKeys() {
  const res = await apiFetch('/api/settings/api-keys');
  const data = await parseResponse(res);
  if (!res.ok) {
    throw new Error(data?.detail || 'API 키 목록을 불러오지 못했습니다.');
  }
  return data;
}

async function testApiKey(provider) {
  const res = await apiFetch(`/api/settings/api-keys/${provider}/test`, {
    method: 'POST',
  });
  const data = await parseResponse(res);
  if (!res.ok) {
    throw new Error(data?.detail || 'API 키 테스트에 실패했습니다.');
  }
  return data;
}

// ── 설정: WordPress ───────────────────────────────────────────

async function saveWpSettings(data) {
  const res = await apiFetch('/api/settings/wordpress', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  const result = await parseResponse(res);
  if (!res.ok) {
    throw new Error(result?.detail || 'WordPress 설정 저장에 실패했습니다.');
  }
  return result;
}

async function getWpSettings() {
  const res = await apiFetch('/api/settings/wordpress');
  const data = await parseResponse(res);
  if (!res.ok) {
    throw new Error(data?.detail || 'WordPress 설정을 불러오지 못했습니다.');
  }
  return data;
}

async function testWpConnection() {
  const res = await apiFetch('/api/settings/wordpress/test', {
    method: 'POST',
  });
  const data = await parseResponse(res);
  if (!res.ok) {
    throw new Error(data?.detail || 'WordPress 연결 테스트에 실패했습니다.');
  }
  return data;
}

// ── 설정: 파이프라인 ──────────────────────────────────────────

async function getPipelineSettings() {
  const res = await apiFetch('/api/settings/pipeline');
  const data = await parseResponse(res);
  if (!res.ok) {
    throw new Error(data?.detail || '파이프라인 설정을 불러오지 못했습니다.');
  }
  return data;
}

async function updatePipelineSettings(data) {
  const res = await apiFetch('/api/settings/pipeline', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  const result = await parseResponse(res);
  if (!res.ok) {
    throw new Error(result?.detail || '파이프라인 설정 저장에 실패했습니다.');
  }
  return result;
}

// ── 파이프라인 실행 ────────────────────────────────────────────

async function executePipeline(slot) {
  const res = await apiFetch('/api/pipeline/execute', {
    method: 'POST',
    body: JSON.stringify({ slot: slot || 'morning' }),
  });
  const data = await parseResponse(res);
  if (res.status === 402) {
    throw new Error('Pro 플랜에서만 파이프라인을 실행할 수 있습니다.');
  }
  if (res.status === 409) {
    throw new Error('파이프라인이 이미 실행 중입니다.');
  }
  if (!res.ok) {
    throw new Error(data?.detail || '파이프라인 실행에 실패했습니다.');
  }
  return data;
}

async function getRuns(limit = 20, offset = 0) {
  const res = await apiFetch(`/api/pipeline/runs?limit=${limit}&offset=${offset}`);
  const data = await parseResponse(res);
  if (!res.ok) {
    throw new Error(data?.detail || '실행 이력을 불러오지 못했습니다.');
  }
  return data;
}

async function getPosts(limit = 20, offset = 0) {
  const res = await apiFetch(`/api/pipeline/posts?limit=${limit}&offset=${offset}`);
  const data = await parseResponse(res);
  if (!res.ok) {
    throw new Error(data?.detail || '발행 포스트 목록을 불러오지 못했습니다.');
  }
  return data;
}

// ── 결제 ──────────────────────────────────────────────────────

async function getSubscription() {
  const res = await apiFetch('/api/payments/subscription');
  const data = await parseResponse(res);
  if (!res.ok) {
    throw new Error(data?.detail || '구독 정보를 불러오지 못했습니다.');
  }
  return data;
}

async function readyPayment(plan = 'pro', amount = 49900) {
  const res = await apiFetch('/api/payments/ready', {
    method: 'POST',
    body: JSON.stringify({ plan, amount }),
  });
  const data = await parseResponse(res);
  if (!res.ok) {
    throw new Error(data?.detail || '결제 준비에 실패했습니다.');
  }
  return data;
}

async function cancelSubscription() {
  const res = await apiFetch('/api/payments/subscription/cancel', {
    method: 'POST',
  });
  const data = await parseResponse(res);
  if (!res.ok) {
    throw new Error(data?.detail || '구독 해지에 실패했습니다.');
  }
  return data;
}

// ── Mock 데이터 (API 미연결 시 UI 테스트용) ────────────────────

const MOCK = {
  user: {
    id: 1,
    email: 'demo@macromalt.com',
    name: '홍길동',
    plan: 'free',
    created_at: '2026-01-15T09:00:00Z',
  },
  apiKeys: [
    { provider: 'openai',  is_valid: true,  last_tested_at: '2026-03-25T10:00:00Z' },
    { provider: 'gemini',  is_valid: true,  last_tested_at: '2026-03-25T10:01:00Z' },
    { provider: 'dart',    is_valid: false, last_tested_at: null },
    { provider: 'bok',     is_valid: false, last_tested_at: null },
    { provider: 'fred',    is_valid: false, last_tested_at: null },
    { provider: 'krx',     is_valid: false, last_tested_at: null },
  ],
  runs: [
    { id: 5, status: 'success', slot: 'morning', triggered_by: 'manual', started_at: '2026-03-26T09:00:00Z', finished_at: '2026-03-26T09:12:00Z', cost_usd: 0.18, cost_krw: 246 },
    { id: 4, status: 'success', slot: 'evening', triggered_by: 'schedule', started_at: '2026-03-25T18:00:00Z', finished_at: '2026-03-25T18:11:00Z', cost_usd: 0.17, cost_krw: 232 },
    { id: 3, status: 'failed',  slot: 'morning', triggered_by: 'schedule', started_at: '2026-03-25T09:00:00Z', finished_at: '2026-03-25T09:02:00Z', cost_usd: 0.01, cost_krw: 14 },
    { id: 2, status: 'success', slot: 'evening', triggered_by: 'manual',   started_at: '2026-03-24T18:00:00Z', finished_at: '2026-03-24T18:13:00Z', cost_usd: 0.21, cost_krw: 287 },
    { id: 1, status: 'success', slot: 'morning', triggered_by: 'schedule', started_at: '2026-03-24T09:00:00Z', finished_at: '2026-03-24T09:10:00Z', cost_usd: 0.16, cost_krw: 219 },
  ],
  posts: [
    { id: 5, wp_post_id: 1205, wp_post_url: 'https://example.com/macro-outlook-2026', title: '2026년 3월 매크로 전망: 미국 경기침체 가능성과 달러 약세', category: '분석', published_at: '2026-03-26T09:12:00Z' },
    { id: 4, wp_post_id: 1204, wp_post_url: 'https://example.com/kospi-outlook', title: 'KOSPI 2600 돌파 가능성 — 외국인 수급과 환율 분석', category: '픽', published_at: '2026-03-25T18:11:00Z' },
    { id: 3, wp_post_id: 1203, wp_post_url: 'https://example.com/fed-rate-cut', title: 'Fed 금리 인하 시나리오 3가지와 한국 금융시장 영향', category: '분석', published_at: '2026-03-24T18:13:00Z' },
    { id: 2, wp_post_id: 1202, wp_post_url: 'https://example.com/china-stimulus', title: '중국 경기부양책 효과와 원자재 시장 파급 분석', category: '분석', published_at: '2026-03-24T09:10:00Z' },
    { id: 1, wp_post_id: 1201, wp_post_url: 'https://example.com/dollar-index', title: '달러 인덱스 하락 국면, 신흥국 자산에 미치는 영향', category: '픽', published_at: '2026-03-23T18:08:00Z' },
  ],
};

// ── 유틸리티 ──────────────────────────────────────────────────

function isLoggedIn() {
  return !!getAccessToken();
}

function formatDate(isoStr) {
  if (!isoStr) return '—';
  const d = new Date(isoStr);
  return d.toLocaleString('ko-KR', { timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function formatKRW(krw) {
  if (krw === null || krw === undefined) return '—';
  return `₩${krw.toLocaleString('ko-KR')}`;
}

window.API = {
  API_BASE,
  register,
  login,
  logout,
  getMe,
  saveApiKey,
  getApiKeys,
  testApiKey,
  saveWpSettings,
  getWpSettings,
  testWpConnection,
  getPipelineSettings,
  updatePipelineSettings,
  executePipeline,
  getRuns,
  getPosts,
  getSubscription,
  readyPayment,
  cancelSubscription,
  isLoggedIn,
  formatDate,
  formatKRW,
  MOCK,
};
