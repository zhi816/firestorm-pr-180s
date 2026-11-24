#!/usr/bin/env python3
"""status.py: Repository status inspector for firestorm-pr-180s.

Cross-platform Python status check (macOS, Linux, Windows). Fetches origin so
ahead/behind counts are never silently stale; exits non-zero if fetch or local
Git queries fail (unless --allow-offline is passed for fetch failures).
Zero emoji constraint strictly enforced.
"""
import argparse
import os
import subprocess
import sys
from datetime import datetime

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))


def run_git(cwd, *args):
    return subprocess.run(
        ['git', '-C', cwd, *args],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
    )


def checked_git_out(cwd, description, *args, default='unknown'):
    r = run_git(cwd, *args)
    if r.returncode == 0:
        return r.stdout.strip(), True
    err_msg = (r.stderr or r.stdout or '').strip()
    print(f'    ERROR: {description} failed (exit code {r.returncode}).')
    if err_msg:
        for line in err_msg.splitlines():
            print(f'      {line}')
    return default, False


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass

    ap = argparse.ArgumentParser(description='Repository status inspector for firestorm-pr-180s')
    ap.add_argument('--allow-offline', action='store_true',
                    help='Return exit code 0 even if git fetch fails (warnings are still printed)')
    args = ap.parse_args()

    print('==================================================')
    print('Repository Status Check (firestorm-pr-180s)')
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print('==================================================')

    if not os.path.isdir(os.path.join(REPO_ROOT, '.git')):
        print(f'ERROR: Git repository not detected at {REPO_ROOT}', file=sys.stderr)
        sys.exit(1)

    inspection_ok = True
    branch, ok = checked_git_out(REPO_ROOT, 'current branch query', 'rev-parse', '--abbrev-ref', 'HEAD')
    inspection_ok = inspection_ok and ok

    fetch_ok = True
    fetch_res = run_git(REPO_ROOT, 'fetch', 'origin', '--prune', '--quiet')
    if fetch_res.returncode != 0:
        fetch_ok = False
        err_msg = (fetch_res.stderr or fetch_res.stdout or '').strip()
        print(f'    WARNING: git fetch origin failed (exit code {fetch_res.returncode})!')
        if err_msg:
            for line in err_msg.splitlines():
                print(f'      {line}')
        print('    WARNING: Remote commit and Ahead/Behind counts below are STALE (check network or .git write permissions).')

    target_ref = 'origin/main'
    if branch not in ('unknown', 'HEAD', 'main'):
        has_remote_branch = run_git(REPO_ROOT, 'rev-parse', '--verify', f'origin/{branch}').returncode == 0
        if has_remote_branch:
            target_ref = f'origin/{branch}'

    local_rev, ok = checked_git_out(REPO_ROOT, 'local commit query', 'rev-parse', 'HEAD')
    inspection_ok = inspection_ok and ok
    remote_rev, ok = checked_git_out(REPO_ROOT, f'{target_ref} query', 'rev-parse', target_ref)
    inspection_ok = inspection_ok and ok
    ahead, ok = checked_git_out(REPO_ROOT, 'ahead count query', 'rev-list', '--count', f'{target_ref}..HEAD')
    inspection_ok = inspection_ok and ok
    behind, ok = checked_git_out(REPO_ROOT, 'behind count query', 'rev-list', '--count', f'HEAD..{target_ref}')
    inspection_ok = inspection_ok and ok

    status_res = run_git(REPO_ROOT, 'status', '--porcelain')
    if status_res.returncode == 0:
        status_text = status_res.stdout.rstrip('\r\n')
    else:
        inspection_ok = False
        status_text = None
        err_msg = (status_res.stderr or status_res.stdout or '').strip()
        print(f'    ERROR: git status failed (exit code {status_res.returncode}); working-tree state is unknown.')
        if err_msg:
            for line in err_msg.splitlines():
                print(f'      {line}')

    print(f'[1] firestorm-pr-180s: {REPO_ROOT}')
    print(f'    Branch: {branch} (tracking {target_ref})')
    print(f'    Local commit:  {local_rev}')
    print(f'    Remote commit: {remote_rev}' + ('' if fetch_ok else ' (STALE - fetch failed)'))
    print(f'    Ahead: {ahead} | Behind: {behind}' + ('' if fetch_ok else ' (STALE - fetch failed)'))
    if status_text is None:
        print('    Working tree: UNKNOWN (git status failed)')
    elif status_text:
        print('    Uncommitted changes:')
        for line in status_text.splitlines():
            print(f'      {line}')
    else:
        print('    Working tree: Clean')

    print('==================================================')
    if not (inspection_ok and (fetch_ok or args.allow_offline)):
        print('ERROR: Repository check failed; see warnings above.', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
