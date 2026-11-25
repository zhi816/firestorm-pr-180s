# AGENTS.md - 炎上大作戰：危機公關 180 秒（維護與協作手冊）

> **專案核心精神**：
> 《炎上大作戰：危機公關 180 秒》（Firestorm PR: 180s Crisis Survival）是一套以純前端單檔（`index.html`）部署於 GitHub Pages 的互動式危機公關模擬遊戲。
> 本專案採用 **LLM Wiki 文件架構 + 多 AI 異步協作規範**，方便使用者於手機端隨時檢視進度與指派待辦任務，並確保不同 AI 代理（Claude Code、Codex、Antigravity 等）接力開發時脈絡不中斷、版面不走樣、歷史紀錄不遺失。
> **格式硬性規範**：所有治理文件（`AGENTS.md`、`DESIGN.md`、`CLAUDE.md`、`README.md`、`docs/index.md`、`docs/log.md`、`docs/issues.md`、`docs/todo.md`）與新寫程式碼中，**嚴格禁止使用任何表情符號（Emoji）**，一律使用純文字、中括號標籤或幾何符號。

---

## 一、入口速查（每次接手先看這裡）

| 你要做什麼 | 先讀哪些檔案／跑哪支指令 |
| :--- | :--- |
| 剛開新對話、從手機指派接手任務 | 跑 `status.py` → `git log --oneline -10` → 整份讀 [`docs/todo.md`](./docs/todo.md) → 跑 `pipeline_status.py` |
| 準備寫程式或修改畫面（`index.html`／樣張） | 必讀 [`DESIGN.md`](./DESIGN.md)（含待決與否決紀錄）、[`docs/art/美術設計規格書.md`](./docs/art/美術設計規格書.md)、[`docs/dev/實作規格書.md`](./docs/dev/實作規格書.md)，並依 `game-build-pipeline` 執行 |
| 查詢某個檔案或模組有沒有未結問題／舊紀錄 | 執行 `python3 .agents/skills/project-audit/scripts/issues_for.py <檔案或關鍵字>`（或直接看 [`docs/issues.md`](./docs/issues.md)） |
| 查詢最近幾次討論與產出細節 | 執行 `python3 .agents/skills/git-sync-guardian/scripts/log_tail.py -n 3`（**日誌只寫不讀，不得整份讀取**） |
| 準備完成交付與推送 | 跑 `lint_project.py` → 跑 `log_time.py` 寫 [`docs/log.md`](./docs/log.md) → 刪 [`docs/todo.md`](./docs/todo.md) 已完成條目 → 用 `safe_commit_push.py` 提交並推送 |

---

## 二、專案架構與三層分工

```text
firestorm-pr-180s/
├── AGENTS.md                  # 【規範層：Schema】本維護手冊（AI 協作唯一真實來源）
├── DESIGN.md                  # 【規範層：Design Ledger】美術與 UX 方向紀錄（已定／暫定／待決／否決／歷程）
├── CLAUDE.md                  # Claude Code 自動載入入口（指向本檔與 .claude/skills/）
├── README.md                  # 專案首頁、玩法簡介與整體進度清單
├── index.html                 # 【展示與應用層】遊戲正式本體（純前端單檔，部署於 GitHub Pages；待建立）
├── worker/                    # 可選的 Cloudflare Worker 中繼程式（代管 API 金鑰；待建立，見 TD-012）
├── .github/workflows/pages.yml # GitHub Pages 發布流程（只上傳 index.html）
├── .agents/skills/            # 專屬 Skill 正本（見第四章）
├── .claude/skills/            # 供 Claude Code（含手機／網頁版）載入之轉介檔，內容指向 .agents/skills/ 正本
└── docs/                      # 【知識與協作層】
    ├── index.md               # 所有文件目錄（一句話摘要；新增／刪除文件須同步更新）
    ├── log.md                 # 工作與決策流水帳（Append-only，只在檔尾追加）
    ├── issues.md              # 問題與缺陷清單（只放尚未結案之 FP-NNN 條目）
    ├── issues/closed/         # 已結案問題歸檔（由 archive_issues.py 統一搬移，只追加）
    ├── todo.md                # 待辦任務看板（TD-NNN；手機端指派入口，完成即刪）
    ├── proposal/              # 企劃：動機、玩法、課堂理論對應（Reflection / Multi-Agent）
    ├── dev/                   # 程式：狀態機、計分公式、角色與事件庫、LLM Prompt、JSON、離線模式、Canvas
    ├── art/                   # 美術：像素 RPG 規格書與互動樣張（samples/）
    ├── assets/                # 流程圖與技術架構圖
    └── archive/               # 【原始資料層】早期提案與 v1 規格書（唯讀，嚴禁修改）
```

