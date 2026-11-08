# -*- coding: utf-8 -*-
"""河小智 · 个人事务中心。

任务管理说明：
- 数据源是 core.tasks 的持久化任务库（按账号落盘 .data/tasks_*.json），
  支持新增、修改、删除、勾选完成，任务带分类、优先级与真实截止时间；
- 页面上的进度环、优先级分布、分类分布、近 7 天完成趋势等数字
  全部由 core.tasks.task_stats() 按真实记录实时计算；
- 待办用 st.checkbox 渲染（原生控件通过页面级 CSS 融入白色面板），
  勾选即写库并 rerun；「上一轮快照」机制防止外部状态变化导致死循环。
"""

from __future__ import annotations

from datetime import datetime, timedelta

import streamlit as st

from core import auth, data, tasks, ui, viz
from core.tasks import PRIORITIES


def _render_html(markup: str, **kwargs) -> None:
    """优先走 core.ui.render_html（站内链接在当前标签页打开），旧版本回退 st.markdown。"""
    render = getattr(ui, "render_html", None)
    if callable(render):
        render(markup)
    else:
        st.markdown(markup, **kwargs)


_CK_KEY = "center_task_"
_SEEN_KEY = "center_task_seen"
_DEL_CONFIRM_KEY = "center_del_confirm_"

_SERVICE_ICONS = {"classroom": "book-open", "library": "library", "wrench": "wrench"}

# 「我的河大」内部导航：每个功能独立成一页，避免单页过长。
_VIEWS = ("overview", "tasks", "stats")

