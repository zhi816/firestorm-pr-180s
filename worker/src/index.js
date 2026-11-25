// 炎上大作戰：Cloudflare Worker 中繼伺服器（docs/dev/實作規格書.md 第七章）
//
// 讓玩家不必輸入金鑰就能使用 AI 判讀，金鑰只存在 Worker 的加密變數（Secret）。
// - 兩位 AI 依序呼叫（docs/dev/實作規格書.md 第四章）：POST /crowd 網民大軍留言、POST /judge 公關裁判長判讀。
// - 前端只送 { character, event_id, tactics, statement, revise_of }（/judge 另附 crowd 網民留言），
//   Prompt 由本程式組裝，模型與 max_tokens 鎖死，回應只回傳白名單欄位，避免被當成通用 AI 代理。
// - 限流：每次 AI 呼叫各算 1 次，每 IP 每小時上限、全站每日上限（臺北時間 0 點重置），超過回 429，前端改走離線模式。
// - 聲明稿上限 500 字，超過直接拒絕。
//
// 環境變數（Cloudflare 後台 Settings > Variables and Secrets）：
//   COMMAND_CODE_API_KEY    必填，類型選 Secret
//   IP_HOURLY_LIMIT         選填，每 IP 每小時 AI 呼叫上限，預設 60（每局送審 2 次）
//   DAILY_LIMIT             選填，全站每日 AI 呼叫上限，預設 600
//   CROWD_MODEL             選填，網民大軍模型，預設 Qwen/Qwen3.7-Flash
//   JUDGE_MODEL             選填，公關裁判長模型，預設 xiaomi/mimo-v2.6-flash
//   MODEL                   選填，同時覆蓋兩位角色的模型（優先度低於 CROWD_MODEL / JUDGE_MODEL）
//   CROWD_REASONING_EFFORT  選填，網民大軍推理檔位（如 off / low / omit）
//   JUDGE_REASONING_EFFORT  選填，公關裁判長推理檔位（如 off / low / omit）
//   REASONING_EFFORT        選填，同時覆蓋兩位角色的推理檔位
//   ALLOWED_ORIGINS         選填，允許呼叫的網頁來源，逗號分隔，預設 https://zhi816.github.io
import { DurableObject } from "cloudflare:workers";
import { CHARACTERS, EVENTS, findTactic, CROWD_PROMPT, JUDGE_PROMPT, crowdPrompt, judgePrompt } from "./prompt-data.js";

const UPSTREAM = "https://api.commandcode.ai/provider/v1/chat/completions";
// 與 index.html 的 DEFAULT_MODELS / AI_KINDS / MODEL_EFFORT 一致：網民重網感與速度，裁判重穩定結構
const KINDS = {
  crowd: { model: "Qwen/Qwen3.7-Flash", system: CROWD_PROMPT, user: c => crowdPrompt(c), max_tokens: 2000, temperature: 0.9 },
  judge: { model: "xiaomi/mimo-v2.6-flash", system: JUDGE_PROMPT, user: c => judgePrompt(c, c.crowd), max_tokens: 2000, temperature: 0.7 }
};
const MODEL_EFFORT = {
  "deepseek/deepseek-v4.1-flash-fast": "off",
  "deepseek/deepseek-v4.1-flash": "off",
  "deepseek/deepseek-v4-flash-fast": "low",
  "tencent/hy4-flash": "off",
  "Qwen/Qwen3.8-Flash": "low",
  "z-ai/glm-5.3-flash": "low"
};
const UPSTREAM_TIMEOUT_MS = 30000;   // 診斷 Qwen3.7 / MiMo 實際耗時與 token 用量，確認後再調回合理上限
const STATEMENT_MAX = 500;           // 與 index.html 聲明稿輸入框 maxlength 一致
const COMMENT_MAX = 80;              // 網民留言每則上限（與前端 normalizeCrowd() 一致）
const BODY_MAX = 8192;
const DEFAULT_ORIGINS = ["https://zhi816.github.io"];
const RED_FLAGS = ["threat_lawsuit", "guilt_trip", "profanity", "contradiction"];
const HOUR_MS = 3600000, DAY_MS = 86400000, TAIPEI_OFFSET_MS = 8 * HOUR_MS;

