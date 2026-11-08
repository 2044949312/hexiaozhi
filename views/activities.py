# -*- coding: utf-8 -*-
"""河小智 · 校园活动页。

页面结构（校园活动模块内的二级导航）：
- 官方活动（默认）：?page=activities&view=official
  分类筛选用 &cat=科技（“全部”不写参数）；首页推荐用 &id=ai-hackathon，
  该活动置顶并高亮。
- 我的活动：?page=activities&view=mine
  内部再分四个独立页面，用 &mtab= 切换：
  - mtab=joined（默认）：我报名的活动
  - mtab=create：创建活动
  - mtab=created：我创建的活动
  - mtab=tasks：活动任务（只显示与本人报名 / 自建活动相关的任务）
  各页只统计当前账号真实选择或创建的数据，避免出现用户没选过的内容。

报名：HTML GET 表单提交 page=activities&view=official&join=ai-hackathon，
由 core.state.register_activity 去重，报名状态记录在 st.session_state.registrations。
取消报名：page=activities&view=official&cancel=ai-hackathon
（在「我的活动」中取消时保留 view=mine，处理完仍留在当前页）。
"""

from __future__ import annotations

from datetime import date, datetime, time as dtime, timedelta

import streamlit as st

from core import activity_store
from core import activity_tasks as task_store
from core import data, ui
from core.state import is_registered, register_activity, registrations, unregister_activity


def _render_html(markup: str, **kwargs) -> None:
    """优先走 core.ui.render_html（站内链接在当前标签页打开），旧版本回退 st.markdown。"""
    render = getattr(ui, "render_html", None)
    if callable(render):
        render(markup)
    else:
        st.markdown(markup, **kwargs)


_CATEGORY_TONES = {"科技": "blue", "文艺": "gold", "讲座": "teal", "运动": "green", "其他": "gray"}
_CATEGORY_ICONS = {"科技": "cpu", "文艺": "music", "讲座": "book-open", "运动": "run", "其他": "compass"}

