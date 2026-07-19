from app.routes import api_bp
from flask import jsonify


@api_bp.route("/hello")
def hello():
    """骨架测试接口"""
    return jsonify({
        "code": 0,
        "message": "ok",
        "data": {"message": "Hello from Flask!"}
    })
