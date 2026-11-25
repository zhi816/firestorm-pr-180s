// 從根目錄 index.html 抽出 Worker 組裝 Prompt 所需的資料，寫成 src/prompt-data.js。
//
// 遊戲資料（角色、事件、策略）、SYSTEM_PROMPT 與 userPrompt() 只在 index.html 維護一份，
// 本腳本把它們原樣搬進 Worker，避免兩邊說法不一致（見 docs/dev/實作規格書.md 第七章）。
//
// 用法（於倉庫根目錄或 worker/ 內皆可）：
//   node worker/build.mjs          重新產生 src/prompt-data.js
//   node worker/build.mjs --check  只檢查是否與 index.html 同步，不同步時以結束碼 1 離開
//
// wrangler.toml 的 [build] 會在每次 wrangler deploy 前自動執行本腳本。
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const here = dirname(fileURLToPath(import.meta.url));
const htmlPath = join(here, "..", "index.html");
const outPath = join(here, "src", "prompt-data.js");

const html = readFileSync(htmlPath, "utf8");

function between(src, start, end, label) {
  const a = src.indexOf(start);
  if (a < 0) throw new Error(`index.html 找不到 ${label} 的起點：${start}`);
  const b = src.indexOf(end, a + start.length);
  if (b < 0) throw new Error(`index.html 找不到 ${label} 的終點：${end}`);
  return src.slice(a, b);
}

// 1. 遊戲資料區塊：從「遊戲資料」區段標題到「小工具」區段標題
const dataChunk = between(html, "/* ==================== 遊戲資料", "/* ==================== 小工具", "遊戲資料區塊");
const ctx = vm.createContext({});
const data = vm.runInContext(dataChunk + "\n;({ CHARACTERS, CRISIS_EVENTS })", ctx);

// 2. SYSTEM_PROMPT（樣板字串內不含插值，直接求值）
const sysChunk = between(html, "const SYSTEM_PROMPT = `", "`;\n", "SYSTEM_PROMPT") + "`;";
const SYSTEM_PROMPT = vm.runInContext(sysChunk + "\nSYSTEM_PROMPT", vm.createContext({}));

// 3. userPrompt() 原始碼：原樣複製進 Worker 模組（Worker 不允許 eval，故以原始碼形式輸出）
const userPromptSrc = between(html, "function userPrompt(c){", "async function callLLMJudge", "userPrompt()").trimEnd();

// 只保留組 Prompt 與驗證輸入需要的欄位，其餘（數值、關鍵字、離線留言、畫面效果）不帶進 Worker
const characters = {};
for (const [id, ch] of Object.entries(data.CHARACTERS)) {
  characters[id] = { name: ch.name, role: ch.role, desc: ch.desc };
}
const events = {};
for (const ev of data.CRISIS_EVENTS) {
  events[ev.id] = {
    id: ev.id,
    title: ev.title,
    bg_alert: ev.bg_alert,
    characters: ev.characters,
    inquiries: ev.inquiries.map(x => ({ q: x.q })),
    forms: ev.forms.map(t => ({ id: t.id, label: t.label })),
    talks: ev.talks.map(t => ({ id: t.id, label: t.label }))
  };
}

const out = `// 本檔由 worker/build.mjs 從根目錄 index.html 自動產生，請勿手動修改。
// 改了 index.html 的角色、事件、策略、SYSTEM_PROMPT 或 userPrompt() 後，執行 node worker/build.mjs 重新產生。

export const SYSTEM_PROMPT = ${JSON.stringify(SYSTEM_PROMPT)};

export const CHARACTERS = ${JSON.stringify(characters, null, 2)};

export const EVENTS = ${JSON.stringify(events, null, 2)};

const tacticsOf = ev => [...ev.forms, ...ev.talks];
export const findTactic = (ev, id) => tacticsOf(ev).find(t => t.id === id);

export ${userPromptSrc}
`;

const check = process.argv.includes("--check");
const current = existsSync(outPath) ? readFileSync(outPath, "utf8") : "";
if (check) {
  if (current === out) {
    console.log("[OK] worker/src/prompt-data.js 與 index.html 同步");
    process.exit(0);
  }
  console.error("[FAIL] worker/src/prompt-data.js 與 index.html 不同步，請執行 node worker/build.mjs");
  process.exit(1);
}
if (current === out) {
  console.log("[OK] worker/src/prompt-data.js 已是最新，未改寫");
} else {
  writeFileSync(outPath, out);
  console.log(`[OK] 已產生 worker/src/prompt-data.js（角色 ${Object.keys(characters).length} 位、事件 ${Object.keys(events).length} 則）`);
}
