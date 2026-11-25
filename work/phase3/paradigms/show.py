"""Cards A..B with their new items.   usage: show.py A B [grep]"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
items = json.load(open(os.path.join(ROOT, 'work', 'tmp', 'items.json'), encoding='utf-8'))
a, b = int(sys.argv[1]), int(sys.argv[2])
g = sys.argv[3] if len(sys.argv) > 3 else ''
for x in items:
    if a <= x['n'] <= b and (not g or g in x['gr'] or g in ' '.join(x['new'])):
        print(x['n'], x['ch'], x['gr'][:75], '|', ' '.join(x['new']))
