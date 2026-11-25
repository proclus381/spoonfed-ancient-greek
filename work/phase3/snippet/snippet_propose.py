"""Options for the snippet pass (docs/WORD_ORDER.md §5–6), per card, for the reader to choose from.

usage: snippet_propose.py LO HI OUT.tsv        (venv python, repository root; chapters LO..HI)
For every 3rd-person clause (one finite verb, not εἰμί) whose stated subject does not hold the card's new item:
  out    the subject left out; English with he / she / it / they (from the syllabus gloss; '?' = check by hand)
  after  the subject moved right after the verb (only when it stands before it)
For every predication S + PRED + ἐστί / εἰσί (copula not the item):
  nocop  PRED S, the copula left out (Smyth §944, §1168)
A default is marked: out when the subject's lemma occurs in the two cards before (a continuing topic) and the clause
keeps at least two words; otherwise after when the subject occurred earlier in the chapter; otherwise none.
OUT: n, ch, option, default (*), new Greek, new English, old Greek, old English, items. A summary line per chapter
gives the figures with the defaults applied (subject left out, stated subject after the verb)."""
import collections
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'project'))
sys.path.insert(0, os.path.join(ROOT, 'work', 'phase3', 'word_order'))
import config as P  # noqa: E402
import check2 as K  # noqa: E402
import propose as PR  # noqa: E402

PERSON = set('''ἄνθρωπος ἀνήρ γυνή παῖς δοῦλος δούλη δεσπότης δέσποινα πατήρ μήτηρ υἱός θυγάτηρ ἀδελφός ἀδελφή πάππος
γέρων γραῦς νεανίας κόρη παρθένος αὐτουργός γεωργός ποιμήν ἄγγελος κῆρυξ βασιλεύς βασίλεια ξένος φίλος φίλη πολίτης
ναύτης ναύκληρος κυβερνήτης στρατηγός στρατιώτης ὁπλίτης πολέμιος ἱερεύς ἰατρός ποιητής ῥήτωρ διδάσκαλος μαθητής
κλέπτης φύλαξ δεσμώτης ἔμπορος πένης πλούσιος σοφός θεός θεά τύραννος ἱκέτης πρέσβυς δικαστής νεκρός τροφός
παιδοτρίβης κιθαριστής γραμματιστής μελοποιός συγγραφεύς ἑταῖρος γίγας λῃστής οἰκέτης ἀστός μέτοικος πρόγονος
σύμμαχος ναύαρχος ἐρέτης σαλπιγκτής χορός γείτων συγγενής ἐπιστάτης βουλευτής ἀλλαντοπώλης παππίας νύμφη πόσις
ἄνασσα κυνηγέτης ἰδιώτης τεχνίτης ἀλαζών γονεύς ἀνόητος δῆμος πτωχός οἰκεῖος φυγάς'''.split())
GLOSS = {}
for f in sorted(os.listdir(os.path.join(ROOT, 'project', 'syllabus'))):
    for l in open(os.path.join(ROOT, 'project', 'syllabus', f), encoding='utf-8'):
        c = [x.strip() for x in l.split('|')]
        if len(c) >= 2 and c[0] and not c[0].startswith(('#', 'L:', 'C:', 'X:')):
            GLOSS.setdefault(K.nfc(c[0]), c[1])
IRREG = {'man': ['men'], 'woman': ['women'], 'child': ['children'], 'person': ['people'], 'ox': ['oxen'],
         'foot': ['feet'], 'boy': ['boys'], 'wolf': ['wolves'], 'thief': ['thieves'], 'sheep': ['sheep']}
DET = {'the', 'a', 'an', 'his', 'her', 'their', 'my', 'our', 'your', 'this', 'that', 'these', 'those'}


def pronoun(gender, number, person):
    if number == 'p':
        return 'they'
    if not person:
        return 'it'
    return 'she' if gender == 'f' else 'he'


