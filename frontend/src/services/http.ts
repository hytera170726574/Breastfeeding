const API_BASE_URL = '/api';

let isHandlingUnauthorized = false;

export interface ApiRequestOptions extends RequestInit {
  auth?: boolean;
}

interface ApiEnvelope<T> {
  data?: T;
  message?: string;
  [key: string]: unknown;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { auth = true, headers, ...rest } = options;
  const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null;

  const finalHeaders = new Headers(headers as HeadersInit);
  if (!finalHeaders.has('Content-Type')) {
    finalHeaders.set('Content-Type', 'application/json');
  }

  if (auth && token) {
    finalHeaders.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: finalHeaders,
  });

  const isJson = response.headers.get('content-type')?.includes('application/json');
  const payload = isJson ? ((await response.json()) as ApiEnvelope<T>) : null;

  if (!response.ok) {
    const message = payload?.message || `请求失败: ${response.status}`;
    if (response.status === 401 && typeof window !== 'undefined' && !isHandlingUnauthorized) {
      isHandlingUnauthorized = true;
      // 统一处理过期或未授权状态：清理本地认证信息并回到登录页
      localStorage.removeItem('authToken');
      localStorage.removeItem('currentBabyId');
      window.location.replace('/');
    }
    throw new ApiError(response.status, message);
  }

  if (!payload) {
    throw new ApiError(response.status, '响应格式不正确，未返回JSON');
  }

  return (payload.data ?? (payload as unknown as T)) as T;
}