/* ==================== 限流（Durable Object，SQLite 儲存，免費方案可用） ==================== */
export class RateLimiter extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec("CREATE TABLE IF NOT EXISTS hits (k TEXT PRIMARY KEY, n INTEGER NOT NULL, exp INTEGER NOT NULL)");
  }
  // 同一個 Durable Object 內的呼叫依序執行，計數不會互相覆蓋
  hit(ipKey, ipLimit, dayLimit) {
    const now = Date.now();
    this.sql.exec("DELETE FROM hits WHERE exp < ?", now);
    const b = buckets(now);
    const ipK = `ip:${ipKey}:${b.hour}`, dayK = `day:${b.day}`;
    const get = k => {
      const rows = this.sql.exec("SELECT n FROM hits WHERE k = ?", k).toArray();
      return rows.length ? rows[0].n : 0;
    };
    const verdict = decide(get(ipK), get(dayK), ipLimit, dayLimit, b);
    if (!verdict.ok) return verdict;
    const bump = (k, exp) => this.sql.exec(
      "INSERT INTO hits (k, n, exp) VALUES (?, 1, ?) ON CONFLICT(k) DO UPDATE SET n = n + 1", k, exp);
    bump(ipK, b.hourEnd);
    bump(dayK, b.dayEnd);
    return verdict;
  }
}

function buckets(now) {
  const hour = Math.floor(now / HOUR_MS);
  const day = Math.floor((now + TAIPEI_OFFSET_MS) / DAY_MS);
  return { hour, day, hourEnd: (hour + 1) * HOUR_MS, dayEnd: (day + 1) * DAY_MS - TAIPEI_OFFSET_MS, now };
}
function decide(ipN, dayN, ipLimit, dayLimit, b) {
  if (dayN >= dayLimit) return { ok: false, reason: "daily_limit", retryAfter: Math.ceil((b.dayEnd - b.now) / 1000) };
  if (ipN >= ipLimit) return { ok: false, reason: "ip_limit", retryAfter: Math.ceil((b.hourEnd - b.now) / 1000) };
  return { ok: true };
}

// 未綁定 Durable Object 時的備援：只在單一執行個體記憶體內計數，重啟即歸零，僅供本機測試
const memHits = new Map();
function memoryHit(ipKey, ipLimit, dayLimit) {
  const b = buckets(Date.now());
  for (const [k, v] of memHits) if (v.exp < b.now) memHits.delete(k);
  const ipK = `ip:${ipKey}:${b.hour}`, dayK = `day:${b.day}`;
  const verdict = decide((memHits.get(ipK) || {}).n || 0, (memHits.get(dayK) || {}).n || 0, ipLimit, dayLimit, b);
  if (!verdict.ok) return verdict;
  memHits.set(ipK, { n: ((memHits.get(ipK) || {}).n || 0) + 1, exp: b.hourEnd });
  memHits.set(dayK, { n: ((memHits.get(dayK) || {}).n || 0) + 1, exp: b.dayEnd });
  return verdict;
}

async function rateLimit(env, ip) {
  const ipLimit = positiveInt(env.IP_HOURLY_LIMIT, 60);
  const dayLimit = positiveInt(env.DAILY_LIMIT, 600);
  const ipKey = await sha256Short(ip);   // 只存雜湊，不存原始 IP
  if (!env.LIMITER) return memoryHit(ipKey, ipLimit, dayLimit);
  const stub = env.LIMITER.get(env.LIMITER.idFromName("global"));
  return stub.hit(ipKey, ipLimit, dayLimit);
}

/* ==================== 小工具 ==================== */
function positiveInt(v, d) {
  const n = parseInt(v, 10);
  return Number.isFinite(n) && n > 0 ? n : d;
}
async function sha256Short(s) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(buf)].slice(0, 8).map(x => x.toString(16).padStart(2, "0")).join("");
}
function allowedOrigin(env, origin) {
  if (!origin) return null;
  const list = env.ALLOWED_ORIGINS
    ? env.ALLOWED_ORIGINS.split(",").map(s => s.trim()).filter(Boolean)
    : DEFAULT_ORIGINS;
  if (list.includes(origin)) return origin;
  // 本機開發（python3 -m http.server）一律放行
  if (/^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/.test(origin)) return origin;
  return null;
}
function corsHeaders(origin) {
  return origin ? {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin"
  } : { "Vary": "Origin" };
}
function json(status, body, origin, extra = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", ...corsHeaders(origin), ...extra }
  });
}