def en_out(en, lemma, gender, number, person):
    """replace the subject's English noun phrase by a pronoun; '?' when it cannot be found safely"""
    pr = pronoun(gender, number, person)
    words = re.findall(r"[A-Za-z'-]+|[^A-Za-z'-]+", en)
    heads = set()
    g = GLOSS.get(lemma, '')
    for w in re.findall(r"[A-Za-z'-]+", g)[:3]:
        if w.lower() not in DET and w.lower() not in ('to', 'be', 'one', 'who', 'of'):
            heads |= {w.lower(), w.lower() + 's', w.lower() + 'es'} | set(IRREG.get(w.lower(), []))
            break
    if lemma[:1].isupper():
        heads |= {lemma.lower()}
    idx = [i for i, w in enumerate(words) if w.lower() in heads]
    if not idx:
        if words and words[0] in ('The', 'A'):                 # "The X …": take article + one word
            idx = [2] if len(words) > 2 else []
        if not idx:
            return '?' + en
    i = idx[0]
    gw = {w.lower() for w in re.findall(r"[A-Za-z'-]+", g)}
    while i + 2 < len(words) and words[i + 1] == ' ' and words[i + 2].lower() in gw:   # "slave woman"
        i += 2
    i0 = idx[0]
    j = i0
    k = i0 - 2
    while k >= 0 and words[k + 1].strip() == '' and (words[k].lower() in DET or (k > 0 and words[k].islower()
                                                                                   and words[k - 2].lower() in DET
                                                                                   if k >= 2 else False)):
        j = k
        if words[k].lower() in DET:
            break
        k -= 2
    start = j
    cap = start == 0 or (start >= 1 and words[start - 1].strip() in ('“', '"'))
    rep = pr.capitalize() if cap else pr
    out = ''.join(words[:start]) + rep + ''.join(words[i + 1:])
    # a following "of the X" genitive after the head belongs to the phrase: leave it out too
    out = re.sub(r'^(%s) of (the|his|her|their) [a-z]+' % re.escape(rep), r'\1', out)
    if re.search(r'\b(says|said|asks|asked|cries|replies|answers)\b\s*$', ''.join(words[:start])):
        return '?' + en                                        # speech tag: keep the subject
    if start != 0 and not re.match(r'^(At|In|On|After|Then|Now|Suddenly|At last|Meanwhile|When|There|So|But|And|'
                                   r'Soon|Today|Tomorrow|Yesterday|Next|Already|Still|Often|Again|First|Every)',
                                   en):
        return '?' + out
    return out


def lemmas_of(c):
    return {ch[0] for ch in c['chosen'] if ch and ch[0] != 'chunk'}


