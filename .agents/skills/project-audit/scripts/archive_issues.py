#!/usr/bin/env python3
"""archive_issues.py: 把 docs/issues.md 中已結案（fixed / wontfix）的條目搬到 docs/issues/closed/。

歸檔檔依條目標題第三段（相對於倉庫根目錄之檔案）對應：
    index.html 之條目 -> docs/issues/closed/index.html.md
    docs/dev/實作規格書.md 之條目 -> docs/issues/closed/docs/dev/實作規格書.md

條目內容原封不動，僅將相對連結換算為歸檔檔所在位置。歸檔檔只追加。

用法（於倉庫任意位置執行）：
    python3 .agents/skills/project-audit/scripts/archive_issues.py                 # 預覽
    python3 .agents/skills/project-audit/scripts/archive_issues.py --apply --agent "Claude Code by Anthropic"
    python3 .agents/skills/project-audit/scripts/archive_issues.py --apply --no-commit
"""
import argparse
import os
import posixpath
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GUARDIAN = os.path.normpath(os.path.join(HERE, '..', '..', 'git-sync-guardian', 'scripts'))
sys.path.insert(0, GUARDIAN)
from stage_issues import blocks, rebuild, CLOSED_STATES, CLOSED_DIR, PATH  # noqa: E402

HEAD_RE = re.compile(r'^### (FP-\d{3,}) \| (\w+) \| ([^|]+?) \|')
LINK_RE = re.compile(r'\]\(([^)\s]+)((?:\s+"[^"]*")?)\)')


def run(args, cwd, check=True):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.stderr.write(r.stderr)
        sys.exit(1)
    return r


def archive_rel(target):
    t = target.replace('\\', '/').lstrip('./')
    if not t.endswith('.md'):
        t = t + '.md'
    return CLOSED_DIR + '/' + t


def rewrite_links(text, archive_path):
    """把相對於 docs/ 的連結改為相對於歸檔檔所在資料夾。"""
    new_dir = posixpath.dirname(archive_path)

    def sub(m):
        target, title = m.group(1), m.group(2)
        if re.match(r'^[a-z][a-z0-9+.-]*:', target, re.I) or target.startswith('#') or target.startswith('/'):
            return m.group(0)
        path, sep, frag = target.partition('#')
        if not path:
            return m.group(0)
        full = posixpath.normpath(posixpath.join('docs', path))
        return '](%s%s%s%s)' % (posixpath.relpath(full, new_dir), sep, frag, title)

    return LINK_RE.sub(sub, text)


