# -*- coding: utf-8 -*-
"""河小智 · 河南大学 AI 智慧校园服务平台

启动方式（Windows）：
    .\\start.ps1
或：
    $env:PYTHONPATH="$PWD\\.deps"; python -m streamlit run app.py --server.port 8501
"""

from __future__ import annotations

import importlib

import streamlit as st

st.set_page_config(
    page_title="河小智 · 河南大学 AI 智慧校园",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "河小智 · 河南大学 AI 智慧校园服务平台｜大学生黑客松「校园新物种」赛道参赛作品",
    },
)

from core.auth import current_user, end_session  # noqa: E402
from core.state import init_state  # noqa: E402
from core.theme import inject_theme  # noqa: E402
from core.ui import footer, topbar  # noqa: E402

PAGES = {
    "home": "首页",
    "qa": "智能问答",
    "services": "办事流程导航",
    "activities": "校园活动",
    "center": "个人事务中心",
    "growth": "个人成长档案",
}

inject_theme()

# 退出登录：清空当前浏览器会话，回到登录页。
_logout = st.query_params.get("logout", "")
if isinstance(_logout, list):
    _logout = _logout[0] if _logout else ""
if str(_logout).lower() in {"1", "true", "yes"}:
    end_session()
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()

# 先恢复登录身份，再初始化会话状态：问答记录按账号隔离，
# 必须知道当前账号后才能读取对应的历史。
user = current_user()
init_state()
if user is None:
    # 未登录时不渲染站点壳层，只展示登录 / 注册界面。
    from views import auth as auth_view  # noqa: E402

    auth_view.render()
    st.stop()

page = st.query_params.get("page", "home")
if isinstance(page, list):
    page = page[0] if page else "home"
page = str(page) if page else "home"
if page not in PAGES:
    page = "home"

topbar(page, user)

try:
    module = importlib.import_module(f"views.{page}")
    module.render()
except ModuleNotFoundError as exc:
    if getattr(exc, "name", "") == f"views.{page}":
        st.markdown(
            f"""
<div class="empty-state" style="margin-top:30px">
  <div class="empty-icon">🚧</div>
  <h3>{PAGES[page]} 正在接入中</h3>
  <p>页面模块尚未完成，请先返回首页体验其他功能。</p>
  <a class="btn btn-primary" href="?page=home">返回首页</a>
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        raise
except Exception as exc:  # pragma: no cover - 现场演示的友好兜底
    st.error("页面加载遇到了一个小问题，请返回首页重试。")
    with st.expander("查看技术细节"):
        st.exception(exc)
    st.markdown('<a class="btn btn-primary" href="?page=home">返回首页</a>', unsafe_allow_html=True)

footer()
