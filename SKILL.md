---
name: cheat-sheet-generator
description: Generate a dense, print-ready A4 exam cheat sheet from the user's own lecture notes (PDFs/PPT). Closed-loop print tuning (KaTeX math, exact page fit, optional colour-coded keyword system). Use when the user asks for a cheat sheet / exam reference sheet / formula sheet from their course materials, and asks how many pages/cells the sheet should have.
---

# Cheat Sheet Generator

Turn a folder of lecture notes into a maximally dense, print-perfect A4 cheat sheet.
The **only inputs the user must provide**:

1. **Path to their lecture notes** (folder or list of PDF/PPT files, one file per lecture/topic).
2. **Layout**: how many pages and how many cells per page (default: 1 page A4 landscape, 5 columns × 2 rows = 10 cells, one lecture per cell).

Everything else is produced by you (the agent) following the workflow below.

> Privacy rule: never write the user's name, student ID, institution or course code into the
> generated sheet or repo unless the user explicitly asks for a title line. Content comes only
> from the notes the user provides in this session.

## Deliverable

A single PDF (default `cheatsheet.pdf`) at exact page size, 100% print scale, no clipping,
every cell filled to within ~1 mm of its bottom edge.

## Assets you need once

- **KaTeX offline dist**: run `npm install katex` (or download the dist) so that the folder
  `katex/package/dist` exists next to the scripts. The HTML references
  `katex/package/dist/katex.min.css` + `.min.js` — no network needed at print time.
- **Chrome** (headless) for print-to-PDF. `build.py` looks it up via `shutil.which` and common
  install paths; override `CHROME` if needed.
- Python packages: `pymupdf`. Optional: `pdftotext` (poppler) for faster text extraction.

## Workflow

### 1. Confirm inputs
Ask for (or detect) the notes folder and the layout. Compute `cells = pages × cols × rows`
and check the note count matches (one lecture per cell is the default; let the user merge/split).

### 2. Extract content
- Run `python scripts/extract.py "<notes-folder>" > dump.txt` — dumps per-file text
  (pdftotext -layout when available, else pymupdf) and optionally renders slide images.
- **Math must be transcribed from the rendered slides, never from raw text extraction**
  (pdftotext garbles formulas). Render pages to images (extract.py `--images` flag) and read
  them to verify every formula in standard textbook notation before writing it into content.

### 3. Write `scripts/content.py`
One block per cell, using the item DSL (see `scripts/content_template.py`):

| tag | meaning | notes |
|-----|---------|-------|
| `('h', title)` | section chip (dark inline chip) | merges with a following short `'p'` or `'e'` on one line |
| `('p', text)` | prose paragraph | supports `**bold**`, `*italic*`, `==yellow==`, `~~green~~`, `@@orange@@`, `##red##`, `%%blue%%`, `{{purple}}`, and `$inline math$` |
| `('e', latex, note)` | display formula (KaTeX) + right-hand note | note explains every parameter; split wide formulas into two rows so notes stay large |
| `('t', rows, 'cN')` | small table | first row = header |
| `('note', text)` | tinted inline banner | e.g. worked-exercise steps |

Rules that make it dense and usable:
- Every formula parameter is explained in its note. Formulas sit flush left; the note fills
  the remaining width.
- Solve one or more worked examples per high-yield topic and print the full answer steps —
  exam short answers usually mirror them.
- End each block with a "WHICH …?" decision mini-block (when to use which test/distribution/
  method) — the single highest-value content for multiple-choice questions.
- Use `\sum\nolimits` inside fractions to halve formula height. Split multi-part formulas
  (cases, matrices) onto their own full-width rows (`WIDE` auto-detected).

### 4. (Optional) purpose tags — `scripts/purpose.py`
`PURPOSE` maps a unique prefix of an equation note → a short "what is this for" tag that is
prepended to the note in a distinct colour. Start from the empty dict and add one entry per
formula. Keep tags ≤ 8 words, in the user's language.

### 5. (Optional) colour-coded keywords — `scripts/markers.py`
`PAIRS` = exact `(old, new)` replacements for hand-placed highlight bands;
`BLUE` = keyword regex list auto-highlighted as "method names" (question keywords).
Recommended 6-colour semantic system (pastel highlighter bands, eye-friendly):
yellow = definitions · green = decisions/when-to-use · orange = thresholds &
interpretation · red = test decisions & traps · blue = method/statistic names ·
purple = procedures/steps. Adapt the keyword list to the user's subject.

### 6. Build + closed-loop print tuning
Screen layout ≠ print layout, so never trust the browser autofit alone:

```bash
python scripts/build.py        # writes cheatsheet.html + prints cheatsheet.pdf
python scripts/tune.py         # measures the PRINTED PDF (span bboxes), rebalances per-cell
python scripts/finalize.py     # per-cell line-height bisection: largest lh that still fits
python scripts/lock35.py       # optional: lock every cell to one uniform font size
```

- `tune.py`/`finalize.py` measure each cell's bottom gap from the PDF text spans and adjust
  per-cell `font-size` / `line-height` (stored in `sizes.json`). Iterate until all gaps are
  0.3–1.2 mm and none negative (negative = clipped content).
- If a cell still overflows at the minimum: shrink `.katex` em size or `.eqp` (note) em size
  slightly, then re-run. Never let content clip.
- Chrome print quirks: borders < 0.5 pt snap up to 0.5 pt (hairlines are faked with
  `transform: scaleY(.11)` — see CSS); always print with
  `--no-pdf-header-footer --virtual-time-budget=20000` and absolute paths.
- Verify the final PDF: page count == requested pages, page size exact, no horizontal
  overflow (`data-over` attribute in the HTML), and render a page image to visually check.

### 7. Deliver
Present the PDF. Include a colour legend when the highlight system is on, and remind the
user to print at **100% scale**, colour on, "background graphics" enabled.
