# 待辦清單（Todo）

> 本檔登記尚未完成之開發任務、交接事項與須等使用者確認才能動工的工作，也是手機端深夜指派任務的主要入口。格式與規則見 [AGENTS.md](../AGENTS.md) 第六章第 4 節，接手順序見第五章第 4 節。標題四段依序為：編號、狀態（`open` / `waiting` / `doing`）、範圍（`app` / `art` / `spec` / `test` / `rule` / `skill` / `deploy`）、標題。
>
> 完成或經同意放棄之條目直接刪除，並於當次日誌條目寫明編號；新增前以 `python3 .agents/skills/git-sync-guardian/scripts/stage_todo.py --next-id` 取號。不收程式 Bug 或規格矛盾（登記於 [issues.md](issues.md)）、美術方向選擇題本身（登記於 [DESIGN.md](../DESIGN.md) 第五章）。

### TD-006 | open | app | 串接 Command Code Provider API 與 JSON 防呆
- **內容**：依 [實作規格書.md](dev/實作規格書.md) 第一、四章，實作 `callLLMJudge()`：呼叫 `https://api.commandcode.ai/provider/v1/chat/completions`（Key 讀自 `localStorage`，日後改走 TD-012 中繼），System Prompt 要求回傳第四章第 2 節之判讀 JSON（逐題回應、誠意、甩鍋、紅旗、代寫嫌疑、敗筆、評語、6 則留言、新聞標題）；撤回後第二次送審附上第一次的敗筆；12 秒逾時、非 200、429 或 JSON 解析失敗時自動改用離線判讀；欄位缺漏以離線結果補齊。先以少量真實呼叫實測預設模型 `deepseek/deepseek-v4.1-flash-fast` 與備選模型之延遲和 JSON 穩定度，結果寫回實作規格書。
- **完成條件**：有 Key 時可正常判讀並交給前端公式計分；無 Key 與模擬失敗時離線模式順暢通關；`pipeline_status.py` 之 P4 檢核通過；Key 未出現在任何受版控檔案。
- **關聯**：TD-011
- **進度**：2026-11-25 第一版 `index.html` 已寫好 `callLLMJudge()`（Command Code 端點、12 秒逾時、代碼框清洗、欄位缺漏以離線結果補齊、撤回時附上次敗筆）與設定彈窗（Key、模型）。2026-11-25 經 Worker 中繼（`TD-012` 已完成）以預設模型 `deepseek/deepseek-v4.1-flash-fast` 實測 1 次：約 6.2 秒、回傳合法 JSON、欄位齊全；備選模型與玩家自備 Key 路徑尚未實測，留待 `TD-013`、`TD-014` 改完 Prompt 後與 `TD-015` 一併量測。Claude Code by Anthropic。
- **來源**：[實作規格書.md](dev/實作規格書.md) 第四章；2026-11-25 拆解建檔，Antigravity by Google DeepMind；2026-11-25 遊戲流程 v2 定案後更新，Claude Code by Anthropic。

### TD-007 | open | app | 實作結局（含隱藏結局）、像素新聞卡、名醫診斷書、最佳紀錄與音效
- **內容**：依 [美術設計規格書.md](art/美術設計規格書.md) 第十、十一章與 [實作規格書.md](dev/實作規格書.md) 第四章第 4 節、第八章：（1）四種結局加隱藏結局 `ENDING_GHOSTWRITER`；（2）`320×180` 放大 4 倍成 `1280×720` 之「炎上新聞台 FNN」像素新聞卡（逐字量寬度斷行、一鍵下載＋長按存圖提示）；（3）米黃紙張「AI 公關名醫診斷書」（病患為所選角色）；（4）`localStorage` 最佳紀錄；（5）Web Audio 8-bit 音效（電腦與手機皆預設開啟）與靜音鈕，支援 `prefers-reduced-motion`。
- **完成條件**：五種結局之新聞卡、診斷書與表情皆正確渲染並可下載 PNG，最佳紀錄於封面顯示，音效可開關且無音檔依賴，`pipeline_status.py` 之 P5 檢核通過。
- **關聯**：TD-011
- **進度**：2026-11-25 第一版已完成五種結局（含隱藏結局）、像素新聞卡（一鍵下載＋長按提示）、名醫診斷書、最佳紀錄與 Web Audio 音效（2026-11-25 改為電腦與手機皆預設開啟）；尚缺：音效實際聽感確認（新聞卡缺字 `FP-002` 已於 2026-11-25 修正）。Claude Code by Anthropic。
- **來源**：[美術設計規格書.md](art/美術設計規格書.md) 第十、十一章；2026-11-25 拆解建檔，Antigravity by Google DeepMind；2026-11-25 遊戲流程 v2 定案後更新，Claude Code by Anthropic。

