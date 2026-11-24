#!/usr/bin/env python3
"""sync.py: Safe pre-flight synchronization for firestorm-pr-180s.

Fetches origin and safely merges origin/main (or origin/<current-branch> when on a
feature branch with an upstream). Automatically resolves append-only conflicts in
docs/log.md via merge_log.py. Uses --autostash so other agents' uncommitted edits
remain unstaged in the working tree.
"""
import os
import subprocess
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..', '..'))


def run_git(cwd, *args):
    return subprocess.run(
        ['git', '-C', cwd, *args],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
    )


def git_out(cwd, *args, default=''):
    r = run_git(cwd, *args)
    return r.stdout.strip() if r.returncode == 0 else default


def only_log_conflict(cwd):
    unmerged = git_out(cwd, 'diff', '--name-only', '--diff-filter=U')
    return unmerged == 'docs/log.md'


def has_unmerged(cwd):
    return bool(git_out(cwd, 'diff', '--name-only', '--diff-filter=U'))


def top_stash_is_autostash(cwd):
    stash_list = git_out(cwd, 'stash', 'list')
    first_line = stash_list.splitlines()[0] if stash_list else ''
    return 'autostash' in first_line


def run_merge_log(cwd):
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    r = subprocess.run(
        [sys.executable, os.path.join(SCRIPT_DIR, 'merge_log.py')],
        cwd=cwd,
        env=env,
    )
    return r.returncode == 0


def merge_remote(cwd, target_ref, ff_only=False):
    args = ['merge']
    if ff_only:
        args.append('--ff-only')
    args.extend(['--autostash', '--no-edit', target_ref])

    res = subprocess.run(['git', '-C', cwd, *args])
    if res.returncode != 0:
        if only_log_conflict(cwd):
            if not run_merge_log(cwd):
                return False
            if run_git(cwd, 'add', 'docs/log.md').returncode != 0:
                return False
            commit_res = run_git(cwd, 'commit', '-q', '--no-edit')
            if commit_res.returncode != 0:
                if commit_res.stderr:
                    sys.stderr.write(commit_res.stderr)
                print('    ERROR: 日誌衝突已整理，但合併提交失敗；請保留現況並人工處理。', file=sys.stderr)
                return False
        else:
            return False

    if has_unmerged(cwd):
        if only_log_conflict(cwd) and top_stash_is_autostash(cwd):
            if not run_merge_log(cwd):
                return False
            if run_git(cwd, 'reset', '-q').returncode != 0:
                print('    ERROR: 無法清除合併索引中的暫存狀態。', file=sys.stderr)
                return False
            if run_git(cwd, 'stash', 'drop', '-q').returncode != 0:
                print('    ERROR: 已合併日誌，但無法刪除 autostash；請檢查 git stash list。', file=sys.stderr)
                return False
        else:
            print('    ERROR: 放回未提交修改時發生衝突，修改仍保存在 git stash 中，請人工處理。', file=sys.stderr)
            return False

    if run_git(cwd, 'reset', '-q').returncode != 0:
        print('    ERROR: 合流後無法清除暫存狀態。', file=sys.stderr)
        return False
    return True


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print('==================================================')
    print('Starting Sync Operation (firestorm-pr-180s)')
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print('==================================================')

    if not os.path.isdir(os.path.join(REPO_ROOT, '.git')):
        print(f'ERROR: Git directory not found at {REPO_ROOT}.', file=sys.stderr)
        sys.exit(1)

    branch = git_out(REPO_ROOT, 'branch', '--show-current')
    if not branch:
        print('ERROR: Detached HEAD state; switch to main or a named branch before syncing.', file=sys.stderr)
        sys.exit(1)

    fetch_res = subprocess.run(['git', '-C', REPO_ROOT, 'fetch', 'origin', '--prune', '--tags'])
    if fetch_res.returncode != 0:
        print('ERROR: git fetch origin failed (check network or .git write permissions).', file=sys.stderr)
        sys.exit(1)

    target_ref = 'origin/main'
    if branch != 'main' and run_git(REPO_ROOT, 'rev-parse', '--verify', f'origin/{branch}').returncode == 0:
        target_ref = f'origin/{branch}'

    ahead = int(git_out(REPO_ROOT, 'rev-list', '--count', f'{target_ref}..HEAD', default='0') or '0')
    behind = int(git_out(REPO_ROOT, 'rev-list', '--count', f'HEAD..{target_ref}', default='0') or '0')

    print(f'>>> Branch: {branch} vs {target_ref} -> Ahead: {ahead}, Behind: {behind}')

    if behind == 0 and ahead == 0:
        print(f'    Status: Already up to date with {target_ref}.')
    elif behind > 0 and ahead == 0:
        print(f'    Status: Fast-forward pull available. Pulling {behind} incoming commit(s)...')
        if not merge_remote(REPO_ROOT, target_ref, ff_only=True):
            sys.exit(1)
        print('    Successfully updated to latest remote commit.')
    elif behind > 0 and ahead > 0:
        print(f'    Status: Divergent branches detected (Local ahead by {ahead}, Remote ahead by {behind}).')
        print('    Attempting automatic merge...')
        if merge_remote(REPO_ROOT, target_ref, ff_only=False):
            print('    Merge completed successfully.')
        else:
            print('    ERROR: Merge conflict detected. Resolve manually (check docs/log.md) and commit.', file=sys.stderr)
            sys.exit(1)
    else:
        print(f'    Status: Local branch is ahead by {ahead} commit(s). Ready for push.')

    print('==================================================')


if __name__ == '__main__':
    main()
