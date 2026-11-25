"""Options and flags for the information-structure pass (docs/WORD_ORDER_PLAN.md), per card, for the reader to decide.

usage: is_propose.py LO HI OUT.tsv        (venv python, repository root; chapters LO..HI)
Per 3rd-person clause (one finite verb, not εἰμί) with a stated nominative subject phrase:
  out     the subject left out (English with he / she / it / they; '?' = give the English by hand)
  after   the subject moved right after the verb (only when it stands before it)
  before  the subject moved to the front of the clause, the rest in its order (only when it follows the verb)
Per predication S + PRED + ἐστί / εἰσί:  nocop  PRED S
Flags (column 'flags'), from the sentence's own signals:
  OVS       a definite object / dative phrase opens the clause and the subject follows the verb: reads as a contrast
  OLAC      a noun subject and a noun object in one clause (corpus: 8–11% of clauses with a noun object)
  cont      the subject's lemma occurs in the two cards before (a continuing topic)
  item      the subject holds the card's new item
  speech / pres   verb class (speech verb, presentative verb); otherwise an ordinary verb
  μδ        the subject is marked by μέν / δέ (a contrastive topic: stays first)
  pos=before|after   where the subject stands now
Rows 'hand' list clauses the segmenter cannot reorder, with their flags."""
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'project'))
sys.path.insert(0, os.path.join(ROOT, 'work', 'phase3', 'word_order'))
sys.path.insert(0, os.path.join(ROOT, 'work', 'phase3', 'snippet'))
import config as P  # noqa: E402
import check2 as K  # noqa: E402
import propose as PR  # noqa: E402
import snippet_propose as SP  # noqa: E402

SPEECH = {'λέγω', 'φημί', 'εἶπον', 'ἐρωτάω', 'ἔρομαι', 'ἀποκρίνομαι', 'ὑπολαμβάνω', 'βοάω', 'κελεύω', 'καλέω'}
PRES = PR.THETIC | {'εἰσέρχομαι', 'ἀπέρχομαι', 'παραγίγνομαι', 'πάρειμι', 'ἥκω'}


def is_np(p, case):
    return p.typ in ('np', 'npi') and p.case == case


