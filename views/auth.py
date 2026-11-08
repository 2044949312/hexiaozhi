# -*- coding: utf-8 -*-
"""河小智 · 登录 / 注册页。

用户必须先创建账号才能进入站点。账号由系统按注册顺序自动编号，
用户名由用户在注册时自行设置；密码只保存加盐哈希。
"""

from __future__ import annotations

import streamlit as st

from core import auth, ui

_STYLE = """
<style>
.st-key-auth-page{max-width:520px;margin:0 auto;padding:1.2rem 0;animation:fadeUp .45s ease both;}
/* 主容器铺满视口，让登录卡片在页面中垂直居中；内容超高时从头开始排，保持可滚动。 */
[data-testid="stMainBlockContainer"]{min-height:100dvh;display:flex;flex-direction:column;}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"]{justify-content:safe center!important;}

/* ---------- 表单卡片 ---------- */
.st-key-auth-card{
  min-height:620px;padding:34px 38px 26px;border-radius:26px;
  /* 半透明毛玻璃：卡片保持通透，能隐约看到身后的校门。 */
  background:rgba(255,255,255,.70);
  border:1px solid rgba(255,255,255,.62);
  box-shadow:0 30px 70px rgba(2,12,30,.30),0 6px 18px rgba(2,12,30,.12);
  backdrop-filter:blur(12px) saturate(1.12);
  -webkit-backdrop-filter:blur(12px) saturate(1.12);
  display:flex;flex-direction:column;
}
.st-key-auth-card > [data-testid="stVerticalBlock"]{gap:.35rem;flex:1;}
.auth-card-brand{display:flex;align-items:center;gap:9px;margin-bottom:18px;}
.auth-card-brand .brand-logo{width:36px;height:36px;border-radius:11px;box-shadow:0 6px 15px rgba(29,78,216,.18);}
.auth-card-brand b{font-size:17px;font-weight:850;letter-spacing:.03em;}
.auth-card-head{padding-bottom:2px;}
.auth-card-eyebrow{
  display:inline-flex;align-items:center;gap:7px;font-size:9px;font-weight:800;
  letter-spacing:.15em;color:var(--primary);text-transform:uppercase;
}
.auth-card-eyebrow i{width:6px;height:6px;border-radius:50%;background:var(--teal-2);box-shadow:0 0 0 4px rgba(20,184,166,.12);}
.auth-card-head h2{
  margin:9px 0 7px;font-size:30px;line-height:1.22;font-weight:850;
  letter-spacing:-.04em;color:var(--ink);
}
.auth-card-head p{margin:0;font-size:11.5px;line-height:1.75;color:var(--muted);}

.st-key-auth-tabs{
  margin:17px 0 3px;padding:5px;border-radius:14px;
  background:#F3F6FB;border:1px solid #EAF0F8;
}
.st-key-auth-tabs [data-testid="stHorizontalBlock"]{gap:4px;}
.st-key-auth-tabs [data-testid="stColumn"]{padding:0;}
.st-key-auth-tabs .stButton>button{
  width:100%;min-height:40px;padding:0 12px;border:0!important;border-radius:10px;
  background:transparent;color:#64748B;font-family:var(--font);font-size:12px;font-weight:750;
  box-shadow:none!important;transition:all .18s ease;
}
.st-key-auth-tabs .stButton>button:hover{color:var(--primary);background:rgba(255,255,255,.7);transform:none;}
.st-key-auth-tabs .stButton>button[kind="primary"]{
  color:var(--primary)!important;background:#fff!important;
  box-shadow:0 5px 15px rgba(29,78,216,.1)!important;
}

/* 提示条 */
.auth-notice{
  display:flex;align-items:flex-start;gap:9px;margin:12px 0 4px;padding:11px 12px;
  border-radius:12px;border:1px solid transparent;font-size:10.5px;line-height:1.65;
  animation:fadeIn .25s ease;
}
.auth-notice .auth-notice-icon{flex:0 0 auto;display:grid;place-items:center;margin-top:1px;}
.auth-notice b{display:block;font-size:11px;font-weight:800;margin-bottom:2px;}
.auth-notice p{margin:0;color:inherit;opacity:.82;font-size:10px;line-height:1.7;}
.auth-notice strong{
  font-family:"Consolas","SFMono-Regular",monospace;font-size:11.5px;letter-spacing:.05em;
  padding:1px 5px;border-radius:5px;background:rgba(255,255,255,.68);
}
.auth-notice.success{background:#F0FDF8;border-color:#C9F4E4;color:#087A63;}
.auth-notice.error{background:#FFF5F6;border-color:#FBD5DB;color:#BE123C;}

/* 账号自动编号提示 */
.auth-account-auto{
  display:flex;align-items:flex-start;gap:8px;margin:4px 0 10px;padding:9px 11px;
  border-radius:10px;background:#F7FAFF;border:1px dashed #DCE7F7;
  font-size:9.5px;line-height:1.65;color:#5B6B84;
}
.auth-account-auto svg{flex:0 0 auto;margin-top:1px;color:var(--primary);}
.auth-account-auto b{color:var(--ink-soft);font-weight:750;}

/* 表单 */
.st-key-auth-card [data-testid="stForm"]{padding:0;border:0;background:transparent;}
.st-key-auth-card [data-testid="stForm"] [data-testid="stVerticalBlock"]{gap:.25rem;}
.st-key-auth-card [data-testid="stTextInput"]{margin-top:2px;}
.st-key-auth-card [data-testid="stTextInput"] label{margin-bottom:6px;}
.st-key-auth-card [data-testid="stTextInput"] label p{
  font-family:var(--font)!important;font-size:10.5px!important;font-weight:750!important;
  color:var(--ink-soft)!important;letter-spacing:.01em;
}
.st-key-auth-card [data-testid="stTextInput"] [data-baseweb="input"]{
  background:#F8FAFD;border:1px solid #E2EAF6;border-radius:12px;
  transition:border-color .18s ease,box-shadow .18s ease,background .18s ease;
  min-height:47px;
}
.st-key-auth-card [data-testid="stTextInput"] [data-baseweb="input"]:focus-within{
  background:#fff;border-color:#93B4EA;box-shadow:0 0 0 3px rgba(37,99,235,.09);
}
.st-key-auth-card [data-testid="stTextInput"] input{
  min-height:45px;padding:0 13px;background:transparent!important;
  font-family:var(--font)!important;font-size:12px!important;color:var(--ink)!important;
}
.st-key-auth-card [data-testid="stTextInput"] input::placeholder{color:#9AA9BE;font-size:11px;}
.st-key-auth-card [data-testid="stFormSubmitButton"]{margin-top:12px;}
.st-key-auth-card [data-testid="stFormSubmitButton"] button{
  width:100%;min-height:47px;border:0;border-radius:12px;
  background:linear-gradient(135deg,#1D4ED8,#2563EB)!important;color:#fff!important;
  font-family:var(--font);font-size:12.5px;font-weight:800;letter-spacing:.03em;
  box-shadow:0 11px 23px rgba(29,78,216,.24);transition:all .2s ease;
}
.st-key-auth-card [data-testid="stFormSubmitButton"] button:hover{
  transform:translateY(-1px);box-shadow:0 15px 28px rgba(29,78,216,.32)!important;
}
.auth-password-rules{display:flex;flex-wrap:wrap;gap:6px;margin:1px 0 3px;}
.auth-password-rules span{
  display:inline-flex;align-items:center;gap:4px;padding:4px 7px;border-radius:999px;
  background:#F5F8FD;border:1px solid #EAF0F8;color:#7A899F;font-size:8.5px;font-weight:650;
}
.auth-password-rules svg{color:#94A3B8;}
.auth-form-divider{
  display:flex;align-items:center;gap:8px;margin:12px 0 8px;
  font-size:8.5px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#9AA8BD;
}
.auth-form-divider::before,.auth-form-divider::after{content:"";flex:1;height:1px;background:#EDF2F9;}
.auth-form-divider svg{color:var(--teal);}
.auth-security-note{
  display:flex;align-items:flex-start;gap:6px;margin:1px 0 3px;
  font-size:8.5px;line-height:1.65;color:var(--muted-light);
}
.auth-security-note svg{flex:0 0 auto;margin-top:1px;color:#94A3B8;}

/* 找回密码 */
.auth-steps{display:flex;align-items:center;gap:8px;margin:13px 0 12px;}
.auth-step{
  display:inline-flex;align-items:center;gap:5px;font-size:8.5px;font-weight:750;color:#9AA8BD;
  white-space:nowrap;
}
.auth-step i{
  width:17px;height:17px;border-radius:6px;display:grid;place-items:center;
  font-size:8px;font-style:normal;font-weight:850;background:#F1F5FB;color:#8DA0B9;
}
.auth-step.active{color:var(--primary);}
.auth-step.active i{background:var(--primary);color:#fff;box-shadow:0 4px 10px rgba(29,78,216,.2);}
.auth-step.done{color:#0F9488;}
.auth-step.done i{background:var(--teal-soft);color:#0F9488;}
.auth-step-line{flex:1;height:1px;background:#E7EDF6;}
.auth-question-card{
  position:relative;overflow:hidden;margin:5px 0 10px;padding:13px 14px;border-radius:13px;
  background:linear-gradient(135deg,#F4F8FF,#F8FCFB);border:1px solid #DDE9FA;
}
.auth-question-card::after{
  content:"";position:absolute;width:100px;height:100px;right:-40px;top:-55px;border-radius:50%;
  background:radial-gradient(circle,rgba(20,184,166,.14),transparent 70%);pointer-events:none;
}
.auth-question-top{display:flex;align-items:center;justify-content:space-between;gap:10px;}
.auth-question-label{display:inline-flex;align-items:center;gap:5px;font-size:8px;font-weight:800;letter-spacing:.1em;color:var(--primary);text-transform:uppercase;}
.auth-question-account{
  font-family:"Consolas","SFMono-Regular",monospace;font-size:8.5px;font-weight:750;color:#5B6B84;
  padding:3px 6px;border-radius:5px;background:rgba(255,255,255,.8);border:1px solid #E3ECF8;
}
.auth-question-text{
  margin-top:8px;font-size:13px;line-height:1.55;font-weight:800;color:var(--ink);letter-spacing:-.01em;
}
.auth-question-meta{font-size:8.5px;color:var(--muted);line-height:1.6;margin-top:5px;}
.st-key-auth-reset-actions{margin-top:2px;}
.st-key-auth-reset-actions .stButton>button{
  width:auto!important;min-height:30px;padding:0 9px;border:0;background:transparent;
  color:var(--muted);font-size:9.5px;font-weight:700;box-shadow:none!important;
}
.st-key-auth-reset-actions .stButton>button:hover{color:var(--primary);background:#F4F8FF;transform:none;}

.auth-login-hint{
  display:flex;align-items:flex-start;gap:7px;margin-top:12px;padding:9px 11px;
  border-radius:10px;background:#FFFBF0;border:1px solid #F8EBCB;
  font-size:9.5px;line-height:1.65;color:#8A6112;
}
.auth-login-hint svg{flex:0 0 auto;margin-top:1px;color:#C88B15;}
.auth-card-foot{
  display:flex;align-items:center;gap:6px;margin-top:auto;padding-top:18px;
  font-size:8.5px;line-height:1.6;color:#6F7F95;
}
.auth-card-foot svg{flex:0 0 auto;color:#8C9AAF;}

/* 小屏：卡片占满宽度，内边距收紧 */
@media (max-width:920px){
  /* 顶部留出固定校徽的位置，避免卡片与之重叠。 */
  .st-key-auth-page{padding-top:56px;}
  .st-key-auth-card{min-height:0;padding:28px 26px 24px;border-radius:24px;}
  .auth-card-head h2{font-size:27px;}
  /* Streamlit 默认会把窄屏列换成上下堆叠，登录 / 注册 / 找回保持并排。 */
  .st-key-auth-tabs [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;}
  .st-key-auth-tabs [data-testid="stColumn"]{
    flex:1 1 0!important;width:auto!important;min-width:0!important;
  }
  .st-key-auth-tabs .stButton>button{padding:0 5px;font-size:11px;}
}
@media (max-width:480px){
  .st-key-auth-page [data-testid="stAppViewBlockContainer"]{padding-left:.9rem;padding-right:.9rem;}
  .st-key-auth-card{padding:23px 18px 21px;border-radius:21px;}
  .auth-card-head h2{font-size:25px;}
  .st-key-auth-tabs{margin-top:14px;}
}
</style>
"""


