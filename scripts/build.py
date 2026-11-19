# -*- coding: utf-8 -*-
"""Engine: content.py -> HTML (KaTeX) -> print-perfect PDF via headless Chrome."""
import re, os, json, shutil, subprocess
import config
from content import B
from purpose import PURPOSE
import markers

OUT_HTML = 'cheatsheet.html'
OUT_PDF = 'cheatsheet.pdf'
for _k in ('katex/package/dist', 'katex/dist', 'node_modules/katex/dist'):   # npm install katex
    if os.path.exists(_k + '/katex.min.css'):
        KATEX = _k
        break
else:
    KATEX = 'katex/package/dist'      # download the dist here if npm is unavailable

CHROME = (shutil.which('chrome') or shutil.which('google-chrome')
          or shutil.which('chromium') or 'chrome')
for _p in (r'C:/Program Files/Google/Chrome/Application/chrome.exe',
           r'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'):
    if os.path.exists(_p):
        CHROME = _p
        break

# ---- colour-coding pass on all prose text ----------------------------------
for _blk in B:
    for _i, _it in enumerate(_blk['items']):
        if _it[0] in ('p', 'note'):
            _blk['items'][_i] = (_it[0], markers.transform(_it[1]))
        elif _it[0] == 'e' and len(_it) > 2 and _it[2]:
            _blk['items'][_i] = (_it[0], _it[1], markers.transform(_it[2]))


def purpose_span(note):
    for k, v in PURPOSE.items():
        if note.startswith(k):
            return '<span class="pp">▸%s</span>' % v
    return ''


def esc_text(t):
    t = re.sub(r'&(?!(amp|lt|gt|nbsp|hellip|mdash|ndash);)', '&amp;', t)
    t = t.replace('<', '&lt;').replace('>', '&gt;')
    return t


def subscripts(s):
    return re.sub(r'(?<![A-Za-z0-9])([A-Za-z\u03b1-\u03c9\u0391-\u03a9])_\{?([A-Za-z0-9,\+\u03b1-\u03c9]{1,6})\}?',
                  r'\1<sub>\2</sub>', s)


def inline(t):
    parts = t.split('$')
    out = []
    for i, seg in enumerate(parts):
        if i % 2 == 1:
            out.append('$' + esc_text(seg) + '$')
        else:
            seg = esc_text(seg)
            seg = re.sub(r'\*\*([^*:]{2,26})\*\*:', r'<mark><b>\1</b></mark>:', seg)
            seg = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', seg)
            seg = re.sub(r'==(.+?)==', r'<mark>\1</mark>', seg)
            seg = re.sub(r'~~(.+?)~~', r'<span class="mg">\1</span>', seg)
            seg = re.sub(r'@@(.+?)@@', r'<span class="mo">\1</span>', seg)
            seg = re.sub(r'##(.+?)##', r'<span class="mr">\1</span>', seg)
            seg = re.sub(r'%%(.+?)%%', r'<span class="mb">\1</span>', seg)
            seg = re.sub(r'\{\{(.+?)\}\}', r'<span class="mp">\1</span>', seg)
            seg = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', seg)
            seg = subscripts(seg)
            seg = seg.replace('`', '')
            out.append(seg)
    return ''.join(out)


WIDE = ('pmatrix', 'cases', '\\begin')
PER_PAGE = config.COLS * config.ROWS
if len(B) > PER_PAGE * config.PAGES:
    print('WARNING: %d blocks > %d cells (%d pages); extras are dropped'
          % (len(B), PER_PAGE * config.PAGES, config.PAGES))