def main():
    LO, HI, OUT = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    cards, known, uses = K.run(P.sentence_paths(), quiet=True, show=False)
    rows, prev = [], []
    for c in cards:
        if not LO <= c['chapter'] <= HI or c['src'] != 'composed':
            prev.append(c)
            continue
        ch, toks, chosen, gr = c['chapter'], c['toks'], c['chosen'], c['gr']
        itoks = set()
        for it in c['new']:
            itoks |= set(c['items'].get(it, []))
        recent = set()
        for p in prev[-2:]:
            recent |= SP.lemmas_of(p)
        bounds, cur = [], [0]
        for i in range(1, len(toks)):
            if gr[toks[i - 1][1]:toks[i][0]].strip():
                bounds.append(cur)
                cur = [i]
            else:
                cur.append(i)
        bounds.append(cur)
        quote = '«' in gr or '“' in gr
        items = ','.join(sorted(c['new']))
        for ix in bounds:
            phs = PR.phrases(ix, chosen, toks)
            bt = [K.bare(toks[i][2]) for i in ix]
            if not phs:
                fin = [i for i in ix if chosen[i] and chosen[i][0] != 'chunk' and chosen[i][1][0] == 'v'
                       and chosen[i][1][4] in 'iso' and chosen[i][1][1] == '3' and chosen[i][0] != 'εἰμί']
                subj = [i for k, i in enumerate(ix[:-1]) if chosen[i] and chosen[i][0] == 'ὁ' and
                        chosen[i][1][0] == 'l' and chosen[i][1][7] == 'n' and chosen[ix[k + 1]] and
                        chosen[ix[k + 1]][0] != 'chunk' and chosen[ix[k + 1]][1][0] == 'n' and
                        chosen[ix[k + 1]][1][7] == 'n']
                if len(fin) == 1 and subj:
                    fl = ['pos=' + ('after' if subj[0] > fin[0] else 'before')]
                    if chosen[fin[0]][0] in SPEECH:
                        fl.append('speech')
                    if any(b in ('μεν', 'δε') for b in bt[:4]):
                        fl.append('μδ')
                    if set(ix) & itoks & {subj[0], subj[0] + 1}:
                        fl.append('item')
                    rows.append((c['n'], ch, 'hand', ' '.join(fl), '', '', gr, c['en'], items))
                continue
            fins = [p for p in phs if p.typ == 'V']
            if len(fins) != 1:
                continue
            V = fins[0]
            tag = V.tag
            S = next((p for p in phs if p.typ in ('np', 'npi') and p.case == 'n' and p is not V), None)
            if V.lemma == 'εἰμί':
                if K.bare(toks[V.idx[-1]][2]) not in PR.COP or set(V.idx) & itoks or getattr(V, 'neg', False):
                    continue
                body = [p for p in phs if p is not V]
                if len(body) == 2 and S is not None and S.typ == 'np':
                    PRd = body[0] if body[1] is S else body[1]
                    if PRd.typ in ('adj', 'npi') and PRd.case == 'n' and not getattr(PRd, 'neg', False):
                        r = SP.build(c, ix, PRd.idx + S.idx, 'nocop', '', set(), c['en'], ch)
                        if r:
                            rows.append(r[:3] + ('',) + r[4:])
                continue
            if tag[1] != '3' or S is None:
                continue
            vpos, spos = ix.index(V.idx[-1]), ix.index(S.idx[0])
            head = next((i for i in reversed(S.idx) if chosen[i] and chosen[i][0] != 'chunk' and
                         chosen[i][1][0] == 'n'), S.idx[-1])
            if not chosen[head] or chosen[head][0] == 'chunk':
                continue
            lem = chosen[head][0]
            g, num = chosen[head][1][6], chosen[head][1][2]
            if g == 'n' and tag[5] != 'p' and not (S.typ == 'np' and any(chosen[i][1][7] == 'n' for i in S.idx
                                                                         if chosen[i] and chosen[i][0] == 'ὁ')):
                continue                                   # a neuter "subject" of an active verb may be the object
            fl = ['pos=' + ('after' if spos > vpos else 'before')]
            if V.lemma in SPEECH:
                fl.append('speech')
            elif V.lemma in PRES:
                fl.append('pres')
            sb = [K.bare(toks[i][2]) for i in ix[spos:spos + 3]]
            if any(b in ('μεν', 'δε') for b in sb):
                fl.append('μδ')
            if lem in recent:
                fl.append('cont')
            if set(S.idx) & itoks:
                fl.append('item')
            objs = [p for p in phs if p is not V and p is not S and p.typ in ('np', 'npi') and p.case in ('a', 'd')]
            if any(p.typ in ('np', 'npi') and any(chosen[i] and chosen[i][0] != 'chunk' and chosen[i][1][0] == 'n'
                                                  for i in p.idx) and p.case == 'a' for p in objs):
                fl.append('OLAC')
            first = phs[0]
            if first is not S and first.typ == 'np' and first.case in ('a', 'd') and spos > vpos:
                fl.append('OVS')
            flags = ' '.join(fl)
            person = lem in SP.PERSON or lem[:1].isupper()
            rest = [i for i in ix if i not in S.idx]
            postpos = any(K.bare(toks[i][2]) in PR.POSTPOS for i in S.idx)
            chunk = any(chosen[i] and chosen[i][0] == 'chunk' for i in S.idx)
            if len(rest) >= 2 and not (quote and V.lemma in ('λέγω', 'φημί')) and not postpos and not chunk:
                r = SP.build(c, ix, rest, 'out', '', set(), SP.en_out(c['en'], lem, g, num, person), ch)
                if r:
                    rows.append(r[:3] + (flags,) + r[4:])
            if spos < vpos and not postpos and not chunk:
                new = [i for i in ix if i not in S.idx]
                k = new.index(V.idx[-1]) + 1
                r = SP.build(c, ix, new[:k] + S.idx + new[k:], 'after', '', set(), c['en'], ch)
                if r:
                    rows.append(r[:3] + (flags,) + r[4:])
            if spos > vpos and not postpos and not chunk:
                lead = []
                for p in phs:                     # a setting before the verb (time, place, participle) stays first
                    if p is V or p is S or not (p.typ in ('adv', 'pp', 'chunk') and ix.index(p.idx[0]) < vpos):
                        break
                    lead += p.idx
                new = lead + S.idx + [i for i in ix if i not in S.idx and i not in lead]
                r = SP.build(c, ix, new, 'before', '', set(), c['en'], ch)
                if r:
                    rows.append(r[:3] + (flags,) + r[4:])
            if not any(r and r[0] == c['n'] for r in rows[-3:]):
                rows.append((c['n'], ch, 'flag', flags, '', '', gr, c['en'], items))
        prev.append(c)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('n\tch\toption\tflags\tnew\tnew_en\told\told_en\titems\n')
        for r in rows:
            f.write('\t'.join(str(x) for x in r) + '\n')
    print('%d rows' % len(rows))


if __name__ == '__main__':
    main()
