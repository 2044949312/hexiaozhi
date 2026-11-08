# -*- coding: utf-8 -*-
"""河小智 · 任务数据可视化组件（个人事务中心 / 成长档案共用）。

所有图表的数字都来自 core.tasks.task_stats() 的实时计算，
组件本身不做任何数据推断或硬编码。
"""

from __future__ import annotations

from . import ui

_BAR_TONES = {
    "rose": "var(--rose)",
    "blue": "var(--primary-2)",
    "teal": "var(--teal)",
    "violet": "var(--violet)",
    "gold": "#C88B15",
    "green": "#16A34A",
}


def _hbar(label: str, value: int, total: int, tone: str, foot: str = "") -> str:
    percent = int(round(value / total * 100)) if total else 0
    color = _BAR_TONES.get(tone, "var(--primary-2)")
    foot_html = f'<span class="hbar-foot">{ui.e(foot)}</span>' if foot else ""
    return (
        '<div class="hbar">'
        '<div class="hbar-head"><span class="hbar-label">'
        + ui.e(label)
        + f'</span><span class="hbar-value">{int(value)}<i>/{int(total)}</i></span></div>'
        + f'<div class="hbar-track"><span style="width:{percent}%;background:{color}"></span></div>'
        + foot_html
        + "</div>"
    )


def progress_ring_card(stats: dict) -> str:
    """完成进度环 + 关键计数。"""
    overdue_html = (
        f'<span class="viz-alert">{ui.icon("alert-circle", 12)}有 {int(stats["overdue"])} 项已过期</span>'
        if stats["overdue"]
        else '<span class="viz-ok">' + ui.icon("circle-check", 12) + "没有逾期任务</span>"
    )
    return (
        '<section class="panel viz-card">'
        '<div class="panel-head"><div>'
        f'<div class="panel-title"><span class="panel-icon">{ui.icon("target", 17)}</span>完成进度</div>'
        f'<div class="panel-sub">共 {int(stats["total"])} 项任务 · 更新于 {ui.e(stats["updated_at"])}</div>'
        "</div></div>"
        '<div class="viz-ring-row">'
        + ui.ring(int(stats["rate"]), "完成率", 128)
        + '<div class="viz-counts">'
        f'<div class="viz-count"><b>{int(stats["done"])}</b><span>已完成</span></div>'
        f'<div class="viz-count"><b>{int(stats["open"])}</b><span>进行中</span></div>'
        f'<div class="viz-count"><b>{int(stats["today_done"])}</b><span>今日完成</span></div>'
        f'<div class="viz-count"><b>{int(stats["today_total"])}</b><span>今日待办</span></div>'
        "</div></div>"
        f'<div class="viz-foot">{overdue_html}</div>'
        "</section>"
    )


def priority_bars_card(stats: dict) -> str:
    rows = []
    buckets = stats["by_priority"]
    order = ["high", "medium", "low"]
    for key in order:
        bucket = buckets.get(key) or {}
        total = int(bucket.get("total") or 0)
        if not total:
            continue
        done = int(bucket.get("done") or 0)
        rows.append(
            _hbar(
                str(bucket.get("label") or key),
                done,
                total,
                str(bucket.get("tone") or "blue"),
                foot=f"已完成 {done} · 进行中 {total - done}",
            )
        )
    body = "".join(rows) or '<div class="viz-empty">暂无任务，新增一条试试。</div>'
    return (
        '<section class="panel viz-card">'
        '<div class="panel-head"><div>'
        f'<div class="panel-title"><span class="panel-icon">{ui.icon("flag", 17)}</span>任务优先级分布</div>'
        '<div class="panel-sub">按优先级统计完成情况</div>'
        "</div></div>"
        f'<div class="hbar-list">{body}</div>'
        "</section>"
    )


