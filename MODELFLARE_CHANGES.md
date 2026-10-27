# Modelflare Edition changes

This fork keeps upstream `ZhuLinsen/daily_stock_analysis` behavior for every other provider, prompt, and analysis path. A user can run with only `MODELFLARE_API_KEY` (optional `MODELFLARE_BASE_URL`, default `https://modelflare.dev/v1`). `MODELFLARE_KEY` remains a legacy alias. The default model stays `openai/gpt-6.1-sol`.

In-app sponsor links, including `utm_source=daily_stock_analysis&utm_campaign=app` and the upstream `utm_campaign=daily_stock_analysis` banners, were intentionally left unchanged.

Upstream sync is `.github/workflows/mf-upstream-sync.yml`. It fetches `https://github.com/ZhuLinsen/daily_stock_analysis.git` directly (no repo variable), uses `secrets.MF_SYNC_TOKEN` with a `github.token` fallback, merges (never rebases or force-pushes), opens an issue and aborts on conflict, and otherwise pushes `sync/upstream-YYYYMMDD` and opens a PR. It does not delete upstream workflow files.

## Files

- `.env.example` — documents `MODELFLARE_API_KEY` as the one-key setup and keeps `MODELFLARE_KEY` as the legacy name. Adds the `LLM_MODELFLARE_BASE_URL=` example the daily-analysis workflow test expects.
- `.github/workflows/00-daily-analysis.yml` — passes both `MODELFLARE_API_KEY` and `MODELFLARE_KEY`. The config guard treats either key as configured. A step before analysis runs `python -m src.services.modelflare_smoke` and fails with the friendly message when a key is set but the call fails. The step exits 0 when no key is present.
- `.github/workflows/mf-upstream-sync.yml` — weekly/manual upstream merge described above.
- `README.md` — Modelflare Edition header above `<!-- MF-END -->`. Quick start deploy command is `MODELFLARE_API_KEY=sk-xxx docker compose -f docker/docker-compose.yml up -d server`. Default model `gpt-6.1-sol`. Signup link uses `utm_campaign=mf_daily_stock_analysis`. `<!-- MF-SCREENSHOT -->` is a placeholder only. Original README body below the marker is unchanged.
- `docs/README_EN.md` — same header in English, with `<!-- MF-SCREENSHOT -->`. Original lines below the marker are unchanged.
- `docs/README_CHT.md` — same header: English paragraphs kept, Chinese paragraphs translated into Traditional Chinese, with `<!-- MF-SCREENSHOT -->`. Original lines below the marker are unchanged.
- `docs/CHANGELOG.md` — one Unreleased note for the one-key alias, friendly errors, onboarding, and Actions smoke check.
- `api/app.py` — best-effort startup smoke on a background thread so the server still boots if Modelflare is down. The task is cancelled on shutdown.
- `docker/docker-compose.yml` — injects `MODELFLARE_API_KEY` and `MODELFLARE_BASE_URL` (default `https://modelflare.dev/v1`). No extra compose file.
- `src/config.py` — `resolve_llm_channel_names` / `resolve_llm_channel_api_keys` accept `MODELFLARE_API_KEY` first and `MODELFLARE_KEY` second. Explicit channel keys and explicit `LLM_CHANNELS` still win. Blank base URL for the `modelflare` channel uses `MODELFLARE_BASE_URL` or `https://modelflare.dev/v1`.
- `src/core/config_registry.py` — settings schema for `MODELFLARE_API_KEY`, optional `MODELFLARE_BASE_URL`, and legacy `MODELFLARE_KEY`.
- `src/services/system_config_service.py` — exposes those three settings keys to the Web config API.
- `src/llm/modelflare_errors.py` — friendly copy used only when the base URL host contains `modelflare.dev`. 401 / invalid key, 402 or 403/429 balance-quota text, and 403 or 503 `model_not_found` / 分组 are separate messages. Other hosts return `None` so the caller keeps the original error.
- `src/services/modelflare_smoke.py` — one tiny chat completion for startup and for `python -m src.services.modelflare_smoke`. Reuses the helper above. Does not log the key. 403 is a group error unless the body matches balance/quota.
- `src/analyzer.py` — the LiteLLM error text and the analysis failure shown to notifications pass through `rewrite_modelflare_error`. Non-Modelflare failures are unchanged.
- `src/notification.py` — Modelflare failure text that contains `modelflare.dev` may use 240 characters so the friendly URL is not cut at 100. Other notifications stay at 100.
- `apps/dsa-web/src/components/settings/modelflareErrors.ts` — same host check and copy for the Web UI.
- `apps/dsa-web/src/components/settings/LLMChannelEditor.tsx` — connection-test text for a `modelflare.dev` base URL (or a blank URL on a channel named `modelflare`) replaces `api_key_rejected`, `insufficient_balance`, and `quota_exceeded` with that copy, and maps plain 403 / `model_not_found` to the group message. Other providers keep the old hints. Editing the shorthand key writes `MODELFLARE_API_KEY` and clears a stored `MODELFLARE_KEY`.
- `apps/dsa-web/src/components/settings/llmProviderTemplates.ts` — Modelflare preset models are only `gpt-6.1-sol`, `gpt-6-sol`, `gpt-6-astra`, `claude-sonnet-5`, `claude-opus-5-5`, `gemini-3.1-pro-preview`, and `grok-4.7`.
- `apps/dsa-web/src/components/settings/ModelflareOnboarding.tsx` — one key field, shown only when no usable LLM channel and neither Modelflare key is set. Save writes `MODELFLARE_API_KEY` through `systemConfigApi.update`, then calls `testLLMChannel`. Success shows 已连通; failure shows the friendly reason.
- `apps/dsa-web/src/pages/SettingsPage.tsx` — mounts that card next to `FirstRunSetupCard`. `FirstRunSetupCard` itself is unchanged.
- `apps/dsa-web/src/pages/HomePage.tsx` — one mount above the existing setup banner.
- `apps/dsa-web/src/pages/__tests__/HomePage.test.tsx` — market-review tests now allow the single onboarding `getConfig` read. They still assert the review request is not a saved config write.
- `apps/dsa-web/src/components/settings/__tests__/LLMChannelEditor.test.tsx` — shorthand save expects `MODELFLARE_API_KEY`, and the new-channel preset matches the strong model list.
- `apps/dsa-web/src/components/settings/__tests__/llmProviderTemplates.test.ts` — same preset list.
- `tests/test_llm_channel_config.py` — `MODELFLARE_API_KEY` resolves the channel name and key, wins over `MODELFLARE_KEY`, and does not override an explicit channel key.
- `tests/test_daily_analysis_workflow_llm_env.py` — still requires `MODELFLARE_KEY` in the analysis step and also requires `MODELFLARE_API_KEY` plus the smoke step.
- `tests/test_modelflare_errors.py` — 401 key, 402/403/429 balance, 403 and 503 group, and a non-Modelflare URL left unchanged.

## Not done

- No screenshot was generated. `<!-- MF-SCREENSHOT -->` is only a marker.
- Web unit tests were not executed here (`apps/dsa-web/node_modules` is not installed).
- The full backend suite was not run. The Modelflare pytest files below passed: 102 tests.
