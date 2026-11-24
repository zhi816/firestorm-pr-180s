#!/usr/bin/env python3
"""issues_for.py: 列出某個檔案或模組的全部問題與相關待辦。

涵蓋：docs/issues.md 中尚未結案者、docs/issues/closed/ 中已結案者，
以及 docs/todo.md 中提到該路徑／關鍵字或「關聯」到其問題編號之待辦。

用法（於倉庫任意位置執行）：
    python3 .agents/skills/project-audit/scripts/issues_for.py index.html
    python3 .agents/skills/project-audit/scripts/issues_for.py docs/dev/實作規格書.md
    python3 .agents/skills/project-audit/scripts/issues_for.py 實作規格書 --open
    python3 .agents/skills/project-audit/scripts/issues_for.py index.html --list
"""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', 'git-sync-guardian', 'scripts')))
from stage_issues import blocks, PATH, CLOSED_DIR  # noqa: E402

HEAD_RE = re.compile(r'^### (FP-\d{3,}) \| (\w+) \| ([^|]+?) \|')
TODO_ITEM = re.compile(r'(?m)^### (TD-\d{3,}) \|')
BOUNDARY = re.compile(r'(?m)^##+ ')


def read(path):
    with open(path, encoding='utf-8') as fh:
        return fh.read().replace('\r\n', '\n')


def entries(text):
    out = []
    for iid, (s, e) in sorted(blocks(text).items(), key=lambda kv: int(kv[0][3:])):
        blk = text[s:e].strip('\n')
        m = HEAD_RE.match(blk)
        if m:
            out.append((iid, m.group(2), m.group(3).strip(), blk))
    return out


def match_target(target_path, query):
    q = query.replace('\\', '/').lower()
    t = target_path.replace('\\', '/').lower()
    return q == t or q in t


def related_todos(root, query, issue_ids):
    todo_path = os.path.join(root, 'docs', 'todo.md')
    if not os.path.exists(todo_path):
        return []
    text = read(todo_path)
    out = []
    q = query.replace('\\', '/').lower()
    for m in TODO_ITEM.finditer(text):
        nxt = BOUNDARY.search(text, m.end())
        blk = text[m.start():nxt.start() if nxt else len(text)].strip('\n')
        low = blk.lower()
        if q in low or any(iid in blk for iid in issue_ids):
            out.append(blk)
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description='列出某一檔案或關鍵字之未結問題、已歸檔紀錄與相關待辦')
    ap.add_argument('target', help='檔案路徑或關鍵字，例如 index.html 或 實作規格書')
    ap.add_argument('--open', action='store_true', help='只列出尚未結案之問題與相關待辦，不列歸檔')
    ap.add_argument('--list', action='store_true', help='只列標題，不印條目內容')
    a = ap.parse_args()

    root = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True).stdout.strip() \
        or os.getcwd()
    print('查詢目標：' + a.target)

    issues_file = os.path.join(root, PATH)
    cur = [x for x in entries(read(issues_file)) if match_target(x[2], a.target)] if os.path.exists(issues_file) else []
    print('\n== docs/issues.md 中符合條目：%d 筆（open %d） ==' % (len(cur), sum(1 for x in cur if x[1] == 'open')))
    for _, _, _, blk in cur:
        print('\n' + (blk.split('\n', 1)[0] if a.list else blk))

    page_ids = {x[0] for x in cur}

    if not a.open:
        closed_base = os.path.join(root, CLOSED_DIR)
        archived = []
        for dp, _, files in os.walk(closed_base):
            for f in sorted(files):
                if f.endswith('.md'):
                    for x in entries(read(os.path.join(dp, f))):
                        if match_target(x[2], a.target):
                            archived.append(x)
        page_ids.update(x[0] for x in archived)
        print('\n== docs/issues/closed/ 中已歸檔紀錄：%d 筆 ==' % len(archived))
        for _, _, _, blk in archived:
            print('\n' + (blk.split('\n', 1)[0] if a.list else blk))

    todos = related_todos(root, a.target, page_ids)
    print('\n== docs/todo.md 中相關待辦：%d 筆 ==' % len(todos))
    for blk in todos:
        print('\n' + (blk.split('\n', 1)[0] if a.list else blk))


if __name__ == '__main__':
    main()
