"""Check that every card's GUID key (its original Greek, through guid_overrides.txt) is unique, and report how many
notes keep the GUID of the baseline deck (project/cards_current.tsv).  usage: guid_check.py"""
import csv
import os
import sys
import unicodedata
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as P  # noqa: E402

nfc = lambda s: unicodedata.normalize('NFC', s.strip())  # noqa: E731
OV = {}
for line in open(P.GUID_OVERRIDES, encoding='utf-8'):
    if '→' in line:
        old, new = [nfc(x) for x in line.split('→', 1)]
        OV[new] = old
cards = []
for p in P.sentence_paths():
    for line in open(p, encoding='utf-8'):
        if line.strip() and not line.startswith('#'):
            cards.append(nfc(line.split('|')[0]))
keys = [OV.get(g, g) for g in cards]
dup = [k for k, n in Counter(keys).items() if n > 1]
csv.field_size_limit(10 ** 7)
base = [nfc(r['greek']) for r in csv.DictReader(open(P.CARDS_BASELINE, encoding='utf-8'), delimiter='\t',
                                                quoting=csv.QUOTE_NONE)]
base_keys = {OV.get(g, g) for g in base}
kept = sum(1 for k in keys if k in base_keys)
print('cards %d, unique GUID keys %d, duplicates %d; notes keeping a baseline GUID %d of %d; new notes %d; '
      'baseline notes gone %d' % (len(cards), len(set(keys)), len(dup), kept, len(base_keys), len(cards) - kept,
                                  len(base_keys - set(keys))))
for k in dup[:10]:
    print('DUPLICATE', k)
sys.exit(1 if dup else 0)
