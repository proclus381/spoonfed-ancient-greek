"""Dump the checker's view of every card (items, new items, chosen lemmas) to work/tmp/items.json, and query it.

usage: items_dump.py                      (re-run the checker and write the dump, ~35 s)
       items_dump.py q ITEM [ITEM ...]    (cards that use any of the items, e.g. L:πλέω X:gen-time 'πόλις:gen.s.f')
       items_dump.py lemma LEMMA [MAXCH]  (cards with a token of that lemma, up to chapter MAXCH)"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as P  # noqa: E402

OUT = P.scratch('items.json')


def dump():
    import check2 as K
    cards, known, uses = K.run(P.sentence_paths(), quiet=True, show=False)
    rows = []
    for c in cards:
        rows.append({'n': c['n'], 'ch': c['chapter'], 'file': c['file'], 'line': c['line'], 'gr': c['gr'], 'en': c['en'],
                     'src': c['src'], 'new': c['new'], 'items': sorted(c['items']),
                     'lemmas': sorted({ch[0] for ch in c['chosen'] if ch and ch[0] != 'chunk'})})
    json.dump(rows, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    print('wrote', OUT, len(rows), 'cards')


def load():
    return json.load(open(OUT, encoding='utf-8'))


def show(r):
    print('%5d ch%-2d %s:%d [%s] %s | %s | %s' % (r['n'], r['ch'], r['file'], r['line'], ', '.join(r['new']), r['gr'],
                                                 r['en'], r['src']))


if __name__ == '__main__':
    if len(sys.argv) == 1:
        dump()
    elif sys.argv[1] == 'q':
        want = set(sys.argv[2:])
        for r in load():
            if want & set(r['items']):
                show(r)
    elif sys.argv[1] == 'lemma':
        lem = sys.argv[2]
        maxch = int(sys.argv[3]) if len(sys.argv) > 3 else 99
        for r in load():
            if r['ch'] <= maxch and lem in r['lemmas']:
                show(r)