def _photo_style() -> str:
    """登录页背景与左上角校徽：校门照片原图清晰呈现作氛围底图。

    背景图固定铺满视口且不做模糊，保留校门的完整细节；照片上只叠
    一层很淡的暗色渐变。校徽同样固定在左上角，作为页面身份标识，
    不参与页面布局，也不会遮挡居中的登录卡片。
    """
    photo = ui.asset_uri("henan-gate.jpg")
    logo = ui.asset_uri("henan-logo.png")
    if not photo and not logo:
        return ""

    background_css = (
        f"""
.stApp::before{{
  content:"";position:fixed;inset:0;z-index:0;pointer-events:none;
  background:
    linear-gradient(118deg,rgba(5,18,40,.30) 0%,rgba(8,34,62,.18) 55%,rgba(8,52,64,.18) 100%),
    url("{photo}") center 42%/cover no-repeat;
  filter:saturate(1.04);
}}"""
        if photo
        else ""
    )
    logo_css = (
        f"""
.stApp::after{{
  content:"";position:fixed;top:26px;left:34px;z-index:6;pointer-events:none;
  width:184px;height:57px;
  background:url("{logo}") left center/contain no-repeat;
  filter:drop-shadow(0 8px 18px rgba(3,18,40,.30));
}}
@media (max-width:920px){{
  .stApp::after{{top:14px;left:20px;width:124px;height:38px;}}
}}
@media (max-width:480px){{
  .stApp::after{{top:12px;left:16px;width:112px;height:35px;}}
}}"""
        if logo
        else ""
    )
    return f"""
<style>
body,.stApp{{background:#081627!important;}}
[data-testid="stAppViewContainer"]{{background:transparent!important;}}
[data-testid="stMain"]{{position:relative;z-index:1;}}{background_css}{logo_css}
</style>
"""