_STYLE = """
<style>
/* ---------- 任务面板 ---------- */
.st-key-center-task-panel{
  background:#fff;border:1px solid var(--border);border-radius:23px;
  padding:20px 22px 13px;box-shadow:var(--shadow-sm);
}
.st-key-center-task-panel [data-testid="stVerticalBlock"]{gap:.35rem;}
.st-key-center-task-panel [data-testid="stHorizontalBlock"]{
  align-items:center;gap:10px;padding:4px 0;border-bottom:1px dashed #EDF1F8;
}
.st-key-center-task-panel [data-testid="stHorizontalBlock"]:last-of-type{border-bottom:0;}
.st-key-center-task-panel [data-testid="stCheckbox"]{margin:0;}
.st-key-center-task-panel [data-testid="stCheckbox"] label{gap:10px;align-items:flex-start;padding:5px 0;}
.st-key-center-task-panel [data-testid="stCheckbox"] label p{
  font-size:12.5px!important;font-weight:650!important;line-height:1.5!important;color:var(--ink)!important;
}
.st-key-center-task-panel [data-testid="stCheckbox"] [data-baseweb="checkbox"] div{border-radius:7px;}
.st-key-center-task-panel [data-testid="stCheckbox"]:has(input:checked) label p{
  color:#9AA8BD!important;text-decoration:line-through;
}
.st-key-center-task-panel [data-testid="stTabs"] [data-baseweb="tab-list"]{gap:4px;border-bottom:1px solid var(--border);}
.st-key-center-task-panel [data-baseweb="tab"]{
  padding:6px 12px;border-radius:10px 10px 0 0;font-size:11px;font-weight:700;color:var(--muted);
}
.st-key-center-task-panel [data-baseweb="tab"][aria-selected="true"]{
  color:var(--primary);background:var(--primary-soft);border-bottom:2px solid var(--primary);
}
.st-key-center-task-panel [data-baseweb="tab-highlight"]{display:none;}
.st-key-center-task-panel button[data-testid="stBaseButton-secondary"],
.st-key-center-task-panel button[data-testid="stBaseButton-secondaryFormSubmit"]{
  font-size:10px;padding:3px 8px;min-height:0;border-radius:8px;color:var(--muted);
  border:1px solid var(--border);background:#F8FAFF;white-space:nowrap;
}
.st-key-center-task-panel button[data-testid="stBaseButton-secondary"]:hover{
  color:var(--primary);border-color:#C9DAF9;background:var(--primary-soft);
}
.st-key-center-task-panel button.task-del-armed{
  color:#fff!important;background:var(--rose)!important;border-color:var(--rose)!important;
}
.center-task-meta{display:flex;flex-direction:column;align-items:flex-end;gap:4px;text-align:right;}
.center-task-meta .meta-line{display:inline-flex;align-items:center;gap:3px;font-size:9px;color:var(--muted);line-height:1.4;}
.center-task-meta .meta-line svg{color:#A7B4C7;flex:0 0 auto;}
.center-task-meta .meta-line.due-hot{color:var(--rose);font-weight:700;}
.center-task-meta .meta-line.due-hot svg{color:var(--rose);}
.center-task-meta .meta-line.done-at{color:var(--teal);}
.center-task-meta .meta-line.done-at svg{color:var(--teal);}
.center-empty{
  padding:26px 0 20px;text-align:center;color:var(--muted);font-size:11px;line-height:1.8;
}
.center-empty svg{color:#B9C6DB;display:block;margin:0 auto 8px;}
/* ---------- 新增任务表单 ---------- */
.st-key-center-add-form{
  background:#F8FAFF;border:1px solid var(--border);border-radius:16px;padding:14px 16px 6px;margin-bottom:12px;
}
.st-key-center-add-form label{font-size:10px!important;color:var(--muted)!important;font-weight:700!important;}
.st-key-center-add-form [data-testid="stTextInput"] input,
.st-key-center-add-form [data-baseweb="select"] > div,
.st-key-center-add-form [data-testid="stDateInput"] input,
.st-key-center-add-form [data-testid="stTimeInput"] input{font-size:11.5px;}
/* ---------- 数据可视化 ---------- */
.viz-card{padding-bottom:16px;}
.viz-ring-row{display:flex;align-items:center;gap:22px;flex-wrap:wrap;margin-top:6px;}
.viz-counts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;flex:1;min-width:200px;}
.viz-count{background:#F8FAFF;border:1px solid #E7EEFB;border-radius:13px;padding:10px 13px;}
.viz-count b{display:block;font-size:17px;font-weight:800;color:var(--ink);line-height:1.15;}
.viz-count span{font-size:9.5px;color:var(--muted);margin-top:3px;display:block;}
.viz-foot{margin-top:14px;padding-top:11px;border-top:1px dashed #EDF1F8;font-size:10px;}
.viz-alert{display:inline-flex;align-items:center;gap:5px;color:var(--rose);font-weight:700;}
.viz-ok{display:inline-flex;align-items:center;gap:5px;color:var(--teal);font-weight:700;}
.viz-empty{padding:16px 0;text-align:center;color:var(--muted);font-size:10.5px;display:flex;align-items:center;justify-content:center;gap:6px;}
.hbar-list{display:flex;flex-direction:column;gap:13px;margin-top:4px;}
.hbar-head{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px;}
.hbar-label{font-size:11px;font-weight:700;color:var(--ink);}
.hbar-value{font-size:12px;font-weight:800;color:var(--ink);}
.hbar-value i{font-style:normal;font-size:9.5px;font-weight:600;color:var(--muted-light);}
.hbar-track{height:8px;border-radius:999px;background:#EEF2F9;overflow:hidden;}
.hbar-track span{display:block;height:100%;border-radius:999px;transition:width .4s ease;}
.hbar-foot{font-size:8.5px;color:var(--muted-light);margin-top:4px;display:block;}
.viz-week{display:flex;align-items:flex-end;gap:8px;height:96px;margin-top:10px;padding:0 4px;}
.viz-week .week-bar{flex:1;height:100%;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:3px;}
.viz-week .week-bar i{display:block;width:100%;max-width:34px;border-radius:6px 6px 3px 3px;background:linear-gradient(180deg,#93C5FD,#2563EB);}
.viz-week .week-bar.today i{background:linear-gradient(180deg,#5EEAD4,#0D9488);}
.viz-week .week-bar b{font-size:9.5px;color:var(--ink-soft);font-weight:800;}
.viz-week .week-bar span{font-size:8px;color:var(--muted-light);}
.due-list{display:flex;flex-direction:column;}
.due-row{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 0;border-bottom:1px dashed #EDF1F8;flex-wrap:wrap;}
.due-row:last-child{border-bottom:0;padding-bottom:2px;}
.due-title{font-size:12px;font-weight:700;color:var(--ink);line-height:1.5;}
.due-row.overdue .due-title{color:var(--rose);}
.due-meta{display:inline-flex;align-items:center;gap:8px;flex:0 0 auto;}
.due-date{display:inline-flex;align-items:center;gap:4px;font-size:9.5px;color:var(--muted);}
.due-row.overdue .due-date{color:var(--rose);font-weight:700;}
.due-cat{font-size:9px;color:var(--muted-light);background:#F5F7FB;border-radius:999px;padding:3px 8px;}
/* ---------- 个人信息卡 ---------- */
.profile-meta{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;}
.profile-meta span{
  display:inline-flex;align-items:center;gap:4px;font-size:9px;color:rgba(255,255,255,.68);
  padding:4px 8px;border-radius:999px;background:rgba(255,255,255,.08);
  border:1px solid rgba(255,255,255,.13);
}
.profile-head{align-items:flex-start;}
.profile-link{
  margin-left:auto;display:inline-flex;align-items:center;gap:5px;flex:0 0 auto;
  padding:9px 12px;border-radius:10px;background:rgba(255,255,255,.12);
  border:1px solid rgba(255,255,255,.2);color:#fff;font-size:10px;font-weight:700;
  text-decoration:none;white-space:nowrap;transition:all .18s ease;
}
.profile-link:hover{background:rgba(255,255,255,.22);}
/* ---------- 我的河大：页头 + 二级导航按键 ---------- */
.center-head{
  display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap;
  margin:0 0 18px;
}
.center-eyebrow{
  display:inline-flex;align-items:center;gap:6px;font-size:10px;font-weight:800;
  letter-spacing:.1em;color:var(--primary);
}
.center-head h1{
  margin:6px 0 5px;font-size:clamp(22px,2.4vw,29px);line-height:1.2;
  font-weight:850;letter-spacing:-.03em;color:var(--ink);
}
.center-head p{margin:0;font-size:10.5px;color:var(--muted);line-height:1.6;}
.center-nav{
  display:flex;align-items:center;gap:5px;padding:5px;border-radius:16px;background:#fff;
  border:1px solid var(--border);box-shadow:var(--shadow-xs);
  max-width:100%;overflow-x:auto;scrollbar-width:none;
}
.center-nav::-webkit-scrollbar{display:none;}
.center-nav-item{
  display:inline-flex;align-items:center;gap:7px;padding:9px 15px;border-radius:11px;
  color:var(--muted)!important;font-size:12px;font-weight:750;line-height:1.2;
  text-decoration:none!important;white-space:nowrap;transition:all .18s ease;
}
.center-nav-item svg{flex:0 0 auto;}
.center-nav-item:hover{background:#F6FAFF;color:var(--primary)!important;}
.center-nav-item.active{
  background:linear-gradient(135deg,#1D4ED8,#2563EB);color:#fff!important;
  box-shadow:0 8px 18px rgba(29,78,216,.22);
}
.center-nav-count{
  display:inline-flex;align-items:center;justify-content:center;min-width:20px;height:20px;
  padding:0 6px;border-radius:999px;background:var(--primary-soft);color:var(--primary);
  font-size:9.5px;font-weight:800;
}
.center-nav-item.active .center-nav-count{background:rgba(255,255,255,.22);color:#fff;}
/* ---------- 概览：待办速览 ---------- */
.ov-todo-list{display:flex;flex-direction:column;}
.ov-todo{
  display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px dashed #EDF1F8;
  text-decoration:none!important;color:inherit!important;transition:all .16s ease;
}
.ov-todo:last-child{border-bottom:0;padding-bottom:2px;}
.ov-todo:hover{background:#F8FAFF;margin:0 -10px;padding-left:10px;padding-right:10px;border-radius:11px;}
.ov-dot{width:8px;height:8px;border-radius:50%;flex:0 0 auto;background:var(--primary);}
.ov-dot.rose{background:var(--rose);}
.ov-dot.teal{background:var(--teal);}
.ov-dot.gold{background:#D99A16;}
.ov-dot.violet{background:var(--violet);}
.ov-todo-main{flex:1;min-width:0;display:flex;flex-direction:column;}
.ov-todo-title{display:block;font-size:12.5px;font-weight:650;color:var(--ink);line-height:1.45;}
.ov-todo-meta{display:flex;flex-wrap:wrap;gap:9px;font-size:9px;color:var(--muted);margin-top:3px;}
.ov-todo-meta span{display:inline-flex;align-items:center;gap:3px;}
.ov-todo-meta .hot{color:var(--rose);font-weight:700;}
.ov-empty{
  padding:22px 0 16px;text-align:center;color:var(--muted);font-size:11px;line-height:1.8;
}
.ov-empty svg{color:#B9C6DB;display:block;margin:0 auto 8px;}
.ov-progress{margin:2px 0 4px;}
@media (max-width:960px){
  [data-testid="stHorizontalBlock"]:has(.st-key-center-task-panel){flex-wrap:wrap;}
  [data-testid="stHorizontalBlock"]:has(.st-key-center-task-panel) > [data-testid="stColumn"]{
    flex:1 1 100%!important;width:100%!important;min-width:100%!important;
  }
  .profile-link{display:none;}
  .viz-ring-row{gap:14px;}
  .center-head{align-items:flex-start;}
}
@media (max-width:760px){
  .center-task-meta{display:none;}
  .profile-meta{display:none;}
  .viz-counts{grid-template-columns:repeat(2,minmax(0,1fr));}
  .center-nav{width:100%;}
  .center-nav-item{flex:1;justify-content:center;padding:9px 8px;font-size:10.5px;gap:4px;}
  .center-nav-item svg{display:none;}
  .center-head h1{font-size:22px;}
  /* 移动端任务行保持单行：标题 + 修改 / 删除，避免纵向堆叠 */
  .st-key-center-task-panel [data-testid="stHorizontalBlock"]:has([data-testid="stCheckbox"]){
    flex-wrap:nowrap!important;gap:6px!important;
  }
  .st-key-center-task-panel [data-testid="stHorizontalBlock"]:has([data-testid="stCheckbox"]) > [data-testid="stColumn"]{
    min-width:0!important;width:auto!important;
  }
  .st-key-center-task-panel [data-testid="stHorizontalBlock"]:has([data-testid="stCheckbox"]) > [data-testid="stColumn"]:nth-child(1){
    flex:1 1 auto!important;
  }
  .st-key-center-task-panel [data-testid="stHorizontalBlock"]:has([data-testid="stCheckbox"]) > [data-testid="stColumn"]:nth-child(2){
    display:none!important;
  }
  .st-key-center-task-panel [data-testid="stHorizontalBlock"]:has([data-testid="stCheckbox"]) > [data-testid="stColumn"]:nth-child(3){
    flex:0 0 124px!important;
  }
  .st-key-center-task-panel [data-testid="stHorizontalBlock"]:has([data-testid="stCheckbox"]) [data-testid="stHorizontalBlock"]{
    flex-wrap:nowrap!important;gap:5px!important;
  }
  .st-key-center-task-panel [data-testid="stHorizontalBlock"]:has([data-testid="stCheckbox"]) [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{
    flex:1 1 0!important;min-width:0!important;width:auto!important;
  }
}
</style>
"""


