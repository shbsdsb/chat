/**
 * SSE 流式请求辅助函数
 *
 * 用法：
 *   const es = sse("/conversations/:id/chat", {
 *     method: "POST",
 *     body: JSON.stringify({ content: "你好" }),
 *     onMessage({ delta, done, stopped }) { ... },
 *     onError(err) { ... },
 *   });
 *   // 停止生成：
 *   es.close();
 */

import { useAlertStore } from "@/stores/alert";

const HTTP_STATUS_MSG = {
  400: "请求参数有误，请检查输入内容",
  401: "认证失败，请检查 API Key 是否正确",
  402: "账户余额不足，请充值后重试",
  403: "没有访问权限，请检查 API Key 权限",
  404: "请求的资源不存在",
  405: "请求方法不被允许",
  408: "请求超时，请检查网络后重试",
  409: "资源冲突，请刷新后重试",
  422: "请求参数验证失败",
  429: "请求过于频繁，请稍后重试",
  500: "服务器内部错误，请稍后重试",
  502: "网关错误，服务可能正在重启",
  503: "服务暂时不可用，请稍后重试",
  504: "网关超时，请稍后重试",
};

function _alert() {
  try {
    return useAlertStore();
  } catch {
    return null;
  }
}

export function sse(url, { method = "POST", body, headers = {}, onMessage, onError, onDone } = {}) {
  const controller = new AbortController();
  const signal = controller.signal;

  fetch("/api" + url, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body,
    signal,
  })
    .then(async (resp) => {
      if (!resp.ok) {
        const status = resp.status;
        let msg;
        try {
          const data = await resp.json();
          msg = data.message || data.error;
        } catch {
          // 无法解析 JSON
        }
        if (!msg) {
          msg = HTTP_STATUS_MSG[status] || `请求失败（HTTP ${status}）`;
        }
        const alertStore = _alert();
        if (alertStore) {
          alertStore.error("请求失败", msg);
        }
        throw new Error(msg);
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const chunk = JSON.parse(line.slice(6));
              onMessage?.(chunk);
            } catch {
              // 忽略解析失败的行
            }
          }
        }
      }
      onDone?.();
    })
    .catch((err) => {
      if (err.name === "AbortError") return;
      onError?.(err);
    });

  // 返回关闭函数
  return { close: () => controller.abort() };
}
