# 待辦清單（Todo）

> 本檔登記尚未完成之開發任務、交接事項與須等使用者確認才能動工的工作，也是手機端深夜指派任務的主要入口。格式與規則見 [AGENTS.md](../AGENTS.md) 第六章第 4 節，接手順序見第五章第 4 節。標題四段依序為：編號、狀態（`open` / `waiting` / `doing`）、範圍（`app` / `art` / `spec` / `test` / `rule` / `skill` / `deploy`）、標題。
>
> 完成或經同意放棄之條目直接刪除，並於當次日誌條目寫明編號；新增前以 `python3 .agents/skills/git-sync-guardian/scripts/stage_todo.py --next-id` 取號。不收程式 Bug 或規格矛盾（登記於 [issues.md](issues.md)）、美術方向選擇題本身（登記於 [DESIGN.md](../DESIGN.md) 第五章）。

### TD-003 | open | app | 建立 index.html 灰盒骨架與雙端版面（電腦三欄＋手機階段式切換）
- **內容**：依 [實作規格書.md](dev/實作規格書.md) 第六章與 [美術設計規格書.md](art/美術設計規格書.md) 第三、九章，在根目錄建立單檔 `index.html` 灰盒骨架：匯入第三章 CSS 變數（`--night`、`--panel`、`--gold`、`--long` 等）、Cubic 11 與 Noto Sans TC（離線退回系統黑體）；電腦版（>1080px）三欄、761～1080px 兩欄、手機版（<=760px）固定頂部狀態列＋5 格底部分頁＋一次顯示一個階段；預留角色選擇頁、裁決頁區塊；右上角設定彈窗（API Key 密碼欄、模型下拉、音效開關、清除紀錄）。可參考 [像素風格樣張_v3.html](art/samples/像素風格樣張_v3.html) 的 CSS 元件，但須依正式狀態機整理乾淨。
- **完成條件**：`index.html` 存在，`pipeline_status.py` 之 P1 檢核通過，`lint_project.py` ERROR 0，`verify_app.js` 在 `1360x900` 與 `390x844` 無橫向捲軸與 JS 錯誤。
- **來源**：[實作規格書.md](dev/實作規格書.md) Step 1；2026-11-25 拆解建檔，Antigravity by Google DeepMind；2026-11-25 遊戲流程 v2 定案後更新，Claude Code by Anthropic。

### TD-004 | open | app | 實作狀態機、180 秒計時器、裁決頁與緊急撤回閉環
- **內容**：依 [實作規格書.md](dev/實作規格書.md) 第二章，實作 `gameState` 狀態機 `STATE_TITLE` → `STATE_SELECT` → `STATE_CRISIS` → `STATE_PR_DRAFT` → `STATE_AUDITING` → `STATE_VERDICT` →（`STATE_REVISE` → `STATE_PR_DRAFT`）→ `STATE_RESULT`。計時從進入寫稿才開始、送審等待回應時暫停、撤回後從剩餘秒數接續；撤回每局限 1 次並套用「截圖已流出」懲罰；神隱（歸零或空白）與敷衍（少於 20 字）判定；剩 30 秒紅字閃爍；手機底部分頁隨狀態自動切換。
- **完成條件**：全部狀態可互動切換（判讀先用假資料），撤回只能按一次且秒數正確接續，`pipeline_status.py` 之 P2 檢核通過，`verify_app.js` 雙端無錯誤。
- **關聯**：TD-003
- **來源**：[實作規格書.md](dev/實作規格書.md) 第二章與 Step 2；2026-11-25 拆解建檔，Antigravity by Google DeepMind；2026-11-25 遊戲流程 v2 定案後更新，Claude Code by Anthropic。

### TD-005 | open | app | 實作事件庫、策略指令連動、道歉影片圖層與點陣 Canvas
- **內容**：於 `index.html` 納入 [角色與事件庫.md](dev/角色與事件庫.md) 之 10 則 `CRISIS_EVENTS`（含三大質疑關鍵字、`tactic_overrides`）與 [實作規格書.md](dev/實作規格書.md) 第三章 `TACTICS`；依角色抽事件且連續兩局不重複；實作 `128×72` 道歉影片圖層疊加（背景、桌子、補光燈、主角、律師、診斷書道具、字幕、LIVE 標籤）與 6 種酸民 12×12 點陣頭像。
- **完成條件**：抽題與三大質疑顯示正常，勾選策略即時切換影片圖層，留言瀑布流與手機直播聊天室（最多 3 則）動態渲染正常，`pipeline_status.py` 之 P3 檢核通過。
- **關聯**：TD-003、TD-010
- **來源**：[實作規格書.md](dev/實作規格書.md) 第三章與 [美術設計規格書.md](art/美術設計規格書.md) 第六、七章；2026-11-25 拆解建檔，Antigravity by Google DeepMind；2026-11-25 遊戲流程 v2 定案後更新，Claude Code by Anthropic。

