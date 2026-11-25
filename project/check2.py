# -*- coding: utf-8 -*-
"""Companion checker (v3).
    python3 check2.py [-q] [--cover] sentences/ch01.txt [sentences/ch02.txt ...]   (files in deck order)

Card file lines:   greek | english | source [| +X:item +X:item2 ...]
For every card: analyse each word (forms_extra.txt > generated paradigms of the syllabus words >
treebank lexicon), compute its items (L:lemma, grammar keys, C:phrases, X:constructions declared in
column 4), and report: new items, n+1 violations, items used before their syllabus chapter,
unknown forms (= probably misspelt), words that are not in the syllabus."""
import json, os, re, sys, unicodedata as ud
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
GREEK = 'Ͱ-Ͽἀ-῿'
WORD = re.compile(r"[%s̀-ͯ]+᾽?" % GREEK)
ACC, GRV, CIRC = '́', '̀', '͂'


def nfc(s): return ud.normalize('NFC', s)


def bare(w):
    d = ud.normalize('NFD', w.lower())
    return ''.join(c for c in d if not ud.combining(c) and c != '᾽').replace('ς', 'σ')


def variants(w):
    """lookup variants: as is, lower-cased first letter, grave→acute, enclitic double accent removed"""
    out = [w]
    if w[:1].isupper():
        out.append(nfc(w[0].lower() + w[1:]))
    more = []
    for v in out:
        d = ud.normalize('NFD', v).replace(GRV, ACC)
        more.append(nfc(d))
        acc = [i for i, c in enumerate(d) if c in (ACC, CIRC)]
        if len(acc) == 2:                                   # ἄνθρωπός (ἐστιν) → ἄνθρωπος
            more.append(nfc(d[:acc[1]] + d[acc[1] + 1:]))
    for v in more:
        if v not in out:
            out.append(v)
    return [v.rstrip('᾽') for v in out] + [v for v in out if v.endswith('᾽')]


# ---------------------------------------------------------------- data
LEX = json.load(open(os.path.join(HERE, 'tb', 'lexicon.json'), encoding='utf-8'))
ALIAS = {'ἀποθνῄσκω': 'ἀποθνήσκω', 'οἴομαι': 'οἶμαι', 'θάλασσα': 'θάλαττα', 'γίνομαι': 'γίγνομαι', 'γινώσκω': 'γιγνώσκω', 'πράσσω': 'πράττω',
         'φυλάσσω': 'φυλάττω', 'ἐλάσσων': 'ἐλάττων', 'ἥσσων': 'ἥττων', 'τάσσω': 'τάττω',
         'κηρύσσω': 'κηρύττω', 'γλῶσσα': 'γλῶττα', 'σφάζω': 'σφάττω', 'ταράσσω': 'ταράττω',
         'ἡμεῖς': 'ἐγώ', 'ὑμεῖς': 'σύ', 'ἑαυτοῦ': 'ἑαυτόν', 'σεαυτοῦ': 'σεαυτόν',
         'ἐμαυτοῦ': 'ἐμαυτόν', 'εἶπον': 'λέγω', 'οὕτως': 'οὕτω', 'ἵλαος': 'ἵλεως'}


def lem(l):
    l = re.sub(r'[#\d]+$', '', l).replace('(ς)', '')
    l = nfc(ud.normalize('NFD', l).replace(GRV, ACC))
    return ALIAS.get(l, l)


EXTRA = {}
p = os.path.join(HERE, 'forms_extra.txt')
if os.path.exists(p):
    for line in open(p, encoding='utf-8'):
        line = line.split('#')[0].strip()
        if '=' in line:
            f, v = line.split('=', 1)
            EXTRA[nfc(f.strip())] = [a.split() for a in v.split('|') if a.strip()]

DUALX = {}                        # forms_dual.txt: dual forms (added to the other analyses, not overriding them)
p = os.path.join(HERE, 'forms_dual.txt')
if os.path.exists(p):
    for line in open(p, encoding='utf-8'):
        line = line.split('#')[0].strip()
        if '=' in line:
            f, v = line.split('=', 1)
            DUALX.setdefault(nfc(f.strip()), []).extend(a.split() for a in v.split('|') if a.strip())

SYL, EN, CHUNKS, CLASS, XITEMS, NAMES = {}, {}, [], [], {}, set()
XLEMMA = {}                       # sense items: X:sense-… → the word whose new sense it is
XHINT = {}                        # sense items: short Cloze hint (the explanation is EN)
PART_CH = {}                      # (lemma, principal part) → chapter whose word list gives it
for fn in sorted(os.listdir(os.path.join(HERE, 'syllabus'))):
    m = re.match(r'ch(\d\d)\.txt$', fn)
    if not m:
        continue
    ch = int(m.group(1))
    for line in open(os.path.join(HERE, 'syllabus', fn), encoding='utf-8'):
        line = line.split('#')[0].strip()
        if '|' not in line:
            continue
        cols = [x.strip() for x in line.split('|')]
        head, en = cols[0], cols[1]
        cl = cols[2] if len(cols) > 2 else ''
        if head.startswith('C:'):
            variants_ = [v.strip() for v in head[2:].split(' / ')]
            name = nfc('C:' + variants_[0])
            for v in variants_:
                CHUNKS.append((tuple(bare(t) for t in WORD.findall(v)), name, ch))
            EN[name] = en
        elif head.startswith('X:'):
            XITEMS[head] = ch
            EN[head] = en
            if cl.startswith('lemma='):              # a later sense: X:sense-… | explanation | lemma=χειμών hint=winter
                lm, _, hn = cl.partition(' hint=')
                XLEMMA[head] = nfc(lm.split('=', 1)[1].strip())
                XHINT[head] = hn.strip() or en
        else:
            for h in head.split(','):
                h = nfc(h.strip())
                SYL.setdefault(h, ch)
                EN.setdefault('L:' + h, en)
                if en == '(name)':
                    NAMES.add(h)
                if cl:
                    CLASS.append((h, cl))
                    for _w in cl.split():
                        if _w.split('=')[0] in ('fut', 'aorp', 'pf', 'pfm'):
                            PART_CH.setdefault((h, _w.split('=')[0]), ch)
CHUNKS.sort(key=lambda c: -len(c[0]))
FREE_LEMMAS = {'ὁ'}


def _opts(words):
    o = {}
    for w in words:
        k, _, v = w.partition('=')
        if k == 'g':
            o['gender'] = v
        elif k == 'impf':
            o['impf'] = False if v == '0' else nfc(v)
        elif k in ('aor', 'aor2', 'aor_mid', 'raor'):
            o[k] = nfc(v).replace('·', '|')            # δι·ῆλθον: prefix before the augment
        elif k in ('fut', 'aorp', 'pf', 'pfm'):          # principal parts (book 2); a final ! = learnt as a new stem
            o[k] = nfc(v).rstrip('!').replace('·', '|')
        elif k in ('short', 'long', 'mid', 'sa'):
            o[k] = True
        elif k in ('pre', 'base', 'eimi'):
            o[k] = nfc(v)
        elif k in ('gen', 'acc', 'voc', 'neut', 'cmp', 'sup'):
            o[k] = nfc(v)
    return o


IMPF = {}                         # augmented imperfect stems (compounds, irregular augments): impf.txt
for line in open(os.path.join(HERE, 'impf.txt'), encoding='utf-8'):
    line = line.split('#')[0].strip()
    if '=' in line:
        a, b = [nfc(x.strip()) for x in line.split('=', 1)]
        IMPF[a] = b


# verbs whose future is not “aorist stem + ω” although the aorist is sigmatic (ἀκούσομαι, βοήσομαι, καλῶ …):
# no automatic future for them or their compounds — the syllabus gives it (fut=…)
NO_AUTO_FUT = ('ἀκούω', 'βοάω', 'γελάω', 'σιγάω', 'σιωπάω', 'θαυμάζω', 'πλέω', 'πνέω', 'καλέω', 'ᾄδω', 'οἰμώζω',
               'αινέω', 'βαδίζω', 'πηδάω', 'σπουδάζω', 'ἁρπάζω', 'ρέω', 'χέω', 'νέω', 'δέω', 'τελέω', 'ἀπολαύω',
               'κλαίω', 'θέω', 'πίπτω', 'δάκνω', 'εἰκάζω')
PREFIXES = set('ανα απο δια εισ εκ εξ εν εμ εγ επι κατα μετα παρα περι προ προσ συν συμ συγ συλ υπερ υπο αντι αμφι απ αν κατ επ παρ υπ δι μετ αφ καθ εφ επαν υφ μεθ ανθ'.split()) | {''}
PARTS = {}                        # lemma → {'fut': spec, 'aorp': …, 'pf': …, 'pfm': …} (explicit principal parts)
IRR_PART = set()                  # (lemma, part) given with ! : the stem is an item of its own
for _h, _cl in CLASS:
    for _w in _cl.split():
        _k, _, _v = _w.partition('=')
        if _k in ('fut', 'aorp', 'pf', 'pfm'):
            PARTS.setdefault(_h, {})[_k] = nfc(_v).rstrip('!').replace('·', '|')
            if _v.endswith('!'):
                IRR_PART.add((_h, _k))
FUT_CTR = {}                      # lemma → contract class of its future (μενῶ: ε)
BASE = {}                         # compound → simple verb whose principal parts it shares (ἀναβαίνω → βαίνω)
for _h, _cl in CLASS:
    for _w in _cl.split():
        if _w.startswith('base='):
            BASE[_h] = nfc(_w[5:])
HAS_STRONG = {h for h, cl in CLASS if any(x in cl for x in ('aor2=', 'aor_mid=', 'raor=')) or 'irr' in cl.split()}


def auto_future(h, o):
    """regular future from a sigmatic 1st aorist: ἔλυσα → λύσω, ἐδεξάμην → δέξομαι, ἐνόμισα → νομιῶ"""
    a = o.get('aor')
    if h in PARTS and 'fut' in PARTS[h] or any(bare(h).endswith(bare(x)) and bare(h)[:-len(bare(x))] in PREFIXES
                                               for x in NO_AUTO_FUT):
        return None
    if not a:                                           # ποιέω, πιστεύω … listed without an aorist: by rule
        import parts
        if h in HAS_STRONG or not bare(h).endswith(('εω', 'αω', 'οω', 'ευω', 'εομαι', 'αομαι', 'οομαι', 'ευομαι')):
            return None
        return parts.regular_parts(h).get('fut')
    a1, _, a1s = a.partition('/')
    if not a1s or bare(a1s)[-1:] not in ('σ', 'ψ', 'ξ'):
        return None
    dep = bare(a1).endswith('αμην')
    if bare(h).endswith(('ιζω', 'ιζομαι')) and bare(a1s).endswith('ισ'):
        import morph
        st = morph.strip(a1s)[:-1]
        return st + ('οῦμαι' if dep else 'ῶ')
    return a1s + ('ομαι' if dep else 'ω')


NO_AUTO_AORP = ('καλέω', 'αἱρέω', 'ὁράω', 'αινέω', 'δέω', 'τελέω', 'γελάω', 'ἐάω', 'δοκέω', 'πλέω', 'πνέω', 'χέω', 'ρέω',
                'νέω', 'θέω', 'ζάω', 'χράομαι', 'δράω', 'κτάομαι', 'πλήττω', 'σπάω', 'ἐράω', 'αἰδέομαι', 'ἡγέομαι',
                'ἀφικνέομαι', 'θεάομαι', 'ἰάομαι', 'μιμέομαι', 'ὠνέομαι', 'εὔχομαι', 'μάχομαι', 'ἐργάζομαι',
                'ἀγωνίζομαι', 'λογίζομαι', 'χαρίζομαι', 'ἀσπάζομαι', 'βιάζομαι', 'δέομαι', 'οἰκτίρω', 'ὠθέω')


