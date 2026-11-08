# -*- coding: utf-8 -*-
"""河小智 · 办事流程导航页。

页面由 app.py 调用 render()，不包含 set_page_config / topbar / footer。

页面结构：
1. AI 办事助手：输入办事需求 → AI 识别需求 → 生成办理步骤、所需材料、
   注意事项，并自动生成待办清单（支持原生复选框勾选完成）。
2. 流程库：``?q=`` 关键词搜索、``?cat=`` 分类筛选，两者可组合且互相保留。
3. 流程数据来自 ``core.data.PROCESSES``（整理自河南大学官网公开信息，
   每条标注依据来源）；识别与计划生成逻辑在 ``core.services_ai``。
"""

from __future__ import annotations

import hashlib

import streamlit as st

from core import data, services_ai, ui

_CATEGORY_TONE = {
    "教务学习": "blue",
    "奖助资助": "gold",
    "生活服务": "teal",
    "学生事务": "teal",
    "图书服务": "gold",
    "医疗健康": "rose",
}

# 待办清单面板的局部样式（原生复选框 + 进度行），与全站视觉保持一致。
_TODO_CSS = """
<style>
.svc-todo-panel [data-testid="stVerticalBlock"]{gap:.35rem;}
.svc-todo-panel [data-testid="stCheckbox"]{margin:0;}
.svc-todo-panel [data-testid="stCheckbox"] label{gap:10px;align-items:flex-start;padding:4px 0;}
.svc-todo-panel [data-testid="stCheckbox"] label p{
  font-size:11.5px;line-height:1.65;color:var(--ink-soft);margin:0;}
.svc-todo-panel [data-testid="stCheckbox"]:has(input:checked) label p{
  color:var(--muted);text-decoration:line-through;}
.svc-todo-panel [data-testid="stCheckbox"] [data-baseweb="checkbox"] div{border-radius:7px;}
</style>
"""


def _render(markup: str) -> None:
    """优先走 core.ui.render_html（站内链接在当前标签页打开），旧版本回退 st.markdown。"""
    render_html = getattr(ui, "render_html", None)
    if callable(render_html):
        render_html(markup)
    else:
        st.markdown(markup, unsafe_allow_html=True)


def _resolve_category(raw: str) -> str:
    """容错解析分类：精确匹配优先，其次兼容「图书」这类前缀写法。"""
    value = (raw or "").strip()
    if value in data.PROCESS_CATEGORIES:
        return value
    if value:
        for name in data.PROCESS_CATEGORIES:
            if name != "全部" and value in name:
                return name
        for name in data.PROCESS_CATEGORIES:
            if name != "全部" and name in value:
                return name
    return "全部"


def _filters() -> tuple[str, str]:
    query = ui.qp("q").strip()
    category = _resolve_category(ui.qp("cat"))
    return query, category


def _haystack(item: dict) -> str:
    parts = [
        item.get("title", ""),
        item.get("category", ""),
        item.get("department", ""),
        item.get("summary", ""),
        item.get("location", ""),
        item.get("duration", ""),
        "线上可办" if item.get("online") else "线下办理",
        " ".join(item.get("keywords") or []),
        " ".join(item.get("materials") or []),
        " ".join(item.get("steps") or []),
    ]
    return " ".join(str(part) for part in parts).lower()


def _match_score(item: dict, needle: str) -> int:
    """相关度排序：标题命中优先，其次分类 / 部门，最后材料与步骤。"""
    score = 0
    if needle in item.get("title", "").lower():
        score += 8
    if needle in item.get("category", "").lower():
        score += 3
    if needle in item.get("department", "").lower():
        score += 3
    if needle in item.get("summary", "").lower():
        score += 2
    if needle in item.get("location", "").lower():
        score += 1
    if needle in " ".join(item.get("keywords") or []).lower():
        score += 1
    if needle in " ".join(item.get("materials") or []).lower():
        score += 1
    if needle in " ".join(item.get("steps") or []).lower():
        score += 1
    return score


def _filtered(query: str, category: str) -> list[dict]:
    items = list(data.PROCESSES)
    if category and category != "全部":
        items = [item for item in items if item.get("category") == category]
    needle = query.lower()
    if needle:
        ranked = [
            (item, _match_score(item, needle))
            for item in items
            if needle in _haystack(item)
        ]
        ranked.sort(key=lambda pair: pair[1], reverse=True)
        items = [item for item, _score in ranked]
    return items