_STYLE = """
<style>
.activities-toolbar{
  display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;
  margin:0 2px 18px;
}
.activities-count{
  display:inline-flex;align-items:center;gap:6px;font-size:10.5px;color:var(--muted);
  padding:7px 11px;border-radius:999px;background:#fff;border:1px solid var(--border);
  box-shadow:var(--shadow-xs);
}
.activities-count b{color:var(--primary);font-size:12px;}
.activities-count svg{color:var(--primary);}
.join-flash{
  display:flex;gap:11px;align-items:flex-start;margin:0 2px 18px;padding:14px 17px;
  border-radius:16px;border:1px solid #CFF5EC;background:#ECFDF9;color:#0F766E;
  font-size:11.5px;line-height:1.7;box-shadow:var(--shadow-xs);
}
.join-flash svg{flex:0 0 auto;margin-top:1px;}
.join-flash b{display:block;font-size:12.5px;margin-bottom:2px;}
.join-flash.info{background:#EEF4FF;border-color:#D8E5FB;color:#1D4ED8;}
.join-flash.warning{background:#FFF8E8;border-color:#FBEBC7;color:#8A5B0B;}
.activity-detail-card{margin-bottom:8px;}
.activity-detail-card.spotlight{border-color:#BFD6F8;box-shadow:0 22px 50px rgba(15,27,51,.13);}
.activity-detail-meta{
  display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px 18px;margin:2px 0 12px;
}
.activity-detail-meta .meta-cell{display:flex;align-items:flex-start;gap:8px;min-width:0;}
.activity-detail-meta .meta-cell svg{color:#8FA0B9;flex:0 0 auto;margin-top:2px;}
.activity-detail-meta em{
  display:block;font-style:normal;font-size:8.5px;letter-spacing:.06em;color:var(--muted-light);
}
.activity-detail-meta .meta-value{
  display:block;font-size:11px;font-weight:650;color:var(--ink-soft);line-height:1.5;margin-top:1px;
}
.capacity-row{
  display:flex;align-items:center;justify-content:space-between;gap:10px;
  font-size:10px;color:var(--muted);margin:2px 0 6px;
}
.capacity-row b{color:var(--ink);font-size:11px;}
.capacity-row .capacity-pct{color:var(--primary);font-weight:800;}
.activity-detail-tags{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 4px;}
.join-form .join-hint{font-size:9.5px;color:var(--muted-light);line-height:1.6;margin-left:auto;}
.my-activity-list{display:flex;flex-direction:column;gap:2px;}
.my-activity-row{
  display:flex;align-items:center;gap:11px;padding:10px 0;border-bottom:1px dashed #EDF1F8;
  text-decoration:none;color:inherit;transition:background .16s ease;
}
.my-activity-row:last-child{border-bottom:0;}
.my-activity-row:hover{background:#F8FAFF;margin:0 -9px;padding-left:9px;padding-right:9px;border-radius:11px;}
.my-activity-check{
  width:21px;height:21px;border-radius:7px;flex:0 0 auto;display:grid;place-items:center;
  color:#fff;background:linear-gradient(135deg,#1D4ED8,#14B8A6);
}
.my-activity-main{min-width:0;flex:1;}
.my-activity-main b{display:block;font-size:12px;font-weight:700;color:var(--ink);line-height:1.4;}
.my-activity-main small{display:block;font-size:9.5px;color:var(--muted);margin-top:3px;}
.tip-card .panel-title{font-size:13.5px;}
.tip-card p{margin:8px 0 0;font-size:10.5px;line-height:1.75;color:var(--muted);}
/* ---------- 活动任务看板 ---------- */
.task-board-panel{
  background:#fff;border:1px solid var(--border);border-radius:23px;
  padding:20px 22px 13px;box-shadow:var(--shadow-sm);
}
.task-board-panel [data-testid="stVerticalBlock"]{gap:.4rem;}
.task-board-panel [data-testid="stHorizontalBlock"]{
  align-items:center;gap:12px;padding:3px 0;border-bottom:1px dashed #EDF1F8;
}
.task-board-panel [data-testid="stHorizontalBlock"]:last-of-type{border-bottom:0;padding-bottom:0;}
.task-board-panel [data-testid="stCheckbox"]{margin:0;}
.task-board-panel [data-testid="stCheckbox"] label{gap:11px;align-items:flex-start;padding:5px 0;}
.task-board-panel [data-testid="stCheckbox"] label p{
  font-size:12.5px!important;font-weight:650!important;line-height:1.5!important;color:var(--ink)!important;
}
.task-board-panel [data-testid="stCheckbox"] [data-baseweb="checkbox"] div{border-radius:7px;}
.task-board-panel [data-testid="stCheckbox"]:has(input:checked) label p{
  color:#9AA8BD!important;text-decoration:line-through;
}
.task-meta{display:flex;flex-direction:column;align-items:flex-end;gap:4px;text-align:right;min-width:0;}
.task-meta .meta-line{display:inline-flex;align-items:center;gap:3px;font-size:9px;color:var(--muted);line-height:1.4;}
.task-meta .meta-line svg{color:#A7B4C7;flex:0 0 auto;}
.task-meta .task-progress{display:flex;align-items:center;gap:6px;justify-content:flex-end;width:132px;}
.task-meta .task-progress .mini-progress{flex:1;}
.task-meta .task-progress b{font-size:9.5px;color:var(--primary);font-weight:800;white-space:nowrap;}
.task-note{font-size:9px;color:var(--muted-light);line-height:1.6;text-align:right;max-width:190px;}
.prio-row{display:flex;align-items:center;gap:9px;margin-bottom:11px;}
.prio-row:last-child{margin-bottom:0;}
.prio-row .prio-name{flex:0 0 34px;font-size:10.5px;font-weight:800;color:var(--ink-soft);}
.prio-row .prio-bar{flex:1;height:9px;border-radius:999px;background:#EEF2F8;overflow:hidden;}
.prio-row .prio-bar span{display:block;height:100%;border-radius:999px;}
.prio-row .prio-bar span.rose{background:linear-gradient(90deg,#BE123C,#FB7185);}
.prio-row .prio-bar span.gold{background:linear-gradient(90deg,#D99A16,#F5B942);}
.prio-row .prio-bar span.teal{background:linear-gradient(90deg,#0D9488,#2DD4BF);}
.prio-row b{flex:0 0 auto;font-size:11.5px;color:var(--ink);min-width:16px;text-align:right;}
.chart-title{font-size:11px;font-weight:800;color:var(--ink);margin:0 0 10px;display:flex;align-items:center;gap:6px;}
.chart-title svg{color:var(--primary);}
.chart-divider{height:1px;background:linear-gradient(90deg,#EDF1F8,#fff);margin:16px 0;}
.ring-wrap{display:flex;align-items:center;gap:16px;}
.ring-side{min-width:0;}
.ring-side .ring-line{font-size:10.5px;color:var(--muted);line-height:1.9;}
.ring-side .ring-line b{color:var(--ink);}
.chart-empty{
  display:flex;align-items:center;justify-content:center;gap:7px;height:96px;
  font-size:10.5px;color:var(--muted-light);background:#F8FAFC;border-radius:13px;
}
@media (max-width:960px){
  .activity-detail-meta{grid-template-columns:1fr 1fr;}
  [data-testid="stHorizontalBlock"]:has(.st-key-task-visual){flex-wrap:wrap;}
  [data-testid="stHorizontalBlock"]:has(.st-key-task-visual) > [data-testid="stColumn"]{
    flex:1 1 100%!important;width:100%!important;min-width:100%!important;
  }
}
@media (max-width:760px){
  .task-meta{display:none;}
  .task-board-panel{padding:17px 16px 10px;}
}
@media (max-width:760px){
  .activity-detail-meta{grid-template-columns:1fr;}
  .activities-toolbar{align-items:flex-start;flex-direction:column;}
  .join-form .join-hint{margin-left:0;}
  .my-activity-row{align-items:flex-start;}
}
/* ---------- 校园活动二级导航 ---------- */
.act-nav-wrap{
  display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;
  margin:0 0 18px;
}
.act-nav{
  display:flex;align-items:center;gap:5px;padding:5px;border-radius:16px;
  background:#fff;border:1px solid var(--border);box-shadow:var(--shadow-xs);
  max-width:100%;overflow-x:auto;scrollbar-width:none;
}
.act-nav::-webkit-scrollbar{display:none;}
.act-nav-item{
  display:inline-flex;align-items:center;gap:8px;padding:9px 16px;border-radius:11px;
  text-decoration:none!important;color:var(--muted);font-size:12px;font-weight:750;
  white-space:nowrap;transition:all .18s ease;line-height:1.2;
}
.act-nav-item svg{flex:0 0 auto;}
.act-nav-item:hover{background:#F6FAFF;color:var(--primary);}
.act-nav-item.active{
  background:linear-gradient(135deg,#1D4ED8,#2563EB);color:#fff;
  box-shadow:0 8px 18px rgba(29,78,216,.22);
}
.act-nav-count{
  display:inline-flex;align-items:center;justify-content:center;min-width:20px;height:20px;
  padding:0 6px;border-radius:999px;background:var(--primary-soft);color:var(--primary);
  font-size:9.5px;font-weight:800;
}
.act-nav-item.active .act-nav-count{background:rgba(255,255,255,.22);color:#fff;}
.act-nav-create{
  display:inline-flex;align-items:center;gap:6px;padding:9px 14px;border-radius:11px;
  background:#fff;border:1px solid #D8E6FB;color:var(--primary)!important;
  font-size:11.5px;font-weight:750;text-decoration:none!important;white-space:nowrap;
  box-shadow:var(--shadow-xs);transition:all .18s ease;
}
.act-nav-create:hover{background:#F5F9FF;border-color:#BCD1F1;transform:translateY(-1px);}
/* ---------- 我的活动：报名行 / 自建活动 ---------- */
.my-activity-main-link{
  display:flex;align-items:center;gap:11px;flex:1;min-width:0;
  text-decoration:none!important;color:inherit!important;
}
.my-activity-row .row-cancel{
  display:inline-flex;align-items:center;gap:4px;padding:6px 9px;border-radius:8px;
  border:1px solid var(--border);background:#fff;color:var(--muted)!important;
  font-size:9.5px;font-weight:700;text-decoration:none!important;white-space:nowrap;
  transition:color .16s ease,border-color .16s ease,background .16s ease;
}
.my-activity-row .row-cancel:hover{color:var(--rose)!important;border-color:#FBD5DE;background:#FFF5F7;}
.created-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;}
.created-card{
  display:flex;gap:13px;padding:13px;border-radius:17px;background:#fff;
  border:1px solid var(--border);box-shadow:var(--shadow-xs);min-width:0;
}
.created-thumb{
  width:108px;height:82px;border-radius:12px;overflow:hidden;flex:0 0 auto;
  background:linear-gradient(135deg,#0F2A5C,#14B8A6);
}
.created-thumb img{width:100%;height:100%;object-fit:cover;display:block;}
.created-info{min-width:0;flex:1;}
.created-info .activity-cat{margin-bottom:3px;font-size:8.5px;}
.created-info b{display:block;font-size:12.5px;font-weight:750;color:var(--ink);line-height:1.45;}
.created-info small{display:block;font-size:9px;color:var(--muted);margin-top:4px;line-height:1.55;}
.created-info p{
  font-size:9.5px;color:var(--muted-light);line-height:1.6;margin:5px 0 0;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;
}
.created-actions{display:flex;align-items:center;gap:7px;margin-top:7px;}
.create-hint{font-size:9.5px;color:var(--muted-light);line-height:1.6;margin-top:10px;}
/* ---------- 我的活动：内部导航（每个功能独立成页） ---------- */
.mine-tabs{
  display:flex;align-items:center;gap:4px;margin:0 0 18px;padding:0 0 0;
  border-bottom:1px solid var(--border);max-width:100%;overflow-x:auto;scrollbar-width:none;
}
.mine-tabs::-webkit-scrollbar{display:none;}
.mine-tab{
  display:inline-flex;align-items:center;gap:7px;padding:11px 15px 10px;
  color:var(--muted)!important;font-size:11.5px;font-weight:750;line-height:1.2;
  text-decoration:none!important;white-space:nowrap;border-bottom:2px solid transparent;
  margin-bottom:-1px;transition:color .16s ease,background .16s ease,border-color .16s ease;
}
.mine-tab svg{flex:0 0 auto;}
.mine-tab:hover{color:var(--primary)!important;background:#F6FAFF;border-radius:10px 10px 0 0;}
.mine-tab.active{
  color:var(--primary)!important;border-bottom-color:var(--primary);
  background:linear-gradient(180deg,rgba(37,99,235,.08),rgba(37,99,235,0));
  border-radius:10px 10px 0 0;
}
.mine-tab-count{
  display:inline-flex;align-items:center;justify-content:center;min-width:19px;height:19px;
  padding:0 6px;border-radius:999px;background:var(--primary-soft);color:var(--primary);
  font-size:9px;font-weight:800;
}
.mine-tab.active .mine-tab-count{background:var(--primary);color:#fff;}
@media (max-width:760px){
  .mine-tab{flex:1;justify-content:center;gap:4px;padding:10px 5px 9px;font-size:10px;}
  .mine-tab svg{display:none;}
  .act-nav-wrap{align-items:stretch;}
  .act-nav{width:100%;}
  .act-nav-item{flex:1;justify-content:center;}
  .act-nav-create{justify-content:center;}
  .created-grid{grid-template-columns:1fr;}
  .created-thumb{width:84px;height:66px;}
}
</style>
"""


