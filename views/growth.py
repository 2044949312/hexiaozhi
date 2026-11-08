# -*- coding: utf-8 -*-
"""河小智 · 个人成长档案。

页面用「被看见的成长」叙事串起：成长值 → 四宫格统计 → 个人基本信息
→ 任务完成统计 → 已完成任务 → 关注活动 → 能力进度 → 徽章墙
→ 成长时间线 → 学期目标。

数据来源说明（坚持「数据真实，不可编造」）：
- 任务相关的所有数字（已完成任务、完成率、优先级/分类分布、7 天趋势）
  由 core.tasks.task_stats() 按真实任务记录实时计算；
- 关注活动来自用户在「校园活动」页面的真实报名记录；
- 个人基本信息中的账号、注册时间来自本地账号库；
- 成长值、徽章、时间线等沿用 core.data.GROWTH 演示数据并明确标注。
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from core import auth, data, tasks, ui, viz


def _render_html(markup: str, **kwargs) -> None:
    """优先走 core.ui.render_html（站内链接在当前标签页打开），旧版本回退 st.markdown。"""
    render = getattr(ui, "render_html", None)
    if callable(render):
        render(markup)
    else:
        st.markdown(markup, **kwargs)


_WEEK_LABELS = ["一", "二", "三", "四", "五", "六", "日"]

_STYLE = """
<style>
.growth-top{display:grid;grid-template-columns:minmax(0,.44fr) minmax(0,.56fr);gap:17px;align-items:stretch;}
.growth-score{
  display:flex;flex-direction:column;background:#fff;border:1px solid var(--border);
  border-radius:23px;padding:21px 22px;box-shadow:var(--shadow-sm);
}
.growth-score-main{display:flex;align-items:center;gap:19px;flex-wrap:wrap;}
.growth-level{flex:1;min-width:150px;}
.growth-level b{display:block;font-size:14.5px;font-weight:820;color:var(--ink);letter-spacing:-.01em;}
.growth-level p{margin:6px 0 11px;font-size:10.5px;line-height:1.75;color:var(--muted);}
.level-labels{display:flex;justify-content:space-between;font-size:8.5px;color:var(--muted-light);margin-top:5px;}
.week-caption{
  display:flex;align-items:center;justify-content:space-between;gap:10px;
  margin-top:auto;padding-top:15px;border-top:1px dashed #E7EDF6;font-size:9.5px;color:var(--muted);
}
.week-caption b{color:var(--primary);font-size:11px;}
.week-bars{display:flex;align-items:flex-end;gap:6px;height:60px;margin:10px 0 2px;}
.week-bar{flex:1;height:100%;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:4px;}
.week-bar i{
  display:block;width:100%;max-width:30px;border-radius:5px 5px 3px 3px;
  background:linear-gradient(180deg,#93C5FD,#2563EB);
}
.week-bar.today i{background:linear-gradient(180deg,#5EEAD4,#0D9488);}
.week-bar span{font-size:7.5px;color:var(--muted-light);}
.growth-side{display:flex;flex-direction:column;gap:14px;}
.growth-side .stat-grid{grid-template-columns:repeat(2,minmax(0,1fr));}
.growth-quote{
  display:flex;gap:11px;align-items:flex-start;flex:1;padding:17px 19px;border-radius:19px;
  background:linear-gradient(115deg,#EEF5FF,#F0FCFA 62%,#FFF9ED);
  border:1px solid #DAE9FC;box-shadow:var(--shadow-xs);
}
.growth-quote .quote-icon{color:var(--primary);flex:0 0 auto;margin-top:1px;}
.growth-quote p{margin:0;font-size:11.5px;line-height:1.85;color:var(--ink-soft);}
.growth-quote b{color:var(--primary);}
.skill-list{padding-top:2px;}
.badge-panel-note{margin-top:12px;}
.goal-row{padding:11px 0;border-bottom:1px dashed #EDF1F8;}
.goal-row:last-child{border-bottom:0;padding-bottom:2px;}
.goal-head{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin-bottom:6px;}
.goal-head b{font-size:11.5px;font-weight:700;color:var(--ink);line-height:1.5;}
.goal-head span{font-size:8.5px;color:var(--muted);white-space:nowrap;}
.goal-foot{display:flex;justify-content:space-between;font-size:8.5px;color:var(--muted-light);margin-top:5px;}
.goal-foot b{color:var(--primary);font-size:9.5px;}
.next-level{padding:14px 15px;border-radius:14px;background:#F8FAFF;border:1px solid #E7EEFB;}
.next-level-top{display:flex;gap:11px;align-items:flex-start;}
.next-level-icon{
  width:38px;height:38px;border-radius:11px;flex:0 0 auto;display:grid;place-items:center;
  background:var(--violet-soft);color:var(--violet);
}
.next-level b{display:block;font-size:12px;font-weight:800;color:var(--ink);}
.next-level p{margin:4px 0 0;font-size:9.5px;line-height:1.65;color:var(--muted);}
.next-level-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:13px;}
.next-level-actions .btn{font-size:10px;}
.timeline-intro{font-size:10px;color:var(--muted);line-height:1.7;margin:-2px 0 15px;}
.growth-cta-row{display:flex;gap:9px;flex-wrap:wrap;align-items:center;}
/* ---------- 个人基本信息 ---------- */
.profile-info{display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap;}
.profile-info .info-avatar{
  width:58px;height:58px;border-radius:18px;flex:0 0 auto;display:grid;place-items:center;
  background:linear-gradient(140deg,#1D4ED8,#2563EB 55%,#14B8A6);color:#fff;
  font-size:22px;font-weight:800;box-shadow:0 8px 18px rgba(29,78,216,.22);
}
.profile-info .info-main{flex:1;min-width:220px;}
.profile-info .info-name{font-size:15.5px;font-weight:820;color:var(--ink);letter-spacing:-.01em;}
.profile-info .info-account{font-size:10px;color:var(--muted);margin-top:3px;}
.info-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 14px;margin-top:13px;}
.info-item{background:#F8FAFF;border:1px solid #E7EEFB;border-radius:12px;padding:9px 12px;}
.info-item span{display:block;font-size:8.5px;color:var(--muted-light);letter-spacing:.06em;}
.info-item b{display:block;font-size:11.5px;color:var(--ink);font-weight:750;margin-top:3px;line-height:1.5;}
/* ---------- 已完成任务 ---------- */
.done-row{display:flex;align-items:center;gap:11px;padding:10px 0;border-bottom:1px dashed #EDF1F8;}
.done-row:last-child{border-bottom:0;padding-bottom:2px;}
.done-check{
  width:26px;height:26px;border-radius:9px;flex:0 0 auto;display:grid;place-items:center;
  background:var(--teal-soft);color:var(--teal);
}
.done-body{flex:1;min-width:0;}
.done-title{font-size:12px;font-weight:700;color:var(--ink);line-height:1.5;}
.done-meta{font-size:9px;color:var(--muted);margin-top:3px;display:flex;gap:9px;flex-wrap:wrap;}
.done-meta span{display:inline-flex;align-items:center;gap:3px;}
/* ---------- 关注活动 ---------- */
.focus-row{display:flex;gap:11px;align-items:flex-start;padding:11px 0;border-bottom:1px dashed #EDF1F8;}
.focus-row:last-child{border-bottom:0;padding-bottom:2px;}
.focus-icon{
  width:36px;height:36px;border-radius:11px;flex:0 0 auto;display:grid;place-items:center;
  background:var(--gold-soft);color:#C88B15;
}
.focus-body{flex:1;min-width:0;}
.focus-title{font-size:12px;font-weight:750;color:var(--ink);line-height:1.5;}
.focus-meta{font-size:9px;color:var(--muted);margin-top:4px;display:flex;gap:10px;flex-wrap:wrap;}
.focus-meta span{display:inline-flex;align-items:center;gap:3px;}
@media (max-width:960px){
  .growth-top{grid-template-columns:1fr;}
  .growth-side .stat-grid{grid-template-columns:repeat(4,minmax(0,1fr));}
  .info-grid{grid-template-columns:repeat(2,minmax(0,1fr));}
}
@media (max-width:760px){
  .growth-side .stat-grid{grid-template-columns:repeat(2,minmax(0,1fr));}
  .week-bars{height:52px;}
}
</style>
"""


def _skill_rows() -> str:
    rows = []
    for skill in data.GROWTH["skills"]:
        rows.append(
            '<div class="skill-row">'
            f'<div class="skill-top"><b>{ui.e(skill["name"])}</b><span>{int(skill["value"])}%</span></div>'
            + ui.progress_bar(skill["value"], skill["tone"])
            + "</div>"
        )
    return "".join(rows)


def _badge_items() -> str:
    items = []
    for badge in data.GROWTH["badges"]:
        earned = bool(badge.get("earned"))
        locked_class = "" if earned else " locked"
        desc = badge["desc"] if earned else f"待解锁 · {badge['desc']}"
        items.append(
            f'<div class="badge-item{locked_class}">'
            f'<div class="badge-medal">{ui.icon(badge["icon"], 20)}</div>'
            f'<div class="badge-name">{ui.e(badge["name"])}</div>'
            f'<div class="badge-desc">{ui.e(desc)}</div>'
            "</div>"
        )
    return "".join(items)


def _timeline_items() -> str:
    items = []
    for moment in data.GROWTH["timeline"]:
        items.append(
            '<div class="timeline-item">'
            f'<div class="timeline-date">{ui.e(moment["date"])}</div>'
            f'<div class="timeline-title">{ui.e(moment["title"])}</div>'
            f'<div class="timeline-desc">{ui.e(moment["desc"])}</div>'
            f'<div class="timeline-tag">{ui.tag(moment["tag"], moment["tone"])}</div>'
            "</div>"
        )
    return f'<div class="timeline">{"".join(items)}</div>'


def _goal_rows() -> str:
    rows = []
    for goal in data.GROWTH["goals"]:
        percent = max(0, min(100, int(goal["progress"])))
        rows.append(
            '<div class="goal-row">'
            f'<div class="goal-head"><b>{ui.e(goal["name"])}</b><span>{ui.e(goal["deadline"])}</span></div>'
            + ui.progress_bar(percent, goal["tone"])
            + f'<div class="goal-foot"><span>完成度 <b>{percent}%</b></span><span>目标进行中</span></div>'
            "</div>"
        )
    return "".join(rows)


def _week_bars() -> str:
    weekly = list(data.GROWTH.get("weekly") or [])
    if not weekly:
        return ""
    peak = max(weekly) or 1
    today = datetime.now().weekday()
    bars = []
    for index, value in enumerate(weekly):
        height = max(6, int(round(46 * value / peak)))
        today_class = " today" if index == today else ""
        label = _WEEK_LABELS[index] if index < len(_WEEK_LABELS) else ""
        bars.append(
            f'<div class="week-bar{today_class}" title="周{label} · 活跃度 {value}">'
            f'<i style="height:{height}px"></i><span>{ui.e(label)}</span></div>'
        )
    return "".join(bars)


def _score_card() -> str:
    growth = data.GROWTH
    score = max(0, min(100, int(growth["score"])))
    next_gap = max(0, 100 - score)
    return (
        '<section class="growth-score">'
        '<div class="panel-head"><div>'
        f'<div class="panel-title"><span class="panel-icon">{ui.icon("trending-up", 17)}</span>我的成长值</div>'
        f'<div class="panel-sub">{ui.e(growth["level"])} · 距 {ui.e(growth["next_level"])} 还差 {next_gap} 分</div>'
        "</div>"
        '<span class="pill violet">2026 秋季学期</span>'
        "</div>"
        '<div class="growth-score-main">'
        + ui.ring(score, "成长值", 132)
        + '<div class="growth-level">'
        + f"<b>{ui.e(growth['level'])}</b>"
        + "<p>再完成 2 场校园活动 + 1 次志愿服务，就能解锁「校园领航员」称号。</p>"
        + ui.progress_bar(score, "violet")
        + f'<div class="level-labels"><span>Lv.6 当前</span><span>Lv.7 还差 {next_gap}%</span></div>'
        + "</div></div>"
        + '<div class="week-caption"><span>本周成长活跃度</span>'
        + f'<span>本周累计 <b>+12</b> 点成长值</span></div>'
        + f'<div class="week-bars">{_week_bars()}</div>'
        + "</section>"
    )


def _growth_side() -> str:
    cards = "".join(
        ui.stat_card(
            stat["label"],
            stat["value"],
            stat["unit"],
            stat["icon"],
            stat["tone"],
        )
        for stat in data.GROWTH["stats"]
    )
    return (
        '<div class="growth-side">'
        f'<div class="stat-grid">{cards}</div>'
        '<div class="growth-quote">'
        f'<span class="quote-icon">{ui.icon("sparkles", 18)}</span>'
        '<p>你在图书馆的 <b>120 小时</b>、<b>26 小时</b>志愿服务、<b>12 场</b>校园活动，'
        '都不是白费的时间——它们正在变成你的成长档案里最具体的注脚。</p>'
        "</div></div>"
    )


# --------------------------------------------------------------------------- #
# 新增面板：个人基本信息 / 任务完成统计 / 已完成任务 / 关注活动
# --------------------------------------------------------------------------- #
def _basic_info_panel() -> str:
    account = auth.current_user() or {}
    user = data.USER
    display_name = account.get("username") or user["name"]
    display_initial = account.get("initial") or user["initial"]
    account_no = account.get("account_no") or user["student_id"]
    created_at = str(account.get("created_at") or "")
    if created_at:
        try:
            created_label = datetime.fromisoformat(created_at).strftime("%Y 年 %m 月 %d 日")
        except ValueError:
            created_label = created_at.replace("T", " ")[:19]
    else:
        created_label = "演示模式（未登录）"

    items = [
        ("账号", account_no),
        ("注册时间", created_label),
        ("学院", user["college"]),
        ("专业 / 年级", f'{user["major"]} · {user["grade"]}'),
        ("校区", user["campus"]),
        ("宿舍", user["dorm"]),
        ("学期", user["semester"]),
        ("当前周次", user["week"]),
    ]
    info_grid = "".join(
        f'<div class="info-item"><span>{ui.e(label)}</span><b>{ui.e(value)}</b></div>'
        for label, value in items
    )
    return (
        '<section class="panel">'
        '<div class="panel-head"><div>'
        f'<div class="panel-title"><span class="panel-icon">{ui.icon("id-card", 17)}</span>个人基本信息</div>'
        '<div class="panel-sub">账号信息来自本地账号库，学籍信息为演示档案数据</div>'
        "</div>"
        f'<a class="panel-link" href="?page=center">去事务中心 {ui.icon("chevron-right", 12)}</a>'
        "</div>"
        '<div class="profile-info">'
        f'<div class="info-avatar">{ui.e(display_initial)}</div>'
        '<div class="info-main">'
        f'<div class="info-name">{ui.e(display_name)}</div>'
        f'<div class="info-account">{ui.icon("shield", 11)} 河小智注册用户 · 密码加密存储 · 会话 30 天有效</div>'
        "</div></div>"
        f'<div class="info-grid">{info_grid}</div>'
        "</section>"
    )


def _task_stats_panel() -> str:
    stats = tasks.task_stats()
    return (
        '<section class="panel">'
        '<div class="panel-head"><div>'
        f'<div class="panel-title"><span class="panel-icon">{ui.icon("chart", 17)}</span>任务完成统计</div>'
        f'<div class="panel-sub">更新于 {ui.e(stats["updated_at"])} · 全部由真实任务记录实时计算</div>'
        "</div>"
        f'<a class="panel-link" href="?page=center">管理任务 {ui.icon("chevron-right", 12)}</a>'
        "</div>"
        + viz.stat_cards(stats)
        + '<div style="margin-top:14px">'
        + viz.week_trend_card(stats)
        + "</div>"
        "</section>"
    )


def _completed_tasks_panel() -> str:
    done_items = tasks.get_tasks("done")
    head_count = f'已完成 {len(done_items)} 项任务'
    if not done_items:
        return (
            '<section class="panel">'
            '<div class="panel-head"><div>'
            f'<div class="panel-title"><span class="panel-icon">{ui.icon("circle-check", 17)}</span>已完成任务</div>'
            '<div class="panel-sub">完成个人事务中心的任务后会自动出现在这里</div>'
            "</div></div>"
            '<div class="empty-state" style="padding:26px 0 22px">'
            f'<div class="empty-icon">{ui.icon("trophy", 26)}</div>'
            "<h3>还没有已完成的任务</h3>"
            "<p>去个人事务中心勾选完成一项待办，完成记录（含完成时间）会自动写入成长档案。</p>"
            '<a class="btn btn-primary" href="?page=center">去处理今日待办</a>'
            "</div></section>"
        )
    rows = []
    for item in done_items[:10]:
        completed = str(item.get("completed_at") or "").replace("T", " ")
        completed_label = completed[:16] if completed else "已完成"
        rows.append(
            '<div class="done-row">'
            f'<span class="done-check">{ui.icon("check", 14)}</span>'
            '<div class="done-body">'
            f'<div class="done-title">{ui.e(item["title"])}</div>'
            '<div class="done-meta">'
            f'<span>{ui.icon("clock", 10)}完成于 {ui.e(completed_label)}</span>'
            f'<span>{ui.icon("flag", 10)}{ui.e(item["priority_label"])}</span>'
            f'<span>{ui.icon("layers", 10)}{ui.e(item["category"])}</span>'
            "</div></div>"
            f'<span class="tag {ui.e(item["priority_tone"])}">{ui.e(item["priority_short"])}</span>'
            "</div>"
        )
    return (
        '<section class="panel">'
        '<div class="panel-head"><div>'
        f'<div class="panel-title"><span class="panel-icon">{ui.icon("circle-check", 17)}</span>已完成任务</div>'
        f'<div class="panel-sub">{head_count} · 展示最近 10 项 · 含真实完成时间</div>'
        "</div>"
        f'<a class="panel-link" href="?page=center">继续完成任务 {ui.icon("chevron-right", 12)}</a>'
        "</div>"
        f'<div class="done-list">{"".join(rows)}</div>'
        "</section>"
    )


def _focus_activities_panel() -> str:
    from core.state import registrations

    reg_ids = registrations()
    registered = [act for act in data.ACTIVITIES if act["id"] in reg_ids]
    if not registered:
        return (
            '<section class="panel">'
            '<div class="panel-head"><div>'
            f'<div class="panel-title"><span class="panel-icon">{ui.icon("bookmark", 17)}</span>关注活动</div>'
            '<div class="panel-sub">在校园活动页报名后，活动会出现在这里</div>'
            "</div></div>"
            '<div class="empty-state" style="padding:26px 0 22px">'
            f'<div class="empty-icon">{ui.icon("compass", 26)}</div>'
            "<h3>还没有报名任何活动</h3>"
            "<p>本周有多场校园活动正在报名，报名后会自动同步到你的成长档案。</p>"
            '<a class="btn btn-primary" href="?page=activities">去发现活动</a>'
            "</div></section>"
        )
    rows = []
    for act in registered:
        rows.append(
            '<div class="focus-row">'
            f'<span class="focus-icon">{ui.icon("compass", 17)}</span>'
            '<div class="focus-body">'
            f'<div class="focus-title">{ui.e(act["title"])}</div>'
            '<div class="focus-meta">'
            f'<span>{ui.icon("calendar", 10)}{ui.e(act["date"])} {ui.e(act["time"])}</span>'
            f'<span>{ui.icon("map-pin", 10)}{ui.e(act["location"])}</span>'
            f'<span>{ui.icon("alarm-clock", 10)}报名截止 {ui.e(act["deadline"])}</span>'
            "</div></div>"
            f'<span class="tag gold">{ui.e(act["category"])}</span>'
            "</div>"
        )
    return (
        '<section class="panel">'
        '<div class="panel-head"><div>'
        f'<div class="panel-title"><span class="panel-icon">{ui.icon("bookmark", 17)}</span>关注活动</div>'
        f'<div class="panel-sub">已报名 {len(registered)} 场 · 来自你在校园活动页的真实报名记录</div>'
        "</div>"
        f'<a class="panel-link" href="?page=activities">发现更多 {ui.icon("chevron-right", 12)}</a>'
        "</div>"
        f'<div class="focus-list">{"".join(rows)}</div>'
        "</section>"
    )


def _skills_panel() -> str:
    return (
        '<section class="panel">'
        '<div class="panel-head"><div>'
        f'<div class="panel-title"><span class="panel-icon">{ui.icon("chart", 17)}</span>能力进度</div>'
        f'<div class="panel-sub">5 个能力维度 · 来自课程、活动与项目数据</div>'
        "</div>"
        '<span class="pill blue">持续成长中</span>'
        "</div>"
        f'<div class="skill-list">{_skill_rows()}</div>'
        f'<div class="data-note" style="margin-top:14px">{ui.icon("info", 13)}能力值由课程成绩、项目协作与活动参与综合测算（演示数据），仅用于展示成长趋势。</div>'
        "</section>"
    )


def _badges_panel() -> str:
    earned = sum(1 for badge in data.GROWTH["badges"] if badge.get("earned"))
    total = len(data.GROWTH["badges"])
    return (
        '<section class="panel">'
        '<div class="panel-head"><div>'
        f'<div class="panel-title"><span class="panel-icon">{ui.icon("award", 17)}</span>徽章墙</div>'
        f'<div class="panel-sub">已解锁 {earned} / {total} 枚 · 解锁后会出现在你的档案主页</div>'
        "</div>"
        f'<span class="pill gold">{earned} 枚已点亮</span>'
        "</div>"
        f'<div class="badge-grid">{_badge_items()}</div>'
        f'<div class="data-note badge-panel-note">{ui.icon("sparkles", 13)}灰色徽章是下一阶段的小目标，完成对应条件后即可点亮。</div>'
        "</section>"
    )


def _timeline_panel() -> str:
    return (
        '<section class="panel">'
        '<div class="panel-head"><div>'
        f'<div class="panel-title"><span class="panel-icon">{ui.icon("clock", 17)}</span>成长时间线</div>'
        '<div class="panel-sub">从新生营到挑战杯，4 个被记住的瞬间</div>'
        "</div>"
        f'<a class="panel-link" href="?page=activities">继续去经历 {ui.icon("chevron-right", 12)}</a>'
        "</div>"
        '<div class="timeline-intro">每一次参与，都在悄悄定义你。下面是河小智为你记下的高光时刻。</div>'
        + _timeline_items()
        + "</section>"
    )


def _goals_panel() -> str:
    goals = data.GROWTH["goals"]
    average = int(round(sum(int(goal["progress"]) for goal in goals) / len(goals))) if goals else 0
    return (
        '<section class="panel">'
        '<div class="panel-head"><div>'
        f'<div class="panel-title"><span class="panel-icon">{ui.icon("target", 17)}</span>学期目标</div>'
        f'<div class="panel-sub">平均完成度 {average}% · 距离本学期结束还有 46 天</div>'
        "</div>"
        '<span class="pill teal">稳步推进</span>'
        "</div>"
        f'<div class="goal-list">{_goal_rows()}</div>'
        "</section>"
    )


def _next_level_panel() -> str:
    growth = data.GROWTH
    return (
        '<section class="panel">'
        '<div class="next-level">'
        '<div class="next-level-top">'
        f'<span class="next-level-icon">{ui.icon("graduation-cap", 19)}</span>'
        "<div>"
        f"<b>下一站 · {ui.e(growth['next_level'])}</b>"
        "<p>再积累 14 点成长值并完成 1 次志愿活动，即可解锁新称号与专属徽章。</p>"
        "</div></div>"
        + '<div style="margin-top:13px">'
        + ui.progress_bar(int(growth["score"]), "blue")
        + "</div>"
        '<div class="next-level-actions">'
        '<a class="btn btn-sm btn-primary" href="?page=activities">报名一场活动</a>'
        '<a class="btn btn-sm btn-ghost" href="?page=center">处理今日待办</a>'
        "</div></div>"
        "</section>"
    )


def render() -> None:
    _render_html(_STYLE, unsafe_allow_html=True)

    growth = data.GROWTH
    score = max(0, min(100, int(growth["score"])))
    earned = sum(1 for badge in growth["badges"] if badge.get("earned"))
    stats = tasks.task_stats()
    hero_meta = (
        f'<span>{ui.icon("trending-up", 13)}成长值 {score} / 100</span>'
        f'<span>{ui.icon("star", 13)}{ui.e(growth["level"])}</span>'
        f'<span>{ui.icon("award", 13)}已点亮 {earned} 枚徽章</span>'
        f'<span>{ui.icon("circle-check", 13)}已完成 {int(stats["done"])} 项任务</span>'
    )

    _render_html(
        ui.page_hero(
            eyebrow="MY GROWTH · 个人成长档案",
            title="你在河大的每一步，都值得被看见",
            subtitle="课程、活动、志愿与荣誉自动沉淀成一条属于你的成长曲线。不是为了比较，而是为了看见自己走了多远。",
            icon_name="trending-up",
            tone="teal",
            meta=hero_meta,
        )
        + f'<div class="growth-top">{_score_card()}{_growth_side()}</div>',
        unsafe_allow_html=True,
    )

    # ---- 个人基本信息 + 任务完成统计 ----
    _render_html(
        '<div class="section-space"></div>'
        + ui.section_header(
            title="我的档案",
            eyebrow="MY PROFILE",
            subtitle="账号信息、任务完成情况与成长积累，构成你在河小智的数字身份",
            link_label="回到个人事务中心",
            link_href="?page=center",
            icon_name="id-card",
        )
        + f'<div class="grid-2">{_basic_info_panel()}{_task_stats_panel()}</div>',
        unsafe_allow_html=True,
    )

    # ---- 已完成任务 + 关注活动 ----
    _render_html(
        '<div class="section-space" style="height:14px"></div>'
        + ui.section_header(
            title="任务与活动",
            eyebrow="MY RECORDS",
            subtitle="每一条记录都来自你的真实操作",
            link_label="看看本周活动",
            link_href="?page=activities",
            icon_name="bookmark",
        )
        + f'<div class="grid-2">{_completed_tasks_panel()}{_focus_activities_panel()}</div>',
        unsafe_allow_html=True,
    )

    _render_html(
        '<div class="section-space"></div>'
        + ui.section_header(
            title="能力与徽章",
            eyebrow="CAPABILITY",
            subtitle="能力不是一张成绩单，而是你解决问题、与人协作、持续创造的样子",
            link_label="看看本周活动",
            link_href="?page=activities",
            icon_name="chart",
        )
        + f'<div class="grid-2">{_skills_panel()}{_badges_panel()}</div>',
        unsafe_allow_html=True,
    )

    _render_html(
        '<div class="section-space"></div>'
        + ui.section_header(
            title="成长时间线",
            eyebrow="MILESTONES",
            subtitle="把「我做过什么」变成「我成为了谁」",
            link_label="回到个人事务中心",
            link_href="?page=center",
            icon_name="clock",
        )
        + f'<div class="split-2">{_timeline_panel()}'
        + f'<div class="stack">{_goals_panel()}{_next_level_panel()}</div></div>',
        unsafe_allow_html=True,
    )

    from core.state import registrations

    reg_count = len(registrations())
    _render_html(
        '<a class="growth-banner" href="?page=activities" style="margin-top:20px">'
        f'<span class="growth-icon">{ui.icon("compass", 21)}</span>'
        '<span class="growth-copy"><b>下一段成长，从一场活动开始</b>'
        f'<span>你已报名 {reg_count} 场活动 · 参与记录会自动写入成长档案</span></span>'
        '<span class="growth-stats">'
        f'<span class="growth-stat"><strong>{len(data.ACTIVITIES)}</strong>场在架活动</span>'
        f'<span class="growth-stat"><strong>{reg_count}</strong>已报名</span>'
        f'<span class="growth-stat"><strong>{int(stats["done"])}</strong>项任务完成</span>'
        '</span><span class="growth-cta">去发现活动 ' + ui.icon("arrow-right", 13) + "</span></a>",
        unsafe_allow_html=True,
    )
