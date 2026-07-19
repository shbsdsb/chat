/**
 * 网络层 — 基于 Axios 封装，对后端统一 {code, message, data} 格式自动解包。
 */
import axios from "axios";

const http = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// ── 响应拦截：统一解包 ───────────────────────────────
http.interceptors.response.use(
  (resp) => {
    const body = resp.data;

    // SSE / 非 JSON 响应直接透传
    if (resp.headers["content-type"]?.includes("text/event-stream")) {
      return body;
    }
    if (typeof body !== "object" || body === null) {
      return body;
    }

    // 统一格式 {code, message, data}
    if ("code" in body) {
      if (body.code === 0) {
        return body.data;        // 成功 → 只返回 data
      }
      // code ≠ 0 → 业务错误，抛出给调用方 catch
      const err = new Error(body.message || `业务错误 [${body.code}]`);
      err.code = body.code;
      err.data = body.data;
      return Promise.reject(err);
    }

    // 未识别格式，原样返回
    return body;
  },
  (err) => {
    // HTTP 级错误（网络断开、超时、5xx 等）
    if (err.response) {
      const msg = err.response.data?.message || `HTTP ${err.response.status}`;
      const e = new Error(msg);
      e.code = err.response.status;
      return Promise.reject(e);
    }
    if (err.code === "ECONNABORTED") {
      return Promise.reject(new Error("请求超时"));
    }
    return Promise.reject(new Error("网络异常，请检查连接"));
  }
);

export default http;
