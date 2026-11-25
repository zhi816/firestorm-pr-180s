# 問題與缺陷清單（Issues）

> 本檔登記查核或測試發現之程式缺陷、版面跑版、API 異常與規格前後矛盾，格式與規則見 [AGENTS.md](../AGENTS.md) 第六章第 3 節。標題五段依序為：編號、狀態（`open` / `fixed` / `wontfix`）、相對於倉庫根目錄之檔案路徑、位置或模組、問題類型。
>
> 修正時就地改狀態並追加 `- **處理**：` 行，不得刪除條目；新增前以 `python3 .agents/skills/git-sync-guardian/scripts/stage_issues.py --next-id` 取號。本檔不分節，只放尚未結案條目；已結案條目由 `archive_issues.py` 統一搬至 [docs/issues/closed/](issues/closed/)。查詢特定檔案問題請執行 `python3 .agents/skills/project-audit/scripts/issues_for.py <目標>`。

### FP-001 | fixed | docs/dev/實作規格書.md | 第四章與第六章 | 規格不符
- **問題**：[實作規格書.md](dev/實作規格書.md) 仍保留 v1 時期寫法，與現行規格及版權原則有三處衝突：（1）第四章 Prompt 範例與第六章仍出現真實品牌「蘋果/TVBS」「TVBS 突發新聞」，違反虚構品牌「炎上新聞台 FNN」規定；（2）第六章新聞圖卡尺寸與版型仍寫擬真演播室 `1200 x 675`，未對齊 [美術設計規格書.md](art/美術設計規格書.md) 第十章之 `320×180` 放大 4 倍成 `1280×720` 像素新聞卡；（3）第一章 Gemini 支援寫為舊型號 `gemini-1.5-flash` 且第五章未補充手機 `<=760px` 階段式佈局連結。
- **依據**：[美術設計規格書.md](art/美術設計規格書.md) 第九、十、十二章與 [DESIGN.md](../DESIGN.md) 第一、四、六章。
- **關聯**：TD-002
- **發現於**：2026-11-25 專案架構盤點（Antigravity by Google DeepMind）
- **處理**：2026-11-25，Claude Code by Anthropic。依遊戲流程 v2 定案改寫 [實作規格書.md](dev/實作規格書.md)：移除真實品牌改用「炎上新聞台 FNN」；新聞卡改為 `320×180` 放大 4 倍成 `1280×720`；LLM 改為 Command Code Provider API（不再列 `gemini-1.5-flash`）；第六章補上手機 `<=760px` 階段式版面並指向美術設計規格書第九章。

### FP-002 | fixed | index.html | Cubic11 像素字型子集 | 介面跑版
- **問題**：`index.html` 沿用樣張 v3 內嵌之 Cubic 11 子集，只含樣張用過的字；正式版事件、留言與新聞卡標題中許多字不在子集內，瀏覽器改以 Noto Sans TC 補字，同一行混用兩種字型，新聞卡 Canvas 上尤其明顯（例如「純情」「紀錄」）。
- **依據**：[美術設計規格書.md](art/美術設計規格書.md) 第四章「像素字【定案】」：正式版只把頁面用到的字做成子集並以 base64 內嵌。
- **關聯**：TD-007
- **發現於**：2026-11-25 第一版截圖檢查（Claude Code by Anthropic）。修法：取得 Cubic 11 完整字型檔，以 `index.html` 與事件庫全部用字重新產生子集（約數千字，檔案會變大，須評估大小）。
- **處理**：2026-11-25，Claude Code by Anthropic。經使用者同意，自官方倉庫取得 Cubic 11 v1.451 完整字型（不進版控），新增 [`font_subset.py`](../.agents/skills/game-build-pipeline/scripts/font_subset.py) 以 `index.html` 實際用字重做子集：由 664 字增為 1288 字，woff2 由約 29KB 增為約 53KB，`index.html` 約增加 32KB；依使用者選擇只嵌用到的字，不嵌完整字型。字型本身沒有的 `▮▶▸` 與顏文字 `ꉂ𐤔` 仍由系統字型顯示。以內建瀏覽器實測：頁面 1144 個中文字全部由 Cubic 11 繪製，新聞卡（含原本缺字的「純情」「紀錄」）與診斷書不再混用字型，`verify_app.js` 桌面與手機 FAIL 0。日後新增文字以 `font_subset.py --check` 檢查（已寫入 game-build-pipeline S3）。

