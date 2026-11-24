#!/usr/bin/env python3
"""stage_issues.py: 只把指定編號的問題條目加入 Git 暫存區（docs/issues.md）；另可查下一個可用編號。

docs/issues.md 由多個 AI 共用，工作目錄常同時含有別的代理尚未提交的狀態變更。
本腳本以「HEAD 版問題清單＋指定條目的工作目錄版本」組出要提交的內容，寫入暫存區。
若本檔尚未提交過（HEAD 中不存在），允許僅在指定所有條目時整檔暫存。

條目範圍：從 `### FP-NNN | ...` 標題行起，到下一個 `### ` 或 `## ` 標題行之前為止。

用法（於倉庫任意位置執行）：
    python3 .agents/skills/git-sync-guardian/scripts/stage_issues.py --next-id
    python3 .agents/skills/git-sync-guardian/scripts/stage_issues.py FP-001 FP-002
    python3 .agents/skills/git-sync-guardian/scripts/stage_issues.py FP-001 --dry-run
    python3 .agents/skills/git-sync-guardian/scripts/stage_issues.py ARCHIVED
"""
import argparse
import os
import re
import subprocess
import sys

PATH = 'docs/issues.md'
CLOSED_DIR = 'docs/issues/closed'
CLOSED_STATES = {'fixed', 'wontfix'}
ISSUE = re.compile(r'(?m)^### (FP-\d{3,}) ')
HEAD_LINE = re.compile(r'(?m)^### (FP-\d{3,}) \| (\w+) \| ')
BOUNDARY = re.compile(r'(?m)^##+ ')


def git(*args, data=None):
    r = subprocess.run(['git', *args], input=data, capture_output=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr.decode('utf-8', 'replace'))
        sys.exit(1)
    return r.stdout


def head_text(root, path):
    r = subprocess.run(['git', '-C', root, 'show', 'HEAD:' + path], capture_output=True)
    return r.stdout.decode('utf-8').replace('\r\n', '\n') if r.returncode == 0 else None


def blocks(text):
    out = {}
    for m in ISSUE.finditer(text):
        nxt = BOUNDARY.search(text, m.end())
        out[m.group(1)] = (m.start(), nxt.start() if nxt else len(text))
    return out


def states(text):
    return {m.group(1): m.group(2) for m in HEAD_LINE.finditer(text)}


def preamble_end(text):
    m = BOUNDARY.search(text)
    return m.start() if m else len(text)


def rebuild(text, drop=()):
    drop = set(drop)
    head = text[:preamble_end(text)].rstrip('\n')
    b = blocks(text)
    kept = [text[s:e].strip('\n') for k, (s, e) in sorted(b.items(), key=lambda kv: kv[1][0]) if k not in drop]
    return head + '\n\n' + '\n\n'.join(kept) + '\n' if kept else head + '\n'


def norm(s):
    return s.replace('\r\n', '\n').strip()


def closed_ids(root):
    out = set()
    base = os.path.join(root, CLOSED_DIR)
    for dirpath, _, files in os.walk(base):
        for f in files:
            if f.endswith('.md'):
                with open(os.path.join(dirpath, f), encoding='utf-8') as fh:
                    out.update(ISSUE.findall(fh.read()))
    return out