def _process_card(item: dict, index: int) -> str:
    category = item.get("category", "")
    tone = _CATEGORY_TONE.get(category, "blue")
    online = bool(item.get("online"))
    online_text = "线上可办" if online else "线下办理"
    online_style = (
        "background:var(--teal-soft);color:#0F9488"
        if online
        else "background:#F3F6FA;color:var(--muted)"
    )
    hot = (
        f'<span class="tag gold">{ui.icon("flame", 10)}热门</span>'
        if item.get("hot")
        else ""
    )

    materials = "".join(
        f"<li>{ui.e(material)}</li>" for material in (item.get("materials") or [])
    )
    steps = "".join(
        f'<div class="process-step"><span class="step-num">{number}</span><span>{ui.e(step)}</span></div>'
        for number, step in enumerate(item.get("steps") or [], 1)
    )
    notice = item.get("notice", "")
    notice_html = (
        f'<div class="notice-box">{ui.icon("alert-circle", 12)}<span>{ui.e(notice)}</span></div>'
        if notice
        else ""
    )
    source = item.get("source", "")
    source_html = (
        f'<div class="detail-label">依据来源</div>'
        f'<div style="font-size:10px;line-height:1.7;color:var(--muted);padding-left:2px">'
        f'{ui.icon("bookmark", 11)} {ui.e(source)}</div>'
        if source
        else ""
    )
    ask_href = ui.page_url("services", need=item.get("title") or "")

    return f"""
<article class="process-card" id="process-{ui.e(item.get('id', index))}">
  <div class="process-head">
    <div class="process-icon">{ui.icon(item.get('icon', 'route'), 21)}</div>
    <div style="min-width:0;flex:1">
      <h3 class="process-title">{ui.e(item.get('title', ''))}</h3>
      <div class="process-dept">{ui.icon('users', 10)}{ui.e(item.get('department', ''))}</div>
    </div>
    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:5px;flex:0 0 auto">
      <span class="tag {tone}">{ui.e(category)}</span>
      {hot}
    </div>
  </div>
  <p class="process-desc">{ui.e(item.get('summary', ''))}</p>
  <div class="process-meta">
    <span>{ui.icon('clock', 11)}{ui.e(item.get('duration', ''))}</span>
    <span>{ui.icon('map-pin', 11)}{ui.e(item.get('location', ''))}</span>
    <span style="{online_style}">{ui.icon('globe' if online else 'map-pin', 11)}{online_text}</span>
  </div>
  <details class="card-details">
    <summary>查看材料清单与办理步骤</summary>
    <div class="detail-block">
      <div class="detail-label">所需材料</div>
      <ul class="detail-list">{materials}</ul>
      <div class="detail-label">办理步骤</div>
      <div class="process-steps">{steps}</div>
      {notice_html}
      {source_html}
    </div>
  </details>
  <a class="section-link" style="margin-top:10px;font-size:10.5px" href="{ui.e(ask_href)}">
    {ui.icon('sparkles', 12)}让 AI 帮我规划这件事
  </a>
</article>
"""


def _toolbar(query: str, category: str) -> str:
    chips = []
    for name in data.PROCESS_CATEGORIES:
        active = "active" if name == category else ""
        href = ui.page_url(
            "services",
            cat=None if name == "全部" else name,
            q=query or None,
        )
        chips.append(f'<a class="chip {active}" href="{ui.e(href)}">{ui.e(name)}</a>')

    return f"""
<section class="panel" style="padding:17px 18px;margin-bottom:18px">
  <div class="panel-head" style="margin-bottom:12px;flex-wrap:wrap;gap:8px">
    <div>
      <div class="panel-title"><span class="panel-icon">{ui.icon('filter', 17)}</span>搜索与筛选</div>
      <div class="panel-sub">输入关键词，或按分类快速定位办事入口</div>
    </div>
    <span class="pill">{ui.icon('layout-grid', 12)}共 {len(data.PROCESSES)} 项常用流程</span>
  </div>
  <form class="search-form" method="get" action="" role="search">
    <input type="hidden" name="page" value="services"/>
    <input type="hidden" name="cat" value="{ui.e(category)}"/>
    <span class="search-ico">{ui.icon('search', 16)}</span>
    <input name="q" type="search" value="{ui.e(query)}" placeholder="搜索流程：校园卡、成绩单、医保、转专业……" autocomplete="off" aria-label="搜索办事流程"/>
    <button type="submit">搜索</button>
  </form>
  <div class="chip-row" style="margin-top:12px">{"".join(chips)}</div>
</section>
"""