def _categories() -> list[str]:
    categories: list[str] = []
    for activity in data.ACTIVITIES:
        if activity["category"] not in categories:
            categories.append(activity["category"])
    return categories


def _banner(tone: str, title: str, text: str) -> str:
    icons = {"success": "circle-check", "info": "info", "warning": "alert-circle"}
    return (
        f'<div class="join-flash {ui.e(tone)}">'
        f'{ui.icon(icons.get(tone, "info"), 17)}'
        f"<div><b>{ui.e(title)}</b><span>{text}</span></div>"
        f"</div>"
    )


def _subnav(active: str) -> str:
    """校园活动模块内部导航：官方活动 / 我的活动（只在活动页出现）。"""
    items = [
        ("official", "官方活动", "compass", len(data.ACTIVITIES)),
        # 我的活动不显示合并计数：报名与自建是两个独立页面，
        # 合并数字容易让用户误以为新建活动「凭空多了一条」。
        ("mine", "我的活动", "circle-check", None),
    ]
    links = "".join(
        f'<a class="act-nav-item {"active" if key == active else ""}" '
        f'href="{ui.e(ui.page_url("activities", view=key))}">'
        f"{ui.icon(icon_name, 15)}<span>{ui.e(label)}</span>"
        + (f'<span class="act-nav-count">{count}</span>' if count is not None else "")
        + "</a>"
        for key, label, icon_name, count in items
    )
    create_href = ui.e(ui.page_url("activities", view="mine", mtab="create"))
    # 已经在「创建活动」子页时不再重复显示右上角入口。
    show_create = not (active == "mine" and ui.qp("mtab").strip() == "create")
    create_btn = (
        f'<a class="act-nav-create" href="{create_href}">{ui.icon("plus", 14)}创建活动</a>'
        if show_create
        else ""
    )
    return (
        '<div class="act-nav-wrap">'
        f'<nav class="act-nav" aria-label="校园活动导航">{links}</nav>'
        f"{create_btn}"
        "</div>"
    )


def _mine_tabs(active: str) -> str:
    """「我的活动」内部导航：每个功能都是独立页面。

    计数只来自当前账号真实产生的数据：报名数 = 报名记录条数，
    创建数 = 自建活动条数；创建 / 任务不显示容易误解的合并数字。
    """
    known_ids = {activity["id"] for activity in data.ACTIVITIES}
    reg_count = sum(1 for activity_id in registrations() if activity_id in known_ids)
    items = [
        ("joined", "我报名的活动", "circle-check", reg_count),
        ("create", "创建活动", "plus", None),
        ("created", "我创建的活动", "flag", len(activity_store.created_activities())),
        ("tasks", "活动任务", "chart", None),
    ]
    links = "".join(
        f'<a class="mine-tab {"active" if key == active else ""}" '
        f'href="{ui.e(ui.page_url("activities", view="mine", mtab=key))}">'
        f"{ui.icon(icon_name, 14)}<span>{ui.e(label)}</span>"
        + (f'<span class="mine-tab-count">{count}</span>' if count is not None else "")
        + "</a>"
        for key, label, icon_name, count in items
    )
    return f'<nav class="mine-tabs" aria-label="我的活动导航">{links}</nav>'


def _created_flash() -> str:
    """显示并清空一次创建 / 删除自建活动的提示。"""
    flash = st.session_state.pop("act_created_flash", None)
    if not flash:
        return ""
    tone, title, text = flash
    return _banner(tone, title, ui.e(text))


def _notify_created(tone: str, title: str, text: str) -> None:
    st.session_state["act_created_flash"] = (tone, title, text)


def _handle_join() -> str:
    """处理一次 GET 报名 / 取消报名；register_activity 内部去重。"""
    cancel_id = ui.qp("cancel").strip()
    if cancel_id:
        activity = next((item for item in data.ACTIVITIES if item["id"] == cancel_id), None)
        if activity is None:
            return _banner("warning", "未找到这场活动", "活动可能已经结束或链接有误。")
        if unregister_activity(cancel_id):
            return _banner(
                "info",
                "已取消报名",
                f"「{ui.e(activity['title'])}」已从你的活动行程中移除，名额已释放给其他同学。",
            )
        return _banner("info", "你还没有报名这场活动", "无需取消，直接挑一场感兴趣的活动报名吧。")

    join_id = ui.qp("join").strip()
    if not join_id:
        return ""
    activity = next((item for item in data.ACTIVITIES if item["id"] == join_id), None)
    if activity is None:
        return _banner("warning", "未找到这场活动", "活动可能已经结束或链接有误，去下面看看其他正在报名的活动吧。")
    title = ui.e(activity["title"])
    if register_activity(join_id):
        return _banner(
            "success",
            "报名成功",
            f"「{title}」已加入你的活动行程，如需退出可在活动卡片上点「取消报名」。",
        )
    if is_registered(join_id):
        return _banner(
            "info",
            "你已报名这场活动",
            f"「{title}」已经在你的活动行程里，无需重复报名，活动开始前 24 小时会收到提醒。",
        )
    return ""


def _chip(label: str, active: bool, href: str, icon_name: str = "") -> str:
    ico = ui.icon(icon_name, 12) if icon_name else ""
    return f'<a class="chip {"active" if active else ""}" href="{ui.e(href)}">{ico}{ui.e(label)}</a>'


def _cover(activity: dict) -> str:
    hot = (
        f'<span class="cover-hot">{ui.icon("flame", 11)}HOT</span>'
        if activity.get("hot")
        else ""
    )
    return (
        '<div class="activity-cover">'
        + ui.img_tag(activity["cover"], f"{activity['title']} 活动封面", fallback_icon="compass")
        + '<div class="cover-badges">'
        + f'<span class="cover-date">{ui.icon("calendar", 11)}{ui.e(activity["date"])}</span>'
        + hot
        + "</div></div>"
    )


