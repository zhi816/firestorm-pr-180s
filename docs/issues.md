# 問題與缺陷清單（Issues）

> 本檔登記查核或測試發現之程式缺陷、版面跑版、API 異常與規格前後矛盾，格式與規則見 [AGENTS.md](../AGENTS.md) 第六章第 3 節。標題五段依序為：編號、狀態（`open` / `fixed` / `wontfix`）、相對於倉庫根目錄之檔案路徑、位置或模組、問題類型。
>
> 修正時就地改狀態並追加 `- **處理**：` 行，不得刪除條目；新增前以 `python3 .agents/skills/git-sync-guardian/scripts/stage_issues.py --next-id` 取號。本檔不分節，只放尚未結案條目；已結案條目由 `archive_issues.py` 統一搬至 [docs/issues/closed/](issues/closed/)。查詢特定檔案問題請執行 `python3 .agents/skills/project-audit/scripts/issues_for.py <目標>`。

### FP-001 | open | docs/dev/實作規格書.md | 第四章與第六章 | 規格不符
- **問題**：[實作規格書.md](dev/實作規格書.md) 仍保留 v1 時期寫法，與現行規格及版權原則有三處衝突：（1）第四章 Prompt 範例與第六章仍出現真實品牌「蘋果/TVBS」「TVBS 突發新聞」，違反虚構品牌「炎上新聞台 FNN」規定；（2）第六章新聞圖卡尺寸與版型仍寫擬真演播室 `1200 x 675`，未對齊 [美術設計規格書.md](art/美術設計規格書.md) 第十章之 `320×180` 放大 4 倍成 `1280×720` 像素新聞卡；（3）第一章 Gemini 支援寫為舊型號 `gemini-1.5-flash` 且第五章未補充手機 `<=760px` 階段式佈局連結。
- **依據**：[美術設計規格書.md](art/美術設計規格書.md) 第九、十、十二章與 [DESIGN.md](../DESIGN.md) 第一、四、六章。
- **關聯**：TD-002
- **發現於**：2026-11-25 專案架構盤點（Antigravity by Google DeepMind）
