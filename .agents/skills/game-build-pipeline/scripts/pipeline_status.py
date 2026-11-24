#!/usr/bin/env python3
"""pipeline_status.py: 檢查 firestorm-pr-180s 目前開發進度、規格完整性與待辦狀態。

專案尚未建立 index.html 時，自動顯示規劃/樣張狀態與下一批可接手之 open TD-NNN 任務；
index.html 建立後，掃描關鍵模組標記（CSS Tokens、狀態機、事件庫、API/Fallback、Canvas/音效），
讓手機端使用者與接手 AI 一條指令掌握專案現況。

用法：
    python3 .agents/skills/game-build-pipeline/scripts/pipeline_status.py
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))


def read_if_exists(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p):
        return None
    with open(p, 'rb') as f:
        return f.read().decode('utf-8', 'replace')


def count_todos():
    txt = read_if_exists('docs/todo.md') or ''
    items = re.findall(r'(?m)^### (TD-\d{3,}) \| (\w+) \| (\w+) \| (.+)$', txt)
    return items


def count_issues():
    txt = read_if_exists('docs/issues.md') or ''
    items = re.findall(r'(?m)^### (FP-\d{3,}) \| (\w+) \| ([^|]+?) \|', txt)
    return items


def check_step(label, ok, detail=''):
    tag = 'OK     ' if ok else 'PENDING'
    suffix = f' ({detail})' if detail else ''
    print(f'  [{tag}] {label}{suffix}')


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print('==================================================')
    print('Firestorm PR: 180s - Build Pipeline Status')
    print('==================================================')

    # Phase 0: Docs & Samples
    print('\n[Phase 0] 文件架構與設計樣張')
    check_step('治理與設計檔 (AGENTS.md / DESIGN.md)',
               all(os.path.isfile(os.path.join(ROOT, f)) for f in ('AGENTS.md', 'DESIGN.md', 'docs/todo.md', 'docs/issues.md')))
    check_step('像素 RPG 規格與樣張 v3',
               os.path.isfile(os.path.join(ROOT, 'docs/art/美術設計規格書.md'))
               and os.path.isfile(os.path.join(ROOT, 'docs/art/samples/像素風格樣張_v3.html')))

    app_txt = read_if_exists('index.html')
    print('\n[Phase 1-5] index.html 遊戲本體實作檢核')
    if app_txt is None:
        check_step('index.html 建立', False, '尚未建立，請從 docs/todo.md 接手 TD-003')
    else:
        check_step('index.html 建立', True, f'{len(app_txt)} 字元')
        check_step('P1 像素 Design Tokens 與字型 (--night / --gold / Cubic11)',
                   '--night' in app_txt and '--gold' in app_txt and 'Cubic' in app_txt)
        check_step('P2 狀態機與 Reflection 撤回閉環 (STATE_REVISE)',
                   all(s in app_txt for s in ('STATE_TITLE', 'STATE_SELECT', 'STATE_CRISIS', 'STATE_AUDITING', 'STATE_VERDICT', 'STATE_REVISE', 'STATE_RESULT')))
        check_step('P3 事件庫與點陣圖層/角色 Canvas',
                   'CRISIS_EVENTS' in app_txt or ('inquiries' in app_txt and '<canvas' in app_txt.lower()))
        check_step('P4 LLM API 串接與離線 Fallback',
                   ('api.commandcode.ai' in app_txt or 'workers.dev' in app_txt)
                   and ('fallback' in app_txt.lower() or 'offline' in app_txt.lower()))
        check_step('P5 結局新聞卡 (320x180) 與 Web Audio 音效',
                   ('ENDING_PERFECT' in app_txt and 'ENDING_DESTROYED' in app_txt)
                   and ('AudioContext' in app_txt or 'webkitAudioContext' in app_txt))

    todos = count_todos()
    issues = count_issues()
    open_todos = [t for t in todos if t[1] == 'open']
    waiting_todos = [t for t in todos if t[1] == 'waiting']
    doing_todos = [t for t in todos if t[1] == 'doing']
    open_issues = [i for i in issues if i[1] == 'open']

    print('\n[協作看板摘要]')
    print(f'  待辦 (docs/todo.md): open {len(open_todos)} | doing {len(doing_todos)} | waiting {len(waiting_todos)}')
    if open_todos:
        print('  可立即指派的 open 任務：')
        for tid, _, scope, title in open_todos[:5]:
            print(f'    - {tid} [{scope}] {title}')
    print(f'  問題 (docs/issues.md): open {len(open_issues)} | total {len(issues)}')
    for iid, st, target in open_issues[:5]:
        print(f'    - {iid} ({st}) {target.strip()}')
    print('==================================================')


if __name__ == '__main__':
    main()
