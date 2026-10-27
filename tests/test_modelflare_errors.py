# -*- coding: utf-8 -*-
"""Friendly Modelflare error copy stays off other providers."""

from src.llm.modelflare_errors import friendly_modelflare_error, rewrite_modelflare_error

ZH_KEY = "Modelflare API Key 无效或已停用。请到 https://modelflare.dev/keys 复制新的 Key。"
EN_KEY = "Your Modelflare API key is invalid or revoked. Get a key at https://modelflare.dev/keys"
ZH_BALANCE = "Modelflare 余额不足，请充值：https://modelflare.dev/wallet"
EN_BALANCE = "Insufficient Modelflare balance. Top up at https://modelflare.dev/wallet"
BASE = "https://modelflare.dev/v1"
MODEL = "gpt-6.1-sol"


def test_invalid_key_401_is_split_from_group_and_balance() -> None:
    assert friendly_modelflare_error(
        status=401, detail="invalid api key", model=MODEL, base_url=BASE, language="zh",
    ) == ZH_KEY
    assert friendly_modelflare_error(
        status=None, detail="Unauthorized", model=MODEL, base_url=BASE, language="en",
    ) == EN_KEY


def test_402_and_quota_messages_are_balance_not_group() -> None:
    assert friendly_modelflare_error(
        status=402, detail="payment required", model=MODEL, base_url=BASE,
    ) == ZH_BALANCE
    assert friendly_modelflare_error(
        status=403, detail="insufficient quota", model=MODEL, base_url=BASE, language="en",
    ) == EN_BALANCE
    assert friendly_modelflare_error(
        status=429, detail="余额不足", model=MODEL, base_url="https://api.modelflare.dev/v1",
    ) == ZH_BALANCE


def test_403_and_model_not_found_are_group_errors() -> None:
    group = friendly_modelflare_error(
        status=403, detail="forbidden", model=f"openai/{MODEL}", base_url=BASE,
    )
    assert group == (
        "当前 Key 的分组无法调用模型 gpt-6.1-sol，"
        "请在 https://modelflare.dev/keys 调整分组，或换一个模型。"
    )
    assert "余额" not in (group or "")
    service = friendly_modelflare_error(
        status=503,
        detail='{"error":{"code":"model_not_found"}}',
        model=MODEL,
        base_url=BASE,
        language="en",
    )
    assert service is not None
    assert "gpt-6.1-sol" in service
    assert service.startswith("This Modelflare key's group cannot call model")


def test_non_modelflare_url_is_unchanged() -> None:
    original = "Error code: 401 - invalid api key"
    assert friendly_modelflare_error(
        status=401, detail=original, model=MODEL, base_url="https://api.openai.com/v1",
    ) is None
    assert rewrite_modelflare_error(original, model=MODEL, base_url="https://api.openai.com/v1") == original
    assert friendly_modelflare_error(
        status=403, detail="forbidden model_not_found", base_url="https://gateway.example.com/v1",
    ) is None