def _card_header(view: str) -> str:
    if view == "register":
        eyebrow = "CREATE ACCOUNT · 创建账号"
        title = "先认识一下，<br>再一起出发。"
        desc = "取一个用户名，再留一组密保问答。账号号会按注册顺序自动发放。"
    elif view == "reset":
        eyebrow = "ACCOUNT RECOVERY · 找回密码"
        title = "别担心，<br>我们一起找回它。"
        desc = "通过注册时设置的密保问题验证身份，验证通过后即可设置新密码。"
    else:
        eyebrow = "WELCOME BACK · 账号登录"
        title = "欢迎回来，<br>今天也一起探索河大。"
        desc = "使用注册时获得的账号号或用户名登录，继续你的校园旅程。"
    return f"""
<div class="auth-card-brand">{ui.logo_mark()}<b>河小智</b></div>
<div class="auth-card-head">
  <div class="auth-card-eyebrow"><i></i>{eyebrow}</div>
  <h2>{title}</h2>
  <p>{desc}</p>
</div>
"""


def _notice_html() -> str:
    error = st.session_state.get("auth_error")
    success = st.session_state.get("auth_success")
    if error:
        return (
            '<div class="auth-notice error">'
            f'<span class="auth-notice-icon">{ui.icon("alert-circle", 16)}</span>'
            f"<div><b>请检查一下</b><p>{ui.e(error)}</p></div>"
            "</div>"
        )
    if isinstance(success, str):
        success = {"kind": "register", "account": success}
    if isinstance(success, dict) and success.get("account"):
        account = ui.e(success["account"])
        if success.get("kind") == "reset":
            title = "密码重置成功"
            body = (
                f"账号 <strong>{account}</strong> 的新密码已生效，并已自动填入登录框。"
                "请使用新密码重新登录。"
            )
        else:
            title = "账号创建成功"
            body = (
                f"你的专属账号号是 <strong>{account}</strong>，"
                "已自动填入下方登录框。请使用刚才设置的密码完成登录。"
            )
        return (
            '<div class="auth-notice success">'
            f'<span class="auth-notice-icon">{ui.icon("circle-check", 16)}</span>'
            f"<div><b>{title}</b><p>{body}</p></div>"
            "</div>"
        )
    return ""


