# -*- coding: utf-8 -*-
"""河小智 · 页面二：智能问答（AI 聊天 + 校园政策知识库）

页面职责（由 app.py 调用 render()，不包含 set_page_config / topbar / footer）：

- AI 聊天界面：气泡对话、欢迎语、输入条、发送按钮。
- 连续对话：消息保存在 ``st.session_state`` 并持久化到 ``.tmp/qa_session.json``，
  刷新页面、跳转其它页面再回来，对话仍在；追问由 ``core.kb`` 结合上文回答。
- 校园政策问答：本地制度知识库（``core.policy`` + ``core.data.QA_KB``）检索式回答。
- PDF 文件上传：``core.pdf_reader`` 纯标准库解析中文 PDF，加入本次检索范围。
- 知识库检索：右侧检索面板 + 每个回答的检索轨迹（命中片段与分数）。
- 答案来源引用：每个回答可展开「依据来源」，含制度名、文号、条款、摘录。
- 常见问题推荐：右侧 FAQ 推荐 + 5 个预设快捷问题（点击即真正发起提问）。

交互实现说明：问答、快捷问题、继续追问、上传、检索全部使用 Streamlit 组件
（同一次会话内完成，不整页刷新），因此「连续对话」是真实的；从首页 / 其它页面
带 ``?q=`` 进入时由 ``_handle_params()`` 处理一次，``token`` 保证不重复入栈。
``?new=1`` / ``?clear=1`` 也由 token 保证只生效一次。
"""

from __future__ import annotations

import hashlib
import os
import time

import streamlit as st
import streamlit.components.v1 as components

from core import auth, data, ui

try:  # 问答引擎（队友并行开发，缺失时页面降级而不是整页崩溃）
    from core import kb
except Exception:  # pragma: no cover - 仅用于并行开发期间的兜底
    kb = None

try:  # 大模型增强（可选）：未配置 API 或调用失败时自动沿用本地回答
    from core import llm_qa
except Exception:  # pragma: no cover
    llm_qa = None

try:
    from core import pdf_reader
except Exception:  # pragma: no cover
    pdf_reader = None

try:
    from core import policy
except Exception:  # pragma: no cover
    policy = None

try:
    from core.state import (
        append_qa,
        clear_qa,
        qa_add_doc,
        qa_docs,
        qa_history,
        qa_last_result,
        qa_new_session,
        qa_remove_doc,
        qa_session_no,
    )
except Exception:  # pragma: no cover - 旧 state 兼容
    from core.state import append_qa, clear_qa, qa_history  # type: ignore

    def qa_docs() -> list:
        return list(st.session_state.get("qa_docs", []))

    def qa_add_doc(doc: dict) -> None:
        docs = st.session_state.setdefault("qa_docs", [])
        docs.append(doc)
        st.session_state.qa_docs = docs

    def qa_remove_doc(doc_id: str) -> None:
        st.session_state.qa_docs = [d for d in qa_docs() if d.get("id") != doc_id]

    def qa_new_session() -> str:
        clear_qa()
        st.session_state.qa_docs = []
        return ""

    def qa_session_no() -> int:
        return 1

    def qa_last_result():
        history = qa_history()
        for message in reversed(history):
            if message.get("role") == "assistant" and isinstance(message.get("content"), dict):
                return message["content"]
        return None

import os as _os

_BASE_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_SAMPLES_DIR = _os.path.join(_BASE_DIR, "docs", "samples")

# 与 core/theme.py 中 .pill / .tag 的色板保持一致
_TONE_STYLE = {
    "blue": ("var(--primary-soft)", "var(--primary)"),
    "teal": ("var(--teal-soft)", "#0F9488"),
    "gold": ("var(--gold-soft)", "#B7790B"),
    "violet": ("var(--violet-soft)", "var(--violet)"),
    "rose": ("var(--rose-soft)", "var(--rose)"),
    "green": ("#ECFDF3", "#15803D"),
    "gray": ("#F3F6FA", "var(--muted)"),
}


def _tone(tone: str) -> tuple[str, str]:
    return _TONE_STYLE.get(str(tone or "").strip().lower(), _TONE_STYLE["blue"])