def render_items(items):
    h = []
    i, n = 0, len(items)
    while i < n:
        it = items[i]
        k = it[0]
        if k == 'h':
            title = esc_text(it[1])
            i += 1
            nxt = items[i] if i < n else None
            h.append('<div class="sec">')
            if nxt and nxt[0] == 'p':
                h.append('<span class="sh">%s</span><span class="rt"> %s</span></div>'
                         % (title, inline(nxt[1])))
                i += 1
            elif nxt and nxt[0] == 'e' and len(nxt[1]) <= 62 and not any(w in nxt[1] for w in WIDE):
                h.append('<span class="sh">%s</span><span class="mm">$%s$</span></div>'
                         % (title, esc_text(nxt[1])))
                note = nxt[2] if len(nxt) > 2 else ''
                if note:
                    h.append('<div class="eqp">%s %s</div>' % (purpose_span(note), inline(note)))
                i += 1
            else:
                h.append('<span class="sh">%s</span></div>' % title)
        elif k == 'p':
            h.append('<p>%s</p>' % inline(it[1]))
            i += 1
        elif k == 'e':
            src, note = it[1], (it[2] if len(it) > 2 else '')
            if any(w in src for w in WIDE) or len(src) > 110:
                h.append('<div class="eq wide"><span class="mm">\\[%s\\]</span></div>' % esc_text(src))
                if note:
                    h.append('<div class="eqp">%s %s</div>' % (purpose_span(note), inline(note)))
            else:
                h.append('<div class="eq"><span class="mm">\\[%s\\]</span><span class="eqp">%s %s</span></div>'
                         % (esc_text(src), purpose_span(note), inline(note)))
            i += 1
        elif k == 't':
            rows = it[1]
            cls = it[2] if len(it) > 2 else ''
            body = ''
            for ri, row in enumerate(rows):
                tag = 'th' if ri == 0 else 'td'
                body += '<tr>' + ''.join('<%s>%s</%s>' % (tag, inline(c), tag) for c in row) + '</tr>'
            h.append('<table class="tb %s">%s</table>' % (cls, body))
            i += 1
        elif k == 'note':
            h.append('<div class="nb">%s</div>' % inline(it[1]))
            i += 1
        elif k == 'raw':
            h.append(it[1])
            i += 1
    return '\n'.join(h)