_RESET_WIDGET_KEYS = (
    "reset_identifier",
    "reset_answer",
    "reset_new_password",
    "reset_confirm_password",
)


def _clear_reset_state(clear_widgets: bool = False) -> None:
    st.session_state.pop("reset_account", None)
    if clear_widgets:
        for key in _RESET_WIDGET_KEYS:
            st.session_state.pop(key, None)


def _switch_view(view: str) -> None:
    st.session_state.auth_view = view
    st.session_state.pop("auth_error", None)
    st.session_state.pop("auth_success", None)
    _clear_reset_state(clear_widgets=True)
    st.rerun()


def _render_tabs(view: str) -> str:
    """渲染登录 / 注册 / 找回密码切换按钮。"""
    with st.container(key="auth-tabs"):
        login_col, register_col, reset_col = st.columns(3, gap="small")
        with login_col:
            clicked_login = st.button(
                "登录",
                key="auth-tab-login",
                type="primary" if view == "login" else "secondary",
                use_container_width=True,
            )
        with register_col:
            clicked_register = st.button(
                "注册账号",
                key="auth-tab-register",
                type="primary" if view == "register" else "secondary",
                use_container_width=True,
            )
        with reset_col:
            clicked_reset = st.button(
                "找回密码",
                key="auth-tab-reset",
                type="primary" if view == "reset" else "secondary",
                use_container_width=True,
            )
    if clicked_login and view != "login":
        _switch_view("login")
    if clicked_register and view != "register":
        _switch_view("register")
    if clicked_reset and view != "reset":
        _switch_view("reset")
    return view


