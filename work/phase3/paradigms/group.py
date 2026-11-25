"""Group, within each chapter, the cards that introduce cells of one inflection scheme (or one tense-mood-voice
of the verb), so the learner meets a paradigm's forms one after the other.

usage: group.py OPS_OUT [SKIP_FILE]      (repository root; work/tmp/items.json current)
A card moves only (1) within its chapter, (2) earlier, to just after the last card of its scheme's group, (3) if
it is a composed card whose one new item is a grammar key, and (4) if every other item it uses is introduced
before its new place. Moving a card earlier never takes an item from a card it passes. SKIP_FILE lists Greek of
cards not to move (moves the checker rejected). Ops: deck_edit.py MOVE lines, in order."""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
items = json.load(open(os.path.join(ROOT, 'work', 'tmp', 'items.json'), encoding='utf-8'))
skip = set()
if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
    skip = {l.strip() for l in open(sys.argv[2], encoding='utf-8') if l.strip()}


def scheme(k):
    if k.startswith(('L:', 'C:', 'X:', 'S:')) or ':' not in k:
        return None
    return k.split(':', 1)[0]


pos = {c['n']: float(c['n']) for c in items}
intro = {}
for c in items:
    for it in c['new']:
        intro.setdefault(it, c['n'])
by_ch = {}
for c in items:
    by_ch.setdefault(c['ch'], []).append(c)
ops, moved = [], []
for ch, cards in sorted(by_ch.items()):
    last = {}                                   # scheme → card n at the end of its group
    for c in cards:
        new = c['new']
        g = [x for x in new if scheme(x)]
        if len(new) != 1 or len(g) != 1:
            for x in g:
                last[scheme(x)] = c['n']
            continue
        s = scheme(g[0])
        if s not in last:
            last[s] = c['n']
            continue
        a = last[s]
        adjacent = not any(pos[a] < pos[d['n']] < pos[c['n']] for d in cards)
        deps = [x for x in c['items'] if x not in new]
        ok = (not adjacent and c['src'] == 'composed' and c['gr'] not in skip and
              all(x in intro and pos[intro[x]] < pos[a] + 1e-9 or x in intro and intro[x] == a for x in deps))
        if ok:
            pos[c['n']] = pos[a] + 1e-6
            agr = next(d['gr'] for d in cards if d['n'] == a)
            ops.append('MOVE %s >> AFTER %s' % (c['gr'], agr))
            moved.append((ch, s, c['gr'], agr))
        last[s] = c['n']
open(sys.argv[1], 'w', encoding='utf-8').write('\n'.join(ops) + '\n')
print(len(ops), 'moves')
import collections  # noqa: E402
print(collections.Counter(m[0] for m in moved))
