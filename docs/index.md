# 文件總目錄

所有文件的清單。新增、搬動或刪除文件時要同步更新這一頁（規則見 [AGENTS.md](../AGENTS.md)）。

## 協作與設計規範（根目錄）

| 文件 | 摘要 |
| :--- | :--- |
| [AGENTS.md](../AGENTS.md) | AI 協作與維護手冊：三層架構、核心紅線、接手順序、日誌／問題／待辦格式與 Git 協定 |
| [DESIGN.md](../DESIGN.md) | 美術與介面方向紀錄：已定／暫定／待決／否決紀錄與版本歷程（動工前必讀） |
| [CLAUDE.md](../CLAUDE.md) | Claude Code 自動載入入口與快速規則（指向 `AGENTS.md` 與 `.claude/skills/`） |
| [README.md](../README.md) | 專案首頁、玩法簡介、架構總覽與目前進度清單 |

## 紀錄與任務追蹤

| 文件 | 摘要 |
| :--- | :--- |
| [log.md](log.md) | Append-only 工作與決策流水帳（不整份讀取，查詢用 `log_tail.py`） |
| [todo.md](todo.md) | 尚未完成之待辦任務看板（`TD-NNN`），手機端指派任務入口，完成即刪 |
| [issues.md](issues.md) | 尚未結案之缺陷與規格衝突清單（`FP-NNN`），已結案者歸檔於 `issues/closed/` |

## 企劃 `proposal/`

| 文件 | 摘要 |
| :--- | :--- |
| [期末專案提案.md](proposal/期末專案提案.md) | 動機、四階段玩法、雙 AI 智能體（網民大軍＋公關裁判）、Reflection 閉環、時程 |

## 程式 `dev/`

| 文件 | 摘要 |
| :--- | :--- |
| [實作規格書.md](dev/實作規格書.md) | 單檔架構、狀態機、事件庫資料結構、System Prompt 與 JSON 格式、API 呼叫、版面、Canvas 新聞卡、開發檢核清單 |

## 美術 `art/`

| 文件 | 摘要 |
| :--- | :--- |
| [美術設計規格書.md](art/美術設計規格書.md) | v2【暫定】：像素 RPG × 社群。RPG 對照表、Token、字型、元件、道歉影片圖層、點陣角色、動畫、電腦／手機版面、四種結局與新聞卡 |
| [samples/像素風格樣張_v1.html](art/samples/像素風格樣張_v1.html) | 像素 RPG 風格的可互動樣張：狀態血條、道歉影片圖層、酸民留言攻擊。手機版是長捲動，已由 v2 取代 |
| [samples/像素風格樣張_v2.html](art/samples/像素風格樣張_v2.html) | v1 加上手機版：固定狀態列、底部分頁、依階段切換畫面、直播留言疊在影片上 |
| [samples/像素風格樣張_v3.html](art/samples/像素風格樣張_v3.html) | v2 加上結局畫面：四種結局、像素新聞卡、AI 公關名醫診斷書。目前最新版 |
| [reference/參考圖說明.md](art/reference/參考圖說明.md) | 樣張 v3 的靜態參考圖包：電腦與手機各階段截圖、四張新聞卡、角色與頭像圖、可讀原始碼，以及給其他 AI 的使用說明 |

## 美術參考圖 `art/reference/`

樣張 v3 的靜態快照，說明見 [參考圖說明.md](art/reference/參考圖說明.md)。

| 檔案 | 內容 |
| :--- | :--- |
| [01_電腦版_完整畫面.png](art/reference/01_電腦版_完整畫面.png) | 電腦版三欄完整畫面 |
| [02_電腦版_道歉影片_鞠躬律師診斷書.png](art/reference/02_電腦版_道歉影片_鞠躬律師診斷書.png) | 道歉影片圖層：鞠躬、律師、診斷書 |
| [03_電腦版_道歉影片_黑底白字.png](art/reference/03_電腦版_道歉影片_黑底白字.png) | 道歉影片圖層：黑底白字 |
| [04_電腦版_結局畫面.png](art/reference/04_電腦版_結局畫面.png) | 電腦版結局全螢幕層 |
| [05_手機版_爆料.png](art/reference/05_手機版_爆料.png) | 手機版爆料階段 |
| [06_手機版_寫稿.png](art/reference/06_手機版_寫稿.png) | 手機版寫稿階段 |
| [07_手機版_公審.png](art/reference/07_手機版_公審.png) | 手機版公審階段（直播聊天室） |
| [08_手機版_結局.png](art/reference/08_手機版_結局.png) | 手機版結局階段（整頁長截圖） |
| [09_新聞卡_身敗名裂.png](art/reference/09_新聞卡_身敗名裂.png) | 新聞卡：身敗名裂 |
| [10_新聞卡_二度炎上.png](art/reference/10_新聞卡_二度炎上.png) | 新聞卡：二度炎上 |
| [11_新聞卡_黑紅巨星.png](art/reference/11_新聞卡_黑紅巨星.png) | 新聞卡：黑紅巨星 |
| [12_新聞卡_公關奇蹟.png](art/reference/12_新聞卡_公關奇蹟.png) | 新聞卡：公關奇蹟 |
| [13_角色與酸民頭像.png](art/reference/13_角色與酸民頭像.png) | 角色與 6 種酸民頭像 |
| [像素風格樣張_v3_原始碼.html](art/reference/像素風格樣張_v3_原始碼.html) | v3 樣張可讀原始碼（字型為佔位字） |

## 圖片 `assets/`

| 檔案 | 內容 |
| :--- | :--- |
| [遊戲核心流程圖.png](assets/遊戲核心流程圖.png) | 四階段詳細流程與 Reflection 閉環 |
| [遊戲流程圖_簡潔版.png](assets/遊戲流程圖_簡潔版.png) | 簡潔版流程圖 |
| [AI技術架構與Reflection流程圖.png](assets/AI技術架構與Reflection流程圖.png) | 雙 AI 資料流與 Reflection 架構 |

## 原始資料 `archive/`（只讀）

| 檔案 | 內容 |
| :--- | :--- |
| [初步提案.txt](archive/初步提案.txt) | 最早的構想：選 GitHub Pages 的理由、雙引擎（API＋離線）架構 |
| [期末專案提案_繳交版.txt](archive/期末專案提案_繳交版.txt) | 提案的純文字繳交版本 |
| [美術設計規格書_v1_擬真介面.md](archive/美術設計規格書_v1_擬真介面.md) | 美術規格書 v1（擬真介面方向），已由像素 RPG 版取代 |
