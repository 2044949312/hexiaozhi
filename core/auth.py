# -*- coding: utf-8 -*-
"""河小智 · 本地账号注册与登录。

设计说明：
- 账号由注册顺序自动编号，格式为 ``HXZ0001``、``HXZ0002``……
  编号来自数据库自增主键，因此天然按注册先后排列。
- 用户名由用户自行设置，不区分英文大小写且不可重复。
- 密码使用 PBKDF2-HMAC-SHA256 + 随机盐哈希后存储，绝不保存明文。
- 注册时必须设置一组「密保问题 + 密保答案」，用于忘记密码时验证身份；
  密保答案同样只保存加盐哈希，不保存明文。
- 账号数据写入项目根目录 ``.data/accounts.db``，可通过环境变量
  ``HXZ_AUTH_DB`` 指向其他路径（自动化测试使用）。

本项目为黑客松演示作品，正式上线应替换为学校统一身份认证。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
import unicodedata
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

import streamlit as st
import streamlit.components.v1 as components

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(
    os.environ.get("HXZ_AUTH_DB", BASE_DIR / ".data" / "accounts.db")
).expanduser()

PBKDF2_ITERATIONS = 260_000
SESSION_KEY = "auth_user"
SESSION_COOKIE = "hxz_session"
SESSION_MAX_AGE = 30 * 24 * 3600

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_一-鿿]{2,16}$")
_ACCOUNT_RE = re.compile(r"^HXZ(\d{4,})$", re.IGNORECASE)
_RESERVED_USERNAME_RE = re.compile(r"^HXZ\d+$", re.IGNORECASE)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    username             TEXT NOT NULL,
    username_key         TEXT NOT NULL UNIQUE,
    password_hash        TEXT NOT NULL,
    security_question    TEXT,
    security_answer_hash TEXT,
    created_at           TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token      TEXT PRIMARY KEY,
    account_no TEXT NOT NULL,
    username   TEXT NOT NULL,
    initial    TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at REAL NOT NULL
)
"""


class AuthError(Exception):
    """可直接展示给用户的账号操作错误。"""


class RegistrationError(AuthError):
    """注册校验失败。"""


def _migrate_accounts(conn: sqlite3.Connection) -> None:
    """为早期版本的账号表补上密保字段，保留已有账号数据。"""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(accounts)")}
    for column in ("security_question", "security_answer_hash"):
        if column in columns:
            continue
        try:
            conn.execute(f"ALTER TABLE accounts ADD COLUMN {column} TEXT")
        except sqlite3.OperationalError:
            # 并发首次启动时另一个连接可能已完成迁移。
            pass


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.executescript(_SCHEMA)
    _migrate_accounts(conn)
    return conn


@contextmanager
def _db() -> Iterator[sqlite3.Connection]:
    """每次操作使用独立连接；正常结束提交，异常回滚，最后关闭。"""
    conn = _connect()
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    salt_b64 = base64.urlsafe_b64encode(salt).decode("ascii")
    digest_b64 = base64.urlsafe_b64encode(digest).decode("ascii")
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_b64}${digest_b64}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(iterations)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


# 账号不存在时也执行一次同强度哈希，避免通过响应时间判断账号是否注册。
_DUMMY_HASH = _hash_password("hxz-demo-not-a-real-password")


def account_number(account_id: int) -> str:
    """把数据库自增 ID 格式化为按注册顺序排列的账号。"""
    return f"HXZ{int(account_id):04d}"


def _initial(username: str) -> str:
    return username[:1].upper() if username else "河"


def _row_to_user(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "account_no": account_number(row["id"]),
        "username": row["username"],
        "initial": _initial(row["username"]),
        "created_at": row["created_at"],
    }


def _validate_username(raw: str) -> str:
    username = unicodedata.normalize("NFKC", raw or "").strip()
    if not username:
        raise RegistrationError("请先设置用户名。")
    if not _USERNAME_RE.fullmatch(username):
        raise RegistrationError("用户名为 2–16 位，仅支持中文、字母、数字和下划线。")
    if _RESERVED_USERNAME_RE.fullmatch(username):
        raise RegistrationError("用户名不能使用「HXZ + 数字」的账号格式。")
    return username


def validate_password(password: str) -> None:
    if not password:
        raise RegistrationError("请设置密码。")
    if not 8 <= len(password) <= 32:
        raise RegistrationError("密码长度需为 8–32 位。")
    if not any(ch.isalpha() for ch in password) or not any(
        ch.isdigit() for ch in password
    ):
        raise RegistrationError("密码需同时包含字母和数字，以提升账号安全性。")


def _clean_text(raw: str) -> str:
    """统一全角字符并压缩空白，避免「答案看起来一样但无法匹配」。"""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", raw or "").strip())


