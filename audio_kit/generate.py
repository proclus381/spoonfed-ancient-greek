#!/usr/bin/env python3
"""Make human-voice audio for the Athenaze companion deck through ai33.pro.

    python3 generate.py credits                 # check the key and your credit balance
    python3 generate.py test                    # 20 sample sentences  -> audio_test/
    python3 generate.py all                     # every sentence       -> audio/   (resumable)
    python3 generate.py retry                   # try failed sentences again
    python3 generate.py install                 # copy audio/ into Anki's media folder (close Anki first)

Settings: put your key in a file named key.txt next to this script (or set AI33_KEY).
Voice: --voice elevenlabs_... (default below). Speed: --speed 0.9 (0.5–1.5).
Only the Python standard library is used; Python 3.8 or newer.
"""
import argparse
import glob
import json
import os
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
API = os.environ.get('AI33_API', 'https://api.ai33.pro')
DEFAULT_VOICE = 'elevenlabs_HXOQciguVdtIpvH2gB8g'
UA = 'athenaze-companion-audio/1.0'


# ---------------------------------------------------------------- http
def key():
    k = os.environ.get('AI33_KEY', '').strip()
    p = os.path.join(HERE, 'key.txt')
    if not k and os.path.exists(p):
        k = open(p, encoding='utf-8').read().strip()
    if not k:
        sys.exit('No API key: put it in key.txt next to this script (one line), or set AI33_KEY.')
    return k


def request(method, url, data=None, headers=None, timeout=60):
    h = {'xi-api-key': key(), 'User-Agent': UA}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get_json(path):
    return json.loads(request('GET', API + path, headers={'Content-Type': 'application/json'}))


def post_form(path, fields):
    b = uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (b, k, v))
    parts.append('--%s--\r\n' % b)
    body = ''.join(parts).encode('utf-8')
    return json.loads(request('POST', API + path, data=body,
                              headers={'Content-Type': 'multipart/form-data; boundary=%s' % b}))


def with_retries(fn, tries=5):
    for i in range(tries):
        try:
            return fn()
        except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
            code = getattr(e, 'code', None)
            if code in (400, 401, 402, 403, 404, 422):
                raise
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def credits():
    r = get_json('/v1/credits')
    return r.get('credits')


# ---------------------------------------------------------------- work
def load_manifest():
    rows = []
    for line in open(os.path.join(HERE, 'audio_manifest.tsv'), encoding='utf-8'):
        fn, text = line.rstrip('\n').split('\t', 1)
        rows.append((fn, text))
    return rows


class State:
    """task ids already submitted (so a restart never pays twice) and failures"""
    def __init__(self, path):
        self.path = path
        self.d = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
        self.lock = threading.Lock()

    def get(self, fn):
        with self.lock:
            return self.d.get(fn)

    def set(self, fn, v):
        with self.lock:
            if v is None:
                self.d.pop(fn, None)
            else:
                self.d[fn] = v

    def save(self):
        with self.lock:
            snap = dict(self.d)
        tmp = self.path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as fh:
            json.dump(snap, fh, ensure_ascii=False, indent=0)
        os.replace(tmp, self.path)


def one(fn, text, outdir, state, args):
    dest = os.path.join(outdir, fn)
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        return fn, 'exists', None
    entry = state.get(fn) or {}
    tid = entry.get('task') if entry.get('voice') == args.voice and not args.resubmit else None
    if not tid:
        r = with_retries(lambda: post_form('/v3/text-to-speech', {
            'text': text, 'voice_id': args.voice, 'speed': str(args.speed),
            'with_transcript': 'false', 'file_name': fn[:-4]}))
        tid = r.get('task_id')
        if not tid:
            return fn, 'error', 'no task id: %s' % json.dumps(r)[:200]
        state.set(fn, {'task': tid, 'voice': args.voice})
    t0 = time.time()
    while True:
        time.sleep(2)
        r = with_retries(lambda: get_json('/v1/task/%s' % tid))
        st = r.get('status')
        if st == 'done':
            url = (r.get('metadata') or {}).get('audio_url')
            if not url:
                return fn, 'error', 'done but no audio_url'
            data = with_retries(lambda: urllib.request.urlopen(
                urllib.request.Request(url, headers={'User-Agent': UA}), timeout=120).read())
            if len(data) < 1000:
                return fn, 'error', 'audio file too small'
            tmp = dest + '.part'
            open(tmp, 'wb').write(data)
            os.replace(tmp, dest)
            return fn, 'ok', r.get('credit_cost')
        if st == 'error':
            state.set(fn, None)                         # next run submits it again
            return fn, 'error', r.get('error_message') or 'error'
        if time.time() - t0 > 600:
            return fn, 'error', 'timed out after 10 min (task %s; run again to keep waiting)' % tid