# --------------------------------------------------------------------------- #
# 页面样式（仅智能问答页注入，避免影响其它页面）
# --------------------------------------------------------------------------- #
_CSS = r"""
<style>
/* ---------- 快捷提问 ---------- */
.st-key-qa-quick{
  background:#fff;border:1px solid var(--border);border-radius:22px;
  padding:18px 20px 15px;box-shadow:var(--shadow-xs);
}
.qa-quick-head{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;flex-wrap:wrap;margin-bottom:13px;}
.qa-quick-eyebrow{display:inline-flex;align-items:center;gap:6px;font-size:9px;font-weight:800;letter-spacing:.16em;color:var(--primary);text-transform:uppercase;}
.qa-quick-title{margin:6px 0 4px;font-size:16px;font-weight:840;color:var(--ink);letter-spacing:-.01em;}
.qa-quick-sub{margin:0;font-size:10.5px;color:var(--muted);line-height:1.6;}
.qa-quick-badge{
  display:inline-flex;align-items:center;gap:5px;padding:6px 10px;border-radius:999px;
  background:var(--primary-soft);color:var(--primary);font-size:9.5px;font-weight:750;white-space:nowrap;
}
.st-key-qa-quick [data-testid="stHorizontalBlock"]{gap:10px;align-items:stretch;}
.st-key-qa-quick [data-testid="stColumn"]{min-width:0;}
.qa-quick-card{
  display:flex;align-items:center;justify-content:space-between;gap:8px;
  padding:9px 11px;border-radius:13px;background:#F8FAFF;border:1px solid #EAF0FB;
}
.qa-quick-ico{width:29px;height:29px;border-radius:9px;display:grid;place-items:center;flex:0 0 auto;}
.qa-quick-hint{font-size:9px;line-height:1.45;color:var(--muted);flex:1;min-width:0;}
.qa-quick-no{font-size:9px;font-weight:800;color:#B6C4DA;font-variant-numeric:tabular-nums;}
.st-key-qa-quick [data-testid="stButton"]>button{
  width:100%;text-align:left;justify-content:flex-start;border-radius:12px;
  padding:9px 11px;min-height:46px;font-size:10.8px;font-weight:750;line-height:1.5;
  color:var(--ink);background:#fff;border:1px solid #DDE8F8;white-space:normal;
  box-shadow:0 2px 8px rgba(15,27,51,.03);
}
.st-key-qa-quick [data-testid="stButton"]>button:hover{
  border-color:#B9D0F3;background:#F6FAFF;color:var(--primary);transform:translateY(-1px);
}

/* ---------- 主布局 ---------- */
.st-key-qa-main{padding:0;}
.st-key-qa-main [data-testid="stHorizontalBlock"]{gap:18px;align-items:flex-start;}
.st-key-qa-main > div > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{min-width:0;}

/* ---------- 聊天卡片 ---------- */
.qa-chat{
  background:#fff;border:1px solid var(--border);border-radius:24px;
  padding:20px 20px 12px;box-shadow:var(--shadow-sm);
}
.qa-chat-head{
  display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;
  padding-bottom:14px;margin-bottom:15px;border-bottom:1px dashed #E9EFF9;
}
.qa-chat-id{display:flex;align-items:center;gap:11px;min-width:0;}
.qa-chat-avatar{
  width:43px;height:43px;border-radius:14px;display:grid;place-items:center;flex:0 0 auto;
  color:#fff;background:linear-gradient(135deg,#1D4ED8,#14B8A6);
  box-shadow:0 8px 18px rgba(29,78,216,.22);
}
.qa-chat-name{display:flex;align-items:center;gap:8px;font-size:14.5px;font-weight:820;color:var(--ink);letter-spacing:-.01em;}
.qa-live{display:inline-flex;align-items:center;gap:5px;font-size:9px;font-weight:750;color:#0F766E;background:#ECFDF9;border:1px solid #CBF5EB;border-radius:999px;padding:3px 7px;}
.qa-live i{width:5px;height:5px;border-radius:50%;background:#14B8A6;box-shadow:0 0 0 3px rgba(20,184,166,.14);}
.qa-chat-sub{font-size:9.5px;color:var(--muted);margin-top:4px;line-height:1.5;}
.qa-chat-tools{display:flex;align-items:center;gap:7px;}
.qa-tool{
  display:inline-flex;align-items:center;gap:5px;padding:7px 10px;border-radius:9px;
  background:#F3F7FE;color:#3D4D68;font-size:9.5px;font-weight:750;text-decoration:none;
  border:1px solid #E4EDFA;transition:all .16s ease;white-space:nowrap;
}
.qa-tool:hover{color:var(--primary);background:#EAF2FF;border-color:#CBDDF7;}
.qa-tool.ghost{background:#fff;}
.qa-stream{display:flex;flex-direction:column;gap:16px;padding-bottom:4px;}
.qa-chat-foot{
  display:flex;align-items:flex-start;gap:6px;margin-top:14px;padding-top:11px;
  border-top:1px dashed #E9EFF9;font-size:9px;line-height:1.6;color:var(--muted-light);
}
.qa-chat-foot svg{flex:0 0 auto;margin-top:1px;}

/* 欢迎态 */
.qa-welcome{padding:10px 4px 18px;text-align:center;}
.qa-welcome-badge{
  width:66px;height:66px;border-radius:20px;display:grid;place-items:center;margin:0 auto 15px;
  background:linear-gradient(140deg,#E9F1FF,#ECFDF9);color:var(--primary);
  box-shadow:inset 0 0 0 1px #E3EDFB;
}
.qa-welcome h2{margin:0 0 8px;font-size:21px;font-weight:840;letter-spacing:-.02em;color:var(--ink);}
.qa-welcome p{margin:0 auto;max-width:520px;font-size:11.5px;line-height:1.9;color:var(--muted);}
.qa-welcome-points{display:flex;flex-wrap:wrap;gap:7px;justify-content:center;margin:16px 0 14px;}
.qa-welcome-points span{
  display:inline-flex;align-items:center;gap:5px;padding:6px 10px;border-radius:999px;
  background:#F7FAFF;border:1px solid #E6EEFA;font-size:9.5px;font-weight:700;color:#43536E;
}
.qa-welcome-note{font-size:9.5px;color:var(--muted-light);}

/* 气泡补充 */
.qa-chat .chat-row{gap:11px;}
.qa-chat .bubble-ai{max-width:calc(100% - 46px);border-radius:6px 18px 18px 18px;}
.qa-chat .bubble-user{border-radius:18px 18px 5px 18px;font-size:12.5px;}
.qa-ans-head{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-bottom:7px;}
.qa-ans-head .answer-title{font-size:15.5px;font-weight:830;margin:0;}
.qa-ans-head .pill{font-size:9px;padding:4px 8px;}
.qa-ans-context{
  display:inline-flex;align-items:center;gap:4px;padding:4px 8px;border-radius:999px;
  background:#ECFDF9;color:#0F7668;border:1px solid #CBF5EB;font-size:9px;font-weight:750;
}
.qa-ans-foot{
  display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:11px;padding-top:9px;
  border-top:1px dashed #E5EBF5;font-size:8.8px;color:var(--muted-light);
}
.qa-ans-foot b{color:#7C8AA5;font-weight:750;}

/* 附件：列表 / 时间线 */
.qa-attach{margin-top:12px;border:1px solid #E6EEFA;border-radius:14px;background:#fff;overflow:hidden;}
.qa-attach-head{
  display:flex;align-items:center;justify-content:space-between;gap:8px;
  padding:9px 12px;background:#F7FAFF;border-bottom:1px solid #EDF2FA;
  font-size:10px;font-weight:800;color:#43536E;
}
.qa-attach-head a{color:var(--primary);font-size:9px;font-weight:750;text-decoration:none;display:inline-flex;align-items:center;gap:3px;}
.qa-attach-item{
  display:flex;align-items:flex-start;gap:10px;padding:10px 12px;
  border-bottom:1px dashed #EDF2FA;text-decoration:none;color:inherit;transition:background .15s ease;
}
.qa-attach-item:last-child{border-bottom:0;}
.qa-attach-item:hover{background:#F9FBFF;}
.qa-attach-ico{width:29px;height:29px;border-radius:9px;display:grid;place-items:center;flex:0 0 auto;}
.qa-attach-body{min-width:0;flex:1;}
.qa-attach-title{display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:11px;font-weight:750;color:var(--ink);line-height:1.45;}
.qa-attach-meta{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-top:3px;font-size:8.8px;color:var(--muted);}
.qa-attach-meta svg{flex:0 0 auto;}
.qa-attach-meta span{display:inline-flex;align-items:center;gap:3px;}
.qa-attach-desc{margin-top:4px;font-size:9.5px;line-height:1.65;color:var(--ink-soft);}
.qa-money{font-size:10px;font-weight:800;color:#B7790B;background:var(--gold-soft);padding:2px 6px;border-radius:6px;white-space:nowrap;}
.qa-tag{display:inline-flex;align-items:center;gap:3px;padding:2px 6px;border-radius:5px;font-size:8px;font-weight:750;background:var(--primary-soft);color:var(--primary);white-space:nowrap;}
.qa-tag.teal{background:var(--teal-soft);color:#0F9488;}
.qa-tag.gold{background:var(--gold-soft);color:#B7790B;}
.qa-tag.violet{background:var(--violet-soft);color:var(--violet);}
.qa-tag.rose{background:var(--rose-soft);color:var(--rose);}
.qa-tag.red{background:#FEF2F2;color:#B91C1C;}
.qa-tag.gray{background:#F3F6FA;color:var(--muted);}
.qa-attach-more{display:flex;align-items:center;gap:5px;padding:8px 12px;background:#FBFCFF;font-size:9px;color:var(--muted);text-decoration:none;}
.qa-attach-more:hover{color:var(--primary);}

/* 时间线（大学四年规划） */
.qa-plan{display:flex;flex-direction:column;}
.qa-plan-item{display:flex;gap:10px;padding:9px 12px;border-bottom:1px dashed #EDF2FA;}
.qa-plan-item:last-child{border-bottom:0;}
.qa-plan-step{
  width:38px;height:24px;border-radius:7px;display:grid;place-items:center;flex:0 0 auto;
  font-size:9.5px;font-weight:800;background:var(--primary-soft);color:var(--primary);
}
.qa-plan-step.teal{background:var(--teal-soft);color:#0F9488;}
.qa-plan-step.gold{background:var(--gold-soft);color:#B7790B;}
.qa-plan-step.violet{background:var(--violet-soft);color:var(--violet);}
.qa-plan-title{font-size:10.5px;font-weight:750;color:var(--ink);}
.qa-plan-desc{font-size:9.3px;line-height:1.6;color:var(--muted);margin-top:2px;}

/* 引用来源 */
.qa-cite{margin-top:12px;border:1px solid #E6EEFA;border-radius:13px;background:#fff;overflow:hidden;}
.qa-cite summary{
  display:flex;align-items:center;gap:7px;padding:9px 12px;cursor:pointer;list-style:none;
  font-size:10px;font-weight:800;color:#3D4D68;background:#FBFCFF;
}
.qa-cite summary::-webkit-details-marker{display:none;}
.qa-cite summary .qa-cite-arrow{margin-left:auto;color:#9AA9C0;transition:transform .18s ease;}
.qa-cite[open] summary .qa-cite-arrow{transform:rotate(180deg);}
.qa-cite[open] summary{border-bottom:1px solid #EDF2FA;}
.qa-cite-item{padding:10px 12px;border-bottom:1px dashed #EDF2FA;}
.qa-cite-item:last-child{border-bottom:0;}
.qa-cite-title{display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:10.5px;font-weight:780;color:var(--primary);}
.qa-cite-meta{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-top:4px;font-size:8.6px;color:var(--muted-light);}
.qa-cite-quote{
  margin:7px 0 0;padding:7px 10px;border-left:2px solid #BFD4F5;background:#F7FAFF;
  border-radius:0 8px 8px 0;font-size:9.5px;line-height:1.75;color:#43536E;
}
.qa-cite-quote b{display:block;font-size:8.5px;color:#7C8AA5;font-weight:750;margin-bottom:2px;}
.qa-cite-link{display:inline-flex;align-items:center;gap:3px;margin-top:6px;font-size:8.6px;color:var(--primary);text-decoration:none;font-weight:750;}
.qa-cite-link:hover{text-decoration:underline;}

/* 检索轨迹 */
.qa-trace{margin-top:8px;border:1px solid #EDF2FA;border-radius:11px;background:#FCFDFF;overflow:hidden;}
.qa-trace summary{display:flex;align-items:center;gap:6px;padding:7px 11px;cursor:pointer;list-style:none;font-size:9px;font-weight:750;color:#7C8AA5;}
.qa-trace summary::-webkit-details-marker{display:none;}
.qa-trace-row{display:flex;align-items:center;gap:8px;padding:6px 11px;border-top:1px dashed #EFF3FA;}
.qa-trace-title{font-size:9px;color:#43536E;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.qa-trace-score{width:56px;height:4px;border-radius:99px;background:#EDF2FA;overflow:hidden;flex:0 0 auto;}
.qa-trace-score i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,#2563EB,#14B8A6);}
.qa-trace-pct{font-size:8px;color:#9AA9C0;width:26px;text-align:right;font-variant-numeric:tabular-nums;}
.qa-trace-src{font-size:7.5px;padding:1px 5px;border-radius:4px;background:#F1F5FB;color:#7C8AA5;flex:0 0 auto;}

/* 回答链接 */
.qa-chat .answer-links a{font-size:9.5px;padding:6px 9px;border-radius:8px;}

/* ---------- 继续追问 ---------- */
.st-key-qa-follow{margin-top:2px;}
.qa-follow-head{display:flex;align-items:center;gap:6px;font-size:9px;font-weight:800;letter-spacing:.08em;color:var(--muted);text-transform:uppercase;padding:2px 4px 7px;}
.st-key-qa-follow [data-testid="stHorizontalBlock"]{gap:8px;}
.st-key-qa-follow [data-testid="stButton"]>button{
  width:100%;border-radius:999px;background:#F2F7FF;border:1px solid #DCE8FB;color:var(--primary);
  font-size:9.5px;font-weight:750;padding:7px 10px;min-height:34px;white-space:normal;line-height:1.45;
}
.st-key-qa-follow [data-testid="stButton"]>button:hover{background:#E7F0FF;border-color:#BFD4F5;}

/* ---------- 输入条 ---------- */
.st-key-qa-composer{margin-top:0;}
.st-key-qa-composer [data-testid="stForm"]{
  border:1px solid var(--border-strong);border-radius:17px;background:#fff;
  padding:5px 6px 5px 13px;box-shadow:var(--shadow-sm);transition:border-color .18s ease,box-shadow .18s ease;
}
.st-key-qa-composer [data-testid="stForm"]:focus-within{border-color:#A9C6F2;box-shadow:0 12px 30px rgba(29,78,216,.12);}
/* 输入框与发送按钮排成一行：输入框自适应宽度，按钮固定 94px。
   注意不能对按钮用绝对定位——Streamlit 的提交按钮容器宽度会塌成 16px，
   right:7px 会相对这个窄容器计算，导致按钮飘到输入条外面。 */
.st-key-qa-composer [data-testid="stForm"] [data-testid="stVerticalBlock"]{
  display:flex;flex-direction:row;align-items:center;gap:7px;
}
.st-key-qa-composer [data-testid="stForm"] .st-key-qa-composer-input{flex:1 1 auto;min-width:0;}
.st-key-qa-composer [data-testid="stForm"] [class*="st-key-FormSubmitter"]{flex:0 0 94px;width:94px;}
.st-key-qa-composer [data-testid="stForm"] [class*="st-key-FormSubmitter"]>div{width:100%;}
.st-key-qa-composer [data-testid="stForm"] [data-testid="stTextInput"]{margin:0;}
.st-key-qa-composer [data-testid="stForm"] [data-testid="stTextInput"]>div{border:0!important;background:transparent!important;box-shadow:none!important;}
.st-key-qa-composer [data-testid="stForm"] input{
  border:0!important;box-shadow:none!important;background:transparent!important;
  height:44px;font-family:var(--font);font-size:12.5px;color:var(--ink);padding:0 4px;
}
.st-key-qa-composer [data-testid="stForm"] input::placeholder{color:#A6B3C8;}
.st-key-qa-composer [data-testid="stForm"] [data-testid="stFormSubmitButton"]{
  position:static;transform:none;width:100%;margin:0;
}
.st-key-qa-composer [data-testid="stForm"] [data-testid="stFormSubmitButton"]>button{
  width:100%;border:0;border-radius:11px;padding:10px 12px;min-height:38px;
  background:linear-gradient(135deg,#1D4ED8,#2563EB);color:#fff;font-size:11px;font-weight:750;
  box-shadow:0 7px 16px rgba(29,78,216,.24);display:inline-flex;align-items:center;justify-content:center;gap:5px;
}
.st-key-qa-composer [data-testid="stForm"] [data-testid="stFormSubmitButton"]>button:hover{background:linear-gradient(135deg,#1B45C4,#1F5AE0);color:#fff;}
.qa-composer-note{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;padding:8px 4px 0;font-size:8.8px;color:var(--muted-light);}
.qa-composer-note span{display:inline-flex;align-items:center;gap:4px;}

/* ---------- 右侧卡片（组件容器） ---------- */
.st-key-qa-upload,.st-key-qa-search,.st-key-qa-faq{
  background:#fff;border:1px solid var(--border);border-radius:20px;
  padding:16px 17px;box-shadow:var(--shadow-xs);
}
.qa-card-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:11px;}
.qa-card-title{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:820;color:var(--ink);letter-spacing:-.01em;}
.qa-card-title .qa-card-ico{width:29px;height:29px;border-radius:9px;display:grid;place-items:center;background:var(--primary-soft);color:var(--primary);}
.qa-card-sub{font-size:9px;color:var(--muted);margin-top:4px;padding-left:37px;line-height:1.5;}
.qa-card-count{font-size:8.5px;font-weight:750;color:var(--primary);background:var(--primary-soft);padding:3px 7px;border-radius:999px;white-space:nowrap;}

/* 上传 */
.st-key-qa-upload [data-testid="stFileUploader"]{margin-top:2px;}
.st-key-qa-upload [data-testid="stFileUploader"] section{
  border:1px dashed #C9DAF9;border-radius:14px;background:#F8FAFF;padding:13px 14px;
}
.st-key-qa-upload [data-testid="stFileUploader"] section:hover{border-color:#A9C6F2;background:#F4F9FF;}
.st-key-qa-upload [data-testid="stFileUploader"] section svg{color:var(--primary);}
.st-key-qa-upload [data-testid="stFileUploader"] section small,
.st-key-qa-upload [data-testid="stFileUploader"] section span,
.st-key-qa-upload [data-testid="stFileUploader"] section div{font-size:9.5px;color:var(--muted);}
.st-key-qa-upload [data-testid="stFileUploader"] button{
  border-radius:9px;border:1px solid #D6E3F6;background:#fff;color:var(--primary);
  font-size:9.5px;font-weight:750;padding:6px 10px;min-height:30px;
}
.st-key-qa-upload [data-testid="stFileUploader"] button:hover{background:#EAF2FF;border-color:#BFD4F5;}
.qa-upload-hint{display:flex;align-items:flex-start;gap:6px;margin-top:9px;font-size:8.8px;line-height:1.6;color:var(--muted-light);}
.qa-upload-hint svg{flex:0 0 auto;margin-top:1px;}
.qa-upload-msg{margin-top:9px;padding:8px 10px;border-radius:9px;font-size:9px;line-height:1.6;}
.qa-upload-msg.ok{background:#ECFDF3;border:1px solid #C9F2D8;color:#15803D;}
.qa-upload-msg.bad{background:#FEF2F2;border:1px solid #FBD5D5;color:#B91C1C;}
.qa-doc-row{padding:9px 0;border-bottom:1px dashed #EDF2FA;}
.qa-doc-row:last-of-type{border-bottom:0;}
.qa-doc-name{display:flex;align-items:center;gap:6px;font-size:10px;font-weight:750;color:var(--ink);overflow-wrap:anywhere;}
.qa-doc-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:3px;font-size:8.5px;color:var(--muted);}
.st-key-qa-upload [data-testid="stButton"]>button{
  border:1px solid #E4EDFA;background:#fff;color:var(--muted);font-size:8.5px;
  padding:3px 8px;min-height:26px;border-radius:7px;font-weight:700;
}
.st-key-qa-upload [data-testid="stButton"]>button:hover{color:var(--rose);border-color:#F4CBDA;background:#FFF5F8;}
.qa-sample-row{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:9px;font-size:8.5px;color:var(--muted-light);}

/* 检索 */
.st-key-qa-search [data-testid="stForm"]{border:0;padding:0;box-shadow:none;background:transparent;}
.st-key-qa-search [data-testid="stTextInput"] input{
  border-radius:11px;border:1px solid var(--border);background:#F8FAFF;height:38px;
  font-size:10.5px;font-family:var(--font);color:var(--ink);padding:0 12px;
}
.st-key-qa-search [data-testid="stTextInput"] input::placeholder{color:#A6B3C8;}
.st-key-qa-search [data-testid="stTextInput"]>div{border:0!important;background:transparent!important;box-shadow:none!important;}
.st-key-qa-search [data-testid="stFormSubmitButton"]>button{
  width:100%;margin-top:7px;border-radius:9px;border:1px solid #DCE8FB;background:#F2F7FF;
  color:var(--primary);font-size:9.5px;font-weight:750;min-height:32px;padding:5px 10px;
}
.st-key-qa-search [data-testid="stFormSubmitButton"]>button:hover{background:#E7F0FF;border-color:#BFD4F5;color:var(--primary);}
.qa-kb-row{
  display:flex;align-items:flex-start;gap:8px;padding:9px 0;border-bottom:1px dashed #EDF2FA;
}
.qa-kb-row:last-of-type{border-bottom:0;}
.qa-kb-body{min-width:0;flex:1;}
.qa-kb-title{font-size:9.8px;font-weight:750;color:var(--ink);line-height:1.45;}
.qa-kb-title:hover{color:var(--primary);}
.qa-kb-snippet{font-size:8.5px;line-height:1.6;color:var(--muted);margin-top:3px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.qa-kb-meta{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:4px;font-size:8px;color:var(--muted-light);}
.qa-kb-score{width:40px;height:3px;border-radius:99px;background:#EDF2FA;overflow:hidden;flex:0 0 auto;}
.qa-kb-score i{display:block;height:100%;background:linear-gradient(90deg,#2563EB,#14B8A6);}
.st-key-qa-search [data-testid="stHorizontalBlock"]{gap:6px;align-items:center;}
.st-key-qa-search [data-testid="stButton"]>button{
  border-radius:7px;border:1px solid #DCE8FB;background:#F7FAFF;color:var(--primary);
  font-size:8px;font-weight:750;padding:3px 6px;min-height:25px;white-space:nowrap;
}
.st-key-qa-search [data-testid="stButton"]>button:hover{background:var(--primary);color:#fff;border-color:transparent;}
.qa-kb-empty{font-size:9px;line-height:1.7;color:var(--muted-light);padding:6px 0;}

/* FAQ */
.st-key-qa-faq [data-testid="stHorizontalBlock"]{gap:7px;}
.st-key-qa-faq [data-testid="stColumn"]{min-width:0;}
.st-key-qa-faq [data-testid="stButton"]>button{
  width:100%;border-radius:9px;border:1px solid #E8EEF9;background:#FBFCFE;color:#3D4D68;
  font-size:8.8px;font-weight:700;padding:7px 8px;min-height:42px;line-height:1.45;
  white-space:normal;text-align:left;justify-content:flex-start;
}
.st-key-qa-faq [data-testid="stButton"]>button:hover{background:#F3F8FF;border-color:#C9DAF9;color:var(--primary);}
.qa-faq-group{font-size:8.5px;font-weight:800;letter-spacing:.1em;color:var(--muted-light);text-transform:uppercase;padding:7px 2px 5px;}

/* ---------- 全宽区块 ---------- */
.qa-doclib{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px;}
.qa-doc{border:1px solid var(--border);border-radius:15px;background:#fff;overflow:hidden;scroll-margin-top:16px;}
.qa-doc summary{
  display:flex;align-items:center;gap:8px;padding:11px 13px;cursor:pointer;list-style:none;
  font-size:10.5px;font-weight:750;color:var(--ink);line-height:1.45;
}
.qa-doc summary::-webkit-details-marker{display:none;}
.qa-doc[open] summary{border-bottom:1px solid #EDF2FA;background:#FBFCFF;}
.qa-doc-cat{font-size:7.8px;font-weight:800;padding:2px 6px;border-radius:5px;background:var(--primary-soft);color:var(--primary);flex:0 0 auto;}
.qa-doc-title{flex:1;min-width:0;}
.qa-doc-no{font-size:8px;color:var(--muted-light);flex:0 0 auto;}
.qa-doc-arrow{color:#9AA9C0;flex:0 0 auto;transition:transform .18s ease;}
.qa-doc[open] .qa-doc-arrow{transform:rotate(180deg);}
.qa-doc-body{padding:10px 13px 12px;}
.qa-doc-meta{font-size:8.3px;color:var(--muted-light);line-height:1.6;}
.qa-doc-summary{margin:6px 0 8px;font-size:9.3px;line-height:1.7;color:var(--ink-soft);}
.qa-clause{display:flex;gap:7px;padding:5px 0;border-top:1px dashed #EFF3FA;font-size:9px;line-height:1.7;color:#43536E;}
.qa-clause b{color:var(--primary);font-weight:750;flex:0 0 auto;white-space:nowrap;}
.qa-tips{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px;}
.qa-tip-card{
  background:#fff;border:1px solid var(--border);border-radius:17px;padding:15px 16px;
  box-shadow:var(--shadow-xs);
}
.qa-tip-title{display:flex;align-items:center;gap:8px;font-size:11.5px;font-weight:800;color:var(--ink);}
.qa-tip-title .qa-tip-ico{width:28px;height:28px;border-radius:9px;display:grid;place-items:center;flex:0 0 auto;}
.qa-tip-desc{margin-top:8px;font-size:9.5px;line-height:1.7;color:var(--muted);}

/* 空状态兜底 */
.qa-missing{padding:26px 22px;text-align:center;background:#fff;border:1px dashed #DDE6F2;border-radius:18px;font-size:11px;color:var(--muted);}

/* ---------- 响应式 ---------- */
@media (max-width:1180px){
  .qa-doclib{grid-template-columns:1fr;}
  .qa-tips{grid-template-columns:1fr;}
}
@media (max-width:1024px){
  .st-key-qa-main > div > [data-testid="stHorizontalBlock"]{flex-wrap:wrap;}
  .st-key-qa-main > div > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{
    flex:1 1 100%!important;width:100%!important;min-width:100%!important;
  }
  .st-key-qa-quick [data-testid="stHorizontalBlock"]{flex-wrap:wrap;}
  .st-key-qa-quick [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{
    flex:1 1 30%!important;min-width:150px!important;
  }
  .qa-welcome p{max-width:100%;}
}
@media (max-width:760px){
  .st-key-qa-quick [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{flex:1 1 46%!important;min-width:132px!important;}
  .qa-chat{padding:15px 13px 9px;border-radius:19px;}
  .qa-chat-head{gap:9px;}
  .qa-chat-name{font-size:13px;}
  .qa-chat-tools{width:100%;justify-content:flex-end;}
  .qa-chat .bubble-ai{max-width:100%;padding:14px;}
  .qa-chat .bubble-user{max-width:88%;}
  .qa-chat .chat-row{gap:8px;}
  .qa-doclib{grid-template-columns:1fr;}
  .st-key-qa-quick{padding:14px 13px 12px;}
  .st-key-qa-composer [data-testid="stForm"]{padding:5px 6px 5px 11px;}
  .st-key-qa-composer [data-testid="stForm"] [class*="st-key-FormSubmitter"]{flex:0 0 74px;width:74px;}
  .st-key-qa-composer [data-testid="stForm"] [data-testid="stFormSubmitButton"]{width:100%;}
}

/* ==========================================================================
   工作台重排（对话优先）
   打开页面第一眼就是对话框；功能导航围绕在对话框右侧、上方与输入条周围。
   长内容（上传 / 检索 / FAQ / 制度库 / 帮助）用 ?page=qa&view=xxx 独立页面承载。
   ========================================================================== */

/* ---------- 主布局：左对话 + 右工作台 ---------- */
.st-key-qa-main{padding:0;}
.st-key-qa-main [data-testid="stHorizontalBlock"]{gap:18px;align-items:stretch;}
.st-key-qa-main > div > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{min-width:0;}
.st-key-qa-chatcol{min-width:0;height:100%;}
.st-key-qa-rail{min-width:0;}

/* ---------- 对话卡片：内部滚动，输入条始终可见 ---------- */
.qa-chat{
  padding:18px 18px 10px;border-radius:24px;
  display:flex;flex-direction:column;min-height:100%;
}
.qa-chat-head{padding-bottom:12px;margin-bottom:12px;}
.qa-chat-avatar{width:39px;height:39px;border-radius:12px;}
.qa-chat-name{font-size:13.5px;}
.qa-chat-sub{font-size:9px;margin-top:3px;}
.qa-chat .qa-stream{
  max-height:min(56vh,560px);overflow-y:auto;overscroll-behavior:contain;
  padding:2px 6px 2px 2px;scrollbar-width:thin;scrollbar-color:#D7E2F2 transparent;
}
.qa-chat .qa-stream.empty{
  min-height:314px;justify-content:center;overflow:visible;max-height:none;
}
.qa-chat .qa-stream::-webkit-scrollbar{width:6px;}
.qa-chat .qa-stream::-webkit-scrollbar-thumb{background:#D7E2F2;border-radius:99px;border:0;}
.qa-chat .qa-stream::-webkit-scrollbar-track{background:transparent;}

/* ---------- 首屏欢迎语：大标题 + 一句解释 ---------- */
.qa-welcome{padding:30px 16px 22px;text-align:center;}
.qa-welcome-badge{
  width:62px;height:62px;border-radius:19px;margin-bottom:18px;
  background:linear-gradient(140deg,#E9F1FF,#ECFDF9);color:var(--primary);
  box-shadow:inset 0 0 0 1px #E3EDFB,0 14px 30px rgba(29,78,216,.09);
}
.qa-welcome h1{
  margin:0 0 13px;font-size:clamp(28px,3.4vw,41px);line-height:1.18;
  font-weight:860;letter-spacing:-.045em;color:var(--ink);
}
.qa-welcome h1 span{
  background:linear-gradient(95deg,#1D4ED8 0%,#0EA5A4 62%,#B7790B 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent;
}
.qa-welcome p{
  margin:0 auto;max-width:620px;font-size:13px;line-height:1.95;color:var(--muted);
}
.qa-welcome-points{display:flex;flex-wrap:wrap;gap:7px;justify-content:center;margin:19px 0 2px;}
.qa-welcome-points span{
  display:inline-flex;align-items:center;gap:5px;padding:6px 10px;border-radius:999px;
  background:#F7FAFF;border:1px solid #E6EEFA;font-size:9.3px;font-weight:700;color:#43536E;
}

/* ---------- 首屏快捷问题：紧凑胶囊按钮 ---------- */
.st-key-qa-quick{
  background:transparent;border:0;border-radius:0;padding:0;box-shadow:none;
  margin-top:2px;
}
.st-key-qa-quick .qa-quick-head{
  display:flex;align-items:center;justify-content:space-between;gap:10px;
  margin:0 2px 8px;padding:0;
}
.st-key-qa-quick .qa-quick-eyebrow{display:inline-flex;align-items:center;gap:5px;font-size:9px;font-weight:800;letter-spacing:.14em;color:var(--primary);text-transform:uppercase;}
.st-key-qa-quick .qa-quick-sub{font-size:8.8px;color:var(--muted-light);white-space:nowrap;}
.st-key-qa-quick [data-testid="stHorizontalBlock"]{gap:8px;flex-wrap:wrap;align-items:stretch;}
.st-key-qa-quick [data-testid="stColumn"]{flex:1 1 150px;min-width:120px;}
.st-key-qa-quick [data-testid="stButton"]>button{
  width:100%;text-align:left;justify-content:flex-start;border-radius:11px;
  padding:9px 11px;min-height:42px;font-size:10.8px;font-weight:750;line-height:1.45;
  color:var(--ink);background:#fff;border:1px solid #DDE8F8;white-space:normal;
  box-shadow:0 2px 8px rgba(15,27,51,.03);
}
.st-key-qa-quick [data-testid="stButton"]>button:hover{
  border-color:#B9D0F3;background:#F6FAFF;color:var(--primary);transform:translateY(-1px);
}

/* ---------- 输入条周围的快捷功能导航 ---------- */
.qa-composer-tools{
  display:flex;align-items:center;gap:6px;flex-wrap:wrap;
  padding:12px 2px 7px;
}
.qa-composer-tools .qa-ct-label{
  display:inline-flex;align-items:center;gap:4px;font-size:8.5px;font-weight:800;
  letter-spacing:.1em;color:var(--muted-light);text-transform:uppercase;margin-right:2px;
}
.qa-composer-tools a{
  display:inline-flex;align-items:center;gap:4px;padding:5px 9px;border-radius:999px;
  background:#fff;border:1px solid #E3EBF8;color:#4A5873;font-size:9px;font-weight:750;
  text-decoration:none;transition:all .16s ease;white-space:nowrap;
}
.qa-composer-tools a:hover{color:var(--primary);border-color:#BCD1F1;background:#F7FAFF;}

/* ---------- 右侧工作台 ---------- */
.st-key-qa-rail{display:flex;flex-direction:column;gap:11px;}
.qa-rail-card{
  background:#fff;border:1px solid var(--border);border-radius:19px;
  padding:14px 14px 12px;box-shadow:var(--shadow-xs);
}
.qa-rail-head{display:flex;align-items:flex-start;justify-content:space-between;gap:8px;margin-bottom:10px;}
.qa-rail-title{display:flex;align-items:center;gap:7px;font-size:12.5px;font-weight:820;color:var(--ink);letter-spacing:-.01em;}
.qa-rail-title .qa-rail-ico{
  width:27px;height:27px;border-radius:8px;display:grid;place-items:center;flex:0 0 auto;
  background:var(--primary-soft);color:var(--primary);
}
.qa-rail-sub{font-size:8.5px;color:var(--muted);margin-top:4px;padding-left:34px;line-height:1.5;}
.qa-rail-tag{
  display:inline-flex;align-items:center;gap:4px;padding:4px 7px;border-radius:999px;
  background:#ECFDF9;color:#0F766E;border:1px solid #CBF5EB;font-size:8px;font-weight:750;white-space:nowrap;
}
.qa-wb-nav{display:flex;flex-direction:column;gap:5px;}
.qa-wb-item{
  display:flex;align-items:center;gap:9px;padding:8px 8px;border-radius:11px;
  border:1px solid transparent;text-decoration:none;color:inherit;transition:all .16s ease;
}
.qa-wb-item:hover{background:#F7FAFF;border-color:#E3ECFA;transform:translateX(1px);}
.qa-wb-ico{
  width:30px;height:30px;border-radius:9px;display:grid;place-items:center;flex:0 0 auto;
  background:var(--primary-soft);color:var(--primary);
}
.qa-wb-item.t-teal .qa-wb-ico{background:var(--teal-soft);color:#0F9488;}
.qa-wb-item.t-gold .qa-wb-ico{background:var(--gold-soft);color:#B7790B;}
.qa-wb-item.t-violet .qa-wb-ico{background:var(--violet-soft);color:var(--violet);}
.qa-wb-item.t-green .qa-wb-ico{background:#ECFDF3;color:#15803D;}
.qa-wb-copy{min-width:0;flex:1;}
.qa-wb-copy b{display:block;font-size:10.6px;font-weight:780;color:var(--ink);line-height:1.3;}
.qa-wb-copy small{display:block;font-size:8.2px;color:var(--muted);margin-top:2px;line-height:1.45;}
.qa-wb-badge{
  font-size:7.8px;font-weight:800;padding:3px 6px;border-radius:999px;
  background:#F3F6FA;color:var(--muted);white-space:nowrap;flex:0 0 auto;
}
.qa-wb-arrow{color:#B6C4DA;flex:0 0 auto;}
.qa-wb-stats{display:grid;grid-template-columns:1fr 1fr;gap:6px;}
.qa-wb-stat{background:#F8FAFF;border:1px solid #EDF2FA;border-radius:9px;padding:7px 8px;}
.qa-wb-stat b{display:block;font-size:14px;font-weight:840;color:var(--ink);line-height:1.1;letter-spacing:-.02em;}
.qa-wb-stat span{display:block;font-size:7.8px;color:var(--muted);margin-top:3px;line-height:1.3;}
.qa-wb-note{
  display:flex;align-items:flex-start;gap:5px;margin-top:9px;padding-top:8px;
  border-top:1px dashed #EDF2FA;font-size:8.2px;line-height:1.55;color:var(--muted-light);
}
.qa-wb-note svg{flex:0 0 auto;margin-top:1px;}
.st-key-qa-rail-ask{
  background:#fff;border:1px solid var(--border);border-radius:19px;
  padding:14px 14px 12px;box-shadow:var(--shadow-xs);
}
.st-key-qa-rail-ask [data-testid="stButton"]>button{
  width:100%;text-align:left;justify-content:flex-start;border-radius:9px;
  border:1px solid #E8EEF9;background:#FBFCFE;color:#3D4D68;
  font-size:8.9px;font-weight:700;padding:7px 9px;min-height:35px;
  line-height:1.45;white-space:normal;margin-bottom:2px;
}
.st-key-qa-rail-ask [data-testid="stButton"]>button:hover{
  background:#F3F8FF;border-color:#C9DAF9;color:var(--primary);
}

/* ---------- 移动端：工作台导航横向滚动 ---------- */
.qa-mobile-tools{display:none;}
@media (max-width:1024px){
  .qa-mobile-tools{
    display:flex;align-items:center;gap:6px;overflow-x:auto;
    margin:0 0 12px;padding:0 1px 5px;scrollbar-width:none;
  }
  .qa-mobile-tools::-webkit-scrollbar{display:none;}
  .qa-mobile-tools a{
    display:inline-flex;align-items:center;gap:4px;flex:0 0 auto;
    padding:7px 10px;border-radius:999px;background:#fff;border:1px solid var(--border);
    color:#4A5873;font-size:9.5px;font-weight:700;text-decoration:none;white-space:nowrap;
  }
  .qa-mobile-tools a:hover{color:var(--primary);border-color:#C9DAF9;}
  .qa-chat .qa-stream{max-height:62vh;}
}

/* ---------- 独立功能页（长内容） ---------- */
.qa-subpage-head{
  display:flex;align-items:flex-start;justify-content:space-between;gap:18px;
  background:#fff;border:1px solid var(--border);border-radius:20px;
  padding:17px 19px;margin-bottom:12px;box-shadow:var(--shadow-xs);
}
.qa-subpage-kicker{
  display:inline-flex;align-items:center;gap:5px;font-size:8.8px;font-weight:800;
  letter-spacing:.15em;color:var(--primary);text-transform:uppercase;
}
.qa-subpage-head h2{
  display:flex;align-items:center;gap:8px;margin:6px 0 4px;
  font-size:22px;font-weight:840;letter-spacing:-.025em;color:var(--ink);
}
.qa-subpage-head h2 svg{color:var(--primary);}
.qa-subpage-head p{margin:0;max-width:720px;font-size:11px;line-height:1.7;color:var(--muted);}
.qa-back{
  display:inline-flex;align-items:center;gap:5px;flex:0 0 auto;
  padding:8px 11px;border-radius:10px;background:var(--primary-soft);
  color:var(--primary);font-size:10.5px;font-weight:750;text-decoration:none;
  white-space:nowrap;transition:all .16s ease;
}
.qa-back:hover{background:#E4EEFF;gap:7px;}
.qa-subnav{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 14px;}
.qa-subnav a{
  padding:6px 10px;border-radius:999px;background:#fff;border:1px solid var(--border);
  font-size:9.5px;font-weight:700;color:var(--muted);text-decoration:none;transition:all .16s ease;
}
.qa-subnav a:hover{color:var(--primary);border-color:#C9DAF9;background:#F7FAFF;}
.qa-subnav a.active{background:linear-gradient(135deg,#1D4ED8,#2563EB);color:#fff;border-color:transparent;}
.qa-subpage-foot{margin-top:16px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;}
.qa-subpage-foot span{font-size:9px;color:var(--muted-light);line-height:1.6;}
@media (max-width:760px){
  .qa-subpage-head{flex-direction:column;gap:10px;padding:15px 14px;}
  .qa-subpage-head h2{font-size:19px;}
  .qa-welcome{padding:24px 10px 18px;}
  .qa-welcome h1{font-size:29px;}
  .qa-welcome p{font-size:12px;}
  .qa-chat .qa-stream{max-height:66vh;}
}
</style>
"""


