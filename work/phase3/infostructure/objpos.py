"""Definite objects and word order (docs/WORD_ORDER_PLAN.md; corpus: with no stated subject a definite object
stands before the verb about half the time but opens the clause only 2–4% of the time).

usage: objpos.py LO HI      (venv python, repository root)
Lists 3rd-person clauses with no stated subject and an article + noun accusative object:
  OPEN  the object opens the clause (marked: needs a reason inside the card)
  ADJ   adjunct (adverb or prepositional phrase) + verb + object: candidates for adjunct–object–verb"""
import os
import sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'project'))
sys.path.insert(0, os.path.join(ROOT, 'work', 'phase3', 'word_order'))
import config as P  # noqa: E402
import check2 as K  # noqa: E402
import propose as PR  # noqa: E402

LO, HI = int(sys.argv[1]), int(sys.argv[2])
cards, known, uses = K.run(P.sentence_paths(), quiet=True, show=False)
for c in cards:
    if c['src'] != 'composed' or not LO <= c['chapter'] <= HI:
        continue
    toks, chosen, gr = c['toks'], c['chosen'], c['gr']
    bounds, cur = [], [0]
    for i in range(1, len(toks)):
        if gr[toks[i - 1][1]:toks[i][0]].strip():
            bounds.append(cur)
            cur = [i]
        else:
            cur.append(i)
    bounds.append(cur)
    for ix in bounds:
        phs = PR.phrases(ix, chosen, toks)
        if not phs:
            continue
        V = [p for p in phs if p.typ == 'V']
        if len(V) != 1 or V[0].tag[1] != '3' or V[0].lemma == 'εἰμί':
            continue
        V = V[0]
        if any(p.typ in ('np', 'npi', 'pron') and p.case == 'n' for p in phs):
            continue
        objs = [p for p in phs if p.typ == 'np' and p.case == 'a']
        if not objs:
            continue
        O = objs[0]
        k_o, k_v = phs.index(O), phs.index(V)
        if k_o == 0:
            print('OPEN %s %s | %s [%s]' % (c['n'], gr, c['en'], ','.join(sorted(c['new']))))
        elif k_o > k_v and k_v > 0 and phs[k_v - 1].typ in ('adv', 'pp') and not getattr(V, 'neg', False):
            print('ADJ  %s %s | %s [%s]' % (c['n'], gr, c['en'], ','.join(sorted(c['new']))))
