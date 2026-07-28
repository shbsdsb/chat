import uuid
import json
from datetime import datetime, timezone
from flask import request, Response, stream_with_context
from app.routes import api_bp
from app.storage import (
    get_conversation, list_conversations, create_conversation,
    update_conversation, delete_conversation,
    get_messages, add_message, get_message, update_message,
    delete_messages_after, delete_message,
    get_last_assistant_message_id, get_messages_for_chat,
    get_default_setting,
)
from app.utils.response import ok, fail
from app.services.sse_manager import sse_manager
from app.services.ai import stream_chat


def _get_conv_or_404(conv_id):
    return get_conversation(conv_id)


def _conv_to_dict(row):
    return row


def _stream_and_save(settings, messages, conv_id, cancel_event,
                     temperature=None, max_tokens=None, top_p=None, request_body=None,
                     user_msg_id=None):
    """Shared SSE generator: stream AI response, save assistant message, unregister."""

    full_content = ""
    full_reasoning = ""
    final_usage = None
    assistant_msg_id = str(uuid.uuid4())
    assistant_created = datetime.now(timezone.utc).isoformat()

    try:
        for chunk in stream_chat(
            settings["api_url"],
            settings["api_key"],
            settings["model"],
            messages,
            settings.get("response_format", ""),
            cancel_event,
            temperature,
            max_tokens,
            top_p,
        ):
            if "error" in chunk:
                yield f"data: {json.dumps({'error': chunk['error']})}\n\n"
                break
            if chunk.get("stopped"):
                yield f"data: {json.dumps({'stopped': True})}\n\n"
                break
            if chunk.get("reasoning_delta"):
                full_reasoning += chunk["reasoning_delta"]
                yield f"data: {json.dumps({'reasoning_delta': chunk['reasoning_delta']})}\n\n"
            if chunk.get("delta"):
                full_content += chunk["delta"]
                yield f"data: {json.dumps({'delta': chunk['delta'], 'done': False})}\n\n"
            if chunk.get("done"):
                final_usage = chunk.get("usage")
                done_data = {"done": True, "user_msg_id": user_msg_id, "assistant_msg_id": assistant_msg_id}
                yield f"data: {json.dumps(done_data)}\n\n"
    finally:
        if full_content or full_reasoning:
            msg_data = {
                "id": assistant_msg_id,
                "conversation_id": conv_id,
                "role": "assistant",
                "content": full_content,
                "reasoning_content": full_reasoning,
                "created_at": assistant_created,
            }
            # ── 扩展钩子：chat.post_receive ──
            from app.extensions import get_extension_manager
            mgr = get_extension_manager()
            # 收集 World Info 条目（当前阶段传空列表，后续 World Info 实现后替换）
            world_info_entries = request_body.get("_world_info_entries", []) if isinstance(request_body, dict) else []
            hook_ctx = {
                "conversation_id": conv_id,
                "messages": messages + [{"role": "assistant", "content": full_content}],
                "request_body": {"model": settings.get("model"), "messages": messages},
                "response_body": {"content": full_content, "reasoning_content": full_reasoning, "usage": final_usage},
                "world_info_entries": world_info_entries,
                "settings": settings,
            }
            ext_results = mgr.dispatcher.dispatch("chat.post_receive", hook_ctx)
            # 合并扩展返回的 message_meta
            ext_data = {}
            for result in ext_results:
                eid = result.get("extension_id", "")
                meta = result.get("message_meta", {})
                if meta:
                    ext_data[eid] = meta
            if ext_data:
                msg_data["extensions"] = ext_data

            add_message(msg_data)
        sse_manager.unregister(conv_id)


@api_bp.route("/conversations")
def list_conversations_route():
    return ok(data=[_conv_to_dict(r) for r in list_conversations()])


@api_bp.route("/conversations", methods=["POST"])
def create_conversation_route():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip() or "新对话"

    cid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    conv = {"id": cid, "title": title, "created_at": now, "updated_at": now}
    create_conversation(conv)

    return ok(data=_conv_to_dict(conv))


