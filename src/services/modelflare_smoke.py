"""Small, non-blocking Modelflare first-run connectivity check.

The check is deliberately independent from the full LiteLLM setup so a user
who only filled MODELFLARE_API_KEY gets a clear result during server startup.
It never runs for other providers and never logs the key.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.llm.modelflare_errors import friendly_modelflare_error

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://modelflare.dev/v1"
DEFAULT_MODEL = "gpt-6.1-sol"


def _friendly_error(status: int | None, detail: str, *, model: str, base_url: str) -> str:
    mapped = friendly_modelflare_error(
        status=status,
        detail=detail,
        model=model,
        base_url=base_url,
        language="zh",
    )
    if mapped:
        return mapped
    return f"Modelflare 连接失败：{detail or 'unknown error'}"


@dataclass
class SmokeOutcome:
    skipped: bool
    ok: bool
    message: str | None = None
    model: str = DEFAULT_MODEL


def _configured_key() -> str:
    return (os.getenv("MODELFLARE_API_KEY") or os.getenv("MODELFLARE_KEY") or "").strip()


def run_smoke() -> SmokeOutcome:
    """Send one tiny Chat Completions request when a Modelflare key is set."""
    api_key = _configured_key()
    if not api_key:
        return SmokeOutcome(skipped=True, ok=True)
    base_url = (os.getenv("MODELFLARE_BASE_URL") or DEFAULT_BASE_URL).strip().rstrip("/")
    model = (os.getenv("LITELLM_MODEL") or "").strip()
    if model.startswith("openai/"):
        model = model[7:]
    model = model or DEFAULT_MODEL
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
        "temperature": 0,
    }).encode("utf-8")
    request = Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "daily-stock-analysis-modelflare/0.1",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:  # noqa: S310 - configured HTTPS endpoint
            if 200 <= response.status < 300:
                return SmokeOutcome(skipped=False, ok=True, model=model)
            detail = response.read(500).decode("utf-8", "replace")
            return SmokeOutcome(
                skipped=False,
                ok=False,
                message=_friendly_error(response.status, detail, model=model, base_url=base_url),
                model=model,
            )
    except HTTPError as exc:
        detail = exc.read(1000).decode("utf-8", "replace")
        return SmokeOutcome(
            skipped=False,
            ok=False,
            message=_friendly_error(exc.code, detail, model=model, base_url=base_url),
            model=model,
        )
    except URLError as exc:
        return SmokeOutcome(
            skipped=False,
            ok=False,
            message=_friendly_error(None, str(exc.reason), model=model, base_url=base_url),
            model=model,
        )
    except Exception as exc:  # pragma: no cover - defensive startup guard
        return SmokeOutcome(
            skipped=False,
            ok=False,
            message=_friendly_error(None, str(exc), model=model, base_url=base_url),
            model=model,
        )


def smoke_failure_message() -> str | None:
    """Friendly failure text, or None when the check is skipped or connected."""
    outcome = run_smoke()
    if outcome.skipped or outcome.ok:
        return None
    return outcome.message or "Modelflare 连接失败：unknown error"


def run_startup_smoke() -> None:
    """Log one tiny Chat Completions result when a Modelflare key is set."""
    outcome = run_smoke()
    if outcome.skipped:
        return
    if outcome.ok:
        logger.info("Modelflare 已连通（模型：%s）", outcome.model)
        return
    logger.warning("%s", outcome.message or "Modelflare 连接失败：unknown error")


def main() -> int:
    if not _configured_key():
        print("No Modelflare key; skip connectivity check")
        return 0
    message = smoke_failure_message()
    if message:
        print(message)
        return 1
    print("Modelflare 已连通")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

