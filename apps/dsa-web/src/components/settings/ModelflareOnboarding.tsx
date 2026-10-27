import type React from 'react';
import { useEffect, useState } from 'react';
import { getParsedApiError } from '../../api/error';
import { systemConfigApi } from '../../api/systemConfig';
import { useUiLanguage } from '../../contexts/UiLanguageContext';
import type { SystemConfigItem, TestLLMChannelResponse } from '../../types/systemConfig';
import { Button } from '../common';
import { modelflareConnectionMessage } from './modelflareErrors';

const SIGNUP_URL = 'https://modelflare.dev/sign-up?utm_source=github&utm_campaign=mf_daily_stock_analysis';
const DEFAULT_BASE_URL = 'https://modelflare.dev/v1';

const DIRECT_LLM_KEYS = new Set([
  'GEMINI_API_KEY',
  'GEMINI_API_KEYS',
  'OPENAI_API_KEY',
  'OPENAI_API_KEYS',
  'ANTHROPIC_API_KEY',
  'ANTHROPIC_API_KEYS',
  'DEEPSEEK_API_KEY',
  'DEEPSEEK_API_KEYS',
  'AIHUBMIX_KEY',
  'ANSPIRE_API_KEYS',
  'LITELLM_API_KEY',
  'LITELLM_CONFIG',
  'LLM_CHANNELS',
  'OLLAMA_API_BASE',
  'OLLAMA_MODEL',
]);

function isConfigured(item: { value?: string | null; rawValueExists?: boolean }): boolean {
  if (item.rawValueExists === false) return false;
  return String(item.value ?? '').trim().length > 0;
}

export function hasUsableLlmChannel(items: SystemConfigItem[]): boolean {
  if (items.some((item) => (item.key === 'MODELFLARE_API_KEY' || item.key === 'MODELFLARE_KEY') && isConfigured(item))) {
    return true;
  }
  return items.some((item) => {
    if (!isConfigured(item)) return false;
    return DIRECT_LLM_KEYS.has(item.key) || /^LLM_[A-Z0-9_]+_API_KEYS?$/.test(item.key);
  });
}

function failureCopy(result: TestLLMChannelResponse, baseUrl: string, language: string): string {
  const friendly = modelflareConnectionMessage({
    baseUrl,
    reason: typeof result.details?.reason === 'string' ? result.details.reason : '',
    error: result.error,
    message: result.message,
    model: result.resolvedModel || 'gpt-6.1-sol',
    httpStatus: typeof result.details?.http_status === 'number' ? result.details.http_status : null,
    language,
  });
  return friendly || result.message || result.error || (language === 'en' ? 'Connection failed' : '连接失败');
}

export const ModelflareOnboarding: React.FC<{ className?: string; onSaved?: () => void }> = ({
  className,
  onSaved,
}) => {
  const { language } = useUiLanguage();
  const en = language === 'en';
  const [visible, setVisible] = useState(false);
  const [configVersion, setConfigVersion] = useState('');
  const [maskToken, setMaskToken] = useState('******');
  const [baseUrl, setBaseUrl] = useState(DEFAULT_BASE_URL);
  const [apiKey, setApiKey] = useState('');
  const [pending, setPending] = useState(false);
  const [notice, setNotice] = useState('');
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        if (typeof systemConfigApi.getConfig !== 'function') return;
        const config = await systemConfigApi.getConfig(false);
        if (cancelled || !config?.items) return;
        setConfigVersion(config.configVersion || '');
        setMaskToken(config.maskToken || '******');
        const savedBase = config.items.find((item) => item.key === 'MODELFLARE_BASE_URL');
        const nextBase = String(savedBase?.value ?? '').trim();
        if (nextBase) setBaseUrl(nextBase);
        setVisible(!hasUsableLlmChannel(config.items));
      } catch {
        // Hidden when settings cannot be read, including mocked test APIs.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (!visible) return null;

  const save = async () => {
    const key = apiKey.trim();
    if (!key || pending) return;
    setPending(true);
    setFailed(false);
    setNotice('');
    try {
      await systemConfigApi.update({
        configVersion,
        maskToken,
        reloadNow: true,
        items: [{ key: 'MODELFLARE_API_KEY', value: key }],
      });
      const result = await systemConfigApi.testLLMChannel({
        name: 'modelflare',
        protocol: 'openai',
        baseUrl,
        apiKey: key,
        models: ['gpt-6.1-sol'],
        enabled: true,
      });
      if (result.success) {
        setNotice(en ? 'Connected' : '已连通');
        setFailed(false);
        onSaved?.();
        return;
      }
      setFailed(true);
      setNotice(failureCopy(result, baseUrl, language));
    } catch (error: unknown) {
      setFailed(true);
      setNotice(getParsedApiError(error).message || (en ? 'Save failed' : '保存失败'));
    } finally {
      setPending(false);
    }
  };

  return (
    <section className={`rounded-2xl border settings-border bg-card/90 px-4 py-4 shadow-soft-card ${className || ''}`}>
      <h2 className="text-sm font-semibold text-foreground">{en ? 'Connect Modelflare' : '连接 Modelflare'}</h2>
      <p className="mt-1 text-xs leading-5 text-muted-text">
        {en
          ? 'One API key is enough. The default model is gpt-6.1-sol.'
          : '只需一把 API Key。默认模型是 gpt-6.1-sol。'}
        {' '}
        <a className="text-cyan underline" href={SIGNUP_URL} target="_blank" rel="noreferrer">
          {en ? 'Get a key' : '获取 Key'}
        </a>
      </p>
      <div className="mt-3 flex flex-col gap-2 sm:flex-row">
        <input
          type="password"
          autoComplete="off"
          value={apiKey}
          placeholder="sk-..."
          aria-label="MODELFLARE_API_KEY"
          className="h-10 min-w-0 flex-1 rounded-xl border settings-border bg-background px-3 text-sm text-foreground"
          onChange={(event) => setApiKey(event.target.value)}
        />
        <Button type="button" variant="settings-primary" size="sm" disabled={pending || !apiKey.trim()} onClick={() => void save()}>
          {pending ? (en ? 'Testing...' : '测试中...') : (en ? 'Save and test' : '保存并测试')}
        </Button>
      </div>
      {notice ? (
        <p className={`mt-2 text-xs leading-5 ${failed ? 'text-danger' : 'text-emerald-600 dark:text-emerald-300'}`}>{notice}</p>
      ) : null}
    </section>
  );
};
