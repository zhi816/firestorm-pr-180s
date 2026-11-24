---
name: game-build-pipeline
description: >-
  End-to-end build and verification pipeline for firestorm-pr-180s (single-file HTML5/CSS/JS Pixel RPG game). Guides agents from picking up a TD-NNN task in docs/todo.md through implementation, browser verification on desktop and mobile, to atomic commit and push.
---

# Game Build Pipeline（遊戲開發與驗收總流程）

> 適用於接手 `docs/todo.md` 任務、實作或修改 `index.html` 與樣張時。開始任何步驟前，先確認已讀過根目錄 `AGENTS.md` 與 `DESIGN.md`。

---

## 五階段標準流程（S0 至 S4）

### S0｜接手與遠端預檢
1. 執行 `git-sync-guardian` 之 `status.py`，若落後遠端則執行 `sync.py`。
2. 執行進度掃描了解目前階段：
   ```bash
   python3 .agents/skills/game-build-pipeline/scripts/pipeline_status.py
   ```
3. 整份閱讀 `docs/todo.md` 鎖定本次指派的 `TD-NNN`；若該條目為 `waiting`，**不得擅自動工**，先詢問或回報等待項目。
4. 閱讀 `DESIGN.md` 第五至七章（待決事項與否決紀錄）與 `docs/issues.md`，確認不會重犯已被否決的設計或忽略既有問題。

### S1｜規格對齊與狀態標記
- 依任務性質精讀對應規格章節（不須盲目修改無關檔案）：
  - 程式架構、狀態機、JSON 格式、Fallback：`docs/dev/實作規格書.md`
  - 像素 Token、RPG 對照、版面、結局與點陣規範：`docs/art/美術設計規格書.md`
  - 參考可運行前端範例：`docs/art/samples/像素風格樣張_v3.html`
- 若為跨回合大型任務，可先將 `docs/todo.md` 對應 `TD-NNN` 狀態改為 `doing` 並填上 `- **負責**：<代理名稱>`。

### S2｜實作開發紅線（不可違反）
1. **單檔零建置**：正式遊戲必須是根目錄單一 `index.html`（內嵌 HTML + CSS + JS），不引入 npm / Vite / React / 外部靜態圖片檔。
2. **設計變數驅動**：色碼與字型一律使用 `美術設計規格書.md` 第三章 CSS 變數（`--night`、`--panel`、`--gold`、`--px`、`--long` 等）。
3. **虛構品牌與現代物件**：新聞台一律稱「炎上新聞台 FNN」、社群為「炎串」、爆料來源為「爆料版」，嚴禁出現真實台標或真人照片；道具只用現代物件（手機、補光燈、麥克風），不用奇幻城堡寶劍。
4. **雙端體驗**：電腦版（>1080px）維持三欄一次看完；手機版（<=760px）為頂部固定狀態列＋底部分頁＋階段式單屏切換＋直播聊天室，無橫向捲軸。
5. **雙引擎與防呆**：Groq / Gemini API Key 僅存 `localStorage`；回傳文字須以 Regex 清洗 ````json 標籤；空白或亂碼輸入判為神隱暴斃；斷網或 API 失敗無縫切換離線智囊庫，確保展演 100% 可玩。
6. **無障礙與動畫**：所有可點元素有 `--cyan` 2px 鍵盤焦點框；像素動畫使用 `steps()` 並尊重 `prefers-reduced-motion`。

### S3｜自我檢查與雙端瀏覽器驗證
完成程式碼後，依序執行：
1. **進度與文件 Lint**：
   ```bash
   python3 .agents/skills/game-build-pipeline/scripts/pipeline_status.py
   python3 .agents/skills/project-audit/scripts/lint_project.py
   ```
   `lint_project.py` 之 `ERROR` 必須為 0。
2. **雙端版面檢查（有瀏覽器工具或本機實測時必跑）**：
   於根目錄啟動本機伺服器 `python3 -m http.server 8781 --bind 127.0.0.1`，開啟 `http://127.0.0.1:8781/index.html`，執行 `.agents/skills/game-build-pipeline/scripts/verify_app.js` 驗證 `1360x900`（桌面）與 `390x844`（手機）皆 `FAIL 0`。
   若實測發現版面或功能缺陷且本回合未立即修完，必須登記為 `FP-NNN` 於 `docs/issues.md`。

### S4｜文件同步與原子交付
1. 若完成整項 `TD-NNN`，直接從 `docs/todo.md` 刪除該條目；若僅完成部分進度，於該條目追加 `- **進度**：...` 並改回 `open`。
2. 若里程碑狀態改變，同步勾選 `README.md` 的「目前進度」清單；若有新增檔案，同步更新 `docs/index.md`。
3. 以 `log_time.py` 取得臺北時間，在 `docs/log.md` 結尾追加一筆紀錄（寫明完成之 `TD-NNN` 編號、執行代理與模型版本）。
4. 使用 `git-sync-guardian` 之 `safe_commit_push.py` 一次提交並推送（記得帶 `--todo TD-NNN` 與 `--agent "<代理名稱>"`）。
