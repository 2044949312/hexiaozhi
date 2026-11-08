# -*- coding: utf-8 -*-
"""河小智 · 会话状态管理。"""

from __future__ import annotations

import json
import os
from typing import Any

import streamlit as st

from .data import ACTIVITIES
from . import tasks as task_store

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STORE_DIR = os.path.join(_ROOT, ".tmp")
_DATA_DIR = os.path.join(_ROOT, ".data")
_MAX_MESSAGES = 30
_MAX_DOC_CHARS = 60000


def _reg_file() -> str:
    """活动报名记录按账号持久化，刷新 / 重登后仍然保留。"""
    return os.path.join(_DATA_DIR, f"registrations_{_qa_owner()}.json")


def _load_registrations() -> list[str]:
    try:
        with open(_reg_file(), "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if isinstance(payload, list):
            valid = {str(item["id"]) for item in ACTIVITIES}
            return [str(item) for item in payload if str(item) in valid]
    except Exception:
        pass
    return []


def _save_registrations() -> None:
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        path = _reg_file()
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(list(st.session_state.get("registrations") or []), fh, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        pass


def _qa_owner() -> str:
    """问答记录按账号隔离，避免不同同学之间串对话。"""
    user = st.session_state.get("auth_user")
    if isinstance(user, dict) and user.get("account_no"):
        return str(user["account_no"])
    return "guest"


def _store_file() -> str:
    return os.path.join(_STORE_DIR, f"qa_session_{_qa_owner()}.json")


def init_state() -> None:
    # 待办已迁移到 core.tasks（按账号持久化到 .data/tasks_*.json），
    # 这里只保留会话级状态：活动报名、问答历史等。
    if "registrations" not in st.session_state:
        st.session_state.registrations = []
    if "qa_messages" not in st.session_state:
        st.session_state.qa_messages = []
    if "qa_last_question" not in st.session_state:
        st.session_state.qa_last_question = ""
    if "last_toggle_token" not in st.session_state:
        st.session_state.last_toggle_token = ""
    # 切换账号时清空上一账号的会话，再从该账号自己的存档恢复。
    owner = _qa_owner()
    if st.session_state.get("qa_owner") != owner:
        st.session_state.qa_owner = owner
        st.session_state.qa_messages = []
        st.session_state.qa_docs = []
        st.session_state.qa_last_question = ""
        st.session_state.qa_session_no = 1
        st.session_state.registrations = _load_registrations()
        qa_restore()


# ---- 待办任务：委托给 core.tasks 的持久化任务库 ----
def get_todos() -> list[dict[str, Any]]:
    """兼容旧接口：返回今日待办（含过期未完成）。"""
    return task_store.get_tasks("today")


def todo_progress() -> tuple[int, int]:
    """今日待办完成进度（首页指标条使用）。"""
    return task_store.todo_progress()


def toggle_todo(todo_id: str) -> bool:
    """兼容旧接口：翻转任务完成状态。"""
    return task_store.toggle_task(todo_id)


def handle_toggle_param() -> None:
    """处理首页待办的一次性 toggle 查询参数，防止 rerun 重复翻转。"""
    init_state()
    todo_id = st.query_params.get("toggle", "")
    token = st.query_params.get("token", "")
    if isinstance(todo_id, list):
        todo_id = todo_id[0] if todo_id else ""
    if isinstance(token, list):
        token = token[0] if token else ""
    if todo_id and token and token != st.session_state.last_toggle_token:
        st.session_state.last_toggle_token = token
        toggle_todo(str(todo_id))


def registrations() -> list[str]:
    init_state()
    return list(st.session_state.registrations)


def register_activity(activity_id: str) -> bool:
    """返回 True 表示本次新报名成功，False 表示已报名。"""
    init_state()
    valid_ids = {item["id"] for item in ACTIVITIES}
    if activity_id not in valid_ids:
        return False
    if activity_id in st.session_state.registrations:
        return False
    st.session_state.registrations.append(activity_id)
    _save_registrations()
    return True


def is_registered(activity_id: str) -> bool:
    init_state()
    return activity_id in st.session_state.registrations


def unregister_activity(activity_id: str) -> bool:
    """取消报名；返回 True 表示本次确实取消了一场已报名活动。"""
    init_state()
    if activity_id not in st.session_state.registrations:
        return False
    st.session_state.registrations = [x for x in st.session_state.registrations if x != activity_id]
    _save_registrations()
    return True


def qa_history() -> list[dict[str, Any]]:
    init_state()
    return st.session_state.qa_messages


def append_qa(question: str, result: dict[str, Any]) -> None:
    init_state()
    history = st.session_state.qa_messages
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": result})
    if len(history) > _MAX_MESSAGES:
        st.session_state.qa_messages = history[-_MAX_MESSAGES:]
    st.session_state.qa_last_question = question
    qa_persist()


def clear_qa() -> None:
    init_state()
    st.session_state.qa_messages = []
    st.session_state.qa_last_question = ""
    qa_persist()


# --------------------------------------------------------------------------- #
# 智能问答：上传资料 / 会话持久化
# --------------------------------------------------------------------------- #
def qa_docs() -> list[dict[str, Any]]:
    init_state()
    docs = st.session_state.get("qa_docs")
    if not isinstance(docs, list):
        docs = []
        st.session_state.qa_docs = docs
    return docs


def qa_add_doc(doc: dict[str, Any]) -> None:
    """登记上传资料：同名覆盖，最多保留 5 份。"""
    init_state()
    if not isinstance(doc, dict):
        return
    docs = [d for d in qa_docs() if str(d.get("name") or "") != str(doc.get("name") or "")]
    docs.append(doc)
    st.session_state.qa_docs = docs[-5:]
    st.session_state.pop("qa_upload_error", None)
    qa_persist()


def qa_remove_doc(doc_id: str) -> None:
    init_state()
    st.session_state.qa_docs = [d for d in qa_docs() if str(d.get("id") or "") != str(doc_id)]
    qa_persist()


def qa_clear_docs() -> None:
    init_state()
    st.session_state.qa_docs = []
    st.session_state.pop("qa_upload_digests", None)
    qa_persist()


def qa_new_session() -> str:
    """清空问答与上传资料，开启一轮新对话，返回新会话 id。"""
    init_state()
    st.session_state.qa_messages = []
    st.session_state.qa_docs = []
    st.session_state.qa_last_question = ""
    st.session_state.pop("qa_upload_digests", None)
    st.session_state.pop("qa_upload_error", None)
    st.session_state.pop("qa_upload_ok", None)
    st.session_state.qa_session_no = int(st.session_state.get("qa_session_no") or 1) + 1
    qa_persist()
    return f"qa-{st.session_state.qa_session_no}"


def qa_session_no() -> int:
    init_state()
    try:
        return max(1, int(st.session_state.get("qa_session_no") or 1))
    except (TypeError, ValueError):
        return 1


def qa_last_result() -> dict[str, Any] | None:
    init_state()
    for message in reversed(st.session_state.qa_messages):
        if message.get("role") == "assistant" and isinstance(message.get("content"), dict):
            return message["content"]
    return None


def _trim_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    trimmed: list[dict[str, Any]] = []
    for message in messages[-_MAX_MESSAGES:]:
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, dict):
            copy = dict(content)
            retrieval = copy.get("retrieval")
            if isinstance(retrieval, list):
                copy["retrieval"] = retrieval[:6]
            attachments = copy.get("attachments")
            if isinstance(attachments, list):
                copy["attachments"] = attachments[:2]
            content = copy
        trimmed.append({"role": message.get("role"), "content": content})
    return trimmed


def _trim_docs(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    trimmed: list[dict[str, Any]] = []
    total = 0
    for doc in docs[:5]:
        if not isinstance(doc, dict):
            continue
        copy = dict(doc)
        chunks = []
        for chunk in (doc.get("chunks") or [])[:20]:
            if not isinstance(chunk, dict):
                continue
            text = str(chunk.get("text") or "")
            if total + len(text) > _MAX_DOC_CHARS:
                text = text[: max(0, _MAX_DOC_CHARS - total)]
            if text:
                chunks.append({"page": chunk.get("page") or 1, "text": text})
                total += len(text)
            if total >= _MAX_DOC_CHARS:
                break
        copy["chunks"] = chunks
        trimmed.append(copy)
        if total >= _MAX_DOC_CHARS:
            break
    return trimmed


def qa_persist() -> None:
    """把对话与上传资料写入 .tmp/qa_session.json（失败时静默忽略）。"""
    try:
        payload = {
            "messages": _trim_messages(qa_history()),
            "docs": _trim_docs(qa_docs()),
            "session_no": qa_session_no(),
        }
        os.makedirs(_STORE_DIR, exist_ok=True)
        store_file = _store_file()
        tmp_file = store_file + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, default=str)
        os.replace(tmp_file, store_file)
    except Exception:
        pass


def qa_restore() -> None:
    """仅当本次会话还没有消息时，从磁盘恢复上次的对话。"""
    try:
        with open(_store_file(), "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception:
        return
    if not isinstance(payload, dict):
        return
    messages = payload.get("messages")
    if isinstance(messages, list) and messages and not st.session_state.get("qa_messages"):
        st.session_state.qa_messages = _trim_messages(messages)
    docs = payload.get("docs")
    if isinstance(docs, list) and docs and not st.session_state.get("qa_docs"):
        st.session_state.qa_docs = _trim_docs(docs)
    try:
        st.session_state.qa_session_no = max(1, int(payload.get("session_no") or 1))
    except (TypeError, ValueError):
        st.session_state.qa_session_no = 1
