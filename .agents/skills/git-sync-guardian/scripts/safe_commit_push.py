#!/usr/bin/env python3
"""safe_commit_push.py: Atomic Commit-and-Push Guardian for firestorm-pr-180s.

Rule 1: Whenever changes are committed, they MUST be pushed immediately.
Rule 4: Commit ONLY your own changes. Never run `git add -A` / `git add .`; every path
        must be listed explicitly, and docs/log.md, docs/issues.md, docs/todo.md are
        staged entry by entry.
Supports both `main` and feature branches (e.g., `claude/...` created by mobile/cloud agents).
Zero emoji constraint strictly enforced.
"""
import ntpath
import os
import subprocess
import sys
import time
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..', '..'))


def usage():
    prog = os.path.basename(sys.argv[0])
    print(f'Usage: python3 .agents/skills/git-sync-guardian/scripts/{prog} "<commit_message>" [main] --agent "<執行代理名稱>" [--branch <branch>] [--log-heading "<exact heading>"] [--issue FP-NNN ...] [--todo TD-NNN ...] [--allow-stale-log] -- <path> [<path> ...]')
    print('')
    print('  --agent          執行代理名稱的一部分（例如 "Claude Code"、"Codex"、"Antigravity"），')
    print('                   用來挑出 docs/log.md 中自己寫的條目。列出 docs/log.md 時為必填。')
    print('  --branch         預期提交與推送的分支名稱（預設為目前分支，不可為 detached HEAD）。')
    print('  --log-heading    只提交指定的新日誌標題；可重複使用。')
    print('  --issue          提交 docs/issues.md 時必填：只提交這些編號的條目（可重複）。')
    print('  --todo           提交 docs/todo.md 時必填：只提交這些編號的條目新增、修改或刪除（可重複）。')
    print('  --allow-stale-log  允許日誌標題時間早於現在 60 分鐘以上（僅限推送失敗後重試）。')
    print("  -- <path>        只會提交這些路徑（相對於倉庫根目錄）。不接受 '.'、'-A' 或資料夾。")
    print('')
    print(f'Example: python3 .agents/skills/git-sync-guardian/scripts/{prog} "docs(design): update DESIGN.md" --agent "Antigravity" -- DESIGN.md docs/log.md')
    sys.exit(1)


def run_git(cwd, *args, check=False):
    for attempt in range(5):
        r = subprocess.run(
            ['git', '-C', cwd, *args],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
        )
        if r.returncode == 0 or 'index.lock' not in (r.stderr or ''):
            break
        time.sleep(0.5 * (attempt + 1))
    if check and r.returncode != 0:
        if r.stderr:
            sys.stderr.write(r.stderr)
        sys.exit(r.returncode)
    return r


def git_out(cwd, *args, default=''):
    r = run_git(cwd, *args)
    return r.stdout.strip() if r.returncode == 0 else default


def run_helper(cwd, script_name, args):
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    r = subprocess.run(
        [sys.executable, os.path.join(SCRIPT_DIR, script_name), *args],
        cwd=cwd,
        env=env,
    )
    return r.returncode == 0


def reset_paths(cwd, paths):
    literal_paths = [f':(literal){p.replace(chr(92), "/")}' for p in paths]
    run_git(cwd, 'reset', '-q', '--', *literal_paths)


def validate_paths(repo_path, paths):
    normalized = []
    for path in paths:
        norm_path = path.replace('\\', '/')
        parts = norm_path.split('/')
        if (
            not norm_path
            or '\n' in path
            or '\r' in path
            or norm_path in ('.', './', '-A', '--all', '*')
            or os.path.isabs(path)
            or ntpath.isabs(path)
            or bool(ntpath.splitdrive(path)[0])
            or norm_path.startswith(':(')
            or any(part in ('.', '..') for part in parts)
        ):
            print(f"ERROR: 不接受路徑 '{path}'；請列出倉庫內單一檔案的相對路徑。")
            return None
        disk_path = os.path.join(repo_path, *parts)
        if os.path.isdir(disk_path):
            print(f"ERROR: '{path}' 是資料夾；為避免遞迴暫存他人檔案，請逐一列出檔案。")
            return None
        indexed = run_git(repo_path, 'ls-files', '-z', '--', f':(literal){norm_path}')
        if indexed.returncode != 0:
            if indexed.stderr:
                sys.stderr.write(indexed.stderr)
            print(f"ERROR: 無法確認 '{path}' 是否為單一檔案路徑；為安全起見已中止。")
            return None
        indexed_paths = [item for item in indexed.stdout.split('\0') if item]
        if any(item != norm_path for item in indexed_paths):
            print(f"ERROR: '{path}' 對應到索引中的資料夾內容；請逐一列出檔案。")
            return None
        normalized.append(norm_path)
    return normalized


def only_log_conflict(cwd):
    return git_out(cwd, 'diff', '--name-only', '--diff-filter=U') == 'docs/log.md'


