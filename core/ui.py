# -*- coding: utf-8 -*-
"""河小智 · 共享 UI 组件与品牌元素。"""

from __future__ import annotations

import base64
import html
import os
import re
from urllib.parse import urlencode

import streamlit as st

from .data import USER

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# 首屏在视觉资产尚未生成时也能保持完整品牌感
_FALLBACK_LOGO = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" role="img" aria-label="河小智">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#1D4ED8"/><stop offset=".55" stop-color="#2563EB"/><stop offset="1" stop-color="#14B8A6"/></linearGradient></defs>
<rect width="96" height="96" rx="26" fill="url(#g)"/>
<rect x="25" y="30" width="46" height="38" rx="14" fill="none" stroke="#fff" stroke-width="4"/>
<path d="M48 20v8" stroke="#fff" stroke-width="4" stroke-linecap="round"/><circle cx="48" cy="18" r="4" fill="#F5B942"/>
<circle cx="38" cy="47" r="4" fill="#fff"/><circle cx="58" cy="47" r="4" fill="#fff"/><path d="M39 57c2.8 3 5.8 4.4 9 4.4s6.2-1.4 9-4.4" fill="none" stroke="#fff" stroke-width="3.6" stroke-linecap="round"/>
<path d="M31 76h34" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity=".55"/>
</svg>"""

NAV_ITEMS = [
    ("home", "首页", "?page=home"),
    ("qa", "智能问答", "?page=qa"),
    ("services", "办事流程", "?page=services"),
    ("activities", "校园活动", "?page=activities"),
    ("center", "我的河大", "?page=center"),
]

ICONS: dict[str, str] = {
    "sparkles": '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3Z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z"/><path d="M5 3v3M3.5 4.5h3"/>',
    "route": '<circle cx="6" cy="19" r="2"/><circle cx="18" cy="5" r="2"/><path d="M8 19h5a3 3 0 0 0 3-3V8a3 3 0 0 1 3-3h-1"/><path d="M6 17V7a2 2 0 0 1 2-2h2"/>',
    "compass": '<circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2.1 4.9-4.9 2.1 2.1-4.9 4.9-2.1Z"/>',
    "layout-grid": '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
    "calendar": '<rect x="3" y="4.5" width="18" height="16" rx="3"/><path d="M8 3v3M16 3v3M3 9.5h18"/><path d="M8 13h2M14 13h2M8 17h2M14 17h2"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "map-pin": '<path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.6"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="3.5"/><path d="M22 21v-2a4 4 0 0 0-3-3.85M16.5 3.5a4 4 0 0 1 0 7"/>',
    "arrow-right": '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>',
    "chevron-right": '<path d="m9 18 6-6-6-6"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "check": '<path d="m5 12 4.5 4.5L19 7"/>',
    "bell": '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "send": '<path d="m22 2-7 20-4-9-9-4 20-7Z"/><path d="M22 2 11 13"/>',
    "book-open": '<path d="M2 5h6a4 4 0 0 1 4 4v12a3 3 0 0 0-3-3H2V5Z"/><path d="M22 5h-6a4 4 0 0 0-4 4v12a3 3 0 0 1 3-3h7V5Z"/>',
    "library": '<path d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6"/><path d="M9 10h.01M15 10h.01"/>',
    "credit-card": '<rect x="2" y="5" width="20" height="14" rx="3"/><path d="M2 10h20M6 15h3"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "wrench": '<path d="M14.7 6.3a4 4 0 0 0-5.6 5.1L3 17.5V21h3.5l6.1-6.1a4 4 0 0 0 5.1-5.6l-2.8 2.8-2-2 2.8-2.8Z"/>',
    "bus": '<rect x="4" y="3" width="16" height="15" rx="3"/><path d="M4 9h16M8 18v2M16 18v2M8 21h8"/><circle cx="8" cy="14" r="1"/><circle cx="16" cy="14" r="1"/>',
    "file-text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z"/><path d="M14 2v6h6M8 13h8M8 17h5"/>',
    "heart": '<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"/>',
    "trophy": '<path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0V4Z"/><path d="M7 6H4v2a4 4 0 0 0 4 4M17 6h3v2a4 4 0 0 1-4 4"/>',
    "award": '<circle cx="12" cy="8" r="5"/><path d="m8.5 12-2 9 5.5-3 5.5 3-2-9"/>',
    "graduation-cap": '<path d="M22 9 12 4 2 9l10 5 10-5Z"/><path d="M6 11v5c0 2 2.7 3.5 6 3.5s6-1.5 6-3.5v-5M22 9v6"/>',
    "home": '<path d="m3 10 9-7 9 7v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-9Z"/><path d="M9 21v-6h6v6"/>',
    "shield": '<path d="M12 22s8-3.5 8-10V5l-8-3-8 3v7c0 6.5 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
    "code": '<path d="m8 8-5 4 5 4M16 8l5 4-5 4M14 4l-4 16"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    "flame": '<path d="M12 22c4 0 7-2.8 7-7 0-4-3-6-4.5-9C14 4 13 2 13 2s-.5 4-2 6c-1 1.4-2 2-2 4.5C8 15 6 14 6 17c0 3 2.5 5 6 5Z"/><path d="M12 22c1.8 0 3-1.4 3-3 0-1.6-1.2-2.4-1.8-3.7-.5-1-.7-2.3-.7-2.3s-1.5 1.7-2.3 3.2C9.5 17.6 9 18.5 9 19.5c0 1.4 1.2 2.5 3 2.5Z"/>',
    "star": '<path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-2.9-5.6 2.9 1.1-6.2L3 9.6l6.2-.9L12 3Z"/>',
    "trending-up": '<path d="m3 17 6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "wallet": '<path d="M20 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0 0 4h15v14H5a2 2 0 0 1-2-2V5"/><path d="M16 13h4"/>',
    "id-card": '<rect x="2" y="5" width="20" height="14" rx="3"/><circle cx="8" cy="11" r="2"/><path d="M5 16c.5-1.5 1.6-2.2 3-2.2s2.5.7 3 2.2M14 10h5M14 14h5"/>',
    "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.4 19.4 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.8 2.1Z"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>',
    "filter": '<path d="M22 3H2l8 9.5V19l4 2v-8.5L22 3Z"/>',
    "refresh": '<path d="M21 12a9 9 0 0 1-15.5 6.2L3 16M3 12A9 9 0 0 1 18.5 5.8L21 8"/><path d="M3 21v-5h5M21 3v5h-5"/>',
    "message": '<path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v8Z"/><path d="M8 9h8M8 13h5"/>',
    "circle-check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 2.5 2.5L16 9"/>',
    "alert-circle": '<circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16.5h.01"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.5h.01"/>',
    "cpu": '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9" y="9" width="6" height="6" rx="1"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
    "zap": '<path d="M13 2 3 14h8l-1 8 10-12h-8l1-8Z"/>',
    "play": '<path d="m7 4 13 8-13 8V4Z"/>',
    "music": '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
    "run": '<circle cx="17" cy="4" r="2"/><path d="m5 21 4-6 3 2 2-5-4-3 4-3M9 15l-2-5 4-2 3 4h5"/>',
    "moon": '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "logout": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4v-.2a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.6-1H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.6v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "x": '<path d="M18 6 6 18M6 6l12 12"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18Z"/>',
    "external": '<path d="M14 3h7v7M21 3l-9 9"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    "paperclip": '<path d="m21.4 11.6-8.9 8.9a6 6 0 0 1-8.5-8.5l8.9-8.9a4 4 0 0 1 5.7 5.7l-8.9 8.9a2 2 0 0 1-2.8-2.8l8.2-8.2"/>',
    "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5"/><path d="M12 3v12"/>',
    "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    "layers": '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 13 9 5 9-5"/>',
    "bookmark": '<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16Z"/>',
    "corner-down-right": '<path d="M15 10l5 5-5 5"/><path d="M4 4v7a4 4 0 0 0 4 4h12"/>',
    "file-up": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z"/><path d="M14 2v6h6"/><path d="M12 18v-6M9 15l3-3 3 3"/>',
    "thumbs-up": '<path d="M7 10v12"/><path d="M15 5.9 14 10h5.8a2 2 0 0 1 2 2.3l-1.3 7a2 2 0 0 1-2 1.7H7V10l4-7a2.6 2.6 0 0 1 4 2.9Z"/>',
    "flag": '<path d="M4 22V4c1.5-1 3-1.5 5-1.5 3 0 4.5 1.5 7 1.5 1.5 0 3-.3 4-1v11c-1 .7-2.5 1-4 1-2.5 0-4-1.5-7-1.5-2 0-3.5.5-5 1.5"/>',
    "alarm-clock": '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2.5M5 3 2 6M19 3l3 3"/>',
    "pencil": '<path d="M21.2 6.4a2 2 0 0 0 0-2.8l-.8-.8a2 2 0 0 0-2.8 0L3 17.2V21h3.8L21.2 6.4Z"/><path d="m16 5 3 3"/>',
    "trash": '<path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M10 11v6M14 11v6"/>',
    "sparkle": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M18.4 5.6l-2.8 2.8M8.4 15.6l-2.8 2.8"/>',
}


def e(value) -> str:
    """HTML 转义，所有动态文本都必须经过它。"""
    return html.escape(str(value), quote=True)


def qp(name: str, default: str = "") -> str:
    """读取查询参数，兼容 Streamlit 不同版本返回 list 的情况。"""
    try:
        value = st.query_params.get(name, default)
    except Exception:
        return default
    if isinstance(value, list):
        return str(value[0]) if value else default
    return str(value) if value is not None else default


def page_url(page: str, **params) -> str:
    query = {"page": page}
    query.update({k: v for k, v in params.items() if v is not None})
    return "?" + urlencode(query)


_IMAGE_MIME = {
    ".svg": "svg+xml",
    ".png": "png",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".webp": "webp",
    ".gif": "gif",
}


def asset_uri(filename: str) -> str:
    """把本地图片转成 data URI。

    说明：Streamlit 的 /app/static 路由不把 .svg 列为安全图片类型，会以
    text/plain + nosniff 返回，浏览器无法作为图片加载；因此这里统一内联。
    为控制单个富文本块体积，首页按区块分段渲染。
    """
    path = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "rb") as fh:
            encoded = base64.b64encode(fh.read()).decode("ascii")
        suffix = _IMAGE_MIME.get(os.path.splitext(filename)[1].lower(), "png")
        return f"data:image/{suffix};base64,{encoded}"
    except OSError:
        return ""


def logo_mark() -> str:
    """返回可直接放进 HTML 的 Logo。"""
    uri = asset_uri("logo.svg")
    if uri:
        return f'<img class="brand-logo" src="{uri}" alt="河小智 Logo" width="42" height="42"/>'
    encoded = base64.b64encode(_FALLBACK_LOGO.encode("utf-8")).decode("ascii")
    return f'<img class="brand-logo" src="data:image/svg+xml;base64,{encoded}" alt="河小智 Logo" width="42" height="42"/>'


def img_tag(filename: str, alt: str, cls: str = "", fallback_icon: str = "sparkles") -> str:
    uri = asset_uri(filename)
    if uri:
        return f'<img class="{e(cls)}" src="{uri}" alt="{e(alt)}" loading="lazy"/>'
    return (
        f'<div class="{e(cls)} img-fallback" role="img" aria-label="{e(alt)}">'
        f"{icon(fallback_icon, 44)}</div>"
    )


def render_html(markup: str) -> None:
    """渲染自定义 HTML，并让站内链接在当前标签页打开。

    注意：``st.markdown`` 会先把内容当 Markdown 解析。模板里给可选片段
    （提示、附件、链接等）预留的行，在片段为空时会变成纯空白行，从而截断
    CommonMark 的 HTML 块；其后带 4 个及以上空格缩进的 HTML 行便会被当成
    「缩进代码块」，把 ``<div>`` 等原始标签直接显示在回答里。
    这里统一去掉行首空白（HTML / CSS / SVG 对行首空白不敏感），避免该问题。
    """
    markup = re.sub(r"(?m)^[ \t]+", "", str(markup or ""))
    # Streamlit 会给 Markdown 中的链接自动补 target="_blank"；显式 _self 可避免
    # 每一次站内跳转都新开一个标签页。
    markup = markup.replace("<a ", '<a target="_self" ')
    st.markdown(markup, unsafe_allow_html=True)


def icon(name: str, size: int = 20, stroke: float = 1.8) -> str:
    body = ICONS.get(name, ICONS["sparkles"])
    return (
        f'<svg class="lucide" viewBox="0 0 24 24" width="{size}" height="{size}" '
        f'fill="none" stroke="currentColor" stroke-width="{stroke}" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>'
    )


def topbar(active: str = "home", user: dict | None = None) -> None:
    nav_html = []
    for key, label, href in NAV_ITEMS:
        active_class = "active" if active == key or (key == "center" and active == "growth") else ""
        nav_html.append(f'<a class="nav-link {active_class}" href="{href}">{label}</a>')
    nav = "".join(nav_html)
    mobile_nav = "".join(
        f'<a class="mobile-nav-link {"active" if active == key else ""}" href="{href}">{icon(icon_name, 16)}{label}</a>'
        for (key, label, href), icon_name in zip(NAV_ITEMS, ["home", "message", "route", "compass", "id-card"])
    )
    display_name = user.get("username") if user else USER["nickname"]
    display_meta = user.get("account_no") if user else USER["level"]
    display_initial = user.get("initial") if user else USER["initial"]
    render_html(
        f"""
