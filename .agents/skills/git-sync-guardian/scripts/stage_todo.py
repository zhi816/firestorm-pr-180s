#!/usr/bin/env python3
"""stage_todo.py: 只把指定編號的待辦條目變更加入 Git 暫存區（docs/todo.md）；另可查下一個可用編號。

docs/todo.md 與日誌、問題清單一樣由多個 AI 共用，本腳本以「HEAD 版待辦清單＋指定條目的工作目錄版本」
組出要提交的內容，寫入暫存區。待辦完成或放棄時直接刪除條目（AGENTS.md 第六章第 5 節），
故指定的編號若在 HEAD 中存在、工作目錄中已刪除，即暫存其刪除。

用法（於倉庫任意位置執行）：
    python3 .agents/skills/git-sync-guardian/scripts/stage_todo.py --next-id
    python3 .agents/skills/git-sync-guardian/scripts/stage_todo.py TD-003 TD-004
    python3 .agents/skills/git-sync-guardian/scripts/stage_todo.py TD-002 --dry-run
"""
import argparse
import os
import re
import subprocess
import sys

PATH = 'docs/todo.md'
LOG = 'docs/log.md'
ITEM = re.compile(r'(?m)^### (TD-\d{3,}) ')
BOUNDARY = re.compile(r'(?m)^##+ ')
ANY_ID = re.compile(r'TD-(\d{3,})')
ID_FORMAT = re.compile(r'TD-\d{3,}')


def git(*args, data=None):
    r = subprocess.run(['git', *args], input=data, capture_output=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr.decode('utf-8', 'replace'))
        sys.exit(1)
    return r.stdout


def head_text(root, path):
    r = subprocess.run(['git', '-C', root, 'show', 'HEAD:' + path], capture_output=True)
    return r.stdout.decode('utf-8').replace('\r\n', '\n') if r.returncode == 0 else None


def work_text(root, path):
    p = os.path.join(root, path)
    if not os.path.exists(p):
        return None
    with open(p, 'rb') as f:
        return f.read().decode('utf-8').replace('\r\n', '\n')


def blocks(text):
    out = {}
    for m in ITEM.finditer(text):
        nxt = BOUNDARY.search(text, m.end())
        out[m.group(1)] = (m.start(), nxt.start() if nxt else len(text))
    return out


def norm(s):
    return s.replace('\r\n', '\n').strip()


def next_id(root):
    nums = []
    for t in (head_text(root, PATH), work_text(root, PATH), work_text(root, LOG)):
        if t:
            nums += [int(n) for n in ANY_ID.findall(t)]
    return 'TD-%03d' % (max(nums, default=0) + 1)


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass
    ap = argparse.ArgumentParser(description='只暫存 docs/todo.md 中指定編號的條目變更（含刪除）')
    ap.add_argument('ids', nargs='*', help='要提交的待辦編號，例如 TD-003')
    ap.add_argument('--next-id', action='store_true', help='只輸出下一個可用編號')
    ap.add_argument('--dry-run', action='store_true', help='只列出結果，不寫入暫存區')
    a = ap.parse_args()

    root = git('rev-parse', '--show-toplevel').decode().strip()
    if a.next_id:
        print(next_id(root))
        return
    if not a.ids:
        sys.stderr.write('錯誤：請列出要提交的待辦編號，例如 TD-003。\n')
        sys.exit(1)
    bad = [k for k in a.ids if not ID_FORMAT.fullmatch(k)]
    if bad:
        sys.stderr.write('錯誤：編號格式應為 TD-NNN：%s\n' % '、'.join(bad))
        sys.exit(1)

    base = head_text(root, PATH)
    work = work_text(root, PATH)
    if work is None:
        sys.stderr.write('錯誤：工作目錄中沒有 %s（待辦清單不得整檔刪除）。\n' % PATH)
        sys.exit(1)
    wb = blocks(work)
    wanted = set(a.ids)

    if base is None:
        missing = [k for k in a.ids if k not in wb]
        if missing:
            sys.stderr.write('錯誤：工作目錄中找不到指定的待辦編號：%s\n' % '、'.join(missing))
            sys.exit(1)
        staged = work
        others = [k for k in wb if k not in wanted]
        if others:
            sys.stderr.write('錯誤：%s 尚未提交過，首次提交會整檔帶入未指定的條目：%s\n'
                             % (PATH, '、'.join(others)))
            sys.exit(1)
        print('%s 尚未提交過，整檔暫存（首次建立）。' % PATH)
        for k in a.ids:
            print('暫存（新條目）：' + k)
    else:
        bb = blocks(base)
        missing = [k for k in a.ids if k not in bb and k not in wb]
        if missing:
            sys.stderr.write('錯誤：HEAD 與工作目錄中都找不到指定的待辦編號：%s\n' % '、'.join(missing))
            sys.exit(1)
        staged = base
        for k in sorted((k for k in wanted if k in bb), key=lambda k: bb[k][0], reverse=True):
            s, e = bb[k]
            staged = staged[:s] + (work[slice(*wb[k])] if k in wb else '') + staged[e:]
        order = sorted(wb, key=lambda k: wb[k][0])
        for k in [k for k in order if k in wanted and k not in bb]:
            cur = blocks(staged)
            prev = [p for p in order[:order.index(k)] if p in cur]
            pos = cur[prev[-1]][1] if prev else len(staged)
            if pos == len(staged) and not staged.endswith('\n\n'):
                staged += '\n' if staged.endswith('\n') else '\n\n'
                pos = len(staged)
            staged = staged[:pos] + work[slice(*wb[k])] + staged[pos:]
        tail = len(work) - len(work.rstrip('\n'))
        staged = staged.rstrip('\n') + '\n' * tail

        others = sorted(
            {k for k in wb if k not in wanted and (k not in bb or norm(work[slice(*wb[k])]) != norm(base[slice(*bb[k])]))}
            | {k for k in bb if k not in wanted and k not in wb})
        for k in a.ids:
            print(('暫存（新條目）：' if k not in bb else '暫存（刪除）：' if k not in wb else '暫存：') + k)
        for k in others:
            print('略過（未指定，留在工作目錄）：' + k)

    if a.dry_run:
        print('（dry-run）未寫入暫存區。')
        return
    sha = git('-C', root, 'hash-object', '-w', '--stdin', data=staged.encode('utf-8')).decode().strip()
    git('-C', root, 'update-index', '--add', '--cacheinfo', '100644,%s,%s' % (sha, PATH))
    print('已暫存 %d 筆；工作目錄中的 %s 未變更。' % (len(a.ids), PATH))


if __name__ == '__main__':
    main()