### 各層寫入權限與資料流向
1. **原始資料層（`docs/archive/`）**：早期文字檔與已淘汰之 `美術設計規格書_v1_擬真介面.md`。**唯讀（Read-Only）**，嚴禁 AI 修改或刪除。
2. **現行知識層（`docs/proposal/`、`docs/dev/`、`docs/art/`）**：永遠反映「現在的決定」。同一件事只在一個地方寫完整規格，其他文件以相對連結指向，避免雙份文件說法矛盾。
3. **協作控制層（`docs/todo.md`、`docs/issues.md`、`docs/log.md`）**：三者分工嚴格切開，不得混記（見第六章）。
4. **應用本體（`index.html`）**：純前端單檔 HTML + CSS + JS，零 npm 建置負擔，直接由 GitHub Pages 託管。

---

## 三、遊戲核心紅線（開發時不可違反）

1. **單檔遊戲本體＋可選中繼**：正式遊戲只存在於根目錄 `index.html`，不依賴外部建置工具（Vite/Webpack）或第三方圖片/音檔。唯一允許的後端是 `worker/` 內的 Cloudflare Worker 中繼程式（代管 API 金鑰、組裝 Prompt、限流），遊戲在沒有它時仍須完整可玩（2026-11-25 使用者同意）。
2. **品牌與素材版權原則**：所有新聞台、社群平台與人物一律虛構——新聞台為 **炎上新聞台 FNN**、社群為 **炎串**、爆料來源為 **爆料版**。嚴禁出現真實台標、Logo、真人照片（`docs/proposal/` 或 `docs/dev/` 早期草稿殘留之真實品牌字樣應依 `FP-001` 清理）。
3. **像素 RPG × 社群世界觀**：場景道具一律使用現代物件（手機、補光燈、麥克風、桌椅），不用奇幻城堡寶劍；角色與頭像由程式繪製點陣圖。
4. **金鑰安全與離線保底**：LLM 只串接 Command Code Provider API；金鑰只能存在 Worker 加密變數或玩家瀏覽器 `localStorage`，絕不寫入任何受版控檔案。AI 只負責判讀與演出文字，數值與結局由前端固定公式計算；必須具備 Markdown 代碼塊清洗、空白與敷衍輸入判定，以及無 Key／斷網／限流時無縫切換的離線模式（關鍵字判讀＋同一套公式）。
5. **Human-in-the-loop Reflection 閉環**：必須實作 `STATE_VERDICT` 裁決頁與 `STATE_REVISE`（「緊急撤回修改」，每局限 1 次），讓玩家看到 AI 裁判挑錯後能於剩餘時間內修正聲明再送審。
6. **雙端體驗與無障礙**：電腦版（>1080px）維持三欄一次看完；手機版（<=760px）採階段式單屏切換（頂部狀態列＋底部分頁＋直播聊天室），無橫向捲軸；所有互動元件具 `--cyan` 2px 鍵盤焦點框並支援 `prefers-reduced-motion`。

---

## 四、專屬 Skill 一覽

正本一律置於 `.agents/skills/<名稱>/SKILL.md`，各 AI 開始對應工作前須先完整讀取；`.claude/skills/` 僅放轉介檔指向正本，修改規則時只改正本。

