# -*- coding: utf-8 -*-
"""Closed-loop tuning: measure the printed PDF and rebalance each cell's font size.
Run build.py first. Writes sizes.json used by subsequent builds."""
import json, os, re, subprocess, html
import pymupdf
import build
import config

PDF = build.OUT_PDF
PAD = 0.55 / 25.4 * 72      # cell bottom padding in pt
TARGET = 0.45 / 25.4 * 72   # wanted gap in pt below last line (~0.45 mm)


def measure():
    d = pymupdf.open(PDF)
    out = {}
    for pi in range(min(len(d), config.PAGES)):
        p = d[pi]
        W, H = p.rect.width, p.rect.height
        dd = p.get_text('dict')
        pad = config.PAD_MM / 25.4 * 72
        row = (H - 2 * pad) / config.ROWS
        colw = W / config.COLS
        for j in range(config.ROWS * config.COLS):
            idx = pi * config.ROWS * config.COLS + j
            if idx >= len(build.B):
                break
            blk = build.B[idx]
            r, c = j % config.COLS, j // config.COLS
            x0, x1 = colw * r, colw * (r + 1)
            ytop, ybot = pad + c * row, pad + c * row + row
            ymax = 0
            for b in dd['blocks']:
                for l in b.get('lines', []):
                    for s in l['spans']:
                        xc = (s['bbox'][0] + s['bbox'][2]) / 2
                        if x0 - 1 <= xc <= x1 + 1 and s['bbox'][1] >= ytop - 1 and s['bbox'][3] <= ybot + 2:
                            ymax = max(ymax, s['bbox'][3])
            out[blk['id']] = (ybot - PAD) - ymax   # gap in pt below last text
    return out


AVAIL = (config.PAGE_H_MM - 2 * config.PAD_MM) / config.ROWS - 4.2  # usable content height per cell (mm)


def init_sizes():
    sizes = json.load(open('sizes.json')) if os.path.exists('sizes.json') else {}
    if sizes and not isinstance(list(sizes.values())[0], dict):
        sizes = {}
    if not sizes:
        build.build()
        dom = subprocess.run([build.CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
                              '--virtual-time-budget=20000', '--dump-dom',
                              'file:///' + os.path.abspath(build.OUT_HTML).replace('\\', '/')],
                             capture_output=True, text=True).stdout
        m = re.search(r'data-fit="([^"]*)"', dom, re.S)
        for r in json.loads(html.unescape(m.group(1))):
            sizes[r['id']] = {'fs': r['size'], 'lh': 1.06}
        json.dump(sizes, open('sizes.json', 'w'), indent=1)
    return sizes


def main():
    sizes = init_sizes()
    for it in range(5):
        build.build()
        build.topdf(build.OUT_HTML, PDF)
        gaps = measure()
        gmm = {k: v / 72 * 25.4 for k, v in gaps.items()}
        print('pass', it, {k: round(v, 1) for k, v in gmm.items()})
        worst = 0
        for k, g in gmm.items():
            c = AVAIL - g                     # current content height (mm)
            want = AVAIL - 0.55
            lh = sizes[k]['lh'] * want / max(c, 20)
            if lh < 1.012:
                sizes[k]['fs'] = round(max(2.9, sizes[k]['fs'] - 0.02), 2)
                lh = 1.012
            sizes[k]['lh'] = round(min(1.55, lh), 3)
            worst = max(worst, abs(g - 0.55))
        json.dump(sizes, open('sizes.json', 'w'), indent=1)
        if worst < 0.3:
            break
    print('final sizes', sizes)


if __name__ == '__main__':
    main()