# --------------------------------------------------------------------------- #
# 基础工具
# --------------------------------------------------------------------------- #
def _e(value) -> str:
    return ui.e(value)


def _render(markup: str) -> None:
    ui.render_html(markup)


def _qp(name: str) -> str:
    return ui.qp(name, "").strip()


def _one(name: str) -> str:
    return _qp(name)


def _seen() -> set:
    value = st.session_state.get("qa_seen_tokens")
    if not isinstance(value, set):
        value = set()
        st.session_state.qa_seen_tokens = value
    return value


def _policy_docs() -> list[dict]:
    docs = getattr(policy, "POLICY_DOCS", None) if policy else None
    return list(docs or [])


def _kb_count() -> int:
    extra = list(getattr(policy, "KB_EXTRA", None) or []) if policy else []
    return len(data.QA_KB) + len(extra)


def _quick_questions() -> list[dict]:
    items = getattr(policy, "QUICK_QUESTIONS", None) if policy else None
    if items:
        return list(items)
    # 兜底：即使政策模块未就绪，5 个快捷问题也必须存在且可提问
    fallback = [
        ("q-student-id", "学生证丢了怎么办？", "补办材料 + 办理地点", "id-card", "blue"),
        ("q-aid", "有哪些学生资助政策？", "奖助贷勤补全清单", "heart", "gold"),
        ("q-activities", "最近有哪些校园活动？", "本周可报名活动", "compass", "teal"),
        ("q-notices", "如何查询学校最新通知？", "官方渠道 + 订阅", "bell", "violet"),
        ("q-plan", "如何规划我的大学生活？", "四年成长路线", "graduation-cap", "rose"),
    ]
    return [
        {
            "id": qid,
            "label": label,
            "question": label,
            "hint": hint,
            "icon": icon_name,
            "tone": tone,
        }
        for qid, label, hint, icon_name, tone in fallback
    ]