| Skill | 何時使用 | 內附關鍵腳本 |
| :--- | :--- | :--- |
| [`game-build-pipeline`](./.agents/skills/game-build-pipeline/SKILL.md) | 接手 `TD-NNN` 任務、建立或修改 `index.html` 與樣張時（從 S0 預檢到 S4 交付） | `pipeline_status.py`、`verify_app.js` |
| [`project-audit`](./.agents/skills/project-audit/SKILL.md) | 每次提交前健康檢查、查核規格與程式碼一致性、登記／查詢／歸檔 `FP-NNN` 問題時 | `lint_project.py`、`issues_for.py`、`archive_issues.py` |
| [`git-sync-guardian`](./.agents/skills/git-sync-guardian/SKILL.md) | 任何 Git 狀態檢查、遠端同步、取得臺北時間、讀取日誌尾部與原子提交推送 | `status.py`、`sync.py`、`safe_commit_push.py`、`log_time.py`、`log_tail.py`、`stage_*.py`、`merge_log.py` |

---

## 五、AI 核心作業流程（Core Operations）

### 1. Build & Feature Dev（接手待辦與程式開發）
1. 先依 `git-sync-guardian` 執行 `status.py` 與 `sync.py` 確認與遠端同步。
2. 執行 `python3 .agents/skills/game-build-pipeline/scripts/pipeline_status.py` 掌握現況，並從 `docs/todo.md` 認領使用者指派的 `open` 任務（**`waiting` 任務在未獲使用者明確拍板前不得擅自動工**）。
3. 依 `game-build-pipeline` 之 S0 至 S4 開發與驗證（包含 `lint_project.py` ERROR 0 與 `verify_app.js` 桌面/手機驗證）。
4. 完成後刪除 `docs/todo.md` 對應條目，更新 `README.md` 進度（若有里程碑完成），寫入 `docs/log.md` 並以 `safe_commit_push.py` 原子推送。

### 2. Update（文件與規格維護）
1. 討論產生新決策時：修改 [`DESIGN.md`](./DESIGN.md) 與對應知識頁（`docs/proposal/`、`docs/dev/`、`docs/art/`），標示確定程度（`【定案】`、`【暫定】`、`【未定】`；`DESIGN.md` 用 `[已定]`、`[暫定]`、`[待決]`、`[否決]`）。
2. 若新增、搬動或刪除文件，同步更新 [`docs/index.md`](./docs/index.md)。
3. 知識頁與 `docs/log.md` 有衝突時，**以 `docs/log.md` 中最新的決策為準**，並將過時知識頁修正（或開立 `FP-NNN` 追蹤）。

### 3. Lint & Audit（專案健康檢查）
每次修改後、提交前執行：
```bash
python3 .agents/skills/project-audit/scripts/lint_project.py
```
腳本自動檢查：核心文件存在性、Zero-Emoji 合規、無 `file:///` 本機路徑、相對連結有效性、`docs/index.md` 覆蓋率、`docs/todo.md` 與 `docs/issues.md` 格式及 `關聯` 編號存在性、`docs/log.md` 格式與 Git append-only 完整性，以及 `index.html` 基本紅線。`ERROR` 必須全部歸零才能提交。

### 4. Handoff（深夜指派與多 AI 交接）
本專案支援手機端指派與多 AI 輪流接手，交接脈絡一律依下列順序取得，**嚴禁整份讀取 `docs/log.md`**：
1. `git log --oneline -10`：掌握最近完成的提交紀錄。
2. 整份閱讀 [`docs/todo.md`](./docs/todo.md)：了解目前未完成任務、進行中任務（`doing`）與等待拍板項目（`waiting`）。
3. 視任務需要閱讀 [`docs/issues.md`](./docs/issues.md) 之 `open` 條目與 [`DESIGN.md`](./DESIGN.md) 第五至七章；查特定檔案問題與歷史使用 `issues_for.py <目標>`。
4. 仍需近期討論細節時，執行 `python3 .agents/skills/git-sync-guardian/scripts/log_tail.py -n 3`（可用 `--grep <關鍵字>` 搜尋）。
5. **交接寫入待辦，不寫入日誌**：做到一半需要他人接手、或須等使用者決定才能動工的工作，登記或更新於 `docs/todo.md`，不得以 `docs/log.md` 充當待辦清單。