def _detail_card(activity: dict, selected_cat: str, spotlight: bool, owned: bool = False) -> str:
    tone = _CATEGORY_TONES.get(activity["category"], "blue")
    icon_name = _CATEGORY_ICONS.get(activity["category"], "compass")
    registered = is_registered(activity["id"])
    try:
        percent = int(round(activity["participants"] / max(activity["capacity"], 1) * 100))
    except (TypeError, ValueError, ZeroDivisionError):
        percent = 0
    percent = max(0, min(100, percent))

    tags = "".join(ui.tag(tag, tone) for tag in activity.get("tags", []))
    meta_cells = [
        ("calendar", "活动日期", activity["date"]),
        ("clock", "活动时间", activity["time"]),
        ("map-pin", "活动地点", activity["location"]),
        ("alert-circle", "报名截止", activity["deadline"]),
    ]
    meta_html = "".join(
        f'<div class="meta-cell">{ui.icon(icon_name, 14)}'
        f"<div><em>{ui.e(label)}</em>"
        f'<span class="meta-value">{ui.e(value)}</span></div></div>'
        for icon_name, label, value in meta_cells
    )

    spotlight_tag = '<span class="tag violet">首页推荐</span>' if spotlight else ""
    card_class = "activity-detail-card spotlight" if spotlight else "activity-detail-card"
    hidden_fields = (
        '<input type="hidden" name="page" value="activities"/>'
        '<input type="hidden" name="view" value="official"/>'
        f'<input type="hidden" name="join" value="{ui.e(activity["id"])}"/>'
        f'<input type="hidden" name="cat" value="{ui.e(selected_cat)}"/>'
    )
    if spotlight:
        hidden_fields += f'<input type="hidden" name="id" value="{ui.e(activity["id"])}"/>'

    if owned:
        action_html = (
            f'<span class="joined-badge">{ui.icon("flag", 13)}我发起的活动</span>'
            f'<span class="join-hint">{ui.icon("users", 11)}已开放报名 · 可回到「我的活动」管理</span>'
        )
    elif registered:
        action_html = (
            f'<span class="joined-badge">{ui.icon("circle-check", 13)}已报名 · 记得按时签到</span>'
            f'<a class="join-cancel" href="?page=activities&view=official&cancel={ui.e(activity["id"])}">{ui.icon("x", 11)}取消报名</a>'
            f'<span class="join-hint">{ui.icon("bell", 11)}活动开始前会通过河小智提醒你</span>'
        )
    else:
        action_html = (
            '<form method="get" action="">'
            + hidden_fields
            + f'<button type="submit">{ui.icon("check", 12)}我要报名</button>'
            + "</form>"
            + f'<span class="join-hint">{ui.icon("users", 11)}名额有限 · 报名后可计入第二课堂</span>'
        )

    return (
        f'<article class="{card_class}" id="activity-{ui.e(activity["id"])}">'
        + _cover(activity)
        + '<div class="activity-detail-body">'
        + f'<div class="activity-cat">{ui.icon(icon_name, 13)} {ui.e(activity["category"])} · CAMPUS {spotlight_tag}</div>'
        + f"<h3>{ui.e(activity['title'])}</h3>"
        + f'<p class="desc">{ui.e(activity["detail"])}</p>'
        + f'<div class="activity-detail-meta">{meta_html}</div>'
        + f'<div class="activity-detail-tags">{tags}</div>'
        + '<div class="capacity-row">'
        + f"<span>{ui.icon('users', 12)}已有 <b>{activity['participants']}</b> / {activity['capacity']} 人报名</span>"
        + f'<span class="capacity-pct">{percent}%</span>'
        + "</div>"
        + ui.progress_bar(percent, tone)
        + f'<div class="join-form">{action_html}</div>'
        + "</div></article>"
    )


def _joined_markup() -> str:
    """「我报名的活动」：官方活动中已报名的场次，可直接取消报名。"""
    ids = registrations()
    lookup = {activity["id"]: activity for activity in data.ACTIVITIES}
    rows = []
    for activity_id in ids:
        activity = lookup.get(activity_id)
        if not activity:
            continue
        detail_url = ui.page_url("activities", view="official", id=activity["id"])
        cancel_url = ui.page_url(
            "activities", view="mine", mtab="joined", cancel=activity["id"]
        )
        rows.append(
            '<div class="my-activity-row">'
            f'<a class="my-activity-main-link" href="{ui.e(detail_url)}">'
            f'<span class="my-activity-check">{ui.icon("check", 12)}</span>'
            f'<span class="my-activity-main"><b>{ui.e(activity["title"])}</b>'
            f'<small>{ui.e(activity["date"])} · {ui.e(activity["time"])} · {ui.e(activity["location"])}</small></span>'
            "</a>"
            '<span class="tag teal">已报名</span>'
            f'<a class="row-cancel" href="{ui.e(cancel_url)}">{ui.icon("x", 10)}取消报名</a>'
            "</div>"
        )
    if rows:
        body = '<div class="my-activity-list">' + "".join(rows) + "</div>"
    else:
        body = ui.empty_state(
            title="还没有报名活动",
            desc="去官方活动看看本周有哪些值得参加的活动，报名后会出现在这里。",
            icon_name="compass",
            action_label="去看官方活动",
            action_href="?page=activities&view=official",
        )
    return (
        '<section class="panel">'
        '<div class="panel-head"><div>'
        f'<div class="panel-title"><span class="panel-icon">{ui.icon("circle-check", 17)}</span>我报名的活动</div>'
        f'<div class="panel-sub">已报名 {len(rows)} 场 · 活动开始前 24 小时提醒</div>'
        '</div><a class="panel-link" href="?page=growth">查看成长档案 ' + ui.icon("chevron-right", 12) + "</a></div>"
        + body
        + f'<div class="data-note" style="margin-top:12px">{ui.icon("info", 13)}报名记录按登录账号保存在本机，刷新或重新登录后仍然保留；正式报名以学校活动系统为准。</div>'
        "</section>"
    )


def _created_markup() -> str:
    """「我创建的活动」：展示当前账号发起的活动。"""
    items = activity_store.created_activities()
    cards = []
    for activity in items:
        icon_name = _CATEGORY_ICONS.get(activity.get("category", "其他"), "compass")
        cards.append(
            '<article class="created-card">'
            '<div class="created-thumb">'
            + ui.img_tag(activity["cover"], f"{activity['title']} 活动封面", fallback_icon="compass")
            + "</div>"
            '<div class="created-info">'
            f'<div class="activity-cat">{ui.icon(icon_name, 11)} {ui.e(activity.get("category", "其他"))} · 学生自建</div>'
            f'<b>{ui.e(activity["title"])}</b>'
            f'<small>{ui.e(activity["date"])} · {ui.e(activity["time"])} · {ui.e(activity["location"])} · 上限 {activity["capacity"]} 人</small>'
            f'<p>{ui.e(activity["detail"])}</p>'
            "</div></article>"
        )
    if cards:
        body = '<div class="created-grid">' + "".join(cards) + "</div>"
    else:
        body = ui.empty_state(
            title="还没有创建活动",
            desc="社团例会、约球、读书会……填好信息就能发起一场属于你的校园活动。",
            icon_name="plus",
            action_label="去创建活动",
            action_href=ui.page_url("activities", view="mine", mtab="create"),
        )
    return (
        '<div class="section-space"></div>'
        + ui.section_header(
            title="我创建的活动",
            eyebrow="MY CREATIONS · 学生自建",
            subtitle=f"当前账号共发起 {len(items)} 场活动，仅自己可见与管理",
            icon_name="flag",
        )
        + '<section class="panel">'
        + body
        + "</section>"
    )


