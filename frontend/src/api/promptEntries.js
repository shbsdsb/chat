// frontend/src/api/promptEntries.js
import http from "./request.js";

export function getEntries(presetId) {
  return http.get("/prompt-entries", { params: { preset_id: presetId } });
}

export function createEntry(presetId, name) {
  return http.post("/prompt-entries", { preset_id: presetId, name });
}

export function updateEntry(id, presetId, data) {
  return http.put(`/prompt-entries/${id}`, { preset_id: presetId, ...data });
}

export function deleteEntry(id, presetId) {
  return http.delete(`/prompt-entries/${id}`, { params: { preset_id: presetId } });
}

export function reorderEntries(presetId, ids) {
  return http.put("/prompt-entries/reorder", { preset_id: presetId, ids });
}
