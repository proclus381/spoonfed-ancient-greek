"""Compare each note's new items with the baseline, matching notes by GUID key (original Greek through
guid_overrides.txt), so moved and rewritten cards are compared with themselves.
usage: regress_notes.py [BASELINE.tsv]   (default project/cards_current.tsv; uses work/tmp/items.json from items_dump.py)"""
import csv
import json
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as P  # noqa: E402

nfc = lambda s: unicodedata.normalize('NFC', s.strip())  # noqa: E731
OV = {}
for line in open(P.GUID_OVERRIDES, encoding='utf-8'):
    if '→' in line:
        old, new = [nfc(x) for x in line.split('→', 1)]
        OV[new] = old
csv.field_size_limit(10 ** 7)
bf = sys.argv[1] if len(sys.argv) > 1 else P.CARDS_BASELINE
base = {OV.get(nfc(r['greek']), nfc(r['greek'])): r for r in
        csv.DictReader(open(bf, encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE)}
cur = json.load(open(P.scratch('items.json'), encoding='utf-8'))
changed = moved = 0
for r in cur:
    k = OV.get(nfc(r['gr']), nfc(r['gr']))
    b = base.get(k)
    new = ', '.join(r['new'])
    if b is None:
        print('NEW NOTE  %5d ch%-2d [%s] %s' % (r['n'], r['ch'], new, r['gr'][:70]))
        continue
    if int(b['chapter']) != r['ch']:
        moved += 1
        print('MOVED     %5d ch%s->ch%d [%s] %s' % (r['n'], b['chapter'], r['ch'], new, r['gr'][:70]))
    if b['new'] != new:
        changed += 1
        print('NEW ITEMS %5d ch%-2d [%s] => [%s] %s' % (r['n'], r['ch'], b['new'], new, r['gr'][:60]))
print('notes %d, moved %d, new items changed %d' % (len(cur), moved, changed))
