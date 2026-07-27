from flask import Blueprint, request
import os
import json

api_bp = Blueprint("api", __name__)


@api_bp.route("/shutdown", methods=["POST"])
def shutdown():
    """由前端 Electron 窗口关闭时调用，优雅关闭 Flask 服务"""
    # 读取配置确认是否允许
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
    try:
        with open(config_path, "r") as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    if not cfg.get("shutdown_with_frontend", False):
        return {"code": 0, "message": "shutdown_with_frontend is disabled"}, 200
    # 优雅关闭
    os._exit(0)
