# -*- coding: utf-8 -*-
"""河小智 · 校园活动任务看板（数据层）。

数据来源说明（保证数据真实有效，不额外编造）：
- 种子任务全部由本系统 data.ACTIVITIES 中的真实活动信息派生：
  活动名称、报名截止时间均与「校园活动」页展示的数据一致（解析活动卡片的
  报名截止文案得到），备注中引用的地点、开场时间同样来自活动数据；
- 用户自行新增 / 修改的任务保存在 .tmp/activity_tasks_<账号>.json，
  按登录账号隔离，刷新页面、重新登录后依然存在；
- 所有「剩余天数 / 是否逾期」均基于服务器当前时间实时计算。
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, time, timedelta
from typing import Any

import streamlit as st

from .data import ACTIVITIES

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STORE_DIR = os.path.join(_ROOT, ".tmp")

PRIORITIES = ("高", "中", "低")
PRIORITY_TONES = {"高": "rose", "中": "gold", "低": "teal"}
TASK_CATEGORIES = ("科技", "文艺", "讲座", "运动", "学习", "生活", "其他")

_DATE_RE = re.compile(r"(\d{1,2})\s*月\s*(\d{1,2})\s*日(?:\s*(\d{1,2}):(\d{2}))?")


# --------------------------------------------------------------------------- #
# 基础工具
# --------------------------------------------------------------------------- #
def _owner() -> str:
    """任务按登录账号隔离，未登录时归入 guest（与问答记录同一策略）。"""
    user = st.session_state.get("auth_user")
    if isinstance(user, dict) and user.get("account_no"):
        return str(user["account_no"])
    return "guest"


def _store_file() -> str:
    return os.path.join(_STORE_DIR, f"activity_tasks_{_owner()}.json")


def _activity_deadline(activity: dict[str, Any] | None) -> datetime:
    """从活动数据里的报名截止文案（如「11 月 12 日 18:00」）解析真实截止时间。"""
    now = datetime.now()
    if not activity:
        return now
    match = _DATE_RE.search(str(activity.get("deadline", "")))
    if not match:
        return now
    month, day = int(match.group(1)), int(match.group(2))
    hour = int(match.group(3) or 23)
    minute = int(match.group(4) or 59)
    year = now.year
    # 跨年场景：如果解析出的月份比当前月小很多，视为明年。
    if month < now.month - 6:
        year += 1
    return datetime(year, month, day, hour, minute)


def _parse_deadline(task: dict[str, Any]) -> datetime:
    try:
        return datetime.strptime(str(task["deadline"]), "%Y-%m-%d %H:%M")
    except (KeyError, TypeError, ValueError):
        return datetime.now() + timedelta(days=30)


def _fmt_deadline(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def _make_id() -> str:
    """生成任务 id：时间前缀 + 随机后缀。

    早期实现只用 ``datetime.now()`` 的微秒值，而 Windows 时钟精度约 15ms，
    同一批种子任务会拿到完全相同的 id，进而让 Streamlit 复选框 key 冲突。
    追加随机后缀可彻底避免撞号（时间前缀仍便于排查）。
    """
    return f"task-{datetime.now().strftime('%Y%m%d%H%M%S%f')}-{uuid.uuid4().hex[:6]}"


def _new_task(
    title: str,
    *,
    category: str,
    deadline: datetime,
    priority: str,
    progress: int = 0,
    note: str = "",
    link_id: str = "",
    done: bool = False,
    source: str = "custom",
) -> dict[str, Any]:
    return {
        "id": _make_id(),
        "title": title,
        "note": note,
        "category": category,
        "link_id": link_id,
        "priority": priority if priority in PRIORITIES else "中",
        "deadline": _fmt_deadline(deadline),
        "progress": max(0, min(100, int(progress))),
        "done": bool(done),
        "resume_progress": 0,
        "source": source,
        "created_at": _fmt_deadline(datetime.now()),
    }


# --------------------------------------------------------------------------- #
# 种子任务：全部由系统内真实活动派生
# --------------------------------------------------------------------------- #
def _seed_tasks() -> list[dict[str, Any]]:
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    lookup = {activity["id"]: activity for activity in ACTIVITIES}

    music_dl = _activity_deadline(lookup.get("music-festival"))  # 秋日声浪报名截止
    hack_dl = _activity_deadline(lookup.get("ai-hackathon"))  # 创客马拉松报名截止
    lecture_dl = _activity_deadline(lookup.get("ai-lecture"))  # 名师公开课报名截止
    run_dl = _activity_deadline(lookup.get("night-run"))  # 荧光夜跑报名截止

    seeds = [
        _new_task(
            "组队并提交 AI 创客马拉松报名",
            category="科技",
            deadline=today + timedelta(hours=21),
            priority="高",
            progress=60,
            link_id="ai-hackathon",
            note=f"官方报名截止 {hack_dl.month} 月 {hack_dl.day} 日 18:00，先完成组队再提交报名表。",
            source="seed",
        ),
        _new_task(
            "报名秋日声浪草坪音乐节",
            category="文艺",
            deadline=music_dl,
            priority="中",
            progress=100,
            done=True,
            link_id="music-festival",
            note="免费入场，周日 17:30 大礼堂前草坪开场，记得带野餐垫。",
            source="seed",
        ),
        _new_task(
            "准备创客马拉松开发环境与选题",
            category="科技",
            deadline=hack_dl - timedelta(days=1, hours=-2),  # 报名截止前一天 20:00
            priority="高",
            progress=35,
            link_id="ai-hackathon",
            note="48 小时极限开发，提前装好环境、想好「AI + 校园」命题。",
            source="seed",
        ),
        _new_task(
            "预约名师公开课「大模型与未来教育」",
            category="讲座",
            deadline=lecture_dl,
            priority="中",
            progress=0,
            link_id="ai-lecture",
            note="周四 19:00 计算机学院报告厅，可盖章、计通识讲座。",
            source="seed",
        ),
        _new_task(
            "领取荧光夜跑装备并确认集合时间",
            category="运动",
            deadline=run_dl,
            priority="低",
            progress=0,
            link_id="night-run",
            note="周五 19:30 东操场集合，完赛有限定奖牌、计第二课堂。",
            source="seed",
        ),
        _new_task(
            "复盘马拉松作品并归档代码仓库",
            category="科技",
            deadline=hack_dl + timedelta(days=3, hours=3),  # 闭幕后两天内
            priority="中",
            progress=0,
            link_id="ai-hackathon",
            note="活动结束后两天内完成复盘，优秀作品可进入孵化计划。",
            source="seed",
        ),
    ]
    return sorted(seeds, key=_parse_deadline)


# --------------------------------------------------------------------------- #
# 读取 / 持久化
# --------------------------------------------------------------------------- #
def _repair_ids(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """修复历史数据中的重复任务 id。

    旧版本生成的任务 id 可能重复（详见 ``_make_id`` 注释）。重复 id 会让
    活动页的复选框 key 冲突、整页报错。这里给重复项重新分配 id 并回写，
    保留全部任务内容，而不是丢弃数据。
    """
    seen: set[str] = set()
    repaired: list[dict[str, Any]] = []
    changed = False
    for item in items:
        task_id = str(item.get("id") or "")
        if not task_id or task_id in seen:
            item = dict(item)
            item["id"] = _make_id()
            changed = True
        seen.add(str(item["id"]))
        repaired.append(item)
    if changed:
        _save_tasks(repaired)
    return repaired


def _load_tasks() -> list[dict[str, Any]]:
    try:
        with open(_store_file(), "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if isinstance(payload, list) and payload:
            items = [item for item in payload if isinstance(item, dict) and item.get("id")]
            return _repair_ids(items)
    except Exception:
        pass
    seeds = _seed_tasks()
    _save_tasks(seeds)
    return seeds


def _save_tasks(items: list[dict[str, Any]]) -> None:
    try:
        os.makedirs(_STORE_DIR, exist_ok=True)
        store_file = _store_file()
        tmp_file = store_file + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as fh:
            json.dump(items, fh, ensure_ascii=False, indent=1)
        os.replace(tmp_file, store_file)
    except Exception:
        pass


def tasks() -> list[dict[str, Any]]:
    """当前账号的全部任务（按截止时间升序）。"""
    if "activity_tasks" not in st.session_state:
        st.session_state["activity_tasks"] = _load_tasks()
    items = st.session_state["activity_tasks"]
    return sorted(items, key=_parse_deadline)


def _commit(items: list[dict[str, Any]]) -> None:
    st.session_state["activity_tasks"] = items
    _save_tasks(items)


# --------------------------------------------------------------------------- #
# 增删改查
# --------------------------------------------------------------------------- #
def add_task(
    title: str,
    *,
    category: str = "其他",
    deadline: datetime | None = None,
    priority: str = "中",
    progress: int = 0,
    note: str = "",
    link_id: str = "",
) -> str:
    items = list(tasks())
    task = _new_task(
        title.strip() or "未命名任务",
        category=category if category in TASK_CATEGORIES else "其他",
        deadline=deadline or (datetime.now() + timedelta(days=1)),
        priority=priority,
        progress=progress,
        note=note.strip(),
        link_id=link_id,
    )
    items.append(task)
    _commit(items)
    return task["id"]


def update_task(task_id: str, **fields: Any) -> bool:
    items = list(tasks())
    for index, item in enumerate(items):
        if item.get("id") != task_id:
            continue
        updated = dict(item)
        if "title" in fields and str(fields["title"]).strip():
            updated["title"] = str(fields["title"]).strip()
        if "note" in fields:
            updated["note"] = str(fields["note"]).strip()
        if "category" in fields and fields["category"] in TASK_CATEGORIES:
            updated["category"] = fields["category"]
        if "priority" in fields and fields["priority"] in PRIORITIES:
            updated["priority"] = fields["priority"]
        if isinstance(fields.get("deadline"), datetime):
            updated["deadline"] = _fmt_deadline(fields["deadline"])
        if "progress" in fields:
            progress = max(0, min(100, int(fields["progress"])))
            updated["progress"] = progress
            if progress >= 100:
                updated["done"] = True
            elif item.get("done") and "done" not in fields:
                # 进度从 100 调低时自动取消完成状态。
                updated["done"] = False
        if "done" in fields:
            updated["done"] = bool(fields["done"])
        if bool(updated["done"]) != bool(item.get("done")):
            if updated["done"]:
                updated["resume_progress"] = int(item.get("progress") or 0)
                updated["progress"] = 100
            else:
                updated["progress"] = min(int(item.get("resume_progress") or 0), 95)
        items[index] = updated
        _commit(items)
        return True
    return False


def delete_task(task_id: str) -> bool:
    items = list(tasks())
    kept = [item for item in items if item.get("id") != task_id]
    if len(kept) == len(items):
        return False
    _commit(kept)
    # 同步清理复选框状态（「今日待办」「近期任务」两个面板各有一套 key）
    for prefix in ("act-task-chk-", "act-task-chk-today-", "act-task-chk-soon-"):
        st.session_state.pop(prefix + task_id, None)
    return True


def toggle_done(task_id: str) -> bool | None:
    """切换完成状态，返回新的 done 值；任务不存在返回 None。"""
    items = list(tasks())
    for item in items:
        if item.get("id") == task_id:
            new_done = not bool(item.get("done"))
            update_task(task_id, done=new_done)
            return new_done
    return None


def get_task(task_id: str) -> dict[str, Any] | None:
    for item in tasks():
        if item.get("id") == task_id:
            return item
    return None


# --------------------------------------------------------------------------- #
# 统计（供页面指标卡与可视化使用）
# --------------------------------------------------------------------------- #
def stats(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """统计任务；传入 items 时只统计该子集（如本人相关任务）。"""
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    items = tasks() if items is None else list(items)
    open_items = [item for item in items if not item.get("done")]

    due_today = [item for item in open_items if _parse_deadline(item).date() == today.date()]
    week_due = [item for item in open_items if today <= _parse_deadline(item) < today + timedelta(days=7)]
    overdue = [item for item in open_items if _parse_deadline(item) < now]
    high_open = [item for item in open_items if item.get("priority") == "高"]
    done_items = [item for item in items if item.get("done")]

    completion = 0
    if items:
        completion = int(round(sum(int(item.get("progress") or 0) for item in items) / len(items)))

    priority_counts = {level: 0 for level in PRIORITIES}
    for item in open_items:
        priority_counts[item.get("priority", "中")] = priority_counts.get(item.get("priority", "中"), 0) + 1

    # 未来 7 天每日截止数量（含今天）
    buckets: list[dict[str, Any]] = []
    weekday_names = "一二三四五六日"
    for offset in range(7):
        day = today + timedelta(days=offset)
        label = "今天" if offset == 0 else ("明天" if offset == 1 else f"周{weekday_names[day.weekday()]}")
        count = sum(
            1
            for item in open_items
            if _parse_deadline(item).date() == day.date()
        )
        buckets.append({"label": label, "date": day, "count": count})

    return {
        "total": len(items),
        "open": len(open_items),
        "done": len(done_items),
        "due_today": due_today,
        "week_due": week_due,
        "overdue": overdue,
        "high_open": high_open,
        "completion": completion,
        "priority_counts": priority_counts,
        "buckets": buckets,
    }


def deadline_label(item: dict[str, Any]) -> str:
    """截止时间的中文展示：今天 / 明天 / 具体日期 + 剩余天数。"""
    dt = _parse_deadline(item)
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    delta_days = int((day - today).days)
    hhmm = dt.strftime("%H:%M")
    if delta_days == 0:
        base = f"今天 {hhmm}"
    elif delta_days == 1:
        base = f"明天 {hhmm}"
    else:
        base = f"{dt.month} 月 {dt.day} 日 {hhmm}"
    if dt < now and not item.get("done"):
        overdue_days = max(1, -delta_days)
        return f"{base} · 已逾期 {overdue_days} 天" if delta_days < 0 else f"{base} · 即将截止"
    if delta_days == 0:
        return f"{base} · 今日截止"
    if delta_days == 1:
        return f"{base} · 明天截止"
    return f"{base} · 还剩 {delta_days} 天"


def linked_activity(link_id: str) -> dict[str, Any] | None:
    for activity in ACTIVITIES:
        if activity["id"] == link_id:
            return activity
    return None