def _results_header(query: str, category: str, items: list[dict]) -> str:
    conditions = []
    if category != "全部":
        conditions.append(f"分类「{category}」")
    if query:
        conditions.append(f"关键词「{query}」")

    if conditions:
        subtitle = f"共找到 <b>{len(items)}</b> 项流程 · " + " · ".join(ui.e(part) for part in conditions)
        reset = f'<a class="section-link" href="?page=services">{ui.e("重置筛选")}{ui.icon("refresh", 15)}</a>'
    else:
        subtitle = f"共找到 <b>{len(items)}</b> 项流程 · 内容整理自河南大学官网与各部门公开办事指南"
        reset = ""

    return f"""
<div class="section-head" style="flex-wrap:wrap;gap:8px">
  <div>
    <div class="section-eyebrow">{ui.icon('route', 13)}PROCESS LIBRARY</div>
    <h2 class="section-title">办事流程一览</h2>
    <p class="section-sub">{subtitle}</p>
  </div>
  {reset}
</div>
"""


def _empty_state(query: str, category: str) -> str:
    if query:
        desc = f"没有找到与「{query}」相关的流程，换个关键词试试，或回到「全部」分类浏览。"
    else:
        desc = f"「{category}」分类下暂时没有可展示的流程，可以切换到其他分类看看。"
    return ui.empty_state(
        title="没有找到匹配的流程",
        desc=desc,
        icon_name="search",
        action_label="清空筛选条件",
        action_href="?page=services",
    )


def _ai_panel(need: str) -> str:
    """AI 办事助手输入区 + 示例需求。"""
    example_chips = "".join(
        f'<a class="chip" href="{ui.e(ui.page_url("services", need=example))}">{ui.e(example)}</a>'
        for example in services_ai.quick_examples()
    )
    return f"""
<section class="panel" style="padding:19px 20px;margin-bottom:18px;border:1px solid #D9E6FB;background:linear-gradient(180deg,#FBFDFF,#F6FAFF)">
  <div class="panel-head" style="margin-bottom:12px;flex-wrap:wrap;gap:8px">
    <div>
      <div class="panel-title"><span class="panel-icon">{ui.icon('sparkles', 17)}</span>AI 办事助手 · 说出你的需求</div>
      <div class="panel-sub">用一句话描述要办的事，AI 自动识别需求，生成办理步骤、材料清单与待办</div>
    </div>
    <span class="pill">{ui.icon('cpu', 12)}AI 识别 · 自动出计划</span>
  </div>
  <form class="search-form" method="get" action="" role="search" style="max-width:100%">
    <input type="hidden" name="page" value="services"/>
    <span class="search-ico">{ui.icon('sparkles', 16)}</span>
    <input name="need" type="search" value="{ui.e(need)}" required
      placeholder="例：校园卡丢了 / 生病没法参加考试 / 想转专业 / 医保怎么报销……"
      autocomplete="off" aria-label="输入办事需求"/>
    <button type="submit">AI 识别需求</button>
  </form>
  <div class="chip-row" style="margin-top:11px">{example_chips}</div>
</section>
"""


