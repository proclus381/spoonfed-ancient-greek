"""Repository paths, all relative to the repository root. Every tool imports this instead of hard-coding paths.

Scripts add their own directory to sys.path explicitly, so this works under `python3 -I` too:

    import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import config as P

Environment overrides: ATH_WORK (work files), ATH_SCRATCH (regenerable intermediates),
ATH_SENTENCES (another set of chNN.txt files).
"""
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.join(ROOT, 'project')          # deck sources, check2.py, build.py
TOOLS = os.path.join(ROOT, 'tools')
SENTENCES = os.environ.get('ATH_SENTENCES', os.path.join(PROJECT, 'sentences'))
SYLLABUS = os.path.join(PROJECT, 'syllabus')
GUID_OVERRIDES = os.path.join(PROJECT, 'guid_overrides.txt')
CARDS_BASELINE = os.path.join(PROJECT, 'cards_current.tsv')

WORK = os.environ.get('ATH_WORK', os.path.join(ROOT, 'work'))
SCRATCH = os.environ.get('ATH_SCRATCH', os.path.join(WORK, 'tmp'))   # match_*.json etc. (git-ignored)

if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)


def sentence_paths():
    """The deck's sentence files, in deck order."""
    return sorted(glob.glob(os.path.join(SENTENCES, 'ch[0-9][0-9].txt')))


def scratch(name):
    os.makedirs(SCRATCH, exist_ok=True)
    return os.path.join(SCRATCH, name)
