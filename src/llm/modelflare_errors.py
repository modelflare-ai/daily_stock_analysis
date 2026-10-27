# -*- coding: utf-8 -*-
"""Friendly Modelflare errors. Other provider hosts are left unchanged."""

from __future__ import annotations

import re
from typing import Any, Optional
from urllib.parse import urlparse

KEY_URL = "https://modelflare.dev/keys"
WALLET_URL = "https://modelflare.dev/wallet"
DEFAULT_MODEL = "gpt-6.1-sol"

_ZH_KEY = f"Modelflare API Key 无效或已停用。请到 {KEY_URL} 复制新的 Key。"
_EN_KEY = f"Your Modelflare API key is invalid or revoked. Get a key at {KEY_URL}"
_ZH_BALANCE = f"Modelflare 余额不足，请充值：{WALLET_URL}"
_EN_BALANCE = f"Insufficient Modelflare balance. Top up at {WALLET_URL}"

_KNOWN_PREFIXES = (
    "Modelflare API Key 无效或已停用。",
    "Your Modelflare API key is invalid or revoked.",
    "当前 Key 的分组无法调用模型",
    "This Modelflare key's group cannot call model",
    "Modelflare 余额不足，请充值：",
    "Insufficient Modelflare balance.",
)
_AUTH_RE = re.compile(r"invalid(?:\s+api)?\s+key|unauthorized|authentication", re.IGNORECASE)
_BALANCE_RE = re.compile(r"quota|balance|insufficient|额度|余额", re.IGNORECASE)
_GROUP_RE = re.compile(r"model_not_found|分组")
_STATUS_RE = re.compile(r"\b(401|402|403|429|503)\b")
_BASE_RE = re.compile(r"https?://[^\s\"']*modelflare\.dev[^\s\"']*", re.IGNORECASE)


def is_modelflare_base_url(base_url: Optional[str]) -> bool:
    """True only when the endpoint host contains modelflare.dev."""
    raw = (base_url or "").strip()
    if not raw:
        return False
    try:
        host = (urlparse(raw).hostname or "").lower()
    except ValueError:
        return False
    return "modelflare.dev" in host


def display_model(model: str) -> str:
    text = (model or "").strip()
    if text.startswith("openai/"):
        text = text[7:]
    return text or DEFAULT_MODEL


def _language(language: str) -> str:
    return "zh" if (language or "zh").lower().startswith("zh") else "en"


def _messages(language: str, model: str) -> dict[str, str]:
    shown = display_model(model)
    if _language(language) == "en":
        return {
            "key": _EN_KEY,
            "balance": _EN_BALANCE,
            "group": (
                f"This Modelflare key's group cannot call model {shown}. "
                f"Change the group at {KEY_URL} or pick another model."
            ),
        }
    return {
        "key": _ZH_KEY,
        "balance": _ZH_BALANCE,
        "group": f"当前 Key 的分组无法调用模型 {shown}，请在 {KEY_URL} 调整分组，或换一个模型。",
    }


def _extract_known(detail: str) -> Optional[str]:
    best: Optional[tuple[int, str]] = None
    for prefix in _KNOWN_PREFIXES:
        index = detail.find(prefix)
        if index < 0:
            continue
        line = detail[index:].splitlines()[0].strip()
        if best is None or index < best[0]:
            best = (index, line)
    return best[1] if best else None


def _status_from_detail(detail: str, status: Optional[int]) -> Optional[int]:
    if status is not None:
        return status
    match = _STATUS_RE.search(detail or "")
    return int(match.group(1)) if match else None


def friendly_modelflare_error(
    *,
    status: Optional[int] = None,
    detail: str = "",
    model: str = "",
    base_url: Optional[str] = None,
    language: str = "zh",
) -> Optional[str]:
    """Return Modelflare copy, or None when the host or failure does not match.

    403 is a group error unless the body matches a balance/quota signal.
    Callers should keep their original text when this returns None.
    """
    text = detail or ""
    known = _extract_known(text)
    if known:
        return known
    resolved = (base_url or "").strip() or (_BASE_RE.search(text).group(0) if _BASE_RE.search(text) else "")
    if not is_modelflare_base_url(resolved):
        return None

    status_code = _status_from_detail(text, status)
    if status_code is None and re.search(r"\bforbidden\b", text, re.IGNORECASE):
        status_code = 403
    messages = _messages(language, model)
    balance = _BALANCE_RE.search(text) is not None
    group = _GROUP_RE.search(text) is not None
    auth = _AUTH_RE.search(text) is not None
    if status_code == 401 or (auth and status_code not in {402, 403, 429, 503}):
        return messages["key"]
    if status_code == 402 or (status_code in {403, 429} and balance):
        return messages["balance"]
    if status_code == 403 or (status_code == 503 and group):
        return messages["group"]
    return None


def base_url_from_model_list(model_list: Any, model: str = "") -> str:
    """Return the Modelflare api_base for this model, if it is unambiguous."""
    selected = (model or "").strip()
    modelflare_urls: list[str] = []
    other = False
    for deployment in model_list or []:
        if not isinstance(deployment, dict):
            continue
        params = deployment.get("litellm_params") or {}
        if not isinstance(params, dict):
            continue
        api_base = str(params.get("api_base") or "").strip()
        if not api_base:
            continue
        names = {
            str(deployment.get("model_name") or "").strip(),
            str(params.get("model") or "").strip(),
        }
        names.discard("")
        if is_modelflare_base_url(api_base):
            if selected and selected in names:
                return api_base
            modelflare_urls.append(api_base)
        else:
            other = True
    if modelflare_urls and not other:
        return modelflare_urls[0]
    return ""


def rewrite_modelflare_error(
    text: str,
    *,
    model: str = "",
    model_list: Any = None,
    base_url: str = "",
    language: str = "zh",
) -> str:
    """Replace a Modelflare failure with friendly copy; leave every other error as-is."""
    friendly = friendly_modelflare_error(
        detail=text or "",
        model=model,
        base_url=base_url or base_url_from_model_list(model_list, model),
        language=language,
    )
    return friendly or text