def _validate_security_question(raw: str) -> str:
    # 问题只用于展示，保留用户习惯的中文标点，不进行全角转半角。
    question = re.sub(r"\s+", " ", (raw or "").strip())
    if not question:
        raise RegistrationError("请设置密保问题，用于忘记密码时验证身份。")
    if not 2 <= len(question) <= 60:
        raise RegistrationError("密保问题需为 2–60 个字符。")
    return question


def _normalize_security_answer(raw: str) -> str:
    """密保答案不区分英文大小写，并忽略首尾及连续空白。"""
    return _clean_text(raw).casefold()


def _validate_security_answer(raw: str) -> str:
    answer = _normalize_security_answer(raw)
    if not answer:
        raise RegistrationError("请设置密保答案。")
    if not 2 <= len(answer) <= 50:
        raise RegistrationError("密保答案需为 2–50 个字符。")
    return answer


def _lookup_account(conn: sqlite3.Connection, identifier: str) -> sqlite3.Row | None:
    """按账号号或用户名查找账号；返回包含密保字段的完整记录。"""
    identifier = unicodedata.normalize("NFKC", identifier or "").strip()
    if not identifier:
        return None
    account_match = _ACCOUNT_RE.fullmatch(identifier)
    if account_match:
        return conn.execute(
            """
            SELECT id, username, password_hash, security_question,
                   security_answer_hash, created_at
            FROM accounts WHERE id = ?
            """,
            (int(account_match.group(1)),),
        ).fetchone()
    return conn.execute(
        """
        SELECT id, username, password_hash, security_question,
               security_answer_hash, created_at
        FROM accounts WHERE username_key = ?
        """,
        (identifier.casefold(),),
    ).fetchone()


def register(
    username: str,
    password: str,
    security_question: str = "",
    security_answer: str = "",
) -> dict[str, Any]:
    """创建账号并返回注册结果（含系统分配的账号号）。

    密保问答为必填项；答案只保存加盐哈希，不保存明文。
    """
    username = _validate_username(username)
    validate_password(password)
    question = _validate_security_question(security_question)
    answer = _validate_security_answer(security_answer)
    username_key = username.casefold()
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")

    try:
        with _db() as conn:
            cursor = conn.execute(
                """
                INSERT INTO accounts (
                    username, username_key, password_hash,
                    security_question, security_answer_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    username_key,
                    _hash_password(password),
                    question,
                    _hash_password(answer),
                    created_at,
                ),
            )
            account_id = int(cursor.lastrowid)
            row = conn.execute(
                "SELECT id, username, created_at FROM accounts WHERE id = ?",
                (account_id,),
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise RegistrationError("该用户名已被使用，请换一个用户名。") from exc

    if row is None:  # pragma: no cover - 写入后立即读取，正常不会发生
        raise RegistrationError("账号创建失败，请稍后重试。")
    return _row_to_user(row)


def get_security_question(identifier: str) -> dict[str, Any] | None:
    """查询账号的密保问题；账号不存在返回 None。

    不返回密保答案或任何哈希值。老版本账号可能尚未设置密保问题，
    此时 ``question`` 为空字符串。
    """
    with _db() as conn:
        row = _lookup_account(conn, identifier)
    if row is None:
        return None
    return {
        "account_no": account_number(row["id"]),
        "username": row["username"],
        "question": str(row["security_question"] or ""),
    }


def reset_password(identifier: str, security_answer: str, new_password: str) -> dict[str, Any]:
    """验证密保答案并重置密码；成功后返回账号信息。"""
    validate_password(new_password)
    answer = _normalize_security_answer(security_answer)
    if not answer:
        raise AuthError("请输入密保答案。")

    with _db() as conn:
        row = _lookup_account(conn, identifier)
        if row is None:
            raise AuthError("该账号不存在，请确认账号号或用户名。")
        stored_answer = str(row["security_answer_hash"] or "")
        if not row["security_question"] or not stored_answer:
            raise AuthError("该账号尚未设置密保问题，暂时无法自助找回密码。")
        if not _verify_password(answer, stored_answer):
            raise AuthError("密保答案不正确，请重新输入。")

        conn.execute(
            "UPDATE accounts SET password_hash = ? WHERE id = ?",
            (_hash_password(new_password), row["id"]),
        )
        # 密码变更后注销该账号的全部登录 Cookie 会话。
        conn.execute(
            "DELETE FROM sessions WHERE account_no = ?",
            (account_number(row["id"]),),
        )
        user = _row_to_user(row)
    return user


def authenticate(identifier: str, password: str) -> dict[str, Any] | None:
    """用账号号或用户名 + 密码登录；失败返回 None。"""
    identifier = unicodedata.normalize("NFKC", identifier or "").strip()
    if not identifier or not password:
        return None

    row: sqlite3.Row | None = None
    with _db() as conn:
        account_match = _ACCOUNT_RE.fullmatch(identifier)
        if account_match:
            row = conn.execute(
                "SELECT id, username, password_hash, created_at FROM accounts WHERE id = ?",
                (int(account_match.group(1)),),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT id, username, password_hash, created_at
                FROM accounts
                WHERE username_key = ?
                """,
                (identifier.casefold(),),
            ).fetchone()

    stored_hash = row["password_hash"] if row is not None else _DUMMY_HASH
    password_ok = _verify_password(password, stored_hash)
    if row is None or not password_ok:
        return None
    return _row_to_user(row)


