# -*- coding: utf-8 -*-
"""Content for the cheat sheet — one block per cell.

Item DSL:
  ('h', 'SECTION TITLE')                     section chip
  ('p', 'prose **bold** $math$ ==mark==')    paragraph
  ('e', r'latex', 'note explaining params')  display formula + note
  ('t', [[row], [row]], 'c9')                small table
  ('note', 'banner text')                    tinted inline banner

See SKILL.md for the full authoring rules.
"""

B = []

# ------------------------------------------------ EXAMPLE BLOCK (edit/replace)
B.append(dict(
    id='T1', no='1', title='TOPIC ONE',
    items=[
        ('h', 'Definitions'),
        ('p', '**Key concept** = replace this sentence with content extracted from the '
              'user\'s lecture notes. Inline math like $x_i$ and marks like ==important== '
              'or %%method-name%% are supported.'),
        ('h', 'Core formula'),
        ('e', r'\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i',
         'x̄ = sample mean; xᵢ = i-th observation; n = number of observations'),
        ('p', 'Explain when to use it, its thresholds and a one-line worked example.'),
        ('h', 'WHICH ONE?'),
        ('p', '==Option A== when …; ==Option B== when … (decision mini-block).'),
    ]))
