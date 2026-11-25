"""Edit the deck's sentence files with operations anchored on a card's Greek text (not on line numbers).

usage: python3 deck_edit.py OPS.txt [--dry]

One operation per line (blank lines and # comments ignored):
  MOVE    <greek of a card> >> BEFORE|AFTER <greek of an anchor card>
  INSERT  <greek | english | source[ | extras]> >> BEFORE|AFTER <greek of an anchor card>
  REPLACE <greek of a card> == <greek | english | source[ | extras]>
  EXTRAS  <greek of a card> == <new column 4, e.g. +X:e-than>      (sets column 4, Greek unchanged)
  DELETE  <greek of a card>                                         (removes the note; its review history is lost)
The anchor may be in another chapter file: MOVE takes the line out of its file and puts it next to the anchor.
MOVE keeps the note's GUID (the Greek is unchanged). REPLACE appends 'original → new' to guid_overrides.txt
when the Greek changes, so the note keeps its GUID (same rule as apply.py). INSERT creates a new note.
Every Greek text must match exactly one card line (NFC, whitespace-trimmed)."""
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as P  # noqa: E402

nfc = lambda s: unicodedata.normalize('NFC', s.strip())  # noqa: E731
dry = '--dry' in sys.argv
ops_path = [a for a in sys.argv[1:] if not a.startswith('--')][0]

files = {os.path.basename(p): open(p, encoding='utf-8').read().split('\n') for p in P.sentence_paths()}
OV = {}
for line in open(P.GUID_OVERRIDES, encoding='utf-8'):
    if '→' in line:
        old, new = [nfc(x) for x in line.split('→', 1)]
        OV[new] = old
overrides = []


def greek_of(line):
    return nfc(line.split('|')[0])


def find(gr):
    gr = nfc(gr)
    hits = [(f, i) for f, L in files.items() for i, l in enumerate(L)
            if l.strip() and not l.startswith('#') and greek_of(l) == gr]
    if len(hits) != 1:
        sys.exit('%d cards match %r' % (len(hits), gr))
    return hits[0]


def place(line, where, anchor):
    f, i = find(anchor)
    files[f].insert(i if where == 'BEFORE' else i + 1, line)
    return f


log = []
for raw in open(ops_path, encoding='utf-8'):
    raw = raw.rstrip('\n')
    if not raw.strip() or raw.lstrip().startswith('#'):
        continue
    op, rest = raw.split(None, 1)
    if op in ('MOVE', 'INSERT'):
        what, tgt = rest.split(' >> ', 1)
        where, anchor = tgt.split(None, 1)
        assert where in ('BEFORE', 'AFTER'), raw
        if op == 'MOVE':
            f, i = find(what)
            line = files[f].pop(i)
            g = place(line, where, anchor)
            log.append('moved %s from %s to %s' % (greek_of(line)[:50], f, g))
        else:
            if any(l.strip() and not l.startswith('#') and greek_of(l) == greek_of(what) for L in files.values() for l in L):
                sys.exit('already in the deck: ' + what)
            if greek_of(what) in set(OV.values()):        # a rewritten note's original Greek: its GUID is taken
                sys.exit('the original Greek of a rewritten note (same GUID): ' + what)
            g = place(what.strip(), where, anchor)
            log.append('inserted %s in %s' % (greek_of(what)[:50], g))
    elif op == 'REPLACE':
        old, new = rest.split(' == ', 1)
        f, i = find(old)
        oldgr, newgr = greek_of(files[f][i]), greek_of(new)
        if oldgr != newgr and any(l.strip() and not l.startswith('#') and greek_of(l) == newgr
                                  for L in files.values() for l in L):
            sys.exit('already in the deck: ' + newgr)
        if oldgr != newgr and newgr in set(OV.values()) and OV.get(oldgr, oldgr) != newgr:
            sys.exit('the original Greek of another rewritten note (same GUID): ' + newgr)
        files[f][i] = new.strip()
        if oldgr != newgr:
            overrides.append('%s → %s' % (OV.get(oldgr, oldgr), newgr))
            OV[newgr] = OV.get(oldgr, oldgr)
        log.append('replaced in %s: %s' % (f, newgr[:50]))
    elif op == 'DELETE':
        f, i = find(rest.strip())
        gone = files[f].pop(i)
        log.append('deleted from %s: %s' % (f, greek_of(gone)[:50]))
    elif op == 'EXTRAS':
        gr, extras = rest.split(' == ', 1) if ' == ' in rest else (rest.rstrip()[:-2].rstrip(), '')
        f, i = find(gr)
        cols = [c.strip() for c in files[f][i].split('|')]
        while len(cols) < 3:
            cols.append('composed')
        cols = cols[:3] + ([extras.strip()] if extras.strip() else [])
        files[f][i] = ' | '.join(cols)
        log.append('extras in %s: %s' % (f, greek_of(files[f][i])[:50]))
    else:
        sys.exit('unknown operation: ' + raw)
print('\n'.join(log))
if dry:
    print('(dry run, nothing written)')
    sys.exit()
for f, L in files.items():
    open(os.path.join(P.SENTENCES, f), 'w', encoding='utf-8').write('\n'.join(L))
if overrides:
    with open(P.GUID_OVERRIDES, 'a', encoding='utf-8') as g:
        for o in overrides:
            g.write(o + '\n')
print('%d operations, %d override lines' % (len(log), len(overrides)))
