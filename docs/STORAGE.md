# 数据存储方案

## 数据库

**SQLite**，文件位于 `user_data/chat.db`。Python 标准库原生支持，零配置。

## 表结构

### conversations

| 列 | 类型 | 约束 | 说明 |
|---|------|------|------|
| id | TEXT | PK | UUID |
| title | TEXT | NOT NULL | 会话标题，默认"新对话" |
| created_at | TEXT | NOT NULL | ISO 8601 时间戳 |
| updated_at | TEXT | NOT NULL | ISO 8601 时间戳 |

### messages

| 列 | 类型 | 约束 | 说明 |
|---|------|------|------|
| id | TEXT | PK | UUID |
| conversation_id | TEXT | NOT NULL, FK | 所属会话 |
| role | TEXT | NOT NULL, CHECK | `user` 或 `assistant` |
| content | TEXT | NOT NULL | 消息内容 |
| created_at | TEXT | NOT NULL | ISO 8601 时间戳 |

外键：`messages.conversation_id → conversations.id`，`ON DELETE CASCADE`。

索引：`idx_messages_conv ON messages(conversation_id, created_at)`。

### settings

| 列 | 类型 | 约束 | 说明 |
|---|------|------|------|
| id | TEXT | PK | UUID |
| name | TEXT | NOT NULL | 配置名称，如"OpenAI 官方" |
| api_url | TEXT | NOT NULL | API 地址 |
| api_key | TEXT | NOT NULL | **Fernet 加密存储** |
| model | TEXT | NOT NULL | 默认 `gpt-4o` |
| response_format | TEXT | NOT NULL | `text` / `json_object` |
| temperature | REAL | NOT NULL | 0~2，默认 0.7 |
| max_tokens | INTEGER | NOT NULL | 默认 4096 |
| is_default | INTEGER | NOT NULL | 0/1，唯一默认 |
| created_at | TEXT | NOT NULL | ISO 8601 |
| updated_at | TEXT | NOT NULL | ISO 8601 |

唯一约束：`is_default=1` 的条目同时只能存在一条（应用层保证）。

## 建表 SQL

```sql
CREATE TABLE conversations (
    id         TEXT PRIMARY KEY,
    title      TEXT NOT NULL DEFAULT '新对话',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE messages (
    id              TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX idx_messages_conv ON messages(conversation_id, created_at);

CREATE TABLE settings (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    api_url         TEXT NOT NULL,
    api_key         TEXT NOT NULL,
    model           TEXT NOT NULL DEFAULT 'gpt-4o',
    response_format TEXT NOT NULL DEFAULT 'text',
    temperature     REAL NOT NULL DEFAULT 0.7,
    max_tokens      INTEGER NOT NULL DEFAULT 4096,
    is_default      INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
```

## API Key 加密

使用 **Fernet**（AES-128-CBC + HMAC），依赖 `cryptography` 包。

### 密钥管理

```
首次启动 → 生成随机 Fernet key → 写入 user_data/.fernet_key
                                                                ↓ chmod 600（或 Windows ACL 限制）
后续启动 → 读取 user_data/.fernet_key → Fernet(key)
```

`.fernet_key` 加入 `.gitignore`，泄露即等价于 API key 泄露。

### 加解密流程

```
                     写入                                 读取
 前端 ──[明文]──→ 后端 ──[encrypt]──→ DB         DB ──[密文]──→ 后端 ──[decrypt]──→ 内存使用
                                                                                      │
 前端 ←──[脱敏: sk-a****]── 后端                                                   不落盘
```

### Python 实现要点

```python
from cryptography.fernet import Fernet

def load_fernet():
    key_path = "user_data/.fernet_key"
    if not os.path.exists(key_path):
        key = Fernet.generate_key()
        with open(key_path, "wb") as f:
            f.write(key)
        # Windows: 隐藏文件 + ACL
        os.chmod(key_path, 0o600)  # Unix 试一次
    with open(key_path, "rb") as f:
        return Fernet(f.read())

fernet = load_fernet()

def encrypt_key(plain: str) -> str:
    return fernet.encrypt(plain.encode()).decode()

def decrypt_key(cipher: str) -> str:
    return fernet.decrypt(cipher.encode()).decode()
```

## 操作映射

| 接口 | SQL / 操作 |
|------|------------|
| 列表会话 | `SELECT * FROM conversations ORDER BY updated_at DESC` |
| 新建会话 | `INSERT INTO conversations` |
| 会话详情 | `SELECT * FROM messages WHERE conversation_id=? ORDER BY created_at` |
| 删除会话 | `DELETE FROM conversations WHERE id=?`（级联） |
| 发送消息 | `INSERT INTO messages`（user → SSE → assistant） |
| 编辑消息 | `UPDATE messages SET content=? WHERE id=?` → `DELETE FROM messages WHERE conversation_id=? AND created_at > ?` |
| 重新生成 | `DELETE FROM messages WHERE id=?`（删最后 assistant）→ 重新 SSE |
| 获取配置列表 | `SELECT * FROM settings ORDER BY created_at` |
| 新增配置 | `INSERT INTO settings`，`api_key` 加密 |
| 更新配置 | `UPDATE settings`，空 key 不覆盖 |
| 删除配置 | `DELETE FROM settings WHERE id=?` |
| 测试连通性 | 从 DB 取出 → 解密 → 发测试请求 |
| 设为默认 | 清除旧默认 → 设新默认 |

## 文件布局

```
user_data/
├── chat.db                   # SQLite 数据库
├── .fernet_key               # Fernet 加密密钥（600 权限）
└── logs/
    └── error.log             # 错误日志
```

## 首次启动初始化

1. 创建 `user_data/` 目录（如不存在）
2. 连接 SQLite，执行 `CREATE TABLE IF NOT EXISTS` 建表
3. 启用 `PRAGMA foreign_keys = ON`
4. 加载/生成 Fernet key