def _login_form() -> None:
    prefill = ""
    if st.session_state.pop("_prefill_login", False):
        # 注册成功后首次进入登录视图：清掉旧控件状态并预填新账号号。
        st.session_state.pop("login_identifier", None)
        prefill = st.session_state.pop("auth_prefill_account", "")
    with st.form("hxz-login", clear_on_submit=False, border=False):
        identifier = st.text_input(
            "账号 / 用户名",
            value=prefill,
            key="login_identifier",
            placeholder="例如 HXZ0001，或你的用户名",
        )
        password = st.text_input(
            "密码",
            key="login_password",
            type="password",
            placeholder="请输入登录密码",
        )
        submitted = st.form_submit_button("登录", type="primary", use_container_width=True)

    if submitted:
        if not identifier.strip():
            st.session_state.auth_error = "请输入账号号或用户名。"
        elif not password:
            st.session_state.auth_error = "请输入登录密码。"
        else:
            user = auth.authenticate(identifier, password)
            if user is None:
                st.session_state.pop("auth_success", None)
                st.session_state.auth_error = (
                    "账号或密码不正确。若你还没有注册，请先切换到「注册账号」创建账号。"
                )
            else:
                st.session_state.pop("auth_error", None)
                st.session_state.pop("auth_success", None)
                auth.start_session(user)
                st.query_params.clear()
                st.query_params["page"] = "home"
                st.rerun()
        st.rerun()

    ui.render_html(
        f'<div class="auth-login-hint">{ui.icon("info", 13)}'
        "<span>首次使用请先注册；忘记密码可点击上方「找回密码」，通过注册时的密保问答重设。</span></div>"
    )