@api_bp.route("/conversations/<conv_id>")
def get_conversation_route(conv_id):
    row = _get_conv_or_404(conv_id)
    if not row:
        return fail(404, "会话不存在", request)

    msgs = get_messages(conv_id)
    data = _conv_to_dict(row)
    data["messages"] = [dict(m) for m in msgs]
    return ok(data=data)


@api_bp.route("/conversations/<conv_id>", methods=["DELETE"])
def delete_conversation_route(conv_id):
    row = _get_conv_or_404(conv_id)
    if not row:
        return fail(404, "会话不存在", request)

    delete_conversation(conv_id)
    return ok()


@api_bp.route("/conversations/<conv_id>/chat", methods=["POST"])
def chat(conv_id):
    row = _get_conv_or_404(conv_id)
    if not row:
        return fail(404, "会话不存在", request)

    settings = get_default_setting()
    if not settings:
        return fail(400, "请先在设置中配置 API", request)

    body = request.get_json(silent=True) or {}
    content = (body.get("content") or "").strip()
    if not content:
        return fail(400, "消息内容不能为空", request)

    # 从请求体读取参数预设值
    temperature = body.get("temperature")
    max_tokens = body.get("max_tokens")
    top_p = body.get("top_p")

    now = datetime.now(timezone.utc).isoformat()

    user_msg_id = str(uuid.uuid4())
    add_message({
        "id": user_msg_id,
        "conversation_id": conv_id,
        "role": "user",
        "content": content,
        "reasoning_content": "",
        "created_at": now,
    })

    # 更新用户消息时间（用于排序）
    update_conversation(conv_id, {"updated_at": now})

    messages = get_messages_for_chat(conv_id)

    cancel_event = sse_manager.register(conv_id)

    return Response(
        stream_with_context(_stream_and_save(settings, messages, conv_id, cancel_event,
                                             temperature=temperature, max_tokens=max_tokens, top_p=top_p,
                                             request_body=body, user_msg_id=user_msg_id)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@api_bp.route("/conversations/<conv_id>/messages/<msg_id>", methods=["PUT"])
def edit_message(conv_id, msg_id):
    row = _get_conv_or_404(conv_id)
    if not row:
        return fail(404, "会话不存在", request)

    msg = get_message(msg_id, conv_id)
    if not msg:
        return fail(404, "消息不存在", request)
    if msg["role"] not in ("user", "assistant"):
        return fail(400, "只能编辑用户或助手消息", request)

    body = request.get_json(silent=True) or {}
    content = (body.get("content") or "").strip()
    if not content:
        return fail(400, "消息内容不能为空", request)

    update_message(msg_id, {"content": content, "conversation_id": conv_id})
    delete_messages_after(conv_id, msg["created_at"])

    updated = get_message(msg_id, conv_id)
    return ok(data=updated)


@api_bp.route("/conversations/<conv_id>/regenerate", methods=["POST"])
def regenerate(conv_id):
    row = _get_conv_or_404(conv_id)
    if not row:
        return fail(404, "会话不存在", request)

    settings = get_default_setting()
    if not settings:
        return fail(400, "请先在设置中配置 API", request)

    last_assistant_id = get_last_assistant_message_id(conv_id)
    if not last_assistant_id:
        return fail(400, "没有可重新生成的 AI 回复", request)

    body = request.get_json(silent=True) or {}
    temperature = body.get("temperature")
    max_tokens = body.get("max_tokens")
    top_p = body.get("top_p")

    delete_message(last_assistant_id, conv_id)

    messages = get_messages_for_chat(conv_id)

    cancel_event = sse_manager.register(conv_id)

    return Response(
        stream_with_context(_stream_and_save(settings, messages, conv_id, cancel_event,
                                             temperature=temperature, max_tokens=max_tokens, top_p=top_p,
                                             request_body=body)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@api_bp.route("/conversations/<conv_id>/stop", methods=["POST"])
def stop_generation(conv_id):
    cancelled = sse_manager.cancel(conv_id)
    if cancelled:
        return ok(message="已发送停止信号")
    return ok(message="没有正在进行的生成")