<header class="topbar">
  <a class="brand" href="?page=home" aria-label="河小智首页">
    {logo_mark()}
    <span class="brand-text"><strong>河小智</strong><small>河南大学 · AI 智慧校园</small></span>
  </a>
  <nav class="main-nav" aria-label="主导航">{nav}</nav>
  <div class="top-actions">
    <a class="icon-btn" href="?page=center" aria-label="通知" title="通知">{icon("bell", 19)}<span class="notify-dot"></span></a>
    <a class="user-chip" href="?page=center" aria-label="个人中心">
      <span class="avatar">{e(display_initial)}</span>
      <span class="user-meta"><b>{e(display_name)}</b><small>{e(display_meta)}</small></span>
    </a>
    <a class="icon-btn logout-btn" href="?logout=1" aria-label="退出登录" title="退出登录">{icon("logout", 18)}</a>
  </div>
</header>
<nav class="mobile-nav" aria-label="移动端导航">{mobile_nav}</nav>
"""
    )


def footer() -> None:
    render_html(
        f"""
<footer class="site-footer">
  <div class="footer-main">
    <div class="footer-brand">
      {logo_mark()}
      <div><b>河小智</b><span>让校园生活更简单一点</span></div>
    </div>
    <div class="footer-links">
      <a href="?page=qa">智能问答</a><span></span>
      <a href="?page=services">办事流程</a><span></span>
      <a href="?page=activities">校园活动</a><span></span>
      <a href="?page=growth">成长档案</a>
    </div>
  </div>
  <div class="footer-bottom">
    <span>© 2026 河小智 · 河南大学 AI 智慧校园服务平台</span>
    <span>大学生黑客松「校园新物种」赛道参赛作品 · 演示数据，非学校官方系统</span>
  </div>