def _register_form() -> None:
    ui.render_html(
        f'<div class="auth-account-auto">{ui.icon("id-card", 13)}'
        "<span><b>账号号由系统自动生成。</b>设置用户名、密码和密保问答后，"
        "将按注册顺序获得专属账号号，例如 HXZ0001。</span></div>"
    )
    with st.form("hxz-register", clear_on_submit=False, border=False):
        username = st.text_input(
            "用户名",
            key="register_username",
            placeholder="2–16 位中文、字母、数字或下划线",
        )
        password = st.text_input(
            "设置密码",
            key="register_password",
            type="password",
            placeholder="8–32 位，同时包含字母和数字",
        )
        confirm = st.text_input(
            "确认密码",
            key="register_confirm",
            type="password",
            placeholder="请再次输入密码",
        )
        ui.render_html(
            '<div class="auth-password-rules">'
            f'<span>{ui.icon("check", 10)}8–32 位</span>'
            f'<span>{ui.icon("check", 10)}包含字母和数字</span>'
            f'<span>{ui.icon("shield", 10)}加盐哈希存储</span>'
            "</div>"
        )
        ui.render_html(
            f'<div class="auth-form-divider">{ui.icon("shield", 11)}账号找回保障</div>'
        )
        security_question = st.text_input(
            "密保问题",
            key="register_question",
            placeholder="例如：我最喜欢的校园地点是哪里？",
        )
        security_answer = st.text_input(
            "密保答案",
            key="register_answer",
            placeholder="2–50 字，请填写只有你知道的答案",
        )
        ui.render_html(
            '<div class="auth-security-note">'
            f'{ui.icon("info", 11)}忘记密码时需回答此问题；答案不区分英文大小写，'
            "且只保存加盐哈希。请避免设置容易被他人猜到或包含真实隐私的内容。</div>"
        )
        submitted = st.form_submit_button(
            "创建账号", type="primary", use_container_width=True
        )

    if submitted:
        if not username.strip():
            st.session_state.auth_error = "请先设置用户名。"
        elif not password:
            st.session_state.auth_error = "请设置密码。"
        elif password != confirm:
            st.session_state.auth_error = "两次输入的密码不一致，请重新确认。"
        elif not security_question.strip():
            st.session_state.auth_error = "请设置一个密保问题。"
        elif not security_answer.strip():
            st.session_state.auth_error = "请填写密保答案。"
        else:
            try:
                user = auth.register(
                    username, password, security_question, security_answer
                )
            except auth.AuthError as exc:
                st.session_state.auth_error = str(exc)
            else:
                st.session_state.pop("auth_error", None)
                st.session_state.auth_success = {
                    "kind": "register",
                    "account": user["account_no"],
                }
                st.session_state.auth_view = "login"
                st.session_state.auth_prefill_account = user["account_no"]
                st.session_state._prefill_login = True
                st.rerun()
        st.rerun()


def _reset_steps(step: int) -> str:
    first = "done" if step >= 2 else "active"
    second = "active" if step >= 2 else ""
    return (
        '<div class="auth-steps">'
        f'<span class="auth-step {first}"><i>1</i>验证账号</span>'
        '<span class="auth-step-line"></span>'
        f'<span class="auth-step {second}"><i>2</i>重置密码</span>'
        "</div>"
    )


def _reset_identify_form() -> None:
    ui.render_html(_reset_steps(1))
    with st.form("hxz-reset-identify", clear_on_submit=False, border=False):
        identifier = st.text_input(
            "账号 / 用户名",
            key="reset_identifier",
            placeholder="输入注册时的账号号或用户名",
        )
        submitted = st.form_submit_button(
            "下一步 · 验证密保", type="primary", use_container_width=True
        )

    if submitted:
        if not identifier.strip():
            st.session_state.auth_error = "请输入账号号或用户名。"
        else:
            target = auth.get_security_question(identifier)
            if target is None:
                st.session_state.auth_error = (
                    "未找到该账号。请确认账号号或用户名；还没有账号请先注册。"
                )
            elif not target.get("question"):
                st.session_state.auth_error = (
                    "该账号尚未设置密保问题，暂时无法自助找回密码。"
                    "请联系管理员，或重新注册一个演示账号。"
                )
            else:
                st.session_state.pop("auth_error", None)
                st.session_state.reset_account = target
        st.rerun()

    ui.render_html(
        f'<div class="auth-login-hint">{ui.icon("info", 13)}'
        "<span>找回密码需要验证注册时设置的密保问答；账号号可在注册成功提示中查看，"
        "也可以直接使用用户名。</span></div>"
    )