def _faq_items() -> list[dict]:
    items = getattr(policy, "FAQ_RECOMMENDED", None) if policy else None
    if items:
        return list(items)
    return [{"question": q, "tag": "高频", "hot": i < 3} for i, q in enumerate(data.QA_SUGGESTIONS)]


def _sample_pdfs() -> list[str]:
    try:
        names = [n for n in os.listdir(_SAMPLES_DIR) if n.lower().endswith(".pdf")]
    except OSError:
        return []
    return sorted(names)


def _last_user_question() -> str:
    history = qa_history()
    if len(history) >= 2 and history[-2].get("role") == "user":
        return str(history[-2].get("content", "") or "")
    return ""


# --------------------------------------------------------------------------- #
# 问答动作
# --------------------------------------------------------------------------- #
def _ask(question: str, source: str = "widget") -> None:
    """把问题交给检索引擎，写入历史。"""
    question = str(question or "").strip()
    if not question:
        return
    history = qa_history()
    if history and history[-1].get("role") == "user" and history[-1].get("content") == question:
        return
    if kb is None:
        result = {
            "matched": False,
            "intent": "",
            "title": "问答引擎正在加载",
            "intro": "知识库模块尚未就绪，请稍后再试，或刷新页面。",
            "steps": [],
            "tip": "",
            "tone": "gray",
            "confidence": None,
            "citations": [],
            "links": [["查看办事流程", "?page=services"]],
            "attachments": [],
            "suggestions": [],
            "retrieval": [],
            "context_used": False,
            "raw_question": question,
            "elapsed_ms": 0,
        }
    else:
        try:
            result = kb.answer(question, history=history, uploads=qa_docs())
            if llm_qa is not None:
                try:
                    # 本地检索 + 大模型生成；API 异常时返回原始本地结果
                    result = llm_qa.enhance(question, history, result)
                except Exception:
                    pass
        except Exception as exc:  # pragma: no cover - 现场演示兜底
            result = {
                "matched": False,
                "intent": "",
                "title": "刚才没查到答案",
                "intro": "检索时遇到了一点小问题，请换个问法或稍后重试。",
                "steps": [],
                "tip": "",
                "tone": "rose",
                "confidence": None,
                "citations": [],
                "links": [["查看办事流程", "?page=services"]],
                "attachments": [],
                "suggestions": [item["question"] for item in _quick_questions()[:3]],
                "retrieval": [],
                "context_used": False,
                "raw_question": question,
                "elapsed_ms": 0,
            }
            try:
                st.session_state.qa_last_error = str(exc)[:300]
            except Exception:
                pass
    append_qa(question, result)
    st.session_state.qa_scroll_pending = True


