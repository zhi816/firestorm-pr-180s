---
name: git-sync-guardian
description: >-
  Guard version control synchronization in a multi-AI collaborative environment for firestorm-pr-180s. Ensures pre-flight fetch checks, atomic commit-and-push operations, entry-by-entry staging for shared docs (log/issues/todo), and conflict-free append-only log merges.
---

# Git Sync Guardian（多 AI 協同版本同步守護技能）

## 一、協作背景

本專案支援多代理人（Claude Code 含手機端、Codex、Antigravity / Gemini 等）異步協同開發。為避免分支分岔、本機遺留未推送提交、誤帶走他人修改與日誌覆蓋，所有 Git 操作必須使用本 Skill 的工具鏈。

---

## 二、核心鐵律

1. **提交必含推送（Commit Implies Push）**：完成工作或提交變更時，必須立即推送到遠端（`main` 或當前功能分支），不得留滯未推送的本機 commit。
2. **動工前必先檢查遠端（Pre-flight Fetch Check）**：實質修改前執行 `status.py`；若落後遠端，執行 `sync.py` 安全合流。
3. **日誌並行合流（Log Append-Only Concurrency）**：`docs/log.md` 只在結尾追加，遇衝突時由 `merge_log.py` 按時間保留雙方條目。
4. **只提交自己的修改（Commit Only Your Own Changes）**：嚴禁 `git add -A`、`git add .`、`git commit -a`。共用檔 `docs/log.md`、`docs/issues.md`、`docs/todo.md` 一律經由 `safe_commit_push.py` 逐條暫存。
5. **寫入日誌即提交（Log Implies Commit）**：追加 `docs/log.md` 代表工作已完成，須於同一回合執行 `safe_commit_push.py` 推送；未完成之進度改記於 `docs/todo.md`（若僅新增或更新待辦而無其他已完成產出，可直接提交 `docs/todo.md` 而不另寫日誌）。
6. **撤回工作不刪紀錄（Undo Without Erasing Records）**：不得以 `git revert`、`git reset` 回退整份共用檔；只撤回程式碼或規格內容並另補日誌說明。

---

## 三、常用工具指令

所有腳本皆為跨平台 Python（3.7 以上標準函式庫），於倉庫根目錄執行：

```bash
# 1. 檢查遠端與本機狀態
python3 .agents/skills/git-sync-guardian/scripts/status.py

# 2. 安全合流遠端更新（含 --autostash 與日誌自動合併）
python3 .agents/skills/git-sync-guardian/scripts/sync.py

# 3. 取得寫日誌用的臺北時間（UTC+8，YYYY-MM-DD HH:MM）
python3 .agents/skills/git-sync-guardian/scripts/log_time.py

# 4. 依條目讀取 docs/log.md 最後幾筆（不得整份讀取日誌）
python3 .agents/skills/git-sync-guardian/scripts/log_tail.py -n 3
python3 .agents/skills/git-sync-guardian/scripts/log_tail.py --grep TD-003 -n 0

# 5. 取得下一個待辦 / 問題編號
python3 .agents/skills/git-sync-guardian/scripts/stage_todo.py --next-id
python3 .agents/skills/git-sync-guardian/scripts/stage_issues.py --next-id

# 6. 原子提交並推送（明確列出檔案，共用檔搭配旗標）
python3 .agents/skills/git-sync-guardian/scripts/safe_commit_push.py "<commit_message>" --agent "<代理名稱>" --todo TD-003 -- docs/todo.md docs/log.md index.html
python3 .agents/skills/git-sync-guardian/scripts/safe_commit_push.py "fix(spec): resolve FP-001" --agent "<代理名稱>" --issue FP-001 --todo TD-002 -- docs/dev/實作規格書.md docs/issues.md docs/todo.md docs/log.md
```

### 旗標說明
- `--agent`：列出 `docs/log.md` 時必填，須吻合條目中的 `- **執行代理**：` 一行。
- `--branch`：可選，限定必須在指定分支執行（支援 `main` 與手機/雲端代理開出的 `claude/...` 等具名分支；禁止 detached HEAD）。
- `--issue FP-NNN`：提交 `docs/issues.md` 時必填（可重複）；歸檔搬移時用 `--issue ARCHIVED`。
- `--todo TD-NNN`：提交 `docs/todo.md` 時必填（可重複），包含完成後刪除的條目。
- `--log-heading`：同代理多工作階段同時寫日誌時，精確指定自己的標題。
- `--allow-stale-log`：僅在推送失敗重試等情況下放行超過 60 分鐘的舊日誌時間戳記。