def _nobreath(w):
    return nfc(''.join(c for c in ud.normalize('NFD', w) if c not in '\u0313\u0314'))


def auto_aorp(h, o, w=()):
    """aorist passive by rule: for regular verbs in -έω -άω -όω -εύω -ίζω -άζω -ττω (ἐποιήθην, ἐπαιδεύθην, ἐνομίσθην,
    ἐπράχθην), and for a compound whose simple verb has one (ἀπ-επέμφθην from ἐπέμφθην)"""
    import morph
    if h in PARTS and 'aorp' in PARTS[h]:
        return None
    base = o.get('base') or BASE.get(h)
    a = o.get('aor') or o.get('aor2') or ''
    if base and base in PARTS and 'aorp' in PARTS[base] and nfc(h) != nfc(base):
        bs = PARTS[base]['aorp']
        b1, _, bst = bs.partition('/')
        b1 = b1.replace('|', '')
        if not bst and bare(b1).startswith('ε') and bare(b1)[1:2] not in 'αεηιουω':
            bst = morph.strip(b1)[1:-2]
        pre_st = nfc(h)[:len(nfc(h)) - len(nfc(base))]
        pre_aug = a.partition('|')[0] if '|' in a else (o.get('pre') or '')
        if bst and pre_st and pre_aug and bare(h).endswith(bare(base)[1:]):
            if o.get('pre') and '|' not in a:          # cmpd lines give the full prefix: elide it before the augment
                pre_aug = pre_st if bare(pre_st)[-1:] not in 'αεο' or bare(pre_st) in ('περι', 'προ') else pre_st[:-1]
            return '%s|%s/%s' % (pre_aug, _nobreath(morph.strip(b1)), pre_st + _nobreath(morph.strip(bst)))
        return None
    if 'irr' in w or h in HAS_STRONG or '|' in a or (h in IMPF and '|' in IMPF[h]) or \
            any(bare(h).endswith(bare(x)) and bare(h)[:-len(bare(x))] in PREFIXES for x in NO_AUTO_AORP):
        return None
    if not bare(h).endswith(('εω', 'αω', 'οω', 'ευω', 'εομαι', 'αομαι', 'οομαι', 'ευομαι', 'ιζω', 'αζω', 'ιζομαι',
                             'αζομαι', 'ττω')):
        return None
    try:
        import parts
        return parts.regular_parts(h).get('aorp')
    except Exception:
        return None


def auto_pf(h, o, w=()):
    """perfect active by rule, like auto_pfm (πεποίηκα; ἀπο|δέδωκα from δέδωκα)"""
    if h in PARTS and 'pf' in PARTS[h]:
        return None
    base = o.get('base') or BASE.get(h)
    if base and base in PARTS and 'pf' in PARTS[base] and nfc(h) != nfc(base):
        bp = PARTS[base]['pf'].replace('|', '')
        pre_st = nfc(h)[:len(nfc(h)) - len(nfc(base))]
        if not pre_st or not bare(h).endswith(bare(base)[1:]):
            return None
        if bare(bp)[:1] in 'αεηιουω' and bare(pre_st)[-1:] in 'αεο' and bare(pre_st) not in ('περι', 'προ'):
            pre_st = pre_st[:-1]
        if bare(bp)[:1] in 'αεηιουω' and bare(pre_st)[-1:] == 'κ':
            pre_st = pre_st[:-1] + 'ξ'
        return '%s|%s' % (pre_st, _nobreath(bp) if bare(bp)[:1] in 'αεηιουω' else bp)
    a = o.get('aor') or o.get('aor2') or ''
    if 'irr' in w or h in HAS_STRONG or '|' in a or (h in IMPF and '|' in IMPF[h]) or bare(h).endswith('ομαι') or \
            any(bare(h).endswith(bare(x)) and bare(h)[:-len(bare(x))] in PREFIXES for x in NO_AUTO_AORP):
        return None
    if not bare(h).endswith(('εω', 'αω', 'οω', 'ευω', 'ιζω', 'αζω')):
        return None
    try:
        import parts
        return parts.regular_parts(h).get('pf')
    except Exception:
        return None


def auto_pfm(h, o, w=()):
    """perfect middle by rule (πεποίημαι, πεπαίδευμαι, νενόμισμαι) for the same verbs as auto_aorp, and for a compound
    whose simple verb has one (ἀπο|δέδομαι, ἀν|έγνωσμαι)"""
    import morph
    if h in PARTS and 'pfm' in PARTS[h]:
        return None
    base = o.get('base') or BASE.get(h)
    if base and base in PARTS and 'pfm' in PARTS[base] and nfc(h) != nfc(base):
        bp = PARTS[base]['pfm'].replace('|', '')
        pre_st = nfc(h)[:len(nfc(h)) - len(nfc(base))]
        if not pre_st or not bare(h).endswith(bare(base)[1:]):
            return None
        if bare(bp)[:1] in 'αεηιουω' and bare(pre_st)[-1:] in 'αεο' and bare(pre_st) not in ('περι', 'προ'):
            pre_st = pre_st[:-1]
        if bare(bp)[:1] in 'αεηιουω' and bare(pre_st)[-1:] == 'κ':
            pre_st = pre_st[:-1] + 'ξ'
        return '%s|%s' % (pre_st, _nobreath(bp) if bare(bp)[:1] in 'αεηιουω' else bp)
    a = o.get('aor') or o.get('aor2') or ''
    if 'irr' in w or h in HAS_STRONG or '|' in a or (h in IMPF and '|' in IMPF[h]) or \
            any(bare(h).endswith(bare(x)) and bare(h)[:-len(bare(x))] in PREFIXES for x in NO_AUTO_AORP):
        return None
    if not bare(h).endswith(('εω', 'αω', 'οω', 'ευω', 'εομαι', 'αομαι', 'οομαι', 'ευομαι', 'ιζω', 'αζω', 'ιζομαι',
                             'αζομαι')):
        return None
    try:
        import parts
        return parts.regular_parts(h).get('pfm')
    except Exception:
        return None


COMPOUND_OF = {}                  # (lemma, form) → irregular simple verb whose forms' keys it shares
NUMI = set()                     # verbs in -νυμι: they share the keys of δείκνυμι


def _base_forms(base):
    return [(f, t) for f, v in EXTRA.items() for l, t in v if l == base and t[0] == 'v']


MID_LEMMAS = {bare(h) for h, cl in CLASS if bare(h).endswith('ομαι')} | {bare(k) for k in SYL if bare(k).endswith('ομαι')}


def gen_index():
    import morph, morph2
    entries = []
    for h, cl in CLASS:
        w = cl.split()
        kind = w[0]
        o = _opts(w[1:])
        if kind == 'v' and h in IMPF:
            o['impf'] = IMPF[h]
        if kind == 'v' and 'reg' in w:                   # regular principal parts by rule
            import parts
            for k, v in parts.regular_parts(h, o.get('pre')).items():
                if k == 'fut' and h in PARTS and 'fut' in PARTS[h]:
                    continue
                o.setdefault(k, v)
        pre = o.pop('pre', None)
        base = o.pop('base', None)
        eimi = o.pop('eimi', None)
        if eimi:                                         # compound of ἔρχομαι: ἄπειμι, ἀπιέναι, ἀπιών, ἀπῇα …
            entries.append((h, 'cmpd', dict(pre=eimi, base_forms=_base_forms('εἶμι'), base='εἶμι')))
        if kind == 'cmpd':                               # compound of an irregular verb: ἀποδίδωμι = ἀπο + δίδωμι
            entries.append((h, 'cmpd', dict(pre=pre, base_forms=_base_forms(base), base=base)))
            if 'raor' in o:                              # κατέστην beside κατέστησα
                entries.append((h, 'raor', {'spec': o.pop('raor')}))
            if o.get('fut'):
                entries.append((h, 'fut', dict(spec=o['fut'], mid=True)))
            ap = o.get('aorp') or auto_aorp(h, dict(o, base=base, pre=pre), w)
            if ap:
                entries.append((h, 'aorp', dict(spec=ap)))
            pm = o.get('pfm') or auto_pfm(h, dict(o, base=base, pre=pre), w)
            if pm:
                entries.append((h, 'pfm', dict(spec=pm)))
            pa = o.get('pf') or auto_pf(h, dict(o, base=base, pre=pre), w)
            if pa:
                entries.append((h, 'pf', dict(spec=pa)))
            continue
        if kind == 'adjus':
            entries.append((h, 'adjus', {}))
            continue
        if kind in ('neus', 'nis'):
            entries.append((h, kind, {'gender': o['gender']} if kind == 'nis' and 'gender' in o else {}))
            continue
        if kind == 'numi':                               # δείκνυμι, ζεύγνυμι, ῥήγνυμι: all go like δείκνυμι
            entries.append((h, 'numi', dict(aor=o.get('aor'), impf=o.get('impf') if isinstance(o.get('impf'), str)
                                            else IMPF.get(h))))
            NUMI.add(h)
            if o.get('fut'):
                entries.append((h, 'fut', dict(spec=o['fut'], mid=True)))
            if o.get('aorp'):
                entries.append((h, 'aorp', dict(spec=o['aorp'])))
            if o.get('pfm'):
                entries.append((h, 'pfm', dict(spec=o['pfm'])))
            if o.get('pf'):
                entries.append((h, 'pf', dict(spec=o['pf'])))
            continue
        if kind in ('v', 'vx'):                          # vx: present forms hand-made (πλέω), other tenses generated
            fut = o.pop('fut', None) or ('irr' not in w and kind == 'v' and auto_future(h, o)) or None
            aorp = o.pop('aorp', None) or auto_aorp(h, o, w)
            if aorp:
                entries.append((h, 'aorp', dict(spec=aorp)))
            pfm = o.pop('pfm', None) or auto_pfm(h, o, w)
            if pfm:
                entries.append((h, 'pfm', dict(spec=pfm)))
            pf = o.pop('pf', None) or auto_pf(h, o, w)
            if pf:
                entries.append((h, 'pf', dict(spec=pf)))
            if fut:
                entries.append((h, 'fut', dict(spec=fut, mid=o.get('mid', False), long=o.get('long', False),
                                               short=o.get('short', False))))
                if morph2.fut_class(fut):
                    FUT_CTR[h] = morph2.fut_class(fut)
        if 'cmp' in o or 'sup' in o:                     # regular comparison of an adjective
            entries.append((h, 'adjdeg', {k: o.pop(k) for k in ('cmp', 'sup') if k in o}))
        if 'raor' in o:                                  # root aorist: raor=ἔβην/βη/βα
            entries.append((h, 'raor', {'spec': o.pop('raor')}))
            if kind == 'raor':
                continue
        if kind == 'adj2':
            entries.append((h, 'adj', dict(two_endings=True)))
        elif kind == 'n3':
            entries.append((h, 'n3', dict(gen=o['gen'], gender=o.get('gender', 'm'),
                                          **{k: o[k] for k in ('acc', 'voc') if k in o})))
        elif kind == 'adj3':
            entries.append((h, 'adj3', dict(neut=o['neut'], gen=o['gen'])))
        elif kind in ('nes', 'adjes'):
            entries.append((h, kind, {}))
        elif kind in ('adj', 'n', 'v'):
            if kind != 'n':
                o.pop('gender', None)
            if kind != 'v':
                for k in ('impf', 'aor', 'aor2', 'aor_mid', 'mid') + (('short', 'long', 'sa') if kind != 'n' else ()):
                    o.pop(k, None)
            elif bare(h)[:-1] + 'ομαι' in MID_LEMMAS:      # πείθω / πείθομαι are two syllabus words: no automatic passive
                o['auto_pass'] = False
            entries.append((h, kind, o))
    for h, kind, o in entries:
        if kind == 'cmpd':
            for f, t in morph2.compound(o['pre'], o['base_forms']):
                COMPOUND_OF[(h, f)] = o['base']
    return morph.index(entries)


