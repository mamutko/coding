#!/usr/bin/env python3
"""Make, check and index a batch of voice clips (the voice-over skill; see ../SKILL.md).

Input: a JSON file listing every clip a project wants,
    {"clips": [{"speaker": "garrick", "text": "Hold there, traveller.",
                "voice": {"voice": "ash", "style": "a weathered hunter ...", "speed": 1}}, ...]}
(a speaker with several voices, e.g. the player in a male and a female voice, is listed once per voice under its
own speaker name, such as "hero:m" and "hero:f").

Each clip is named <speaker>-<hash>.mp3 (":" becomes "-"), the hash covering voice, style, speed and text, so a
changed line or voice gets a new clip, an unchanged one is never made twice, and clips no line uses are removed.

  make_voices.py --lines L.json --out DIR                     list missing / unused clips and the cost (makes nothing)
  make_voices.py --lines L.json --out DIR --go --tts T.py     make the missing clips, remove unused ones, write the index
  make_voices.py --lines L.json --out DIR --index-only        only (re)write the index
  ... --verify --stt S.py                                     also transcribe the clips made in this run and flag
                                                              any whose words don't match the text

--tts: the ai-media-generation skill's openai_media.py (it holds its own key; never copy keys into a repo).
--stt: the same skill's google_media.py (transcription, a fraction of a cent a clip).
--index FILE: .json (an object) or .js (`var <--var> = <--var> || {}; Object.assign(<--var>, {...})`), mapping
"speaker|text" to [path, seconds]; the path is --prefix + the file name. Needs ffmpeg and ffprobe.
"""
import argparse, difflib, hashlib, json, os, re, subprocess, sys, tempfile

PER_MIN = 0.015          # gpt-4o-mini-tts, USD per minute of speech
MIN_MIN = 0.05           # the script's least charge per call, in minutes
# mono, 64 kbit/s, the silence at the start and end cut (to 0.05 s before the voice and 0.15 s after it):
# silenceremove only trims the start, so the end is trimmed on the reversed audio
TRIM = ('silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,'
        'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.15,areverse')


def clip_name(c):
    v = c['voice']
    speed = v.get('speed', 1)
    if isinstance(speed, float) and speed.is_integer():
        speed = int(speed)
    # the same as JavaScript's JSON.stringify([voice, style, speed, text]) (no spaces, unicode kept)
    key = json.dumps([v['voice'], v.get('style', ''), speed, c['text']], separators=(',', ':'), ensure_ascii=False)
    return c['speaker'].replace(':', '-') + '-' + hashlib.sha1(key.encode('utf-8')).hexdigest()[:10] + '.mp3'


def seconds(p):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def trim(src, dst):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-af', TRIM, '-ac', '1', '-b:a', '64k', dst], check=True)


def min_seconds(text):   # less than this: the clip came back (nearly) silent or cut off
    return 0.3 + 0.1 * len(text.split())


def words(s):
    return re.sub(r"[^a-z0-9' ]", ' ', s.lower().replace('’', "'")).split()


def make(c, path, tts):
    v = c['voice']
    with tempfile.TemporaryDirectory() as tmp:
        raw = os.path.join(tmp, 'raw.mp3')
        for tries in range(1, 4):   # up to 3 takes
            cmd = [sys.executable, os.path.abspath(tts), 'speak', c['text'], '-v', v['voice'], '-o', raw, '--max-cost', '0.2']
            if v.get('style'):
                cmd += ['--instructions', v['style']]
            if v.get('speed', 1) != 1:
                cmd += ['--speed', str(v['speed'])]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, cwd=os.path.dirname(os.path.abspath(tts)))
            trim(raw, path)
            d = seconds(path)
            if d >= min_seconds(c['text']) or tries == 3:
                print(f'made {os.path.basename(path)} ({d:.2f} s)  {c["speaker"]}: {c["text"]}')
                return
            print(f'too short ({d:.2f} s), again: {c["text"]}')


