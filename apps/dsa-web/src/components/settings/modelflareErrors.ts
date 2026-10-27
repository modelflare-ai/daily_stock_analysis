const KEY_URL = 'https://modelflare.dev/keys';
const DASHBOARD_URL = 'https://modelflare.dev/dashboard';

const BALANCE_RE = /quota|balance|insufficient|额度|余额/i;
const GROUP_RE = /model_not_found|分组/;
const AUTH_RE = /invalid(?:\s+api)?\s+key|unauthorized|authentication/i;

export function isModelflareBaseUrl(baseUrl?: string | null): boolean {
  const raw = (baseUrl || '').trim();
  if (!raw) return false;
  try {
    return new URL(raw).hostname.toLowerCase().includes('modelflare.dev');
  } catch {
    return raw.toLowerCase().includes('modelflare.dev');
  }
}

function displayModel(model?: string | null): string {
  const text = (model || '').trim().replace(/^openai\//, '');
  return text || 'gpt-6.1-sol';
}

function statusFromText(text: string, status?: number | null): number | null {
  if (typeof status === 'number') return status;
  const match = text.match(/\b(401|402|403|429|503)\b/);
  if (match) return Number(match[1]);
  if (/\bforbidden\b/i.test(text)) return 403;
  return null;
}

export function modelflareConnectionMessage(input: {
  baseUrl?: string | null;
  reason?: string | null;
  error?: string | null;
  message?: string | null;
  model?: string | null;
  httpStatus?: number | null;
  language?: string | null;
}): string | undefined {
  if (!isModelflareBaseUrl(input.baseUrl)) return undefined;
  const blob = `${input.error || ''} ${input.message || ''}`;
  const reason = input.reason || '';
  const status = statusFromText(`${blob} ${reason}`, input.httpStatus);
  const en = (input.language || '').toLowerCase().startsWith('en');
  const model = displayModel(input.model);
  const balance = BALANCE_RE.test(blob) || BALANCE_RE.test(reason);
  const group = GROUP_RE.test(blob) || reason === 'model_not_found' || reason === 'model_access_denied';
  const auth = AUTH_RE.test(blob) || reason === 'api_key_rejected';
  const keyCopy = en
    ? `Your Modelflare API key is invalid or revoked. Get a key at ${KEY_URL}`
    : `Modelflare API Key 无效或已停用。请到 ${KEY_URL} 复制新的 Key。`;
  const balanceCopy = en
    ? `Insufficient Modelflare balance. Top up at ${DASHBOARD_URL}`
    : `Modelflare 余额不足，请充值：${DASHBOARD_URL}`;
  const groupCopy = en
    ? `This Modelflare key's group cannot call model ${model}. Change the group at ${KEY_URL} or pick another model.`
    : `当前 Key 的分组无法调用模型 ${model}，请在 ${KEY_URL} 调整分组，或换一个模型。`;

  if (status === 401 || (auth && status !== 402 && status !== 403 && status !== 429 && status !== 503 && !group)) {
    return keyCopy;
  }
  if (
    status === 402
    || reason === 'insufficient_balance'
    || reason === 'quota_exceeded'
    || ((status === 403 || status === 429) && balance)
  ) {
    return balanceCopy;
  }
  if (status === 403 || group || (status === 503 && group)) {
    return groupCopy;
  }
  return undefined;
}
