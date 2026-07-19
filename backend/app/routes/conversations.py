import uuid
import json
from datetime import datetime, timezone
from flask import request, Response, stream_with_context
from app.routes import api_bp
from app.database import get_db
from app.utils.response import ok, fail
from app.services.sse_manager import sse_manager
from app.services.ai import stream_chat


def _get_conv_or_404(conv_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM conversations WHERE id = ?", (conv_id,)
    ).fetchone()


def _conv_to_dict(row):
    return dict(row)


def _get_default_settings():
    db = get_db()
    row = db.execute(
        "SELECT * FROM settings WHERE is_default = 1 LIMIT 1"
    ).fetchone()
    if not row:
        return None
    return dict(row)


def _stream_and_save(settings, messages, conv_id, cancel_event):
    """Shared SSE generator: stream AI response, save assistant message, unregister.

    Yields SSE data events. On any path (success/error/stop), the finally
    block persists the assistant message and unregisters from SSEManager.
    """
    full_content = ""
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
            settings.get("temperature"),
            settings.get("max_tokens"),
        ):
            if "error" in chunk:
                yield f"data: {json.dumps({'error': chunk['error']})}\n\n"
                break
            if chunk.get("stopped"):
                yield f"data: {json.dumps({'stopped': True})}\n\n"
                break
            if chunk.get("delta"):
                full_content += chunk["delta"]
                yield f"data: {json.dumps({'delta': chunk['delta'], 'done': False})}\n\n"
            if chunk.get("done"):
                yield f"data: {json.dumps({'done': True})}\n\n"
    finally:
        if full_content:
            db = get_db()
            db.execute(
                "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, 'assistant', ?, ?)",
                (assistant_msg_id, conv_id, full_content, assistant_created),
            )
            db.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), conv_id),
            )
            db.commit()
        sse_manager.unregister(conv_id)


@api_bp.route("/conversations")
def list_conversations():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM conversations ORDER BY updated_at DESC"
    ).fetchall()
    return ok(data=[_conv_to_dict(r) for r in rows])


@api_bp.route("/conversations", methods=["POST"])
def create_conversation():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip() or "新对话"

    cid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    db = get_db()
    db.execute(
        "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (cid, title, now, now),
    )
    db.commit()

    row = _get_conv_or_404(cid)
    return ok(data=_conv_to_dict(row))


@api_bp.route("/conversations/<conv_id>")
def get_conversation(conv_id):
    row = _get_conv_or_404(conv_id)
    if not row:
        return fail(404, "会话不存在", request)

    db = get_db()
    msgs = db.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conv_id,),
    ).fetchall()

    data = _conv_to_dict(row)
    data["messages"] = [dict(m) for m in msgs]
    return ok(data=data)


@api_bp.route("/conversations/<conv_id>", methods=["DELETE"])
def delete_conversation(conv_id):
    row = _get_conv_or_404(conv_id)
    if not row:
        return fail(404, "会话不存在", request)

    db = get_db()
    db.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    db.commit()
    return ok()


@api_bp.route("/conversations/<conv_id>/chat", methods=["POST"])
def chat(conv_id):
    row = _get_conv_or_404(conv_id)
    if not row:
        return fail(404, "会话不存在", request)

    settings = _get_default_settings()
    if not settings:
        return fail(400, "请先在设置中配置 API", request)

    body = request.get_json(silent=True) or {}
    content = (body.get("content") or "").strip()
    if not content:
        return fail(400, "消息内容不能为空", request)

    db = get_db()
    now = datetime.now(timezone.utc).isoformat()

    user_msg_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, 'user', ?, ?)",
        (user_msg_id, conv_id, content, now),
    )
    db.execute(
        "UPDATE conversations SET updated_at = ?, title = CASE WHEN title = '新对话' THEN ? ELSE title END WHERE id = ?",
        (now, content[:30], conv_id),
    )
    db.commit()

    rows = db.execute(
        "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conv_id,),
    ).fetchall()
    messages = [{"role": r["role"], "content": r["content"]} for r in rows]

    cancel_event = sse_manager.register(conv_id)

    return Response(
        stream_with_context(_stream_and_save(settings, messages, conv_id, cancel_event)),
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

    db = get_db()
    msg = db.execute(
        "SELECT * FROM messages WHERE id = ? AND conversation_id = ?",
        (msg_id, conv_id),
    ).fetchone()
    if not msg:
        return fail(404, "消息不存在", request)
    if msg["role"] != "user":
        return fail(400, "只能编辑用户消息", request)

    body = request.get_json(silent=True) or {}
    content = (body.get("content") or "").strip()
    if not content:
        return fail(400, "消息内容不能为空", request)

    db.execute("UPDATE messages SET content = ? WHERE id = ?", (content, msg_id))
    db.execute(
        "DELETE FROM messages WHERE conversation_id = ? AND created_at > ?",
        (conv_id, msg["created_at"]),
    )
    db.commit()

    updated = db.execute("SELECT * FROM messages WHERE id = ?", (msg_id,)).fetchone()
    return ok(data=dict(updated))


@api_bp.route("/conversations/<conv_id>/regenerate", methods=["POST"])
def regenerate(conv_id):
    row = _get_conv_or_404(conv_id)
    if not row:
        return fail(404, "会话不存在", request)

    settings = _get_default_settings()
    if not settings:
        return fail(400, "请先在设置中配置 API", request)

    db = get_db()
    last_assistant = db.execute(
        "SELECT id FROM messages WHERE conversation_id = ? AND role = 'assistant' ORDER BY created_at DESC LIMIT 1",
        (conv_id,),
    ).fetchone()
    if not last_assistant:
        return fail(400, "没有可重新生成的 AI 回复", request)
    db.execute("DELETE FROM messages WHERE id = ?", (last_assistant["id"],))
    db.commit()

    rows = db.execute(
        "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conv_id,),
    ).fetchall()
    messages = [{"role": r["role"], "content": r["content"]} for r in rows]

    cancel_event = sse_manager.register(conv_id)

    return Response(
        stream_with_context(_stream_and_save(settings, messages, conv_id, cancel_event)),
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