def _date_label() -> str:
    now = datetime.now()
    weekday = "一二三四五六日"[now.weekday()]
    return f"{now.month} 月 {now.day} 日 · 周{weekday}"


def _subnav(active: str) -> str:
    """「我的河大」二级导航：每个功能独立成页，用按键切换。"""
    open_count = len(tasks.get_tasks("today")) + len(tasks.get_tasks("upcoming"))
    items = [
        ("overview", "概览", "layout-grid", None),
        ("tasks", "我的任务", "circle-check", open_count),
        ("stats", "数据看板", "chart", None),
    ]
    links = "".join(
        f'<a class="center-nav-item {"active" if key == active else ""}" '
        f'href="{ui.e(ui.page_url("center", view=key))}">'
        f"{ui.icon(icon_name, 15)}<span>{ui.e(label)}</span>"
        + (f'<span class="center-nav-count">{count}</span>' if count is not None else "")
        + "</a>"
        for key, label, icon_name, count in items
    )
    return f'<nav class="center-nav" aria-label="我的河大导航">{links}</nav>'


def _page_head(active: str) -> str:
    """紧凑页头：标题、日期与二级导航放在同一行，替代整块大 Hero。"""
    return (
        '<header class="center-head">'
        '<div class="center-head-copy">'
        f'<div class="center-eyebrow">{ui.icon("layout-grid", 13)} MY CAMPUS · 我的河大</div>'
        "<h1>个人事务中心</h1>"
        f'<p>{ui.e(_date_label())}</p>'
        "</div>"
        + _subnav(active)
        + "</header>"
    )


