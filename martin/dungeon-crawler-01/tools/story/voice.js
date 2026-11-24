#!/usr/bin/env node
// Voice-over for the dialogue (README.md, Dialogue: Voice-over). Finds every line in story/*.js whose speaker has a
// voice (the story's `voices`): characters' lines, and the hero's lines and choices in each hero voice (m, f). A
// clip is named after its speaker and a hash of its voice and text, so a changed line or voice gets a new clip and
// the old one is removed. Lines with {…} in them change with the game and aren't voiced.
//
//   node tools/story/voice.js                      lists what is missing and what it would cost (nothing is made)
//   node tools/story/voice.js --go --tts <path>    makes the missing clips, removes unused ones, writes the index
//   node tools/story/voice.js --index              only rewrites the index (story/<name>.voices.js)
//
// --tts is the text-to-speech script (the ai-media-generation skill's openai_media.py, which holds its own key;
// also read from $TTS_SCRIPT). Clips go to assets/voice/<story>/<speaker>-<hash>.mp3, made mono, 64 kbit/s, with the
// silence around the voice cut (one that comes back nearly silent is made again, up to 3 times); the
// index story/<name>.voices.js maps "speaker|text" (the hero: "hero:m|text") to [file, seconds].
const fs = require('fs'), path = require('path'), vm = require('vm'), crypto = require('crypto'), { execFileSync } = require('child_process');
const ROOT = path.resolve(__dirname, '..', '..'), DIR = path.join(ROOT, 'story');
const args = process.argv.slice(2), GO = args.includes('--go'), INDEX = args.includes('--index');
const TTS = (args.includes('--tts') ? args[args.indexOf('--tts') + 1] : process.env.TTS_SCRIPT) || '';
const PER_MIN = 0.015;   // gpt-4o-mini-tts, USD per minute of speech (as the script's price table has it)

// mono, 64 kbit/s, the silence at the start and end cut (to 0.05 s before the voice and 0.15 s after it)
const TRIM = 'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,' +
  'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.15,areverse';
const trim = (src, dst) => execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', src, '-af', TRIM, '-ac', '1', '-b:a', '64k', dst]);
const seconds = p => +execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]).toString().trim();
const ctx = vm.createContext({});
for (const f of fs.readdirSync(DIR).filter(f => f.endsWith('.js') && !f.endsWith('.voices.js')).sort())
  vm.runInContext(fs.readFileSync(path.join(DIR, f), 'utf8'), ctx, { filename: f });
const STORIES = ctx.STORIES || {};
const plain = t => typeof t === 'string' && !/(^|[^\\]){/.test(t);
const spoken = t => t.replace(/\\{/g, '{');
let total = { lines: 0, missing: 0, words: 0 };

for (const key in STORIES) {
  const st = STORIES[key], vs = st.voices || {}, out = path.join(ROOT, 'assets', 'voice', key), want = new Map();
  // every (speaker, voice, text) the story speaks
  const add = (who, text) => {
    if (!plain(text)) return;
    const variants = who === 'hero' ? Object.entries(vs.hero || {}).map(([g, v]) => ['hero:' + g, v]) : vs[who] ? [[who, vs[who]]] : [];
    for (const [spk, v] of variants) {
      const h = crypto.createHash('sha1').update(JSON.stringify([v.voice, v.style || '', v.speed || 1, text])).digest('hex').slice(0, 10);
      const file = spk.replace(':', '-') + '-' + h + '.mp3';
      want.set(file, { spk, v, text: spoken(text) });
    }
  };
  const nodes = ns => { for (const n in ns || {}) for (const it of ns[n]) {
    if (it.say != null) add(it.say, it.text);
    if (it.choose) for (const o of it.choose) add('hero', o.text);
  } };
  for (const id in st.chars || {}) nodes(st.chars[id].nodes);
  for (const v of st.convs || []) nodes(v.nodes);
  if (!want.size && !fs.existsSync(out)) continue;
  fs.mkdirSync(out, { recursive: true });
  const have = new Set(fs.readdirSync(out).filter(f => f.endsWith('.mp3')));
  const missing = [...want].filter(([f]) => !have.has(f));
  total.lines += want.size; total.missing += missing.length;
  for (const [, w] of missing) total.words += w.text.split(/\s+/).length;
  if (!GO && !INDEX) {
    console.log(`${key}: ${want.size} clips, ${missing.length} missing, ${[...have].filter(f => !want.has(f)).length} unused`);
    for (const [f, w] of missing) console.log('  ' + w.spk + ': ' + w.text);
    continue;
  }
  if (GO) {
    if (missing.length && !fs.existsSync(TTS)) { console.error('--tts <path to openai_media.py> (or $TTS_SCRIPT) is needed to make clips'); process.exit(1); }
    for (const [f, w] of missing) {
      const raw = path.join(out, f + '.raw.mp3');
      const a = [TTS, 'speak', w.text, '-v', w.v.voice, '-o', raw, '--max-cost', '0.2'];
      if (w.v.style) a.push('--instructions', w.v.style);
      if (w.v.speed) a.push('--speed', String(w.v.speed));
      for (let tries = 1; ; tries++) {   // a clip that comes back (nearly) silent is made again, up to 3 times
        execFileSync('python3', a, { stdio: ['ignore', 'ignore', 'inherit'], cwd: path.dirname(path.resolve(TTS)) });
        trim(raw, path.join(out, f)); fs.unlinkSync(raw);
        const d = seconds(path.join(out, f));
        if (d >= 0.3 + 0.1 * w.text.split(/\s+/).length || tries >= 3) { console.log('made ' + f + ' (' + d.toFixed(2) + ' s)  ' + w.spk + ': ' + w.text); break; }
        console.log('too short (' + d.toFixed(2) + ' s), again: ' + w.text);
      }
    }
    for (const f of have) if (!want.has(f)) { fs.unlinkSync(path.join(out, f)); console.log('removed ' + f); }
  }
  // the index: speaker|text -> [file, seconds]
  const rows = [];
  for (const [f, w] of want) {
    const p = path.join(out, f); if (!fs.existsSync(p)) continue;
    const dur = seconds(p);
    rows.push(`  ${JSON.stringify(w.spk + '|' + w.text)}: [${JSON.stringify('assets/voice/' + key + '/' + f)}, ${dur.toFixed(2)}],`);
  }
  const idx = path.join(DIR, key + '.voices.js');
  fs.writeFileSync(idx, `// Generated by tools/story/voice.js: the voice clips of story/${key}.js ("speaker|text" -> [file, seconds]).\n` +
    `var VOICE_CLIPS = VOICE_CLIPS || {};\nObject.assign(VOICE_CLIPS, {\n${rows.join('\n')}\n});\n`);
  console.log(`${key}: ${rows.length} clips in story/${key}.voices.js`);
}
if (!GO && !INDEX) console.log(`${total.missing} of ${total.lines} clips missing; making them costs about $${(total.words / 150 * PER_MIN).toFixed(3)}` +
  ' (plus a minimum per call). Run with --go --tts <openai_media.py> to make them.');