GEN = gen_index()
IRR_AOR1 = {h for h, cl in CLASS if 'aor=' in cl and 'irr' in cl.split()}
STEMCH = {}                      # S:lemma (the aorist of a verb, learnt as a new form) → chapter
GEN_LEMMAS = {l for v in GEN.values() for l, t in v}

# ---------------------------------------------------------------- grammar keys
CASE = {'n': 'nom', 'g': 'gen', 'd': 'dat', 'a': 'acc', 'v': 'voc'}
# words whose forms are learnt one by one (pronouns, irregular nouns/adjectives): key = lemma:case.num.gender
SPECIFIC = {'αὐτός', 'ἑαυτόν', 'ἐγώ', 'σύ', 'τίς', 'τις', 'οὗτος', 'ἐκεῖνος', 'ὅδε', 'ὅς', 'ἐμαυτόν', 'τηλικοῦτος',
            'σεαυτόν', 'ἀλλήλων', 'ὅστις', 'οὐδείς', 'μηδείς', 'εἷς', 'δύο', 'τρεῖς', 'τέτταρες', 'πᾶς',
            'ἀνήρ', 'πατήρ', 'μήτηρ', 'θυγάτηρ', 'γυνή', 'Ζεύς', 'βοῦς', 'ναῦς', 'ἄλλος', 'τοιοῦτος',
            'τοσοῦτος'}
THIRD_DECL = {'γίγας'} | {h for h, cl in CLASS if cl.split()[:1] == ['n3']}
SPECIFIC3 = {'ἀνήρ', 'πατήρ', 'μήτηρ', 'θυγάτηρ', 'γυνή', 'Ζεύς', 'βοῦς', 'ναῦς', 'παῖς', 'εἷς', 'τρεῖς', 'τέτταρες',
             'τίς', 'τις', 'οὐδείς', 'μηδείς', 'πᾶς', 'ὅστις'}
SPECIFIC |= {'παῖς', 'σεαυτόν', 'ἄστυ', 'ὕδωρ', 'Πειραιεύς'}
SPECIFIC3 |= {'ἄστυ', 'ὕδωρ', 'Πειραιεύς', 'κύων', 'λαγώς', 'ὄρος', 'μάχαιρα'}
SPECIFIC |= {'κύων', 'λαγώς', 'ὄρος', 'μάχαιρα'}
SPECIFIC3 |= {'ἰσχύς', 'χείρ', 'Ζεύς', 'τρεῖς', 'τέτταρες'}
SPECIFIC3 |= {'κανοῦν', 'κρέας', 'ὄναρ', 'τέμενος', 'τεκόντες', 'ἄνθος', 'ὄψις', 'πόσις', 'ὗς', 'πλείων', 'πρᾷος'}
SPECIFIC |= {'ἄνθος', 'ὄψις', 'πόσις', 'ὗς', 'πλείων', 'πρᾷος'}
SPECIFIC |= {'κανοῦν', 'κρέας', 'ὄναρ', 'τέμενος'}
SPECIFIC |= {'ἰσχύς', 'χείρ', 'Ζεύς', 'τρεῖς', 'τέτταρες'}
SPECIFIC |= {'πῦρ'}                # πυρός, πυρί; pl. τὰ πυρά (2nd decl.): irregular (Smyth §285)
SPECIFIC3 |= {'πῦρ'}
SPECIFIC3 |= {'βασιλεύς', 'ναῦς', 'νύξ', 'ξίφος', 'πνεῦμα', 'πόλις', 'πούς', 'στῆθος', 'βασίλεια', 'πύλαι'}
SPECIFIC |= {'βασιλεύς', 'ναῦς', 'νύξ', 'ξίφος', 'πνεῦμα', 'πόλις', 'πούς', 'στῆθος', 'βασίλεια', 'ἐκεῖνος'}
ALIAS['πύλη'] = 'πύλαι'
ALIAS.update({'ἀέκων': 'ἄκων', 'ἰχθύς': 'ἰχθῦς', 'ζῶ': 'ζάω', 'μέλισσα': 'μέλιττα', 'συμπράσσω': 'συμπράττω', 'ἀποκηρύσσω': 'ἀποκηρύττω',
              'κλάω': 'κλαίω', 'σύριγξ': 'σῦριγξ', 'ἐλαία': 'ἐλάα'})
IRREG_ADJ = {'μέγας': {'μεγασ', 'μεγαν', 'μεγα'}, 'πολύς': {'πολυσ', 'πολυν', 'πολυ'},
             'πάμπολυς': {'παμπολυσ', 'παμπολυν', 'παμπολυ'}}
IRREG_VERB = {'εἰμί', 'εἶμι', 'φημί', 'οἶδα', 'τίθημι',
              'δίδωμι', 'ἵημι', 'πάρειμι', 'ἄπειμι', 'ἔξεστι', 'δεῖ', 'χρή'}
# stems in -εσ- (ch.13): τὸ τεῖχος, ἡ τριήρης, ἀληθής — their own endings (-ους, -ει, -η, -εις)
ES = {h for h, cl in CLASS if cl.split()[:1] in (['nes'], ['adjes'])} | {'τριήρης'}
# words whose forms are learnt through another word's keys (μηδείς like οὐδείς, ὅσπερ like ὅς …)
KEYLEMMA = {'τηλικοῦτος': 'τοσοῦτος', 'μηδείς': 'οὐδείς', 'ὅσπερ': 'ὅς', 'ἅπας': 'πᾶς', 'σαυτόν': 'σεαυτόν', 'σύμπας': 'πᾶς'}
SPECIFIC |= {'ἅπας', 'ὅσπερ', 'σαυτόν', 'σύμπας'}    # comparatives in -ων (κρείττων, μείζων, ἀμείνων …) decline like σώφρων: generic keys
SPECIFIC -= {'ἐκεῖνος'}          # ἐκεῖνος, -η, -ο: ordinary endings (ch.14 teaches οὗτος as the irregular one)
NOKEY = {'ὅδε', 'οὑτοσί'}                  # ὅδε, ἥδε, τόδε = article + δε: no form is new once the word is known
# δύναμαι, κεῖμαι, ἐπίσταμαι (ch.16): middle endings without the thematic vowel — keys V…μ (δύναται = Vpmiμ:3s)
# -μι verbs with active and middle forms: their keys keep the voice (δίδωμι:pai3s δίδωσι, δίδωμι:pmi3s δίδοται)
MI_VERBS = {'δίδωμι', 'τίθημι', 'ἵστημι', 'ἵημι', 'δείκνυμι'}
MI_PRES = {'ἵστημι', 'δείκνυμι'}             # present / imperfect active have keys of their own; the rest is regular
DOUBLE_AOR = {'ἵστημι'}          # ἔστησα “I set up” beside ἔστην “I stood”: the 1st aorist is S:ἵστημι~aor1
ATHEM_MID = {'δύναμαι', 'κεῖμαι', 'ἐπίσταμαι', 'κατακεῖμαι', 'κάθημαι', 'παράκειμαι', 'πρόκειμαι', 'ἐξεπίσταμαι'}
ROOT_AOR = re.compile(r'^(βη|βα[σν]|βαντ|γνω|γνο|στη[^σ]|στη$|στα[σν]|σταντ|δυ[^σν]|δυ$|φυ)')


def decl(lemma, tag, form):
    pos, gender = tag[0], tag[6]
    b, f = bare(lemma), bare(form)
    if lemma in ('νοῦς', 'πλοῦς', 'ἔκπλους'):
        return '2c'
    if lemma in ('πύλαι', 'Ἀθῆναι', 'Θερμοπύλαι'):
        return '1f'
    if lemma in ES or lemma == 'πετρώδης':
        return '3esn' if gender == 'n' else '3es'
    if lemma in ('μέλας',) and gender == 'f':
        return '1f'                                        # μέλαινα: mixed declension
    if lemma in ('πλοῦς', 'ἔκπλους'):
        return '2c'
    if pos == 'a':
        if lemma in IRREG_ADJ or b.endswith(('οσ', 'οι')) and lemma != 'ἑπτάρους':
            if gender == 'f':
                return '1f'
            return '2n' if gender == 'n' else '2'
        if gender == 'f' and re.search(r'(σα|σησ|σῃ|σαν|σαι|σων|σαισ|σασ|εια|ειασ|ειαν|ειαι|ειων)$', f):
            return '1f'                                    # πᾶσα, ἡδεῖα …: mixed declension
        return '3n' if gender == 'n' else '3'
    if b.endswith('οσ') and gender == 'n':
        return '3n'                                        # τὸ τεῖχος, τὸ ξίφος
    if b.endswith('οσ') and lemma not in THIRD_DECL:
        return '2'
    if b.endswith('ον') and gender == 'n':
        return '2n'
    if gender == 'f' and b.endswith(('η', 'α')):
        return '1f'
    if gender == 'm' and b.endswith(('ησ', 'ασ')) and not b.endswith(('ευσ',)) and lemma not in THIRD_DECL:
        return '1m'
    return '3n' if gender == 'n' else '3'


def ctr(lemma):
    b = bare(lemma)
    for e, c in (('εω', 'ε'), ('αω', 'α'), ('οω', 'ο'), ('εομαι', 'ε'), ('αομαι', 'α'), ('οομαι', 'ο')):
        if b.endswith(e):
            return c
    return ''


TRUST = [False]                    # True while analysing a generated / hand-made analysis: its tense code is exact


def aor_kind(lemma, tag, form):
    """'a' 1st (sigmatic or liquid) aorist, 'A' 2nd aorist, 'R' root aorist, 'P' passive"""
    t = tag[3]
    if t == 'a' and tag[5] == 'p':
        return 'P'
    if t in 'ARP':
        return t
    if TRUST[0] and t == 'a':
        return 'a'
    f = bare(form)
    f2 = re.sub(r'^(ε|η|ω|ει|ηυ)', '', f)
    if ROOT_AOR.match(f) or ROOT_AOR.match(f2):
        return 'R'
    if re.search(r'θη|θε[ιν]|θεισ|θεντ', f) and tag[5] == 'p':
        return 'P'
    if re.search(r'(α|ασ|αμεν|ατε|αν|αι|ασθαι|αμην|ατο|αμεθα|ασθε|αντο|ασα|ασησ|αντοσ|αμεν[ηο]υ?.*)$', f):
        return 'a'
    if re.search(r'(σον|ψον|ξον)$', f):
        return 'a'                                       # 1st aorist imperative λῦσον
    return 'A'


