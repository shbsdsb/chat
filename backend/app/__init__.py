import json
import os
from flask import Flask
from flask_cors import CORS

from app.storage import init_storage


def create_app():
    flask_app = Flask(__name__)

    # ── 加载 JSON 配置 ───────────────────────────────
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "config.json"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    flask_app.config.from_mapping(config)

    # ── 全局 CORS（允许跨域 + SSE 所需的头） ────────
    CORS(flask_app, resources={
        r"/api/*": {
            "origins": "*",
            "allow_headers": ["Content-Type", "Authorization"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "supports_credentials": False,
        }
    })

    # ── 注册蓝图 ────────────────────────────────────
    from app.routes import api_bp
    import app.routes.example   # noqa — 必须在 register 前导入，注册 /api/hello
    import app.routes.settings      # noqa — 注册 /api/settings 系列路由
    import app.routes.conversations # noqa — 注册 /api/conversations 系列路由

    flask_app.register_blueprint(api_bp, url_prefix="/api")

    # ── 首次启动初始化 ──────────────────────────────
    os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "user_data", "logs"), exist_ok=True)
    init_storage()  # 初始化 JSON 存储（幂等）

    return flask_app