def _ask_from_item(item: dict) -> None:
    question = str(item.get("question") or item.get("title") or "").strip()
    if question:
        _ask(question, source="kb")


def _return_to_chat() -> None:
    """从独立功能页回到对话框。

    直接把查询参数重置为 ``?page=qa``；若浏览器 / Streamlit 版本不支持在
    回调里改 query params，则退化为一次性忽略 view 参数，保证用户一定能
    看到刚刚生成的回答。
    """
    try:
        st.query_params.clear()
        st.query_params["page"] = "qa"
    except Exception:
        st.session_state.qa_view_override = True


def _ask_and_back(question: str) -> None:
    _ask(question, source="tool")
    _return_to_chat()


def _ask_from_item_and_back(item: dict) -> None:
    _ask_from_item(item)
    _return_to_chat()


def _new_session() -> None:
    qa_new_session()
    st.session_state.pop("qa_search_results", None)
    st.session_state.pop("qa_search_query", None)


def _remove_doc(doc_id: str) -> None:
    qa_remove_doc(doc_id)


def _ingest(name: str, payload: bytes, digest: str = "") -> None:
    """解析并登记一份上传资料。"""
    if not pdf_reader or not kb:
        st.session_state.qa_upload_error = "解析模块尚未就绪，请稍后重试。"
        return
    lower = name.lower()
    if lower.endswith(".pdf"):
        extracted = pdf_reader.extract(payload)
    else:
        text = pdf_reader.decode_text_file(payload)
        extracted = {
            "ok": bool(text.strip()),
            "engine": "none",
            "pages": [{"no": 1, "text": text}],
            "page_count": 1,
            "chars": len(text),
            "encrypted": False,
            "scanned": not bool(text.strip()),
            "warnings": [],
            "error": "" if text.strip() else "文件里没有可读取的文字内容。",
        }
    if not extracted.get("ok"):
        st.session_state.qa_upload_error = extracted.get("error") or "这个文件暂时无法解析。"
        return
    if extracted.get("scanned") or not extracted.get("chars"):
        st.session_state.qa_upload_error = "没有检测到文字层（可能是扫描件 / 图片版 PDF），暂时无法用于检索。"
        return
    doc = kb.make_upload(name, extracted)
    doc["size"] = len(payload)
    doc["digest"] = digest
    doc["scanned"] = bool(extracted.get("scanned"))
    qa_add_doc(doc)
    st.session_state.qa_upload_ok = f"已加入检索：{name}（{doc.get('pages', 0)} 页 · {doc.get('chars', 0)} 字）"
    st.session_state.pop("qa_upload_error", None)


def _ingest_sample(filename: str) -> None:
    path = os.path.join(_SAMPLES_DIR, filename)
    try:
        with open(path, "rb") as fh:
            payload = fh.read()
    except OSError:
        st.session_state.qa_upload_error = "示例文件读取失败。"
        return
    _ingest(filename, payload, digest="sample:" + filename)


# --------------------------------------------------------------------------- #
# 答案渲染
# --------------------------------------------------------------------------- #
def _tone_icon(name: str, tone: str, size: int = 15) -> str:
    background, color = _tone(tone)
    return (
        f'<span class="qa-attach-ico" style="background:{background};color:{color}">'
        f"{ui.icon(name, size)}</span>"
    )


def _safe_list(value) -> list:
    return [item for item in (value or []) if item]


def _pct(value) -> int:
    try:
        return max(0, min(99, int(round(float(value) * 100))))
    except (TypeError, ValueError):
        return 0


def _citation_html(citations: list[dict]) -> str:
    citations = _safe_list(citations)
    if not citations:
        return ""
    items = []
    for cite in citations[:4]:
        if not isinstance(cite, dict):
            continue
        source_type = str(cite.get("source_type") or "policy")
        title = str(cite.get("title") or cite.get("file") or "校内制度")
        doc_no = str(cite.get("doc_no") or "")
        department = str(cite.get("department") or "")
        issued = str(cite.get("issued") or "")
        clause = str(cite.get("clause") or "")
        excerpt = str(cite.get("excerpt") or "")
        status = str(cite.get("status") or "")
        if source_type == "upload":
            title = str(cite.get("file") or cite.get("title") or "上传资料")
            meta_bits = [f"第 {cite.get('page', 1)} 页", "上传资料"]
            highlight = f'<span class="qa-tag teal">{ui.icon("paperclip", 9)}个人资料</span>'
            anchor = ""
        else:
            meta_bits = [department, doc_no, f"{issued} 发布" if issued else "", status]
            highlight = f'<span class="qa-tag">{ui.icon("shield", 9)}校内制度</span>'
            doc_id = str(cite.get("doc_id") or "")
            anchor = (
                f'<a class="qa-cite-link" href="?page=qa&view=library#doc-{_e(doc_id)}">查看条款原文 {ui.icon("arrow-right", 9)}</a>'
                if doc_id
                else ""
            )
        meta = " · ".join([bit for bit in meta_bits if bit])
        quote = (
            f'<div class="qa-cite-quote"><b>{_e(clause) if clause else "条文摘录"}</b>{_e(excerpt)}</div>'
            if excerpt
            else ""
        )
        items.append(
            f"""
<div class="qa-cite-item">
  <div class="qa-cite-title">{highlight}<span>{_e(title)}</span></div>
  <div class="qa-cite-meta">{_e(meta)}</div>
  {quote}
  {anchor}
</div>
"""
        )
    if not items:
        return ""
    count = len(citations)
    return f"""
<details class="qa-cite">
  <summary>{ui.icon('bookmark', 13)}依据来源 · {count} 份材料<span class="qa-cite-arrow">{ui.icon('chevron-down', 12)}</span></summary>
  {"".join(items)}
</details>
"""


def _trace_html(retrieval: list[dict]) -> str:
    retrieval = [item for item in _safe_list(retrieval) if isinstance(item, dict)]
    if not retrieval:
        return ""
    source_labels = {
        "policy": "制度",
        "faq": "问答",
        "upload": "资料",
        "kb": "问答",
    }
    rows = []
    for item in retrieval[:5]:
        title = str(item.get("title") or "")
        score = _pct(item.get("score"))
        source = str(item.get("source") or "policy")
        source_label = source_labels.get(source, "知识")
        rows.append(
            f"""
<div class="qa-trace-row">
  <span class="qa-trace-src">{_e(source_label)}</span>
  <span class="qa-trace-title" title="{_e(title)}">{_e(title)}</span>
  <span class="qa-trace-score"><i style="width:{score}%"></i></span>
  <span class="qa-trace-pct">{score}%</span>
</div>
"""
        )
    return f"""
<details class="qa-trace">
  <summary>{ui.icon('database', 12)}知识库检索轨迹 · 命中 {len(retrieval)} 个片段<span class="qa-cite-arrow">{ui.icon('chevron-down', 11)}</span></summary>
  {"".join(rows)}
</details>
"""