def gkey(lemma, tag, form):
    pos = tag[0]
    if pos in 'lx' or lemma in FREE_LEMMAS or lemma in NOKEY:
        return None
    if len(tag) > 2 and tag[2] == 'd':                     # the dual (ch.30)
        if not FINE:
            return 'Vdual' if pos == 'v' else 'Ndual'
        if pos == 'v' and tag[4] == 'p':
            return gkey(lemma, tag[:2] + 's' + tag[3:], form)   # the participle's tense key; its ending: ptc_key
        return dual_key(lemma, tag, form)
    if pos in 'napm' and tag[7] in 'ngdav':
        g = tag[6] if tag[6] in 'mfn' else 'm'
        case = CASE[tag[7]]
        if not FINE and (g == 'n' and case in ('acc', 'voc') or case == 'voc' and tag[2] == 'p'):
            case = 'nom'                                   # neuter nom. = acc. = voc.; voc. pl. = nom. pl.
        cn = '%s.%s' % (case, tag[2] if tag[2] in 'spd' else 's')
        if FINE and g == 'n' and case == 'voc':
            case = 'nom'                                   # a neuter vocative is always its nominative
            cn = '%s.%s' % (case, tag[2] if tag[2] in 'spd' else 's')
        if lemma in ('ἐγώ', 'σύ', 'ἕ', 'σφεῖς'):
            return '%s:%s' % (lemma, cn)
        if lemma == 'πῦρ' and tag[2] == 'p':
            return '2n:' + cn                              # τὰ πυρά, τῶν πυρῶν, τοῖς πυροῖς: 2nd declension
        if lemma in SPECIFIC or lemma == 'ἐκεῖνος' or pos == 'p' and lemma not in ('ἐμός', 'σός', 'ἡμέτερος',
                                                                                  'ὑμέτερος'):
            if pos == 'n' and lemma in SPECIFIC3 and cn == 'nom.s':
                return None                                # citation form
            kl = KEYLEMMA.get(lemma, lemma)
            gm = (SCH.lemma_genders(kl, 'n' if case == 'nom' else tag[7], tag[2], g) or gmerge(lemma, tag, form)) \
                if FINE else g
            return '%s:%s.%s' % (kl, cn, gm)
        if lemma in IRREG_ADJ and bare(form) in IRREG_ADJ[lemma]:
            return '%s:%s.%s' % (lemma, cn, gmerge(lemma, tag, form) if FINE else g)
        d = decl(lemma, tag, form)
        coarse = coarse_key(d, cn, pos)
        if FINE:
            sc = scheme_of(lemma, tag, d)
            if sc:
                cf = cell_full(tag, pos, form, lemma, sc)
                if cf is None:
                    return None                            # the citation form: nom. sg. (masc. of an adjective)
                fk = '%s:%s' % (sc, cf)
                FINE_OF[fk].add(coarse or '%s:%s' % (d, cn))
                return fk
        return coarse
    if pos == 'v':
        person, num, tense, mood, voice = tag[1], tag[2], tag[3], tag[4], tag[5]
        if num == 'S':
            num = 'd'
        if tense in 'aARP':
            tense = aor_kind(lemma, tag, form)
        voice = 'a' if voice == 'a' else ('p' if voice == 'p' and tense in 'aAPf' else 'm')
        c = ctr(lemma) if tense in 'pi' else ''
        if tense == 'f' and voice != 'p':
            c = FUT_CTR.get(lemma, '')                     # μενῶ, μαχοῦμαι: endings of ποιέω
        kl = 'δείκνυμι' if lemma in NUMI else lemma if lemma in IRREG_VERB or lemma in MI_PRES else next(
            (COMPOUND_OF[(lemma, v)] for v in variants(form) if (lemma, v) in COMPOUND_OF), None)
        if (lemma in ATHEM_MID or kl in MI_PRES and voice != 'a') and tense in 'pi':
            c = 'μ'
        # ε-contract forms that only differ from the plain ones by the circumflex are not a new ending
        if c == 'α' and tense in 'pf' and voice == 'a' and mood == 'i' and person + num == '1s':
            c = ''
        if c == 'ε' and tense in 'pf' and voice == 'm' and mood in 'im' and person + num == '2s':
            c = ''
        if c == 'ε' and tense in 'pf' and voice == 'a' and (
                mood == 'i' and person + num in ('1s', '2s', '3s', '2p', '3p') or mood == 'n' or
                mood == 'm' and person + num == '2p'):
            c = ''
        # imperfect of contract verbs: 1st/2nd pl. = augment + the present form (ἐποιοῦμεν, ἐτιμᾶτε)
        if c and tense == 'i' and person + num in ('1p', '2p'):
            c = ''
        if c == 'ε' and tense == 'i' and voice == 'a' and person + num == '2s':
            c = ''                                         # ἐποίεις like ποιεῖς
        if mood == 'n':
            body = '%s%sinf%s' % (tense, voice, c)
        elif mood == 'p':
            body = '%s%sptc%s.%s' % (tense, voice, c, 'f' if tag[6] == 'f' else 'mn')
        elif mood in 'isom':
            body = '%s%s%s%s:%s%s' % (tense, voice, mood, c, person, num)
        else:
            return None
        if mood == 's':                                    # subjunctive: one set of endings for every tense stem
            st = 'a' if tense in 'aA' else tense
            if voice == 'p' and tense in 'aP':
                return 'VPs:%s%s' % (person, num)          # λυθῇ, δοθῇ
            if kl in MI_VERBS and kl != 'δείκνυμι' and (kl not in MI_PRES or voice == 'a' and tense == 'p'):
                return '%s:%s%ss' % (kl, st, voice)        # διδῶ / δῶ, τιθῶ / θῶ, ἱῶ / ὧ, ἱστῶ: one item each
            if kl and kl not in MI_PRES:
                return '%s:%ss%s%s' % (kl, st, person, num)    # εἰμί:ps3s (ᾖ), εἶμι:ps3s (ἴῃ)
            if c in ('α', 'ο') and tense == 'p':
                return 'Vps' + c                           # τιμᾷ = indicative; δηλοῖ, δηλῶτε
            return 'V%s%ss:%s%s' % (st, voice, person, num)
        if tense == 't':
            return 'Vt'                                    # future perfect: one item
        if tense in 'rl' and voice == 'a' and kl != 'οἶδα':   # perfect / pluperfect active: ordinary endings
            return 'V' + body
        if tense in 'rl' and voice != 'a':                 # perfect / pluperfect middle-passive
            kc = 'κ' if bare(form).endswith(('ψαι', 'πται', 'φθε', 'ξαι', 'κται', 'χθε', 'λσαι', 'λται', 'λθε', 'ψο',
                                              'πτο', 'ξο', 'κτο', 'λσο', 'λτο', 'φθαι', 'χθαι', 'λθαι', 'φθον', 'χθον', 'λθον',
                                              'φθην', 'χθην', 'λθην')) else ''
            if mood == 'n':
                return 'V%sminf%s' % (tense, kc)
            if mood == 'p':
                return 'V%smptc' % tense
            if mood in 'im':
                return 'V%sm%s%s:%s%s' % (tense, mood, kc, person, num)
        if mood == 'o':                                    # optative
            if tense == 'f':
                return 'Vfo'                               # (only in indirect speech): one item
            if voice == 'p' and tense in 'aP':
                return 'VPo:%s%s' % (person, num)          # λυθείη, δοθείη
            if kl in MI_VERBS and kl != 'δείκνυμι' and (kl not in MI_PRES or voice == 'a' and tense == 'p'):
                return '%s:%s%so' % (kl, 'p' if tense in 'pi' else 'a', voice)   # διδοίην / δοίην: one item each
            if kl and kl not in MI_PRES:
                return '%s:%so%s%s' % (kl, 'p' if tense in 'pi' else 'r' if tense in 'rl' else 'a', person, num)   # εἴην, ἴοι, φαίην, εἰδείη
            if lemma in ATHEM_MID or kl in MI_PRES and voice != 'a' and tense in 'pi':
                return 'Voμ'                               # δύναιτο, ἐπίσταιτο, κέοιτο
            if tense == 'R' or c and tense == 'p' and voice == 'a':
                return 'Voη:%s%s' % (person, num)          # βαίη, γνοίη, σταίη; φιλοίη, τιμῴη
            if tense == 'a':
                return 'Vo1%s:%s%s' % (voice, person, num)  # λύσαι(μι), λύσειε; λυσαίμην
            return 'Vo%s:%s%s' % (voice, person, num)      # λύοι, λάβοι; λύοιτο, γένοιτο, φιλοῖτο
        if voice == 'p' and tense in 'afP' and mood != 's':  # ἐδόθην, δοθήσεται: ordinary passive endings
            return 'V' + body
        if kl in MI_PRES:                                  # ἵστημι, δείκνυμι: aorists and futures are regular,
            if tense in 'pi' and voice == 'a':             # the middle goes like δύναμαι
                return '%s:%s' % (kl, body.replace(':', ''))
            return 'V' + body
        if kl in MI_VERBS and tense != 'f':                # δώσω, θήσω: ordinary futures
            return '%s:%s' % (kl, body.replace(':', ''))
        if kl in MI_VERBS:
            return 'V' + body
        if kl:
            return '%s:%s' % (kl, (body[0] + body[2:]).replace(':', ''))
        return 'V' + body
    return None



# ---------------------------------------------------------------- inflection schemes: one key per cell
# FINE (the default): every cell of every scheme in project/schemes.py is a key of its own — 3κ:gen.s (φύλακος),
# Aυς:dat.p.f (βαθείαις), Pας:gen.s.m (λύσαντος) — including the cells whose form another cell shares (neuter acc.,
# voc. pl.). ATH_COARSE=1 gives back the old keys (one per declension class and case).
import schemes as SCH  # noqa: E402
FINE = os.environ.get('ATH_COARSE') != '1'
FINE_OF = defaultdict(set)       # fine key → the coarse keys it refines (their chapters gate it)
FINE_MERGED = {}
_LF, _SCH = {}, {}


def lemma_forms(lemma):
    if not _LF:
        for f, al in GEN.items():
            for l, t in al:
                _LF.setdefault(l, {}).setdefault(t[:9], f)
        for f, al in EXTRA.items():
            for a in al:
                if len(a) == 2:
                    _LF.setdefault(a[0], {}).setdefault(a[1][:9], f)
    return _LF.get(lemma, {})


DUAL_VERB = ('σθην', 'σθων', 'σθον', 'την', 'των', 'τον')


def dual_key(lemma, tag, form):
    """the dual, kept bare: one item per dual ending (ch. 30), whatever the paradigm (Smyth §§ 195–203, 462–466):
    nouns, adjectives, participles, pronouns -ω, -ᾱ, -ε, -ει (nom. acc. voc.), -οιν, -αιν (gen. dat.); the
    personal pronouns νώ, σφώ / νῷν, σφῷν; verbs -τον, -την, -σθον, -σθην, imperative -των, -σθων"""
    b = bare(form)
    if tag[0] == 'v':
        return next(('Dual:-' + e for e in DUAL_VERB if b.endswith(bare(e))), None)
    if tag[0] not in 'napm' or tag[7] not in 'ngdav':
        return None
    if lemma in ('ἐγώ', 'σύ'):
        return 'Dual:pers.' + ('NAV' if tag[7] in 'nav' else 'GD')
    if tag[7] in 'gd':
        return 'Dual:-αιν' if b.endswith('αιν') else 'Dual:-οιν'
    if lemma == 'δύο':
        return None
    for e, k in (('ει', '-ει'), ('ε', '-ε'), ('η', '-ε'), ('ω', '-ω'), ('α', '-α')):
        if b.endswith(e):
            return 'Dual:' + k
    return None


def _dual_nominal(lemma, tag, form):
    """dual cells: nom. = acc. = voc. (NAV.d) and gen. = dat. (GD.d) in every paradigm"""
    pos = tag[0]
    if pos not in 'napm' or tag[7] not in 'ngdav':
        return None
    case = 'NAV' if tag[7] in 'nav' else 'GD'
    g = tag[6] if tag[6] in 'mfn' else 'm'
    if lemma in ('ἐγώ', 'σύ', 'ἕ', 'σφεῖς'):
        return '%s:%s.d' % (lemma, case)
    if lemma in SPECIFIC or lemma == 'ἐκεῖνος' or pos == 'p' and lemma not in ('ἐμός', 'σός', 'ἡμέτερος', 'ὑμέτερος'):
        kl = KEYLEMMA.get(lemma, lemma)
        dg = 'mfn' if kl in SCH.MF_LEMMAS or kl in ('δύο', 'ἀμφότερος') else ('f' if g == 'f' else 'mn') \
            if pos in 'pam' else g
        return '%s:%s.d.%s' % (kl, case, dg)
    d = decl(lemma, tag, form)
    sc = scheme_of(lemma, tag, d) if lemma not in IRREG_ADJ else 'Aοη'
    if not sc:
        return 'Ndual'
    if pos == 'n':
        return '%s:%s.d' % (sc, case)
    return '%s:%s.d.%s' % (sc, case, dual_genders(sc, case, g))


DUAL_G = {}                       # lemma-specific words: their dual gender label (see _dual_nominal)