def _plan_panel(need: str, recognized: dict, plan: dict) -> str:
    """AI 识别结果：办理步骤 / 所需材料 / 注意事项 + 来源。"""
    process = plan["process"]
    tone = _CATEGORY_TONE.get(process.get("category", ""), "blue")
    online = bool(process.get("online"))

    steps = "".join(
        f'<div class="process-step"><span class="step-num">{number}</span><span>{ui.e(step)}</span></div>'
        for number, step in enumerate(process.get("steps") or [], 1)
    )
    materials = "".join(
        f"<li>{ui.e(material)}</li>" for material in (process.get("materials") or [])
    )
    notice = process.get("notice", "")
    notice_html = (
        f'<div class="notice-box" style="margin-top:0">{ui.icon("alert-circle", 12)}<span>{ui.e(notice)}</span></div>'
        if notice
        else ""
    )
    source = process.get("source", "")

    keyword_tags = "".join(
        f'<span class="tag blue">{ui.e(keyword)}</span>' for keyword in recognized.get("keywords") or []
    ) or '<span class="tag blue">语义匹配</span>'
    alternatives = recognized.get("alternatives") or []
    alt_html = ""
    if alternatives:
        alt_links = "".join(
            f'<a class="chip" href="{ui.e(ui.page_url("services", need=alt["title"]))}">{ui.e(alt["title"])}</a>'
            for alt in alternatives
        )
        alt_html = f'<div class="chip-row" style="margin-top:10px"><span style="font-size:10.5px;color:var(--muted)">不是想办这个？试试：</span>{alt_links}</div>'

    confidence = int(round(float(recognized.get("confidence") or 0) * 100))
    return f"""
<section class="panel" style="padding:19px 20px;margin-bottom:18px">
  <div class="panel-head" style="margin-bottom:14px;flex-wrap:wrap;gap:8px">
    <div style="min-width:0">
      <div class="panel-title">
        <span class="panel-icon">{ui.icon('cpu', 17)}</span>
        AI 识别结果：{ui.e(process.get('title', ''))}
      </div>
      <div class="panel-sub">
        需求「{ui.e(need)}」 · {ui.e(process.get('department', ''))} ·
        {ui.e(process.get('duration', ''))} · {ui.icon('globe', 11) if online else ui.icon('map-pin', 11)}
        {'线上可办' if online else '线下办理'}
      </div>
    </div>
    <span class="tag {tone}">{ui.e(process.get('category', ''))}</span>
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px">
    <span class="pill" style="font-size:10px">{ui.icon('sparkles', 11)}识别置信度 {confidence}%</span>
    {keyword_tags}
  </div>
  <div class="grid-3" style="align-items:start">
    <div>
      <div class="detail-label" style="margin-top:0">办理步骤</div>
      <div class="process-steps">{steps}</div>
    </div>
    <div>
      <div class="detail-label" style="margin-top:0">所需材料</div>
      <ul class="detail-list">{materials}</ul>
    </div>
    <div>
      <div class="detail-label" style="margin-top:0">注意事项</div>
      {notice_html}
    </div>
  </div>
  <div style="margin-top:14px;padding-top:11px;border-top:1px dashed var(--border);font-size:10px;line-height:1.7;color:var(--muted)">
    {ui.icon('bookmark', 11)} 依据来源：{ui.e(source)}。内容整理自公开渠道，实际办理请以学校主管部门最新通知为准。
  </div>
  {alt_html}
</section>
"""


def _no_match_panel(need: str, recognized: dict) -> str:
    hint = recognized.get("hint") or "暂时没有匹配到具体流程。"
    alternatives = recognized.get("alternatives") or []
    alt_links = "".join(
        f'<a class="chip" href="{ui.e(ui.page_url("services", need=alt["title"]))}">{ui.e(alt["title"])}</a>'
        for alt in alternatives
    )
    alt_html = f'<div class="chip-row" style="margin-top:10px"><span style="font-size:10.5px;color:var(--muted)">相近的流程：</span>{alt_links}</div>' if alt_links else ""
    return f"""
<section class="panel" style="padding:19px 20px;margin-bottom:18px;border:1px solid #FBEBC7;background:#FFFDF6">
  <div class="panel-title" style="font-size:13.5px"><span class="panel-icon" style="background:#FFF3D6">{ui.icon('info', 16)}</span>AI 暂时没听懂「{ui.e(need)}」</div>
  <div style="font-size:11px;line-height:1.8;color:var(--ink-soft);margin-top:8px">{ui.e(hint)}</div>
  {alt_html}
</section>
"""


