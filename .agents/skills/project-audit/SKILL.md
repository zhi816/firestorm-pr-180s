---
name: project-audit
description: >-
  Audit project governance, spec consistency, Zero-Emoji compliance, broken links, log append-only integrity, and issue/todo tracking for firestorm-pr-180s. Use before committing, after spec/code changes, or when investigating/archiving FP-NNN issues.
---

# Project Audit（專案規範與問題稽核技能）

## 一、用途與使用時機

本 Skill 負責維護 `firestorm-pr-180s` 的文件一致性、規範遵循與問題追蹤：
- 每次完成階段任務、修改規格或更新 `index.html` 後，執行 `lint_project.py` 確保無 `ERROR`。
- 發現程式碼錯誤、手機跑版或規格書矛盾時，登記於 `docs/issues.md`（編號 `FP-NNN`），不得只寫在日誌。
- 調查某個檔案或模組的歷史問題與相關待辦時，用 `issues_for.py` 查詢，不必整份閱讀清單。

---

## 二、常用指令

```bash
# 1. 全專案文件與規格檢查（提交前必跑，ERROR 必須為 0）
python3 .agents/skills/project-audit/scripts/lint_project.py
python3 .agents/skills/project-audit/scripts/lint_project.py --errors-only

# 2. 查詢某檔案或關鍵字的未結／已歸檔問題與相關待辦
python3 .agents/skills/project-audit/scripts/issues_for.py index.html
python3 .agents/skills/project-audit/scripts/issues_for.py docs/dev/實作規格書.md

# 3. 歸檔已結案（fixed / wontfix）問題到 docs/issues/closed/
python3 .agents/skills/project-audit/scripts/archive_issues.py
python3 .agents/skills/project-audit/scripts/archive_issues.py --apply --agent "<代理名稱>"
```

---

## 三、問題登記與結案規範

1. **取號**：新增問題前執行 `python3 .agents/skills/git-sync-guardian/scripts/stage_issues.py --next-id` 取得下一個 `FP-NNN`。
2. **格式**：
   ```markdown
   ### FP-001 | open | <相對於倉庫根目錄之檔案路徑> | <位置或模組> | <問題類型>
   - **問題**：具體現象或規格衝突。
   - **依據**：對應規格書或預期行為。
   - **關聯**：TD-NNN（選填，若需排程修補）
   - **發現於**：docs/log.md [YYYY-MM-DD HH:MM] 或 人工審查（執行代理）
   ```
   問題類型建議值：`功能異常`、`介面跑版`、`規格不符`、`API異常`、`無障礙或效能`、`待確認`。
3. **結案不刪不手動搬**：修好後原地把 `open` 改為 `fixed`（或經使用者同意改 `wontfix` 並註明理由），補上 `- **處理**：YYYY-MM-DD、執行代理、修正方式`。歸檔一律由 `archive_issues.py` 統一執行，不得自行剪貼搬移。
4. **互指**：若問題須等使用者決定或另排開發工項，維持 `open` 並於 `docs/todo.md` 開立對應 `TD-NNN`，兩邊以 `- **關聯**：` 互指。
