/**
 * Typed API client wrapper.
 *
 * 目标：让 GET/POST/PUT/DELETE 调用直接按 OpenAPI 推断请求参数与响应类型。
 * 用法示例：
 *
 *   import { api } from "../api/typedClient";
 *
 *   // GET 无参
 *   const overview = await api.get("/api/gaokao/data-overview");
 *
 *   // GET 带 query
 *   const students = await api.get("/api/students", { query: { page: 1, page_size: 50 } });
 *
 *   // POST JSON body
 *   const created = await api.post("/api/students", { body: payload });
 *
 * 旧的 apiRequest / uploadFile / openFile 仍然可用；新页面请优先使用 typed 版本。
 */

import type { paths } from "../types/api.generated";

type HttpMethod = "get" | "post" | "put" | "delete" | "patch";

type PathsWithMethod<M extends HttpMethod> = {
  [P in keyof paths]: paths[P] extends Record<M, unknown> ? P : never;
}[keyof paths];

type OpFor<P extends keyof paths, M extends HttpMethod> = paths[P] extends Record<
  M,
  infer Op
>
  ? Op
  : never;

type QueryOf<Op> = Op extends { parameters: { query?: infer Q } } ? Q : undefined;
type PathParamsOf<Op> = Op extends { parameters: { path?: infer P } } ? P : undefined;

type JsonBodyOf<Op> = Op extends {
  requestBody: { content: { "application/json": infer B } };
}
  ? B
  : Op extends {
        requestBody?: { content: { "application/json": infer B } };
      }
    ? B | undefined
    : undefined;

type ResponseOf<Op> = Op extends {
  responses: { 200: { content: { "application/json": infer R } } };
}
  ? R
  : Op extends {
        responses: { 201: { content: { "application/json": infer R } } };
      }
    ? R
    : void;

type RequiredKeys<T> = {
  [K in keyof T]-?: undefined extends T[K] ? never : K;
}[keyof T];

type IsEmpty<T> = [T] extends [undefined]
  ? true
  : [T] extends [never]
    ? true
    : keyof T extends never
      ? true
      : false;

type HasRequired<T> = IsEmpty<T> extends true ? false : RequiredKeys<T> extends never ? false : true;

type BaseOptions<Op> = {
  query?: QueryOf<Op>;
  path?: PathParamsOf<Op>;
  body?: JsonBodyOf<Op>;
  signal?: AbortSignal;
  headers?: Record<string, string>;
};

// RequestOptions 必选化：如果 path/body/query 里有 required 字段，就强制调用方传。
type RequestOptions<Op> = (HasRequired<PathParamsOf<Op>> extends true
  ? { path: PathParamsOf<Op> }
  : { path?: PathParamsOf<Op> }) &
  (HasRequired<QueryOf<Op>> extends true ? { query: QueryOf<Op> } : { query?: QueryOf<Op> }) &
  (HasRequired<JsonBodyOf<Op>> extends true ? { body: JsonBodyOf<Op> } : { body?: JsonBodyOf<Op> }) & {
    signal?: AbortSignal;
    headers?: Record<string, string>;
  };

type MaybeRequestOptions<Op> =
  HasRequired<BaseOptions<Op>> extends true ? [RequestOptions<Op>] : [RequestOptions<Op>?];

function buildUrl<P extends string>(template: P, path?: Record<string, unknown>, query?: Record<string, unknown>): string {
  let url: string = template;
  if (path) {
    for (const [key, value] of Object.entries(path)) {
      url = url.replace(`{${key}}`, encodeURIComponent(String(value)));
    }
  }
  if (query && Object.keys(query).length > 0) {
    const params = new URLSearchParams();
    for (const [key, raw] of Object.entries(query)) {
      if (raw === undefined || raw === null) continue;
      if (Array.isArray(raw)) {
        for (const item of raw) {
          if (item === undefined || item === null) continue;
          params.append(key, String(item));
        }
      } else {
        params.append(key, String(raw));
      }
    }
    const queryString = params.toString();
    if (queryString) {
      url += (url.includes("?") ? "&" : "?") + queryString;
    }
  }
  return url;
}

async function requestJson<Op>(
  method: HttpMethod,
  pathTemplate: string,
  options: RequestOptions<Op> | undefined,
): Promise<ResponseOf<Op>> {
  const init: RequestInit = { method: method.toUpperCase() };
  const headers = new Headers(options?.headers);
  if (options && "body" in options && options.body !== undefined) {
    headers.set("Content-Type", headers.get("Content-Type") ?? "application/json");
    init.body = JSON.stringify(options.body);
  }
  init.headers = headers;
  if (options?.signal) {
    init.signal = options.signal;
  }

  const url = buildUrl(
    pathTemplate,
    options?.path as Record<string, unknown> | undefined,
    options?.query as Record<string, unknown> | undefined,
  );

  const response = await fetch(url, init);
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `请求失败: ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as ResponseOf<Op>;
  }
  return (await response.json()) as ResponseOf<Op>;
}

export const api = {
  get<P extends PathsWithMethod<"get">>(
    pathTemplate: P,
    ...args: MaybeRequestOptions<OpFor<P, "get">>
  ): Promise<ResponseOf<OpFor<P, "get">>> {
    return requestJson<OpFor<P, "get">>(
      "get",
      pathTemplate,
      args[0] as RequestOptions<OpFor<P, "get">> | undefined,
    );
  },

  post<P extends PathsWithMethod<"post">>(
    pathTemplate: P,
    ...args: MaybeRequestOptions<OpFor<P, "post">>
  ): Promise<ResponseOf<OpFor<P, "post">>> {
    return requestJson<OpFor<P, "post">>(
      "post",
      pathTemplate,
      args[0] as RequestOptions<OpFor<P, "post">> | undefined,
    );
  },

  put<P extends PathsWithMethod<"put">>(
    pathTemplate: P,
    ...args: MaybeRequestOptions<OpFor<P, "put">>
  ): Promise<ResponseOf<OpFor<P, "put">>> {
    return requestJson<OpFor<P, "put">>(
      "put",
      pathTemplate,
      args[0] as RequestOptions<OpFor<P, "put">> | undefined,
    );
  },

  delete<P extends PathsWithMethod<"delete">>(
    pathTemplate: P,
    ...args: MaybeRequestOptions<OpFor<P, "delete">>
  ): Promise<ResponseOf<OpFor<P, "delete">>> {
    return requestJson<OpFor<P, "delete">>(
      "delete",
      pathTemplate,
      args[0] as RequestOptions<OpFor<P, "delete">> | undefined,
    );
  },

  patch<P extends PathsWithMethod<"patch">>(
    pathTemplate: P,
    ...args: MaybeRequestOptions<OpFor<P, "patch">>
  ): Promise<ResponseOf<OpFor<P, "patch">>> {
    return requestJson<OpFor<P, "patch">>(
      "patch",
      pathTemplate,
      args[0] as RequestOptions<OpFor<P, "patch">> | undefined,
    );
  },
};

export type { paths };