def dual_genders(sc, case, g):
    """the dual: masc. = neuter (καλώ, καλοῖν; λύοντε, λυόντοιν), the feminine its own (καλά, καλαῖν; λυούσα);
    adjectives of two endings one form for all genders (σώφρονε, σωφρόνοιν)"""
    if sc in SCH.TWO_ENDINGS:
        return 'mfn'
    return 'f' if g == 'f' else 'mn'


_GM = {}


def gmerge(lemma, tag, form):
    """the genders whose form in this cell is the same word: 'mn' for σοφοῦ, 'mfn' for σοφῶν, 'mf' for ἀδύνατος"""
    g = tag[6] if tag[6] in 'mfn' else 'm'
    case, num = tag[7], tag[2]
    if case == 'v' and g == 'n':
        case = 'n'
    sub = (tag[3], tag[5]) if tag[0] == 'v' else (tag[8:9] if tag[8:9] in ('c', 's') else '-',)
    ck = (lemma, tag[0], sub, case, num, bare(form))
    if ck in _GM:
        return _GM[ck]
    lf = lemma_forms(lemma)
    same = set(g)
    for t, f in lf.items():
        if t[0] != tag[0] or t[2] != num or t[6] not in 'mfn':
            continue
        tc = 'n' if t[7] == 'v' and t[6] == 'n' else t[7]
        if tc != case:
            continue
        if tag[0] == 'v' and (t[3], t[5], t[4]) != (tag[3], tag[5], 'p'):
            continue
        if tag[0] != 'v' and (t[8:9] if t[8:9] in ('c', 's') else '-') != sub[0]:
            continue
        if any(bare(f2) == bare(form) for t2, f2 in [(t, f)]):
            same.add(t[6])
    # a gender may have several forms in one cell (the generator keeps the first): look the form up as well
    for l, t in GEN.get(form, []) + [tuple(a) for a in EXTRA.get(form, []) if len(a) == 2]:
        if l == lemma and t[0] == tag[0] and t[2] == num and t[6] in 'mfn' and \
                ('n' if t[7] == 'v' and t[6] == 'n' else t[7]) == case:
            same.add(t[6])
    r = ''.join(x for x in 'mfn' if x in same)
    _GM[ck] = r
    return r


def coarse_key(d, cn, pos):
    """the old key of a 1st–3rd declension form (None: the citation form)"""
    case, num = cn.split('.')
    if case in ('acc', 'voc') and d in ('2n', '3n', '3esn', '2cn') or case == 'voc' and num == 'p':
        cn = 'nom.' + num                                  # merged cells: nom. = acc. = voc.
    if cn == 'nom.s' and (d in ('3', '3n', '3es') or pos == 'n' and d in ('1m', '1f', '3esn', '2c')):
        return None
    if d == '2n' and cn.startswith(('gen', 'dat')) or d == '1m' and cn == 'gen.s':
        d = '2'
    if d == '3esn' and cn.startswith(('gen', 'dat')):
        d = '3es'
    return '%s:%s' % (d, cn)


def scheme_of(lemma, tag, d):
    pos = tag[0]
    if lemma in SCH.OVERRIDE:
        return SCH.OVERRIDE[lemma]
    if lemma in IRREG_ADJ:
        return 'Aοη'                                       # μεγάλου, πολλῆς: like σοφός
    deg = tag[8] if len(tag) > 8 and tag[8] in 'cs' else '-'
    ck = (lemma, pos, deg)
    if ck in _SCH:
        return _SCH[ck]
    lf = lemma_forms(lemma)
    sc = None
    if pos == 'n':
        def F(case, num):
            return next((bare(f) for t, f in lf.items() if t[0] == 'n' and t[2] == num and t[7] == case), '')
        sc = SCH.noun_scheme(F, d, tag[6])
    elif pos in 'apm':
        def F(case, num, gen):
            return next((bare(f) for t, f in lf.items() if t[0] == pos and t[2] == num and t[7] == case and
                         t[6] == gen and (t[8] if len(t) > 8 and t[8] in 'cs' else '-') == deg), '')
        sc = SCH.adj_scheme(F, lemma, deg)
    if sc is None:
        sc = SCH.lemma_scheme(lemma, 'a' if pos in 'pm' else pos, tag[6], bare)
    _SCH[ck] = sc
    return sc


def cell_full(tag, pos, form, lemma, sc):
    """case.number(.gender) of a fine key; None for the citation form"""
    case, num = CASE[tag[7]], tag[2] if tag[2] in 'spd' else 's'
    g = tag[6] if tag[6] in 'mfn' else 'm'
    if pos == 'n' and case == 'voc' and g == 'n':
        case = 'nom'                                       # a neuter vocative is its nominative
    if pos == 'n':
        lf = lemma_forms(lemma)
        if case == 'nom' and (num == 's' or lf and not any(t[2] == 's' for t in lf)):
            return None
        cf = '%s.%s' % (case, num)
    else:
        if case == 'voc' and g == 'n':
            case = 'nom'
        if case == 'nom' and num == 's' and g == 'm':
            return None
        gm = SCH.genders(sc, tag[7] if case != 'nom' else 'n', num, g)
        if case == 'nom' and num == 's' and 'm' in gm:
            return None                                    # nom. sg. masc. (and fem. of a two-ending adjective)
        cf = '%s.%s.%s' % (case, num, gm)
    if case == 'voc' and num == 's' and sc[:1] == '3':     # 3rd decl.: a vocative = nominative is a cell of its own
        nom = next((f for t, f in lemma_forms(lemma).items() if t[0] == tag[0] and t[2] == 's' and t[7] == 'n' and
                    t[6] == tag[6] and t[8:9] == tag[8:9]), None)
        if nom and bare(nom) == bare(form):
            cf += '='
    return cf


_PSC = {}


def ptc_key(lemma, tag, form):
    """declension key of a participle: Pας:gen.s.m (λύσαντος); None for the nom. sg. masc."""
    if not FINE or tag[0] != 'v' or tag[4] != 'p' or tag[7] not in 'ngdav':
        return None
    tn, vc = tag[3], tag[5]
    ck = (lemma, tn, vc)
    if ck not in _PSC:
        lf = lemma_forms(lemma)
        pick = lambda g: next((f for t, f in lf.items() if t[0] == 'v' and t[4] == 'p' and t[3] == tn and  # noqa
                               t[5] == vc and t[2] == 's' and t[6] == g and t[7] == 'n'), '')
        nm, nf = pick('m'), pick('f')
        sc = SCH.ptc_scheme(bare(nm), bare(nf), vc, nm) if nm else None
        if sc is None:
            if vc != 'a' and not (vc == 'p' and tn in 'aP'):
                sc = 'Pμεν'
            elif tn in 'aP' and vc == 'p':
                sc = 'Pεις'
            elif tn in 'rl':
                sc = 'Pως'
            elif tn == 'a':
                sc = 'Pας'
            else:
                sc = {'ε': 'Pεων', 'ο': 'Pεων', 'α': 'Pαων'}.get(ctr(lemma), 'Pων')
        _PSC[ck] = sc
    sc = _PSC[ck]
    fb = bare(form)
    if tn in 'rl' and vc == 'a' and ('ωτ' in fb[-6:] or re.search(r'ωσ(α|ησ|η|αν|αι|ασ|ων|αισ)$', fb) or
                                     sc == 'Pως' and 'κ' not in fb[-5:] and re.search(r'ιστ(ημι|αμαι)$', bare(lemma))):
        sc = 'Pωσ'                                         # ἑστώς, -ῶσα, -ός (beside ἑστηκώς, -κυῖα)
    case, num, g = CASE[tag[7]], tag[2] if tag[2] in 'spd' else 's', tag[6] if tag[6] in 'mfn' else 'm'
    if case == 'voc' and g == 'n':
        case = 'nom'
    if case == 'nom' and num == 's' and g == 'm':
        return None
    if num == 'd':
        return dual_key(lemma, tag[:4] + 'x' + tag[5:], form) if False else _dual_ending(form, tag)
    return '%s:%s.%s.%s' % (sc, case, num, SCH.genders(sc, case[0] if case != 'nom' else 'n', num, g))


def specific_generic(k):
    """lemma-specific nominal key → the generic key whose chapter gates it"""
    lemma, cn = k.split(':', 1)
    if lemma in ('ἐγώ', 'σύ', 'ἕ', 'σφεῖς'):
        return 'pers:' + cn
    case, num, g = cn.split('.')
    g = g[-1] if g.endswith('n') and len(g) > 1 and 'm' not in g else g[0]
    if lemma in SPECIFIC3:
        return '%s:%s.%s' % ('3n' if g == 'n' else '3', case, num)
    d = {'m': '2', 'n': '2n', 'f': '1f'}[g]
    return '%s:%s.%s' % (d, case, num)


KEYPAT = [  # (regex on key, chapter) — first match wins
    # ---- book 2
    (r'Vf[am].*', 17), (r'εἰμί:f.*', 17), (r'εἶμι:p(i[123][sp]|ptc.*)', 17),
    (r'ἵστημι:[pi]a.*', 20),
    (r'[NV]dual', 30),
    (r'V[pPaAR][amp]m[εαομ]?:3[sp]', 31),
    (r'οἶδα:.*', 29), (r'(ἕ|σφεῖς):.*', 29),
    (r'V(t|[rl]m).*', 27), (r'V[rl]a.*', 28),
    (r'V(fo|Po:|o).*', 25), (r'(δίδωμι|τίθημι|ἵστημι|ἵημι):[pa][am]o', 25),
    (r'(εἰμί|εἶμι|πάρειμι|ἄπειμι|φημί|δεῖ|χρή|ἔξεστι):[pa]o.*', 25),
    (r'V(P|fp).*', 24),
    (r'φημί:(pi[12][sp]|pi3p|ii[12][sp]|ii3p|pinf)', 23),
    (r'δείκνυμι:[pi]a.*', 22),
    (r'V[paR][am]s:.*', 21), (r'Vps[αο]', 21), (r'(εἰμί|εἶμι|πάρειμι|ἄπειμι):ps.*', 21),
    (r'(δίδωμι|τίθημι|ἵστημι|ἵημι):[pa][am]s', 21), (r'ἵημι:.*', 21),
    (r'V.*μ(:|\.|$).*', 16),            # δύναμαι, κεῖμαι, ἐπίσταμαι
    # ch.1  3rd sg. present; nom./acc. (+ gen./dat. after prepositions) of the 2nd declension
    (r'Vpai:3s', 1), (r'εἰμί:pi3s', 1),
    (r'2n?:(nom|acc|gen|dat)\.s', 1), (r'2:(acc|dat)\.p', 1), (r'3n:(nom|acc)\.s', 1),
    # ch.2  present sg.; imperative sg.; all cases of the singular
    (r'Vpai:[12]s', 2), (r'Vpam:2s', 2), (r'Vpamε:2s', 2), (r'εἰμί:pi[12]s', 2), (r'εἰμί:pm2s', 2),
    (r'2n?:voc\.s', 2), (r'1m:(nom|gen|dat|acc|voc)\.s', 2),
    (r'1f:(acc|dat)\.s', 2), (r'pers:(nom|gen|dat|acc)\.s', 2),
    # ch.3  3rd pl.; imperative pl.; infinitive; all cases of the plural (masc., neut.)
    (r'Vpai:3p', 3), (r'Vpam:2p', 3), (r'Vpainf', 3), (r'εἰμί:pi3p', 3), (r'εἰμί:pinf', 3),
    (r'εἰμί:pm2p', 3), (r'2n?:(nom|gen|dat|acc|voc)\.p', 3), (r'1m:.*\.p', 3),
    # ch.4  all persons; feminine; 1st/2nd declension
    (r'Vpai:[12]p', 4), (r'Vpaiε:1p', 4), (r'εἰμί:pi[12]p', 4), (r'1f:.*', 4), (r'pers:nom\.p', 4),
    # ch.5  -α- contracts; personal pronouns (pl.)
    (r'Vpaiα:.*', 5), (r'Vpamα:.*', 5), (r'Vpainfα', 5), (r'pers:.*\.p', 5),
    # ch.6  middle, deponents
    (r'Vpm[im]ε?:.*', 6), (r'Vpminfε?', 6),
    # ch.7  3rd declension
    (r'3n?:.*', 7),
    # ch.8  present middle participle; middle of -α- contracts
    (r'Vpmptcε?\..*', 8), (r'Vpm[im]α:.*', 8), (r'Vpminfα', 8), (r'Vpmptcα\..*', 8),
    # ch.9  present active participle
    (r'Vpaptc.*', 9), (r'εἰμί:pptc.*', 9),
    # ch.11 2nd aorist        ch.12 1st aorist, impf. of εἰμί        ch.13 imperfect
    (r'VA.*', 11), (r'φημί:ii3s', 11), (r'Va.*', 12), (r'εἰμί:ii.*', 12), (r'Vi.*', 13), (r'3esn?:.*', 13),
    # ch.14 comparison       ch.15 root aorist, -ο- contracts, contracted 2nd decl.
    (r'D[cs]', 14), (r'οὗτος:.*', 14), (r'VR.*', 15), (r'V.*ο(:|\.|$).*', 15), (r'2c:.*', 15),
]
KEYCH = {}
# The book teaches the 3rd declension in ch.7 and some irregular words' paradigms later; before that it shows only
# single forms (in a reading or a Lexicon entry). form_gates.txt gives the chapter of each form's first appearance.
FORM_PARADIGM = {'ἀνήρ': 8, 'πατήρ': 8, 'μήτηρ': 8, 'θυγάτηρ': 8, 'πᾶς': 8, 'Ζεύς': 8, 'χείρ': 8, 'ἰσχύς': 8,
                 'εἷς': 8, 'τρεῖς': 8, 'τέτταρες': 8, 'βασιλεύς': 9, 'Πειραιεύς': 9, 'πόλις': 10, 'ἄστυ': 10,
                 'ὄρος': 13, 'ξίφος': 13, 'στῆθος': 13, 'ναῦς': 16, 'βοῦς': 16}
