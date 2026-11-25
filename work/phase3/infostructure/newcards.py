"""Word order of the paradigm cards (2026-11-25): proposals by docs/WORD_ORDER_PLAN.md §2a and §6, for review.

usage: newcards.py NEWCARDS.txt ISP.tsv OUT.tsv      (venv python, repository root)
NEWCARDS: the Greek of the cards to treat; ISP: is_propose.py's options for the whole deck.
Per card, in this order:
  S   a stated subject: kept first when it holds the card's new item (the card's topic) or in a speech tag;
      left out ('out') when it continues from the cards before or a noun object stands beside it (the One
      Lexical Argument Constraint); otherwise after the verb ('after'); presentative verbs: after.
  O   a definite (article) object or dative phrase opening a clause with no stated subject before the verb moves
      right after the verb; an anarthrous complement stays before it (Σῖτον παρέχει τῇ κόρῃ). Not when the phrase
      has πᾶς, ἅπας or a demonstrative, or the card has μέν / δέ.
  V   a vocative opening the card moves after the first word or phrase, or to the end of a short utterance;
      invocations of gods and prayers (ἵλεως ἴσθι) keep it first.
Final acutes and graves are set for the new neighbours. OUT: n, ch, rules, old Greek, new Greek, old English,
new English, extras."""
import os
import re
import sys
import unicodedata as ud

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'project'))
os.chdir(os.path.join(ROOT, 'project'))
import config as P  # noqa: E402
import check2 as K  # noqa: E402

new = set(l.strip() for l in open(sys.argv[1], encoding='utf-8') if l.strip())
isp = {}
for l in open(sys.argv[2], encoding='utf-8'):
    r = l.rstrip('\n').split('\t')
    if r[0] == 'n':
        continue
    isp.setdefault(r[6], {})[r[2]] = (r[3].split(), r[4], r[5])
cards, known, uses = K.run(P.sentence_paths(), quiet=True, show=False)
ALL = set(known)
ART = {'ο', 'η', 'το', 'του', 'τησ', 'τω', 'τη', 'τον', 'την', 'οι', 'αι', 'τα', 'των', 'τοισ', 'ταισ', 'τουσ', 'τασ',
       'τοιν', 'ταιν'}
DEM = {'πᾶς', 'ἅπας', 'σύμπας', 'οὗτος', 'ἐκεῖνος', 'τοιοῦτος', 'τοσοῦτος', 'τηλικοῦτος', 'ὅδε', 'αὐτός'}
GODS = re.compile(r'θε[οέ]|Ζε[ῦυ]|Δήμητ|ἥλιε|σῶτερ|Ἄρτεμ|Ἀπολλ|Ποσειδ|Ἀθην')
PUNCT = re.compile(r'[,.;·!?»“”]')


def accents(words):
    """final acute → grave before another word; grave → acute before punctuation or at the end"""
    out = []
    for i, w in enumerate(words):
        last = i == len(words) - 1 or PUNCT.search(w[-1:])
        d = ud.normalize('NFD', w)
        core = re.sub(r'[^\w̓̔́̀͂ͅ]+$', '', d)
        tail = d[len(core):]
        if not last:
            core2 = re.sub('́([^αεηιουωΑΕΗΙΟΥΩ]*)$', '̀\\1', core)
        else:
            core2 = re.sub('̀([^αεηιουωΑΕΗΙΟΥΩ]*)$', '́\\1', core)
        if not last and re.search('[αεηιουω]', ud.normalize('NFD', re.sub('.*́', '', core) if '́' in core
                                                            else '')):
            core2 = core
        if K.bare(w).strip('.,;·!?»«“”') in ('τι', 'τισ', 'τινα', 'τινοσ', 'τινι', 'τινεσ', 'τινων', 'τισι', 'τινασ'):
            core2 = core                                   # the interrogative τίς never takes a grave
        out.append(ud.normalize('NFC', core2 + tail))
    return out


def cap(w):
    return w[:1].upper() + w[1:] if w else w


def low(w, name):
    return w if name else w[:1].lower() + w[1:]


HINTS = {}


def analyse(gr, ch):
    h = {}
    for f, v in HINTS.items():
        for w in re.findall(r'[\w\u0300-\u036f]+', ud.normalize('NFC', gr)):
            if K.bare(w) == K.bare(f):
                h[w] = v
    items, toks, chosen, probs = K.card_items(gr, ALL, ch, (), h)
    return toks, chosen


def clause_spans(gr, toks):
    spans, cur = [], [0]
    for i in range(1, len(toks)):
        if PUNCT.search(gr[toks[i - 1][1]:toks[i][0]]):
            spans.append(cur)
            cur = [i]
        else:
            cur.append(i)
    spans.append(cur)
    return spans