---

## 六、內容與格式規範

### 1. 協作檔案分工表

| 檔案 | 記錄對象 | 寫作規則 |
| :--- | :--- | :--- |
| [`docs/log.md`](./docs/log.md) | 已完成的工作與已形成的決策（歷史紀錄） | Append-only，只在檔尾追加，完成工作即寫並立即提交 |
| [`docs/issues.md`](./docs/issues.md) | 程式缺陷、手機跑版、API 異常或規格書前後矛盾 | `FP-NNN` 流水號，原地改狀態不刪除；結案由 `archive_issues.py` 歸檔 |
| [`DESIGN.md`](./DESIGN.md) | 美術與 UX 方向的定案、待決選擇題、否決紀錄與版本歷程 | 動工前必讀；已列於「否決紀錄」者不得重提 |
| [`docs/todo.md`](./docs/todo.md) | 尚未完成之開發任務、待使用者拍板之決策工作 | `TD-NNN` 流水號，完成或經同意放棄即直接刪除 |

### 2. 日誌格式 `docs/log.md`
2026-11-07 及以前之既有條目維持原貌不回溯改寫；自本規範啟用起，所有新增條目一律依下列格式追加於檔尾，並載明真實執行代理與底層模型型號：

```markdown
## [YYYY-MM-DD HH:MM] <動作> | <標題> | <模組標籤>
- **執行代理**：<AI 名稱與所屬機構>（例如：Claude Code by Anthropic / Antigravity by Google DeepMind / Codex by OpenAI）
- **模型版本**：<底層 LLM 真實型號與版本>
- **具體變更**：<簡述操作要點、影響檔案與完成的 TD-NNN / FP-NNN 編號>
```

* **標題時間**：寫標題前一律先執行 `python3 .agents/skills/git-sync-guardian/scripts/log_time.py` 取得臺北時間（UTC+8），嚴禁憑估計填寫（`stage_log.py` 會機械攔截未來時間或過舊時間）。
* **動作白名單（`<動作>`）**：`init`（初始化）、`spec`（規格修訂）、`design`（視覺設計）、`feat`（功能實作）、`fix`（缺陷修正）、`audit`（規範審查）、`test`（測試驗證）、`lint`（檢查整理）、`rule`（規範變更）、`update`（內容更新）、`config`（組態變更）、`git`（版本控管）。
* **模組標籤白名單（`<模組標籤>`）**：`#企劃`、`#狀態機`、`#LLM串接`、`#離線資料`、`#UI介面`、`#手機版`、`#像素美術`、`#新聞圖卡`、`#音效`、`#測試驗證`、`#文件`；涉及多模組或全專案規範者一律填 `全域`。
* **相對路徑**：日誌與所有文件連結一律使用相對路徑，嚴禁 `file:///`。

### 3. 問題清單格式 `docs/issues.md`
* 新編號一律先執行 `python3 .agents/skills/git-sync-guardian/scripts/stage_issues.py --next-id` 取得（`FP-001` 起跳，流水不重用）。本檔不分節，只放尚未結案條目：
  ```markdown
  ### FP-001 | open | docs/dev/實作規格書.md | 第六章 Canvas | 規格不符
  - **問題**：具體現象或規格衝突描述。
  - **依據**：應對照的規格文件或預期行為。
  - **關聯**：TD-002（選填，相關 FP-NNN 或 TD-NNN）
  - **發現於**：docs/log.md [YYYY-MM-DD HH:MM] 或 人工審查（執行代理）
  ```
* **狀態**：`open`（待修）、`fixed`（已修）、`wontfix`（經使用者同意保留，須寫理由）。
* **問題類型建議值**：`功能異常`、`介面跑版`、`規格不符`、`API異常`、`無障礙或效能`、`待確認`。
* **結案與歸檔**：修好後就地將 `open` 改為 `fixed` 並補上 `- **處理**：日期、執行代理、修正方式`，**不得手動刪除或搬移**；歸檔統一由 `python3 .agents/skills/project-audit/scripts/archive_issues.py --apply --agent "<代理名稱>"` 搬至 `docs/issues/closed/`。

