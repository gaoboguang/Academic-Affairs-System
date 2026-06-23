import { getCsrfToken, isUnsafeMethod } from "./authSession";

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const csrfToken = getCsrfToken();
  if (csrfToken && isUnsafeMethod(init?.method)) {
    headers.set("X-CSRF-Token", csrfToken);
  }

  const response = await fetch(path, {
    ...init,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `请求失败: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function uploadFile<T>(
  path: string,
  file: File,
  extraFields: Record<string, string> = {},
): Promise<T> {
  const formData = new FormData();
  formData.append("file", file);
  Object.entries(extraFields).forEach(([key, value]) => {
    formData.append(key, value);
  });

  const response = await fetch(path, {
    method: "POST",
    body: formData,
    headers: getCsrfToken() ? { "X-CSRF-Token": getCsrfToken() as string } : undefined,
    credentials: "include",
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `上传失败: ${response.status}`);
  }

  return (await response.json()) as T;
}

export function openFile(path: string): void {
  window.open(path, "_blank", "noopener,noreferrer");
}