FORM_GATE = {}
for _line in open(os.path.join(HERE, 'form_gates.txt'), encoding='utf-8'):
    if _line.strip() and not _line.startswith('#'):
        _l, _cn, _c = _line.split()
        FORM_GATE['%s:%s' % (nfc(_l), _cn)] = 99 if _c == '-' else int(_c)


def form_gate(k):
    """chapter of a lemma-specific 3rd-declension form key, or None if the rule does not apply"""
    lemma = k.split(':', 1)[0]
    if lemma not in SPECIFIC3 or not re.match(r'.+:(nom|gen|dat|acc|voc)\.[spd]\.[mfn]+$', k):
        return None
    if lemma in ('μάχαιρα', 'βασίλεια', 'πύλαι'):           # 1st declension: taught with the word (ch.4 endings)
        return max(SYL.get(lemma, 0), 4)
    par = max(SYL.get(lemma, 0), FORM_PARADIGM.get(lemma, 7))
    base, gs = k.rsplit('.', 1)
    fg = min([FORM_GATE.get(k, 99)] + [FORM_GATE.get('%s.%s' % (base, x), 99) for x in gs])  # merged genders
    return max(SYL.get(lemma, 0), min(par, fg))


DUAL_RE = re.compile(r'^Dual:|(NAV|GD)\.d|[123]d$')


def _dual_ending(form, tag):
    """a participle's dual: its nominal ending (λύοντε -ε, λυούσα -α, λυομένω -ω, λυόντοιν -οιν, λυούσαιν -αιν)"""
    return dual_key('', 'a' + tag[1:], form)


def key_chapter(k):
    if k in KEYCH:
        return KEYCH[k]
    if FINE and DUAL_RE.search(k):
        KEYCH[k] = 30                                      # the dual: ch. 30
        return 30
    if FINE_OF.get(k, set()) - {k}:
        KEYCH[k] = 99                                      # (guards against a cycle)
        ch = min(key_chapter(c) for c in FINE_OF[k] - {k})
        KEYCH[k] = ch
        return ch
    lemma = k.split(':', 1)[0]
    if form_gate(k) is not None:
        ch = form_gate(k)
    elif re.match(r'.+:(nom|gen|dat|acc|voc)\.[spd]\.[mfn]+$', k) or re.match(r'(ἐγώ|σύ):', k):
        ch = max(SYL.get(lemma, 0), key_chapter(specific_generic(k)))
    elif lemma in IRREG_VERB:
        body = k.split(':', 1)[1]
        v = 'm' if lemma in ('δύναμαι', 'κεῖμαι', 'ἐπίσταμαι') else 'a'
        m = re.match(r'([a-zA-Z])(inf|ptc|[isom])', body)
        if lemma in MI_VERBS:
            m = re.match(r'([a-zA-Z])([amp])(inf|ptc|[isom])', body)
        gen = None
        if m and lemma in MI_VERBS:
            t, v, md = m.groups()
            rest = body[m.end():]
            gen = 'V%s%s%s' % (t, v, md) + (rest if md == 'ptc' else (':' + rest if rest else ''))
            if t in 'aA' and md in ('i', 'm', 'inf', 'ptc'):   # ἔδωκα, ἔθηκα; δοῦναι, θές …: taught with the verb itself
                gen = None
                ch = SYL.get(lemma, 0)
                KEYCH[k] = ch
                return ch
        elif m:
            t, md = m.groups()
            rest = body[m.end():]
            gen = 'V%s%s%s' % (t, v, md) + (rest if md == 'ptc' else (':' + rest if rest else ''))
        ch = SYL.get(lemma, 0)
        for pat, c in KEYPAT:
            if re.fullmatch(pat, k):
                ch = max(ch, c)
                break
        else:
            ch = max(ch, key_chapter(gen) if gen else 99)
    else:
        ch = 99
        for pat, c in KEYPAT:
            if re.fullmatch(pat, k):
                ch = c
                break
    KEYCH[k] = ch
    return ch


def ch_of(item):
    if item.startswith('L:'):
        return SYL.get(item[2:], 99 if not item[2:3].isupper() else 0)
    if item.startswith('C:'):
        return next((c for t, i, c in CHUNKS if i == item), 99)
    if item.startswith('X:'):
        return XITEMS.get(item, 99)
    if item.startswith('S:'):
        return STEMCH.get(item, 99)
    return key_chapter(item)


STEM_PART = {'fut': 17, 'aorp': 24, 'pfm': 27, 'pf': 28}     # chapter from which a principal part can be met


def stem_lemma(x):
    return x[2:].split('~')[0]


def is_bundled(k, new, items=None):
    """a lemma-specific key that comes together with its own (new) lemma counts as one item; so does a grammar
    key on the same word as a new aorist stem (S:…)"""
    if k.startswith(('L:', 'C:', 'X:', 'S:')) or ':' not in k:
        return False
    kl = k.split(':', 1)[0]
    if ('L:' + kl) in new or any(x[2:] in KEYLEMMA and KEYLEMMA[x[2:]] == kl and x.startswith('L:') and
                                 items is not None and set(items.get(x, [])) & set(items.get(k, [])) for x in new):
        return True
    if items:
        toks = set(items.get(k, []))
        if k[:1] == 'P' and k.split(':', 1)[0] in SCH.PTC_SCHEMES and any(
                'ptc' in x and x != k and toks & set(items.get(x, [])) for x in new):
            return True                                    # -ομένη, -ουσα: the cell comes with the new participle
        return any(x.startswith('S:') and toks & set(items.get(x, [])) for x in new)
    return False


def s_with_lemma(x, new):
    """an aorist stem S:lemma met together with its (new) lemma: one item (ἀνέστη: the word comes with its aorist)"""
    return x.startswith('S:') and ('L:' + stem_lemma(x)) in new


# ---------------------------------------------------------------- analysis
FORM_OF = {}


def analyses(tok):
    r = _analyses(tok)
    if FINE and r:
        FORM_OF[id(r)] = bare(tok)
        out = syncretic(r)
        FORM_OF.pop(id(r), None)
        return out
    return r


def syncretic(al):
    """cells that always share one form (Smyth §209, §196): voc. pl. = nom. pl.; neuter nom. = acc.; in the dual
    nom. = acc. = voc. and gen. = dat. A list that has only one of them gets the other as well"""
    have = {(l, t) for l, t, s in al}
    out = list(al)
    for l, t, s in al:
        if len(t) < 9 or not (t[0] in 'nap' or t[0] == 'v' and t[4] == 'p') or t[7] not in 'ngdav':
            continue
        twins = []
        if t[2] == 'p' and t[7] == 'n' and t[6] != 'n':
            twins = ['v']
        if t[6] == 'n' and t[7] in 'na':
            twins = ['n', 'a']
        if t[2] == 'd':
            twins = ['n', 'a', 'v'] if t[7] in 'nav' else ['g', 'd']
        if t[2] == 's' and t[7] in 'nv' and (t[0] == 'v' or t[6] == 'f' and FORM_OF.get(id(al), '')[-1:] in 'αη'):
            twins = ['n', 'v']                             # participles; the feminine in -α / -η: voc. = nom.
        for c in twins:
            t2 = t[:7] + c + t[8:]
            if (l, t2) not in have:
                have.add((l, t2))
                out.append((l, t2, s))
    return out


def _analyses(tok):
    """manual analyses (forms_extra.txt) override everything; otherwise generated paradigms of the
    syllabus words (authoritative for their lemmas) + treebank analyses of other lemmas"""
    for v in variants(tok):
        if v in EXTRA:
            return [(lem(l), t[:9], 'extra') for l, t in EXTRA[v]] + \
                [(lem(l), t[:9], 'extra') for w in variants(tok) for l, t in DUALX.get(w, [])]
    al, tb = [], []
    for v in variants(tok):
        for l, t in GEN.get(v, []):
            if (l, t[:9], 'gen') not in al:
                al.append((l, t[:9], 'gen'))
    for v in variants(tok):
        if v in LEX:
            cand = [(lem(l), t[:9], t[10:]) for l, t, n in LEX[v]]
            attic = [a for a in cand if a[2] not in ('hdt',)]
            tb += [a for a in (attic or cand) if a[0] not in GEN_LEMMAS and a not in tb]
            break
    if al:                     # with generated analyses, keep only treebank lemmas that look like the word
        tb = [a for a in tb if bare(a[0])[:1] == bare(tok)[:1]]
    for v in variants(tok):
        for l, t in DUALX.get(v, []):
            if (l, t[:9], 'extra') not in al:
                al.append((lem(l), t[:9], 'extra'))
    return (al + tb) or None


HINT_CASE = {'nom': 'n', 'gen': 'g', 'dat': 'd', 'acc': 'a', 'voc': 'v'}


def hint_ok(hint, lemma, tag):
    if hint is None:
        return True
    want_lemma, feats = hint
    if want_lemma and lemma != want_lemma:
        return False
    for f in feats:
        if f in ('m', 'f', 'n') and tag[6] != f:
            return False
        if f in HINT_CASE and tag[7] != HINT_CASE[f]:
            return False
        if f in ('s', 'p', 'd') and tag[2] != f:
            return False
        if re.fullmatch(r'[123][spd]', f) and tag[1:3] != f:
            return False
        if f in ('inf', 'ptc', 'imp', 'ind') and tag[4] != {'inf': 'n', 'ptc': 'p', 'imp': 'm', 'ind': 'i'}[f]:
            return False
        if f in ('pres', 'impf', 'aor', 'fut', 'pf', 'plpf') and tag[3] not in {
                'pres': 'p', 'impf': 'i', 'aor': 'aARP', 'fut': 'f', 'pf': 'r', 'plpf': 'l'}[f]:
            return False
        if f in ('subj', 'opt') and tag[4] != {'subj': 's', 'opt': 'o'}[f]:
            return False
        if f in ('act', 'mid', 'pass') and tag[5] != {'act': 'a', 'mid': 'm', 'pass': 'p'}[f]:
            return False
    return True