def _overview_todo_panel() -> str:
    """概览页的待办速览：只读摘要，处理任务请进入「我的任务」。"""
    today_items = tasks.get_tasks("today")
    upcoming_items = tasks.get_tasks("upcoming")
    open_items = today_items + upcoming_items
    done_count, total_count = tasks.todo_progress()
    percent = int(done_count / total_count * 100) if total_count else 0

    rows = []
    for item in open_items[:5]:
        tone = "rose" if item["is_overdue"] else item["priority_tone"]
        due_class = " hot" if item["is_overdue"] else ""
        place_html = (
            f'<span>{ui.icon("map-pin", 10)}{ui.e(item["place"])}</span>'
            if item.get("place")
            else ""
        )
        rows.append(
            f'<a class="ov-todo" href="{ui.e(ui.page_url("center", view="tasks"))}">'
            f'<span class="ov-dot {ui.e(tone)}"></span>'
            '<span class="ov-todo-main">'
            f'<span class="ov-todo-title">{ui.e(item["title"])}</span>'
            '<span class="ov-todo-meta">'
            f'<span class="{due_class.strip()}">{ui.icon("alarm-clock", 10)}{ui.e(item["due_label"])}</span>'
            f'<span>{ui.icon("flag", 10)}{ui.e(item["priority_short"])}优先级 · {ui.e(item["category"])}</span>'
            + place_html
            + "</span></span></a>"
        )
    body = (
        "".join(rows)
        or '<div class="ov-empty">' + ui.icon("circle-check", 22)
        + "今天没有待办任务<br>去「我的任务」安排一件新事情吧。</div>"
    )
    return (
        '<section class="panel">'
        '<div class="panel-head"><div>'
        f'<div class="panel-title"><span class="panel-icon">{ui.icon("circle-check", 17)}</span>待办速览</div>'
        f'<div class="panel-sub">今日进度 {done_count}/{total_count} · 未完成 {len(open_items)} 项</div>'
        "</div>"
        f'<a class="panel-link" href="{ui.e(ui.page_url("center", view="tasks"))}">去任务页 {ui.icon("chevron-right", 12)}</a>'
        "</div>"
        f'<div class="ov-progress"><div class="todo-progress-row"><span>今日完成进度</span>'
        f"<span><b>{done_count}</b> / {total_count}</span></div>"
        f'<div class="progress-track"><div class="progress-fill" style="width:{percent}%"></div></div></div>'
        f'<div class="ov-todo-list">{body}</div>'
        "</section>"
    )


