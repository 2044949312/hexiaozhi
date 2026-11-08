# -*- coding: utf-8 -*-
"""河小智 · 轻量校园问答引擎（兼容旧接口）

旧版 ``answer(question)`` 仅返回首页需要的字段；现在统一委托给
``core.kb.answer``（本地检索增强），并额外透传引用、检索轨迹等新字段。
真实版本可替换为 LLM + 向量知识库，当前实现不依赖外部模型与网络。
"""

from __future__ import annotations

from typing import Any

from . import kb as _kb


def answer(question: str) -> dict[str, Any]:
    """返回旧接口字段，供首页 / 其它页面复用。"""
    result = _kb.answer(question)
    citations = result.get("citations") or []
    source = result.get("source") or ""
    if citations and not source:
        first = citations[0]
        source = str(first.get("title") or first.get("file") or "")

    return {
        **result,
        # 兼容旧字段命名
        "entry_id": result.get("intent") or "",
        "source": source or "河小智 · 校园知识库（演示版）",
        "title": result.get("title") or "河小智的回答",
        "intro": result.get("intro") or "",
        "steps": list(result.get("steps") or []),
        "tip": result.get("tip") or "",
        "links": list(result.get("links") or []),
        "tone": result.get("tone") or "blue",
        "confidence": result.get("confidence"),
        "suggestions": list(result.get("suggestions") or []),
        "raw_question": result.get("raw_question") or str(question or ""),
        "matched": bool(result.get("matched")),
    }
