from flask import request
from app.routes import api_bp
from app.storage import (
    get_entries,
    create_entry,
    update_entry,
    delete_entry,
    reorder_entries,
)
from app.storage.param_presets import get_param_preset
from app.utils.response import ok, fail


def _verify_preset(preset_id):
    """校验参数预设存在。"""
    if not get_param_preset(preset_id):
        return False
    return True


@api_bp.route("/prompt-entries", methods=["GET"])
def list_prompt_entries():
    preset_id = request.args.get("preset_id", "")
    if not preset_id:
        return fail(400, "缺少 preset_id 参数")
    if not _verify_preset(preset_id):
        return fail(404, "参数预设不存在")
    entries = get_entries(preset_id)
    return ok(entries)


@api_bp.route("/prompt-entries", methods=["POST"])
def create_prompt_entry():
    data = request.get_json(silent=True) or {}
    preset_id = data.get("preset_id", "")
    name = data.get("name", "")
    if not preset_id:
        return fail(400, "缺少 preset_id 参数")
    if not _verify_preset(preset_id):
        return fail(404, "参数预设不存在")
    if not name or not name.strip():
        return fail(400, "名称不能为空")
    entry = create_entry(preset_id, name)
    return ok(entry, "创建成功")


@api_bp.route("/prompt-entries/<entry_id>", methods=["PUT"])
def update_prompt_entry(entry_id):
    data = request.get_json(silent=True) or {}
    preset_id = data.get("preset_id", "")
    if not preset_id:
        return fail(400, "缺少 preset_id 参数")
    if not _verify_preset(preset_id):
        return fail(404, "参数预设不存在")
    updates = {}
    if "name" in data:
        if not data["name"] or not data["name"].strip():
            return fail(400, "名称不能为空")
        updates["name"] = data["name"]
    if "enabled" in data:
        updates["enabled"] = data["enabled"]
    if not updates:
        return fail(400, "没有需要更新的字段")
    entry = update_entry(preset_id, entry_id, updates)
    if entry is None:
        return fail(404, "条目不存在")
    return ok(entry, "更新成功")


@api_bp.route("/prompt-entries/<entry_id>", methods=["DELETE"])
def delete_prompt_entry(entry_id):
    preset_id = request.args.get("preset_id", "")
    if not preset_id:
        return fail(400, "缺少 preset_id 参数")
    if not _verify_preset(preset_id):
        return fail(404, "参数预设不存在")
    delete_entry(preset_id, entry_id)
    return ok(None, "删除成功")


@api_bp.route("/prompt-entries/reorder", methods=["PUT"])
def reorder_prompt_entries():
    data = request.get_json(silent=True) or {}
    preset_id = data.get("preset_id", "")
    ids = data.get("ids", [])
    if not preset_id:
        return fail(400, "缺少 preset_id 参数")
    if not _verify_preset(preset_id):
        return fail(404, "参数预设不存在")
    if not isinstance(ids, list):
        return fail(400, "ids 必须是数组")
    reorder_entries(preset_id, ids)
    return ok(None, "排序成功")