def verify(c, path, stt):
    out = subprocess.run([sys.executable, os.path.abspath(stt), 'transcribe', os.path.abspath(path)], capture_output=True, text=True,
                         cwd=os.path.dirname(os.path.abspath(stt))).stdout.strip().splitlines()
    out = [l for l in out if l.strip() and 'cost' not in l.lower()]   # (the script also prints its cost)
    heard = out[-1].strip() if out else ''
    r = difflib.SequenceMatcher(None, words(c['text']), words(heard)).ratio()
    flag = 'OK ' if r >= 0.8 else 'CHECK'
    print(f'{flag} {r:.2f}  {c["speaker"]}: "{c["text"]}"  heard: "{heard}"')
    return r >= 0.8


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--lines', required=True)
    ap.add_argument('--out', required=True, help='the folder the clips live in (only .mp3 files there are managed)')
    ap.add_argument('--index', help='the index file to write (.json or .js)')
    ap.add_argument('--var', default='VOICE_CLIPS', help='the .js index\'s variable')
    ap.add_argument('--prefix', default='', help='prepended to the file name in the index (e.g. assets/voice/story/)')
    ap.add_argument('--header', default='', help='a comment line for the .js index')
    ap.add_argument('--go', action='store_true')
    ap.add_argument('--index-only', action='store_true')
    ap.add_argument('--tts', default=os.environ.get('TTS_SCRIPT', ''))
    ap.add_argument('--verify', action='store_true', help='transcribe the clips made in this run (--stt)')
    ap.add_argument('--stt', default=os.environ.get('STT_SCRIPT', ''))
    a = ap.parse_args()

    clips = json.load(open(a.lines, encoding='utf-8'))['clips']
    want = {}
    for c in clips:
        want[clip_name(c)] = c
    os.makedirs(a.out, exist_ok=True)
    have = {f for f in os.listdir(a.out) if f.endswith('.mp3')}
    missing = [f for f in want if f not in have]
    unused = sorted(have - set(want))
    cost = sum(max(len(want[f]['text'].split()) / 150, MIN_MIN) for f in missing) * PER_MIN

    if not a.go and not a.index_only:
        print(f'{len(want)} clips, {len(missing)} missing, {len(unused)} unused')
        for f in missing:
            print(f'  {want[f]["speaker"]}: {want[f]["text"]}')
        print(f'making them costs about ${cost:.3f}. Run with --go --tts <openai_media.py> to make them.')
        return

    made = []
    if a.go:
        if missing and not os.path.exists(a.tts):
            sys.exit('--tts <path to openai_media.py> (or $TTS_SCRIPT) is needed to make clips')
        print(f'making {len(missing)} clips, about ${cost:.3f}')
        for f in missing:
            make(want[f], os.path.join(a.out, f), a.tts)
            made.append(f)
        for f in unused:
            os.remove(os.path.join(a.out, f))
            print('removed ' + f)
        if a.verify and made:
            if not os.path.exists(a.stt):
                sys.exit('--stt <path to google_media.py> (or $STT_SCRIPT) is needed to verify')
            bad = [f for f in made if not verify(want[f], os.path.join(a.out, f), a.stt)]
            print(f'{len(made) - len(bad)} of {len(made)} match' + (f'; listen to: {", ".join(bad)}' if bad else ''))

    if a.index:
        rows = {}
        for f, c in want.items():
            p = os.path.join(a.out, f)
            if os.path.exists(p):
                rows[c['speaker'] + '|' + c['text']] = [a.prefix + f, round(seconds(p), 2)]
        if a.index.endswith('.js'):
            body = ''.join(f'  {json.dumps(k, ensure_ascii=False)}: [{json.dumps(v[0])}, {v[1]:.2f}],\n' for k, v in rows.items())
            text = (f'// {a.header}\n' if a.header else '') + \
                f'var {a.var} = {a.var} || {{}};\nObject.assign({a.var}, {{\n{body}}});\n'
        else:
            text = json.dumps(rows, ensure_ascii=False, indent=1) + '\n'
        with open(a.index, 'w', encoding='utf-8') as fh:
            fh.write(text)
        print(f'{len(rows)} clips in {a.index}')


if __name__ == '__main__':
    main()
