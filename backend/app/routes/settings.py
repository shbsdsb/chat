import uuid
from datetime import datetime, timezone
from flask import request
from app.routes import api_bp
from app.storage import (
    get_setting, list_settings_raw, create_setting,
    update_setting, delete_setting, get_default_setting, set_default_setting,
)
from app.utils.response import ok, fail
from app.services.http_client import api_get
import requests


def _row_to_dict(row):
    d = dict(row)
    d["is_default"] = bool(d.get("is_default"))
    return d


def _get_setting_or_404(setting_id):
    return get_setting(setting_id)


@api_bp.route("/settings")
def list_settings():
    return ok(data=[_row_to_dict(r) for r in list_settings_raw()])


@api_bp.route("/settings", methods=["POST"])
def create_setting_route():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    api_url = (body.get("api_url") or "").strip()
    api_key = body.get("api_key", "")

    if not name:
        return fail(400, "name 不能为空", request)
    if not api_url:
        return fail(400, "api_url 不能为空", request)

    sid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    model = body.get("model", "gpt-4o")
    response_format = body.get("response_format", "")
    temperature = body.get("temperature", 0.7)
    max_tokens = body.get("max_tokens", 4096)

    s = {
        "id": sid,
        "name": name,
        "api_url": api_url,
        "api_key": api_key,
        "model": model,
        "response_format": response_format,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "is_default": False,
        "created_at": now,
        "updated_at": now,
    }
    create_setting(s)

    return ok(data=_row_to_dict(s))


@api_bp.route("/settings/<setting_id>", methods=["PUT"])
def update_setting_route(setting_id):
    row = _get_setting_or_404(setting_id)
    if not row:
        return fail(404, "配置不存在", request)

    body = request.get_json(silent=True) or {}
    name = (body.get("name") or row["name"]).strip()
    api_url = (body.get("api_url") or row["api_url"]).strip()
    model = body.get("model", row["model"])
    response_format = body.get("response_format", row["response_format"])
    temperature = body.get("temperature", row["temperature"])
    max_tokens = body.get("max_tokens", row["max_tokens"])

    new_api_key = body.get("api_key", "")
    if new_api_key == "":
        api_key = row["api_key"]
    else:
        api_key = new_api_key

    now = datetime.now(timezone.utc).isoformat()

    updates = {
        "name": name,
        "api_url": api_url,
        "api_key": api_key,
        "model": model,
        "response_format": response_format,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "updated_at": now,
    }
    update_setting(setting_id, updates)

    updated = _get_setting_or_404(setting_id)
    return ok(data=_row_to_dict(updated))


@api_bp.route("/settings/<setting_id>", methods=["DELETE"])
def delete_setting_route(setting_id):
    row = _get_setting_or_404(setting_id)
    if not row:
        return fail(404, "配置不存在", request)
    if row.get("is_default"):
        return fail(409, "不能删除默认配置，请先切换默认配置", request)

    delete_setting(setting_id)
    return ok()


@api_bp.route("/settings/<setting_id>/test", methods=["POST"])
def test_setting(setting_id):
    row = _get_setting_or_404(setting_id)
    if not row:
        return fail(404, "配置不存在", request)

    api_key = row["api_key"]

    url = row["api_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": row["model"],
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": row.get("max_tokens", 5),
        "stream": False,
    }
    if row.get("temperature") is not None:
        payload["temperature"] = row["temperature"]

    import time
    start = time.time()
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        latency_ms = int((time.time() - start) * 1000)
        data = resp.json()
        model_used = data.get("model", row["model"])
        return ok(data={
            "success": True,
            "latency_ms": latency_ms,
            "model": model_used,
        })
    except requests.RequestException as e:
        latency_ms = int((time.time() - start) * 1000)
        return fail(502, f"连通性测试失败: {e}", request)


@api_bp.route("/settings/models", methods=["POST"])
def fetch_models():
    body = request.get_json(silent=True) or {}
    api_url = (body.get("api_url") or "").strip()
    api_key = (body.get("api_key") or "").strip()

    if not api_url:
        return fail(400, "api_url 不能为空", request)

    url = api_url.rstrip("/") + "/models"
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    data, error = api_get(url, headers={"Authorization": f"Bearer {api_key}"} if api_key else {})
    if error:
        return fail(502, f"获取模型列表失败: {error}", request)
    models = [m.get("id", "") for m in data.get("data", [])]
    return ok(data=models)


@api_bp.route("/settings/<setting_id>/default", methods=["PUT"])
def set_default_route(setting_id):
    row = _get_setting_or_404(setting_id)
    if not row:
        return fail(404, "配置不存在", request)

    set_default_setting(setting_id)
    return ok(data={"is_default": True})
