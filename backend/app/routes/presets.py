from flask import request
from app.routes import api_bp
from app.storage.presets import (
    list_presets, get_preset, create_preset, update_preset,
    delete_preset, get_default_preset, set_default_preset,
)
from app.utils.response import ok, fail


def _get_or_404(preset_id):
    return get_preset(preset_id)


@api_bp.route("/presets")
def list_presets_route():
    return ok(data=list_presets())


@api_bp.route("/presets/<preset_id>")
def get_preset_route(preset_id):
    row = _get_or_404(preset_id)
    if not row:
        return fail(404, "参数预设不存在", request)
    return ok(data=row)


@api_bp.route("/presets", methods=["POST"])
def create_preset_route():
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
    preset = create_preset({
        "name": name, "temperature": temperature,
        "max_tokens": max_tokens, "top_p": top_p,
    })
    return ok(data=preset)


@api_bp.route("/presets/<preset_id>", methods=["PUT"])
def update_preset_route(preset_id):
    row = _get_or_404(preset_id)
    if not row:
        return fail(404, "参数预设不存在", request)
    body = request.get_json(silent=True) or {}
    updated = update_preset(preset_id, body)
    return ok(data=updated)


@api_bp.route("/presets/<preset_id>", methods=["DELETE"])
def delete_preset_route(preset_id):
    row = _get_or_404(preset_id)
    if not row:
        return fail(404, "参数预设不存在", request)
    if row.get("is_default"):
        return fail(409, "不能删除默认参数预设，请先切换默认预设", request)
    delete_preset(preset_id)
    return ok()


@api_bp.route("/presets/<preset_id>/default", methods=["PUT"])
def set_default_preset_route(preset_id):
    row = _get_or_404(preset_id)
    if not row:
        return fail(404, "参数预设不存在", request)
    set_default_preset(preset_id)
    return ok(data={"is_default": True})
