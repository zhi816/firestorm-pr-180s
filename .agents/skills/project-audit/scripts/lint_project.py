#!/usr/bin/env python3
"""lint_project.py: firestorm-pr-180s 專案結構與文件健康檢查腳本。

只用 Python 標準函式庫（3.7 以上），於倉庫根目錄執行：
    python3 .agents/skills/project-audit/scripts/lint_project.py
    python3 .agents/skills/project-audit/scripts/lint_project.py --errors-only
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))

REQUIRED_FILES = [
    'AGENTS.md',
    'DESIGN.md',
    'CLAUDE.md',
    'README.md',
    'docs/index.md',
    'docs/log.md',
    'docs/issues.md',
    'docs/todo.md',
]

ZERO_EMOJI_FILES = [
    'AGENTS.md',
    'DESIGN.md',
    'CLAUDE.md',
    'README.md',
    'docs/index.md',
    'docs/log.md',
    'docs/issues.md',
    'docs/todo.md',
    'docs/art/美術設計規格書.md',
]

EMOJI_RE = re.compile(r'[\U0001F300-\U0001FAFF\u2600-\u27BF]')
LINK_RE = re.compile(r'\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')

LOG_ACTIONS = {
    'init', 'spec', 'design', 'feat', 'fix', 'audit',
    'test', 'lint', 'rule', 'update', 'config', 'git',
}
LOG_TAGS = {
    '#企劃', '#狀態機', '#LLM串接', '#離線資料', '#UI介面',
    '#手機版', '#像素美術', '#新聞圖卡', '#音效', '#測試驗證', '#文件', '全域',
}
LEGACY_LOG_TYPES = {'決策', '討論', '產出', '待辦'}

TODO_SCOPES = {'app', 'art', 'spec', 'test', 'rule', 'skill', 'deploy'}
TODO_STATES = {'open', 'waiting', 'doing'}
ISSUE_STATES = {'open', 'fixed', 'wontfix'}
ISSUE_TYPES = {'功能異常', '介面跑版', '規格不符', 'API異常', '無障礙或效能', '待確認'}

errors = []
warnings = []
infos = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def info(msg):
    infos.append(msg)


def read_utf8(rel):
    p = os.path.join(ROOT, rel)
    with open(p, 'rb') as f:
        raw = f.read()
    if raw.startswith(b'\xef\xbb\xbf'):
        err(f'{rel}: 檔案含有 UTF-8 BOM，應改為無 BOM。')
    return raw.decode('utf-8').replace('\r\n', '\n')


def check_required():
    for rel in REQUIRED_FILES:
        if not os.path.isfile(os.path.join(ROOT, rel)):
            err(f'缺少必要核心文件：{rel}')


def check_emoji():
    for rel in ZERO_EMOJI_FILES:
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            continue
        txt = read_utf8(rel)
        hits = EMOJI_RE.findall(txt)
        if hits:
            err(f'{rel}: 違反 Zero-Emoji 規範，偵測到表情符號 {sorted(set(hits))}')


def check_links():
    md_files = []
    for f in ('AGENTS.md', 'DESIGN.md', 'CLAUDE.md', 'README.md'):
        if os.path.isfile(os.path.join(ROOT, f)):
            md_files.append(f)
    docs_dir = os.path.join(ROOT, 'docs')
    for dp, _, fns in os.walk(docs_dir):
        if 'archive' in dp.split(os.sep):
            continue
        for f in fns:
            if f.endswith('.md'):
                md_files.append(os.path.relpath(os.path.join(dp, f), ROOT).replace('\\', '/'))

    for rel in sorted(md_files):
        txt = read_utf8(rel)
        # 移除 code blocks，避免範例假路徑觸發誤報
        cleaned = re.sub(r'```[\s\S]*?```', '', txt)
        base_dir = os.path.dirname(os.path.join(ROOT, rel))
        for m in LINK_RE.finditer(cleaned):
            target = m.group(1)
            if target.startswith('file:///'):
                err(f'{rel}: 禁止使用本機絕對路徑連結 {target}')
                continue
            if re.match(r'^[a-z][a-z0-9+.-]*:', target, re.I) or target.startswith('#'):
                continue
            path_part = target.split('#', 1)[0]
            if not path_part:
                continue
            resolved = os.path.normpath(os.path.join(base_dir, path_part))
            if not os.path.exists(resolved):
                # index.html 尚未建立前，README / docs 中的 index.html 連結降級為 INFO
                if path_part.endswith('index.html') and not os.path.exists(os.path.join(ROOT, 'index.html')):
                    info(f'{rel}: 指向尚未建立的 index.html（{target}）')
                else:
                    err(f'{rel}: 壞掉的相對連結 -> {target}')


def check_index():
    idx_path = os.path.join(ROOT, 'docs', 'index.md')
    if not os.path.isfile(idx_path):
        return
    idx_txt = read_utf8('docs/index.md')
    docs_dir = os.path.join(ROOT, 'docs')
    for dp, _, fns in os.walk(docs_dir):
        rel_dir = os.path.relpath(dp, docs_dir).replace('\\', '/')
        if rel_dir.startswith('issues/closed'):
            continue
        for f in sorted(fns):
            if f.startswith('.') or f == 'index.md':
                continue
            rel_in_docs = f if rel_dir == '.' else f'{rel_dir}/{f}'
            if rel_in_docs not in idx_txt and f not in idx_txt:
                warn(f'docs/index.md: 尚未收錄 {rel_in_docs}')


def check_todo(all_issue_ids):
    rel = 'docs/todo.md'
    if not os.path.isfile(os.path.join(ROOT, rel)):
        return set()
    txt = read_utf8(rel)
    item_re = re.compile(r'(?m)^### (TD-\d{3,}) \| (\w+) \| (\w+) \| (.+)$')
    any_h3 = re.compile(r'(?m)^### (.+)$')
    boundary = re.compile(r'(?m)^##+ ')

    seen = set()
    blocks = []
    for m in any_h3.finditer(txt):
        line = m.group(0)
        hm = item_re.match(line)
        if not hm:
            err(f'{rel}: 待辦標題格式不符「### TD-NNN | state | scope | title」：{line}')
            continue
        tid, st, sc, title = hm.groups()
        if tid in seen:
            err(f'{rel}: 重複的待辦編號 {tid}')
        seen.add(tid)
        if st not in TODO_STATES:
            err(f'{rel}: {tid} 狀態無效「{st}」（應為 {sorted(TODO_STATES)}）')
        if sc not in TODO_SCOPES:
            err(f'{rel}: {tid} 範圍無效「{sc}」（應為 {sorted(TODO_SCOPES)}）')
        nxt = boundary.search(txt, m.end())
        blk = txt[m.start():nxt.start() if nxt else len(txt)]
        blocks.append((tid, st, blk))

    for tid, st, blk in blocks:
        if '- **內容**：' not in blk:
            err(f'{rel}: {tid} 缺少「- **內容**：」')
        if '- **完成條件**：' not in blk:
            err(f'{rel}: {tid} 缺少「- **完成條件**：」')
        if '- **來源**：' not in blk:
            warn(f'{rel}: {tid} 建議補上「- **來源**：」')
        if st == 'waiting' and '- **等待**：' not in blk:
            err(f'{rel}: {tid} 狀態為 waiting，必須填寫「- **等待**：」')
        if st == 'doing' and '- **負責**：' not in blk:
            err(f'{rel}: {tid} 狀態為 doing，必須填寫「- **負責**：」')

    return seen


def collect_issue_ids():
    ids = set()
    for path in [os.path.join(ROOT, 'docs', 'issues.md')]:
        if os.path.isfile(path):
            txt = open(path, encoding='utf-8').read()
            ids.update(re.findall(r'(?m)^### (FP-\d{3,}) \|', txt))
    closed_dir = os.path.join(ROOT, 'docs', 'issues', 'closed')
    if os.path.isdir(closed_dir):
        for dp, _, fns in os.walk(closed_dir):
            for f in fns:
                if f.endswith('.md'):
                    txt = open(os.path.join(dp, f), encoding='utf-8').read()
                    ids.update(re.findall(r'(?m)^### (FP-\d{3,}) \|', txt))
    return ids


def check_issues_and_crossrefs(todo_ids):
    rel = 'docs/issues.md'
    head_re = re.compile(r'(?m)^### (FP-\d{3,}) \| (\w+) \| ([^|]+?) \| ([^|]+?) \| (.+)$')
    any_h3 = re.compile(r'(?m)^### (.+)$')
    boundary = re.compile(r'(?m)^##+ ')

    seen = set()
    closed_unarchived = 0
    all_blocks = []

    if os.path.isfile(os.path.join(ROOT, rel)):
        txt = read_utf8(rel)
        # 分節標題檢查（不允許 ## 分節）
        for m in re.finditer(r'(?m)^## .+$', txt):
            err(f'{rel}: 問題清單不應分節，發現標題「{m.group(0)}」')
        for m in any_h3.finditer(txt):
            line = m.group(0)
            hm = head_re.match(line)
            if not hm:
                err(f'{rel}: 標題格式不符「### FP-NNN | state | file | loc | type」：{line}')
                continue
            iid, st, target, loc, itype = [x.strip() for x in hm.groups()]
            if iid in seen:
                err(f'{rel}: 重複的問題編號 {iid}')
            seen.add(iid)
            if st not in ISSUE_STATES:
                err(f'{rel}: {iid} 狀態無效「{st}」')
            if st in ('fixed', 'wontfix'):
                closed_unarchived += 1
            if itype not in ISSUE_TYPES:
                warn(f'{rel}: {iid} 問題類型「{itype}」不在建議清單 {sorted(ISSUE_TYPES)}')
            nxt = boundary.search(txt, m.end())
            blk = txt[m.start():nxt.start() if nxt else len(txt)]
            all_blocks.append((rel, iid, st, blk))

    if closed_unarchived >= 10:
        warn(f'{rel}: 已有 {closed_unarchived} 筆已結案條目尚未歸檔，建議執行 archive_issues.py。')

    closed_dir = os.path.join(ROOT, 'docs', 'issues', 'closed')
    if os.path.isdir(closed_dir):
        for dp, _, fns in os.walk(closed_dir):
            for f in sorted(fns):
                if not f.endswith('.md'):
                    continue
                crel = os.path.relpath(os.path.join(dp, f), ROOT).replace('\\', '/')
                ctxt = read_utf8(crel)
                for m in any_h3.finditer(ctxt):
                    hm = head_re.match(m.group(0))
                    if not hm:
                        err(f'{crel}: 歸檔標題格式不符：{m.group(0)}')
                        continue
                    iid, st, *_ = [x.strip() for x in hm.groups()]
                    if iid in seen:
                        err(f'{crel}: 與現行或他檔重複的問題編號 {iid}')
                    seen.add(iid)
                    if st == 'open':
                        err(f'{crel}: 歸檔檔不得包含 open 問題 {iid}')
                    nxt = boundary.search(ctxt, m.end())
                    blk = ctxt[m.start():nxt.start() if nxt else len(ctxt)]
                    all_blocks.append((crel, iid, st, blk))

    for file_rel, iid, st, blk in all_blocks:
        if '- **問題**：' not in blk:
            err(f'{file_rel}: {iid} 缺少「- **問題**：」')
        if '- **發現於**：' not in blk:
            warn(f'{file_rel}: {iid} 建議補上「- **發現於**：」')
        if st in ('fixed', 'wontfix') and '- **處理**：' not in blk:
            err(f'{file_rel}: {iid} 已結案但缺少「- **處理**：」')
        rel_m = re.search(r'(?m)^- \*\*關聯\*\*：(.+)$', blk)
        if rel_m:
            refs = re.findall(r'(?:FP|TD)-\d{3,}', rel_m.group(1))
            for r in refs:
                if r.startswith('FP-') and r not in seen:
                    err(f'{file_rel}: {iid} 的「關聯」指向不存在的問題 {r}')
                if r.startswith('TD-') and r not in todo_ids:
                    if st == 'open':
                        warn(f'{file_rel}: {iid} 仍為 open，但關聯待辦 {r} 已不在 docs/todo.md（可檢查是否已可修）')

    # 也檢查 todo.md 的關聯是否指向存在的 FP/TD
    todo_path = os.path.join(ROOT, 'docs', 'todo.md')
    if os.path.isfile(todo_path):
        ttxt = read_utf8('docs/todo.md')
        for m in re.finditer(r'(?m)^### (TD-\d{3,}) \|[\s\S]*?(?=\n##+ |\Z)', ttxt):
            tid = m.group(1)
            rm = re.search(r'(?m)^- \*\*關聯\*\*：(.+)$', m.group(0))
            if rm:
                for r in re.findall(r'(?:FP|TD)-\d{3,}', rm.group(1)):
                    if r.startswith('FP-') and r not in seen:
                        err(f'docs/todo.md: {tid} 的「關聯」指向不存在的問題 {r}')
                    if r.startswith('TD-') and r not in todo_ids:
                        warn(f'docs/todo.md: {tid} 的「關聯」{r} 目前不在待辦清單（可能已完成刪除）')

    return seen


def check_log():
    rel = 'docs/log.md'
    if not os.path.isfile(os.path.join(ROOT, rel)):
        return
    txt = read_utf8(rel)
    any_h2 = re.compile(r'(?m)^## \[([^\]]+)\] (.+)$')
    new_fmt = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2})$')
    legacy_fmt = re.compile(r'^(\d{4}-\d{2}-\d{2})$')
    boundary = re.compile(r'(?m)^## \[')

    matches = list(any_h2.finditer(txt))
    for i, m in enumerate(matches):
        ts, rest = m.group(1), m.group(2)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(txt)
        blk = txt[m.start():end]
        if legacy_fmt.match(ts):
            parts = [p.strip() for p in rest.split('|')]
            if len(parts) < 2 or parts[0] not in LEGACY_LOG_TYPES:
                warn(f'{rel}: 舊條目格式提示 [{ts}] {rest}')
            continue
        if not new_fmt.match(ts):
            err(f'{rel}: 日誌時間格式錯誤「[{ts}]」，應為 YYYY-MM-DD HH:MM')
            continue
        parts = [p.strip() for p in rest.split('|')]
        if len(parts) != 3:
            err(f'{rel}: 新條目標題須為三段「## [YYYY-MM-DD HH:MM] 動作 | 標題 | 標籤」：## [{ts}] {rest}')
            continue
        action, title, tags_str = parts
        if action not in LOG_ACTIONS:
            err(f'{rel}: [{ts}] 動作「{action}」不在白名單 {sorted(LOG_ACTIONS)}')
        tags = tags_str.split()
        if not tags or any(t not in LOG_TAGS for t in tags):
            err(f'{rel}: [{ts}] 標籤「{tags_str}」含白名單外標籤（可用：{sorted(LOG_TAGS)}）')
        if '- **執行代理**：' not in blk:
            err(f'{rel}: [{ts}] 缺少「- **執行代理**：」')
        if '- **模型版本**：' not in blk:
            err(f'{rel}: [{ts}] 缺少「- **模型版本**：」')
        if '- **具體變更**：' not in blk:
            err(f'{rel}: [{ts}] 缺少「- **具體變更**：」')


def check_git_append_only(current_issue_ids):
    if not os.path.isdir(os.path.join(ROOT, '.git')):
        return
    # 檢查曾經在 HEAD 提交過的 log 標題與 FP-NNN 問題編號是否仍然存在
    r = subprocess.run(['git', '-C', ROOT, 'log', '-p', '--pretty=format:__COMMIT__%H', '--', 'docs/log.md'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        return
    cur_log = read_utf8('docs/log.md') if os.path.isfile(os.path.join(ROOT, 'docs', 'log.md')) else ''
    cur_ts = set(re.findall(r'(?m)^## \[([^\]]+)\] ([^\n]+)', cur_log))
    committed_headings = set(re.findall(r'(?m)^\+## \[([^\]]+)\] ([^\n]+)', r.stdout))
    for ts, rest in sorted(committed_headings):
        if (ts, rest) not in cur_ts:
            # 僅檢查時間戳記是否還在，避免舊標題微調誤報；若連時間都消失則報 ERROR
            if f'[{ts}]' not in cur_log:
                err(f'docs/log.md: 曾提交過之日誌條目 [{ts}] 已遺失（違反 append-only）')

    r_iss = subprocess.run(['git', '-C', ROOT, 'log', '-p', '--', 'docs/issues.md'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r_iss.returncode == 0:
        ever_fp = set(re.findall(r'(?m)^\+### (FP-\d{3,}) \|', r_iss.stdout))
        for fp in sorted(ever_fp):
            if fp not in current_issue_ids:
                err(f'docs/issues.md: 曾提交過之問題編號 {fp} 已遺失（不得刪除問題條目）')


def check_app_index_html():
    app_path = os.path.join(ROOT, 'index.html')
    if not os.path.isfile(app_path):
        info('index.html: 尚未建立（專案尚在規劃/規格階段）')
        return
    txt = read_utf8('index.html')
    if EMOJI_RE.findall(txt):
        warn('index.html: 偵測到 Emoji（建議改為純像素圖示或文字標籤）')
    for brand in ('TVBS', '蘋果日報', 'YouTube', 'Threads', 'Dcard'):
        if brand in txt:
            warn(f'index.html: 出現真實品牌名稱「{brand}」（請確認未違反虛構品牌原則：炎上新聞台 FNN / 炎串 / 爆料版）')
    if 'STATE_REVISE' not in txt:
        warn('index.html: 未偵測到 STATE_REVISE（緊急撤回 Reflection 閉環狀態）')


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass
    ap = argparse.ArgumentParser(description='firestorm-pr-180s 專案結構與文件檢查')
    ap.add_argument('--errors-only', action='store_true', help='只顯示 ERROR')
    a = ap.parse_args()

    check_required()
    check_emoji()
    check_links()
    check_index()
    todo_ids = check_todo(collect_issue_ids())
    issue_ids = check_issues_and_crossrefs(todo_ids)
    check_log()
    check_git_append_only(issue_ids)
    check_app_index_html()

    if not a.errors_only:
        for msg in infos:
            print('INFO   ' + msg)
        for msg in warnings:
            print('WARN   ' + msg)
    for msg in errors:
        print('ERROR  ' + msg)

    print(f'Summary: ERROR {len(errors)}, WARN {len(warnings)}, INFO {len(infos)}')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
