/**
 * CSS 预设 API
 */
import http from "./request.js";

export function list() {
  return http.get("/css-presets");
}

export function create(data) {
  return http.post("/css-presets", data);
}

export function update(id, data) {
  return http.put(`/css-presets/${id}`, data);
}

export function remove(id) {
  return http.delete(`/css-presets/${id}`);
}

export function setDefault(id) {
  return http.put(`/css-presets/${id}/default`);
}
