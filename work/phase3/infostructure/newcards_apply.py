"""Turn newcards.py's proposals (after the hand corrections below) into deck_edit.py REPLACE operations.

usage: newcards_apply.py PROPOSALS.tsv OPS_OUT        (repository root)
The card's column 4 (hints, + items, flags) is carried over; a hint's form is matched to the new sentence's
spelling (capital, grave or acute), so it still finds its word."""
import os
import re
import sys
import unicodedata as ud

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'project'))
import config as P  # noqa: E402
import check2 as K  # noqa: E402

FIX = {   # hand corrections: Greek → (new Greek or None to leave the card, new English or None)
    'Ὁ αὐτουργὸς τὸ καλὸν δένδρον φιλεῖ.': ('Φιλεῖ τὸ καλὸν δένδρον.', 'He loves the beautiful tree.'),
    'Ὁ αὐτουργὸς μικρὸν ἀγρὸν γεωργεῖ.': (None, 'He works a small field.'),
    'Οἱ νεανίαι τοὺς γέροντας τιμῶσιν.': (None, 'They honour the old.'),
    'Ὁ δῆμος τὸν ῥήτορα θαυμάζει.': (None, 'They admire the speaker.'),
    'Ὁ δῆμος τῷ ῥήτορι πείθεται.': (None, 'They are persuaded by the speaker.'),
    'Ὁ δῆμος τοὺς ῥήτορας θαυμάζει.': (None, 'They admire the speakers.'),
    'Ὁ δῆμος νόμους ἐτίθετο.': (None, 'They were making laws.'),
    'Ἡ μήτηρ τὸ παιδίον ἀπὸ τοῦ στήθους λαμβάνει.': ('Λαμβάνει τὸ παιδίον ἀπὸ τοῦ στήθους.',
                                                     'She takes the baby from her breast.'),
    'Τὴν πειθὼ τιμῶσιν οἱ ῥήτορες.': ('Οἱ ῥήτορες τιμῶσι τὴν πειθώ.', 'Speakers honour persuasion.'),
    'Ὁ ῥήτωρ πειθοῦς δεῖται.': ('KEEP', None),
    '«Ὦ παῖδες, τί ποιεῖτε;»': ('«Τί ποιεῖτε ἐνταῦθα, ὦ παῖδες;»', '“What are you doing here, children?”'),
}
lines = {}
for p in P.sentence_paths():
    for l in open(p, encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            parts = [x.strip() for x in l.rstrip('\n').split('|')]
            lines[ud.normalize('NFC', parts[0])] = parts
ops = []
for l in open(sys.argv[1], encoding='utf-8'):
    r = l.rstrip('\n').split('\t')
    if r[0] == 'n':
        continue
    old, new, en = r[3], r[4], r[6]
    if old in FIX:
        g, e = FIX[old]
        if g == 'KEEP':
            continue
        new, en = g or new, e or en
    parts = lines[old]
    extras = parts[3] if len(parts) > 3 else ''
    toks = re.findall(r'[\ẁ-ͯ᾽]+', ud.normalize('NFD', new))
    toks = [ud.normalize('NFC', t) for t in toks]

    def fixhint(m):
        form, rest = m.group(1), m.group(2)
        match = next((t for t in toks if K.bare(t) == K.bare(form)), form)
        return '@' + match + rest
    extras = re.sub(r'@([^\s=:]+)((?:=[^\s:]+)?(?::\S+)?)', fixhint, extras)
    src = parts[2] if len(parts) > 2 and parts[2] else 'composed'
    ops.append('REPLACE %s == %s | %s | %s%s' % (old, new, en, src, (' | ' + extras) if extras else ''))
open(sys.argv[2], 'w', encoding='utf-8').write('\n'.join(ops) + '\n')
print(len(ops), 'REPLACE operations')