CSS = r"""
@page { size: {PW}mm {PH}mm; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  width: {PW}mm; overflow: hidden;
  font-family: "Segoe UI", "Microsoft JhengHei", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
  color: #111; background: #fff; line-height: 1.06;
  -webkit-font-smoothing: antialiased;
}
.page { width: {PW}mm; height: {PH}mm; display: grid; overflow: hidden; padding: {PAD}mm;
  page-break-after: always;
  grid-template-columns: repeat({COLS}, 1fr); grid-template-rows: repeat({ROWS}, 1fr); }
.page:last-child { page-break-after: auto; }
.cell { position: relative; overflow: hidden; display: flex; flex-direction: column;
  min-width: 0; min-height: 0;
  padding: 0 .95mm .5mm; border-right: .25pt solid #9aa3ad; border-bottom: .25pt solid #9aa3ad; }
.cell.lastcol { border-right: none; }
.cell.lastrow { border-bottom: none; }
.hd { display: flex; align-items: baseline; gap: .6mm; background: #16283f; color: #fff;
  margin: 0 0 .35mm; padding: .38mm .8mm .34mm; }
.hd .no { font-size: 1.02em; font-weight: 700; color: #f2c14e; letter-spacing: .02em; }
.hd .tt { font-size: .92em; font-weight: 700; letter-spacing: .03em; }
.bd { flex: 1 1 auto; overflow: hidden; min-width: 0; }
p { margin: 0 0 .2pt; text-align: left; hyphens: auto; }
b { font-weight: 650; }
.sec { position: relative; margin-top: .3mm; padding-top: .12mm; }
.sec::before { content: ''; position: absolute; left: 0; right: 0; top: 0; height: .9pt;
  background: #151515; transform: scaleY(.24); transform-origin: top; }
.sec:first-child { margin-top: 0; padding-top: 0; }
.sec:first-child::before { display: none; }
.sh { display: inline; background: #1d3a5f; color: #fff; font-size: .84em; font-weight: 700;
  letter-spacing: .035em; text-transform: uppercase; padding: .06mm .45mm .03mm; }
.rt { display: inline; }
mark { background: linear-gradient(#ffe25c,#ffe25c) no-repeat .02em .13em / calc(100% - .04em) .62em;
  color: #000; padding: 0; }
.mg { background: linear-gradient(#b4e8aa,#b4e8aa) no-repeat .02em .13em / calc(100% - .04em) .62em;
  color: #000; padding: 0; }
.mo { background: linear-gradient(#ffc98c,#ffc98c) no-repeat .02em .13em / calc(100% - .04em) .62em;
  color: #000; padding: 0; }
.mr { background: linear-gradient(#ffadad,#ffadad) no-repeat .02em .13em / calc(100% - .04em) .62em;
  color: #000; padding: 0; }
.mb { background: linear-gradient(#aed4ff,#aed4ff) no-repeat .02em .13em / calc(100% - .04em) .62em;
  color: #000; padding: 0; }
.mp { background: linear-gradient(#d8bdff,#d8bdff) no-repeat .02em .13em / calc(100% - .04em) .62em;
  color: #000; padding: 0; }
.eq { display: flex; align-items: baseline; gap: 1.0mm; margin: .12pt 0 .05pt; }
.eq .mm { flex: 0 0 auto; }
.eq.wide { display: block; }
.eq .eqp { flex: 1 1 auto; min-width: 12mm; }
.eqp { font-size: .78em; line-height: 1.0; color: #222; text-align: left; margin: .05mm 0 .3pt; }
.pp { font-size: 1.12em; font-weight: 700; color: #1d4e89; }
.nb { display: inline; background: #f6e2b8; color: #111; font-weight: 700; font-size: .95em;
  letter-spacing: .03em; padding: .05mm .5mm .02mm; margin-right: .5mm; }
.tb { border-collapse: collapse; width: 100%; font-size: .84em; margin: .2pt 0 .4pt; }
.tb th, .tb td { border: .2pt solid #9aa3ad; padding: .05mm .3mm; text-align: center; }
.tb th { background: #e8ebef; font-weight: 700; }
.katex { font-size: .97em; line-height: 1.0; }
.katex-display { margin: 0; text-align: left; }
.katex-display > .katex { white-space: nowrap; display: inline-block; }
/* chrome snaps any border < .5pt up to .5pt: fake a true hairline by scaling */
.katex .mfrac .frac-line { border-bottom-width: 1pt !important; transform: scaleY(.11); transform-origin: center; }
.katex .sqrt > .sqrt-line { border-top-width: 1pt !important; transform: scaleY(.11); transform-origin: center; }
.katex .overline .overline-line, .katex .underline .underline-line { border-bottom-width: 1pt !important; transform: scaleY(.11); transform-origin: center; }
.katex .hline, .katex .hdashline { border-bottom-width: 1pt !important; transform: scaleY(.11); transform-origin: center; }
""".replace('{PW}', str(config.PAGE_W_MM)).replace('{PH}', str(config.PAGE_H_MM)) \
    .replace('{PAD}', str(config.PAD_MM)).replace('{COLS}', str(config.COLS)) \
    .replace('{ROWS}', str(config.ROWS))