def _growth_banner(stats: dict) -> str:
    return (
        '<a class="growth-banner" href="?page=growth">'
        f'<span class="growth-icon">{ui.icon("trending-up", 21)}</span>'
        '<span class="growth-copy"><b>完成任务，都在为你的成长档案添砖加瓦</b>'
        "<span>任务完成情况会实时同步到个人成长档案的任务统计</span></span>"
        '<span class="growth-stats">'
        f'<span class="growth-stat"><strong>{int(stats["total"])}</strong>项任务</span>'
        f'<span class="growth-stat"><strong>{int(stats["done"])}</strong>已完成</span>'
        '</span><span class="growth-cta">查看成长档案 '
        + ui.icon("arrow-right", 13)
        + "</span></a>"
    )


def _profile_card(stats: dict) -> str:
    account = auth.current_user() or {}
    display_name = account.get("username") or "河小智用户"
    display_initial = account.get("initial") or display_name[:1]
    account_no = account.get("account_no") or "—"
    created_at = str(account.get("created_at") or "").replace("T", " ")[:10]
    cards = [
        ("today", "今日待办", f'{int(stats["today_done"])}/{int(stats["today_total"])}', ""),
        ("open", "未完成", str(int(stats["open"])), ""),
        ("done", "已完成", str(int(stats["done"])), ""),
        ("rate", "完成率", f'{int(stats["rate"])}%', ""),
    ]
    stats_html = "".join(
        f'<div class="profile-stat"><strong>{ui.e(value)}</strong><span>{ui.e(label)}</span></div>'
        for _, label, value, _suffix in cards
    )
    meta = f'<span>{ui.icon("id-card", 11)}{ui.e(account_no)}</span>'
    if created_at:
        meta += f'<span>{ui.icon("calendar", 11)}注册于 {ui.e(created_at)}</span>'
    return (
        '<section class="profile-card">'
        '<div class="profile-head">'
        f'<div class="profile-avatar">{ui.e(display_initial)}</div>'
        "<div>"
        f'<h2 class="profile-name">{ui.e(display_name)}</h2>'
        f'<div class="profile-meta">{meta}</div>'
        "</div>"
        f'<a class="profile-link" href="?page=growth">{ui.icon("trending-up", 13)}我的成长档案</a>'
        "</div>"
        f'<div class="profile-stats">{stats_html}</div>'
        "</section>"
    )


def _services_panel() -> str:
    services = "".join(
        f'<a class="service-tile" href="{ui.e(service["href"])}">'
        f'<span class="service-icon">{ui.icon(_SERVICE_ICONS.get(service["icon"], service["icon"]), 17)}</span>'
        f'<span><span class="service-name">{ui.e(service["name"])}</span>'
        f'<span class="service-desc">{ui.e(service["desc"])}</span></span></a>'
        for service in data.SERVICES[:6]
    )
    return (
        '<section class="panel">'
        '<div class="panel-head"><div>'
        f'<div class="panel-title"><span class="panel-icon">{ui.icon("layout-grid", 17)}</span>快捷服务</div>'
        '<div class="panel-sub">常用入口，一步直达</div>'
        "</div>"
        f'<a class="panel-link" href="?page=services">全部服务 {ui.icon("chevron-right", 12)}</a>'
        "</div>"
        f'<div class="service-grid">{services}</div>'
        "</section>"
    )


