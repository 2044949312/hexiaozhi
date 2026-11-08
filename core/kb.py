# -*- coding: utf-8 -*-
"""河小智 · 校园知识库检索引擎（纯标准库，无需联网 / API Key）。

对外接口（与 docs/QA_PAGE2_SPEC.md 第 3.1 节一致）：

- ``answer(question, history=None, uploads=None) -> dict``  结构化问答结果
- ``search(query, limit=6, uploads=None) -> list[dict]``    知识库检索
- ``make_upload(name, extracted) -> dict``                  登记上传资料
- ``followups(result) -> list[str]``                        生成 3 条追问建议

实现说明：中文按 2-gram + 关键词加权检索，数据来自 ``core.data.QA_KB`` 与
``core.policy.KB_EXTRA``；答案中的引用来自 ``core.policy.CITATIONS_BY_KB`` 映射
的制度条款。任何异常都会兜底为 fallback 答案，绝不向上抛出。
"""

from __future__ import annotations

import hashlib
import re
import time
from datetime import datetime
from typing import Any

from . import data

try:  # 政策知识库（缺失时仍可用 QA_KB 提供基础问答）
    from . import policy
except Exception:  # pragma: no cover - 并行开发阶段的兜底
    policy = None  # type: ignore[assignment]

_PUNCT = re.compile(
    r"[\s，。！？、；：,.!?;:~～（）()【】\[\]“”\"'《》<>·—\-_/\\|]+"
)
_GREETINGS = ["你好", "您好", "嗨", "hello", "hi", "在吗", "早上好", "上午好", "下午好", "晚上好"]


# --------------------------------------------------------------------------- #
# 文本工具
# --------------------------------------------------------------------------- #
def _clean(text: Any) -> str:
    return _PUNCT.sub("", str(text or "").strip().lower())


def _grams(text: Any, size: int = 2) -> set[str]:
    cleaned = _clean(text)
    if not cleaned:
        return set()
    if len(cleaned) < size:
        return {cleaned}
    return {cleaned[i : i + size] for i in range(len(cleaned) - size + 1)}


def _overlap(query_grams: set[str], text: Any) -> float:
    """query 的 2-gram 在 text 中的覆盖率（0—1）。"""
    if not query_grams:
        return 0.0
    return len(query_grams & _grams(text)) / len(query_grams)


def _truncate(text: Any, limit: int = 120) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _iso_today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# --------------------------------------------------------------------------- #
# 数据装配
# --------------------------------------------------------------------------- #
def _policy_docs() -> list[dict]:
    return list(getattr(policy, "POLICY_DOCS", None) or [])


def _doc_index() -> dict[str, dict]:
    return {str(doc.get("id") or ""): doc for doc in _policy_docs() if doc.get("id")}


def _entries() -> list[dict]:
    """QA_KB + KB_EXTRA，统一补齐 citations / extras 字段。"""
    citation_map = getattr(policy, "CITATIONS_BY_KB", None) or {}
    merged: list[dict] = []
    seen: set[str] = set()
    for raw in list(data.QA_KB) + list(getattr(policy, "KB_EXTRA", None) or []):
        if not isinstance(raw, dict):
            continue
        entry_id = str(raw.get("id") or "")
        if not entry_id or entry_id in seen:
            continue
        seen.add(entry_id)
        entry = dict(raw)
        citations = entry.get("citations")
        if not citations:
            citations = citation_map.get(entry_id, [])
        entry["citations"] = list(citations or [])
        entry["extras"] = list(entry.get("extras") or [])
        merged.append(entry)
    return merged


def _entry_index() -> dict[str, dict]:
    return {str(entry.get("id") or ""): entry for entry in _entries()}


# --------------------------------------------------------------------------- #
# 检索打分
# --------------------------------------------------------------------------- #
def _score_entry(query_clean: str, query_grams: set[str], entry: dict) -> float:
    question = str(entry.get("question") or "")
    question_clean = _clean(question)
    raw = 0.0

    if question_clean and query_clean == question_clean:
        raw += 100.0
    elif question_clean and (question_clean in query_clean or query_clean in question_clean):
        raw += 42.0

    for keyword in entry.get("keywords") or []:
        key = _clean(keyword)
        if key and key in query_clean:
            raw += 10.0 + min(len(key), 8) * 2.0

    raw += _overlap(query_grams, question) * 24.0
    raw += _overlap(query_grams, entry.get("title")) * 14.0
    raw += _overlap(query_grams, entry.get("intro")) * 6.0
    raw += _overlap(query_grams, " ".join(str(s) for s in (entry.get("steps") or []))) * 5.0
    return raw


