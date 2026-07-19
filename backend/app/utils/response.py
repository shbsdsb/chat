import json
import os
import logging
from datetime import datetime, timezone
from flask import jsonify, request as flask_request

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
LOG_DIR = os.path.join(PROJECT_ROOT, "user_data", "logs")


def ok(data=None, message="ok"):
    return jsonify({"code": 0, "message": message, "data": data})


def fail(code, message, request=None):
    req = request or flask_request
    os.makedirs(LOG_DIR, exist_ok=True)

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "code": code,
        "message": message,
    }

    if req:
        log_entry["method"] = req.method
        log_entry["path"] = req.path
        if req.is_json:
            body = req.get_json(silent=True) or {}
            masked = {}
            for key, val in body.items():
                if key in ("api_key", "password", "secret"):
                    masked[key] = "***"
                else:
                    masked[key] = val
            log_entry["body"] = masked

    with open(os.path.join(LOG_DIR, "error.log"), "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    return jsonify({"code": code, "message": message, "data": None})
