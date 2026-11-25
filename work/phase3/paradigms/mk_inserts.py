"""Turn new paradigm cards into deck_edit.py INSERT operations, each placed after its anchor card.

usage: mk_inserts.py NEW.tsv OPS.txt        (repository root; anchors numbered as in work/tmp/items.json)
NEW.tsv: anchor card number <TAB> Greek <TAB> English [<TAB> extras]     (# comments allowed)
Rows with the same anchor follow each other in the order given (the 2nd goes after the 1st new card, …), so a
paradigm's new cards stand together right after the card that introduced their sibling."""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
cards = {c['n']: c for c in json.load(open(os.path.join(ROOT, 'work', 'tmp', 'items.json'), encoding='utf-8'))}
last = {}
ops = []
for line in open(sys.argv[1], encoding='utf-8'):
    if not line.strip() or line.startswith('#'):
        continue
    p = line.rstrip('\n').split('\t')
    n, gr, en = (int(p[0]) if p[0].isdigit() else p[0].strip()), p[1].strip(), p[2].strip()
    ex = p[3].strip() if len(p) > 3 else ''
    anchor = last.get(n, cards[n]['gr'] if isinstance(n, int) else n)   # an anchor may be given as its Greek
    ops.append('INSERT %s | %s | composed%s >> AFTER %s' % (gr, en, (' | ' + ex) if ex else '', anchor))
    last[n] = gr
open(sys.argv[2], 'w', encoding='utf-8').write('\n'.join(ops) + '\n')
print(len(ops), 'INSERT operations')