</footer>
"""
    )


def section_header(
    title: str,
    eyebrow: str = "",
    subtitle: str = "",
    link_label: str = "",
    link_href: str = "",
    icon_name: str = "",
) -> str:
    eyebrow_html = (
        f'<div class="section-eyebrow">{icon(icon_name, 13) if icon_name else ""}{e(eyebrow)}</div>'
        if eyebrow
        else ""
    )
    link_html = (
        f'<a class="section-link" href="{e(link_href)}">{e(link_label)}{icon("arrow-right", 16)}</a>'
        if link_label and link_href
        else ""
    )
    return f"""
<div class="section-head">
  <div>
    {eyebrow_html}
    <h2 class="section-title">{e(title)}</h2>
    {f'<p class="section-sub">{e(subtitle)}</p>' if subtitle else ''}
  </div>
  {link_html}
</div>
"""


def page_hero(
    eyebrow: str,
    title: str,
    subtitle: str,
    icon_name: str = "sparkles",
    tone: str = "blue",
    meta: str = "",
) -> str:
    meta_html = f'<div class="page-hero-meta">{meta}</div>' if meta else ""
    return f"""
<section class="page-hero {e(tone)}">
  <div class="page-hero-copy">
    <div class="eyebrow"><span class="eyebrow-dot"></span>{e(eyebrow)}</div>
    <h1>{title}</h1>
    <p>{e(subtitle)}</p>
    {meta_html}
  </div>
  <div class="page-hero-art" aria-hidden="true">
    <div class="page-hero-ring"></div>
    {icon(icon_name, 88, 1.25)}
  </div>