def _score_doc(query_clean: str, query_grams: set[str], doc: dict) -> float:
    raw = 0.0
    for keyword in doc.get("keywords") or []:
        key = _clean(keyword)
        if key and key in query_clean:
            raw += 8.0 + min(len(key), 8) * 1.6
    raw += _overlap(query_grams, doc.get("title")) * 18.0
    raw += _overlap(query_grams, doc.get("summary")) * 10.0
    sections = " ".join(str(s.get("text") or "") for s in (doc.get("sections") or []) if isinstance(s, dict))
    raw += _overlap(query_grams, sections) * 8.0
    return raw


def _normalize(raw: float, ceiling: float = 70.0) -> float:
    if raw <= 0:
        return 0.0
    return round(min(0.99, raw / ceiling), 3)


def _best_section(doc: dict, query_grams: set[str]) -> dict:
    sections = [s for s in (doc.get("sections") or []) if isinstance(s, dict)]
    if not sections:
        return {}
    best = max(sections, key=lambda s: _overlap(query_grams, s.get("text")))
    return best


def _citations_for(entry: dict, query_grams: set[str]) -> list[dict]:
    index = _doc_index()
    citations: list[dict] = []
    for doc_id in entry.get("citations") or []:
        doc = index.get(str(doc_id))
        if not doc:
            continue
        section = _best_section(doc, query_grams)
        citations.append(
            {
                "doc_id": str(doc.get("id") or ""),
                "title": str(doc.get("title") or ""),
                "doc_no": str(doc.get("doc_no") or ""),
                "department": str(doc.get("department") or ""),
                "issued": str(doc.get("issued") or ""),
                "clause": str(section.get("clause") or ""),
                "excerpt": _truncate(section.get("text") or doc.get("summary") or "", 150),
                "status": str(doc.get("status") or "现行有效"),
                "source_type": "policy",
            }
        )
        if len(citations) >= 2:
            break
    return citations


def _intent_label(entry: dict, citations: list[dict]) -> str:
    if citations:
        doc = _doc_index().get(str(citations[0].get("doc_id") or ""))
        if doc and doc.get("category"):
            return str(doc["category"])
    return str(entry.get("category") or "校园问答")


def _retrieval_for(entry: dict, citations: list[dict], query_grams: set[str], score: float) -> list[dict]:
    rows: list[dict] = []
    for citation in citations[:2]:
        rows.append(
            {
                "source": "policy",
                "title": citation.get("title") or "校内制度",
                "snippet": citation.get("excerpt") or "",
                "score": round(min(0.99, max(0.2, score)), 2),
                "meta": " · ".join(
                    bit for bit in (citation.get("department"), citation.get("doc_no")) if bit
                ),
                "doc_id": citation.get("doc_id") or "",
            }
        )
    rows.append(
        {
            "source": "faq",
            "title": str(entry.get("question") or entry.get("title") or "校园问答"),
            "snippet": _truncate(entry.get("intro") or "", 90),
            "score": round(min(0.99, max(0.15, score - 0.05)), 2),
            "meta": "校园问答库",
            "kb_id": str(entry.get("id") or ""),
        }
    )
    if len(rows) < 3:
        for doc in _policy_docs():
            if any(row.get("doc_id") == doc.get("id") for row in rows):
                continue
            doc_score = _score_doc("", query_grams, doc)
            if doc_score <= 0:
                continue
            rows.append(
                {
                    "source": "policy",
                    "title": str(doc.get("title") or ""),
                    "snippet": _truncate(doc.get("summary") or "", 90),
                    "score": round(min(0.95, 0.2 + doc_score / 120.0), 2),
                    "meta": " · ".join(
                        bit for bit in (doc.get("department"), doc.get("doc_no")) if bit
                    ),
                    "doc_id": str(doc.get("id") or ""),
                }
            )
            if len(rows) >= 4:
                break
    return rows[:5]


# --------------------------------------------------------------------------- #
# 富内容附件
# --------------------------------------------------------------------------- #
_ACTIVITY_ICONS = {"科技": "code", "文艺": "music", "讲座": "book-open", "体育": "run", "志愿": "heart"}
_ACTIVITY_TONES = {"科技": "blue", "文艺": "rose", "讲座": "teal", "体育": "gold", "志愿": "violet"}