def _todo_panel(need: str, plan: dict) -> None:
    """自动生成的待办清单：原生复选框，勾选即完成。"""
    plan_id = hashlib.md5(need.encode("utf-8")).hexdigest()[:8]
    todos = plan["todos"]
    if not todos:
        return

    with st.container(key="svc-todo-panel"):
        st.markdown(
            f"""
<div class="panel" style="padding:19px 20px">
  <div class="panel-head" style="margin-bottom:6px;flex-wrap:wrap;gap:8px">
    <div>
      <div class="panel-title"><span class="panel-icon">{ui.icon('circle-check', 17)}</span>自动生成的待办清单</div>
      <div class="panel-sub">AI 已把「{ui.e(need)}」拆解成下面这些待办，完成一项勾一项</div>
    </div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        done = 0
        for todo in todos:
            key = f"svc-{plan_id}-{todo['id']}"
            checked = bool(st.checkbox(
                f"{todo['label']}",
                key=key,
                value=False,
                help=None,
            ))
            if checked:
                done += 1
        total = len(todos)
        percent = int(round(done * 100 / total)) if total else 0

        if done >= total and total:
            st.markdown(
                f"""
<div class="notice-box" style="background:#EFFDF6;border-color:#C9F0DB;color:#116B3F;margin-top:8px">
  {ui.icon('circle-check', 13)}<span>太棒了，这份待办已全部完成！办理过程中如有变化，请以学校主管部门最新通知为准。</span>
</div>
""",
                unsafe_allow_html=True,
            )

        col_progress, col_reset = st.columns([4, 1])
        with col_progress:
            st.markdown(
                f"""
<div class="todo-progress-row" style="margin-top:6px">
  <span>完成进度</span>
  <span><b>{done}</b> / {total} · {percent}%</span>
</div>
<div class="mini-progress"><span class="teal" style="width:{percent}%"></span></div>
""",
                unsafe_allow_html=True,
            )
        with col_reset:
            if st.button("重置勾选", key=f"svc-reset-{plan_id}", use_container_width=True):
                for todo in todos:
                    st.session_state.pop(f"svc-{plan_id}-{todo['id']}", None)
                st.rerun()


def _tips() -> str:
    items = [
        ("file-text", "blue", "材料一次带齐", "展开卡片可看到完整材料清单，出发前先核对一遍，少跑一趟冤枉路。"),
        ("globe", "teal", "线上优先办理", "标注「线上可办」的流程可在线提交，办理进度随时可查。"),
        ("message", "gold", "不确定就问", "遇到特殊情况，到「智能问答」描述你的场景，河小智会给出下一步。"),
    ]
    cards = []
    for icon_name, tone, title, desc in items:
        cards.append(
            f"""
<section class="panel" style="padding:16px 17px">
  <div class="panel-title" style="font-size:13.5px"><span class="panel-icon" style="width:30px;height:30px">{ui.icon(icon_name, 15)}</span>{ui.e(title)}</div>
  <div style="font-size:10.5px;line-height:1.75;color:var(--muted);margin-top:9px;padding-left:39px">{ui.e(desc)}</div>
</section>
"""
        )
    return "".join(cards)


def render() -> None:
    query, category = _filters()
    items = _filtered(query, category)
    need = ui.qp("need").strip()

    online_count = sum(1 for item in data.PROCESSES if item.get("online"))
    hero = ui.page_hero(
        eyebrow="SERVICE NAVIGATOR · 办事流程",
        title='办事不迷路，<span style="background:linear-gradient(95deg,#8EF7E1,#A9D3FF,#FFD580);-webkit-background-clip:text;background-clip:text;color:transparent">一次就办成</span>',
        subtitle="说出你的需求，AI 识别后自动生成办理步骤、材料清单与待办；也可以按分类浏览全部流程。",
        icon_name="route",
        tone="teal",
        meta=(
            f'<span>{ui.icon("sparkles", 12)}AI 需求识别</span>'
            f'<span>{ui.icon("layout-grid", 12)}{len(data.PROCESSES)} 项真实流程</span>'
            f'<span>{ui.icon("globe", 12)}{online_count} 项支持线上办理</span>'
        ),
    )

    ai_html = _ai_panel(need)
    plan_html = ""
    if need:
        recognized = services_ai.recognize(need)
        if recognized.get("matched"):
            plan = services_ai.build_plan(recognized["process"])
            plan_html = _plan_panel(need, recognized, plan)
        else:
            plan_html = _no_match_panel(need, recognized)
            plan = None
    else:
        plan = None

    if items:
        grid = f'<div class="process-grid">{"".join(_process_card(item, index) for index, item in enumerate(items))}</div>'
    else:
        grid = _empty_state(query, category)

    _render(
        f"""
{hero}
{ai_html}
{plan_html}
{_toolbar(query, category)}
{_results_header(query, category, items)}
{grid}
<div class="grid-3" style="margin-top:18px">{_tips()}</div>
<div class="data-note" style="margin-top:18px">{ui.icon('info', 13)}以上流程均整理自河南大学官网、教务处、校医院、图书馆等部门公开发布的办事指南（依据来源见各卡片与识别结果），实际办理请以学校各主管部门最新通知为准；正式上线后将接入官方业务系统实时状态。</div>
"""
    )

    # 待办清单使用原生复选框（勾选即完成），单独渲染在 HTML 内容之后。
    if need and plan is not None:
        _render(_TODO_CSS)
        _todo_panel(need, plan)