# --------------------------------------------------------------------------- #
# 任务管理：新增 / 列表 / 勾选 / 修改 / 删除
# --------------------------------------------------------------------------- #
def _add_task_form() -> None:
    now = datetime.now()
    default_date = (now + timedelta(hours=1)).date()
    default_time = (now + timedelta(hours=1)).time().replace(second=0, microsecond=0)

    with st.container(key="center-add-form"):
        with st.form("center_add_task_form", border=False):
            title = st.text_input("任务标题", key="new_task_title", placeholder="例如：提交《自然语言处理》实验报告")
            row1 = st.columns([1, 1, 1, 1])
            category = row1[0].selectbox("分类", tasks.CATEGORIES, key="new_task_cat")
            priority_label = row1[1].selectbox(
                "优先级",
                [pri["label"] for pri in PRIORITIES.values()],
                index=1,
                key="new_task_pri",
            )
            due_date = row1[2].date_input("截止日期", value=default_date, format="YYYY-MM-DD", key="new_task_date")
            due_time = row1[3].time_input("截止时间", value=default_time, key="new_task_time")
            row2 = st.columns([1.6, 1])
            place = row2[0].text_input("地点 / 平台（可选）", key="new_task_place", placeholder="例如：线上 · 雨课堂")
            note = row2[1].text_input("备注（可选）", key="new_task_note", placeholder="补充说明")
            submitted = st.form_submit_button("＋ 新增任务", type="primary", use_container_width=True)

    if not submitted:
        return
    title = (title or "").strip()
    if not title:
        st.error("请先填写任务标题。")
        return
    priority_key = next(
        (key for key, pri in PRIORITIES.items() if pri["label"] == priority_label),
        "medium",
    )
    due = f"{due_date.isoformat()}T{due_time.strftime('%H:%M')}"
    try:
        tasks.add_task(title, category=category, priority=priority_key, due=due, place=place, note=note)
    except ValueError as exc:
        st.error(str(exc))
        return
    for key in ("new_task_title", "new_task_place", "new_task_note"):
        st.session_state.pop(key, None)
    st.toast("任务已新增，并同步到成长档案统计。")
    st.rerun()


@st.dialog("修改任务")
def _edit_task_dialog(task_id: str) -> None:
    task = tasks.get_task(task_id)
    if not task:
        st.info("该任务已被删除。")
        return
    with st.form("center_edit_task_form", border=False):
        title = st.text_input("任务标题", value=task["title"])
        row1 = st.columns([1, 1])
        category = row1[0].selectbox("分类", tasks.CATEGORIES, index=tasks.CATEGORIES.index(task["category"]))
        priority_label = row1[1].selectbox(
            "优先级",
            [pri["label"] for pri in PRIORITIES.values()],
            index=list(PRIORITIES.keys()).index(task["priority"]),
        )
        row2 = st.columns([1, 1])
        try:
            due_dt = datetime.strptime(task["due"], "%Y-%m-%dT%H:%M")
        except (TypeError, ValueError):
            due_dt = datetime.now()
        due_date = row2[0].date_input("截止日期", value=due_dt.date(), format="YYYY-MM-DD")
        due_time = row2[1].time_input("截止时间", value=due_dt.time().replace(second=0, microsecond=0))
        place = st.text_input("地点 / 平台（可选）", value=task.get("place", ""))
        note = st.text_input("备注（可选）", value=task.get("note", ""))
        if st.form_submit_button("保存修改", type="primary", use_container_width=True):
            priority_key = next(
                (key for key, pri in PRIORITIES.items() if pri["label"] == priority_label),
                "medium",
            )
            due = f"{due_date.isoformat()}T{due_time.strftime('%H:%M')}"
            try:
                tasks.update_task(
                    task_id,
                    title=title,
                    category=category,
                    priority=priority_key,
                    due=due,
                    place=place,
                    note=note,
                )
            except ValueError as exc:
                st.error(str(exc))
                return
            st.toast("任务已更新。")
            st.rerun()


