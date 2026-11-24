# 待辦清單（Todo）

> 本檔登記尚未完成之開發任務、交接事項與須等使用者確認才能動工的工作，也是手機端深夜指派任務的主要入口。格式與規則見 [AGENTS.md](../AGENTS.md) 第六章第 4 節，接手順序見第五章第 4 節。標題四段依序為：編號、狀態（`open` / `waiting` / `doing`）、範圍（`app` / `art` / `spec` / `test` / `rule` / `skill` / `deploy`）、標題。
>
> 完成或經同意放棄之條目直接刪除，並於當次日誌條目寫明編號；新增前以 `python3 .agents/skills/git-sync-guardian/scripts/stage_todo.py --next-id` 取號。不收程式 Bug 或規格矛盾（登記於 [issues.md](issues.md)）、美術方向選擇題本身（登記於 [DESIGN.md](../DESIGN.md) 第五章）。

### TD-001 | waiting | rule | 定案遊戲調性與長文字字型，移除規格書【未定】標示
- **內容**：[美術設計規格書.md](art/美術設計規格書.md) 與 [DESIGN.md](../DESIGN.md) 第五章仍有兩項未定項目：（1）遊戲整體調性偏「緊張壓迫」或偏「荒謬好笑」；（2）聲明稿與留言長文字採用 `Cubic 11`（選項 A）或 `Noto Sans TC`（選項 B）。定案後須更新 [DESIGN.md](../DESIGN.md)、[美術設計規格書.md](art/美術設計規格書.md) 對應章節之【未定】標記與 `--long` 變數設定。
- **完成條件**：兩項決策皆由使用者拍板並改為【定案】／`[已定]`，於 `docs/log.md` 記一筆 `design` 或 `rule` 紀錄。
- **等待**：使用者決定遊戲調性傾向與 `--long` 長文字字型。
- **來源**：[docs/log.md](log.md) `[2026-11-07] 待辦 | 規格書 v2 之後`；2026-11-25 遷移建檔，Antigravity by Google DeepMind。

### TD-002 | open | spec | 對齊實作規格書與像素 RPG v2 設計規格（消除真實品牌與舊新聞卡規格）
- **內容**：[實作規格書.md](dev/實作規格書.md) 為早期 v1 時期撰寫，與現行像素 RPG v2 規格及版權原則存在三處落差（詳見 `FP-001`）：（1）仍寫真實品牌「蘋果/TVBS」與「TVBS 突發新聞」，須改為虛構品牌「炎上新聞台 FNN」；（2）第六章新聞圖卡仍為擬真 `1200×675` 演播室版型，須對齊 [美術設計規格書.md](art/美術設計規格書.md) 第十章的 `320×180` 放大 4 倍成 `1280×720` 像素新聞卡；（3）第一章 Gemini 預留型號仍寫 `gemini-1.5-flash` 及缺少手機 <=760px 階段式切換說明。
- **完成條件**：更新 [實作規格書.md](dev/實作規格書.md) 消除上述三處落差；`FP-001` 改為 `fixed` 並補上處理行；`lint_project.py` ERROR 0。
- **關聯**：FP-001
- **來源**：2026-11-25 專案架構盤點發現，Antigravity by Google DeepMind。

### TD-003 | open | app | 建立 index.html 灰盒骨架與雙端版面（電腦三欄＋手機階段式切換）
- **內容**：依 [實作規格書.md](dev/實作規格書.md) 第五章與 [美術設計規格書.md](art/美術設計規格書.md) 第三、九章，在根目錄建立單檔 `index.html` 灰盒骨架：匯入第三章 CSS 變數（`--night`、`--panel`、`--gold` 等）與 Cubic 11 字型基礎設定；電腦版（>1080px）三欄佈局、761～1080px 兩欄佈局、手機版（<=760px）固定頂部狀態列＋5 格底部分頁＋一次顯示一個階段；右上角包含 API Key 設定彈窗（存取 `localStorage`）與靜音開關預留位。可參考 [像素風格樣張_v3.html](art/samples/像素風格樣張_v3.html) 的 CSS 元件與結構，但須依正式遊戲狀態機整理乾淨。
- **完成條件**：`index.html` 存在，執行 `pipeline_status.py` 之 P1 檢核通過，`lint_project.py` ERROR 0，`verify_app.js` 在 `1360x900` 與 `390x844` 無橫向捲軸與 JS 錯誤。
- **來源**：[docs/log.md](log.md) `[2026-11-07] 待辦 | 規格書 v2 之後` 與 [實作規格書.md](dev/實作規格書.md) Step 1；2026-11-25 拆解建檔，Antigravity by Google DeepMind。

### TD-004 | open | app | 實作前端狀態機、180 秒倒數計時器與緊急撤回 Reflection 閉環
- **內容**：在 `index.html` 實作 `gameState` 單一全域狀態機，串接 `STATE_TITLE` → `STATE_CRISIS` → `STATE_PR_DRAFT` → `STATE_AUDITING` → `STATE_RESULT` 與核心亮點 `STATE_REVISE`（180 秒內按「緊急撤回修改」凍結扣粉、保留剩餘時間回到寫稿，依 AI 批改重提）；實作 `setInterval` 180 秒倒數（剩 30 秒紅字閃爍、歸零判神隱暴斃）與手機底部分頁自動切換連動。
- **完成條件**：完整狀態機與 `STATE_REVISE` 閉環可互動切換，`pipeline_status.py` 之 P2 檢核通過，`verify_app.js` 雙端無錯誤。
- **關聯**：TD-003
- **來源**：[實作規格書.md](dev/實作規格書.md) 第二章與 Step 2、Step 7；2026-11-25 拆解建檔，Antigravity by Google DeepMind。

