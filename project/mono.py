import unicodedata as ud, re
def mono(s):
    s = ud.normalize('NFD', s)
    s = s.replace('̀', '́').replace('͂', '́')           # grave, circumflex → acute
    s = re.sub('[̓̔̓ͅ]', '', s)                          # breathings, iota subscript, coronis
    s = s.replace('᾽', '’').replace('᾿', '’').replace('᾽', '’')
    s = re.sub('́+', '́', s)
    s = ud.normalize('NFC', s)
    s = s.replace('·', ';').replace('·', ',')                           # ano teleia → comma for a short pause
    return s

_V = 'αεηιουωάέήίόύώϊϋΐΰ'
_DIPH = re.compile('(αι|ει|οι|υι|αυ|ευ|ου|ηυ|αί|εί|οί|υί|αύ|εύ|ού|ηύ)')
def _syll(w):
    w = _DIPH.sub('a', w.lower())
    return sum(1 for ch in w if ch in _V or ch == 'a')
_STRIP = str.maketrans('άέήίόύώ', 'αεηιουω')
def modern(s):
    """monotonic + no accent on monosyllables (as in Modern Greek), except ή 'or' and πού/πώς questions"""
    s = mono(s)
    def fix(m):
        w = m.group(0)
        if _syll(w) == 1 and w.lower() not in ('ή', 'πού', 'πώς', 'πή'):
            return w.translate(_STRIP)
        return w
    return re.sub(r'[^\W\d_]+', fix, s)
