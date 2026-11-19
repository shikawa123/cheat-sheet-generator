# -*- coding: utf-8 -*-
"""Extract text (and optionally page images) from the user's lecture notes.

Usage:
  python extract.py <folder-or-file> [more paths...] > dump.txt
  python extract.py --images <folder-or-file> [more paths...]   # also renders PNGs to ./_slides/
"""
import os, sys, glob, subprocess

try:
    import pymupdf
except ImportError:
    pymupdf = None


def iter_pdfs(paths):
    for p in paths:
        if os.path.isdir(p):
            yield from sorted(glob.glob(os.path.join(p, '**', '*.pdf'), recursive=True))
        elif p.lower().endswith('.pdf'):
            yield p
        else:
            print('SKIP (not pdf):', p, file=sys.stderr)


def pdf_text(path):
    """pdftotext -layout if available (fast, keeps columns), else pymupdf."""
    try:
        r = subprocess.run(['pdftotext', '-layout', path, '-'],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout
    except FileNotFoundError:
        pass
    if pymupdf is None:
        return '(install pymupdf or poppler pdftotext to extract text)'
    d = pymupdf.open(path)
    return '\n'.join('--- page %d ---\n%s' % (i + 1, pg.get_text())
                     for i, pg in enumerate(d))


def pdf_images(path, outdir='_slides'):
    if pymupdf is None:
        return
    os.makedirs(outdir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(path))[0]
    d = pymupdf.open(path)
    for i, pg in enumerate(d):
        pix = pg.get_pixmap(dpi=110)
        pix.save(os.path.join(outdir, '%s_p%02d.png' % (stem, i + 1)))


def main():
    args = sys.argv[1:]
    do_img = '--images' in args
    paths = [a for a in args if a != '--images']
    if not paths:
        print(__doc__)
        return
    for f in iter_pdfs(paths):
        print('=' * 20, os.path.basename(f), '=' * 20)
        print(pdf_text(f))
        if do_img:
            pdf_images(f)
            print('[images rendered to ./_slides/]', file=sys.stderr)


if __name__ == '__main__':
    main()