### TD-008 | waiting | test | 手機實機測試專注寫稿模式（虛擬鍵盤高度）與新聞卡存圖
- **內容**：在真實手機瀏覽器（iOS Safari / Android Chrome）測試 `index.html` 手機版：點擊聲明稿輸入框進入「專注寫稿模式」時，隱藏指令區後字幕預覽、輸入框與發布鈕是否確實留在虛擬鍵盤上方而不被遮住；以及像素新聞卡一鍵下載與長按存圖在手機瀏覽器之實際可用性。
- **完成條件**：完成實機測試紀錄，若發現跑版已修復或登記 `FP-NNN`；[DESIGN.md](../DESIGN.md) 第五章第 1 項可標為已定。
- **等待**：結局畫面收尾（`TD-007`）後，由使用者於實機操作回報體感（`index.html` 第一版已可測）。
- **關聯**：TD-007
- **來源**：[docs/log.md](log.md) `[2026-11-07] 待辦 | 規格書 v2 之後`；2026-11-25 遷移建檔，Antigravity by Google DeepMind。

### TD-009 | open | deploy | 準備 GitHub Pages 部署、全流程驗收與期末 Demo 檢核
- **內容**：確認單檔 `index.html` 可直接在 GitHub Pages 根目錄正常運行（無相對路徑失效、Cubic 11 子集內嵌可離線顯示、離線模式正常）；Pages 以 `.github/workflows/pages.yml` 只發布 `index.html`（2026-11-25 使用者決定，比照 Epoch-Kairos）；更新 [README.md](../README.md) 線上遊玩網址與進度勾選；完成桌面與手機全流程驗收以備錄製 1～3 分鐘 Demo 影片與期末報告。
- **完成條件**：GitHub Pages 線上可玩、無控制台錯誤、`lint_project.py` ERROR 0、`pipeline_status.py` 全數 OK。
- **進度**：2026-11-25 已新增 `.github/workflows/pages.yml`；使用者已將 Pages Source 設為 GitHub Actions 並完成首次部署，<https://zhi816.github.io/firestorm-pr-180s/> 回應 200，README 已加線上網址；尚缺手機實機驗收與 Demo 影片。Claude Code by Anthropic。
- **關聯**：TD-006、TD-007、TD-008
- **來源**：[README.md](../README.md) 目前進度與 [期末專案提案.md](proposal/期末專案提案.md) 第六章；2026-11-25 建檔，Antigravity by Google DeepMind。

### TD-010 | open | app | 實作角色選擇頁與 4 位主角點陣圖
- **內容**：依 [角色與事件庫.md](dev/角色與事件庫.md) 第一章，於 `index.html` 建立 `CHARACTERS` 資料（初始粉絲、廠商信任、專屬規則）與 `STATE_SELECT` 角色卡（電腦 4 欄、手機 2×2）；依 [美術設計規格書.md](art/美術設計規格書.md) 第七章，以同一套 28×28 骨架繪製小艾、阿凱、博士 Leo、饅頭四位主角與共用表情集（含隱藏結局「被抓包」）。
- **完成條件**：可選任一角色並帶入正確初始數值，四位角色各表情於影片區、新聞卡與診斷書正確顯示，`verify_app.js` 雙端無錯誤。
- **進度**：2026-11-25 第一版已完成 `STATE_SELECT` 角色卡與 4 位主角（同一骨架換髮色、服裝與配件：耳機、眼鏡、廚師帽）及表情集；畫風仍為灰盒程度（阿凱短髮剪裁不完整），待使用者看過後決定是否精修。2026-11-25 依使用者要求，道歉影片背景改為每位角色各一間直播間（美妝化妝間、電競房、書房、廚房），並加入 30 餘種事件道具與關燈、雜訊畫面效果。Claude Code by Anthropic。
- **來源**：2026-11-25 使用者指示（開場自選角色，先做 4 位），Claude Code by Anthropic。