def _render_create_form() -> None:
    """活动创建：发布后写入当前账号的自建活动库。"""
    _render_html(
        '<div id="create-activity" class="section-space"></div>'
        + ui.section_header(
            title="创建活动",
            eyebrow="CREATE · 发起你的校园活动",
            subtitle="社团活动、约球、读书会都可以，填好信息即可发布到「我创建的活动」。",
            icon_name="plus",
        )
    )
    # 发布成功后轮换表单控件 key，让下一次输入从空白开始；校验失败时保留已填内容。
    token = int(st.session_state.get("act-create-token", 0))
    prefix = f"act-new-{token}"
    with st.form("act-create-form", clear_on_submit=False):
        title = st.text_input(
            "活动名称", placeholder="例如：计算机学院羽毛球友谊赛", key=f"{prefix}-title"
        )
        c1, c2, c3 = st.columns(3)
        category = c1.selectbox("活动分类", list(activity_store.CATEGORIES), key=f"{prefix}-category")
        activity_date = c2.date_input(
            "活动日期",
            value=date.today() + timedelta(days=7),
            min_value=date.today(),
            key=f"{prefix}-date",
        )
        start_time = c3.time_input("开始时间", value=dtime(19, 0), key=f"{prefix}-time")
        location = st.text_input(
            "活动地点", placeholder="例如：金明校区 · 东体育馆", key=f"{prefix}-location"
        )
        c4, c5 = st.columns(2)
        capacity = c4.number_input(
            "人数上限", min_value=1, max_value=5000, value=60, step=10, key=f"{prefix}-capacity"
        )
        tags = c5.text_input(
            "活动标签（可选，逗号分隔）", placeholder="例如：友谊赛, 可盖章", key=f"{prefix}-tags"
        )
        c6, c7 = st.columns(2)
        deadline_date = c6.date_input(
            "报名截止日期",
            value=date.today() + timedelta(days=5),
            min_value=date.today(),
            key=f"{prefix}-deadline-date",
        )
        deadline_time = c7.time_input(
            "报名截止时间", value=dtime(18, 0), key=f"{prefix}-deadline-time"
        )
        detail = st.text_area(
            "活动简介",
            placeholder="介绍一下活动内容、参与方式和注意事项……",
            height=96,
            key=f"{prefix}-detail",
        )
        submitted = st.form_submit_button("发布活动", use_container_width=True)
        if submitted:
            title_clean = title.strip()
            location_clean = location.strip()
            start_at = datetime.combine(activity_date, start_time)
            deadline_at = datetime.combine(deadline_date, deadline_time)
            if not title_clean:
                _notify_created("warning", "还没有填写活动名称", "请补充活动名称后再发布。")
            elif not location_clean:
                _notify_created("warning", "还没有填写活动地点", "请补充活动地点后再发布。")
            elif deadline_at > start_at:
                _notify_created("warning", "报名截止时间不合理", "报名截止时间需要早于活动开始时间。")
            else:
                activity_store.add_activity(
                    title_clean,
                    category=category,
                    activity_date=activity_date,
                    start_time=start_time,
                    location=location_clean,
                    capacity=int(capacity),
                    deadline_date=deadline_date,
                    deadline_time=deadline_time,
                    detail=detail,
                    tags=tags,
                )
                _notify_created(
                    "success",
                    "活动创建成功",
                    f"「{title_clean}」已发布，正在打开「我创建的活动」。",
                )
                st.session_state["act-create-token"] = token + 1
                # 发布后直接切到「我创建的活动」页，只多出这一条真实记录。
                st.query_params["view"] = "mine"
                st.query_params["mtab"] = "created"
            st.rerun()
    _render_html(
        f'<div class="create-hint">{ui.icon("info", 13)}自建活动仅保存在你的账号下；如需修改，请先在下方删除后重新创建。</div>'
    )


def _render_created_manager() -> None:
    """删除自建活动（两步确认，避免误删）。"""
    items = activity_store.created_activities()
    if not items:
        return
    lookup = {str(item["id"]): item for item in items}
    ids = list(lookup)
    _render_html('<div style="height:14px"></div>')
    chosen = st.selectbox(
        "选择要删除的自建活动",
        ids,
        format_func=lambda aid: f'{lookup[aid].get("title", "活动")}（{lookup[aid].get("date", "")}）',
        key="act-created-pick",
    )
    confirm = st.checkbox("我确认删除这场自建活动（不可恢复）", key="act-created-del-confirm")
    if st.button("删除活动", disabled=not confirm, use_container_width=True, key="act-created-del"):
        target = lookup.get(chosen) or {}
        activity_store.delete_activity(chosen)
        st.session_state.pop("act-created-pick", None)
        st.session_state.pop("act-created-del-confirm", None)
        _notify_created("info", "活动已删除", f"「{target.get('title', '活动')}」已从我的活动中移除。")
        st.rerun()


# --------------------------------------------------------------------------- #
# 活动任务看板
# --------------------------------------------------------------------------- #
_CHK_PREFIX = "act-task-chk-"


def _chk_key(task_id: str, group: str = "") -> str:
    """任务复选框的组件 key。

    同一条任务可能同时出现在「今日待办」和「近期任务」两个面板里，
    key 必须按面板分组，否则 Streamlit 会抛 DuplicateElementKey。
    """
    prefix = f"{_CHK_PREFIX}{group}-" if group else _CHK_PREFIX
    return prefix + str(task_id)


def _board_flash() -> str:
    """显示并清空一次任务操作的结果提示。"""
    flash = st.session_state.pop("act_task_flash", None)
    if not flash:
        return ""
    tone, title, text = flash
    return _banner(tone, title, text)


def _notify(tone: str, title: str, text: str) -> None:
    st.session_state["act_task_flash"] = (tone, title, text)


def _sync_task_widgets(items: list[dict], group: str) -> None:
    """任务状态在别处被修改时，先同步复选框控件，避免反向覆盖。"""
    seen = st.session_state.get("act_task_seen")
    if not isinstance(seen, dict):
        return
    for item in items:
        key = _chk_key(item["id"], group)
        if key not in st.session_state:
            continue
        if item["id"] in seen and bool(seen[item["id"]]) != bool(item.get("done")):
            st.session_state[key] = bool(item.get("done"))


def _is_overdue(item: dict) -> bool:
    if item.get("done"):
        return False
    deadline = task_store._parse_deadline(item)
    return deadline < datetime.now()


def _task_meta_html(item: dict) -> str:
    progress = int(item.get("progress") or 0)
    if item.get("done"):
        tags = '<span class="tag green">已完成</span>'
    else:
        tone = task_store.PRIORITY_TONES.get(item.get("priority", "中"), "blue")
        tags = f'<span class="tag {tone}">{ui.e(item["priority"])}优先级</span>'
        if _is_overdue(item):
            tags += '<span class="tag rose">已逾期</span>'
    tags += f'<span class="tag gray">{ui.e(item.get("category", "其他"))}</span>'

    lines = f'<span class="meta-line">{ui.icon("clock", 10)}{ui.e(task_store.deadline_label(item))}</span>'
    activity = task_store.linked_activity(str(item.get("link_id") or ""))
    if activity:
        lines += (
            f'<span class="meta-line">{ui.icon("compass", 10)}'
            f'{ui.e(activity["title"])} · {ui.e(activity["location"])}</span>'
        )
    elif item.get("note"):
        lines += f'<span class="meta-line">{ui.icon("info", 10)}{ui.e(item["note"])}</span>'
    progress_html = (
        f'<span class="task-progress">{ui.progress_bar(progress, "blue")}<b>{progress}%</b></span>'
    )
    return f'<div class="task-meta">{tags}{lines}{progress_html}</div>'


