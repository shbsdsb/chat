import json
import os
import re
import threading

_lock = threading.Lock()


def _find_project_root():
    """从当前文件向上查找项目根目录（包含 backend/ 和 user_data/ 的目录）"""
    path = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        if os.path.isdir(os.path.join(path, "backend")) and \
           os.path.isdir(os.path.join(path, "user_data")):
            return path
        path = os.path.dirname(path)
    # 回退：4 层（适配 user_data/extensions/<ext_id>/backend.py 结构）
    return os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))


_STORAGE_DIR = os.path.join(_find_project_root(), "user_data", "extensions", "dashboard")


_CONV_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_\-]{1,64}$')


def _validate_conv_id(conv_id):
    """校验 conv_id 仅含安全字符，防止路径遍历"""
    return bool(_CONV_ID_PATTERN.match(conv_id))


def _metrics_path(conv_id):
    return os.path.join(_STORAGE_DIR, f"{conv_id}.json")


def _read_metrics(conv_id):
    path = _metrics_path(conv_id)
    if not os.path.exists(path):
        return {
            "request_count": 0,
            "total_completion_tokens": 0,
            "total_prompt_tokens": 0,
            "last_hit_rate": 0.0,
            "updated_at": "",
        }
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "request_count": 0,
            "total_completion_tokens": 0,
            "total_prompt_tokens": 0,
            "last_hit_rate": 0.0,
            "updated_at": "",
        }


def _write_metrics(conv_id, metrics):
    os.makedirs(_STORAGE_DIR, exist_ok=True)
    with _lock:
        with open(_metrics_path(conv_id), "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)


def _estimate_tokens(text):
    """简易 token 估算：中文 ~1.5 char/token，英文 ~4 char/token，取平均 ~3"""
    if not text:
        return 0
    return max(1, len(text) // 3)


def on_chat_post_receive(ctx):
    conv_id = ctx.get("conversation_id")
    if not conv_id:
        return None

    metrics = _read_metrics(conv_id)
    metrics["request_count"] = metrics.get("request_count", 0) + 1

    # 累加 completion tokens
    response_body = ctx.get("response_body", {})
    content = response_body.get("content", "")
    reasoning = response_body.get("reasoning_content", "")
    added = _estimate_tokens(content) + _estimate_tokens(reasoning)
    metrics["total_completion_tokens"] = metrics.get("total_completion_tokens", 0) + added

    # 估算 prompt tokens（用当前消息列表长度）
    messages = ctx.get("messages", [])
    prompt_text = "".join(m.get("content", "") for m in messages)
    metrics["total_prompt_tokens"] = metrics.get("total_prompt_tokens", 0) + _estimate_tokens(prompt_text)

    # 上下文缓存命中率（基于 DeepSeek API 返回的 usage）
    usage = ctx.get("response_body", {}).get("usage") or {}
    hit = usage.get("prompt_cache_hit_tokens", 0)
    miss = usage.get("prompt_cache_miss_tokens", 0)
    if hit + miss > 0:
        metrics["last_hit_rate"] = round(hit / (hit + miss), 2)
    else:
        metrics["last_hit_rate"] = 0.0

    from datetime import datetime, timezone
    metrics["updated_at"] = datetime.now(timezone.utc).isoformat()
    _write_metrics(conv_id, metrics)
    return None


def register_api_routes(app):
    @app.route("/ext/dashboard/<conv_id>/metrics")
    def dashboard_metrics(conv_id):
        from flask import jsonify
        if not _validate_conv_id(conv_id):
            return jsonify({
                "code": 400,
                "message": "invalid conversation_id",
                "data": None,
            }), 400
        metrics = _read_metrics(conv_id)
        return jsonify({
            "code": 0,
            "message": "ok",
            "data": metrics,
        })
