# -*- coding: utf-8 -*-
"""河小智 · 大模型问答增强层。

调用顺序：``core.kb`` 先做本地知识库检索 → 本模块把命中条目、制度摘录和
最近几轮对话一起交给大模型，生成更自然、更完整的回答 → 保留原有的
引用、检索轨迹、附件与链接，页面气泡样式不变。

任何一步失败（未配置密钥、断网、超时、API 报错）都会回退到原本的本地回答，
因此离线演示、无密钥环境下功能完全不受影响。
"""

from __future__ import annotations

from typing import Any

from . import llm

# 人设与输出约束。明确要求「纯文本、不要 HTML / Markdown 符号」，
# 这样回答可以直接放进气泡，不会出现 <div>、** 之类的原始符号。
SYSTEM_PROMPT = """你是「河小智」，河南大学 AI 智慧校园服务平台里的校园助手，服务对象是本校学生和教职工。

回答要求：
1. 用简体中文，语气亲切、像学长学姐一样直接解决问题；先给结论，再分点说步骤、所需材料、注意事项。
2. 涉及学校政策、办理流程、地点、电话、费用、时间等内容时，只能依据下面提供的「校内资料」；资料里没有的信息不要编造，直接说明"校内资料里暂时没有这一条"，并建议咨询主管部门或查看学校官网。
3. 只输出纯文本：不要输出任何 HTML 标签（如 <div>、<br>），也不要用 Markdown 标记（如 **、##、```、|）；分点用「1.」「2.」或「-」，每点单独一行。
4. 一般问题控制在 300 字以内；用户明确要求详细说明时再展开。
5. 涉及学籍、奖助、报销、纪律等个人权益事项时，最后补一句"具体以主管部门最新通知为准"。
6. 如果用户只是打招呼或闲聊，简短自然地回应，并引导他说出校园里想办的事。
"""

_MAX_HISTORY = 3  # 最多带 3 轮历史，避免上下文过长
_MAX_CONTEXT = 2600  # 校内资料上下文长度上限


def _message_text(message: dict[str, Any]) -> str:
    """把历史消息转成纯文本，供大模型理解上文。"""
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, dict):
        bits = [str(content.get("title") or ""), str(content.get("intro") or "")]
        steps = content.get("steps") or []
        if isinstance(steps, list) and steps:
            bits.append("；".join(str(step) for step in steps[:6]))
        return "\n".join(bit for bit in bits if bit).strip()
    return ""


def _history_messages(history: list[dict] | None) -> list[dict[str, str]]:
    if not history:
        return []
    messages: list[dict[str, str]] = []
    for message in history[-_MAX_HISTORY * 2:]:
        role = message.get("role")
        if role not in {"user", "assistant"}:
            continue
        text = _message_text(message)
        if not text:
            continue
        if messages and messages[-1]["role"] == role:
            messages[-1]["content"] += "\n" + text
        else:
            messages.append({"role": role, "content": text[:1200]})
    return messages


def _local_context(result: dict[str, Any]) -> str:
    """把本地检索结果整理成大模型可引用的资料块。"""
    parts: list[str] = []

    intro = str(result.get("intro") or "").strip()
    if result.get("matched") and intro:
        lines = [f"知识库条目：{result.get('title') or ''}", f"要点：{intro}"]
        steps = [str(step) for step in (result.get("steps") or []) if str(step).strip()]
        if steps:
            lines.append("参考步骤：\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1)))
        tip = str(result.get("tip") or "").strip()
        if tip:
            lines.append("注意事项：" + tip)
        parts.append("\n".join(lines))

    for index, cite in enumerate(result.get("citations") or [], 1):
        if not isinstance(cite, dict):
            continue
        head = " · ".join(
            bit
            for bit in [
                str(cite.get("title") or cite.get("file") or ""),
                str(cite.get("doc_no") or ""),
                str(cite.get("clause") or ""),
            ]
            if bit
        )
        excerpt = str(cite.get("excerpt") or "").strip()
        if head or excerpt:
            parts.append(f"依据 {index}：{head}\n{excerpt}")

    for item in (result.get("retrieval") or [])[:3]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        snippet = str(item.get("snippet") or item.get("excerpt") or "").strip()
        if title and snippet:
            parts.append(f"相关片段：{title} —— {snippet}")

    text = "\n\n".join(part for part in parts if part.strip())
    return text[:_MAX_CONTEXT]


def enhance(
    question: str,
    history: list[dict] | None,
    result: dict[str, Any],
) -> dict[str, Any]:
    """用大模型增强回答；未启用或失败时原样返回本地结果。"""
    if not isinstance(result, dict):
        return result
    if not llm.is_enabled():
        return result

    context = _local_context(result)
    if context:
        user_content = f"【校内资料】\n{context}\n\n【我的问题】\n{question}"
    else:
        user_content = (
            "【校内资料】\n本次检索没有命中校内制度或知识库条目。\n\n"
            f"【我的问题】\n{question}"
        )

    messages = _history_messages(history)
    messages.append({"role": "user", "content": user_content})

    try:
        text = llm.chat(
            messages,
            system=SYSTEM_PROMPT,
            max_tokens=1100,
            temperature=0.3,
        )
    except llm.LLMError as exc:
        # 静默回退：保留本地答案，仅记录原因，方便在页面或日志中排查
        result = dict(result)
        result["llm_used"] = False
        result["llm_error"] = str(exc)[:200]
        return result

    text = text.strip()
    if not text:
        return result

    cfg = llm.config()
    enhanced = dict(result)
    enhanced.update(
        {
            "title": str(result.get("title") or "河小智的回答"),
            "intro": text,
            # 正文已包含步骤与注意事项，置空避免同一段内容显示两遍
            "steps": [],
            "tip": "",
            "source": f"大模型 {cfg['model']} + 校内知识库",
            "llm_used": True,
            "llm_model": cfg["model"],
        }
    )
    return enhanced
