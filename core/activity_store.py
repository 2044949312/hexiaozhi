# -*- coding: utf-8 -*-
"""河小智 · 学生自建活动数据层。

官方活动来自 ``core.data.ACTIVITIES``（只读演示数据）；同学们自己发起的
活动保存在 ``.data/activities_<账号>.json``，按登录账号隔离，刷新页面或
重新登录后依然保留。

这里只负责「我的活动」中的创建 / 删除；报名状态仍由 ``core.state`` 管理。
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import date, datetime, time
from typing import Any

import streamlit as st

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_ROOT, ".data")

CATEGORIES = ("科技", "文艺", "讲座", "运动", "其他")

_COVER_BY_CATEGORY = {
    "科技": "activity-ai.svg",
    "文艺": "activity-music.svg",
    "讲座": "activity-lecture.svg",
    "运动": "activity-run.svg",
    "其他": "activity-ai.svg",
}
_ACCENT_BY_CATEGORY = {
    "科技": "#2563EB",
    "文艺": "#F59E0B",
    "讲座": "#14B8A6",
    "运动": "#22C55E",
    "其他": "#7C3AED",
}
_WEEKDAYS = "一二三四五六日"


def _owner() -> str:
    """自建活动按登录账号隔离，未登录时归入 guest（与问答记录同一策略）。"""
    user = st.session_state.get("auth_user")
    if isinstance(user, dict) and user.get("account_no"):
        return str(user["account_no"])
    return "guest"


def _store_file() -> str:
    return os.path.join(_DATA_DIR, f"activities_{_owner()}.json")


def _load() -> list[dict[str, Any]]:
    try:
        with open(_store_file(), "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict) and item.get("id")]
    except Exception:
        pass
    return []


def _save(items: list[dict[str, Any]]) -> None:
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        path = _store_file()
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(items, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
    except Exception:
        pass


def created_activities() -> list[dict[str, Any]]:
    """当前账号创建的活动（按创建时间倒序，最新的在前）。"""
    owner = _owner()
    if st.session_state.get("created_activities_owner") != owner:
        st.session_state["created_activities_owner"] = owner
        st.session_state["created_activities"] = _load()
    items = st.session_state.get("created_activities")
    if not isinstance(items, list):
        items = []
        st.session_state["created_activities"] = items
    return list(items)


def _commit(items: list[dict[str, Any]]) -> None:
    st.session_state["created_activities"] = items
    st.session_state["created_activities_owner"] = _owner()
    _save(items)


def _split_tags(raw: str) -> list[str]:
    tags = [part.strip() for part in re.split(r"[,，、;；\s]+", str(raw or "")) if part.strip()]
    return tags[:4]


def _format_date(value: date) -> str:
    return f"{value.month} 月 {value.day} 日"


def _format_time(value: time) -> str:
    return value.strftime("%H:%M")


def _is_recent(item: dict[str, Any], seconds: int = 120) -> bool:
    """判断活动是否在最近 seconds 秒内创建（用于拦截重复提交）。"""
    try:
        created = datetime.strptime(str(item.get("created_at", "")), "%Y-%m-%d %H:%M")
    except (TypeError, ValueError):
        return False
    return abs((datetime.now() - created).total_seconds()) <= seconds


def add_activity(
    title: str,
    *,
    category: str,
    activity_date: date,
    start_time: time,
    location: str,
    capacity: int,
    deadline_date: date,
    deadline_time: time,
    detail: str = "",
    tags: str = "",
) -> dict[str, Any]:
    """创建一场活动并立即持久化，返回活动字典。"""
    category = category if category in CATEGORIES else "其他"
    title = str(title or "").strip() or "未命名活动"
    detail = str(detail or "").strip()
    tag_list = _split_tags(tags)
    if "学生自建" not in tag_list:
        tag_list = ["学生自建"] + tag_list
    activity = {
        "id": f"custom-{uuid.uuid4().hex[:12]}",
        "category": category,
        "title": title,
        "summary": detail[:48] if detail else f"{category} · 学生自建活动",
        "date": _format_date(activity_date),
        "time": f"周{_WEEKDAYS[activity_date.weekday()]} {_format_time(start_time)} 开始",
        "location": str(location or "").strip() or "地点待定",
        "participants": 0,
        "capacity": max(1, int(capacity or 1)),
        "deadline": f"{_format_date(deadline_date)} {_format_time(deadline_time)}",
        "tags": tag_list[:4],
        "cover": _COVER_BY_CATEGORY.get(category, "activity-ai.svg"),
        "accent": _ACCENT_BY_CATEGORY.get(category, "#7C3AED"),
        "hot": False,
        "detail": detail or "活动详情待补充，欢迎同学们在活动开始前关注最新通知。",
        "source": "student",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    items = created_activities()
    # 防重复：同一名称 / 时间 / 地点在 2 分钟内的重复提交不再新增记录。
    for existing in items:
        if (
            str(existing.get("title")) == activity["title"]
            and str(existing.get("date")) == activity["date"]
            and str(existing.get("time")) == activity["time"]
            and str(existing.get("location")) == activity["location"]
            and _is_recent(existing)
        ):
            return existing
    items.insert(0, activity)
    _commit(items)
    return activity


def delete_activity(activity_id: str) -> bool:
    items = created_activities()
    kept = [item for item in items if str(item.get("id")) != str(activity_id)]
    if len(kept) == len(items):
        return False
    _commit(kept)
    return True


def get_activity(activity_id: str) -> dict[str, Any] | None:
    for item in created_activities():
        if str(item.get("id")) == str(activity_id):
            return item
    return None
