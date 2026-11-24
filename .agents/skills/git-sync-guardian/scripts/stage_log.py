#!/usr/bin/env python3
"""stage_log.py: 只把「自己寫的」日誌條目加入 Git 暫存區（docs/log.md）。

多個 AI 共用同一個工作目錄時，docs/log.md 常同時含有別的代理尚未提交的條目。
本腳本以「HEAD 版日誌 + 自己的新條目」組出要提交的版本，寫入暫存區；
工作目錄中的檔案不變，別人的條目留給他們自己提交。

判斷依據：條目中「- **執行代理**：」一行包含指定的代理名稱（不分大小寫）。
相容 2026-11-08 以前之舊版條目（## [YYYY-MM-DD] ...，無 HH:MM），保留於既有條目中不更動。

用法（於倉庫根目錄或任意子目錄執行）：
    python3 .agents/skills/git-sync-guardian/scripts/stage_log.py "Claude Code"
    python3 .agents/skills/git-sync-guardian/scripts/stage_log.py "Antigravity" --dry-run
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime

LOG_PATH = 'docs/log.md'
ANY_HEADING = re.compile(r'(?m)^## \[(\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2})?)\]')
NEW_HEADING = re.compile(r'^## \[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]')
AGENT_LINE = re.compile(r'(?m)^- \*\*執行代理\*\*：(.*)$')

FUTURE_MINUTES = 5
STALE_MINUTES = 60


def git(*args, data=None):
    r = subprocess.run(['git', *args], input=data, capture_output=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr.decode('utf-8', 'replace'))
        sys.exit(1)
    return r.stdout


def split(text):
    """回傳 (檔頭, [條目...])；每個條目從標題行開始，到下一個標題前為止（含尾端空行）。"""
    idx = [m.start() for m in ANY_HEADING.finditer(text)]
    if not idx:
        return text, []
    return text[:idx[0]], [text[a:b] for a, b in zip(idx, idx[1:] + [len(text)])]


def norm(entry):
    return entry.replace('\r\n', '\n').strip()


def check_timestamps(mine, allow_stale):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from log_time import now_taipei
    now = now_taipei().replace(tzinfo=None)
    bad = False
    for e, _ in mine:
        head = e.splitlines()[0]
        m = NEW_HEADING.match(e)
        if not m:
            sys.stderr.write('錯誤：新日誌條目必須包含臺北時間 HH:MM（格式 ## [YYYY-MM-DD HH:MM]）：%s\n' % head)
            bad = True
            continue
        t = datetime.strptime(m.group(1), '%Y-%m-%d %H:%M')
        diff = (t - now).total_seconds() / 60
        if diff > FUTURE_MINUTES:
            sys.stderr.write('錯誤：日誌標題時間晚於現在（臺北時間 %s）：%s\n' % (now.strftime('%Y-%m-%d %H:%M'), head))
            bad = True
        elif -diff > STALE_MINUTES and not allow_stale:
            sys.stderr.write('錯誤：日誌標題時間早於現在 %d 分鐘以上（臺北時間 %s）：%s\n'
                             % (STALE_MINUTES, now.strftime('%Y-%m-%d %H:%M'), head))
            bad = True
    if bad:
        sys.stderr.write('請先執行 python3 .agents/skills/git-sync-guardian/scripts/log_time.py 取得目前時間，\n'
                         '再於工作目錄中修正自己這筆尚未提交的條目標題。若條目確實早已寫好（例如推送失敗後重試），\n'
                         '可改加 --allow-stale。\n')
    return bad


def with_work_trailing(base_entry, work_entry, eol):
    body = base_entry.rstrip(' \t\r\n')
    trailing = work_entry[len(work_entry.rstrip(' \t\r\n')):]
    trailing = trailing.replace('\r\n', '\n').replace(' ', '').replace('\t', '')
    if eol == '\r\n':
        trailing = trailing.replace('\n', '\r\n')
    return body + trailing


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass
    ap = argparse.ArgumentParser(description='只暫存指定代理寫的 docs/log.md 條目')
    ap.add_argument('agent', help='執行代理名稱的一部分，例如 "Claude Code"、"Codex"、"Antigravity"')
    ap.add_argument('--heading', action='append', default=[], help='只選取指定的新日誌標題行；可重複指定')
    ap.add_argument('--dry-run', action='store_true', help='只列出結果，不寫入暫存區')
    ap.add_argument('--allow-stale', action='store_true',
                    help='允許標題時間早於現在 %d 分鐘以上（僅限推送失敗後重試）' % STALE_MINUTES)
    a = ap.parse_args()

    root = git('rev-parse', '--show-toplevel').decode().strip()
    head_r = subprocess.run(['git', '-C', root, 'show', 'HEAD:' + LOG_PATH], capture_output=True)
    base = head_r.stdout.decode('utf-8') if head_r.returncode == 0 else ''
    work = open(f'{root}/{LOG_PATH}', 'rb').read().decode('utf-8')

    _, base_entries = split(base)
    _, work_entries = split(work)
    work_keys = [norm(e) for e in work_entries]
    base_keys = {norm(e) for e in base_entries}

    missing = [e for e in base_entries if norm(e) not in set(work_keys)]
    if missing:
        sys.stderr.write('錯誤：工作目錄的日誌改寫或刪除了已提交的條目（違反 append-only），請先處理：\n')
        for e in missing:
            sys.stderr.write('  ' + e.splitlines()[0] + '\n')
        sys.exit(1)

    new_entries = [e for e, k in zip(work_entries, work_keys) if k not in base_keys]
    if a.heading:
        available = {e.splitlines()[0].strip() for e in new_entries if e.splitlines()}
        missing_h = set(a.heading) - available
        if missing_h:
            sys.stderr.write('錯誤：找不到指定的新日誌標題：\n')
            for heading in sorted(missing_h):
                sys.stderr.write('  ' + heading + '\n')
            sys.exit(1)
        selected = set(a.heading)
        new_entries = [e for e in new_entries if e.splitlines() and e.splitlines()[0].strip() in selected]

    mine, others = [], []
    for e in new_entries:
        m = AGENT_LINE.search(e)
        who = m.group(1).strip() if m else '（未標明執行代理）'
        (mine if m and a.agent.lower() in who.lower() else others).append((e, who))

    if check_timestamps(mine, a.allow_stale):
        sys.exit(1)

    for e, who in mine:
        print('暫存：' + e.splitlines()[0])
    for e, who in others:
        if a.heading and e.splitlines()[0].strip() in set(a.heading):
            sys.stderr.write('錯誤：指定的日誌標題不屬於代理「' + a.agent + '」：' + e.splitlines()[0] + '\n')
            sys.exit(1)
        print('略過（' + who + '）：' + e.splitlines()[0])
    if not mine:
        print('沒有「' + a.agent + '」的新條目，未變更暫存區。')
        return

    base_header, base_entries = split(base)
    work_header, _ = split(work)
    if not base_header and work_header:
        base_header = work_header
    elif base_header != work_header and not others:
        # 允許在首次引進新規範時更新檔頭說明（只要沒有其他人的未提交條目）
        base_header = work_header

    base_keys_list = [norm(e) for e in base_entries]
    mine_keys = {norm(e) for e, _ in mine}
    eol = '\r\n' if (base or work).count('\r\n') * 2 > (base or work).count('\n') else '\n'

    plan, ptr = [], 0
    for entry, key in zip(work_entries, work_keys):
        if ptr < len(base_entries) and key == base_keys_list[ptr]:
            plan.append(('base', with_work_trailing(base_entries[ptr], entry, eol)))
            ptr += 1
        elif key in mine_keys:
            plan.append(('mine', entry))
    if ptr != len(base_entries):
        sys.stderr.write('警告：工作目錄中已提交條目的順序與 HEAD 不同，新條目改為接在檔尾。\n')
        plan = [('base', e) for e in base_entries] + [('mine', e) for e, k in zip(work_entries, work_keys) if k in mine_keys]

    staged = base_header

    def ensure_blank_line(text):
        if not text or text.endswith('\n\n') or text.endswith('\r\n\r\n'):
            return text
        return text + (eol if text.endswith('\n') else eol + eol)

    for kind, entry in plan:
        if kind == 'base':
            staged += entry
            continue
        staged = ensure_blank_line(staged)
        body = entry.replace('\r\n', '\n')
        if not body.endswith('\n'):
            body += '\n'
        if eol == '\r\n':
            body = body.replace('\n', '\r\n')
        staged += body
    if a.dry_run:
        print('（dry-run）共 %d 筆，未寫入暫存區。' % len(mine))
        return
    sha = git('-C', root, 'hash-object', '-w', '--stdin', data=staged.encode('utf-8')).decode().strip()
    git('-C', root, 'update-index', '--add', '--cacheinfo', '100644,%s,%s' % (sha, LOG_PATH))
    print('已暫存 %d 筆；工作目錄中的 %s 未變更，其他代理的 %d 筆條目留在工作目錄。' % (len(mine), LOG_PATH, len(others)))


if __name__ == '__main__':
    main()