### TD-006 | open | app | 串接 Command Code Provider API 與 JSON 防呆
- **內容**：依 [實作規格書.md](dev/實作規格書.md) 第一、四章，實作 `callLLMJudge()`：呼叫 `https://api.commandcode.ai/provider/v1/chat/completions`（Key 讀自 `localStorage`，日後改走 TD-012 中繼），System Prompt 要求回傳第四章第 2 節之判讀 JSON（逐題回應、誠意、甩鍋、紅旗、代寫嫌疑、敗筆、評語、6 則留言、新聞標題）；撤回後第二次送審附上第一次的敗筆；12 秒逾時、非 200、429 或 JSON 解析失敗時自動改用離線判讀；欄位缺漏以離線結果補齊。先以少量真實呼叫實測預設模型 `deepseek/deepseek-v4.1-flash-fast` 與備選模型之延遲和 JSON 穩定度，結果寫回實作規格書。
- **完成條件**：有 Key 時可正常判讀並交給前端公式計分；無 Key 與模擬失敗時離線模式順暢通關；`pipeline_status.py` 之 P4 檢核通過；Key 未出現在任何受版控檔案。
- **關聯**：TD-004、TD-011
- **來源**：[實作規格書.md](dev/實作規格書.md) 第四章；2026-11-25 拆解建檔，Antigravity by Google DeepMind；2026-11-25 遊戲流程 v2 定案後更新，Claude Code by Anthropic。

### TD-007 | open | app | 實作結局（含隱藏結局）、像素新聞卡、名醫診斷書、最佳紀錄與音效
- **內容**：依 [美術設計規格書.md](art/美術設計規格書.md) 第十、十一章與 [實作規格書.md](dev/實作規格書.md) 第四章第 4 節、第八章：（1）四種結局加隱藏結局 `ENDING_GHOSTWRITER`；（2）`320×180` 放大 4 倍成 `1280×720` 之「炎上新聞台 FNN」像素新聞卡（逐字量寬度斷行、一鍵下載＋長按存圖提示）；（3）米黃紙張「AI 公關名醫診斷書」（病患為所選角色）；（4）`localStorage` 最佳紀錄；（5）Web Audio 8-bit 音效（電腦版預設開、手機版預設靜音）與靜音鈕，支援 `prefers-reduced-motion`。
- **完成條件**：五種結局之新聞卡、診斷書與表情皆正確渲染並可下載 PNG，最佳紀錄於封面顯示，音效可開關且無音檔依賴，`pipeline_status.py` 之 P5 檢核通過。
- **關聯**：TD-005、TD-011
- **來源**：[美術設計規格書.md](art/美術設計規格書.md) 第十、十一章；2026-11-25 拆解建檔，Antigravity by Google DeepMind；2026-11-25 遊戲流程 v2 定案後更新，Claude Code by Anthropic。

### TD-008 | waiting | test | 手機實機測試專注寫稿模式（虛擬鍵盤高度）與新聞卡存圖
- **內容**：在真實手機瀏覽器（iOS Safari / Android Chrome）測試 `index.html` 手機版：點擊聲明稿輸入框進入「專注寫稿模式」時，隱藏指令區後字幕預覽、輸入框與發布鈕是否確實留在虛擬鍵盤上方而不被遮住；以及像素新聞卡一鍵下載與長按存圖在手機瀏覽器之實際可用性。
- **完成條件**：完成實機測試紀錄，若發現跑版已修復或登記 `FP-NNN`；[DESIGN.md](../DESIGN.md) 第五章第 1 項可標為已定。
- **等待**：`index.html` 灰盒與結局畫面完成（`TD-003`、`TD-007`），並由使用者於實機操作回報體感。
- **關聯**：TD-003、TD-007
- **來源**：[docs/log.md](log.md) `[2026-11-07] 待辦 | 規格書 v2 之後`；2026-11-25 遷移建檔，Antigravity by Google DeepMind。