def main():
    LO, HI, OUT = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    cards, known, uses = K.run(P.sentence_paths(), quiet=True, show=False)
    rows, summ = [], collections.defaultdict(collections.Counter)
    seen_ch = collections.defaultdict(set)
    prev = []
    for c in cards:
        if not LO <= c['chapter'] <= HI:
            prev.append(c)
            continue
        ch = c['chapter']
        if c['src'] != 'composed':
            prev.append(c)
            continue
        toks, chosen, gr = c['toks'], c['chosen'], c['gr']
        itoks = set()
        for it in c['new']:
            itoks |= set(c['items'].get(it, []))
        recent = set()
        for p in prev[-2:]:
            recent |= lemmas_of(p)
        bounds, cur = [], [0]
        for i in range(1, len(toks)):
            if gr[toks[i - 1][1]:toks[i][0]].strip():
                bounds.append(cur)
                cur = [i]
            else:
                cur.append(i)
        bounds.append(cur)
        quote = '«' in gr or '“' in gr
        for ix in bounds:
            phs = PR.phrases(ix, chosen, toks)
            if not phs:
                # not segmentable: list a 3rd-person clause with a stated article + noun subject for writing by hand
                fin = [i for i in ix if chosen[i] and chosen[i][0] != 'chunk' and chosen[i][1][0] == 'v'
                       and chosen[i][1][4] in 'isom' and chosen[i][1][1] == '3' and chosen[i][0] != 'εἰμί']
                subj = [i for k, i in enumerate(ix[:-1]) if chosen[i] and chosen[i][0] == 'ὁ' and chosen[i][1][0] == 'l'
                        and chosen[i][1][7] == 'n' and chosen[ix[k + 1]] and chosen[ix[k + 1]][0] != 'chunk'
                        and chosen[ix[k + 1]][1][0] == 'n' and chosen[ix[k + 1]][1][7] == 'n' and not (
                            {i, ix[k + 1]} & itoks)]
                if len(fin) == 1 and subj:
                    rows.append((c['n'], ch, 'hand', '', '', '', gr, c['en'], ','.join(sorted(c['new']))))
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
                        new = [i for i in PRd.idx] + [i for i in S.idx]
                        rows.append(build(c, ix, new, 'nocop', '', set(), c['en'], ch))
                        summ[ch]['pred'] += 1
                continue
            if tag[1] != '3':
                continue
            summ[ch]['3p'] += 1
            if S is None:
                summ[ch]['3p out'] += 1
                continue
            vpos = ix.index(V.idx[-1])
            spos = ix.index(S.idx[0])
            if set(S.idx) & itoks and spos < vpos and not any(chosen[i] and chosen[i][0] == 'chunk' for i in S.idx) \
                    and not any(K.bare(toks[i][2]) in PR.POSTPOS for i in S.idx):
                new = [i for i in ix if i not in S.idx]      # the new item is the subject: it may still follow the verb
                k = new.index(V.idx[-1]) + 1
                rows.append(build(c, ix, new[:k] + S.idx + new[k:], 'after', '', set(), c['en'], ch))
            if set(S.idx) & itoks or any(chosen[i] and chosen[i][0] == 'chunk' for i in S.idx) or \
                    any(K.bare(toks[i][2]) in PR.POSTPOS for i in S.idx):
                summ[ch]['subj kept'] += 1
                summ[ch]['subj after kept' if spos > vpos else 'subj before kept'] += 1
                continue
            head = next((i for i in reversed(S.idx) if chosen[i] and chosen[i][0] != 'chunk' and chosen[i][1][0] == 'n'),
                        S.idx[-1])
            if chosen[head][1][6] == 'n' and tag[5] != 'p':      # a neuter "subject" of an active verb may be the object
                summ[ch]['subj kept'] += 1
                summ[ch]['subj after kept' if spos > vpos else 'subj before kept'] += 1
                continue
            lem = chosen[head][0]
            g, num = chosen[head][1][6], chosen[head][1][2]
            person = lem in PERSON or lem[:1].isupper()
            cont = lem in recent
            rest = [i for i in ix if i not in S.idx]
            opts = []
            if len(rest) >= 2 and not (quote and V.lemma in ('λέγω', 'φημί')):
                en = en_out(c['en'], lem, g, num, person)
                opts.append(('out', rest, en))
            if spos < vpos:
                new = [i for i in ix if i not in S.idx]
                k = new.index(V.idx[-1]) + 1
                new = new[:k] + S.idx + new[k:]
                opts.append(('after', new, c['en']))
            default = 'out' if cont and opts and opts[0][0] == 'out' else \
                ('after' if lem in seen_ch[ch] and spos < vpos else '')
            for name, new, en in opts:
                rows.append(build(c, ix, new, name, '*' if name == default else '', set(), en, ch))
            summ[ch]['subj cand'] += 1
            summ[ch]['def ' + (default or 'keep')] += 1
            summ[ch]['def keep ' + ('after' if spos > vpos else 'before')] += default == ''
            seen_ch[ch].add(lem)
        prev.append(c)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('n\tch\toption\tdefault\tnew\tnew_en\told\told_en\titems\n')
        for r in rows:
            if r:
                f.write('\t'.join(str(x) for x in r) + '\n')
    for ch in sorted(summ):
        s = summ[ch]
        n3 = s['3p']
        out = s['3p out'] + s['def out']
        after = s['subj after kept'] + s['def after'] + s['def keep after']
        stated = n3 - out
        print('ch%-2d 3p %3d; with defaults: subject left out %3.0f%%, stated after %3.0f%%; predications %d' % (
            ch, n3, 100 * out / max(n3, 1), 100 * after / max(stated, 1), s['pred']))


def build(c, ix, new, name, dflt, copidx, en, ch):
    toks, chosen, gr = c['toks'], c['chosen'], c['gr']
    cap = toks[ix[0]][2][:1].isupper() and not PR.is_name(chosen[ix[0]])
    seq = []
    for i in new:
        w = toks[i][2]
        if cap and i == ix[0]:
            w = w[:1].lower() + w[1:]
        t = chosen[i][1] if chosen[i] and chosen[i][0] != 'chunk' else None
        seq.append((w, t, False))
    words = PR.render(seq)
    if cap and words:
        words[0] = words[0][:1].title() + words[0][1:]
    # rebuild: the clause's span replaced by the new words
    a, b = toks[ix[0]][0], toks[ix[-1]][1]
    newgr = gr[:a] + ' '.join(words) + gr[b:]
    if K.nfc(newgr) == K.nfc(gr):
        return None
    return (c['n'], ch, name, dflt, newgr, en, gr, c['en'], ','.join(sorted(c['new'])))


if __name__ == '__main__':
    main()