def _activity_items(limit: int = 4) -> list[dict]:
    items = []
    for activity in data.ACTIVITIES[:limit]:
        category = str(activity.get("category") or "")
        items.append(
            {
                "icon": _ACTIVITY_ICONS.get(category, "compass"),
                "tone": _ACTIVITY_TONES.get(category, "gold"),
                "title": str(activity.get("title") or ""),
                "meta": f"{activity.get('date') or ''} · {activity.get('location') or ''}".strip(" ·"),
                "desc": str(activity.get("summary") or ""),
                "tag": category,
                "href": f"?page=activities&id={activity.get('id') or ''}",
            }
        )
    return items


def _aid_items(limit: int = 6) -> list[dict]:
    items = []
    for item in list(getattr(policy, "AID_POLICIES", None) or [])[:limit]:
        items.append(
            {
                "icon": "wallet",
                "tone": str(item.get("tone") or "gold"),
                "title": str(item.get("name") or ""),
                "amount": str(item.get("amount") or ""),
                "meta": " · ".join(
                    bit for bit in (item.get("target"), item.get("deadline")) if bit
                ),
                "desc": str(item.get("desc") or ""),
                "tag": "资助",
                "href": "?page=services&q=资助",
            }
        )
    return items


def _notice_items(limit: int = 5) -> list[dict]:
    items = []
    for item in list(getattr(policy, "NOTICES", None) or [])[:limit]:
        items.append(
            {
                "icon": "bell",
                "tone": "violet" if item.get("tag") == "置顶" else "blue",
                "title": str(item.get("title") or ""),
                "meta": f"{item.get('date') or ''} · {item.get('department') or ''}".strip(" ·"),
                "desc": str(item.get("summary") or ""),
                "tag": str(item.get("tag") or item.get("category") or "通知"),
                "href": str(item.get("href") or "?page=qa"),
            }
        )
    return items


def _plan_items() -> list[dict]:
    items = []
    for stage in list(getattr(policy, "PLAN_STAGES", None) or []):
        points = [str(p) for p in (stage.get("items") or []) if p]
        items.append(
            {
                "step": str(stage.get("stage") or ""),
                "title": str(stage.get("title") or stage.get("focus") or ""),
                "desc": "；".join(points[:2]),
                "tone": str(stage.get("tone") or "blue"),
            }
        )
    return items


def _attachments_for(entry: dict) -> list[dict]:
    blocks: list[dict] = []
    for extra in entry.get("extras") or []:
        if extra == "activities":
            blocks.append({"type": "list", "title": "近期校园活动", "items": _activity_items()})
        elif extra == "aid_policies":
            blocks.append({"type": "list", "title": "资助政策清单", "items": _aid_items()})
        elif extra == "notices":
            blocks.append({"type": "list", "title": "最新通知公告", "items": _notice_items()})
        elif extra == "plan":
            blocks.append({"type": "timeline", "title": "四年规划建议", "items": _plan_items()})
    return [block for block in blocks if block.get("items")]


