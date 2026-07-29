"""
Message Inspector -- 后端扩展
在消息发送给 AI 之前，将完整 messages 数组以格式化 JSON 打印到终端。
"""
import json
import os


def on_chat_pre_send(ctx):
    # 读取扩展 settings，检查 print_messages 开关
    try:
        ext_dir = os.path.dirname(os.path.abspath(__file__))
        settings_path = os.path.join(ext_dir, "settings.json")
        if os.path.isfile(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            features = settings.get("features", {})
            if not features.get("print_messages", True):
                return
    except Exception:
        pass  # settings 不可用时默认打印

    messages = ctx.get("messages", [])
    conv_id = ctx.get("conversation_id", "?")

    print(f"\n{'=' * 60}")
    print(f"  [Message Inspector] conversation: {conv_id}")
    print(f"  messages count: {len(messages)}")
    print(f"{'=' * 60}")
    print(json.dumps(messages, indent=2, ensure_ascii=False))
    print(f"{'=' * 60}\n")
