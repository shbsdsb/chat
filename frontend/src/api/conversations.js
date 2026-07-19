/**
 * 会话相关 API
 */
import http from "./request.js";

export function list() {
  return http.get("/conversations");
}

export function create(title) {
  return http.post("/conversations", { title });
}

export function detail(id) {
  return http.get(`/conversations/${id}`);
}

export function remove(id) {
  return http.delete(`/conversations/${id}`);
}

// chat / regenerate 为 SSE 流式，使用 sse() 工具函数调用

export function rename(id, title) {
  return http.put(`/conversations/${id}`, { title });
}

export function editMessage(convId, msgId, content) {
  return http.put(`/conversations/${convId}/messages/${msgId}`, { content });
}

export function stopGeneration(convId) {
  return http.post(`/conversations/${convId}/stop`);
}