def tag(chosen, i):
    c = chosen[i]
    return c[1] if c and isinstance(c[1], str) else ''


def lem(chosen, i):
    c = chosen[i]
    return c[0] if c else ''


def finite(t):
    return t[:1] == 'v' and t[4:5] in 'isom'


def fix_object(gr, ch):
    """O: move a definite oblique phrase that stands before the verb, in a clause with no stated subject before
    the verb, to after the verb (and after a subject standing right after it)"""
    toks, chosen = analyse(gr, ch)
    if any(K.bare(t[2]) in ('μεν', 'δε') for t in toks):
        return gr, False
    for sp in clause_spans(gr, toks):
        v = next((i for i in sp if finite(tag(chosen, i))), None)
        if v is None:
            continue
        pre = [i for i in sp if i < v]
        if any(K.bare(toks[i][2]) in ('ο', 'η', 'οι', 'αι') and tag(chosen, i)[7:8] == 'n' or
               tag(chosen, i)[:1] in 'npam' and tag(chosen, i)[7:8] == 'n' for i in pre):
            continue                                       # a stated subject before the verb
        if any(lem(chosen, i) in ('ὅς', 'ὅσπερ', 'ὅστις') or K.bare(toks[i][2]) in (
                'οτε', 'επει', 'εαν', 'ινα', 'οτι', 'ει', 'ωσ', 'οταν', 'επειδη') for i in pre):
            continue                                       # a relative or subordinate clause
        if lem(chosen, v) == 'εἰμί':
            continue                                       # predications: not this rule
        i0 = next((i for i in pre if K.bare(toks[i][2]) in ART), None)
        if i0 is None or tag(chosen, i0)[7:8] not in 'agd' and K.bare(toks[i0][2]) not in ('το', 'τα'):
            continue
        PREP = ('εν', 'εκ', 'εξ', 'εισ', 'προσ', 'απο', 'αφ', 'υπο', 'υφ', 'δια', 'επι', 'μετα', 'παρα', 'περι', 'προ',
                'μεχρι', 'εγγυσ', 'πλησιον', 'ανευ', 'ενεκα', 'αντι', 'υπερ', 'κατα', 'συν', 'αμφι', 'εωσ', 'εξω', 'ενδον')
        if any(K.bare(toks[i][2]) in PREP for i in pre if i0 - 2 <= i < i0):
            continue                                       # a prepositional phrase: a setting
        if i0 > sp[0] and lem(chosen, i0 - 1) in DEM:
            continue                                       # πᾶσαν τὴν ἡμέραν, τοῦτον τὸν …
        case, num = tag(chosen, i0)[7] or 'a', tag(chosen, i0)[2]
        if K.bare(toks[i0][2]) in ('το', 'τα'):
            case = 'a'

        def agrees(i):
            return any(t[7:8] == case and t[2:3] == num or t[7:8] in 'na' and case == 'a' and t[6:7] == 'n' and
                       t[2:3] == num for l, t, x in (K.analyses(toks[i][2]) or []))
        last = i0
        for i in range(i0 + 1, v):
            if agrees(i) and K.bare(toks[i][2]) not in ART:
                last = i
        end = last
        while end + 1 < v and K.bare(toks[end + 1][2]) in ART and tag(chosen, end + 1)[7:8] == 'g':
            k = end + 2                                    # a dependent genitive: τὸν ψόφον τῶν (ταχέων) κυνῶν
            while k < v and any(t[7:8] == 'g' for l, t, x in (K.analyses(toks[k][2]) or [])):
                k += 1
            if k == end + 2:
                break
            end = k - 1
        if tag(chosen, last)[:1] == 'v' and last + 1 < v and K.bare(toks[last + 1][2]) in ART:
            j = last + 1                                   # a participle's own object: τοῖς ὁρῶσι τὸν χορόν
            k = j + 1
            while k < v and tag(chosen, k)[:1] != 'n':
                k += 1
            if k < v:
                end = max(end, k)
        np = list(range(i0, end + 1))
        if any(lem(chosen, i) in DEM for i in np):
            continue
        before = [i for i in pre if i < i0] + [i for i in pre if i > end]
        after = [i for i in sp if i > v]
        subj = []
        if after and K.bare(toks[after[0]][2]) in ('ο', 'η', 'οι', 'αι'):
            k = 1
            while k < len(after) and tag(chosen, after[k])[7:8] == 'n':
                k += 1
            subj = after[:k]
        order = before + [v] + subj + np + after[len(subj):]
        idx = {i: k for k, i in enumerate(sp)}
        names = {i: toks[i][2][:1].isupper() and lem(chosen, i)[:1].isupper() for i in sp}
        neww = [low(toks[i][2], names[i]) for i in order]
        a, b = toks[sp[0]][0], toks[sp[-1]][1]
        if not gr[:a].strip(' «“'):
            neww[0] = cap(neww[0])
        seg = ' '.join(accents(neww))
        return gr[:a] + seg + gr[b:], True
    return gr, False