def next_id(root):
    nums = []
    p = os.path.join(root, PATH)
    if os.path.exists(p):
        with open(p, encoding='utf-8') as fh:
            nums += [int(x[3:]) for x in ISSUE.findall(fh.read())]
    nums += [int(x[3:]) for x in closed_ids(root)]
    log = os.path.join(root, 'docs', 'log.md')
    if os.path.exists(log):
        with open(log, encoding='utf-8') as fh:
            nums += [int(n) for n in re.findall(r'FP-(\d{3,})', fh.read())]
    return 'FP-%03d' % (max(nums) + 1 if nums else 1)


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass
    ap = argparse.ArgumentParser(description='只暫存 docs/issues.md 中指定編號的條目')
    ap.add_argument('ids', nargs='*', help='要提交的問題編號（例如 FP-001）；PREAMBLE 代表檔頭前言；ARCHIVED 代表歸檔搬移')
    ap.add_argument('--dry-run', action='store_true', help='只列出結果，不寫入暫存區')
    ap.add_argument('--next-id', action='store_true', help='印出下一個可用編號（掃描 issues.md、歸檔與日誌）')
    a = ap.parse_args()

    root = git('rev-parse', '--show-toplevel').decode().strip()
    if a.next_id:
        print(next_id(root))
        return
    if not a.ids:
        ap.error('須指定編號、PREAMBLE、ARCHIVED，或使用 --next-id')

    base = head_text(root, PATH)
    work_path = os.path.join(root, PATH)
    if not os.path.exists(work_path):
        sys.stderr.write('錯誤：工作目錄中找不到 %s。\n' % PATH)
        sys.exit(1)
    work = open(work_path, 'rb').read().decode('utf-8').replace('\r\n', '\n')
    wb = blocks(work)

    want_preamble = 'PREAMBLE' in a.ids
    archived = 'ARCHIVED' in a.ids
    raw_ids = [k for k in a.ids if k not in ('PREAMBLE', 'ARCHIVED')]

    if base is None:
        if archived:
            sys.stderr.write('錯誤：%s 尚未提交過，不能使用 ARCHIVED。\n' % PATH)
            sys.exit(1)
        missing = [k for k in raw_ids if k not in wb]
        if missing:
            sys.stderr.write('錯誤：工作目錄中找不到指定的問題編號：%s\n' % '、'.join(missing))
            sys.exit(1)
        wanted = set(raw_ids)
        others = [k for k in wb if k not in wanted]
        if others:
            sys.stderr.write('錯誤：%s 尚未提交過，首次提交會整檔帶入未指定的條目：%s\n' % (PATH, '、'.join(others)))
            sys.exit(1)
        staged = work
        print('%s 尚未提交過，整檔暫存（首次建立）。' % PATH)
        for k in raw_ids:
            print('暫存（新條目）：' + k)
    else:
        bb = blocks(base)
        gone = [k for k in bb if k not in wb]

        if archived:
            if raw_ids:
                sys.stderr.write('錯誤：ARCHIVED 只能與 PREAMBLE 併用，其他條目請另行提交：%s\n' % '、'.join(raw_ids))
                sys.exit(1)
            if not gone:
                sys.stderr.write('錯誤：ARCHIVED 模式下工作目錄沒有被搬走的條目。\n')
                sys.exit(1)
            st = states(base)
            not_closed = [k for k in gone if st.get(k) not in CLOSED_STATES]
            if not_closed:
                sys.stderr.write('錯誤：以下條目在 HEAD 中不是 fixed / wontfix，不得歸檔：%s\n' % '、'.join(not_closed))
                sys.exit(1)
            have = closed_ids(root)
            missing = [k for k in gone if k not in have]
            if missing:
                sys.stderr.write('錯誤：以下條目已自 docs/issues.md 移除，卻不在 docs/issues/closed/ 中：%s\n' % '、'.join(missing))
                sys.exit(1)
            staged = rebuild(base, gone)
            print('暫存：歸檔搬移 %d 筆（%s 至 %s）' % (len(gone), gone[0], gone[-1]))
        else:
            if gone:
                shown = '、'.join(gone[:10]) + ('等 %d 筆' % len(gone) if len(gone) > 10 else '')
                sys.stderr.write('錯誤：工作目錄刪除了已提交的問題條目（問題清單不得刪除條目；歸檔請用 archive_issues.py）：%s\n' % shown)
                sys.exit(1)
            missing = [k for k in raw_ids if k not in wb]
            if missing:
                sys.stderr.write('錯誤：工作目錄中找不到指定的問題編號：%s\n' % '、'.join(missing))
                sys.exit(1)
            staged = base
            wanted = set(raw_ids)
            for k in sorted((k for k in wanted if k in bb), key=lambda k: bb[k][0], reverse=True):
                s, e = bb[k]
                ws, we = wb[k]
                staged = staged[:s] + work[ws:we] + staged[e:]
            order = sorted(wb, key=lambda k: wb[k][0])
            for k in [k for k in order if k in wanted and k not in bb]:
                ws, we = wb[k]
                chunk = work[ws:we]
                cur = blocks(staged)
                prev = [p for p in order[:order.index(k)] if p in cur]
                pos = cur[prev[-1]][1] if prev else len(staged)
                if pos == len(staged) and not staged.endswith('\n\n'):
                    staged += '\n' if staged.endswith('\n') else '\n\n'
                    pos = len(staged)
                staged = staged[:pos] + chunk + staged[pos:]
            for k in raw_ids:
                print(('暫存（新條目）：' if k not in bb else '暫存：') + k)

        if want_preamble:
            staged = work[:preamble_end(work)] + staged[preamble_end(staged):]
            print('暫存：檔頭說明（PREAMBLE）')

        wanted = set(raw_ids)
        others = [k for k in wb if k not in wanted and (k not in bb or norm(work[slice(*wb[k])]) != norm(base[slice(*bb[k])]))]
        for k in others:
            print('略過（未指定，留在工作目錄）：' + k)

    if a.dry_run:
        print('（dry-run）未寫入暫存區。')
        return
    sha = git('-C', root, 'hash-object', '-w', '--stdin', data=staged.encode('utf-8')).decode().strip()
    git('-C', root, 'update-index', '--add', '--cacheinfo', '100644,%s,%s' % (sha, PATH))
    print('已暫存 %s；工作目錄中的檔案未變更。' % PATH)


if __name__ == '__main__':
    main()
