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
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

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
