/**
 * API 配置相关 API
 */
import http from "./request.js";

export function list() {
  return http.get("/settings");
}

export function create(data) {
  return http.post("/settings", data);
}

export function update(id, data) {
  return http.put(`/settings/${id}`, data);
}

export function remove(id) {
  return http.delete(`/settings/${id}`);
}

export function test(id) {
  return http.post(`/settings/${id}/test`);
}

export function setDefault(id) {
  return http.put(`/settings/${id}/default`);
}

export function fetchModels(apiUrl, apiKey) {
  return http.get("/settings/models", {
    params: { api_url: apiUrl, api_key: apiKey },
  });
}