def run(rows, outdir, args):
    os.makedirs(outdir, exist_ok=True)
    state = State(os.path.join(outdir, '_tasks.json'))
    todo = [(f, t) for f, t in rows if not (os.path.exists(os.path.join(outdir, f))
                                           and os.path.getsize(os.path.join(outdir, f)) > 1000)]
    chars = sum(len(t) for _, t in todo)
    print('%d sentences to do (%d already done), %d characters. Voice: %s, speed %s'
          % (len(todo), len(rows) - len(todo), chars, args.voice, args.speed))
    try:
        print('credits before: %s' % credits())
    except Exception as e:                              # noqa: BLE001
        sys.exit('Could not reach ai33 / key rejected: %s' % e)
    errors, done, cost, last_save = [], 0, 0, time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(one, f, t, outdir, state, args) for f, t in todo]
        for fut in as_completed(futs):
            try:
                fn, status, info = fut.result()
            except Exception as e:                      # noqa: BLE001
                fn, status, info = '?', 'error', repr(e)[:200]
            if status == 'ok':
                done += 1
                cost += info or 0
            elif status == 'error':
                errors.append((fn, info))
            if time.time() - last_save > 10:
                state.save()
                last_save = time.time()
            n = done + len(errors)
            if n % 25 == 0 or n == len(todo):
                print('  %d / %d  (errors %d)' % (n, len(todo), len(errors)), flush=True)
    state.save()
    with open(os.path.join(outdir, '_errors.tsv'), 'w', encoding='utf-8') as fh:
        for fn, info in errors:
            fh.write('%s\t%s\n' % (fn, info))
    print('finished: %d new files, %d errors%s' % (done, len(errors),
          ' (listed in %s/_errors.tsv; run "retry")' % os.path.basename(outdir) if errors else ''))
    try:
        print('credits after: %s' % credits())
    except Exception:                                   # noqa: BLE001
        pass


TEST_N = 20


def test_rows(rows):
    step = max(1, len(rows) // TEST_N)
    return rows[::step][:TEST_N]


def anki_media_dirs():
    home = os.path.expanduser('~')
    cands = [os.path.join(home, 'Library', 'Application Support', 'Anki2'),     # macOS
             os.path.join(os.environ.get('APPDATA', ''), 'Anki2'),               # Windows
             os.path.join(home, '.local', 'share', 'Anki2')]                     # Linux
    out = []
    for c in cands:
        out += [d for d in glob.glob(os.path.join(c, '*', 'collection.media')) if os.path.isdir(d)]
    return out


def install(args):
    src = os.path.join(HERE, 'audio')
    files = [f for f in os.listdir(src) if f.startswith('athv_') and f.endswith('.mp3')] if os.path.isdir(src) else []
    if not files:
        sys.exit('No files in audio/ yet: run "python3 generate.py all" first.')
    dirs = [args.media] if args.media else anki_media_dirs()
    if not dirs:
        sys.exit('Could not find Anki\'s media folder. Give it with --media "<path to collection.media>".')
    if len(dirs) > 1:
        print('Several Anki profiles found:')
        for i, d in enumerate(dirs, 1):
            print('  %d) %s' % (i, d))
        dirs = [dirs[int(input('Which one? number: ')) - 1]]
    dst = dirs[0]
    for f in files:
        shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
    print('copied %d files into %s' % (len(files), dst))
    print('Now open Anki and import Athenaze_Companion_ch01-31_humanvoice.apkg, then sync.')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['credits', 'test', 'all', 'retry', 'install'])
    ap.add_argument('--voice', default=DEFAULT_VOICE)
    ap.add_argument('--speed', type=float, default=1.0)
    ap.add_argument('--workers', type=int, default=6, help='requests at the same time (default 6)')
    ap.add_argument('--resubmit', action='store_true', help='ignore saved task ids and submit again')
    ap.add_argument('--media', help='path to Anki collection.media (for install)')
    args = ap.parse_args()
    if args.command == 'credits':
        print('key OK, credits: %s' % credits())
        return
    if args.command == 'install':
        install(args)
        return
    rows = load_manifest()
    if args.command == 'test':
        out = os.path.join(HERE, 'audio_test', args.voice)
        run(test_rows(rows), out, args)
        with open(os.path.join(out, '_sentences.txt'), 'w', encoding='utf-8') as fh:
            for f, t in test_rows(rows):
                fh.write('%s\t%s\n' % (f, t))
        print('Listen to the files in %s (the texts are in _sentences.txt).' % out)
        return
    if args.command == 'retry':
        args.resubmit = False
    run(rows, os.path.join(HERE, 'audio'), args)


if __name__ == '__main__':
    main()