def fix_vocative(gr):
    m = re.match(r'^(«?)Ὦ ([^,]+), (.+?)([.;!]?»?)$', gr)
    if not m:
        return gr, False
    q, voc, rest, end = m.groups()
    if GODS.search(voc) or re.search(r'ἵλε[ωῳ]', rest) or 'βασιλεῦ' in voc:
        return gr, False
    rw = rest.split()
    if len(rw) <= 2 and ',' not in rest:
        out = '%s%s, ὦ %s%s' % (q, cap(rest), voc, end)
    else:
        k = 1
        b0 = K.bare(rw[0])
        if b0 in ART or b0 in ('εν', 'εκ', 'εισ', 'περι', 'προσ', 'απο', 'υπο', 'δια', 'επι', 'μετα', 'παρα') or \
                b0 == 'δια' and K.bare(rw[1]) == 'τι':
            k = 2
            while k < len(rw) - 1 and K.bare(rw[k - 1]) in ART:
                k += 1
        if b0 == 'δια' and len(rw) > 1 and K.bare(rw[1]) == 'τι':
            k = 2
        if b0 in ('ου', 'ουκ', 'ουχ', 'μη', 'μηκετι', 'ουκετι', 'μηδεν') and len(rw) > 1:
            k = 2
        if k >= len(rw) - 1:
            out = '%s%s, ὦ %s%s' % (q, cap(rest), voc, end)
            return ' '.join(accents(out.split(' '))), True
        head, tail = ' '.join(rw[:k]), ' '.join(rw[k:])
        out = '%s%s, ὦ %s, %s%s' % (q, cap(head), voc, tail, end)
    words = accents(out.split(' '))
    return ' '.join(words), True


KEEP_SUBJECT = {                                   # generic statements: the subject is the topic
    'Ὁ θεὸς παντὶ ἀνθρώπῳ σῖτον παρέχει.',
}
AFTER_INSTEAD = {'Αἱ πόλεις μεγάλας δυνάμεις ἔχουσιν.'}
rows = []
for c in cards:
    gr = c['gr']
    if gr not in new or c['src'] != 'composed':
        continue
    en, rules, g2, en2 = c['en'], [], gr, c['en']
    HINTS.clear()
    HINTS.update(c['hints'])
    opts = isp.get(gr, {})
    flags = set()
    for o, (fl, ng, ne) in opts.items():
        flags |= set(fl)
    choice = None
    has_subject = re.search(r'(^|[\s«“])(Ὁ|ὁ|Ἡ|ἡ|Οἱ|οἱ|Αἱ|αἱ|Τὸ|τὸ|Τὰ|τὰ)\s', gr)
    imp3 = any(re.match(r'^V\w*m\w*:3[sp]$', x) for x in c['new'])
    dual = any(x.startswith('Dual:') for x in c['new'])
    if opts and 'hand' not in opts and 'speech' not in flags and has_subject and not imp3 and not dual \
            and gr not in KEEP_SUBJECT:
        before = 'pos=before' in flags
        if 'item' in flags:
            choice = 'after' if 'pres' in flags and before else None
        elif 'pres' in flags:
            choice = 'after' if before else None
        elif ('OLAC' in flags or 'cont' in flags) and 'out' in opts and not opts['out'][2].startswith('?') \
                and gr not in AFTER_INSTEAD:
            choice = 'out'
        elif before:
            choice = 'after'
        if choice and choice in opts:
            g2, en2 = opts[choice][1], opts[choice][2]
            rules.append('S:' + choice)
    g3, o = fix_object(g2, c['chapter']) if not dual else (g2, False)
    if o:
        rules.append('O')
    g4, v = fix_vocative(g3)
    if v:
        rules.append('V')
    if g4 != gr:
        rows.append((c['n'], c['chapter'], ' '.join(rules), gr, g4, en, en2, ' '.join(
            '@%s' % h if not hv[0] and not hv[1] else '@%s%s%s' % (h, ('=' + hv[0]) if hv[0] else '',
                                                                 (':' + '.'.join(hv[1])) if hv[1] else '')
            for h, hv in c['hints'].items())))
with open(sys.argv[3], 'w', encoding='utf-8') as out:
    out.write('n\tch\trules\told\tnew\told_en\tnew_en\textras\n')
    for r in rows:
        out.write('\t'.join(str(x) for x in r) + '\n')
import collections  # noqa: E402
print(len(rows), 'cards to change;', collections.Counter(x for r in rows for x in r[2].split()))