### TD-009 | open | deploy | 準備 GitHub Pages 部署、全流程驗收與期末 Demo 檢核
- **內容**：確認單檔 `index.html` 可直接在 GitHub Pages 根目錄正常運行（無相對路徑失效、Cubic 11 子集內嵌可離線顯示、離線模式正常）；決定 Pages 採「從分支部署」（`docs/` 等文件一併公開）或以 workflow 只發布 `index.html`；更新 [README.md](../README.md) 線上遊玩網址與進度勾選；完成桌面與手機全流程驗收以備錄製 1～3 分鐘 Demo 影片與期末報告。
- **完成條件**：GitHub Pages 線上可玩、無控制台錯誤、`lint_project.py` ERROR 0、`pipeline_status.py` 全數 OK。
- **關聯**：TD-006、TD-007、TD-008
- **來源**：[README.md](../README.md) 目前進度與 [期末專案提案.md](proposal/期末專案提案.md) 第六章；2026-11-25 建檔，Antigravity by Google DeepMind。

### TD-010 | open | app | 實作角色選擇頁與 4 位主角點陣圖
- **內容**：依 [角色與事件庫.md](dev/角色與事件庫.md) 第一章，於 `index.html` 建立 `CHARACTERS` 資料（初始粉絲、廠商信任、專屬規則）與 `STATE_SELECT` 角色卡（電腦 4 欄、手機 2×2）；依 [美術設計規格書.md](art/美術設計規格書.md) 第七章，以同一套 28×28 骨架繪製小艾、阿凱、博士 Leo、饅頭四位主角與共用表情集（含隱藏結局「被抓包」）。
- **完成條件**：可選任一角色並帶入正確初始數值，四位角色各表情於影片區、新聞卡與診斷書正確顯示，`verify_app.js` 雙端無錯誤。
- **關聯**：TD-003
- **來源**：2026-11-25 使用者指示（開場自選角色，先做 4 位），Claude Code by Anthropic。

### TD-011 | open | app | 實作前端計分公式與離線關鍵字判讀
- **內容**：依 [實作規格書.md](dev/實作規格書.md) 第三至五章，實作純函式 `scoreRound(judgement, ctx)`（合併 LLM 或離線判讀、策略效果與一致性檢查、事件 `tactic_overrides`、角色倍率、撤回與小幫手懲罰，算出掉粉、炎上度、廠商信任與結局）與 `offlineJudge(statement, event)`（關鍵字逐題判讀、誠意與甩鍋規則、紅旗偵測、從 `offline_comments` 與模板產生文字）；為 10 則事件各補齊 12 則離線留言。
- **完成條件**：以至少 5 組固定測試稿（誠懇、甩鍋、威脅提告、空白、小幫手原稿）驗證同一輸入結果一致且結局符合預期；試玩後將公式調整結果寫回實作規格書並把 [DESIGN.md](../DESIGN.md) 第五章第 2 項標為已定。
- **關聯**：TD-004、TD-005
- **來源**：2026-11-25 使用者同意「LLM 判讀、前端計分」，Claude Code by Anthropic。

### TD-012 | open | deploy | 建置 Cloudflare Worker 中繼伺服器代管 API 金鑰
- **內容**：依 [實作規格書.md](dev/實作規格書.md) 第七章，於 `worker/` 撰寫 Cloudflare Worker：接收 `{ character, event_id, tactics, statement, revise_of }`，於伺服器端組裝 Prompt、鎖定模型與 `max_tokens`，以加密變數保存 Command Code 金鑰；實作每 IP 每小時與全站每日上限、聲明稿 500 字上限；前端改為優先呼叫 Worker，失敗時退回玩家 Key 或離線模式。Cloudflare 帳號由使用者自行註冊，部署步驟寫成文件交由使用者操作。
- **完成條件**：其他裝置不輸入 Key 即可取得 AI 判讀；金鑰不在任何受版控檔案與前端回應中；超過上限時前端自動切換離線模式；`lint_project.py` ERROR 0。
- **關聯**：TD-006
- **來源**：2026-11-25 使用者指示（希望別人不輸入金鑰即可使用使用者的 API，中繼伺服器排入之後的待辦），Claude Code by Anthropic。
