# -*- coding: utf-8 -*-
"""Keep every cell's font size locked at one uniform size (default from config),
solving line-height only. Set config.FONT_LOCK = 3.5 (for example) to use."""
import json
import pymupdf
import build
import config

PDF = build.OUT_PDF
PAD = 0.55 / 25.4 * 72
AVAIL = (config.PAGE_H_MM - 2 * config.PAD_MM) / config.ROWS - 4.2
FS = config.FONT_LOCK or 3.5
LH_MIN, LH_MAX = 1.0, 1.55


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
            out[blk['id']] = (ybot - PAD) - ymax
    return out


def main():
    sizes = {blk['id']: {'fs': FS, 'lh': 1.012} for blk in build.B}
    for it in range(12):
        build.build()
        build.topdf(build.OUT_HTML, PDF)
        g = {k: v / 72 * 25.4 for k, v in measure().items()}
        print('pass', it, {k: round(v, 2) for k, v in g.items()})
        worst = 0
        for k, gap in g.items():
            c = max(AVAIL - gap, 20)
            target = sizes[k]['lh'] * (AVAIL - 0.45) / c
            lh = sizes[k]['lh'] + 0.7 * (target - sizes[k]['lh'])   # damping
            lh = min(LH_MAX, max(LH_MIN, lh))
            sizes[k]['lh'] = round(lh, 3)
            worst = max(worst, abs(gap - 0.45))
        json.dump(sizes, open('sizes.json', 'w'), indent=1)
        if worst < 0.25:
            break
    print('final', sizes)
    bad = {k: round(v, 2) for k, v in g.items() if v < 0.05}
    print('OVERFLOW cells:', bad if bad else 'none')


if __name__ == '__main__':
    main()