### 4. 待辦清單格式 `docs/todo.md`
* 新編號一律先執行 `python3 .agents/skills/git-sync-guardian/scripts/stage_todo.py --next-id` 取得（`TD-001` 起跳，流水不重用）。本檔不分節，依編號排列：
  ```markdown
  ### TD-001 | open | app | 一句話說明要做什麼
  - **內容**：具體要做什麼、涉及哪些檔案、參考哪份規格。
  - **完成條件**：做到什麼程度與通過哪些檢查才算完成。
  - **等待**：須等使用者拍板之事項（狀態為 waiting 時必填）。
  - **負責**：執行代理（狀態為 doing 時必填）。
  - **進度**：已完成與卡住之處（選填，做到一半時填寫）。
  - **關聯**：相關之 FP-NNN 或 TD-NNN（選填）。
  - **來源**：docs/log.md [YYYY-MM-DD HH:MM] 或使用者指示；登記日期與執行代理。
  ```
* **狀態**：`open`（可直接認領）、`waiting`（等使用者決定，嚴禁擅自動工）、`doing`（某代理進行中，中斷時須改回 `open` 並填「進度」）。完成或經使用者同意放棄時**直接刪除條目**，並在當次 `docs/log.md` 條目寫明編號。
* **範圍**：`app`（`index.html` 主程式）、`art`（美術與樣張）、`spec`（`docs/` 企劃與規格）、`test`（測試與實機驗證）、`rule`（`AGENTS.md` / `DESIGN.md` / `README.md`）、`skill`（`.agents/skills/` 與腳本）、`deploy`（GitHub Pages 與 Demo）。
* **不必寫日誌的情形**：若僅在 `docs/todo.md` 新增、拆解或調整待辦條目，而無其他已完成產出時，可直接以 `safe_commit_push.py` 提交 `docs/todo.md`，不另寫日誌。

---

## 七、多 AI 協同開發與 Git 版本控制協定

1. **提交必含推送（Commit Implies Push）**：任何完成階段任務的 `commit` 必須立即 `push` 至遠端（`main` 或雲端代理開立之 `claude/...` 等具名分支），確認 `Ahead: 0`。
2. **動工前必先檢查遠端（Pre-flight Fetch Check）**：開始實質改檔前執行 `python3 .agents/skills/git-sync-guardian/scripts/status.py`，落後時以 `sync.py` 合流。
3. **只提交自己的修改（Commit Only Your Own Changes）**：嚴禁 `git add -A`、`git add .`、`git commit -a`。一律使用 `safe_commit_push.py` 明確列出自己改動的檔案；共用檔 `docs/log.md`、`docs/issues.md`、`docs/todo.md` 由對應 `stage_*.py` 逐條暫存。
4. **寫入日誌即提交（Log Implies Commit）**：追加 `docs/log.md` 代表工作完成，須在同一回合內執行 `safe_commit_push.py` 提交並推送（使用者明確要求暫緩時除外）。寫日誌一律追加於檔尾，不得讀入整檔後覆寫，以免蓋掉他人新條目。
5. **日誌並行合流原則**：遇 `docs/log.md` 合併衝突時，由 `merge_log.py` 按時間先後保留所有條目，嚴禁刪除或覆蓋他方紀錄。
6. **撤回工作不刪紀錄**：要撤回某次程式或文件改動時，不得以 `git revert`、`git reset` 回退整份共用檔；只撤回程式碼或規格內容，`docs/log.md`、`docs/issues.md`、`docs/todo.md` 紀錄全數保留，並另追加日誌說明撤回原因。
7. **語言與寫作慣例**：一律繁體中文；檔名用中文、資料夾用英文小寫；樣張舊版加 `_vN` 版號，不覆蓋舊版。