def card_items(gr, known, chapter, manual=(), hints=None, en=''):
    """→ items {item: [token indices]}, tokens [(start, end, text)], chosen analyses, problems"""
    hints = hints or {}
    # ἔλυον, ἐποίουν, εἶδον …: 1st sg. or 3rd pl.? — the translation decides (“I …”), hints (@form:3p) override
    person_pref = '1s' if re.search(r"\bI\b|\bI'", en) else '3p'
    gr = nfc(gr)
    toks = [(m.start(), m.end(), m.group(0)) for m in WORD.finditer(gr)]
    b = [bare(t[2]) for t in toks]
    items, chosen, problems, i = defaultdict(list), [None] * len(toks), [], 0
    while i < len(toks):
        hit = None
        for ct, it, ch in CHUNKS:
            if tuple(b[i:i + len(ct)]) == ct:
                hit = (ct, it, ch)
                break
        if hit:
            items[hit[1]] += list(range(i, i + len(hit[0])))
            for j in range(i, i + len(hit[0])):
                chosen[j] = ('chunk', hit[1])
            i += len(hit[0])
            continue
        tok = toks[i][2]
        if tok.endswith('᾽'):
            items['X:elision'].append(i)
        al = analyses(tok)
        if al is None:
            problems.append('unknown form ' + tok)
            i += 1
            continue
        best = None
        h = next((hints[v] for v in variants(tok) if v in hints), None) or hints.get(bare(tok))
        if h and any(hint_ok(h, l, t) for l, t, s in al):
            al = [a for a in al if hint_ok(h, a[0], a[1])]
        elif h:
            problems.append('hint matches no analysis: ' + tok)
        if bare(tok) in ('ο', 'η', 'οι', 'αι') and GRV in ud.normalize('NFD', tok) and any(a[0] != 'ὁ' for a in al):
            al = [a for a in al if a[0] != 'ὁ']           # ὃ, ἣ, οἳ, αἳ: with a grave accent never the article
        after_o = i > 0 and (b[i - 1] == 'ω' or i > 1 and b[i - 2] == 'ω' and chosen[i - 1] and
                             isinstance(chosen[i - 1][1], str) and chosen[i - 1][1][7:8] == 'v' and
                             not re.search(r'[,·;.!]', gr[toks[i - 1][1]:toks[i][0]]))
        if FINE and after_o and any(t[7:8] == 'v' for l, t, s in al):
            al = [a for a in al if a[1][7:8] == 'v']      # ὦ φίλε, ὦ ἄνδρες: the vocative
        elif FINE and not h:
            al = [a for a in al if a[1][7:8] != 'v'] or al  # without ὦ (or a hint) not a vocative
        for lemma, tag, s in al:
            TRUST[0] = s in ('gen', 'extra')
            its = []
            if lemma not in FREE_LEMMAS and tag[0] not in 'l':
                its.append('L:' + lemma)
            k = gkey(lemma, tag, tok)
            if k:
                its.append(k)
            pk = ptc_key(lemma, tag, tok)
            if pk:
                its.append(pk)
                FINE_OF[pk].add(k or 'Vpaptc.mn')
            if tag[0] == 'a' and len(tag) > 8 and tag[8] in 'cs':
                its.append('D' + tag[8])                   # comparative / superlative (ch.14)
            new = [x for x in its if x not in known]
            cost = (sum(1 for x in its if ch_of(x) > chapter),
                    1 if tag[0] == 'v' and tag[1:3] in ('1s', '3p') and tag[1:3] != person_pref else 0,
                    len([x for x in new if not is_bundled(x, new)]),
                    1 if FINE and tag[7:8] == 'v' and not after_o and tag[0] != 'v' else 0,
                    0 if s in ('extra', 'gen') else 1)
            if best is None or cost < best[0]:
                best = (cost, its, lemma, tag, s)
        for x in best[1]:
            items[x].append(i)
        chosen[i] = (best[2], best[3])
        lm, tg = best[2], best[3]
        TRUST[0] = best[4] in ('gen', 'extra')
        if tg[0] == 'v' and tg[3] in 'aARP':
            kind = aor_kind(lm, tg, tok)
            if kind == 'a' and BASE.get(lm, lm) in DOUBLE_AOR:
                s = 'S:%s~aor1' % BASE.get(lm, lm)
                items[s].append(i)
                STEMCH.setdefault(s, 20)
            elif kind == 'P':                              # ἐλήφθην: the aorist passive stem, when it is irregular
                l2 = BASE[lm] if (BASE.get(lm), 'aorp') in IRR_PART else lm
                if (l2, 'aorp') in IRR_PART:
                    s = 'S:%s~aorp' % l2
                    items[s].append(i)
                    STEMCH.setdefault(s, max(SYL.get(l2, 0), STEM_PART['aorp'], PART_CH.get((l2, 'aorp'), 0)))
            elif kind in 'AR' or kind == 'a' and lm in IRR_AOR1:
                s = 'S:' + lm
                if s not in known and lm in BASE and chapter >= 17:
                    s = 'S:' + BASE[lm]                    # ἐπανῆλθον: the aorist of ἔρχομαι, already known
                items[s].append(i)
                STEMCH.setdefault(s, max(SYL.get(lm, 0), {'A': 11, 'a': 12, 'R': 15, 'P': 99}[kind]))
        if tg[0] == 'v' and tg[3] in 'rlt':
            part = 'pf' if tg[5] == 'a' else 'pfm'
            l2 = BASE[lm] if (BASE.get(lm), part) in IRR_PART else lm
            if (l2, part) in IRR_PART:
                s = 'S:%s~%s' % (l2, part)
                items[s].append(i)
                STEMCH.setdefault(s, max(SYL.get(l2, 0), STEM_PART[part], PART_CH.get((l2, part), 0)))
        if tg[0] == 'v' and tg[3] == 'f':
            part = 'aorp' if tg[5] == 'p' else 'fut'
            if (BASE.get(lm), part) in IRR_PART:
                lm = BASE[lm]
            if (lm, part) in IRR_PART:
                s = 'S:%s~%s' % (lm, part)
                items[s].append(i)
                STEMCH.setdefault(s, max(SYL.get(lm, 0), STEM_PART[part], PART_CH.get((lm, part), 0)))
        if best[2] not in SYL and best[2] not in FREE_LEMMAS and best[3][0] != 'x' and not tok[:1].isupper():
            problems.append('not in syllabus: %s (%s)' % (best[2], tok))
        i += 1
    for x in manual:
        items.setdefault(x, [])
        if x.startswith('X:') and x not in XITEMS:
            problems.append('unknown construction ' + x)
        if x in XLEMMA:                                    # a sense item points at the word it is about
            items[x] = [i for i, c in enumerate(chosen) if c and c[0] == XLEMMA[x]]
            if not items[x]:
                problems.append('sense item %s: no token of %s' % (x, XLEMMA[x]))
    for x in [x for x in items if x.startswith('L:') and (x[2:3].isupper() and x[2:] not in SYL or x[2:] in NAMES)]:
        del items[x]                                       # names are free
    return dict(items), toks, chosen, problems


