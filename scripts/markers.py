# -*- coding: utf-8 -*-
"""Optional colour-coding pass (pastel highlighter bands, same colour = same kind).

Marker syntax usable directly in content.py text:
  ==..==  yellow  definitions / key concepts
  ~~..~~  green   decisions & when-to-use
  @@..@@  orange  thresholds & interpretation values
  ##..##  red     test decisions & traps
  %%..%%  blue    method / statistic names (auto-highlighted from BLUE list)
  {{..}}  purple  procedures & step counts

Customize PAIRS and BLUE to the user's subject; delete entries freely.
"""
import re

PAIRS = [
    # (exact old substring, new substring with markers) — hand-placed marks
]

# starter keyword list — replace with subject-specific method names
BLUE = [
    'mean', 'median', 'mode', 'variance', 'standard deviation', 'covariance',
    'correlation', 'regression', 'hypothesis', 'p-value', 'z-test', 't-test',
    'population', 'sample frame', 'confidence interval', 'critical value',
]

_PROTECT = re.compile(r'(==.*?==|~~.*?~~|@@.*?@@|##.*?##|%%.*?%%|\{\{.*?\}\})')
_TERMS = sorted(set(BLUE), key=len, reverse=True)
_BLUE_RX = re.compile(
    r'(?<![A-Za-z0-9])(?:' + '|'.join(_TERMS) + r')(?![A-Za-z0-9])', re.IGNORECASE)


def _mark_plain(seg):
    tokens = _PROTECT.split(seg)
    for i in range(0, len(tokens), 2):
        if tokens[i]:
            tokens[i] = _BLUE_RX.sub(lambda m: '%%' + m.group(0) + '%%', tokens[i])
    return ''.join(tokens)


def transform(text):
    for old, new in PAIRS:
        text = text.replace(old, new)
    parts = text.split('$')
    for i in range(0, len(parts), 2):        # mark only non-math segments
        parts[i] = _mark_plain(parts[i])
    return '$'.join(parts)