def account_count() -> int:
    with _db() as conn:
        row = conn.execute("SELECT COUNT(*) AS total FROM accounts").fetchone()
    return int(row["total"]) if row is not None else 0


# ---------- Streamlit 会话 ----------


def _write_cookie(token: str) -> None:
    """通过同源 iframe 写入登录 Cookie，让整页跳转后仍保持登录。"""
    value = f"{SESSION_COOKIE}={token}; path=/; max-age={SESSION_MAX_AGE}; SameSite=Lax"
    if not token:
        value = f"{SESSION_COOKIE}=; path=/; max-age=0; SameSite=Lax"
    try:
        components.html(
            f"""
<script>
(function () {{
  var value = {value!r};
  try {{ document.cookie = value; }} catch (err) {{}}
  try {{ window.parent.document.cookie = value; }} catch (err) {{}}
}})();
</script>
""",
            height=0,
        )
    except Exception:
        pass


def _read_cookie() -> str:
    try:
        cookies = st.context.cookies
        value = cookies.get(SESSION_COOKIE) if cookies else None
    except Exception:
        value = None
    return str(value) if value else ""


def _create_session(user: dict[str, Any]) -> str:
    token = secrets.token_urlsafe(32)
    payload = {
        "account_no": str(user.get("account_no") or ""),
        "username": str(user.get("username") or ""),
        "initial": str(user.get("initial") or ""),
        "created_at": str(user.get("created_at") or ""),
    }
    if not payload["account_no"]:
        return ""
    try:
        with _db() as conn:
            conn.execute("DELETE FROM sessions WHERE expires_at < ?", (time.time(),))
            conn.execute(
                "INSERT OR REPLACE INTO sessions "
                "(token, account_no, username, initial, created_at, expires_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    token,
                    payload["account_no"],
                    payload["username"],
                    payload["initial"],
                    payload["created_at"],
                    time.time() + SESSION_MAX_AGE,
                ),
            )
    except Exception:
        return ""
    return token


def _load_session(token: str) -> dict[str, Any] | None:
    if not token:
        return None
    try:
        with _db() as conn:
            row = conn.execute(
                "SELECT account_no, username, initial, created_at "
                "FROM sessions WHERE token = ? AND expires_at > ?",
                (token, time.time()),
            ).fetchone()
    except Exception:
        return None
    if row is None:
        return None
    return {
        "account_no": row["account_no"],
        "username": row["username"],
        "initial": row["initial"],
        "created_at": row["created_at"],
    }


def current_user() -> dict[str, Any] | None:
    """返回当前浏览器会话的登录用户，未登录时返回 None。

    优先读 ``st.session_state``；整页跳转 / 刷新导致会话丢失时，
    再通过浏览器 Cookie 中的会话 token 自动恢复登录。
    """
    user = st.session_state.get(SESSION_KEY)
    if not (isinstance(user, dict) and user.get("account_no")):
        user = _load_session(_read_cookie())
        if user:
            st.session_state[SESSION_KEY] = user
            st.session_state["_auth_cookie_written"] = True

    if isinstance(user, dict) and user.get("account_no"):
        # 登录后的第一次渲染必须真正把 Cookie 发给浏览器。登录表单提交后会立刻
        # st.rerun()，登录那一轮的组件不会下发，所以在这里补写一次。
        if not st.session_state.get("_auth_cookie_written"):
            token = _create_session(user)
            if token:
                _write_cookie(token)
                st.session_state["_auth_cookie_written"] = True
        return user
    return None


def start_session(user: dict[str, Any]) -> None:
    payload = {
        key: user[key]
        for key in ("account_no", "username", "initial", "created_at")
        if key in user
    }
    st.session_state[SESSION_KEY] = payload
    st.session_state["_auth_cookie_written"] = False


def end_session() -> None:
    token = _read_cookie()
    if token:
        try:
            with _db() as conn:
                conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        except Exception:
            pass
    st.session_state.pop(SESSION_KEY, None)
    st.session_state.pop("_auth_cookie_written", None)
    _write_cookie("")
