# -*- coding: utf-8 -*-
"""Final pass: per-cell line-height bisection so every cell fits (gap >= 0.15 mm)
with the largest possible line spacing. Run after tune.py."""
import json
import pymupdf
import build
import config

PDF = build.OUT_PDF
PAD = 0.55 / 25.4 * 72
AVAIL = (config.PAGE_H_MM - 2 * config.PAD_MM) / config.ROWS - 4.2
FS = config.FONT_LOCK or 3.5
GAP_OK = 0.15          # mm; below this = treat as overflow
ROUNDS = 11


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
            out[blk['id']] = (ybot - PAD) - ymax   # pt
    return out


def main():
    sizes = json.load(open('sizes.json'))
    lh = {k: v['lh'] for k, v in sizes.items()}
    for k in lh:
        sizes[k]['fs'] = FS
    lo = {k: None for k in lh}
    hi = {k: None for k in lh}
    for it in range(ROUNDS):
        build.build()
        build.topdf(build.OUT_HTML, PDF)
        g = {k: v / 72 * 25.4 for k, v in measure().items()}
        print('pass', it, {k: round(v, 2) for k, v in g.items()}, 'lh', lh)
        for k, v in g.items():
            if v >= GAP_OK:
                if lo[k] is None or lh[k] > lo[k]:
                    lo[k] = lh[k]
            else:
                hi[k] = lh[k]
        for k in lh:
            if lo[k] is not None and hi[k] is not None and hi[k] - lo[k] > 0.004:
                lh[k] = round((lo[k] + hi[k]) / 2, 3)
            elif lo[k] is None:
                lh[k] = round(lh[k] * 0.985, 3)
        for k in lh:
            sizes[k]['lh'] = lh[k]
        json.dump(sizes, open('sizes.json', 'w'), indent=1)
    for k in lh:
        if lo[k] is not None:
            sizes[k]['lh'] = lo[k]
    json.dump(sizes, open('sizes.json', 'w'), indent=1)
    build.build()
    build.topdf(build.OUT_HTML, PDF)
    g = {k: v / 72 * 25.4 for k, v in measure().items()}
    bad = {k: round(v, 2) for k, v in g.items() if v < GAP_OK}
    print('FINAL gaps', {k: round(v, 2) for k, v in g.items()})
    print('BAD (overflow):', bad if bad else 'none')


if __name__ == '__main__':
    main()
