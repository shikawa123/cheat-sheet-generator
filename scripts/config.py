# -*- coding: utf-8 -*-
"""Layout configuration — the only place to change page geometry."""

PAGE_W_MM = 297          # A4 landscape
PAGE_H_MM = 210
PAD_MM = 6.5             # outer safe border (printers clip ~5mm otherwise)
COLS = 5
ROWS = 2                 # cells per page = COLS * ROWS, one lecture per cell
PAGES = 1
FONT_LOCK = None         # e.g. 3.5 -> every cell locked to 3.5 pt; None = autofit