def _render_task_rows(items: list[dict], group: str) -> bool:
    _sync_task_widgets(items, group)
    changed = False
    seen: dict[str, bool] = {}
    rendered: set[str] = set()
    for item in items:
        task_id = str(item["id"])
        if task_id in rendered:
            # 防御历史脏数据里的重复 id：同一面板内只渲染一次
            continue
        rendered.add(task_id)
        key = _chk_key(task_id, group)
        if key not in st.session_state:
            st.session_state[key] = bool(item.get("done"))
        left, right = st.columns([0.64, 0.36], gap="small")
        with left:
            checked = st.checkbox(item["title"], key=key)
        with right:
            _render_html(_task_meta_html(item), unsafe_allow_html=True)
        seen[task_id] = bool(item.get("done"))
        if bool(checked) != bool(item.get("done")):
            task_store.toggle_done(task_id)
            seen[task_id] = bool(checked)
            changed = True
    # 两个面板都会执行到这里：合并同步状态，而不是互相覆盖
    merged = dict(st.session_state.get("act_task_seen") or {})
    merged.update(seen)
    st.session_state["act_task_seen"] = merged
    return changed


def _my_task_pool() -> list[dict]:
    """当前账号「自己的」活动任务。

    系统种子任务只有在关联活动是本人已报名或本人创建时才显示；
    本人手动新增的任务始终显示。这样没报名过的活动不会凭空出现任务，
    新建活动也不会自动多出一批任务，统计只反映用户真实选择。
    """
    own_ids = set(registrations())
    own_ids.update(str(item.get("id")) for item in activity_store.created_activities())
    return [
        item
        for item in task_store.tasks()
        if item.get("source") != "seed" or str(item.get("link_id") or "") in own_ids
    ]


def _render_today_panel(pool: list[dict]) -> None:
    tstats = task_store.stats(pool)
    items = tstats["due_today"]
    with st.container(key="task-today"):
        _render_html(
            '<div class="panel-head"><div>'
            f'<div class="panel-title"><span class="panel-icon">{ui.icon("sun", 17)}</span>今日待办</div>'
            f'<div class="panel-sub">{_date_label()} · {len(items)} 项待处理</div>'
            "</div>"
            f'<span class="panel-link">{ui.icon("alert-circle", 12)}逾期 / 今日截止会置顶提醒</span>'
            "</div>",
            unsafe_allow_html=True,
        )
        if items:
            if _render_task_rows(items, "today"):
                st.rerun()
        else:
            _render_html(
                ui.empty_state(
                    title="今天没有截止的任务",
                    desc="本周的报名与备赛任务都在「近期任务」里，抓紧安排起来。",
                    icon_name="circle-check",
                ),
                unsafe_allow_html=True,
            )
        _render_html(
            f'<div class="data-note" style="margin-top:12px">{ui.icon("info", 13)}勾选即完成（进度自动记为 100%）；任务数据实时计算截止与逾期状态。</div>',
            unsafe_allow_html=True,
        )


def _upcoming_items(pool: list[dict], days: int = 14) -> list[dict]:
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    horizon = now + timedelta(days=days)
    items = []
    for item in pool:
        if item.get("done"):
            continue
        deadline = task_store._parse_deadline(item)
        if deadline.date() == today.date():
            continue  # 今日截止的任务已在「今日待办」展示，避免重复
        if deadline < now or deadline <= horizon:  # 逾期 + 未来 14 天
            items.append(item)
    return items


def _render_soon_panel(pool: list[dict]) -> None:
    items = _upcoming_items(pool)
    done_total = task_store.stats(pool)
    with st.container(key="task-soon"):
        _render_html(
            '<div class="panel-head"><div>'
            f'<div class="panel-title"><span class="panel-icon">{ui.icon("calendar", 17)}</span>近期任务</div>'
            f'<div class="panel-sub">未来 14 天 {len(items)} 项 · 全部任务 {done_total["done"]} / {done_total["total"]} 已完成</div>'
            "</div></div>",
            unsafe_allow_html=True,
        )
        if items:
            if _render_task_rows(items, "soon"):
                st.rerun()
        else:
            _render_html(
                ui.empty_state(
                    title="近期没有待办任务",
                    desc="点击下方「新增任务」，把下一场活动的报名与准备计划加进来。",
                    icon_name="compass",
                ),
                unsafe_allow_html=True,
            )


def _task_form_fields(defaults: dict) -> dict:
    """新增 / 修改共用的表单控件，返回提交后的字段值。"""
    c1, c2 = st.columns(2)
    title = st.text_input("任务名称", value=defaults.get("title", ""), placeholder="例如：报名校园歌手大赛")
    category = c1.selectbox(
        "分类", list(task_store.TASK_CATEGORIES),
        index=list(task_store.TASK_CATEGORIES).index(defaults.get("category", "其他"))
        if defaults.get("category", "其他") in task_store.TASK_CATEGORIES else len(task_store.TASK_CATEGORIES) - 1,
    )
    priority = c2.selectbox(
        "优先级", list(task_store.PRIORITIES),
        index=list(task_store.PRIORITIES).index(defaults.get("priority", "中"))
        if defaults.get("priority", "中") in task_store.PRIORITIES else 1,
    )
    default_raw = defaults.get("deadline")
    if isinstance(default_raw, datetime):
        default_dt = default_raw
    elif isinstance(default_raw, str):
        try:
            default_dt = datetime.strptime(default_raw, "%Y-%m-%d %H:%M")
        except ValueError:
            default_dt = datetime.now() + timedelta(days=1)
    else:
        default_dt = datetime.now() + timedelta(days=1)
    c3, c4 = st.columns(2)
    d = c3.date_input("截止日期", value=default_dt.date())
    t = c4.time_input("截止时间", value=default_dt.time().replace(second=0, microsecond=0))
    progress = st.slider("完成进度", 0, 100, int(defaults.get("progress") or 0))
    note = st.text_input("备注（可选）", value=defaults.get("note", ""))
    done = st.checkbox("标记为已完成", value=bool(defaults.get("done")))
    return {
        "title": title,
        "category": category,
        "priority": priority,
        "deadline": datetime.combine(d, t),
        "progress": progress,
        "note": note,
        "done": done,
    }


def _render_manage_panel(pool: list[dict]) -> None:
    all_items = pool

    def _label(item: dict) -> str:
        dt = task_store._parse_deadline(item)
        state = "已完成" if item.get("done") else "进行中"
        return f"{item['title']}（{dt.month}月{dt.day}日 {dt.strftime('%H:%M')} · {state}）"

    with st.container(key="task-manage"):
        _render_html(
            '<div class="panel-head"><div>'
            f'<div class="panel-title"><span class="panel-icon">{ui.icon("settings", 17)}</span>任务管理</div>'
            '<div class="panel-sub">新增、修改、删除你的活动任务，操作立即保存</div>'
            "</div></div>",
            unsafe_allow_html=True,
        )
        add_tab, edit_tab, del_tab = st.tabs(["新增任务", "修改任务", "删除任务"])

        with add_tab:
            with st.form("act-task-add", clear_on_submit=True):
                fields = _task_form_fields({})
                if st.form_submit_button("新增任务", use_container_width=True):
                    if not str(fields["title"]).strip():
                        _notify("warning", "还没有填写任务名称", "任务名称为必填项，请补充后再提交。")
                    else:
                        task_store.add_task(
                            str(fields["title"]),
                            category=fields["category"],
                            deadline=fields["deadline"],
                            priority=fields["priority"],
                            progress=fields["progress"],
                            note=fields["note"],
                        )
                        _notify("success", "新增任务成功", f"「{fields['title']}」已加入你的活动任务看板。")
                    st.rerun()

        with edit_tab:
            if not all_items:
                _render_html(
                    '<div class="data-note">当前没有可修改的任务，先在上方新增一个吧。</div>',
                    unsafe_allow_html=True,
                )
            else:
                ids = [str(item["id"]) for item in all_items]
                chosen = st.selectbox("选择要修改的任务", ids, format_func=lambda tid: _label(task_store.get_task(tid) or {}), key="act-edit-pick")
                current = task_store.get_task(chosen) or {}
                with st.form("act-task-edit"):
                    fields = _task_form_fields(current)
                    if st.form_submit_button("保存修改", use_container_width=True):
                        if not str(fields["title"]).strip():
                            _notify("warning", "任务名称不能为空", "请填写任务名称后再保存。")
                        else:
                            task_store.update_task(
                                chosen,
                                title=fields["title"],
                                category=fields["category"],
                                priority=fields["priority"],
                                deadline=fields["deadline"],
                                progress=fields["progress"],
                                note=fields["note"],
                                done=fields["done"],
                            )
                            _notify("success", "修改已保存", f"「{fields['title']}」的任务信息已更新。")
                        st.rerun()

        with del_tab:
            if not all_items:
                _render_html('<div class="data-note">当前没有可删除的任务。</div>', unsafe_allow_html=True)
            else:
                ids = [str(item["id"]) for item in all_items]
                chosen = st.selectbox("选择要删除的任务", ids, format_func=lambda tid: _label(task_store.get_task(tid) or {}), key="act-del-pick")
                confirm = st.checkbox("我确认要删除这个任务（不可恢复）", key="act-del-confirm")
                if st.button("删除任务", disabled=not confirm, use_container_width=True):
                    target = task_store.get_task(chosen)
                    task_store.delete_task(chosen)
                    _notify("info", "任务已删除", f"「{target['title'] if target else '任务'}」已从看板移除。")
                    st.rerun()