/* ==================== 輸入驗證 ==================== */
function validate(body, kind) {
  if (!body || typeof body !== "object") return { error: "bad_json" };
  const ch = CHARACTERS[body.character];
  const ev = EVENTS[body.event_id];
  if (!ch) return { error: "bad_character" };
  if (!ev) return { error: "bad_event" };
  if (!ev.characters.includes("ALL") && !ev.characters.includes(body.character)) return { error: "bad_event" };
  if (typeof body.statement !== "string") return { error: "bad_statement" };
  const text = body.statement.trim();
  if (!text) return { error: "empty_statement" };
  if (text.length > STATEMENT_MAX) return { error: "statement_too_long" };
  const tactics = Array.isArray(body.tactics) ? [...new Set(body.tactics)] : [];
  if (tactics.length > 8 || tactics.some(id => typeof id !== "string" || !findTactic(ev, id))) return { error: "bad_tactics" };
  let prevFlaws = null;
  if (body.revise_of != null) {
    if (!Array.isArray(body.revise_of) || body.revise_of.length > 3 || body.revise_of.some(s => typeof s !== "string")) {
      return { error: "bad_revise_of" };
    }
    prevFlaws = body.revise_of.map(s => s.trim().slice(0, 60)).filter(Boolean);
    if (!prevFlaws.length) prevFlaws = null;
  }
  let crowd = null;
  if (kind === "judge" && body.crowd != null) {
    if (!Array.isArray(body.crowd) || body.crowd.length > 6 || body.crowd.some(s => typeof s !== "string")) {
      return { error: "bad_crowd" };
    }
    crowd = body.crowd.map(s => s.trim().slice(0, COMMENT_MAX));
    if (crowd.length < 6 || crowd.some(s => !s)) crowd = null;
  }
  return { c: { char: body.character, event: ev, tactics, text, prevFlaws, crowd } };
}

/* ==================== 回應白名單（與 index.html 的 normalizeCrowd()、normalizeJudge() 對應） ==================== */
const str = (v, n) => (typeof v === "string" ? v.trim().slice(0, n) : "");
function sanitizeCrowd(j) {
  if (!j || !Array.isArray(j.comments) || j.comments.length < 6) return null;
  const comments = j.comments.slice(0, 6).map(x => str(typeof x === "string" ? x : String((x && x.comment) || ""), COMMENT_MAX));
  return comments.every(Boolean) ? { comments } : null;
}
function sanitizeJudge(j) {
  if (!j || typeof j !== "object") return null;
  const int100 = v => (v !== null && v !== "" && Number.isFinite(+v) ? Math.max(0, Math.min(100, Math.round(+v))) : null);
  const out = {};
  if (Array.isArray(j.inquiries) && j.inquiries.length === 3) {
    out.inquiries = j.inquiries.map(x => (String(x).includes("answer") ? "answered" : "dodged"));
  }
  if (Array.isArray(j.critical_flaws)) {
    const f = j.critical_flaws.slice(0, 3).map(x => str(String(x), 60)).filter(Boolean);
    if (f.length) out.critical_flaws = f;
  }
  if (Array.isArray(j.red_flags)) out.red_flags = [...new Set(j.red_flags.filter(f => RED_FLAGS.includes(f)))];
  out.ghostwrite_suspect = j.ghostwrite_suspect === true;
  for (const k of ["core_attitude", "expert_verdict", "headline"]) {
    const v = str(j[k], 60);
    if (v) out[k] = v;
  }
  const s = int100(j.sincerity), h = int100(j.shirking);
  if (s !== null) out.sincerity = s;
  if (h !== null) out.shirking = h;
  // 連誠意與逐題判讀都沒有，視為無效輸出
  if (out.sincerity === undefined && !out.inquiries) return null;
  return out;
}
const SANITIZE = { crowd: sanitizeCrowd, judge: sanitizeJudge };

/* ==================== 呼叫 Command Code ==================== */
function resolveModelConfig(env, kind) {
  const modelKey = kind === "crowd" ? "CROWD_MODEL" : "JUDGE_MODEL";
  const effortKey = kind === "crowd" ? "CROWD_REASONING_EFFORT" : "JUDGE_REASONING_EFFORT";
  const model = (env[modelKey] || env.MODEL || KINDS[kind].model).trim();
  const rawEffort = env[effortKey] !== undefined ? env[effortKey] : env.REASONING_EFFORT;
  let effort = null;
  if (rawEffort !== undefined) {
    const trimmed = String(rawEffort).trim();
    if (trimmed && trimmed !== "omit") effort = trimmed;
  } else {
    effort = MODEL_EFFORT[model] || null;
  }
  return { model, effort };
}