### TD-011 | open | app | 實作前端計分公式與離線關鍵字判讀
- **內容**：依 [實作規格書.md](dev/實作規格書.md) 第三至五章，實作純函式 `scoreRound(judgement, ctx)`（合併 LLM 或離線判讀、策略效果與一致性檢查、事件專屬指令的 `fx` 效果、角色倍率、撤回與小幫手懲罰，算出掉粉、炎上度、廠商信任與結局）與 `offlineJudge(statement, event)`（關鍵字逐題判讀、誠意與甩鍋規則、紅旗偵測、從 `offline_comments` 與模板產生文字）；為 10 則事件各補齊 12 則離線留言。
- **完成條件**：以至少 5 組固定測試稿（誠懇、甩鍋、威脅提告、空白、小幫手原稿）驗證同一輸入結果一致且結局符合預期；試玩後將公式調整結果寫回實作規格書並把 [DESIGN.md](../DESIGN.md) 第五章第 2 項標為已定。
- **進度**：2026-11-25 第一版已完成 `scoreRound()` 與 `offlineJudge()`，並以 5 組稿（甩鍋、誠懇全答、空白神隱、官腔小幫手原稿、撤回後改寫）驗證結局符合預期；係數已依實測下修（見實作規格書第四章）。2026-11-25 已為 10 則事件各補齊 12 則離線留言（每位人設 2 則隨機抽 1 則，少量混入 2026 年台灣 Threads 用語），System Prompt 亦允許 AI 適度用梗。尚缺：試玩後再調門檻。另於 2026-11-25 策略改為每則事件 4 個專屬影片形式＋4 個專屬公關話術（共 80 個，見角色與事件庫第三章），計分改由各指令的 `fx` 資料驅動，話術另附專屬留言；各選項數值仍待實機調手感。Claude Code by Anthropic。
- **來源**：2026-11-25 使用者同意「LLM 判讀、前端計分」，Claude Code by Anthropic。

### TD-015 | open | test | 實測評估是否啟用 JSON 模式（`response_format`）
- **內容**：[實作規格書.md](dev/實作規格書.md) 第四章第 6 節規定呼叫 LLM 時要帶 `response_format: { type: "json_object" }`（JSON 模式，由服務端保證回傳語法正確的 JSON），但目前前端 `callLLMJudge()` 與 Worker（`worker/src/index.js` 組裝請求處）都沒有帶。目前只靠 Prompt 文字要求「只輸出 JSON」，模型多寫說明、少括號或被截斷時解析失敗，該局改走離線。先用真實 Key 對三個候選模型（`deepseek/deepseek-v4.1-flash-fast`、`z-ai/glm-5.3-flash`、`google/gemini-3.8-flash`）各送數份稿，比較帶與不帶此參數時的成功率、延遲與是否回錯誤；再決定：（1）全部支援就直接加上；（2）部分不支援就改成「帶參數被拒絕時拿掉參數重送一次」；（3）效果不明顯就不加，並把規格書該句改掉。前端與 Worker 兩條路徑做法要一致；若 `TD-013` 已拆成兩次呼叫，兩支請求都要評估。
- **完成條件**：實測結果（各模型是否支援、JSON 解析成功率、延遲）寫回實作規格書第四章第 6 節，程式與規格書說法一致；選定做法後模擬參數被拒絕時遊戲仍能順利通關；`lint_project.py` ERROR 0。
- **關聯**：TD-006
- **來源**：2026-11-25 使用者指示（盤點 AI 用途與提案對照時發現規格書有寫、程式沒做，決定放到後面測試評估），Claude Code by Anthropic。

### TD-017 | open | app | 優化電腦寬螢幕三欄排版與畫面空間配置
- **內容**：依使用者於 2026-11-27 提供的實機畫面截圖（[桌面版排版截圖_開場.jpg](assets/桌面版排版截圖_開場.jpg)、[桌面版排版截圖_裁決.jpg](assets/桌面版排版截圖_裁決.jpg)），目前 `index.html` 電腦版（`>1080px`）整體 `.wrap` 限制在 `max-width: 1200px` 置中，寬螢幕下左右兩側留白過大，所有內容（頂欄、三欄與底部對話框）擠在畫面中央；且在裁決階段（`STATE_VERDICT`）中欄同時堆疊影片播放器與「裁判長判決」面板、右欄「炎串 · 留言區」單欄拉長，整體空間比例與閱讀寬度仍有優化空間。後續需評估放寬容器寬度、調整欄寬比例或各階段面板配置，並同步更新 [美術設計規格書.md](art/美術設計規格書.md) 第九章與 [DESIGN.md](../DESIGN.md) 第三章（僅優化桌面端，不影響手機 `<=760px` 既有體驗）。
- **完成條件**：與使用者確認排版優化方案並實作於 `index.html`；寬螢幕下左右留白過大與中央擁擠問題改善；`verify_app.js` 桌面與手機皆 FAIL 0、`lint_project.py` ERROR 0。
- **來源**：2026-11-27 使用者回報（提供截圖，先存檔列待辦暫不修改），Antigravity by Google DeepMind。
