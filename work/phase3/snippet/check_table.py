"""Check a rewrite table (old Greek, new Greek, new English or '=', rule) before it is applied.

usage: python3 -I check_table.py TABLE.tsv ALL_RAW MEL1_DIR MEL2_DIR
Reports, per row: the new Greek is already a card or another note's original (deck_edit.py would refuse it); a clause
of 4+ words occurs verbatim in the books (rule 1, a copyright question: keep the order and change or add a word that
sets the card apart; never fall back to a worse order). Shorter matches are not reported: a 3-word clause is no
copyright issue. Prints counts and the offending rows only (no book text). Exit status 1 if any row fails."""
import os
import re
import sys
import unicodedata as ud

tab, raw_p, m1, m2 = sys.argv[1:5]
nfc = lambda s: ud.normalize('NFC', s.strip())  # noqa: E731
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
G = re.compile(r"[Ͱ-Ͽἀ-῿]+")


def bare(s):
    s = ud.normalize('NFD', s.lower())
    return ''.join(c for c in s if ud.category(c) != 'Mn').replace('ς', 'σ')


def clauses(s):
    for cl in re.split(r'[·,;.«»:!;?]', s):
        b = ' '.join(bare(x) for x in G.findall(cl))
        if len(b.split()) >= 3:
            yield cl.strip(), b


txt = open(raw_p, encoding='utf-8').read()
for d in (m1, m2):
    txt += ' '.join(open(os.path.join(d, f), encoding='utf-8').read() for f in sorted(os.listdir(d)) if f.endswith('.txt'))
book = ' ' + ' '.join(bare(x) for x in G.findall(txt)) + ' '
deck, orig = set(), set()
sdir = os.path.join(ROOT, 'project', 'sentences')
for f in os.listdir(sdir):
    for l in open(os.path.join(sdir, f), encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            deck.add(nfc(l.split('|')[0]))
OV = {}
for l in open(os.path.join(ROOT, 'project', 'guid_overrides.txt'), encoding='utf-8'):
    if '→' in l:
        orig.add(nfc(l.split('→')[0]))
        OV[nfc(l.split('→')[1])] = nfc(l.split('→')[0])
bad, n, seen = 0, 0, set()
for l in open(tab, encoding='utf-8'):
    if not l.strip() or l.startswith('#'):
        continue
    old, new = [nfc(x) for x in l.rstrip('\n').split('\t')[:2]]
    n += 1
    why = []
    if old not in deck:
        why.append('old Greek not in the deck')
    if (new in deck or new in orig or new in seen) and OV.get(old, old) != new:   # back to its own original is fine
        why.append('already a card or an original')
    seen.add(new)
    for cl, b in clauses(new):
        hit = book.count(' ' + b + ' ')
        if hit and len(b.split()) >= 4:
            why.append('book clause %r (%d): change or add a word, keep the order' % (cl, hit))
    if why:
        bad += 1
        print('%s  <- %s' % (new, '; '.join(why)))
print('%d rows, %d with problems' % (n, bad))
sys.exit(1 if bad else 0)
