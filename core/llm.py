# -*- coding: utf-8 -*-
"""河小智 · 大模型 API 客户端（Anthropic Messages 协议）。

设计目标：

- **零新增依赖**：只用标准库 ``urllib``，离线包 ``.deps`` 不需要重装。
- **密钥不进代码**：优先读环境变量，其次读项目根目录 ``.env``；
  ``.env`` 不会被提交或打包时才需要特别注意（含密钥，勿外发）。
- **可随时关掉**：把 ``.env`` 里的 ``HXZ_LLM`` 设为 ``0``，或删掉密钥，
  问答立刻回到纯本地知识库模式，页面功能不受影响。

配置项（环境变量优先，其次 .env）：

========================  ==========================================
``HXZ_LLM``               1 启用 / 0 关闭，默认有密钥即启用
``HXZ_API_BASE``          接口地址，默认 https://cn.sidrune.ai
``HXZ_API_KEY``           密钥；也兼容 ANTHROPIC_AUTH_TOKEN
``HXZ_MODEL``             模型，默认 deepseek-v4-flash
``HXZ_API_TIMEOUT``       单次请求超时秒数，默认 45
========================  ==========================================
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _ROOT / ".env"

DEFAULT_BASE = "https://cn.sidrune.ai"
DEFAULT_MODEL = "deepseek-v4-flash"

_env_cache: dict[str, str] | None = None


class LLMError(RuntimeError):
    """API 调用失败（网络、鉴权、超时、返回格式异常等）。"""


def _file_env() -> dict[str, str]:
    """读取项目根目录 .env（简单 KEY=VALUE 格式，支持引号与注释）。"""
    global _env_cache
    if _env_cache is not None:
        return _env_cache
    data: dict[str, str] = {}
    try:
        raw = _ENV_FILE.read_text(encoding="utf-8")
    except Exception:
        raw = ""
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            data[key] = value
    _env_cache = data
    return data


def reload_config() -> None:
    """修改 .env 后调用，可在不重启服务的情况下生效。"""
    global _env_cache
    _env_cache = None


def _get(*names: str, default: str = "") -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return str(value).strip()
    file_env = _file_env()
    for name in names:
        value = file_env.get(name)
        if value:
            return str(value).strip()
    return default


def config() -> dict[str, Any]:
    """返回当前生效配置（密钥会被打码，便于在页面上安全展示）。"""
    key = _get("HXZ_API_KEY", "ANTHROPIC_AUTH_TOKEN")
    base = _get("HXZ_API_BASE", "ANTHROPIC_BASE_URL", default=DEFAULT_BASE).rstrip("/")
    model = _get("HXZ_MODEL", default=DEFAULT_MODEL)
    switch = _get("HXZ_LLM", default="")
    enabled = bool(key) and switch.lower() not in {"0", "false", "off", "no"}
    try:
        timeout = float(_get("HXZ_API_TIMEOUT", default="45"))
    except ValueError:
        timeout = 45.0
    timeout = max(5.0, min(timeout, 120.0))
    return {
        "enabled": enabled,
        "base": base or DEFAULT_BASE,
        "model": model or DEFAULT_MODEL,
        "key": key,
        "key_masked": (key[:6] + "…" + key[-4:]) if len(key) > 12 else ("已配置" if key else "未配置"),
        "timeout": timeout,
    }


def is_enabled() -> bool:
    return bool(config()["enabled"])


def _extract_text(payload: dict[str, Any]) -> str:
    """Anthropic 返回的 content 是块数组，可能包含 thinking 块，只取正文。"""
    parts: list[str] = []
    for block in payload.get("content") or []:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            parts.append(str(block.get("text") or ""))
    if not parts and isinstance(payload.get("content"), str):
        parts.append(str(payload["content"]))
    return "\n".join(part for part in parts if part).strip()


def chat(
    messages: list[dict[str, str]],
    system: str = "",
    max_tokens: int = 1200,
    temperature: float = 0.3,
    timeout: float | None = None,
) -> str:
    """调用大模型，返回纯文本回答；失败抛出 :class:`LLMError`。

    ``messages`` 使用 Anthropic 格式：[{"role": "user"|"assistant", "content": "..."}]。
    """
    cfg = config()
    if not cfg["enabled"]:
        raise LLMError("未配置 API 密钥，当前为本地知识库模式")

    body: dict[str, Any] = {
        "model": cfg["model"],
        "max_tokens": int(max_tokens),
        "temperature": float(temperature),
        "messages": messages,
    }
    if system:
        body["system"] = system

    request = urllib.request.Request(
        url=cfg["base"] + "/v1/messages",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "content-type": "application/json",
            "accept": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": cfg["key"],
            "authorization": "Bearer " + cfg["key"],
            "user-agent": "HeXiaoZhi/1.0",
        },
    )

    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout or cfg["timeout"]) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:  # 4xx / 5xx：读出服务端错误信息
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        raise LLMError(f"API 返回 HTTP {exc.code}：{detail or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise LLMError(f"无法连接 API：{exc.reason}") from exc
    except TimeoutError as exc:
        raise LLMError("API 响应超时") from exc
    except Exception as exc:  # pragma: no cover - 兜底，绝不让页面崩掉
        raise LLMError(f"API 调用失败：{exc}") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMError("API 返回的不是合法 JSON") from exc

    if isinstance(payload, dict) and payload.get("error"):
        raise LLMError("API 报错：" + str(payload["error"])[:300])

    text = _extract_text(payload if isinstance(payload, dict) else {})
    if not text:
        raise LLMError("API 没有返回正文内容")

    _ = started  # 保留计时点，便于后续做耗时统计
    return text
