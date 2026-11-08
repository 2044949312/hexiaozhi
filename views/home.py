# -*- coding: utf-8 -*-
"""河小智 · 首页。"""

from __future__ import annotations

from datetime import datetime

from core import auth, data, ui
from core.state import todo_progress


def _greeting() -> str:
    hour = datetime.now().hour
    if hour < 6:
        return "夜深了"
    if hour < 9:
        return "早上好"
    if hour < 12:
        return "上午好"
    if hour < 14:
        return "中午好"
    if hour < 18:
        return "下午好"
    return "晚上好"


def _feature_card(feature: dict) -> str:
    return f"""
<a class="feature-card {ui.e(feature['tone'])}" href="{ui.e(feature['href'])}">
  <div class="feature-icon">{ui.icon(feature['icon'], 23)}</div>
  <div class="feature-title">{ui.e(feature['title'])}</div>
  <div class="feature-desc">{ui.e(feature['desc'])}</div>
  <div class="feature-bottom">
    <span class="feature-tag">{ui.e(feature['tag'])}</span>
    <span class="feature-arrow">{ui.icon('arrow-right', 15)}</span>
  </div>
</a>
"""


def render() -> None:
    done_count, total_count = todo_progress()
    remaining = total_count - done_count
    user = data.USER
    account = auth.current_user()
    display_name = account["username"] if account else user["nickname"]
    service_total = len(data.SERVICES) + len(data.PROCESSES)

    suggestions = "".join(
        f'<a class="suggest-chip" href="{ui.e(ui.page_url("qa", q=question))}">{ui.icon("sparkles", 11)}{ui.e(question)}</a>'
        for question in data.QA_SUGGESTIONS[:3]
    )
    feature_cards = "".join(_feature_card(feature) for feature in data.FEATURES)

    ui.render_html(
        f"""
<!-- ================= 首页 Hero ================= -->
<section class="hero">
  <div class="hero-copy">
    <div class="eyebrow"><span class="eyebrow-dot"></span>HENAN UNIVERSITY · AI CAMPUS</div>
    <h1>{_greeting()}，{ui.e(display_name)} 👋<br><span class="grad">我是河小智</span>，你的 AI 校园伙伴</h1>
    <p class="hero-desc">欢迎回来。把政策、流程、活动和校园里的小事交给我，<b>少跑一趟路，多留一点时间给热爱。</b></p>
    <form class="ai-form" method="get" action="" role="search">
      <input type="hidden" name="page" value="qa"/>
      <span class="ai-form-icon">{ui.icon('sparkles', 20)}</span>
      <input name="q" type="search" placeholder="问政策、找流程、约活动……试试问我" autocomplete="off" aria-label="AI 智能问答输入框" required/>
      <button type="submit">{ui.icon('send', 15)}<span>问问河小智</span></button>
    </form>
    <div class="suggest-row">{suggestions}</div>
    <div class="hero-trust">{ui.icon('shield', 13)}基于校内制度知识库 · 回答标注来源 · 7 × 24 小时在线</div>
  </div>
  <div class="hero-visual" aria-hidden="true">
    <div class="hero-orbit orbit-3"></div>
    <div class="hero-orbit"><div class="hero-orbit orbit-2"><span class="orbit-dot"></span></div></div>
    <div class="hero-mascot">{ui.img_tag('mascot.svg', '河小智 AI 校园助手吉祥物')}</div>
    <div class="float-card top">
      <span class="float-icon">{ui.icon('zap', 15)}</span>
      <span><b>AI 秒答</b>已聚合 {service_total} 项校园服务</span>
    </div>
    <div class="float-card bottom">
      <span class="float-icon">{ui.icon('sparkles', 15)}</span>
      <span><b>有问必答</b>平均 1.8 秒响应</span>
    </div>
  </div>
</section>

<!-- ================= 今日指标 ================= -->
<div class="metric-strip">
  <div class="metric">
    <span class="metric-icon">{ui.icon('book-open', 18)}</span>
    <div><div class="metric-value">4<small>节</small></div><div class="metric-label">今日课程 · 下一节 10:10</div></div>
  </div>
  <div class="metric">
    <span class="metric-icon">{ui.icon('circle-check', 18)}</span>
    <div><div class="metric-value">{remaining}<small>项</small></div><div class="metric-label">待办事项 · 已完成 {done_count}/{total_count}</div></div>
  </div>
  <div class="metric">
    <span class="metric-icon">{ui.icon('calendar', 18)}</span>
    <div><div class="metric-value">4<small>场</small></div><div class="metric-label">本周活动 · 2 场即将截止</div></div>
  </div>
  <div class="metric">
    <span class="metric-icon">{ui.icon('trending-up', 18)}</span>
    <div><div class="metric-value">86<small>/100</small></div><div class="metric-label">成长值 · {ui.e(user['level'])}</div></div>
  </div>
</div>
"""
    )
    ui.render_html(
        f"""
<!-- ================= 核心功能 ================= -->
<div class="feature-grid">{feature_cards}</div>
<a class="growth-banner" href="?page=growth">
  <span class="growth-icon">{ui.icon('trending-up', 21)}</span>
  <span class="growth-copy">
    <b>个人成长档案 · 记录你在河大的每一步</b>
    <span>课程、活动、志愿、荣誉自动沉淀，让成长被看见</span>
  </span>
  <span class="growth-stats">
    <span class="growth-stat"><strong>86</strong>成长值</span>
    <span class="growth-stat"><strong>5</strong>枚徽章</span>
    <span class="growth-stat"><strong>26h</strong>志愿时长</span>
  </span>
  <span class="growth-cta">查看我的档案 {ui.icon('arrow-right', 13)}</span>
</a>
"""
    )
