"""Lemmas (and chunks) known before card N: what a new card inserted after card N may use.
usage: known_at.py N [M]    (repository root; work/tmp/items.json) — with M, only those introduced in (M, N]"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
items = json.load(open(os.path.join(ROOT, 'work', 'tmp', 'items.json'), encoding='utf-8'))
n = int(sys.argv[1])
m = int(sys.argv[2]) if len(sys.argv) > 2 else 0
out = []
for c in items:
    if m < c['n'] <= n:
        out += [x for x in c['new'] if x.startswith(('L:', 'C:', 'X:'))]
print(' '.join(x[2:] if x.startswith('L:') else x for x in out))
