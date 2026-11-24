# CLAUDE.md - Claude Code 入口與快速規則

> 本專案的完整維護手冊、格式規範與多 AI 協作協定統一收錄於根目錄 [`AGENTS.md`](./AGENTS.md)，美術與 UX 決策（含否決紀錄）收錄於 [`DESIGN.md`](./DESIGN.md)。

Claude Code（含桌面、終端機與手機／網頁版）在開始任何實質工作前，請依序完成下列動作：

1. **先讀入口文件**：
   - [`AGENTS.md`](./AGENTS.md)：完整架構、日誌／問題／待辦格式與 Git 鐵律。
   - [`DESIGN.md`](./DESIGN.md)：美術方向與否決紀錄（勿重提已否決方案）。
   - [`docs/todo.md`](./docs/todo.md)：目前可認領的 `open` 任務與須等確認的 `waiting` 任務。
   - [`docs/issues.md`](./docs/issues.md)：目前尚未結案的 `FP-NNN` 問題清單。
2. **載入對應 Skill**：`.claude/skills/` 內已設定轉介檔指向 `.agents/skills/` 正本：
   - 開發或修改 `index.html`／樣張：`game-build-pipeline`
   - 健康檢查與問題管理：`project-audit`
   - 遠端同步與提交推送：`git-sync-guardian`
3. **每日與每次交接鐵律**：
   - **動工前先同步**：執行 `python3 .agents/skills/git-sync-guardian/scripts/status.py`（必要時 `sync.py`）。
   - **不整份讀 `docs/log.md`**：查近期紀錄一律跑 `python3 .agents/skills/git-sync-guardian/scripts/log_tail.py -n 3`。
   - **Zero-Emoji**：所有文件與新程式碼嚴禁使用 Emoji，一律繁體中文。
   - **提交必含推送，只提交自己的修改**：寫入 `docs/log.md`（先跑 `log_time.py` 取得臺北時間）後，使用 `safe_commit_push.py` 搭配 `--agent`、`--todo`、`--issue` 提交並立即推送。