</section>
"""


def pill(text: str, tone: str = "blue", icon_name: str = "") -> str:
    ico = icon(icon_name, 13) if icon_name else ""
    return f'<span class="pill {e(tone)}">{ico}{e(text)}</span>'


def tag(text: str, tone: str = "blue") -> str:
    return f'<span class="tag {e(tone)}">{e(text)}</span>'


def ring(value: int, label: str = "成长值", size: int = 146) -> str:
    try:
        value = max(0, min(100, int(value)))
    except (TypeError, ValueError):
        value = 0
    return f"""
<div class="ring" style="--value:{value};--size:{size}px" role="img" aria-label="{e(label)} {value}%">
  <div class="ring-inner"><strong>{value}<small>%</small></strong><span>{e(label)}</span></div>
</div>
"""


def progress_bar(value: int, tone: str = "blue") -> str:
    try:
        value = max(0, min(100, int(value)))
    except (TypeError, ValueError):
        value = 0
    return f'<div class="mini-progress"><span class="{e(tone)}" style="width:{value}%"></span></div>'


def empty_state(title: str, desc: str = "", icon_name: str = "search", action_label: str = "", action_href: str = "") -> str:
    action = (
        f'<a class="btn btn-ghost" href="{e(action_href)}">{e(action_label)}</a>'
        if action_label and action_href
        else ""
    )
    return f"""
<div class="empty-state">
  <div class="empty-icon">{icon(icon_name, 34)}</div>
  <h3>{e(title)}</h3>
  <p>{e(desc)}</p>
  {action}
</div>
"""


def stat_card(label: str, value: str, unit: str = "", icon_name: str = "sparkles", tone: str = "blue", foot: str = "") -> str:
    foot_html = f'<div class="stat-foot">{e(foot)}</div>' if foot else ""
    return f"""
<div class="stat-card {e(tone)}">
  <div class="stat-icon">{icon(icon_name, 20)}</div>
  <div class="stat-value">{e(value)}<small>{e(unit)}</small></div>
  <div class="stat-label">{e(label)}</div>
  {foot_html}
</div>
"""


def scroll_top() -> None:
    """在页面切换后回到顶部，避免继承上一页滚动位置。"""
    st.markdown(
        """
<script>
const scroller = window.parent.document.querySelector('[data-testid="stMain"]');
if (scroller) { scroller.scrollTo({top: 0, behavior: "instant"}); }
</script>
""",
        unsafe_allow_html=True,
    )