# --------------------------------------------------------------------------- #
# 上传资料
# --------------------------------------------------------------------------- #
def make_upload(name: str, extracted: dict) -> dict:
    pages = [p for p in (extracted.get("pages") or []) if isinstance(p, dict)]
    chunks: list[dict] = []
    for page in pages:
        text = str(page.get("text") or "").strip()
        if not text:
            continue
        chunks.append({"page": int(page.get("no") or len(chunks) + 1), "text": text})
    chars = int(extracted.get("chars") or sum(len(c["text"]) for c in chunks))
    digest_source = f"{name}:{chars}:{time.time_ns()}".encode("utf-8", "ignore")
    return {
        "id": "upload-" + hashlib.md5(digest_source).hexdigest()[:10],
        "name": str(name or "上传资料"),
        "pages": int(extracted.get("page_count") or len(chunks) or 1),
        "chars": chars,
        "chunks": chunks,
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def _upload_candidates(uploads: list[dict] | None, query_clean: str, query_grams: set[str]) -> list[dict]:
    candidates: list[dict] = []
    for document in uploads or []:
        if not isinstance(document, dict):
            continue
        name = str(document.get("name") or "上传资料")
        for chunk in document.get("chunks") or []:
            if not isinstance(chunk, dict):
                continue
            text = str(chunk.get("text") or "")
            if not text.strip():
                continue
            grams = _grams(text)
            if not grams:
                continue
            overlap = len(query_grams & grams) / max(1, len(query_grams))
            keyword_hit = 1.0 if query_clean and query_clean in _clean(text) else 0.0
            score = min(1.0, overlap * 0.9 + keyword_hit * 0.35)
            if score <= 0:
                continue
            candidates.append(
                {
                    "name": name,
                    "page": int(chunk.get("page") or 1),
                    "text": text,
                    "score": score,
                }
            )
    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates


def _upload_answer(candidate: dict, query_grams: set[str]) -> dict:
    text = str(candidate.get("text") or "")
    # 取与问题最相关的一段作为摘录
    sentences = [s.strip() for s in re.split(r"(?<=[。！？；\n])", text) if s.strip()]
    ranked = sorted(sentences, key=lambda s: _overlap(query_grams, s), reverse=True)
    excerpt_sentences = [s for s in ranked if _overlap(query_grams, s) > 0][:3] or ranked[:2]
    excerpt = _truncate(" ".join(excerpt_sentences) or text, 180)
    score = float(candidate.get("score") or 0.0)
    name = str(candidate.get("name") or "上传资料")
    page = int(candidate.get("page") or 1)
    return {
        "matched": True,
        "intent": "upload",
        "intent_label": "个人资料",
        "title": "根据你上传的资料",
        "intro": f"在「{name}」第 {page} 页找到了与你的问题相关的内容：{excerpt}",
        "steps": [s for s in excerpt_sentences][:3],
        "tip": "以上内容来自你上传的本地资料，仅用于本次对话；重要事项请以原始文件与主管部门通知为准。",
        "tone": "teal",
        "confidence": round(min(0.95, 0.5 + score), 2),
        "citations": [
            {
                "title": name,
                "file": name,
                "page": page,
                "excerpt": excerpt,
                "source_type": "upload",
            }
        ],
        "links": [["查看办事流程", "?page=services"]],
        "attachments": [],
        "retrieval": [
            {
                "source": "upload",
                "title": f"{name} · 第 {page} 页",
                "snippet": _truncate(excerpt, 90),
                "score": round(score, 2),
                "meta": f"个人资料 · 第 {page} 页",
            }
        ],
        "suggestions": ["那要带什么材料？", "多久能办好？", "在哪里办理？"],
        "context_used": False,
    }


# --------------------------------------------------------------------------- #
# 连续追问
# --------------------------------------------------------------------------- #
_FOLLOWUP_CUES = {
    "materials": ["材料", "带什么", "需要什么", "准备什么", "证件", "资料"],
    "time": ["多久", "多长时间", "几天", "什么时候", "时限", "多久能", "几号", "时间"],
    "location": ["在哪", "哪里", "地点", "校区", "窗口", "大厅", "办公室", "地址"],
    "reserve": ["预约", "提前", "要不要预约", "需不需要预约"],
    "process": ["然后", "接下来", "下一步", "流程", "怎么办", "怎么弄", "还要"],
}

_CUE_TITLES = {
    "materials": "需要带哪些材料",
    "time": "办理需要多长时间",
    "location": "去哪里办理",
    "reserve": "是否需要预约",
    "process": "接下来怎么办理",
}

_CUE_KEYWORDS = {
    "materials": ["材料", "身份证", "照片", "申请表", "证明", "携带", "准备", "证件", "复印件"],
    "time": ["工作日", "分钟", "小时", "天", "截止", "时间", "当天", "即时", "期间"],
    "location": ["校区", "大厅", "窗口", "地点", "中心", "办公室", "行政楼", "楼", "处"],
    "reserve": ["预约", "提前", "线上", "系统", "公众号"],
    "process": ["首先", "然后", "之后", "下一步", "提交", "领取", "完成"],
}


def _followup_kind(question: str) -> str:
    cleaned = _clean(question)
    if len(cleaned) > 24:
        return ""
    for kind, cues in _FOLLOWUP_CUES.items():
        if any(_clean(cue) in cleaned for cue in cues):
            return kind
    return ""


def _previous_context(history: list[dict] | None) -> tuple[str, dict | None]:
    """从历史中找到上一问与上一条结构化回答。"""
    if not history:
        return "", None
    last_result = None
    last_question = ""
    for index in range(len(history) - 1, -1, -1):
        message = history[index]
        if not isinstance(message, dict):
            continue
        if last_result is None and message.get("role") == "assistant" and isinstance(message.get("content"), dict):
            last_result = message["content"]
            continue
        if last_result is not None and message.get("role") == "user":
            last_question = str(message.get("content") or "")
            break
    return last_question, last_result


def _followup_answer(kind: str, previous: dict, previous_question: str) -> dict | None:
    if not isinstance(previous, dict):
        return None
    previous_intent = str(previous.get("intent") or "")
    previous_title = str(previous.get("title") or "")
    entry = _entry_index().get(previous_intent)

    blocks: list[str] = []
    if entry:
        keys = _CUE_KEYWORDS.get(kind) or []
        matched_steps = [str(s) for s in (entry.get("steps") or []) if any(k in str(s) for k in keys)]
        if not matched_steps:
            matched_steps = [str(s) for s in (entry.get("steps") or [])][:3]
        blocks = matched_steps
        intro = f"接着上一个问题「{previous_question or entry.get('question') or previous_title}」，关于「{_CUE_TITLES[kind]}」，可以这样看："
        title = f"接着上一个问题 · {entry.get('title') or previous_title}"
        citations = _citations_for(entry, _grams(previous_question or entry.get("question") or ""))
        tone = str(entry.get("tone") or previous.get("tone") or "blue")
        labels = _intent_label(entry, citations)
        confidence = previous.get("confidence")
        suggestions = followups(previous)
    else:
        # 上传资料 / 兜底回答：直接利用上一条回答的步骤与摘录
        blocks = [str(s) for s in (previous.get("steps") or [])][:3]
        if not blocks:
            intro_text = str(previous.get("intro") or "")
            blocks = [intro_text] if intro_text else []
        intro = f"接着上一个问题「{previous_question or previous_title}」，关于「{_CUE_TITLES[kind]}」，补充说明如下："
        title = f"接着上一个问题 · {previous_title or '上一轮回答'}"
        citations = list(previous.get("citations") or [])
        tone = str(previous.get("tone") or "blue")
        labels = str(previous.get("intent_label") or "追问")
        confidence = previous.get("confidence")
        suggestions = ["那要带什么材料？", "多久能办好？", "在哪里办理？"]

    if not blocks:
        return None

    return {
        "matched": True,
        "intent": previous_intent,
        "intent_label": labels,
        "title": title,
        "intro": intro,
        "steps": blocks,
        "tip": str(previous.get("tip") or ""),
        "tone": tone,
        "confidence": confidence,
        "citations": citations,
        "links": list(previous.get("links") or [["查看办事流程", "?page=services"]]),
        "attachments": [],
        "retrieval": list(previous.get("retrieval") or [])[:4],
        "suggestions": suggestions,
        "context_used": True,
    }


def followups(result: dict | None) -> list[str]:
    """基于命中条目生成 3 条追问建议。"""
    result = result if isinstance(result, dict) else {}
    intent = str(result.get("intent") or "")
    presets = {
        "student-id": ["那要带什么材料？", "多久能办好？", "在哪里办理？"],
        "aid-policies": ["家庭经济困难怎么认定？", "国家奖学金怎么申请？", "助学贷款怎么办理？"],
        "activities-latest": ["AI 创客马拉松怎么报名？", "活动能算第二课堂学分吗？", "这周还有哪些讲座？"],
        "notices-query": ["期末考试怎么安排？", "怎么订阅学院通知？", "重要通知在哪里看？"],
        "life-plan": ["大二应该重点做什么？", "想考研要提前准备什么？", "怎么找实习？"],
        "campus-card": ["那要带什么材料？", "多久能办好？", "在哪里办理？"],
        "library": ["怎么预约研讨间？", "可以借多少本书？", "期末周开放时间有变化吗？"],
        "scholarship": ["需要准备哪些材料？", "什么时候开始申请？", "国家励志奖学金和它冲突吗？"],
    }
    chosen = list(presets.get(intent) or [])
    if len(chosen) < 3:
        pool = [
            "那要带什么材料？",
            "多久能办好？",
            "在哪里办理？",
            "需要预约吗？",
            "还有哪些注意事项？",
        ]
        for item in pool:
            if item not in chosen:
                chosen.append(item)
            if len(chosen) >= 3:
                break
    return chosen[:3]


# --------------------------------------------------------------------------- #
# fallback / 问候
# --------------------------------------------------------------------------- #
def _fallback(question: str) -> dict[str, Any]:
    suggestions = [
        "学生证丢了怎么办？",
        "有哪些学生资助政策？",
        "最近有哪些校园活动？",
        "如何查询学校最新通知？",
    ]
    return {
        "matched": False,
        "intent": "",
        "intent_label": "",
        "title": "这个问题我还在学习",
        "intro": "校内知识库里暂时没有找到完全匹配的答案。你可以换个说法，或者直接点下面的高频问题试试。",
        "steps": [],
        "tip": "带上校区、时间等关键信息会更容易命中，例如「金明校区校园卡丢了，明天要考试」。",
        "tone": "gray",
        "confidence": None,
        "citations": [],
        "links": [["浏览办事流程", "?page=services"], ["查看校园活动", "?page=activities"]],
        "attachments": [],
        "retrieval": [],
        "suggestions": suggestions,
        "context_used": False,
        "raw_question": question,
    }


def _greeting(question: str) -> dict[str, Any]:
    return {
        "matched": True,
        "intent": "greeting",
        "intent_label": "问候",
        "title": "你好呀，我是河小智 👋",
        "intro": "我是河南大学 AI 智慧校园助手，可以帮你查政策、找流程、约活动、办事务。今天想先解决哪件小事？",
        "steps": [],
        "tip": "试试问我：「学生证丢了怎么办？」「有哪些学生资助政策？」",
        "tone": "blue",
        "confidence": 1.0,
        "citations": [],
        "links": [["去办事流程导航", "?page=services"], ["看看本周活动", "?page=activities"]],
        "attachments": [],
        "retrieval": [],
        "suggestions": ["学生证丢了怎么办？", "有哪些学生资助政策？", "最近有哪些校园活动？"],
        "context_used": False,
        "raw_question": question,
    }


# --------------------------------------------------------------------------- #
# 主问答
# --------------------------------------------------------------------------- #
def _answer(
    question: str,
    history: list[dict] | None = None,
    uploads: list[dict] | None = None,
) -> dict[str, Any]:
    raw = str(question or "").strip()
    if not raw:
        return _fallback(raw)

    cleaned = _clean(raw)
    if any(_clean(g) in cleaned for g in _GREETINGS) and len(cleaned) <= 12:
        return _greeting(raw)

    query_grams = _grams(raw)

    # 1) 连续追问：只有短追问才结合上文
    kind = _followup_kind(raw)
    if kind and history:
        previous_question, previous = _previous_context(history)
        if previous:
            followup = _followup_answer(kind, previous, previous_question)
            if followup:
                return followup

    # 2) 知识库条目打分
    entries = _entries()
    ranked = sorted(
        ((_score_entry(cleaned, query_grams, entry), entry) for entry in entries),
        key=lambda pair: pair[0],
        reverse=True,
    )
    best_raw, best_entry = ranked[0] if ranked else (0.0, None)
    best_norm = _normalize(best_raw)

    # 3) 上传资料打分（相关度高于知识库时优先使用）
    upload_candidates = _upload_candidates(uploads, cleaned, query_grams)
    top_upload = upload_candidates[0] if upload_candidates else None
    if top_upload and float(top_upload["score"]) >= 0.2 and (
        best_entry is None or float(top_upload["score"]) >= best_norm
    ):
        return _upload_answer(top_upload, query_grams)

    # 4) 命中知识库
    if best_entry is not None and best_raw >= 8:
        citations = _citations_for(best_entry, query_grams)
        result = {
            "matched": True,
            "intent": str(best_entry.get("id") or ""),
            "intent_label": _intent_label(best_entry, citations),
            "title": str(best_entry.get("title") or "河小智的回答"),
            "intro": str(best_entry.get("intro") or ""),
            "steps": [str(s) for s in (best_entry.get("steps") or [])],
            "tip": str(best_entry.get("tip") or ""),
            "tone": str(best_entry.get("tone") or "blue"),
            "confidence": best_norm,
            "citations": citations,
            "links": [list(link) for link in (best_entry.get("links") or []) if isinstance(link, (list, tuple))],
            "attachments": _attachments_for(best_entry),
            "retrieval": _retrieval_for(best_entry, citations, query_grams, best_norm),
            "suggestions": followups({"intent": best_entry.get("id")}),
            "context_used": False,
            "source": str(best_entry.get("source") or ""),
            "raw_question": raw,
        }
        if not result["links"]:
            result["links"] = [["查看办事流程", "?page=services"]]
        return result

    # 5) 上传资料单独命中（即使知识库没有答案）
    if top_upload:
        return _upload_answer(top_upload, query_grams)

    return _fallback(raw)


def answer(
    question: str,
    history: list[dict] | None = None,
    uploads: list[dict] | None = None,
) -> dict[str, Any]:
    """返回结构化回答；任何异常都兜底为 fallback。"""
    started = time.perf_counter()
    try:
        result = _answer(question, history=history, uploads=uploads)
    except Exception:  # pragma: no cover - 现场演示兜底
        result = _fallback(str(question or ""))
    result["raw_question"] = str(question or "").strip()
    result["elapsed_ms"] = max(1, int((time.perf_counter() - started) * 1000))
    return result


# --------------------------------------------------------------------------- #
# 知识库检索
# --------------------------------------------------------------------------- #
def search(query: str, limit: int = 6, uploads: list[dict] | None = None) -> list[dict]:
    """按关键词检索制度、问答与上传资料，返回可直接展示的条目。"""
    keyword = str(query or "").strip()
    if not keyword:
        return []
    cleaned = _clean(keyword)
    query_grams = _grams(keyword)
    results: list[dict] = []

    # 制度文档
    doc_index = _doc_index()
    entry_index = _entries()
    doc_questions: dict[str, str] = {}
    for entry in entry_index:
        for doc_id in entry.get("citations") or []:
            doc_questions.setdefault(str(doc_id), str(entry.get("question") or ""))

    for doc in _policy_docs():
        raw = _score_doc(cleaned, query_grams, doc)
        if raw <= 0:
            continue
        section = _best_section(doc, query_grams)
        results.append(
            {
                "source": "policy",
                "id": str(doc.get("id") or ""),
                "doc_id": str(doc.get("id") or ""),
                "kb_id": "",
                "title": str(doc.get("title") or ""),
                "snippet": _truncate(section.get("text") or doc.get("summary") or "", 110),
                "score": _normalize(raw),
                "meta": " · ".join(bit for bit in (doc.get("department"), doc.get("doc_no")) if bit),
                "question": doc_questions.get(str(doc.get("id") or ""), ""),
            }
        )

    # 问答条目
    for entry in entry_index:
        raw = _score_entry(cleaned, query_grams, entry)
        if raw <= 0:
            continue
        results.append(
            {
                "source": "faq",
                "id": str(entry.get("id") or ""),
                "doc_id": (entry.get("citations") or [""])[0],
                "kb_id": str(entry.get("id") or ""),
                "title": str(entry.get("question") or entry.get("title") or ""),
                "snippet": _truncate(entry.get("intro") or "", 110),
                "score": _normalize(raw),
                "meta": str(entry.get("source") or "校园问答库"),
                "question": str(entry.get("question") or ""),
            }
        )

    # 上传资料
    for chunk in _upload_candidates(uploads, cleaned, query_grams):
        results.append(
            {
                "source": "upload",
                "id": "",
                "doc_id": "",
                "kb_id": "",
                "title": f"{chunk['name']} · 第 {chunk['page']} 页",
                "snippet": _truncate(chunk.get("text") or "", 110),
                "score": round(float(chunk.get("score") or 0.0), 3),
                "meta": "个人资料",
                "question": keyword,
            }
        )

    # 去重并按分数排序
    deduped: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for item in sorted(results, key=lambda row: float(row.get("score") or 0), reverse=True):
        key = (str(item.get("source")), str(item.get("id")), str(item.get("title")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= max(1, int(limit)):
            break
    return deduped


# --------------------------------------------------------------------------- #
# 自检（python -m core.kb）
# --------------------------------------------------------------------------- #
if __name__ == "__main__":  # pragma: no cover
    samples = [
        "学生证丢了怎么办？",
        "有哪些学生资助政策？",
        "最近有哪些校园活动？",
        "如何查询学校最新通知？",
        "如何规划我的大学生活？",
        "校园卡丢了怎么补办？",
        "那要带什么材料？",
    ]
    for index, sample in enumerate(samples):
        history = []
        if index == 6:
            history = [
                {"role": "user", "content": "学生证丢了怎么办？"},
                {"role": "assistant", "content": answer("学生证丢了怎么办？")},
            ]
        result = answer(sample, history=history)
        print(
            f"{sample} -> {result.get('intent')} | {result.get('title')} | "
            f"置信度 {result.get('confidence')} | 引用 {len(result.get('citations') or [])}"
        )
