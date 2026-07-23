/**
 * 参数预设 API
 */
import http from "./request.js";

export function list() {
  return http.get("/param-presets");
}

export function create(data) {
  return http.post("/param-presets", data);
}

export function update(id, data) {
  return http.put(`/param-presets/${id}`, data);
}

export function remove(id) {
  return http.delete(`/param-presets/${id}`);
}

export function setDefault(id) {
  return http.put(`/param-presets/${id}/default`);
}