def _attachment_html(attachments: list[dict]) -> str:
    blocks = []
    for att in _safe_list(attachments):
        if not isinstance(att, dict):
            continue
        kind = str(att.get("type") or "list")
        title = str(att.get("title") or "相关资料")
        items = [item for item in (att.get("items") or []) if isinstance(item, dict)]
        if not items:
            continue
        head = f"""
<div class="qa-attach-head">
  <span>{ui.icon('layers', 12)}{_e(title)}</span>
  <span style="font-weight:600;color:var(--muted-light)">{len(items)} 条</span>
</div>
"""
        if kind == "timeline":
            rows = []
            for item in items[:6]:
                tone = str(item.get("tone") or "blue")
                rows.append(
                    f"""
<div class="qa-plan-item">
  <span class="qa-plan-step {_e(tone)}">{_e(item.get('step') or '')}</span>
  <div style="min-width:0">
    <div class="qa-plan-title">{_e(item.get('title') or '')}</div>
    <div class="qa-plan-desc">{_e(item.get('desc') or '')}</div>
  </div>
</div>
"""
                )
            blocks.append(f'<div class="qa-attach">{head}<div class="qa-plan">{"".join(rows)}</div></div>')
            continue
        rows = []
        for item in items[:6]:
            tone = str(item.get("tone") or "blue")
            icon_name = str(item.get("icon") or "file-text")
            tags = []
            tag = str(item.get("tag") or "")
            if tag:
                tags.append(f'<span class="qa-tag {_e(tone) if tone != "blue" else ""}">{_e(tag)}</span>')
            amount = str(item.get("amount") or "")
            if amount:
                tags.append(f'<span class="qa-money">{_e(amount)}</span>')
            meta = str(item.get("meta") or "")
            href = str(item.get("href") or "")
            desc = str(item.get("desc") or "")
            inner = f"""
{_tone_icon(icon_name, tone)}
<div class="qa-attach-body">
  <div class="qa-attach-title">{_e(item.get('title') or '')}{"".join(tags)}</div>
  {f'<div class="qa-attach-meta">{_e(meta)}</div>' if meta else ''}
  {f'<div class="qa-attach-desc">{_e(desc)}</div>' if desc else ''}
</div>
{ui.icon('chevron-right', 12) if href else ''}
"""
            safe_href = ui.e(href) if href.startswith(("?", "/", "#", "http")) else "#"
            if href:
                rows.append(f'<a class="qa-attach-item" href="{safe_href}">{inner}</a>')
            else:
                rows.append(f'<div class="qa-attach-item">{inner}</div>')
        blocks.append(f'<div class="qa-attach">{head}<div>{"".join(rows)}</div></div>')
    return "".join(blocks)


def _answer_bubble(result) -> str:
    if isinstance(result, str):
        result = {"title": "河小智的回答", "intro": result}
    if not isinstance(result, dict):
        result = {"title": "河小智的回答", "intro": str(result)}
    title = str(result.get("title") or "河小智的回答")
    intro = str(result.get("intro") or "")
    # 大模型回答是带换行的纯文本：转义后把换行转成 <br>，
    # 既保留分段/分点排版，又不会出现原始 HTML 标签。
    intro_html = _e(intro).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
    steps = _safe_list(result.get("steps"))
    tip = str(result.get("tip") or "")
    tone = str(result.get("tone") or "blue")
    matched = bool(result.get("matched", True))
    confidence = result.get("confidence")
    intent_label = str(result.get("intent_label") or "")
    context_used = bool(result.get("context_used"))
    citations = _safe_list(result.get("citations"))
    retrieval = _safe_list(result.get("retrieval"))
    links = _safe_list(result.get("links"))
    attachments = _safe_list(result.get("attachments"))
    elapsed = result.get("elapsed_ms")
    source = str(result.get("source") or "")

    pills = []
    if intent_label:
        pills.append(f'<span class="pill {_e(tone)}">{ui.icon("target", 10)}{_e(intent_label)}</span>')
    if not matched:
        pills.append(f'<span class="pill gray">{ui.icon("alert-circle", 10)}未命中知识库</span>')
    elif isinstance(confidence, (int, float)) and _pct(confidence):
        pills.append(f'<span class="pill {_e(tone)}">{ui.icon("sparkle", 10)}匹配度 {_pct(confidence)}%</span>')
    if context_used:
        pills.append(f'<span class="qa-ans-context">{ui.icon("corner-down-right", 10)}结合上文</span>')
    if result.get("llm_used"):
        model_name = str(result.get("llm_model") or "")
        label = "AI 生成" + (f" · {model_name}" if model_name else "")
        pills.append(f'<span class="pill teal">{ui.icon("sparkles", 10)}{_e(label)}</span>')
    elif result.get("llm_error"):
        # API 配置有问题时给出可见提示，方便排查；回答本身仍是本地知识库结果
        pills.append(
            f'<span class="pill gray" title="{_e(result.get("llm_error"))}">'
            f'{ui.icon("alert-circle", 10)}API 未生效 · 本地回答</span>'
        )

    steps_html = ""
    if steps:
        rows = "".join(
            f'<div class="answer-step"><span class="step-num">{number}</span><span>{_e(step)}</span></div>'
            for number, step in enumerate(steps, 1)
        )
        steps_html = f'<div class="answer-steps">{rows}</div>'

    tip_html = (
        f'<div class="answer-tip">{ui.icon("sparkles", 12)}<span>{_e(tip)}</span></div>'
        if tip
        else ""
    )

    links_html = ""
    anchors = []
    for link in links:
        if not isinstance(link, (list, tuple)) or len(link) < 2:
            continue
        label, href = str(link[0]), str(link[1])
        if not href.startswith(("?", "/", "#", "http")):
            continue
        anchors.append(f'<a href="{ui.e(href)}">{_e(label)}{ui.icon("arrow-right", 10)}</a>')
    if anchors:
        links_html = f'<div class="answer-links">{"".join(anchors)}</div>'

    cite_html = _citation_html(citations)
    trace_html = _trace_html(retrieval)
    attach_html = _attachment_html(attachments)

    foot_bits = []
    if retrieval:
        foot_bits.append(f"检索 <b>{len(retrieval)}</b> 个片段")
    if citations:
        foot_bits.append(f"引用 <b>{len(citations)}</b> 份依据")
    if isinstance(elapsed, (int, float)) and elapsed:
        foot_bits.append(f"耗时 <b>{int(elapsed)}</b> ms")
    if not foot_bits and source:
        foot_bits.append(f"来源：{_e(source)}")
    foot_html = (
        f'<div class="qa-ans-foot">{ui.icon("zap", 10)}' + " · ".join(foot_bits) + "</div>"
        if foot_bits
        else ""
    )

    return f"""
<div class="chat-row">
  <div class="chat-avatar qa-avatar">{ui.icon('sparkles', 16)}</div>
  <div class="bubble-ai">
    <div class="qa-ans-head"><div class="answer-title">{_e(title)}</div>{"".join(pills)}</div>
    {f'<div class="answer-intro">{intro_html}</div>' if intro else ''}
    {steps_html}
    {attach_html}
    {tip_html}
    {cite_html}
    {trace_html}
    {links_html}
    {foot_html}
  </div>
</div>
"""


def _user_bubble(text: str) -> str:
    account = auth.current_user() or {}
    initial = account.get("initial") or data.USER["initial"]
    return f"""
<div class="chat-row user">
  <div class="bubble-user" style="overflow-wrap:anywhere;word-break:break-word">{_e(text)}</div>
  <div class="chat-avatar" style="background:linear-gradient(135deg,#0F2A5C,#0E7490)">{_e(initial)}</div>
</div>
"""


def _welcome_html() -> str:
    points = [
        ("book-open", "制度知识库"),
        ("paperclip", "PDF 上传"),
        ("shield", "来源可追溯"),
        ("message", "连续追问"),
    ]
    chips = "".join(
        f'<span>{ui.icon(icon_name, 11)}{label}</span>' for icon_name, label in points
    )
    return f"""
<div class="qa-welcome">
  <div class="qa-welcome-badge">{ui.icon('sparkles', 30)}</div>
  <h1>有问题，先问<span>河小智</span></h1>
  <p>校园政策、办事流程、最新通知、四年规划——用大白话问，答案带办理步骤与制度依据，还支持上传 PDF 让回答更懂你。</p>
  <div class="qa-welcome-points">{chips}</div>
</div>
"""


def _chat_card_html() -> str:
    history = qa_history()
    docs = qa_docs()
    try:
        session_no = qa_session_no()
    except Exception:
        session_no = 1
    rounds = sum(1 for message in history if message.get("role") == "assistant")
    token = str(time.time_ns())
    if history:
        stream = "".join(
            _user_bubble(str(message.get("content") or ""))
            if message.get("role") == "user"
            else _answer_bubble(message.get("content"))
            for message in history
        )
        stream_class = "qa-stream"
    else:
        stream = _welcome_html()
        stream_class = "qa-stream empty"
    sub = (
        f"已载入 {len(_policy_docs())} 篇制度 · {_kb_count()} 条问答"
        f" · 本轮上传 {len(docs)} 份资料"
        f" · 对话 #{session_no}"
    )
    if rounds:
        sub += f" · 已完成 {rounds} 轮"
    return f"""
<div class="qa-chat">
  <div class="qa-chat-head">
    <div class="qa-chat-id">
      <div class="qa-chat-avatar">{ui.icon('sparkles', 21)}</div>
      <div>
        <div class="qa-chat-name">河小智 · 校园政策问答<span class="qa-live"><i></i>在线</span></div>
        <div class="qa-chat-sub">{_e(sub)}</div>
      </div>
    </div>
    <div class="qa-chat-tools">
      <a class="qa-tool" href="?page=qa&new=1&token={_e(token)}">{ui.icon('plus', 11)}新对话</a>
      <a class="qa-tool ghost" href="?page=qa&clear=1&token={_e(token)}">{ui.icon('refresh', 11)}清空</a>
    </div>
  </div>
  <div class="{stream_class}">{stream}</div>
  <div class="qa-chat-foot">{ui.icon('shield', 11)}答案由校内知识库检索 + 大模型生成（可在 .env 关闭大模型），每条都标注依据来源；涉及个人权益的事项，请以主管部门最新通知为准。</div>
</div>
"""


# --------------------------------------------------------------------------- #
# 页面区块
# --------------------------------------------------------------------------- #
def _quick_panel(prefix: str = "welcome", on_ask=None) -> None:
    """首屏的 5 个快捷问题：紧凑胶囊样式，点击直接发起问答。"""
    items = _quick_questions()
    if not items:
        return
    ask = on_ask or _ask
    head = f"""
<div class="qa-quick-head">
  <div class="qa-quick-eyebrow">{ui.icon('zap', 11)}猜你想问 · QUICK ASK</div>
  <span class="qa-quick-sub">{ui.icon('sparkles', 10)}点击即答 · 无需打字</span>
</div>
"""
    with st.container(key="qa-quick"):
        _render(head)
        columns = st.columns(len(items), gap="small")
        for index, (column, item) in enumerate(zip(columns, items), 1):
            with column:
                st.button(
                    str(item.get("label") or item.get("question") or ""),
                    key=f"qa-quick-{prefix}-{item.get('id') or index}",
                    on_click=ask,
                    args=(str(item.get("question") or item.get("label") or ""),),
                    use_container_width=True,
                    help=str(item.get("hint") or ""),
                )


def _composer_tools() -> None:
    """紧贴输入条的快捷功能导航：不需要离开对话就能发现全部能力。"""
    _render(
        f"""
<div class="qa-composer-tools">
  <span class="qa-ct-label">{ui.icon('layout-grid', 10)}快捷工具</span>
  <a href="?page=qa&view=upload">{ui.icon('paperclip', 10)}上传 PDF</a>
  <a href="?page=qa&view=search">{ui.icon('database', 10)}知识库检索</a>
  <a href="?page=qa&view=faq">{ui.icon('flame', 10)}常见问题</a>
  <a href="?page=qa&view=library">{ui.icon('book-open', 10)}制度原文</a>
  <a href="?page=qa&view=guide">{ui.icon('shield', 10)}使用帮助</a>
</div>
"""
    )