def has_unmerged(cwd):
    return bool(git_out(cwd, 'diff', '--name-only', '--diff-filter=U'))


def top_stash_is_autostash(cwd):
    stash_list = git_out(cwd, 'stash', 'list')
    first_line = stash_list.splitlines()[0] if stash_list else ''
    return 'autostash' in first_line


def parse_cli(argv):
    if len(argv) < 3:
        usage()
    commit_msg = argv[0]
    rest = argv[1:]
    if rest and rest[0] == 'main':
        rest = rest[1:]

    agent = ''
    expected_branch = ''
    log_headings = []
    allow_stale = False
    issues = []
    todos = []

    idx = 0
    while idx < len(rest) and rest[idx] != '--':
        opt = rest[idx]
        if opt == '--agent' and idx + 1 < len(rest):
            agent = rest[idx + 1]
            idx += 2
        elif opt == '--branch' and idx + 1 < len(rest):
            expected_branch = rest[idx + 1]
            idx += 2
        elif opt == '--log-heading' and idx + 1 < len(rest):
            log_headings.append(rest[idx + 1])
            idx += 2
        elif opt == '--allow-stale-log':
            allow_stale = True
            idx += 1
        elif opt == '--issue' and idx + 1 < len(rest):
            issues.append(rest[idx + 1])
            idx += 2
        elif opt == '--todo' and idx + 1 < len(rest):
            todos.append(rest[idx + 1])
            idx += 2
        else:
            print(f"Unknown option '{opt}'.")
            usage()

    if idx >= len(rest) or rest[idx] != '--':
        usage()
    paths = rest[idx + 1:]
    if not paths:
        print('ERROR: 未列出任何要提交的檔案。')
        usage()

    return commit_msg, expected_branch, agent, log_headings, allow_stale, issues, todos, paths


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', line_buffering=True)
        except Exception:
            pass

    commit_msg, expected_branch, agent, log_headings, allow_stale, issues, todos, paths = parse_cli(sys.argv[1:])

    if not os.path.isdir(os.path.join(REPO_ROOT, '.git')):
        print(f'ERROR: Git directory not found at {REPO_ROOT}.')
        sys.exit(1)

    branch = git_out(REPO_ROOT, 'branch', '--show-current', default='')
    if not branch:
        print('ERROR: 目前為 detached HEAD，請切換到 main 或功能分支後再提交。')
        sys.exit(1)
    if expected_branch and branch != expected_branch:
        print(f"ERROR: 預期分支為 '{expected_branch}'，但目前在 '{branch}'。")
        sys.exit(1)

    print('==================================================')
    print('Atomic Commit-and-Push Guardian (firestorm-pr-180s)')
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f'Branch: {branch}')
    print(f"Agent: {agent or '（未指定）'}")
    print(f'Message: {commit_msg}')
    print('==================================================')

    prestaged = git_out(REPO_ROOT, 'diff', '--cached', '--name-only')
    if prestaged:
        print('ERROR: 暫存區已有檔案（可能是其他代理暫存的），為避免誤提交，已中止：')
        for line in prestaged.splitlines():
            print(f'    {line}')
        sys.exit(1)

    paths = validate_paths(REPO_ROOT, paths)
    if paths is None:
        sys.exit(1)

    print('    提交前先向 origin 取得最新狀態...')
    run_git(REPO_ROOT, 'fetch', 'origin', '--prune', '--quiet', check=True)

    for p in paths:
        norm_p = p.replace('\\', '/')
        if norm_p == 'docs/log.md':
            if not agent:
                reset_paths(REPO_ROOT, paths)
                print('ERROR: 提交 docs/log.md 時必須以 --agent 指定執行代理名稱。')
                sys.exit(1)
            stage_args = [agent]
            for h in log_headings:
                stage_args.extend(['--heading', h])
            if allow_stale:
                stage_args.append('--allow-stale')
            if not run_helper(REPO_ROOT, 'stage_log.py', stage_args):
                reset_paths(REPO_ROOT, paths)
                print('ERROR: 日誌暫存失敗（見上方訊息），已還原本次暫存，未提交任何內容。')
                sys.exit(1)
        elif norm_p == 'docs/issues.md':
            if not issues:
                reset_paths(REPO_ROOT, paths)
                print('ERROR: 提交 docs/issues.md 時必須以 --issue FP-NNN 列出自己修改的問題編號（可重複），已還原本次暫存。')
                sys.exit(1)
            if not run_helper(REPO_ROOT, 'stage_issues.py', issues):
                reset_paths(REPO_ROOT, paths)
                print('ERROR: 問題清單暫存失敗（見上方訊息），已還原本次暫存，未提交任何內容。')
                sys.exit(1)
        elif norm_p == 'docs/todo.md':
            if not todos:
                reset_paths(REPO_ROOT, paths)
                print('ERROR: 提交 docs/todo.md 時必須以 --todo TD-NNN 列出自己新增、修改或刪除的待辦編號（可重複），已還原本次暫存。')
                sys.exit(1)
            if not run_helper(REPO_ROOT, 'stage_todo.py', todos):
                reset_paths(REPO_ROOT, paths)
                print('ERROR: 待辦清單暫存失敗（見上方訊息），已還原本次暫存，未提交任何內容。')
                sys.exit(1)
        else:
            r = run_git(REPO_ROOT, 'add', '--', f':(literal){norm_p}')
            if r.returncode != 0:
                reset_paths(REPO_ROOT, paths)
                if r.stderr:
                    sys.stderr.write(r.stderr)
                sys.exit(r.returncode)

    print('    即將提交的檔案：')
    stat_out = git_out(REPO_ROOT, 'diff', '--cached', '--stat')
    if stat_out:
        for line in stat_out.splitlines():
            print(f'    {line}')

    if run_git(REPO_ROOT, 'diff', '--cached', '--quiet').returncode == 0:
        print('    暫存區沒有變更，不建立新提交。')
    else:
        commit_res = run_git(REPO_ROOT, 'commit', '-q', '-m', commit_msg)
        if commit_res.returncode != 0:
            for out in (commit_res.stdout, commit_res.stderr):
                if out:
                    sys.stderr.write(out)
            reset_paths(REPO_ROOT, paths)
            print('ERROR: 建立提交失敗，已還原本次暫存，未提交任何內容。')
            sys.exit(1)
        print(f"    已建立提交：{git_out(REPO_ROOT, 'log', '--oneline', '-1')}")

    remote_ref = f'origin/{branch}'
    has_remote_branch = run_git(REPO_ROOT, 'rev-parse', '--verify', remote_ref).returncode == 0
    if has_remote_branch:
        behind = int(git_out(REPO_ROOT, 'rev-list', '--count', f'HEAD..{remote_ref}', default='0') or '0')
        if behind > 0:
            print(f'    遠端 {remote_ref} 領先 {behind} 個提交，進行三方合併...')
            merge_res = subprocess.run(['git', '-C', REPO_ROOT, 'merge', '--autostash', '--no-edit', remote_ref])
            if merge_res.returncode != 0:
                if only_log_conflict(REPO_ROOT):
                    print('    只有 docs/log.md 衝突，依 append-only 原則自動合併...')
                    if not run_helper(REPO_ROOT, 'merge_log.py', []):
                        sys.exit(1)
                    run_git(REPO_ROOT, 'add', 'docs/log.md', check=True)
                    commit_res = run_git(REPO_ROOT, 'commit', '-q', '--no-edit')
                    if commit_res.returncode != 0:
                        if commit_res.stderr:
                            sys.stderr.write(commit_res.stderr)
                        print('ERROR: 日誌衝突已整理，但合併提交失敗；請人工處理。')
                        sys.exit(commit_res.returncode)
                else:
                    print(f'ERROR: 合併衝突。請人工排解後再執行 git push origin {branch}。')
                    sys.exit(1)

            if has_unmerged(REPO_ROOT):
                if only_log_conflict(REPO_ROOT) and top_stash_is_autostash(REPO_ROOT):
                    print('    放回未提交修改時 docs/log.md 衝突，自動併入...')
                    if not run_helper(REPO_ROOT, 'merge_log.py', []):
                        sys.exit(1)
                    run_git(REPO_ROOT, 'reset', '-q')
                    run_git(REPO_ROOT, 'stash', 'drop', '-q')
                else:
                    print('ERROR: 放回未提交修改時發生衝突，修改仍在 git stash 中；請人工處理。')
                    sys.exit(1)

            run_git(REPO_ROOT, 'reset', '-q')

    print(f'    推送到 origin {branch}...')
    push_args = ['git', '-C', REPO_ROOT, 'push']
    if not has_remote_branch:
        push_args.append('-u')
    push_args.extend(['origin', branch])
    push_res = subprocess.run(push_args)
    if push_res.returncode != 0:
        sys.exit(push_res.returncode)

    run_git(REPO_ROOT, 'fetch', 'origin', branch, '--quiet', check=True)
    ahead_after = int(git_out(REPO_ROOT, 'rev-list', '--count', f'origin/{branch}..HEAD', default='0') or '0')
    if ahead_after == 0:
        print(f'    Success: Fully synchronized with origin/{branch} (Ahead: 0).')
    else:
        print(f'    ERROR: Push failed or local still ahead by {ahead_after} commit(s).')
        sys.exit(1)

    remaining = git_out(REPO_ROOT, 'status', '--porcelain')
    if remaining:
        print('    工作目錄仍有未提交的修改（可能屬於其他代理或暫存檔）：')
        for line in remaining.splitlines():
            print(f'    {line}')
    print('==================================================')


if __name__ == '__main__':
    main()