def header(target, archive_path):
    d = posixpath.dirname(archive_path)
    target_rel = posixpath.relpath(target.lstrip('./'), d)
    issues = posixpath.relpath(PATH, d)
    return ('# 已結案問題：%s\n\n'
            '> 本檔收錄 [%s](%s) 已結案（`fixed` / `wontfix`）之問題條目，由 `archive_issues.py` 自 '
            '[docs/issues.md](%s) 搬入；條目內容原封不動，僅相對連結已換算為本檔位置。本檔只追加，不修改已歸檔條目；'
            '同一處再出問題時於 docs/issues.md 開新編號並加「關聯」行。\n'
            % (target, target, target_rel, issues))


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass
    ap = argparse.ArgumentParser(description='把已結案問題條目搬到 docs/issues/closed/')
    ap.add_argument('--apply', action='store_true', help='實際寫檔（預設只預覽）')
    ap.add_argument('--no-commit', action='store_true', help='與 --apply 併用：只寫檔，不提交')
    ap.add_argument('--agent', default='', help='執行代理名稱（--apply 且提交時必填）')
    a = ap.parse_args()
    if a.apply and not a.no_commit and not a.agent:
        ap.error('--apply 會立即提交，須以 --agent 指定執行代理名稱')

    root = run(['git', 'rev-parse', '--show-toplevel'], os.getcwd()).stdout.strip()
    branch = run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], root).stdout.strip()
    if not branch or branch == 'HEAD':
        sys.exit('錯誤：目前為 detached HEAD；請先切換到具名分支再歸檔。')

    if run(['git', 'fetch', 'origin', '--quiet'], root, check=False).returncode != 0:
        sys.exit('錯誤：git fetch 失敗，未做任何變更。')
    head = run(['git', 'rev-parse', 'HEAD'], root).stdout.strip()
    remote_ref = 'origin/' + branch
    if run(['git', 'rev-parse', '--verify', remote_ref], root, check=False).returncode == 0:
        remote = run(['git', 'rev-parse', remote_ref], root).stdout.strip()
        if head != remote:
            sys.exit('錯誤：本機與 %s 不一致；先執行 sync.py 或推送，再歸檔。' % remote_ref)
    if run(['git', 'diff', '--cached', '--name-only'], root).stdout.strip():
        sys.exit('錯誤：暫存區已有檔案（可能屬於他人），未做任何變更。')

    dirty = run(['git', 'status', '--porcelain', '--', PATH, 'docs/issues'], root).stdout.strip()
    if dirty:
        sys.exit('拒絕執行：下列檔案有尚未提交的修改，請待提交後再歸檔：\n' + dirty)

    head_show = run(['git', 'show', 'HEAD:' + PATH], root, check=False)
    if head_show.returncode != 0:
        print('docs/issues.md 尚未提交過，沒有可歸檔之條目。')
        return
    text = head_show.stdout.replace('\r\n', '\n')
    b = blocks(text)
    moves = {}
    for iid, (s, e) in sorted(b.items(), key=lambda kv: int(kv[0][3:])):
        block = text[s:e].strip('\n')
        m = HEAD_RE.match(block)
        if not m:
            sys.exit('錯誤：%s 標題格式不符。' % iid)
        if m.group(2) in CLOSED_STATES:
            target = m.group(3).strip()
            moves.setdefault(target, []).append((iid, block))

    if not moves:
        print('沒有可歸檔的已結案條目。')
        return

    total = sum(len(v) for v in moves.values())
    print('%s %d 筆已結案條目（%d 個目標檔案）：' % ('搬移' if a.apply else '可搬移', total, len(moves)))
    new_files = []
    for target, items in sorted(moves.items()):
        ap_path = archive_rel(target)
        new_files.append(ap_path)
        print('  %s <- %s' % (ap_path, '、'.join(iid for iid, _ in items)))

    if not a.apply:
        print('\n以上為預覽，加 --apply --agent "<代理名稱>" 才會實際搬移並提交。')
        return

    for target, items in sorted(moves.items()):
        ap_path = archive_rel(target)
        full = os.path.join(root, ap_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        existing = ''
        if os.path.exists(full):
            with open(full, encoding='utf-8') as fh:
                existing = fh.read().replace('\r\n', '\n').rstrip('\n')
        chunks = [rewrite_links(blk, ap_path) for _, blk in items]
        out = (existing if existing else header(target, ap_path).rstrip('\n')) + '\n\n' + '\n\n'.join(chunks) + '\n'
        with open(full, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(out)

    all_ids = [iid for items in moves.values() for iid, _ in items]
    with open(os.path.join(root, PATH), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(rebuild(text, all_ids))

    if a.no_commit:
        print('已搬移至歸檔檔並更新 %s（--no-commit，請立即自行提交）。' % PATH)
        return

    msg = 'chore(issues): archive %d closed issue(s)' % total
    cmd = [sys.executable, os.path.join(GUARDIAN, 'safe_commit_push.py'),
           msg, '--agent', a.agent, '--issue', 'ARCHIVED', '--', PATH, *sorted(set(new_files))]
    rc = subprocess.run(cmd, cwd=root).returncode
    if rc != 0:
        sys.exit(rc)


if __name__ == '__main__':
    main()
