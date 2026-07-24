import uuid
from datetime import datetime, timezone
from flask import request
from app.routes import api_bp
from app.storage import (
    list_css_presets_raw, get_css_preset, create_css_preset,
    update_css_preset, delete_css_preset,
    get_default_css_preset, set_default_css_preset,
)
from app.utils.response import ok, fail


def _row_to_dict(row):
    d = dict(row)
    d["is_default"] = bool(d.get("is_default"))
    return d


def _get_or_404(preset_id):
    return get_css_preset(preset_id)


@api_bp.route("/css-presets")
def list_css_presets_route():
    return ok(data=[_row_to_dict(r) for r in list_css_presets_raw()])


@api_bp.route("/css-presets", methods=["POST"])
def create_css_preset_route():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()

    if not name:
        return fail(400, "name 不能为空", request)

    content = body.get("content", "")

    pid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    p = {
        "id": pid,
        "name": name,
        "content": content,
        "is_default": False,
        "created_at": now,
        "updated_at": now,
    }
    create_css_preset(p)

    return ok(data=_row_to_dict(p))


@api_bp.route("/css-presets/<preset_id>", methods=["PUT"])
def update_css_preset_route(preset_id):
    row = _get_or_404(preset_id)
    if not row:
        return fail(404, "CSS 预设不存在", request)

    body = request.get_json(silent=True) or {}
    name = (body.get("name") or row["name"]).strip()

    if not name:
        return fail(400, "name 不能为空", request)

    content = body.get("content", row["content"])

    now = datetime.now(timezone.utc).isoformat()

    updates = {
        "name": name,
        "content": content,
        "updated_at": now,
    }
    update_css_preset(preset_id, updates)

    updated = _get_or_404(preset_id)
    return ok(data=_row_to_dict(updated))


@api_bp.route("/css-presets/<preset_id>", methods=["DELETE"])
def delete_css_preset_route(preset_id):
    row = _get_or_404(preset_id)
    if not row:
        return fail(404, "CSS 预设不存在", request)
    if row.get("is_default"):
        return fail(409, "不能删除默认CSS预设，请先切换默认预设", request)

    delete_css_preset(preset_id)
    return ok()


@api_bp.route("/css-presets/<preset_id>/default", methods=["PUT"])
def set_default_css_preset_route(preset_id):
    row = _get_or_404(preset_id)
    if not row:
        return fail(404, "CSS 预设不存在", request)

    set_default_css_preset(preset_id)
    return ok(data={"is_default": True})
