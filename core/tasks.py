# -*- coding: utf-8 -*-
"""河小智 · 个人任务库（个人事务中心 / 成长档案共用数据层）。

设计说明：
- 每个登录账号（按 account_no 隔离）拥有独立的任务库，落盘为
  ``.data/tasks_<账号>.json``；未登录游客写入 ``tasks_guest.json``。
- 任务字段包含标题、分类、优先级、截止时间、地点、备注、完成状态，
  以及真实的创建时间与完成时间——所有页面展示的统计数字一律由
  这些真实记录实时计算，不在页面上硬编码。
- 任务库不含任何预置/模拟任务：账号首次使用时为空列表，由用户自己新增，
  此后每次增删改都会真实落盘。
"""

from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Any

import streamlit as st

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_ROOT, ".data")

# 分类与优先级的唯一取值；页面上的下拉框与统计都以此为准。
CATEGORIES = ["学习", "生活", "工作", "活动", "其他"]
PRIORITIES = {
    "high": {"label": "高优先级", "short": "高", "tone": "rose", "rank": 0},
    "medium": {"label": "中优先级", "short": "中", "tone": "blue", "rank": 1},
    "low": {"label": "低优先级", "short": "低", "tone": "teal", "rank": 2},
}

_WEEKDAY = "一二三四五六日"


# --------------------------------------------------------------------------- #
# 存储
# --------------------------------------------------------------------------- #
def _owner() -> str:
    user = st.session_state.get("auth_user")
    if isinstance(user, dict) and user.get("account_no"):
        return str(user["account_no"])
    return "guest"


def _store_file() -> str:
    return os.path.join(_DATA_DIR, f"tasks_{_owner()}.json")