def _prio_bars_html(counts: dict[str, int]) -> str:
    max_count = max(counts.values(), default=0) or 1
    rows = []
    for level in task_store.PRIORITIES:
        count = counts.get(level, 0)
        width = int(count / max_count * 100)
        tone = task_store.PRIORITY_TONES[level]
        rows.append(
            f'<div class="prio-row"><span class="prio-name">{level}</span>'
            f'<div class="prio-bar"><span class="{tone}" style="width:{max(width, 4 if count else 0)}%"></span></div>'
            f"<b>{count}</b></div>"
        )
    return "".join(rows)


def _deadline_chart_svg(buckets: list[dict]) -> str:
    counts = [int(b["count"]) for b in buckets]
    if not any(counts):
        return (
            '<div class="chart-empty">'
            + ui.icon("check", 15)
            + "未来 7 天没有截止任务，节奏很轻松"
            + "</div>"
        )
    width, height = 340, 168
    pad_top, pad_bottom = 24, 30
    chart_h = height - pad_top - pad_bottom
    slot = (width - 20) / len(buckets)
    bar_w = 20
    max_count = max(counts)
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="未来 7 天截止任务分布" style="width:100%;height:auto;display:block">',
        '<defs><linearGradient id="taskbar" x1="0" y1="0" x2="0" y2="1">'
        '<stop stop-color="#2563EB"/><stop offset="1" stop-color="#60A5FA"/></linearGradient></defs>',
        # 网格线
        f'<line x1="8" y1="{pad_top}" x2="{width - 8}" y2="{pad_top}" stroke="#EEF2F8" stroke-width="1"/>',
        f'<line x1="8" y1="{pad_top + chart_h}" x2="{width - 8}" y2="{pad_top + chart_h}" stroke="#DDE6F2" stroke-width="1"/>',
    ]
    for index, bucket in enumerate(buckets):
        count = counts[index]
        cx = 10 + slot * index + slot / 2
        bar_h = (count / max_count) * (chart_h - 10) if count else 0
        y = pad_top + chart_h - bar_h
        color = "#F5B942" if index == 0 else "url(#taskbar)"
        if count:
            parts.append(
                f'<rect x="{cx - bar_w / 2:.1f}" y="{y:.1f}" width="{bar_w}" height="{bar_h:.1f}" rx="5" fill="{color}"/>'
            )
            parts.append(
                f'<text x="{cx:.1f}" y="{y - 6:.1f}" text-anchor="middle" font-size="10" font-weight="700" fill="#334155">{count}</text>'
            )
        else:
            parts.append(
                f'<circle cx="{cx:.1f}" cy="{pad_top + chart_h - 4:.1f}" r="2.5" fill="#D6DFEC"/>'
            )
        label_color = "#B7790B" if index == 0 else "#94A3B8"
        parts.append(
            f'<text x="{cx:.1f}" y="{pad_top + chart_h + 14}" text-anchor="middle" font-size="9.5" font-weight="700" fill="{label_color}">{ui.e(bucket["label"])}</text>'
        )
        parts.append(
            f'<text x="{cx:.1f}" y="{pad_top + chart_h + 26}" text-anchor="middle" font-size="8.5" fill="#B6C2D4">{bucket["date"].month}/{bucket["date"].day}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def _render_visual_panel(pool: list[dict]) -> None:
    tstats = task_store.stats(pool)
    with st.container(key="task-visual"):
        _render_html(
            '<div class="panel-head"><div>'
            f'<div class="panel-title"><span class="panel-icon">{ui.icon("chart", 17)}</span>任务可视化</div>'
            '<div class="panel-sub">完成率、优先级分布与截止节奏一目了然</div>'
            "</div></div>",
            unsafe_allow_html=True,
        )
        _render_html(
            '<div class="ring-wrap">'
            + ui.ring(tstats["completion"], "整体完成率", 128)
            + '<div class="ring-side">'
            + f'<div class="ring-line">全部任务 <b>{tstats["total"]}</b> 项 · 已完成 <b>{tstats["done"]}</b> 项</div>'
            + f'<div class="ring-line">高优先级未完成 <b>{len(tstats["high_open"])}</b> 项</div>'
            + f'<div class="ring-line">已逾期 <b>{len(tstats["overdue"])}</b> 项 · 今日截止 <b>{len(tstats["due_today"])}</b> 项</div>'
            + "</div></div>",
            unsafe_allow_html=True,
        )
        _render_html(
            '<div class="chart-divider"></div>'
            '<div class="chart-title">' + ui.icon("filter", 14) + "优先级分布（未完成）</div>"
            + _prio_bars_html(tstats["priority_counts"])
            + '<div class="chart-divider"></div>'
            '<div class="chart-title">' + ui.icon("calendar", 14) + "未来 7 天截止任务</div>"
            + _deadline_chart_svg(tstats["buckets"])
            + f'<div class="data-note" style="margin-top:14px">{ui.icon("info", 13)}图表基于当前任务列表实时统计；今天截止的任务以金色高亮。</div>',
            unsafe_allow_html=True,
        )


def _render_task_board() -> None:
    # 先按当前账号过滤：没报名的活动不会把自己的种子任务算进来。
    pool = _my_task_pool()
    _render_html(
        '<div class="section-space"></div>'
        + ui.section_header(
            title="活动任务看板",
            eyebrow="TASK BOARD · 我的任务",
            subtitle="只汇总你报名 / 创建的活动任务，以及你手动新增的任务",
            link_label="查看个人事务中心",
            link_href="?page=center",
            icon_name="circle-check",
        )
        + _board_flash(),
        unsafe_allow_html=True,
    )
    tstats = task_store.stats(pool)
    _render_html(
        '<div class="grid-4" style="margin-bottom:18px">'
        + ui.stat_card("今日待办", str(len(tstats["due_today"])), "项", "sun", "gold", foot="今天 24:00 前需处理")
        + ui.stat_card("7 天内截止", str(len(tstats["week_due"])), "项", "calendar", "blue", foot="含今日与已逾期任务")
        + ui.stat_card("高优先级未完成", str(len(tstats["high_open"])), "项", "flame", "rose", foot="建议优先安排")
        + ui.stat_card("整体完成率", str(tstats["completion"]), "%", "trending-up", "teal", foot=f'已完成 {tstats["done"]} / {tstats["total"]} 项')
        + "</div>",
        unsafe_allow_html=True,
    )
    left, right = st.columns([1.3, 0.7], gap="medium")
    with left:
        _render_today_panel(pool)
        _render_html('<div style="height:14px"></div>', unsafe_allow_html=True)
        _render_soon_panel(pool)
        _render_html('<div style="height:14px"></div>', unsafe_allow_html=True)
        _render_manage_panel(pool)
    with right:
        _render_visual_panel(pool)
    _render_html(
        f'<div class="data-note" style="margin-top:14px">{ui.icon("database", 13)}统计只包含与本人报名 / 自建活动相关的任务和手动新增任务；没报名过的官方活动不会出现在这里，新建活动也不会自动增加任务。</div>',
        unsafe_allow_html=True,
    )


def _date_label() -> str:
    now = datetime.now()
    weekday = "一二三四五六日"[now.weekday()]
    return f"{now.month} 月 {now.day} 日 · 周{weekday}"


def _official_tips() -> str:
    tips = (
        '<div class="grid-3" style="margin-top:20px">'
        '<div class="card tip-card"><div class="panel-title"><span class="panel-icon">'
        + ui.icon("bell", 17)
        + "</span>签到与提醒</div><p>报名成功后，活动开始前 24 小时河小智会推送提醒；现场扫码签到，未签到将影响第二课堂学分认定。</p></div>"
        '<div class="card tip-card"><div class="panel-title"><span class="panel-icon">'
        + ui.icon("award", 17)
        + "</span>第二课堂学分</div><p>标注「第二课堂」的活动完成后会自动计入成长档案，可在个人成长档案中查看记录。</p></div>"
        '<div class="card tip-card"><div class="panel-title"><span class="panel-icon">'
        + ui.icon("refresh", 17)
        + "</span>退改说明</div><p>报名后在活动卡片上点「取消报名」即可退出；无故缺席 2 次将暂停一周报名权限，请合理安排时间。</p></div>"
        "</div>"
    )
    growth_cta = (
        '<a class="growth-banner" href="?page=growth" style="margin-top:18px">'
        f'<span class="growth-icon">{ui.icon("trending-up", 21)}</span>'
        '<span class="growth-copy"><b>每一场活动，都会留在你的成长档案里</b>'
        '<span>参与记录、志愿时长与第二课堂学分自动沉淀，让成长被看见</span></span>'
        f'<span class="growth-cta">查看我的成长档案 {ui.icon("arrow-right", 13)}</span>'
        "</a>"
    )
    return tips + growth_cta


def _render_official(flash_html: str) -> None:
    """官方活动：浏览分类、查看详情、报名 / 取消报名。"""
    categories = _categories()
    selected_cat = ui.qp("cat").strip()
    if selected_cat not in categories:
        selected_cat = "全部"
    focus_id = ui.qp("id").strip()

    filtered = [
        activity for activity in data.ACTIVITIES if selected_cat == "全部" or activity["category"] == selected_cat
    ]
    if focus_id:
        filtered.sort(key=lambda activity: 0 if activity["id"] == focus_id else 1)

    reg_count = len(registrations())
    total_people = sum(activity["participants"] for activity in data.ACTIVITIES)
    hero_meta = (
        f'<span>{ui.icon("calendar", 13)}本周 {len(data.ACTIVITIES)} 场活动</span>'
        f'<span>{ui.icon("users", 13)}{total_people} 人次已报名</span>'
        f'<span>{ui.icon("filter", 13)}{len(categories)} 个活动分类</span>'
        f'<span>{ui.icon("check", 13)}我已报名 {reg_count} 场</span>'
    )
    chips = [
        _chip("全部活动", selected_cat == "全部", "?page=activities&view=official", "layout-grid"),
    ]
    for category in categories:
        chips.append(
            _chip(
                category,
                selected_cat == category,
                ui.page_url("activities", view="official", cat=category),
                _CATEGORY_ICONS.get(category, "compass"),
            )
        )

    if not filtered:
        _render_html(
            ui.page_hero(
                eyebrow="CAMPUS NOW · 校园活动",
                title="去现场，才算真的上过大学",
                subtitle="社团、讲座、音乐节与夜跑，河大的新鲜事都在这里。选一场喜欢的，和同频的人一起出发。",
                icon_name="compass",
                tone="gold",
            )
            + flash_html,
            unsafe_allow_html=True,
        )
        _render_html(
            ui.empty_state(
                title="这个分类下暂时没有活动",
                desc="换个分类看看，或者回到全部活动列表。",
                icon_name="compass",
                action_label="查看全部活动",
                action_href="?page=activities&view=official",
            )
            + _official_tips(),
            unsafe_allow_html=True,
        )
        return

    _render_html(
        ui.page_hero(
            eyebrow="CAMPUS NOW · 校园活动",
            title="去现场，才算真的上过大学",
            subtitle="社团、讲座、音乐节与夜跑，河大的新鲜事都在这里。选一场喜欢的，和同频的人一起出发。",
            icon_name="compass",
            tone="gold",
            meta=hero_meta,
        )
        + flash_html
        + f'<div class="activities-toolbar"><div class="chip-row">{"".join(chips)}</div>'
        + f'<div class="activities-count">{ui.icon("filter", 13)}共 <b>{len(filtered)}</b> 场活动 · 已报名 <b>{reg_count}</b> 场</div></div>',
        unsafe_allow_html=True,
    )
    # 每张活动卡单独成块：封面以内联 base64 提供，分段渲染可控制单个富文本块体积。
    for activity in filtered:
        _render_html(
            _detail_card(activity, selected_cat, activity["id"] == focus_id),
            unsafe_allow_html=True,
        )
    _render_html(_official_tips(), unsafe_allow_html=True)


_MINE_TABS = ("joined", "create", "created", "tasks")


def _render_mine(flash_html: str) -> None:
    """我的活动：四个功能各自独立成页，用 mtab 切换，默认「我报名的活动」。"""
    tab = ui.qp("mtab").strip()
    if tab not in _MINE_TABS:
        tab = "joined"

    _render_html(_mine_tabs(tab), unsafe_allow_html=True)
    if flash_html:
        _render_html(flash_html, unsafe_allow_html=True)

    if tab == "create":
        _render_create_form()
    elif tab == "created":
        _render_html(_created_markup(), unsafe_allow_html=True)
        _render_created_manager()
    elif tab == "tasks":
        # 活动任务看板：今日待办 / 近期任务 / 优先级 / 进度 / 增删改 / 可视化。
        _render_task_board()
    else:
        _render_html(_joined_markup(), unsafe_allow_html=True)


def render() -> None:
    _render_html(_STYLE, unsafe_allow_html=True)

    view = ui.qp("view").strip()
    if view not in ("official", "mine"):
        view = "official"

    flash_html = _handle_join() + _created_flash()
    _render_html(_subnav(view), unsafe_allow_html=True)
    if view == "mine":
        _render_mine(flash_html)
    else:
        _render_official(flash_html)