def _chat_workspace() -> None:
    history = qa_history()
    _render(_chat_card_html())

    # 没有任何对话时，把 5 个快捷问题放在欢迎语下面，用户第一眼就能开始。
    if not history:
        _quick_panel()

    last = None
    try:
        last = qa_last_result()
    except Exception:
        last = None
    suggestions = [
        str(item)
        for item in _safe_list((last or {}).get("suggestions") if isinstance(last, dict) else [])
        if str(item).strip()
    ][:3]
    if suggestions:
        with st.container(key="qa-follow"):
            _render(f'<div class="qa-follow-head">{ui.icon("corner-down-right", 11)}继续追问 · 基于上一轮回答</div>')
            columns = st.columns(len(suggestions), gap="small")
            for index, (column, question) in enumerate(zip(columns, suggestions), 1):
                with column:
                    st.button(
                        question,
                        key=f"qa-follow-{index}-{abs(hash(question)) % 100000}",
                        on_click=_ask,
                        args=(question,),
                        use_container_width=True,
                    )

    _composer_tools()
    with st.container(key="qa-composer"):
        with st.form("qa-composer-form", clear_on_submit=True):
            question = st.text_input(
                "向河小智提问",
                key="qa-composer-input",
                placeholder="试试问我：学生证丢了怎么办？/ 最近有哪些校园活动？",
                label_visibility="collapsed",
                autocomplete="off",
            )
            submitted = st.form_submit_button("发送")
        _render(
            f"""
<div class="qa-composer-note">
  <span>{ui.icon('paperclip', 10)}快捷工具可上传 PDF，让回答基于你的资料</span>
  <span>{ui.icon('corner-down-right', 10)}Enter 发送 · 支持连续追问</span>
</div>
"""
        )
    if submitted:
        _ask(question)
        st.rerun()


def _upload_panel() -> None:
    docs = qa_docs()
    with st.container(key="qa-upload"):
        _render(
            f"""
<div class="qa-card-head">
  <div>
    <div class="qa-card-title"><span class="qa-card-ico">{ui.icon('paperclip', 15)}</span>PDF 资料上传</div>
    <div class="qa-card-sub">上传后自动解析文字，加入本次问答的检索范围</div>
  </div>
  <span class="qa-card-count">{len(docs)} / 5 份</span>
</div>
"""
        )
        if pdf_reader is not None:
            uploaded = st.file_uploader(
                "上传 PDF 资料",
                type=["pdf", "txt", "md"],
                accept_multiple_files=True,
                label_visibility="collapsed",
                key="qa-uploader",
            )
            if uploaded:
                processed = st.session_state.get("qa_upload_digests")
                if not isinstance(processed, set):
                    processed = set()
                    st.session_state.qa_upload_digests = processed
                for file in uploaded:
                    try:
                        payload = file.getvalue()
                    except Exception:
                        continue
                    digest = hashlib.md5(payload).hexdigest()
                    if digest in processed:
                        continue
                    if len(docs) >= 5:
                        st.session_state.qa_upload_error = "最多同时保留 5 份资料，请先移除不需要的文件。"
                        break
                    processed.add(digest)
                    with st.spinner(f"正在解析 {file.name} …"):
                        _ingest(file.name, payload, digest=digest)
                    docs = qa_docs()
        sample_files = _sample_pdfs()
        if sample_files:
            _render('<div class="qa-sample-row">' + ui.icon("sparkles", 10) + "没有准备文件？试试示例：</div>")
            for index, filename in enumerate(sample_files[:2]):
                st.button(
                    "载入示例 · " + filename.replace(".pdf", "")[:18],
                    key=f"qa-sample-{index}",
                    on_click=_ingest_sample,
                    args=(filename,),
                    use_container_width=True,
                )
        if st.session_state.get("qa_upload_error"):
            _render(f'<div class="qa-upload-msg bad">{_e(st.session_state.qa_upload_error)}</div>')
        if st.session_state.get("qa_upload_ok"):
            _render(f'<div class="qa-upload-msg ok">{_e(st.session_state.qa_upload_ok)}</div>')
        if docs:
            _render('<div style="margin-top:4px"></div>')
            for doc in docs:
                left, right = st.columns([0.78, 0.22], gap="small")
                with left:
                    _render(
                        f"""
<div class="qa-doc-row">
  <div class="qa-doc-name">{ui.icon('file-text', 12)}{_e(doc.get('name') or '资料')}</div>
  <div class="qa-doc-meta">
    <span>{ui.icon('layers', 9)}{_e(doc.get('pages', 0))} 页</span>
    <span>{ui.icon('book-open', 9)}{_e(doc.get('chars', 0))} 字</span>
    <span class="qa-tag teal">{ui.icon('check', 8)}已加入检索</span>
  </div>
</div>
"""
                    )
                with right:
                    st.button(
                        "移除",
                        key=f"qa-rm-{doc.get('id')}",
                        on_click=_remove_doc,
                        args=(str(doc.get("id") or ""),),
                        use_container_width=True,
                    )
        _render(
            f'<div class="qa-upload-hint">{ui.icon("info", 10)}文件只在本机内存中解析，不会上传到任何服务器；换新对话会自动清空。</div>'
        )


def _search_panel() -> None:
    with st.container(key="qa-search"):
        _render(
            f"""
<div class="qa-card-head">
  <div>
    <div class="qa-card-title"><span class="qa-card-ico">{ui.icon('database', 15)}</span>知识库检索</div>
    <div class="qa-card-sub">按制度名、部门或问题关键词检索校内知识库</div>
  </div>
  <span class="qa-card-count">{len(_policy_docs())} 篇</span>
</div>
"""
        )
        with st.form("qa-kb-search-form", clear_on_submit=False):
            query = st.text_input(
                "检索知识库",
                key="qa-kb-query",
                placeholder="搜制度 / 政策 / 流程，如「奖学金」",
                label_visibility="collapsed",
                autocomplete="off",
            )
            searched = st.form_submit_button("检索知识库")
        if searched:
            keyword = str(query or "").strip()
            st.session_state.qa_search_query = keyword
            if keyword and kb is not None:
                try:
                    st.session_state.qa_search_results = kb.search(
                        keyword, limit=5, uploads=qa_docs()
                    )
                except Exception:
                    st.session_state.qa_search_results = []
            else:
                st.session_state.qa_search_results = []
        results = st.session_state.get("qa_search_results") or []
        keyword = st.session_state.get("qa_search_query") or ""
        if results:
            for index, item in enumerate(results[:4]):
                if not isinstance(item, dict):
                    continue
                source = str(item.get("source") or "policy")
                label = {"policy": "制度", "upload": "资料", "faq": "问答"}.get(source, "知识")
                score = _pct(item.get("score"))
                left, right = st.columns([0.78, 0.22], gap="small")
                with left:
                    _render(
                        f"""
<div class="qa-kb-row">
  <div class="qa-kb-body">
    <div class="qa-kb-title">{_e(item.get('title') or '')}</div>
    <div class="qa-kb-snippet">{_e(item.get('snippet') or '')}</div>
    <div class="qa-kb-meta">
      <span class="qa-tag {'teal' if source == 'upload' else 'gray'}">{_e(label)}</span>
      <span>{_e(item.get('meta') or '')}</span>
      <span class="qa-kb-score"><i style="width:{score}%"></i></span>
      <span>{score}%</span>
    </div>
  </div>
</div>
"""
                    )
                with right:
                    st.button(
                        "追问",
                        key=f"qa-kb-ask-{index}",
                        on_click=_ask_from_item_and_back,
                        args=(item,),
                        use_container_width=True,
                    )
        elif keyword:
            _render(f'<div class="qa-kb-empty">没有检索到「{_e(keyword)}」相关的校内资料，换个关键词试试，例如「奖学金」「报修」「选课」。</div>')
        else:
            _render(
                f'<div class="qa-kb-empty">输入关键词即可检索 {len(_policy_docs())} 篇制度、{_kb_count()} 条问答与已上传资料。</div>'
            )


def _faq_panel() -> None:
    items = _faq_items()[:8]
    if not items:
        return
    with st.container(key="qa-faq"):
        _render(
            f"""
<div class="qa-card-head">
  <div>
    <div class="qa-card-title"><span class="qa-card-ico">{ui.icon('flame', 15)}</span>常见问题推荐</div>
    <div class="qa-card-sub">同学们问得最多的问题，点击直接得到答案</div>
  </div>
  <span class="qa-card-count">{ui.icon('trending-up', 9)}高频</span>
</div>
"""
        )
        columns = st.columns(2, gap="small")
        for index, item in enumerate(items):
            question = str(item.get("question") or "")
            with columns[index % 2]:
                st.button(
                    question,
                    key=f"qa-faq-{index}",
                    on_click=_ask_and_back,
                    args=(question,),
                    use_container_width=True,
                )


_TOOL_META = {
    "upload": ("PDF 资料上传", "上传通知、制度或学院资料，解析后加入本次问答的检索范围。", "paperclip", "blue"),
    "search": ("知识库检索", "按制度名、部门或问题关键词检索校内知识库。", "database", "teal"),
    "faq": ("常见问题推荐", "同学们问得最多的 8 个问题，点击直接得到答案。", "flame", "gold"),
    "library": ("制度原文库", "逐篇查看制度文号、发布部门、条款与摘录。", "book-open", "violet"),
    "guide": ("使用帮助", "怎么问更准、上传资料怎么用、来源与条款怎么看。", "shield", "green"),
}


def _workbench_rail() -> None:
    """对话框右侧的功能工作台：导航围绕对话，长内容进入独立页面。"""
    history = qa_history()
    docs = qa_docs()
    rounds = sum(1 for message in history if message.get("role") == "assistant")
    try:
        session_no = qa_session_no()
    except Exception:
        session_no = 1
    total_docs = len(_policy_docs())
    total_kb = _kb_count()
    total_faq = len(_faq_items())

    nav = []
    for key, (title, desc, icon_name, tone) in _TOOL_META.items():
        if key == "upload":
            badge = f"{len(docs)} / 5"
        elif key in ("search", "library"):
            badge = f"{total_docs} 篇"
        elif key == "faq":
            badge = f"{total_faq} 条"
        else:
            badge = "指南"
        nav.append(
            f"""
<a class="qa-wb-item t-{_e(tone)}" href="?page=qa&view={_e(key)}" title="{_e(title)} · 打开独立页面">
  <span class="qa-wb-ico">{ui.icon(icon_name, 14)}</span>
  <span class="qa-wb-copy"><b>{_e(title)}</b><small>{_e(desc)}</small></span>
  <span class="qa-wb-badge">{_e(badge)}</span>
  <span class="qa-wb-arrow">{ui.icon('chevron-right', 12)}</span>
</a>
"""
        )
    _render(
        f"""
<div class="qa-rail-card">
  <div class="qa-rail-head">
    <div>
      <div class="qa-rail-title"><span class="qa-rail-ico">{ui.icon('layout-grid', 14)}</span>功能工作台</div>
      <div class="qa-rail-sub">对话不中断，功能随手可用</div>
    </div>
    <span class="qa-rail-tag">{ui.icon('sparkles', 9)}在线</span>
  </div>
  <nav class="qa-wb-nav">{"".join(nav)}</nav>
</div>
<div class="qa-rail-card">
  <div class="qa-rail-head">
    <div>
      <div class="qa-rail-title"><span class="qa-rail-ico" style="background:var(--teal-soft);color:#0F9488">{ui.icon('chart', 14)}</span>本轮状态</div>
      <div class="qa-rail-sub">当前对话 #{session_no} · 记录按账号保存</div>
    </div>
  </div>
  <div class="qa-wb-stats">
    <div class="qa-wb-stat"><b>{rounds}</b><span>已完成轮次</span></div>
    <div class="qa-wb-stat"><b>{len(docs)}</b><span>上传资料</span></div>
    <div class="qa-wb-stat"><b>{total_docs}</b><span>制度原文</span></div>
    <div class="qa-wb-stat"><b>{total_kb}</b><span>知识库问答</span></div>
  </div>
  <div class="qa-wb-note">{ui.icon('shield', 10)}回答逐条标注依据；涉及个人权益请以主管部门最新通知为准。</div>
</div>
"""
    )

    faq = _faq_items()[:3]
    if not faq:
        return
    with st.container(key="qa-rail-ask"):
        _render(
            f"""
<div class="qa-rail-head">
  <div>
    <div class="qa-rail-title"><span class="qa-rail-ico" style="background:var(--gold-soft);color:#B7790B">{ui.icon('flame', 14)}</span>试试这样问</div>
    <div class="qa-rail-sub">高频问题，点击直接得到答案</div>
  </div>
  <span class="qa-rail-tag">{ui.icon('trending-up', 9)}高频</span>
</div>
"""
        )
        for index, item in enumerate(faq):
            question = str(item.get("question") or "")
            if not question:
                continue
            st.button(
                question,
                key=f"qa-rail-faq-{index}",
                on_click=_ask,
                args=(question,),
                use_container_width=True,
            )