def category_bars_card(stats: dict) -> str:
    rows = []
    buckets = stats["by_category"]
    tones = ["blue", "teal", "violet", "gold", "rose"]
    for index, (name, bucket) in enumerate(buckets.items()):
        total = int(bucket.get("total") or 0)
        if not total:
            continue
        done = int(bucket.get("done") or 0)
        rows.append(
            _hbar(
                str(name),
                done,
                total,
                tones[index % len(tones)],
                foot=f"共 {total} 项 · 已完成 {done}",
            )
        )
    body = "".join(rows) or '<div class="viz-empty">暂无任务，新增一条试试。</div>'
    return (
        '<section class="panel viz-card">'
        '<div class="panel-head"><div>'
        f'<div class="panel-title"><span class="panel-icon">{ui.icon("layers", 17)}</span>任务分类分布</div>'
        '<div class="panel-sub">学习、生活、工作、活动、其他</div>'
        "</div></div>"
        f'<div class="hbar-list">{body}</div>'
        "</section>"
    )


def week_trend_card(stats: dict) -> str:
    week = stats.get("week") or []
    peak = max((int(day["count"]) for day in week), default=0) or 1
    total_week = sum(int(day["count"]) for day in week)
    bars = []
    for day in week:
        count = int(day["count"])
        height = max(5, int(round(52 * count / peak)))
        today_class = " today" if day.get("is_today") else ""
        tip = f"{day['label']}（{day['date']}）完成 {count} 项"
        bars.append(
            f'<div class="week-bar{today_class}" title="{ui.e(tip)}">'
            f'<i style="height:{height}px"></i><b>{count}</b><span>{ui.e(day["label"])}</span></div>'
        )
    return (
        '<section class="panel viz-card">'
        '<div class="panel-head"><div>'
        f'<div class="panel-title"><span class="panel-icon">{ui.icon("chart", 17)}</span>近 7 天完成趋势</div>'
        f'<div class="panel-sub">本周累计完成 <b>{total_week}</b> 项 · 按真实完成时间统计</div>'
        "</div>"
        f'<span class="pill blue">按天统计</span>'
        "</div>"
        f'<div class="viz-week">{"".join(bars)}</div>'
        "</section>"
    )


def upcoming_card(stats: dict) -> str:
    items = stats.get("upcoming") or []
    rows = []
    for task in items:
        pri_tag = f'<span class="tag {ui.e(task["priority_tone"])}">{ui.e(task["priority_short"])}</span>'
        overdue_class = " overdue" if task["is_overdue"] else ""
        rows.append(
            f'<div class="due-row{overdue_class}">'
            f'<span class="due-title">{ui.e(task["title"])}</span>'
            f'<span class="due-meta">{pri_tag}'
            f'<span class="due-date">{ui.icon("clock", 11)}{ui.e(task["due_label"])}</span>'
            f'<span class="due-cat">{ui.e(task["category"])}</span></span>'
            "</div>"
        )
    body = (
        "".join(rows)
        or '<div class="viz-empty">' + ui.icon("circle-check", 16) + " 没有进行中的任务，安排一件新事情吧。</div>"
    )
    return (
        '<section class="panel viz-card">'
        '<div class="panel-head"><div>'
        f'<div class="panel-title"><span class="panel-icon">{ui.icon("alarm-clock", 17)}</span>即将截止</div>'
        '<div class="panel-sub">按截止时间排序 · 过期任务标红提醒</div>'
        "</div>"
        f'<a class="panel-link" href="{ui.e(ui.page_url("center", view="tasks"))}">去处理 {ui.icon("chevron-right", 12)}</a>'
        "</div>"
        f'<div class="due-list">{body}</div>'
        "</section>"
    )


def stat_cards(stats: dict) -> str:
    """任务完成统计的四宫格（成长档案使用）。"""
    cards = (
        ui.stat_card("任务总数", str(stats["total"]), "项", "layout-grid", "blue"),
        ui.stat_card("已完成", str(stats["done"]), "项", "circle-check", "teal"),
        ui.stat_card("完成率", str(stats["rate"]), "%", "trending-up", "violet"),
        ui.stat_card(
            "已过期" if stats["overdue"] else "进行中",
            str(stats["overdue"] if stats["overdue"] else stats["open"]),
            "项",
            "alert-circle" if stats["overdue"] else "clock",
            "rose" if stats["overdue"] else "gold",
        ),
    )
    return f'<div class="stat-grid">{cards}</div>'