def _sync_task_widgets(items: list[dict]) -> None:
    """若任务在别处被修改，先把复选框控件同步到最新状态。"""
    seen = st.session_state.get(_SEEN_KEY)
    if not isinstance(seen, dict):
        return
    for item in items:
        key = _CK_KEY + item["id"]
        if key not in st.session_state:
            continue
        if item["id"] in seen and bool(seen[item["id"]]) != bool(item["done"]):
            st.session_state[key] = bool(item["done"])


def _task_row(item: dict, show_completed_time: bool = False) -> tuple[dict[str, bool], bool]:
    """渲染一行任务；返回 (本行勾选快照, 是否发生了勾选变化)。"""
    key = _CK_KEY + item["id"]
    if key not in st.session_state:
        st.session_state[key] = bool(item["done"])
    left, mid, act = st.columns([0.56, 0.26, 0.18], gap="small")
    with left:
        checked = st.checkbox(item["title"], key=key)
    with mid:
        if show_completed_time:
            completed = str(item.get("completed_at") or "")
            completed_label = completed.replace("T", " ") if completed else "已完成"
            meta_html = (
                f'<span class="meta-line done-at">{ui.icon("circle-check", 10)}完成于 {ui.e(completed_label)}</span>'
                f'<span class="meta-line">{ui.icon("flag", 10)}{ui.e(item["priority_label"])}</span>'
            )
        else:
            due_line = f'<span class="meta-line{" due-hot" if item["is_overdue"] else ""}">{ui.icon("alarm-clock", 10)}{ui.e(item["due_label"])}</span>'
            place_html = (
                f'<span class="meta-line">{ui.icon("map-pin", 10)}{ui.e(item["place"])}</span>'
                if item.get("place")
                else ""
            )
            meta_html = (
                f'<span class="meta-line">{ui.icon("flag", 10)}{ui.e(item["priority_short"])}优先级 · {ui.e(item["category"])}</span>'
                + due_line
                + place_html
            )
        _render_html(
            f'<div class="center-task-meta">'
            f'<span class="tag {ui.e(item["priority_tone"])}">{ui.e(item["priority_short"])}</span>'
            + meta_html
            + "</div>",
            unsafe_allow_html=True,
        )
    with act:
        confirm_key = _DEL_CONFIRM_KEY + item["id"]
        # 显式确认：按钮文字直接变成「确认?」，再点一次才真正删除。
        armed = bool(st.session_state.get(confirm_key))
        btn1, btn2 = st.columns(2, gap="small")
        if btn1.button("修改", key=f"center_edit_{item['id']}", help="修改该任务"):
            _edit_task_dialog(item["id"])
        del_label = "确认?" if armed else "删除"
        del_help = "再次点击以确认删除" if armed else "删除该任务"
        if btn2.button(del_label, key=f"center_del_{item['id']}", help=del_help):
            if armed:
                st.session_state.pop(confirm_key, None)
                tasks.delete_task(item["id"])
                st.session_state.pop(key, None)
                st.toast("任务已删除。")
                st.rerun()
            else:
                st.session_state[confirm_key] = True
                # 立刻重跑一次，让按钮文字切换成「确认?」。否则本轮渲染已经完成，
                # 用户点完看不到任何反馈，容易连点两下直接删掉任务。
                st.rerun()
    changed = bool(checked) != bool(item["done"])
    if changed:
        tasks.set_done(item["id"], bool(checked))
    return {item["id"]: bool(item["done"])}, changed


