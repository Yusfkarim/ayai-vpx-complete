// anakin.ai guest chat client — باشترین app ی خۆڕایی + واژووی ڕەسەن
// stdin: {"model_id": 309, "messages": [{"role","content"}...], "system": "...", "app_id": 19510}
// stdout: {"ok":true,"answer":"..."} یان {"ok":false,"error":"..."}
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const objectHash = require(path.join(__dirname, 'anakin_objecthash.js'));
const crypto = require('node:crypto');

const SECRET = '^wqZ*7@*2zTd2vcqPC9YWYgbwpq4dm&ZF9cQxpckt3Vge%';
const FE_VERSION = "1.0.4-release.202512191850";
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36";

function sign(body) {
  const ts = Date.now();
  const bh = objectHash(JSON.parse(JSON.stringify(body)), {
    respectFunctionProperties: false, respectType: false, respectFunctionNames: false,
    unorderedArrays: false, unorderedSets: true, unorderedObjects: true, ignoreUnknown: true,
  });
  const rc = objectHash(bh + SECRET + ts, { algorithm: 'md5' });
  const sc = objectHash(rc + SECRET + ts, { algorithm: 'md5' });
  const ss = objectHash(SECRET.replace('7', '2').replace('9', '1'), { algorithm: 'md5' });
  return { ts, sc, rc, ss };
}

async function anakinChat(appId, modelId, content, messages = [], prompt = "", timeoutMs = 90000) {
  const body = {
    uniqId: Math.random().toString(36).slice(2, 23),
    appConversationId: "10010" + Math.random().toString(36).slice(2, 12),
    type: "CHAT_BOT",
    prompt,
    inputSchema: [],
    embedding: { fileIds: [] },
    greeting: { text: "", defaultQuestions: [], chatAssistant: { autoSuggestion: true } },
    model: { modelId },
    modelId,
    messages,
    scene: "TRY_IT_OUT",
    content,
  };
  Object.assign(body, sign(body));
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const r = await fetch(`https://api.anakin.ai/api/v1/workspaces/0/apps/${appId}/draft-conversation-messages?locale=en-US`, {
      method: "POST",
      signal: ctrl.signal,
      headers: {
        "Content-Type": "application/json",
        "User-Agent": UA,
        "Origin": "https://app.anakin.ai", "Referer": "https://app.anakin.ai/",
        "x-device-id": crypto.randomUUID(),
        "x-client-mode": "web",
        "x-client-version": FE_VERSION,
        "Accept": "text/event-stream",
      },
      body: JSON.stringify(body),
    });
    if (r.status !== 200) {
      const t2 = await r.text().catch(() => '');
      throw Object.assign(new Error("anakin http " + r.status), { code: r.status, body: t2.slice(0, 200) });
    }
    const txt = await r.text();
    let err = null, out = '';
    for (const line of txt.split('\n')) {
      if (!line.startsWith('data: ')) continue;
      const d = line.slice(6).trim();
      if (d === '[DONE]') break;
      try {
        const j = JSON.parse(d);
        if (j.errorCode) { err = "anakin errorCode " + j.errorCode; break; }
        if (j.event === undefined && j.content !== undefined && j.content !== '') {
          // completed = وەڵامی تەواو — delta تەنها پارچەیە؛ completed دوات دێت → بیگۆڕە
          out = j.content;
        }
      } catch (e) {}
    }
    if (err) throw Object.assign(new Error(err), { code: 429 });
    if (!String(out).trim()) throw new Error("anakin: بەتاڵ");
    return String(out).trim();
  } finally {
    clearTimeout(t);
  }
}

import fs from 'node:fs';
const raw = fs.readFileSync(0, 'utf8');
let req = {};
try { req = JSON.parse(raw); } catch (e) { console.log(JSON.stringify({ ok: false, error: "bad input" })); process.exit(0); }
const appId = req.app_id || 19510;
const modelId = req.model_id || 309;
const prompt = String(req.system || '').slice(0, 1200);
const msgsIn = Array.isArray(req.messages) ? req.messages : [];
let content = '';
let messages = [];
if (msgsIn.length) {
  const hist = msgsIn.filter(m => m.role === 'user' || m.role === 'assistant');
  const last = hist[hist.length - 1];
  content = (last && last.role === 'user') ? last.content : (msgsIn[msgsIn.length - 1] || {}).content || '';
  messages = hist.slice(0, -1).slice(-16).map(m => ({ role: m.role, content: String(m.content || '').slice(0, 6000) }));
} else {
  content = String(req.content || '');
}
try {
  const answer = await anakinChat(appId, modelId, content, messages, prompt);
  console.log(JSON.stringify({ ok: true, answer }));
} catch (e) {
  console.log(JSON.stringify({ ok: false, error: String(e.message || e).slice(0, 120), code: e.code }));
}
