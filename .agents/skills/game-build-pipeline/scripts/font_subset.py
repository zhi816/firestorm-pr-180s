#!/usr/bin/env python3
"""font_subset.py: 以 index.html 實際用到的字，重新產生內嵌 Cubic 11 像素字型子集。

背景：index.html 以 base64 內嵌 Cubic 11 子集（美術設計規格書第四章【定案】）。
新增事件、留言或介面文字後，若沒有重做子集，缺字會改由 Noto Sans TC 補上，
同一行混用兩種字型（見 FP-002）。每次大量新增文字後都應重跑本腳本。

需求：fontTools 與 brotli（輸出 woff2 用）。系統 Python 沒有時，建議裝在暫存虛擬環境：
    python3 -m venv <暫存資料夾>/venv
    <暫存資料夾>/venv/bin/pip install fonttools brotli
完整字型請自官方倉庫 https://github.com/ACh-K/Cubic-11 之 fonts/web/Cubic_11.woff2 取得，
放在倉庫外（不進版控）。

用法：
    <venv>/bin/python .agents/skills/game-build-pipeline/scripts/font_subset.py --check
        只檢查：列出 index.html 用到、但目前內嵌子集沒有的字。缺中文字時結束碼為 1。
    <venv>/bin/python .agents/skills/game-build-pipeline/scripts/font_subset.py --font <完整字型路徑>
        預覽：產生新子集並報告字數與大小，不改檔。
    <venv>/bin/python .agents/skills/game-build-pipeline/scripts/font_subset.py --font <完整字型路徑> --apply
        寫入：把 index.html 內 Cubic11 的 base64 換成新子集。
"""
import argparse
import base64
import io
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..', '..'))

FONT_RE = re.compile(
    r'(@font-face\{font-family:"Cubic11";src:url\(data:font/woff2;base64,)([A-Za-z0-9+/=]+)(\))'
)
BASE64_RE = re.compile(r'base64,[A-Za-z0-9+/=]+')

# 介面常用但未必出現在現有文字中的字元，一併收入，避免日後小幅改字就缺字。
EXTRA_CHARS = (
    ''.join(chr(c) for c in range(0x20, 0x7F))
    + '，。、：；！？「」『』（）《》〈〉【】…—～·％＋－×÷＝＜＞０１２３４５６７８９'
)


def is_cjk(cp):
    return (0x3400 <= cp <= 0x4DBF) or (0x4E00 <= cp <= 0x9FFF) or (0xF900 <= cp <= 0xFAFF)


def load_fonttools():
    try:
        from fontTools.ttLib import TTFont
        from fontTools import subset
        import brotli  # noqa: F401  woff2 壓縮所需
    except ImportError:
        print('[ERROR] 需要 fontTools 與 brotli。請在暫存虛擬環境安裝：')
        print('        python3 -m venv <暫存資料夾>/venv && <暫存資料夾>/venv/bin/pip install fonttools brotli')
        sys.exit(2)
    return TTFont, subset


def used_codepoints(html):
    body = BASE64_RE.sub('', html)
    cps = {ord(c) for c in body + EXTRA_CHARS}
    return {c for c in cps if c >= 0x20 and c not in (0x7F,)}


def fmt_chars(cps, limit=80):
    s = ''.join(chr(c) for c in sorted(cps))
    return s if len(s) <= limit else s[:limit] + f' ...（共 {len(cps)} 字）'


def main():
    ap = argparse.ArgumentParser(description='重新產生 index.html 內嵌之 Cubic 11 子集')
    ap.add_argument('--font', help='Cubic 11 完整字型（.woff2 或 .ttf），放在倉庫外')
    ap.add_argument('--html', default=os.path.join(REPO_ROOT, 'index.html'))
    ap.add_argument('--check', action='store_true', help='只檢查目前內嵌子集的缺字')
    ap.add_argument('--apply', action='store_true', help='把新子集寫回 index.html')
    args = ap.parse_args()

    TTFont, subset = load_fonttools()
    html = open(args.html, encoding='utf-8').read()
    m = FONT_RE.search(html)
    if not m:
        print('[ERROR] index.html 找不到 Cubic11 之 @font-face base64 內嵌字型')
        sys.exit(2)
    used = used_codepoints(html)

    if args.check:
        cur = TTFont(io.BytesIO(base64.b64decode(m.group(2))))
        missing = used - set(cur.getBestCmap())
        cjk = {c for c in missing if is_cjk(c)}
        print(f'內嵌子集 {len(cur.getBestCmap())} 字；頁面用到 {len(used)} 字；缺 {len(missing)} 字（中文 {len(cjk)} 字）')
        if missing:
            print('缺字：' + fmt_chars(missing))
        sys.exit(1 if cjk else 0)

    if not args.font:
        ap.error('產生子集需要 --font <完整字型路徑>（或改用 --check）')

    full = TTFont(args.font)
    full_cmap = set(full.getBestCmap())
    keep = used & full_cmap
    absent = used - full_cmap

    opts = subset.Options()
    opts.flavor = 'woff2'
    opts.hinting = False
    opts.notdef_outline = True
    opts.drop_tables += ['FFTM']  # FontForge 時間戳記，網頁用不到
    sub = subset.Subsetter(options=opts)
    sub.populate(unicodes=sorted(keep))
    font = TTFont(args.font)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = 'woff2'
    font.save(buf)
    data = buf.getvalue()
    b64 = base64.b64encode(data).decode('ascii')

    old_len = len(m.group(2))
    print(f'頁面用到 {len(used)} 字，完整字型含其中 {len(keep)} 字')
    if absent:
        print(f'完整字型本身沒有的 {len(absent)} 字（將由 Noto Sans TC 或系統字型補字）：' + fmt_chars(absent))
    print(f'新子集 woff2 {len(data):,} bytes，base64 {len(b64):,} 字元（原 {old_len:,} 字元）')

    if args.apply:
        new_html = html[:m.start(2)] + b64 + html[m.end(2):]
        with open(args.html, 'w', encoding='utf-8', newline='') as f:
            f.write(new_html)
        print(f'[OK] 已寫入 {args.html}')
    else:
        print('（預覽模式，未改檔；加 --apply 寫入）')


if __name__ == '__main__':
    main()
