// 從根目錄 index.html 抽出 Worker 組裝 Prompt 所需的資料，寫成 src/prompt-data.js。
//
// 遊戲資料（角色、事件、策略）與兩位 AI 的 Prompt（index.html 中「PROMPT 區塊」：CROWD_PROMPT、JUDGE_PROMPT、
// crowdPrompt()、judgePrompt()）只在 index.html 維護一份，本腳本把它們原樣搬進 Worker，
// 避免兩邊說法不一致（見 docs/dev/實作規格書.md 第四、七章）。
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

// 2. PROMPT 區塊：原樣複製進 Worker 模組（Worker 不允許 eval，故以原始碼形式輸出）
const START = "/* ==== PROMPT 區塊開始", END = "/* ==== PROMPT 區塊結束 ==== */";
const blockStart = html.indexOf(START);
const blockEnd = html.indexOf(END);
if (blockStart < 0 || blockEnd < blockStart) throw new Error("index.html 找不到 PROMPT 區塊標記");
const promptBlock = html.slice(html.indexOf("\n", blockStart) + 1, blockEnd).trimEnd();
const EXPORTS = ["CROWD_NAMES", "CROWD_PROMPT", "JUDGE_PROMPT", "crowdPrompt", "judgePrompt"];

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

const header = `// 本檔由 worker/build.mjs 從根目錄 index.html 自動產生，請勿手動修改。
// 改了 index.html 的角色、事件、策略或 PROMPT 區塊（兩位 AI 的 Prompt）後，執行 node worker/build.mjs 重新產生。
`;
const dataSrc = `export const CHARACTERS = ${JSON.stringify(characters, null, 2)};

export const EVENTS = ${JSON.stringify(events, null, 2)};

const tacticsOf = ev => [...ev.forms, ...ev.talks];
export const findTactic = (ev, id) => tacticsOf(ev).find(t => t.id === id);
`;

// 先在沙盒裡實際跑一次兩支 Prompt 函式，確認區塊沒有引用 Worker 不存在的變數
{
  const sandbox = vm.createContext({});
  const probe = dataSrc.replace(/^export /gm, "") + "\n" + promptBlock + "\n;(() => {" +
    "const ev = Object.values(EVENTS)[0];" +
    "const c = { char: ev.characters.find(x => CHARACTERS[x]) || Object.keys(CHARACTERS)[0], event: ev, tactics: [ev.forms[0].id, ev.talks[0].id], text: '測試聲明', prevFlaws: ['上次的敗筆'] };" +
    "return [typeof CROWD_PROMPT, typeof JUDGE_PROMPT, crowdPrompt(c), judgePrompt(c, ['a','b','c','d','e','f']), judgePrompt(c, null)];" +
    "})()";
  const r = vm.runInContext(probe, sandbox);
  if (r[0] !== "string" || r[1] !== "string" || !r[2].includes("測試聲明") || !r[3].includes("顯微鏡柯南：a") || !r[4].includes("網友留言暫時載入失敗")) {
    throw new Error("PROMPT 區塊試跑結果不符預期");
  }
}

const out = `${header}
${dataSrc}
${promptBlock}

export { ${EXPORTS.join(", ")} };
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
