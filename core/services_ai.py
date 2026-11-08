# -*- coding: utf-8 -*-
"""河小智 · 办事需求 AI 识别与办理计划生成。

功能（对应办事流程导航页「AI 办事助手」）：

- ``recognize(need) -> dict``      识别用户输入的办事需求，匹配最合适的流程
- ``build_plan(process) -> dict``  根据命中的流程生成办理计划与待办清单

实现说明：流程数据来自 ``core.data.PROCESSES``（整理自河南大学官网公开信息，
每条均标注依据来源）。识别算法为「关键词命中 + 2-gram 覆盖度」加权打分，
与 ``core.kb`` 问答引擎同一套思路，纯标准库、不依赖外部模型与网络，
现场演示稳定；后续可无缝替换为 LLM + 向量检索。

任何异常都会兜底为未识别结果，绝不向上抛出。
"""

from __future__ import annotations

import re
import time
from typing import Any

from . import data

_PUNCT = re.compile(r"[\s，。！？、；：,.!?;:~～（）()【】\[\]“”\"'《》<>·—\-_/\\|]+")

# 打分权重：关键词命中是最强信号，其次标题 / 摘要 / 步骤的 2-gram 覆盖度。
_KEYWORD_BASE = 14.0
_KEYWORD_LENGTH_BONUS = 1.6  # 每个字符（上限 8）额外加权
_TITLE_WEIGHT = 30.0
_SUMMARY_WEIGHT = 8.0
_STEPS_WEIGHT = 5.0
_META_WEIGHT = 5.0
_MATCH_THRESHOLD = 10.0  # 至少要有一个关键词或较强的语义重叠才算命中


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


def _score_process(cleaned: str, query_grams: set[str], item: dict) -> tuple[float, list[str]]:
    """返回（得分, 命中的关键词列表）。"""
    score = 0.0
    hits: list[str] = []
    for keyword in item.get("keywords") or []:
        key = _clean(keyword)
        if key and key in cleaned:
            score += _KEYWORD_BASE + min(len(key), 8) * _KEYWORD_LENGTH_BONUS
            hits.append(str(keyword))
    score += _overlap(query_grams, item.get("title")) * _TITLE_WEIGHT
    score += _overlap(query_grams, item.get("summary")) * _SUMMARY_WEIGHT
    score += _overlap(query_grams, " ".join(str(s) for s in (item.get("steps") or []))) * _STEPS_WEIGHT
    meta = " ".join(str(item.get(part) or "") for part in ("category", "department", "location"))
    score += _overlap(query_grams, meta) * _META_WEIGHT
    return score, hits


def recognize(need: str) -> dict[str, Any]:
    """识别用户输入的办事需求。

    返回字段：
    - ``matched``      是否命中流程
    - ``process``      命中的流程条目（未命中为 None）
    - ``confidence``   置信度 0—1
    - ``keywords``     命中的关键词
    - ``alternatives`` 备选流程（最多 2 条）
    - ``hint``         未命中时的引导提示
    """
    raw = str(need or "").strip()
    if not raw:
        return _no_match("请先输入你的办事需求。")

    cleaned = _clean(raw)
    query_grams = _grams(raw)

    scored: list[tuple[float, dict, list[str]]] = []
    for item in data.PROCESSES:
        score, hits = _score_process(cleaned, query_grams, item)
        scored.append((score, item, hits))
    scored.sort(key=lambda pair: pair[0], reverse=True)

    best_score, best_item, best_hits = scored[0]
    alternatives = [
        {"id": item.get("id") or "", "title": str(item.get("title") or "")}
        for score, item, _hits in scored[1:4]
        if score > 0
    ][:2]

    if best_item is None or best_score < _MATCH_THRESHOLD:
        return _no_match(
            "暂时没有匹配到具体流程。你可以换一种说法，"
            "例如「校园卡丢了」「想转专业」「生病没法参加考试」「医保怎么报销」。",
            alternatives=alternatives,
        )

    confidence = round(min(0.97, best_score / 40.0), 2)
    return {
        "matched": True,
        "process": best_item,
        "confidence": confidence,
        "keywords": best_hits,
        "alternatives": alternatives,
        "hint": "",
        "need": raw,
        "recognized_at": time.strftime("%Y-%m-%d %H:%M"),
    }


def _no_match(hint: str, alternatives: list[dict] | None = None) -> dict[str, Any]:
    return {
        "matched": False,
        "process": None,
        "confidence": 0.0,
        "keywords": [],
        "alternatives": list(alternatives or []),
        "hint": hint,
        "need": "",
        "recognized_at": time.strftime("%Y-%m-%d %H:%M"),
    }


def build_plan(process: dict) -> dict[str, Any]:
    """根据命中的流程自动生成待办清单。

    待办 = 材料准备项（每项材料一条）+ 办理动作项（每个步骤一条）。
    """
    process_id = str(process.get("id") or "plan")
    todos: list[dict[str, str]] = []

    for index, material in enumerate(process.get("materials") or [], 1):
        todos.append(
            {
                "id": f"{process_id}-m{index}",
                "label": f"准备材料：{material}",
                "kind": "材料",
                "tone": "gold",
            }
        )
    for index, step in enumerate(process.get("steps") or [], 1):
        todos.append(
            {
                "id": f"{process_id}-s{index}",
                "label": step,
                "kind": f"步骤 {index}",
                "tone": "blue",
            }
        )

    return {
        "process": process,
        "todos": todos,
        "generated_at": time.strftime("%Y-%m-%d %H:%M"),
    }


def quick_examples() -> list[str]:
    """输入框下方的示例需求（点击即发起一次识别）。"""
    return [
        "校园卡丢了怎么补办？",
        "期末生病没法参加考试怎么办？",
        "想换个专业怎么申请？",
        "生病住院了医保怎么报销？",
        "成绩单怎么申请电子版？",
        "这学期想申请国家奖学金",
    ]


# --------------------------------------------------------------------------- #
# 自检（python -m core.services_ai）
# --------------------------------------------------------------------------- #
if __name__ == "__main__":  # pragma: no cover
    samples = [
        "校园卡丢了怎么补办？",
        "我生病了没法参加期末考试",
        "想从化学专业转到计算机",
        "去图书馆借两本书",
        "住院花了八千块能报吗",
        "今天食堂吃什么",
    ]
    for sample in samples:
        result = recognize(sample)
        process = result.get("process") or {}
        print(
            f"{sample!r} -> matched={result['matched']} "
            f"process={process.get('title')} conf={result['confidence']} "
            f"keywords={result['keywords']}"
        )