def _reset_password_form(target: dict) -> None:
    account_no = ui.e(target.get("account_no", ""))
    username = ui.e(target.get("username", ""))
    question = ui.e(target.get("question", ""))
    ui.render_html(
        _reset_steps(2)
        + f"""
<div class="auth-question-card">
  <div class="auth-question-top">
    <span class="auth-question-label">{ui.icon("shield", 11)}你的密保问题</span>
    <span class="auth-question-account">{account_no}</span>
  </div>
  <div class="auth-question-text">{question}</div>
  <div class="auth-question-meta">{username} · 请回答注册时设置的密保答案</div>
</div>
"""
    )

    with st.form("hxz-reset-password", clear_on_submit=False, border=False):
        answer = st.text_input(
            "密保答案",
            key="reset_answer",
            placeholder="答案不区分英文大小写",
        )
        new_password = st.text_input(
            "新密码",
            key="reset_new_password",
            type="password",
            placeholder="8–32 位，同时包含字母和数字",
        )
        confirm = st.text_input(
            "确认新密码",
            key="reset_confirm_password",
            type="password",
            placeholder="请再次输入新密码",
        )
        ui.render_html(
            '<div class="auth-password-rules">'
            f'<span>{ui.icon("check", 10)}8–32 位</span>'
            f'<span>{ui.icon("check", 10)}包含字母和数字</span>'
            f'<span>{ui.icon("shield", 10)}重置后旧密码失效</span>'
            "</div>"
        )
        submitted = st.form_submit_button(
            "重置密码", type="primary", use_container_width=True
        )

    if submitted:
        if not answer.strip():
            st.session_state.auth_error = "请输入密保答案。"
        elif not new_password:
            st.session_state.auth_error = "请设置新密码。"
        elif new_password != confirm:
            st.session_state.auth_error = "两次输入的新密码不一致，请重新确认。"
        else:
            try:
                user = auth.reset_password(
                    target.get("account_no", ""), answer, new_password
                )
            except auth.AuthError as exc:
                st.session_state.auth_error = str(exc)
            else:
                st.session_state.pop("auth_error", None)
                _clear_reset_state(clear_widgets=False)
                st.session_state.auth_success = {
                    "kind": "reset",
                    "account": user["account_no"],
                }
                st.session_state.auth_view = "login"
                st.session_state.auth_prefill_account = user["account_no"]
                st.session_state._prefill_login = True
                st.rerun()
        st.rerun()

    with st.container(key="auth-reset-actions"):
        if st.button(
            "← 换一个账号",
            key="reset-change-account",
            type="tertiary",
            use_container_width=False,
        ):
            st.session_state.pop("auth_error", None)
            _clear_reset_state(clear_widgets=False)
            st.rerun()

    ui.render_html(
        f'<div class="auth-security-note" style="margin-top:8px">'
        f'{ui.icon("info", 11)}密码重置后旧密码立即失效；其他设备刷新页面后需使用新密码重新登录。</div>'
    )


def _reset_form() -> None:
    target = st.session_state.get("reset_account")
    if isinstance(target, dict) and target.get("question"):
        _reset_password_form(target)
    else:
        _reset_identify_form()


def render() -> None:
    st.markdown(_STYLE + _photo_style(), unsafe_allow_html=True)

    if "auth_view" not in st.session_state or st.session_state.auth_view not in {
        "login",
        "register",
        "reset",
    }:
        st.session_state.auth_view = "login"

    view = st.session_state.auth_view
    with st.container(key="auth-page"):
        with st.container(key="auth-card"):
            ui.render_html(_card_header(view))
            view = _render_tabs(view)
            notice = _notice_html()
            if notice:
                ui.render_html(notice)
            if view == "register":
                _register_form()
            elif view == "reset":
                _reset_form()
            else:
                _login_form()
            ui.render_html(
                f'<div class="auth-card-foot">{ui.icon("shield", 12)}'
                "密码与密保答案均经加盐哈希保存在本地 · 本演示系统不采集真实身份信息</div>"
            )
