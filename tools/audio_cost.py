"""What an audio update costs: the clips of a manifest that your audio folder does not have yet.

usage: python3 -I audio_cost.py MANIFEST.tsv AUDIO_DIR [UNUSED_DIR] [OLD_MANIFEST.tsv]
MANIFEST: filename <TAB> text (project/out/audio_manifest.tsv after a build).
AUDIO_DIR: the folder of clips you have. UNUSED_DIR: clips set aside earlier;
a clip found there can be moved back instead of generated. OLD_MANIFEST: the previous manifest, for the count of
clips the deck no longer uses. Characters are those of the text sent to the voice (the manifest's text column).
Prints counts only; with --list also the missing filenames."""
import os
import sys

args = [a for a in sys.argv[1:] if not a.startswith('--')]
man, have_dir = args[0], args[1]
unused_dir = args[2] if len(args) > 2 else None
old = args[3] if len(args) > 3 else None


def rows(p):
    out = []
    for l in open(p, encoding='utf-8'):
        if '\t' in l:
            fn, text = l.rstrip('\n').split('\t', 1)
            out.append((fn, text))
    return out


new = rows(man)
have = set(os.listdir(have_dir))
unused = set(os.listdir(unused_dir)) if unused_dir and os.path.isdir(unused_dir) else set()
missing = [(f, t) for f, t in new if f not in have and f not in unused]
back = [(f, t) for f, t in new if f not in have and f in unused]
print('manifest: %d clips, %d characters' % (len(new), sum(len(t) for f, t in new)))
print('already in the audio folder: %d' % sum(1 for f, t in new if f in have))
print('in audio_unused, to move back: %d' % len(back))
print('to generate: %d clips, %d characters' % (len(missing), sum(len(t) for f, t in missing)))
if old:
    keep = {f for f, t in new}
    print('clips of the old manifest no longer used: %d' % sum(1 for f, t in rows(old) if f not in keep))
if '--list' in sys.argv:
    for f, t in missing:
        print(f)