def _load_raw() -> list[dict[str, Any]]:
    try:
        with open(_store_file(), "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception:
        return []
    return payload if isinstance(payload, list) else []


def _save(tasks: list[dict[str, Any]]) -> None:
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        tmp = _store_file() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(tasks, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, _store_file())
    except Exception:
        pass


def _tasks() -> list[dict[str, Any]]:
    return _load_raw()


def _valid_due(value: Any) -> str | None:
    """校验截止时间字符串（YYYY-MM-DDTHH:MM），返回规范化结果或 None。"""
    try:
        return datetime.strptime(str(value), "%Y-%m-%dT%H:%M").strftime("%Y-%m-%dT%H:%M")
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- #
# 增删改查
# --------------------------------------------------------------------------- #
def add_task(
    title: str,
    category: str = "其他",
    priority: str = "medium",
    due: str = "",
    place: str = "",
    note: str = "",
) -> dict[str, Any]:
    """新增任务；截止时间缺省为今天 23:59。返回新任务记录。"""
    title = (title or "").strip()
    if not title:
        raise ValueError("任务标题不能为空。")
    if len(title) > 60:
        raise ValueError("任务标题请控制在 60 字以内。")
    if category not in CATEGORIES:
        category = "其他"
    if priority not in PRIORITIES:
        priority = "medium"
    normalized = _valid_due(due) if due else ""
    if due and not normalized:
        raise ValueError("截止时间格式不正确。")
    if not normalized:
        now = datetime.now()
        normalized = now.strftime("%Y-%m-%d") + "T23:59"
    task = {
        "id": "t-" + secrets.token_hex(4),
        "title": title,
        "category": category,
        "priority": priority,
        "due": normalized,
        "place": (place or "").strip()[:40],
        "note": (note or "").strip()[:120],
        "done": False,
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M"),
        "completed_at": None,
    }
    tasks = _tasks()
    tasks.append(task)
    _save(tasks)
    return task


def update_task(
    task_id: str,
    title: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    due: str | None = None,
    place: str | None = None,
    note: str | None = None,
) -> bool:
    """修改任务字段；字段传 None 表示不修改。"""
    tasks = _tasks()
    for task in tasks:
        if task.get("id") != task_id:
            continue
        if title is not None:
            title = title.strip()
            if not title:
                raise ValueError("任务标题不能为空。")
            task["title"] = title[:60]
        if category is not None and category in CATEGORIES:
            task["category"] = category
        if priority is not None and priority in PRIORITIES:
            task["priority"] = priority
        if due is not None:
            normalized = _valid_due(due)
            if not normalized:
                raise ValueError("截止时间格式不正确。")
            task["due"] = normalized
        if place is not None:
            task["place"] = place.strip()[:40]
        if note is not None:
            task["note"] = note.strip()[:120]
        _save(tasks)
        return True
    return False


def delete_task(task_id: str) -> bool:
    tasks = _tasks()
    remaining = [task for task in tasks if task.get("id") != task_id]
    if len(remaining) == len(tasks):
        return False
    _save(remaining)
    return True


def set_done(task_id: str, done: bool) -> bool:
    tasks = _tasks()
    for task in tasks:
        if task.get("id") != task_id:
            continue
        if bool(task.get("done")) == bool(done):
            return False
        task["done"] = bool(done)
        task["completed_at"] = (
            datetime.now().strftime("%Y-%m-%dT%H:%M") if done else None
        )
        _save(tasks)
        return True
    return False


def toggle_task(task_id: str) -> bool:
    """翻转任务完成状态（兼容首页/旧接口）。"""
    tasks = _tasks()
    for task in tasks:
        if task.get("id") == task_id:
            return set_done(task_id, not bool(task.get("done")))
    return False


# --------------------------------------------------------------------------- #
# 查询视图（派生字段统一在这里计算，页面不做二次推断）
# --------------------------------------------------------------------------- #
def _decorate(task: dict[str, Any], now: datetime) -> dict[str, Any]:
    copy = dict(task)
    try:
        due_dt = datetime.strptime(str(task.get("due")), "%Y-%m-%dT%H:%M")
    except (TypeError, ValueError):
        due_dt = now
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    due_day = due_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    copy["due_dt"] = due_dt
    copy["is_today"] = due_day == today
    copy["is_overdue"] = (not copy.get("done")) and due_dt < now
    delta_days = int((due_day - today).days)
    if delta_days == 0:
        copy["due_label"] = f"今天 {due_dt.strftime('%H:%M')}"
    elif delta_days == 1:
        copy["due_label"] = f"明天 {due_dt.strftime('%H:%M')}"
    elif delta_days == -1:
        copy["due_label"] = f"昨天 {due_dt.strftime('%H:%M')} 已过期"
    elif delta_days < 0:
        copy["due_label"] = f"{-delta_days} 天前已过期"
    elif delta_days < 7:
        copy["due_label"] = f"周{_WEEKDAY[due_dt.weekday()]} {due_dt.strftime('%H:%M')}"
    else:
        copy["due_label"] = due_dt.strftime("%m 月 %d 日 %H:%M")
    pri = PRIORITIES.get(str(task.get("priority")), PRIORITIES["medium"])
    copy["priority_label"] = pri["label"]
    copy["priority_short"] = pri["short"]
    copy["priority_tone"] = pri["tone"]
    return copy


def get_tasks(scope: str = "all") -> list[dict[str, Any]]:
    """按范围返回任务列表。

    - ``today``：截止日期是今天或已过期、尚未完成的任务；
    - ``upcoming``：截止日期在今天之后、尚未完成的任务；
    - ``done``：已完成的任务；
    - ``all``：全部任务。
    """
    now = datetime.now()
    tasks = [_decorate(task, now) for task in _tasks()]
    if scope == "today":
        items = [t for t in tasks if (not t["done"]) and (t["is_today"] or t["is_overdue"])]
        items.sort(key=lambda t: (not t["is_overdue"], t["due_dt"], PRIORITIES[t["priority"]]["rank"]))
        return items
    if scope == "upcoming":
        items = [t for t in tasks if (not t["done"]) and (not t["is_today"]) and not t["is_overdue"]]
        items.sort(key=lambda t: (t["due_dt"], PRIORITIES[t["priority"]]["rank"]))
        return items
    if scope == "done":
        items = [t for t in tasks if t["done"]]
        items.sort(key=lambda t: str(t.get("completed_at") or ""), reverse=True)
        return items
    order = {"today": 0, "overdue": 0, "upcoming": 1, "done": 2}
    tasks.sort(
        key=lambda t: (
            order.get("today" if (not t["done"] and (t["is_today"] or t["is_overdue"])) else "upcoming" if not t["done"] else "done"),
            PRIORITIES[t["priority"]]["rank"],
            t["due_dt"],
        )
    )
    return tasks


def todo_progress() -> tuple[int, int]:
    """今日待办完成进度（首页指标条兼容接口）。"""
    now = datetime.now()
    items = [_decorate(task, now) for task in _tasks()]
    today_scope = [t for t in items if (t["is_today"] or t["is_overdue"])]
    done = sum(1 for t in today_scope if t["done"])
    return done, len(today_scope)


def get_task(task_id: str) -> dict[str, Any] | None:
    now = datetime.now()
    for task in _tasks():
        if task.get("id") == task_id:
            return _decorate(task, now)
    return None


# --------------------------------------------------------------------------- #
# 统计（页面可视化与成长档案「任务完成统计」共用）
# --------------------------------------------------------------------------- #
def task_stats() -> dict[str, Any]:
    """由真实任务记录实时计算统计，不做任何硬编码。"""
    now = datetime.now()
    tasks = [_decorate(task, now) for task in _tasks()]
    total = len(tasks)
    done = sum(1 for t in tasks if t["done"])
    open_total = total - done
    overdue = sum(1 for t in tasks if t["is_overdue"])
    rate = int(round(done / total * 100)) if total else 0

    by_priority = {
        key: {"label": pri["label"], "tone": pri["tone"], "total": 0, "done": 0}
        for key, pri in PRIORITIES.items()
    }
    by_category = {name: {"total": 0, "done": 0} for name in CATEGORIES}
    for task in tasks:
        bucket = by_priority.get(task["priority"])
        if bucket:
            bucket["total"] += 1
            bucket["done"] += 1 if task["done"] else 0
        bucket_cat = by_category.setdefault(task["category"], {"total": 0, "done": 0})
        bucket_cat["total"] += 1
        bucket_cat["done"] += 1 if task["done"] else 0

    # 近 7 天每日完成任务数（按完成时间真实统计）
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week: list[dict[str, Any]] = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        count = 0
        for task in tasks:
            completed = str(task.get("completed_at") or "")
            if completed[:10] == day.strftime("%Y-%m-%d"):
                count += 1
        week.append(
            {
                "date": day.strftime("%m-%d"),
                "label": f"周{_WEEKDAY[day.weekday()]}",
                "count": count,
                "is_today": offset == 0,
            }
        )

    upcoming = [
        task
        for task in get_tasks("upcoming") + get_tasks("today")
        if not task["done"]
    ][:5]

    return {
        "total": total,
        "done": done,
        "open": open_total,
        "overdue": overdue,
        "rate": rate,
        "today_done": sum(1 for t in tasks if t["done"] and t["is_today"]),
        "today_total": sum(1 for t in tasks if t["is_today"] or t["is_overdue"]),
        "by_priority": by_priority,
        "by_category": by_category,
        "week": week,
        "upcoming": upcoming,
        "updated_at": now.strftime("%Y-%m-%d %H:%M"),
    }
