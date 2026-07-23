import uuid
from datetime import datetime, timezone
from flask import request
from app.routes import api_bp
from app.storage import (
    list_param_presets_raw, get_param_preset, create_param_preset,
    update_param_preset, delete_param_preset,
    get_default_param_preset, set_default_param_preset,
)
from app.utils.response import ok, fail


def _row_to_dict(row):
    d = dict(row)
    d["is_default"] = bool(d.get("is_default"))
    return d


def _get_or_404(preset_id):
    return get_param_preset(preset_id)


@api_bp.route("/param-presets")
def list_param_presets_route():
    return ok(data=[_row_to_dict(r) for r in list_param_presets_raw()])


@api_bp.route("/param-presets", methods=["POST"])
def create_param_preset_route():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()

    if not name:
        return fail(400, "name 不能为空", request)

    try:
        temperature = float(body.get("temperature", 0.7))
        max_tokens = int(body.get("max_tokens", 4096))
        top_p = float(body.get("top_p", 1.0))
    except (ValueError, TypeError):
        return fail(400, "参数格式错误", request)

    if not 0 <= temperature <= 2:
        return fail(400, "temperature 范围 0~2", request)
    if max_tokens < 1:
        return fail(400, "max_tokens 必须 > 0", request)
    if not 0 <= top_p <= 1:
        return fail(400, "top_p 范围 0~1", request)

    pid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    p = {
        "id": pid,
        "name": name,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "is_default": False,
        "created_at": now,
        "updated_at": now,
    }
    create_param_preset(p)

    return ok(data=_row_to_dict(p))


@api_bp.route("/param-presets/<preset_id>", methods=["PUT"])
def update_param_preset_route(preset_id):
    row = _get_or_404(preset_id)
    if not row:
        return fail(404, "参数预设不存在", request)

    body = request.get_json(silent=True) or {}
    name = (body.get("name") or row["name"]).strip()

    try:
        temperature = float(body.get("temperature", row["temperature"]))
        max_tokens = int(body.get("max_tokens", row["max_tokens"]))
        top_p = float(body.get("top_p", row["top_p"]))
    except (ValueError, TypeError):
        return fail(400, "参数格式错误", request)

    if not 0 <= temperature <= 2:
        return fail(400, "temperature 范围 0~2", request)
    if max_tokens < 1:
        return fail(400, "max_tokens 必须 > 0", request)
    if not 0 <= top_p <= 1:
        return fail(400, "top_p 范围 0~1", request)

    now = datetime.now(timezone.utc).isoformat()

    updates = {
        "name": name,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "updated_at": now,
    }
    update_param_preset(preset_id, updates)

    updated = _get_or_404(preset_id)
    return ok(data=_row_to_dict(updated))


@api_bp.route("/param-presets/<preset_id>", methods=["DELETE"])
def delete_param_preset_route(preset_id):
    row = _get_or_404(preset_id)
    if not row:
        return fail(404, "参数预设不存在", request)
    if row.get("is_default"):
        return fail(409, "不能删除默认参数预设，请先切换默认预设", request)

    delete_param_preset(preset_id)
    return ok()


@api_bp.route("/param-presets/<preset_id>/default", methods=["PUT"])
def set_default_param_preset_route(preset_id):
    row = _get_or_404(preset_id)
    if not row:
        return fail(404, "参数预设不存在", request)

    set_default_param_preset(preset_id)
    return ok(data={"is_default": True})