def read_cards(path):
    chapter = int(re.search(r'ch(\d\d)', path).group(1))
    for ln, line in enumerate(open(path, encoding='utf-8'), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = [x.strip() for x in line.split('|')]
        while len(parts) < 4:
            parts.append('')
        manual = [w[1:] for w in parts[3].split() if w.startswith('+')]
        hints = {}
        for w in parts[3].split():
            if w.startswith('@'):
                m = re.match(r'@([^=:]+)(?:=([^:]+))?(?::(.+))?$', nfc(w))
                if m:
                    hints[m.group(1)] = (m.group(2), (m.group(3) or '').split('.') if m.group(3) else [])
        flags = [w for w in parts[3].split() if w.startswith('!')]
        yield dict(gr=nfc(parts[0]), en=parts[1], src=parts[2] or 'composed', manual=manual, hints=hints, flags=flags,
                   chapter=chapter, file=os.path.basename(path), line=ln)


def run(paths, quiet=False, show=True):
    known, cards = set(), []
    uses = Counter()
    for path in paths:
        for c in read_cards(path):
            items, toks, chosen, probs = card_items(c['gr'], known, c['chapter'], c['manual'], c['hints'], c['en'])
            new = sorted(x for x in items if x not in known)
            count = len([x for x in new if not is_bundled(x, new, items) and not s_with_lemma(x, new)])
            late = [x for x in items if ch_of(x) > c['chapter']]
            if count > 1 and cards and not (count == 2 and '!bridge' in c.get('flags', ())):
                probs.append('%d NEW' % count)
            if late:
                probs.append('too early: ' + ', '.join('%s(ch%d)' % (x, ch_of(x)) for x in late))
            if not new:                        # the deck is purely n+1 (user's decision 2026-11-24)
                probs.append('nothing new')
            for x in items:
                uses[x] += 1
            credit = set()
            for x in items:
                if x.startswith('C:'):
                    for t in WORD.findall(x[2:]):
                        for l, tg, s in (analyses(t) or []):
                            if l in SYL and SYL[l] <= c['chapter'] and l not in FREE_LEMMAS:
                                credit.add('L:' + l)
            c.update(items=items, toks=toks, chosen=chosen, new=new, problems=probs, n=len(cards) + 1)
            known |= credit
            cards.append(c)
            if show and (probs or not quiet):
                print('%4d %-46s new: %-28s %s' % (c['n'], c['gr'][:46], ', '.join(new),
                                                   ('  <-- ' + '; '.join(probs)) if probs else ''))
            known |= set(items)
    return cards, known, uses


EXPECTED = {   # grammar keys each chapter should bring in (coverage report)
    1: ['Vpai:3s', 'εἰμί:pi3s', '2:nom.s', '2:acc.s', '2:gen.s', '2:dat.s', '2n:nom.s',
        '2:acc.p'],
    2: ['Vpai:1s', 'Vpai:2s', 'Vpam:2s', 'Vpamε:2s', 'εἰμί:pi1s', 'εἰμί:pi2s', '2:voc.s',
        '1m:acc.s', '1m:voc.s', '1m:dat.s', '1f:dat.s'],
    3: ['Vpai:3p', 'Vpam:2p', 'Vpainf', 'εἰμί:pi3p', 'εἰμί:pinf', 'εἰμί:pm2p', 'φημί:pi3s', '2:nom.p', '2:gen.p',
        '2:dat.p', '2n:nom.p', '1m:nom.p', '1m:acc.p'],
    4: ['Vpai:1p', 'Vpai:2p', 'Vpaiε:1p', 'εἰμί:pi1p', 'εἰμί:pi2p', '1f:nom.s', '1f:acc.s', '1f:gen.s',
        '1f:dat.s', '1f:nom.p', '1f:acc.p', '1f:gen.p', '1f:dat.p'],
    5: ['Vpaiα:2s', 'Vpaiα:3s', 'Vpaiα:1p', 'Vpaiα:2p', 'Vpaiα:3p', 'Vpamα:2s', 'Vpamα:2p', 'Vpainfα',
        'ἐγώ:acc.p', 'ἐγώ:dat.p', 'ἐγώ:gen.p', 'σύ:acc.p', 'σύ:dat.p', 'σύ:gen.p'],
    6: ['Vpmi:1s', 'Vpmi:2s', 'Vpmi:3s', 'Vpmi:1p', 'Vpmi:2p', 'Vpmi:3p', 'Vpmm:2s', 'Vpmm:2p', 'Vpminf',
        'Vpmiε:1s', 'Vpmiε:3s', 'Vpmiε:1p', 'Vpmiε:3p', 'Vpminfε'],
    7: ['3:gen.s', '3:dat.s', '3:acc.s', '3:nom.p', '3:gen.p', '3:dat.p', '3:acc.p', '3n:gen.s', '3n:dat.s',
        '3n:nom.p'],
    8: ['Vpmptc.mn', 'Vpmptc.f', 'Vpmptcε.mn', 'Vpmiα:3s', 'Vpmiα:3p', 'Vpminfα', 'Vpmptcα.mn'],
    9: ['Vpaptc.mn', 'Vpaptc.f', 'Vpaptcε.mn', 'Vpaptcε.f', 'Vpaptcα.mn', 'εἰμί:pptc.mn', 'εἰμί:pptc.f'],
    10: ['πόλις:nom.p.f', 'πόλις:gen.p.f'],
    11: ['VAai:1s', 'VAai:2s', 'VAai:3s', 'VAai:1p', 'VAai:2p', 'VAai:3p', 'VAam:2s', 'VAam:2p', 'VAainf',
         'VAaptc.mn', 'VAaptc.f', 'VAmi:1s', 'VAmi:3s', 'VAmi:3p', 'VAminf', 'VAmptc.mn', 'VAmm:2s'],
    12: ['Vaai:1s', 'Vaai:2s', 'Vaai:3s', 'Vaai:1p', 'Vaai:2p', 'Vaai:3p', 'Vaam:2s', 'Vaam:2p', 'Vaainf',
         'Vaaptc.mn', 'Vaaptc.f', 'Vami:3s', 'Vaminf', 'Vamptc.mn', 'εἰμί:ii3s', 'εἰμί:ii3p', 'εἰμί:ii1s'],
    13: ['Viai:1s', 'Viai:2s', 'Viai:3s', 'Viai:1p', 'Viai:2p', 'Viai:3p', 'Vimi:1s', 'Vimi:2s', 'Vimi:3s',
         'Vimi:1p', 'Vimi:2p', 'Vimi:3p', 'Viaiε:3s', 'Viaiε:3p', 'Viaiα:3s', 'Viaiα:3p', 'Vimiε:3s', 'Vimiε:3p',
         'εἶμι:ii3s', 'εἶμι:ii3p'] + ['ὅς:' + k for k in ('nom.s.m', 'nom.s.f', 'nom.s.n', 'acc.s.m', 'acc.s.f',
         'gen.s.m', 'gen.s.f', 'dat.s.m', 'dat.s.f', 'nom.p.m', 'nom.p.f', 'nom.p.n', 'gen.p.m', 'dat.p.m', 'dat.p.f',
         'acc.p.m', 'acc.p.f')] + ['3es:gen.s', '3es:dat.s', '3es:acc.s', '3es:nom.p', '3es:acc.p', '3es:gen.p',
         '3es:dat.p', '3esn:nom.p', '3esn:nom.s'],
    14: ['Dc', 'Ds'] + ['οὗτος:' + k for k in ('nom.s.m', 'nom.s.f', 'nom.s.n', 'acc.s.m', 'acc.s.f', 'gen.s.m',
         'gen.s.f', 'dat.s.m', 'dat.s.f', 'nom.p.m', 'nom.p.f', 'nom.p.n', 'gen.p.m', 'dat.p.m', 'dat.p.f',
         'acc.p.m', 'acc.p.f')],
    15: ['VRai:1s', 'VRai:2s', 'VRai:3s', 'VRai:1p', 'VRai:2p', 'VRai:3p', 'VRainf', 'VRam:2s', 'VRam:2p',
         'VRaptc.mn', 'VRaptc.f', 'Vpaiο:1s', 'Vpaiο:2s', 'Vpaiο:3s', 'Vpaiο:1p', 'Vpaiο:2p', 'Vpaiο:3p', 'Vpainfο',
         'Vpamο:2s', 'Vpaptcο.mn', 'Viaiο:3s', 'Viaiο:3p', 'Vpminfο', '2c:acc.s', '2c:gen.s', '2c:dat.s'],
    16: ['Vpmiμ:1s', 'Vpmiμ:2s', 'Vpmiμ:3s', 'Vpmiμ:1p', 'Vpmiμ:2p', 'Vpmiμ:3p', 'Vimiμ:3s', 'Vimiμ:3p',
         'Vpminfμ', 'Vpmptcμ.mn', 'ναῦς:dat.s.f', 'βοῦς:gen.s.m', 'βοῦς:dat.s.m', 'βοῦς:acc.p.m', 'βοῦς:dat.p.m'],
    17: ['Vfai:1s', 'Vfai:2s', 'Vfai:3s', 'Vfai:1p', 'Vfai:2p', 'Vfai:3p', 'Vfainf', 'Vfaptc.mn', 'Vfaptc.f',
         'Vfmi:1s', 'Vfmi:2s', 'Vfmi:3s', 'Vfmi:1p', 'Vfmi:2p', 'Vfmi:3p', 'Vfminf', 'Vfmptc.mn', 'Vfaiε:1p',
         'Vfmiε:3s', 'Vfmiε:3p', 'Vfmiε:1p', 'εἰμί:fi1s', 'εἰμί:fi2s', 'εἰμί:fi3s', 'εἰμί:fi1p', 'εἰμί:fi2p',
         'εἰμί:fi3p', 'εἰμί:finf', 'εἶμι:pi1s', 'εἶμι:pi2s', 'εἶμι:pi3s', 'εἶμι:pi1p', 'εἶμι:pi2p', 'εἶμι:pi3p',
         'εἶμι:pptc.mn', 'εἶμι:pptc.f'],
    18: [l + ':' + k for l in ('δίδωμι', 'τίθημι') for k in (
            'pai1s', 'pai2s', 'pai3s', 'pai1p', 'pai2p', 'pai3p', 'painf', 'pam2s', 'paptc.mn', 'paptc.f', 'iai3s',
            'iai3p', 'aai1s', 'aai2s', 'aai3s', 'aai1p', 'aai2p', 'aai3p', 'aam2s', 'aam2p', 'aainf', 'aaptc.mn',
            'aaptc.f', 'pmi3s', 'ami3s', 'aminf')],
    20: ['ἵστημι:' + k for k in ('pai1s', 'pai2s', 'pai3s', 'pai1p', 'pai2p', 'pai3p', 'painf', 'pam2s', 'paptc.mn',
                                 'iai3s', 'iai3p')] + ['S:ἵστημι~aor1'],
    21: ['Vpas:' + x for x in ('1s', '2s', '3s', '1p', '2p', '3p')] + ['Vpms:3s', 'Vpms:1p', 'Vpms:3p'] +
        ['Vaas:' + x for x in ('1s', '2s', '3s', '1p', '2p', '3p')] + ['Vams:1s', 'Vams:2s', 'Vams:3s', 'Vams:1p',
                                                                      'Vams:2p', 'Vams:3p'] +
        ['VRas:3s', 'VRas:1p', 'Vpsα', 'Vpsο', 'εἶμι:ps1p', 'εἶμι:ps3s', 'δίδωμι:aas', 'δίδωμι:pas', 'τίθημι:aas',
         'ἵημι:aas'] + ['εἰμί:ps' + x for x in ('1s', '2s', '3s', '1p', '2p', '3p')] +
        ['ἵημι:' + k for k in ('pai1s', 'pai2s', 'pai3s', 'pai1p', 'pai2p', 'pai3p', 'painf', 'pam2s', 'paptc.mn',
                               'iai3s', 'iai3p', 'aai1s', 'aai3s', 'aai1p', 'aai3p', 'aainf', 'aam2s', 'aaptc.mn',
                               'pmi3s', 'pmptc.mn')],
    22: ['δείκνυμι:' + k for k in ('pai1s', 'pai2s', 'pai3s', 'pai1p', 'pai3p', 'painf', 'pam2s', 'paptc.mn',
                                   'iai3s', 'iai3p')],
    23: ['φημί:' + k for k in ('pi1s', 'pi2s', 'pi1p', 'pi2p', 'pi3p', 'ii1s', 'ii3p', 'pinf')],
    24: ['VPpi:' + x for x in ('1s', '2s', '3s', '1p', '2p', '3p')] + ['VPpinf', 'VPpptc.mn', 'VPpptc.f', 'VPpm:2s',
         'VPs:3s', 'VPs:1p', 'Vfpi:1s', 'Vfpi:3s', 'Vfpi:1p', 'Vfpi:3p', 'Vfpinf', 'Vfpptc.mn'],
    25: ['Voa:' + x for x in ('1s', '2s', '3s', '1p', '2p', '3p')] + ['Vom:3s', 'Vom:1s', 'Vom:3p', 'Vo1a:3s',
         'Vo1a:1s', 'Vo1a:3p', 'Vo1m:3s', 'Voη:3s', 'Voη:1s', 'Voη:3p', 'VPo:3s', 'Vfo', 'εἰμί:po3s', 'εἰμί:po1s',
         'εἰμί:po3p', 'εἶμι:po3s', 'φημί:po3s', 'δίδωμι:aao', 'Voμ'],
    27: ['Vrmi:' + x for x in ('1s', '2s', '3s', '1p', '2p', '3p')] + ['Vrmiκ:3s', 'Vrminf', 'Vrminfκ', 'Vrmptc',
         'Vlmi:3s', 'Vlmi:3p', 'Vt'],
    28: ['Vrai:' + x for x in ('1s', '2s', '3s', '1p', '2p', '3p')] + ['Vrainf', 'Vraptc.mn', 'Vraptc.f', 'Vlai:3s',
         'Vlai:3p', 'Vlai:1s'],
    29: ['οἶδα:ri' + x for x in ('1s', '2s', '3s', '1p', '2p', '3p')] + ['οἶδα:li1s', 'οἶδα:li3s', 'οἶδα:li3p',
         'οἶδα:rinf', 'οἶδα:rptc.mn', 'οἶδα:rptc.f', 'οἶδα:rm2s', 'οἶδα:rs3s', 'οἶδα:ro3s',
         'ἕ:dat.s', 'σφεῖς:dat.p', 'σφεῖς:acc.p', 'σφεῖς:gen.p'],
    30: ['Ndual', 'Vdual'],
    31: ['Vpam:3s', 'Vpam:3p', 'Vpmm:3s', 'Vaam:3s'],
}


if __name__ == '__main__':
    quiet = '-q' in sys.argv
    paths = [a for a in sys.argv[1:] if not a.startswith('-')]
    cards, known, uses = run(paths, quiet)
    bad = sum(1 for c in cards if c['problems'])
    print('cards %d, cards with problems %d, items %d' % (len(cards), bad, len(known)))
    if '--cover' in sys.argv:
        maxch = max(c['chapter'] for c in cards)
        missing = [h for h, c in SYL.items() if c <= maxch and 'L:' + h not in known and h not in NAMES]
        missing += [i for t, i, c in CHUNKS if c <= maxch and i not in known]
        missing += [x for x, c in XITEMS.items() if c <= maxch and x not in known]
        missing += [k for ch in range(1, maxch + 1) for k in EXPECTED.get(ch, []) if k not in known]
        missing += sorted({'S:' + h for h, cl in CLASS if ('aor2=' in cl or 'aor_mid=' in cl) and 11 <= maxch
                           and 'S:' + h not in known and h not in BASE and SYL.get(h, 99) <= maxch})
        missing += sorted('S:%s~%s' % (h, k) for h, k in IRR_PART
                          if max(SYL.get(h, 0), STEM_PART[k], PART_CH.get((h, k), 0)) <= maxch
                          and 'S:%s~%s' % (h, k) not in known)
        print('not yet used (%d): %s' % (len(missing), ', '.join(missing)))
        few = sorted((u, x) for x, u in uses.items() if u < 3 and ch_of(x) <= maxch)
        print('used fewer than 3 times (%d): %s' % (len(few), ', '.join('%s×%d' % (x, u) for u, x in few)))
