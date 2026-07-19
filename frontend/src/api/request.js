/**
 * 网络层 — 基于 Axios 封装，对后端统一 {code, message, data} 格式自动解包。
 */
import axios from "axios";
import { useAlertStore } from "@/stores/alert";

const http = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// ── HTTP 状态码 → 中文提示 ──────────────────────────
const HTTP_STATUS_MSG = {
  400: "请求参数有误，请检查输入内容",
  401: "认证失败，请检查 API Key 是否正确",
  402: "账户余额不足，请充值后重试",
  403: "没有访问权限，请检查 API Key 权限",
  404: "请求的资源不存在",
  405: "请求方法不被允许",
  408: "请求超时，请检查网络后重试",
  409: "资源冲突，请刷新后重试",
  410: "请求的资源已被永久删除",
  413: "请求体过大",
  415: "不支持的媒体类型",
  422: "请求参数验证失败",
  429: "请求过于频繁，请稍后重试",
  500: "服务器内部错误，请稍后重试",
  502: "网关错误，服务可能正在重启",
  503: "服务暂时不可用，请稍后重试",
  504: "网关超时，请稍后重试",
};

function getHttpStatusMessage(status) {
  const msg = HTTP_STATUS_MSG[status];
  return msg ? `${msg}（${status}）` : `请求失败（HTTP ${status}）`;
}

// ── 懒加载 alert store（确保 Pinia 已激活时才调用） ──
function _alert() {
  try {
    return useAlertStore();
  } catch {
    return null;
  }
}

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
      // code ≠ 0 → 业务错误，抛出给调用方 catch（不弹窗）
      const err = new Error(body.message || `业务错误 [${body.code}]`);
      err.code = body.code;
      err.data = body.data;
      return Promise.reject(err);
    }

    // 未识别格式，原样返回
    return body;
  },
  (err) => {
    // HTTP 级错误 → 弹出 Alert 提醒
    if (err.response) {
      const status = err.response.status;
      const msg = getHttpStatusMessage(status);
      const alertStore = _alert();
      if (alertStore) {
        alertStore.error("请求失败", msg);
      }
      const e = new Error(msg);
      e.code = status;
      return Promise.reject(e);
    }
    if (err.code === "ECONNABORTED") {
      const alertStore = _alert();
      if (alertStore) {
        alertStore.warning("请求超时", "请求超时，请检查网络连接后重试");
      }
      return Promise.reject(new Error("请求超时"));
    }
    const alertStore = _alert();
    if (alertStore) {
      alertStore.warning("网络异常", "网络连接失败，请检查网络设置");
    }
    return Promise.reject(new Error("网络异常，请检查连接"));
  }
);

export default http;
