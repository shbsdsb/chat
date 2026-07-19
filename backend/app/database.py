"""
数据库初始化
"""
import sqlite3
import os
from flask import g


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
USER_DATA_DIR = os.path.join(PROJECT_ROOT, "user_data")
DB_PATH = os.path.join(USER_DATA_DIR, "chat.db")


# ── 数据库 ─────────────────────────────────────────────

def get_db():
    """每个请求获取同一个 sqlite3 连接（存在 Flask g 上）。"""
    if "db" not in g:
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row       # 让查询结果支持 dict 式访问
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        g.db = conn
    return g.db


def close_db(exc=None):
    """请求结束时关闭数据库连接。"""
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    """建表（幂等），应在首次请求前调用。"""
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            id         TEXT PRIMARY KEY,
            title      TEXT NOT NULL DEFAULT '新对话',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id              TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role            TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
            content         TEXT NOT NULL,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (conversation_id)
                REFERENCES conversations(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_messages_conv
            ON messages(conversation_id, created_at);

        CREATE TABLE IF NOT EXISTS settings (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            api_url         TEXT NOT NULL,
            api_key         TEXT NOT NULL,
            model           TEXT NOT NULL DEFAULT 'gpt-4o',
            response_format TEXT NOT NULL DEFAULT '',
            temperature     REAL NOT NULL DEFAULT 0.7,
            max_tokens      INTEGER NOT NULL DEFAULT 4096,
            is_default      INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()