### TD-005 | open | app | 實作事件庫、策略指令連動、道歉影片圖層與點陣角色 Canvas
- **內容**：於 `index.html` 納入 `CRISIS_EVENTS` 內建危機事件庫（3～5 則，含淘寶貼牌、多重劈腿、手搖飲食安等）與策略標籤（影片形式＋話術手段）；實作 `128×72` 道歉影片圖層疊加系統（背景、桌子、補光燈、小艾、律師、診斷書道具、即時字幕、LIVE 標籤）及程式繪製 6 種酸民 12×12 點陣頭像與小艾 28×28 表情變化。
- **完成條件**：隨機抽題與三大質疑顯示正常，勾選策略即時切換影片圖層，留言瀑布流與手機直播聊天室（最多 3 則）動態渲染正常，`pipeline_status.py` 之 P3 檢核通過。
- **關聯**：TD-003
- **來源**：[實作規格書.md](dev/實作規格書.md) 第三章與 [美術設計規格書.md](art/美術設計規格書.md) 第六、七章；2026-11-25 拆解建檔，Antigravity by Google DeepMind。

### TD-006 | open | app | 串接 Groq / Gemini LLM API、JSON 防呆清洗與離線智囊庫 Fallback
- **內容**：於 `index.html` 實作 `callLLMAdjudicator()`（支援 Groq `llama-3.1-8b-instant` 與 Google Gemini API 切換，API Key 讀寫自 `localStorage`），包含統一 System Prompt（同步產出 6 種人設留言＋公關裁判兩階段 CoT 質化／量化 JSON）、Regex 清洗 ````json 標籤、空白或過短輸入神隱判定，以及無 Key／斷網／限流時自動無縫切換之離線智囊庫 Fallback 資料（每個內建事件至少一組完整離線反應）。
- **完成條件**：有 Key 時可正常呼叫 API 解析回傳並更新扣粉／炎上條／結局；無 Key 與模擬 API 失敗時離線 Fallback 100% 順暢通關；`pipeline_status.py` 之 P4 檢核通過。
- **關聯**：TD-004、TD-005
- **來源**：[實作規格書.md](dev/實作規格書.md) 第四章與 Step 4、Step 8；2026-11-25 拆解建檔，Antigravity by Google DeepMind。

### TD-007 | open | app | 實作四種結局像素新聞卡、AI 公關名醫診斷書與 Web Audio 8-bit 音效
- **內容**：依 [美術設計規格書.md](art/美術設計規格書.md) 第十、十一章，在 `index.html` 完成：（1）四種結局（`ENDING_DESTROYED`、`ENDING_BACKFIRE`、`ENDING_CONTROVERSIAL`、`ENDING_PERFECT`）動態切換；（2）`320×180` 點陣繪製並放大 4 倍成 `1280×720` 的「炎上新聞台 FNN」像素新聞卡（逐字量寬度斷行、含下載／存圖功能）；（3）米黃紙張「AI 公關名醫診斷書」；（4）Web Audio API 8-bit 音效合成（警報、心跳、受擊、爆炸、蓋章、勝利）與靜音按鈕，並確保支援 `prefers-reduced-motion`。
- **完成條件**：四種結局之新聞卡、診斷書與大頭照表情皆正確渲染並可匯出 PNG，音效可開關且無音檔依賴，`pipeline_status.py` 之 P5 檢核通過。
- **關聯**：TD-005、TD-006
- **來源**：[docs/log.md](log.md) `[2026-11-07] 待辦 | 規格書 v2 之後` 與 [美術設計規格書.md](art/美術設計規格書.md) 第十、十一章；2026-11-25 拆解建檔，Antigravity by Google DeepMind。

### TD-008 | waiting | test | 手機實機測試專注寫稿模式（虛擬鍵盤高度）與新聞卡存圖
- **內容**：在真實手機瀏覽器（iOS Safari / Android Chrome）測試 `index.html` 手機版：點擊聲明稿輸入框進入「專注寫稿模式」時，隱藏指令區後字幕預覽、輸入框與發布鈕是否確實留在虛擬鍵盤上方而不被遮住；以及像素新聞卡長按存圖／一鍵下載在手機瀏覽器之實際可用性。
- **完成條件**：完成實機測試紀錄，若發現跑版已修復或登記 `FP-NNN`；[DESIGN.md](../DESIGN.md) 第五章第 3、4 項可標為已定。
- **等待**：`index.html` 灰盒與結局畫面完成（`TD-003`、`TD-007`），並由使用者於實機操作回報體感。
- **關聯**：TD-003、TD-007
- **來源**：[docs/log.md](log.md) `[2026-11-07] 待辦 | 規格書 v2 之後`；2026-11-25 遷移建檔，Antigravity by Google DeepMind。

### TD-009 | open | deploy | 準備 GitHub Pages 部署、全流程驗收與期末 Demo 檢核
- **內容**：確認單檔 `index.html` 可直接在 GitHub Pages 根目錄正常運行（無相對路徑失效、Cubic 11 字型子集內嵌可離線顯示、離線智囊庫備援正常），更新 [README.md](../README.md) 線上遊玩網址與全部進度勾選，完成桌面與手機全流程驗收報告以備錄製 1～3 分鐘 Demo 影片與期末報告。
- **完成條件**：GitHub Pages 線上可玩、無控制台錯誤、`lint_project.py` ERROR 0、`pipeline_status.py` 全數 OK。
- **關聯**：TD-006、TD-007、TD-008
- **來源**：[README.md](../README.md) 目前進度與 [期末專案提案.md](proposal/期末專案提案.md) 第六章；2026-11-25 建檔，Antigravity by Google DeepMind。