FIT_JS = r"""
<script src="KATEX/katex.min.js"></script>
<script src="KATEX/contrib/auto-render.min.js"></script>
<script>
(function(){
  renderMathInElement(document.body, {
    delimiters: [
      {left: '\\[', right: '\\]', display: true},
      {left: '$', right: '$', display: false}
    ],
    throwOnError: false, strict: false, trust: true, output: 'html'
  });
  var cells=[].slice.call(document.querySelectorAll('.cell'));
  var FIXED = window.__FIXED__ || null;
  var res=[];
  if (FIXED) { cells.forEach(function(c){
      var v=FIXED[c.dataset.id];
      if (typeof v === 'number') { c.style.fontSize = v + 'pt'; }
      else { c.style.fontSize = v.fs + 'pt'; c.style.lineHeight = v.lh; }
  }); }
  cells.forEach(function(c){
    if (FIXED) return;
    var bd=c.querySelector('.bd');
    var lo=2.9, hi=6.4, best=lo;
    for(var k=0;k<24;k++){
      var mid=(lo+hi)/2;
      c.style.fontSize=mid+'pt';
      if(bd.scrollHeight<=bd.clientHeight+0.5){ best=mid; lo=mid; } else { hi=mid; }
    }
    var sz=best;
    c.style.fontSize=sz.toFixed(2)+'pt';
    var guard=0;
    while(bd.scrollHeight>bd.clientHeight+0.5 && guard<60){ sz-=0.03; c.style.fontSize=sz.toFixed(2)+'pt'; guard++; }
    res.push({id:c.dataset.id, size:+sz.toFixed(2)});
  });
  var shrunk=[];
  [].slice.call(document.querySelectorAll('.eq, .sec')).forEach(function(box){
    var k=box.querySelector('.katex');
    var kh=box.querySelector('.katex-html') || k;
    if(!k) return;
    var avail=box.clientWidth-1;
    var w=Math.max(k.getBoundingClientRect().width, kh.getBoundingClientRect().width);
    if(w>avail){
      var fs=parseFloat(getComputedStyle(k).fontSize);
      k.style.fontSize=(fs*avail/w*0.98)+'px';
      shrunk.push(Math.round(w-avail)+'px');
    }
  });
  document.documentElement.setAttribute('data-shrunk', JSON.stringify(shrunk));
  var of=[];
  cells.forEach(function(c){
    var cr=c.getBoundingClientRect();
    var bad=[];
    [].slice.call(c.querySelectorAll('.eq .katex-html, .sec .katex-html, p, table, .tb')).forEach(function(el){
      var r=el.getBoundingClientRect();
      if(r.right>cr.right-0.5){
        bad.push(Math.round(r.right-cr.right)+'px :: '+(el.textContent||'').replace(/\s+/g,' ').slice(0,50));
      }
    });
    if(bad.length) of.push({id:c.dataset.id, n:bad.length, items:bad.slice(0,4)});
  });
  document.documentElement.setAttribute('data-over', JSON.stringify(of));
  document.documentElement.setAttribute('data-fit', JSON.stringify(res));
})();
""".replace('KATEX', KATEX) + '</script>'


def build():
    pages = []
    for pg in range(config.PAGES):
        cells = []
        for j in range(PER_PAGE):
            idx = pg * PER_PAGE + j
            if idx >= len(B):
                break
            blk = B[idx]
            r, c = j % config.COLS, j // config.COLS
            cls = 'cell'
            if r == config.COLS - 1:
                cls += ' lastcol'
            if c == config.ROWS - 1:
                cls += ' lastrow'
            cells.append(
                '<div class="%s" data-id="%s">'
                '<div class="hd"><span class="no">%s</span><span class="tt">%s</span></div>'
                '<div class="bd">%s</div></div>'
                % (cls, blk['id'], blk['no'], blk['title'], render_items(blk['items'])))
        pages.append('<div class="page">%s</div>' % ''.join(cells))
    js = FIT_JS
    if os.path.exists('sizes.json'):
        fixed = json.load(open('sizes.json'))
        js = js.replace('<script>\n(function(){',
                        '<script>window.__FIXED__=%s;</script>\n<script>\n(function(){' % json.dumps(fixed))
    html = ('<!DOCTYPE html><html><head><meta charset="utf-8">'
            '<title>Cheat Sheet</title>'
            '<link rel="stylesheet" href="%s/katex.min.css"><style>%s</style></head><body>'
            '%s%s</body></html>' % (KATEX, CSS, ''.join(pages), js))
    with open(OUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    return OUT_HTML


def topdf(src, dst):
    args = [CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
            '--no-pdf-header-footer', '--run-all-compositor-stages-before-draw',
            '--virtual-time-budget=20000',
            '--print-to-pdf=' + os.path.abspath(dst),
            'file:///' + os.path.abspath(src).replace('\\', '/')]
    r = subprocess.run(args, capture_output=True, text=True)
    print(r.stdout[-300:], r.stderr[-300:])
    return dst


if __name__ == '__main__':
    build()
    topdf(OUT_HTML, OUT_PDF)
    import pymupdf
    d = pymupdf.open(OUT_PDF)
    print('pages', len(d), 'size', d[0].rect)
