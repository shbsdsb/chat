/**
 * 预设 API（合并参数预设 + 提示词条目）
 */
import http from "./request.js";

export function list() {
  return http.get("/presets");
}

export function get(id) {
  return http.get(`/presets/${id}`);
}

export function create(data) {
  return http.post("/presets", data);
}

export function update(id, data) {
  return http.put(`/presets/${id}`, data);
}

export function remove(id) {
  return http.delete(`/presets/${id}`);
}

export function setDefault(id) {
  return http.put(`/presets/${id}/default`);
}