async function callUpstream(env, kind, c) {
  const k = KINDS[kind];
  const { model, effort } = resolveModelConfig(env, kind);
  const payload = {
    model,
    temperature: k.temperature,
    max_tokens: k.max_tokens,
    messages: [{ role: "system", content: k.system }, { role: "user", content: k.user(c) }]
  };
  if (effort) payload.reasoning_effort = effort;
  const res = await fetch(env.UPSTREAM_URL || UPSTREAM, {
    method: "POST",
    signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
    headers: { "Authorization": "Bearer " + env.COMMAND_CODE_API_KEY, "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) return { error: "upstream_http", status: res.status, diag: { model, reasoning_effort: effort } };
  const data = await res.json();
  const choice = (data && data.choices && data.choices[0]) || {};
  const msg = choice.message || {};
  let raw = String(msg.content || "");
  // 診斷資訊只含模型、結束原因、長度與 token 用量，不含任何模型輸出或聲明稿內容
  const u = (data && data.usage) || {};
  const diag = {
    model,
    reasoning_effort: effort,
    finish_reason: choice.finish_reason || null,
    content_chars: raw.length,
    reasoning_chars: String(msg.reasoning_content || msg.reasoning || "").length,
    prompt_tokens: u.prompt_tokens ?? null,
    completion_tokens: u.completion_tokens ?? null,
    reasoning_tokens: (u.completion_tokens_details && u.completion_tokens_details.reasoning_tokens) ?? null
  };
  raw = raw.replace(/```json/gi, "").replace(/```/g, "").trim();
  const m = raw.match(/\{[\s\S]*\}/);
  if (!m) return { error: "upstream_no_json", diag };
  let parsed;
  try { parsed = JSON.parse(m[0]); } catch (e) { return { error: "upstream_bad_json", diag }; }
  const result = SANITIZE[kind](parsed);
  return result ? { result, diag } : { error: "upstream_bad_json", diag };
}

/* ==================== 入口 ==================== */
async function handleAI(kind, request, env, origin) {
  if (!env.COMMAND_CODE_API_KEY) return json(503, { error: "not_configured" }, origin);
  const raw = await request.text();
  if (raw.length > BODY_MAX) return json(413, { error: "body_too_large" }, origin);
  let body;
  try { body = JSON.parse(raw); } catch (e) { return json(400, { error: "bad_json" }, origin); }
  const v = validate(body, kind);
  if (v.error) return json(400, { error: v.error }, origin);

  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const rl = await rateLimit(env, ip);
  if (!rl.ok) {
    console.log(JSON.stringify({ event: "rate_limited", kind, reason: rl.reason }));
    return json(429, { error: rl.reason }, origin, { "Retry-After": String(rl.retryAfter) });
  }

  const started = Date.now();
  let r;
  try { r = await callUpstream(env, kind, v.c); }
  catch (e) { r = { error: e && e.name === "TimeoutError" ? "upstream_timeout" : "upstream_fetch" }; }
  // 只記錄結果代碼與耗時，不記錄聲明稿內容
  console.log(JSON.stringify({ event: kind, ok: !r.error, error: r.error, status: r.status, ms: Date.now() - started, ...(r.diag || {}) }));
  if (r.error) return json(r.error === "upstream_timeout" ? 504 : 502, { error: r.error, diag: r.diag || null }, origin);
  return json(200, { [kind]: r.result, diag: r.diag }, origin);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = allowedOrigin(env, request.headers.get("Origin"));

    if (request.method === "GET" && (url.pathname === "/" || url.pathname === "/health")) {
      return json(200, { ok: true, service: "firestorm-relay", ready: Boolean(env.COMMAND_CODE_API_KEY) }, origin);
    }
    const kind = url.pathname === "/crowd" ? "crowd" : url.pathname === "/judge" ? "judge" : null;
    if (!kind) return json(404, { error: "not_found" }, origin);
    if (request.method === "OPTIONS") {
      return origin ? new Response(null, { status: 204, headers: corsHeaders(origin) }) : json(403, { error: "origin_not_allowed" }, null);
    }
    if (request.method !== "POST") return json(405, { error: "method_not_allowed" }, origin, { "Allow": "POST, OPTIONS" });
    if (!origin) return json(403, { error: "origin_not_allowed" }, null);
    return handleAI(kind, request, env, origin);
  }
};