def _mobile_tools_html() -> str:
    links = "".join(
        f'<a href="?page=qa&view={_e(key)}">{ui.icon(icon_name, 11)}{_e(title)}</a>'
        for key, (title, _desc, icon_name, _tone) in _TOOL_META.items()
    )
    return f'<nav class="qa-mobile-tools" aria-label="智能问答功能导航">{ui.icon("layout-grid", 12)}{links}</nav>'


def _guide_page() -> None:
    _capability_panel()
    _render('<div style="height:16px"></div>')
    _tips()
    _render('<div style="height:16px"></div>')
    _quick_panel(prefix="guide", on_ask=_ask_and_back)


def _tool_page(key: str) -> None:
    """独立功能页：承载上传、检索、FAQ、制度库等较长内容。"""
    meta = _TOOL_META.get(key)
    if not meta:
        return
    title, desc, icon_name, _tone = meta
    subnav = "".join(
        f'<a class="{"active" if item_key == key else ""}" href="?page=qa&view={_e(item_key)}">{_e(item_title)}</a>'
        for item_key, (item_title, _d, _i, _t) in _TOOL_META.items()
    )
    _render(
        f"""
<div class="qa-subpage-head">
  <div>
    <div class="qa-subpage-kicker">{ui.icon('layout-grid', 11)}QA WORKBENCH · 独立页面</div>
    <h2>{ui.icon(icon_name, 22)}{_e(title)}</h2>
    <p>{_e(desc)}</p>
  </div>
  <a class="qa-back" href="?page=qa">{ui.icon('corner-down-right', 12)}回到对话</a>
</div>
<nav class="qa-subnav" aria-label="功能页导航">{subnav}</nav>
"""
    )
    if key == "upload":
        _upload_panel()
    elif key == "search":
        _search_panel()
    elif key == "faq":
        _faq_panel()
    elif key == "library":
        _policy_library()
    else:
        _guide_page()
    if key == "library":
        _anchor_to_doc()
    _render(
        f"""
<div class="qa-subpage-foot">
  <span>{ui.icon('info', 11)}这里是智能问答的独立功能页；对话记录与上传资料会保留，返回后继续对话即可。</span>
  <a class="qa-back" href="?page=qa">{ui.icon('message', 12)}继续对话</a>
</div>
"""
    )


def _capability_panel() -> None:
    rows = []
    for item in data.QA_CAPABILITIES:
        background, color = _tone(item.get("tone", "blue"))
        rows.append(
            f"""
<div class="service-tile" style="cursor:default;padding:10px 9px">
  <span class="service-icon" style="background:{background};color:{color}">{ui.icon(item['icon'], 16)}</span>
  <span><span class="service-name">{_e(item['title'])}</span><span class="service-desc">{_e(item['desc'])}</span></span>
</div>
"""
        )
    _render(
        f"""
<section class="panel">
  <div class="panel-head" style="margin-bottom:10px">
    <div>
      <div class="panel-title"><span class="panel-icon">{ui.icon('cpu', 17)}</span>我能帮你做什么</div>
      <div class="panel-sub">四类校园高频问题，一个入口</div>
    </div>
  </div>
  {"".join(rows)}
  <div class="data-note" style="margin-top:10px">{ui.icon('info', 12)}知识库覆盖学生证、资助、教务、后勤、活动与成长规划；回答会标注制度来源，可展开查看条款摘录。</div>
</section>
"""
    )


def _policy_library() -> None:
    docs = _policy_docs()
    if not docs:
        return
    cards = []
    for doc in docs:
        doc_id = str(doc.get("id") or "")
        sections = [item for item in (doc.get("sections") or []) if isinstance(item, dict)]
        clauses = "".join(
            f'<div class="qa-clause"><b>{_e(item.get("clause") or "")}</b><span>{_e(item.get("text") or "")}</span></div>'
            for item in sections[:4]
        )
        cards.append(
            f"""
<details class="qa-doc" id="doc-{_e(doc_id)}">
  <summary>
    <span class="qa-doc-cat">{_e(doc.get('category') or '制度')}</span>
    <span class="qa-doc-title">{_e(doc.get('title') or '')}</span>
    <span class="qa-doc-no">{_e(doc.get('doc_no') or '')}</span>
    <span class="qa-doc-arrow">{ui.icon('chevron-down', 12)}</span>
  </summary>
  <div class="qa-doc-body">
    <div class="qa-doc-meta">{_e(doc.get('department') or '')} · {_e(doc.get('issued') or '')} 发布 · {_e(doc.get('status') or '现行有效')} · 适用：{_e(doc.get('applies_to') or '全体学生')}</div>
    <p class="qa-doc-summary">{_e(doc.get('summary') or '')}</p>
    {clauses}
  </div>
</details>
"""
        )
    _render(
        f"""
<section class="panel" style="margin-top:18px">
  <div class="panel-head" style="margin-bottom:13px">
    <div>
      <div class="panel-title"><span class="panel-icon">{ui.icon('book-open', 17)}</span>制度原文库</div>
      <div class="panel-sub">回答里的「依据来源」都能在这里展开到条款；演示数据，非学校官方发布</div>
    </div>
    <a class="panel-link" href="?page=services">办事流程导航 {ui.icon('chevron-right', 12)}</a>
  </div>
  <div class="qa-doclib">{"".join(cards)}</div>
</section>
"""
    )


def _tips() -> None:
    items = [
        ("message", "blue", "怎么问更准", "带上校区、时间、身份等关键信息，例如「金明校区、大一、学生证丢了」；一次问一件事，答案更精准。"),
        ("paperclip", "teal", "上传资料怎么用", "把学院通知、制度 PDF 上传后，同样的问题会优先结合文件内容回答，并标注「第几页」。"),
        ("shield", "gold", "来源怎么看", "每个回答都可展开「依据来源」，查看制度名、文号、条款与摘录；在页面底部还能读到条款原文。"),
    ]
    cards = []
    for icon_name, tone, title, desc in items:
        background, color = _tone(tone)
        cards.append(
            f"""
<div class="qa-tip-card">
  <div class="qa-tip-title"><span class="qa-tip-ico" style="background:{background};color:{color}">{ui.icon(icon_name, 14)}</span>{_e(title)}</div>
  <div class="qa-tip-desc">{_e(desc)}</div>
</div>
"""
        )
    _render(f'<div class="qa-tips" style="margin-top:18px">{"".join(cards)}</div>')


# --------------------------------------------------------------------------- #
# URL 参数（从首页 / 其它页面带问题进入、新对话、清空）
# --------------------------------------------------------------------------- #
def _handle_params() -> None:
    seen = _seen()
    token = _one("token")

    if _one("new") in ("1", "true", "yes"):
        key = "new:" + (token or "once")
        if key not in seen:
            seen.add(key)
            _new_session()

    if _one("clear") in ("1", "true", "yes"):
        key = "clear:" + (token or "once")
        if key not in seen:
            seen.add(key)
            clear_qa()
            st.session_state.pop("qa_scroll_pending", None)

    question = _one("q")
    if not question:
        return
    # 同一次跳转只入栈一次；刷新 / 回退时若已是最后一问也不重复
    if question == _last_user_question():
        return
    if token:
        key = "ask:" + token
        if key in seen:
            return
        seen.add(key)
    _ask(question, source="link")


def _anchor_to_doc() -> None:
    """从回答的「查看条款原文」跳到制度库时，展开并滚动到对应条款。"""
    try:
        components.html(
            """
<script>
(function () {
  try {
    const doc = window.parent.document;
    const hash = decodeURIComponent(window.parent.location.hash || '');
    if (!hash || !hash.startsWith('#doc-')) return;
    const target = doc.getElementById(hash.slice(1));
    if (!target) return;
    if (target.tagName.toLowerCase() === 'details') target.open = true;
    target.scrollIntoView({block: 'start', behavior: 'auto'});
  } catch (err) {}
})();
</script>
""",
            height=0,
        )
    except Exception:
        pass


def _scroll_to_answer() -> None:
    if not st.session_state.get("qa_scroll_pending"):
        return
    st.session_state.qa_scroll_pending = False
    try:
        components.html(
            """
<script>
try {
  const doc = window.parent.document;
  const rows = doc.querySelectorAll('.qa-stream .chat-row');
  if (rows.length) {
    rows[rows.length - 1].scrollIntoView({block: 'center', behavior: 'smooth'});
  }
} catch (err) {}
</script>
""",
            height=0,
        )
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# 入口
# --------------------------------------------------------------------------- #
def render() -> None:
    _render(_CSS)
    _handle_params()

    if kb is None:
        _render(
            f'<div class="qa-missing">{ui.icon("alert-circle", 26)}<div style="margin-top:10px">问答引擎正在接入中，请稍后刷新页面重试。</div></div>'
        )
        return

    # 独立功能页（上传 / 检索 / FAQ / 制度库 / 帮助）：长内容不挤在对话框旁边。
    view = _one("view").strip().lower()
    if st.session_state.pop("qa_view_override", False):
        view = ""
    if view in _TOOL_META:
        _tool_page(view)
        _render(
            f'<div class="data-note" style="margin-top:16px">{ui.icon("info", 13)}演示说明：本页为黑客松演示版，制度、文号与通知均为示例数据，不连接学校真实业务系统；对话记录仅保存在本机当前浏览器会话中。</div>'
        )
        _scroll_to_answer()
        return

    # 对话优先：进入页面第一眼就是对话框，功能导航在右侧工作台与输入条周围。
    _render(_mobile_tools_html())

    with st.container(key="qa-main"):
        left, right = st.columns([1.62, 0.58], gap="medium")
        with left:
            with st.container(key="qa-chatcol"):
                _chat_workspace()
        with right:
            with st.container(key="qa-rail"):
                _workbench_rail()

    _render(
        f'<div class="data-note" style="margin-top:16px">{ui.icon("info", 13)}演示说明：本页为黑客松演示版，制度、文号与通知均为示例数据，不连接学校真实业务系统；对话记录仅保存在本机当前浏览器会话中。</div>'
    )
    _scroll_to_answer()
