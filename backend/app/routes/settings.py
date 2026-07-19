import uuid
from datetime import datetime, timezone
from flask import request
from app.routes import api_bp
from app.database import get_db, encrypt, decrypt
from app.utils.response import ok, fail
import requests


def _row_to_dict(row):
    d = dict(row)
    if d.get("api_key"):
        key = d["api_key"]
        try:
            key = decrypt(key)
        except Exception:
            pass
        d["api_key"] = key[:4] + "****" if len(key) >= 4 else "****"
    d["is_default"] = bool(d.get("is_default"))
    return d


def _get_setting_or_404(setting_id):
    db = get_db()
    row = db.execute("SELECT * FROM settings WHERE id = ?", (setting_id,)).fetchone()
    return row


@api_bp.route("/settings")
def list_settings():
    db = get_db()
    rows = db.execute("SELECT * FROM settings ORDER BY created_at DESC").fetchall()
    return ok(data=[_row_to_dict(r) for r in rows])


@api_bp.route("/settings", methods=["POST"])
def create_setting():
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
    encrypted_key = encrypt(api_key) if api_key else ""
    model = body.get("model", "gpt-4o")
    response_format = body.get("response_format", "text")
    temperature = body.get("temperature", 0.7)
    max_tokens = body.get("max_tokens", 4096)

    db = get_db()
    db.execute("""
        INSERT INTO settings (id, name, api_url, api_key, model, response_format,
                              temperature, max_tokens, is_default, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
    """, (sid, name, api_url, encrypted_key, model, response_format,
          temperature, max_tokens, now, now))
    db.commit()

    row = _get_setting_or_404(sid)
    return ok(data=_row_to_dict(row))


@api_bp.route("/settings/<setting_id>", methods=["PUT"])
def update_setting(setting_id):
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

    api_key = body.get("api_key", "")
    if api_key == "":
        encrypted_key = row["api_key"]
    else:
        encrypted_key = encrypt(api_key)

    now = datetime.now(timezone.utc).isoformat()

    db = get_db()
    db.execute("""
        UPDATE settings
        SET name = ?, api_url = ?, api_key = ?, model = ?, response_format = ?,
            temperature = ?, max_tokens = ?, updated_at = ?
        WHERE id = ?
    """, (name, api_url, encrypted_key, model, response_format,
          temperature, max_tokens, now, setting_id))
    db.commit()

    updated = _get_setting_or_404(setting_id)
    return ok(data=_row_to_dict(updated))


@api_bp.route("/settings/<setting_id>", methods=["DELETE"])
def delete_setting(setting_id):
    row = _get_setting_or_404(setting_id)
    if not row:
        return fail(404, "配置不存在", request)
    if row["is_default"]:
        return fail(409, "不能删除默认配置，请先切换默认配置", request)

    db = get_db()
    db.execute("DELETE FROM settings WHERE id = ?", (setting_id,))
    db.commit()
    return ok()


@api_bp.route("/settings/<setting_id>/test", methods=["POST"])
def test_setting(setting_id):
    row = _get_setting_or_404(setting_id)
    if not row:
        return fail(404, "配置不存在", request)

    api_key = row["api_key"]
    try:
        api_key = decrypt(api_key)
    except Exception:
        pass

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


@api_bp.route("/settings/<setting_id>/default", methods=["PUT"])
def set_default_setting(setting_id):
    row = _get_setting_or_404(setting_id)
    if not row:
        return fail(404, "配置不存在", request)

    db = get_db()
    db.execute("UPDATE settings SET is_default = 0")
    db.execute("UPDATE settings SET is_default = 1 WHERE id = ?", (setting_id,))
    db.commit()

    return ok(data={"is_default": True})