def _render_task_panel() -> None:
    today_items = tasks.get_tasks("today")
    upcoming_items = tasks.get_tasks("upcoming")
    done_items = tasks.get_tasks("done")
    done_count, total_count = tasks.todo_progress()
    percent = int(done_count / total_count * 100) if total_count else 0

    _sync_task_widgets(today_items + upcoming_items + done_items)

    with st.container(key="center-task-panel"):
        _render_html(
            '<div class="panel-head"><div>'
            f'<div class="panel-title"><span class="panel-icon">{ui.icon("circle-check", 17)}</span>任务清单</div>'
            f'<div class="panel-sub">{_date_label()} · 今日进度 {done_count}/{total_count} · 近期任务 {len(upcoming_items)} 项</div>'
            "</div>"
            f'<a class="panel-link" href="{ui.e(ui.page_url("center", view="stats"))}">数据看板 {ui.icon("chevron-right", 12)}</a>'
            "</div>"
            '<div class="todo-progress-row"><span>今日完成进度</span><span><b>'
            + str(done_count)
            + "</b> / "
            + str(total_count)
            + "</span></div>"
            + f'<div class="progress-track"><div class="progress-fill" style="width:{percent}%"></div></div>',
            unsafe_allow_html=True,
        )

        _add_task_form()

        tab_today, tab_upcoming, tab_done = st.tabs(
            [
                f"⏰ 今日待办 {len(today_items)}",
                f"📅 近期任务 {len(upcoming_items)}",
                f"✅ 已完成 {len(done_items)}",
            ]
        )
        seen: dict[str, bool] = {}
        changed = False

        with tab_today:
            if not today_items:
                _render_html(
                    '<div class="center-empty">' + ui.icon("circle-check", 22)
                    + "今天没有待办任务<br>去「近期任务」看看后面的安排，或新增一条任务。</div>",
                    unsafe_allow_html=True,
                )
            for item in today_items:
                row_seen, row_changed = _task_row(item)
                seen.update(row_seen)
                changed = changed or row_changed

        with tab_upcoming:
            if not upcoming_items:
                _render_html(
                    '<div class="center-empty">' + ui.icon("calendar", 22)
                    + "近期没有新任务<br>点击上方「新增任务」，把下周要做的事提前安排好。</div>",
                    unsafe_allow_html=True,
                )
            for item in upcoming_items:
                row_seen, row_changed = _task_row(item)
                seen.update(row_seen)
                changed = changed or row_changed

        with tab_done:
            if not done_items:
                _render_html(
                    '<div class="center-empty">' + ui.icon("trophy", 22)
                    + "还没有已完成的任务<br>勾选左侧待办即可完成，完成记录会写入成长档案。</div>",
                    unsafe_allow_html=True,
                )
            for item in done_items[:12]:
                row_seen, row_changed = _task_row(item, show_completed_time=True)
                seen.update(row_seen)
                changed = changed or row_changed

        st.session_state[_SEEN_KEY] = seen
        _render_html(
            f'<div class="data-note" style="margin-top:13px">{ui.icon("info", 13)}任务实时保存在本机（.data 目录），并同步到首页待办与成长档案统计；删除需二次确认。</div>',
            unsafe_allow_html=True,
        )

    if changed:
        st.rerun()


def _render_overview() -> None:
    """概览：个人信息 + 待办速览 + 快捷服务，只保留真实、高频的信息。"""
    stats = tasks.task_stats()
    _render_html(_profile_card(stats), unsafe_allow_html=True)
    _render_html('<div style="height:16px"></div>', unsafe_allow_html=True)

    left, right = st.columns([1.36, 0.64], gap="medium")
    with left:
        _render_html(_overview_todo_panel(), unsafe_allow_html=True)
    with right:
        _render_html(_services_panel(), unsafe_allow_html=True)

    _render_html(
        '<div class="section-space" style="height:18px"></div>' + _growth_banner(stats),
        unsafe_allow_html=True,
    )


def _render_tasks() -> None:
    """我的任务：新增 / 修改 / 删除 / 勾选完成的完整管理页。"""
    _render_html(
        ui.section_header(
            title="我的任务",
            eyebrow="MY TASKS",
            subtitle="新增、修改、删除与勾选完成都在这一页，先处理最紧急的一件事",
            link_label="查看数据看板",
            link_href=ui.page_url("center", view="stats"),
            icon_name="circle-check",
        ),
        unsafe_allow_html=True,
    )
    _render_task_panel()


def _render_stats() -> None:
    """数据看板：完成进度、优先级 / 分类分布、趋势与即将截止。"""
    stats = tasks.task_stats()
    _render_html(
        ui.section_header(
            title="任务数据看板",
            eyebrow="MY DASHBOARD",
            subtitle="完成进度、优先级与截止日期一目了然，数字全部来自你的真实任务记录",
            link_label="去任务页",
            link_href=ui.page_url("center", view="tasks"),
            icon_name="chart",
        )
        + f'<div class="grid-2">{viz.progress_ring_card(stats)}{viz.priority_bars_card(stats)}</div>'
        + '<div class="section-space" style="height:14px"></div>'
        + f'<div class="grid-2">{viz.category_bars_card(stats)}{viz.week_trend_card(stats)}</div>'
        + '<div class="section-space" style="height:14px"></div>'
        + viz.upcoming_card(stats),
        unsafe_allow_html=True,
    )


def render() -> None:
    _render_html(_STYLE, unsafe_allow_html=True)

    view = ui.qp("view").strip()
    if view not in _VIEWS:
        view = "overview"

    _render_html(_page_head(view), unsafe_allow_html=True)

    if view == "tasks":
        _render_tasks()
    elif view == "stats":
        _render_stats()
    else:
        _render_overview()
