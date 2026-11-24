#!/usr/bin/env node
// Checks the dialogue files (story/*.js, the format in README.md, Dialogue) without changing them: every item is one
// of the known forms, speakers and the characters conversations belong to exist, jump targets exist, every node is
// reached, and the JavaScript in conditions, effects and {…} text parses. Lists each mistake with its file and where
// in it; exits with 1 if there are any.
//
//   node tools/story/check.js
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = path.resolve(__dirname, '..', '..'), DIR = path.join(ROOT, 'story');
const CHAR_KEYS = ['name', 'sprite', 'hail', 'walkUp', 'wander', 'leave', 'nodes'];
const CONV_KEYS = ['id', 'who', 'when', 'priority', 'hail', 'walkUp', 'repeat', 'nodes'];
const ITEM_KEYS = { say: ['say', 'text', 'if'], do: ['do', 'if'], go: ['go', 'if'], choose: ['choose', 'if'] };
const OPT_KEYS = ['text', 'if', 'do', 'to'];
// Ids the game gives its own entities (README, Dialogue: who is who): usable without an entry in chars
const GAME_IDS = ['aldric', 'borin', 'mirela', 'tobias', 'boss', 'champion', 'skeleton', 'ghoul', 'spider', 'wraith', 'demon'];

const files = fs.readdirSync(DIR).filter(f => f.endsWith('.js') && !f.endsWith('.voices.js')).sort();   // (not the voice indexes)
const ctx = vm.createContext({});
let errs = [], total = 0;
for (const f of files) {
  try { vm.runInContext(fs.readFileSync(path.join(DIR, f), 'utf8'), ctx, { filename: f }); }
  catch (e) { errs.push(f + ': does not run: ' + e.message); }
}
const STORIES = ctx.STORIES || {};
for (const key in STORIES) {
  const st = STORIES[key], file = 'story/' + key + '.js', err = (where, msg) => errs.push(file + ': ' + where + ': ' + msg);
  const js = (where, src, kind) => {   // the same wrapping as the game's storyFn
    if (typeof src !== 'string') return err(where, 'should be a string of JavaScript');
    const body = kind === 'expr' ? 'return (' + src + ');' : kind === 'text' ? 'return `' + src + '`;' : src + '\n';
    try { new Function('S', 'with (S) { ' + body + ' }'); } catch (e) { err(where, 'bad JavaScript (' + e.message + '): ' + src); }
  };
  const text = (where, s) => {
    if (typeof s !== 'string' || !s.trim()) return err(where, 'needs a text');
    if (!/(^|[^\\]){/.test(s)) return;
    js(where + ' text', s.replace(/[`$]/g, c => '\\' + c).replace(/(^|[^\\]){([^}]*)}/g, (m, a, e) => a + '${' + e + '}'), 'text');
  };
  const keys = (where, o, allowed) => { for (const k in o) if (!allowed.includes(k)) err(where, 'unknown key "' + k + '"'); };
  const sets = (where, o) => {   // hail, walkUp, wander, leave, repeat
    if (o.hail != null && !(typeof o.hail === 'number' && o.hail >= 0)) err(where, 'hail: a distance in tiles (0: it waits for a click)');
    for (const k of ['walkUp', 'wander', 'repeat']) if (o[k] != null && typeof o[k] !== 'boolean') err(where, k + ': true or false');
    if (o.leave != null && !(typeof o.leave === 'number' && o.leave > 0)) err(where, 'leave: a distance in tiles');
  };
  if (!st || typeof st !== 'object') { err('top', 'not an object'); continue; }
  keys('top', st, ['chars', 'convs', 'voices']);
  const chars = st.chars || {}, convs = st.convs || [];
  if (!Array.isArray(convs)) { err('top', 'convs should be a list'); continue; }
  const ids = new Set([...GAME_IDS, ...Object.keys(chars)]), convIds = new Set();
  for (const v of convs) { if (convIds.has(v.id)) err(v.id, 'conversation defined twice'); convIds.add(v.id); }
  // items: what they are, their JavaScript, their speakers; jumps collected per conversation
  const items = (where, list, jumps) => {
    if (!Array.isArray(list)) return err(where, 'a node should be a list of items');
    list.forEach((it, i) => {
      const w = where + ' #' + (i + 1), kind = ['say', 'choose', 'go', 'do'].find(k => it && it[k] != null);
      if (!kind) return err(w, 'an item that is none of { say, text }, { do }, { go }, { choose: [...] }');
      keys(w, it, ITEM_KEYS[kind]);
      if (it.if != null) js(w + ' if', it.if, 'expr');
      if (kind === 'say') { if (it.say !== 'hero' && !ids.has(it.say)) err(w, 'unknown speaker ' + it.say + ' (hero, a character in chars, or a game id)'); text(w, it.text); }
      if (kind === 'do') js(w + ' do', it.do, 'code');
      if (kind === 'go') jumps.push([w, it.go]);
      if (kind === 'choose') {
        if (!Array.isArray(it.choose) || !it.choose.length) return err(w, 'choose: a list of choices');
        it.choose.forEach((o, k) => { const ow = w + ' choice ' + (k + 1); keys(ow, o, OPT_KEYS); text(ow, o.text);
          if (o.if != null) js(ow + ' if', o.if, 'expr'); if (o.do != null) js(ow + ' do', o.do, 'code'); if (o.to != null) jumps.push([ow, o.to]); });
      }
    });
  };
  // voices: { speaker: { voice, style } }, the hero's as { m: {…}, f: {…} } (the hero's looks' voices, HERO_VOICE)
  const vs = st.voices || {}, voiceOk = (w, v) => { if (!v || typeof v.voice !== 'string') err(w, 'a voice needs { voice, style }'); else keys(w, v, ['voice', 'style', 'speed']); };
  for (const k in vs) {
    if (k === 'hero') { for (const g of ['m', 'f']) voiceOk('voices.hero.' + g, vs.hero[g]); keys('voices.hero', vs.hero, ['m', 'f']); }
    else if (!ids.has(k)) err('voices', 'no character ' + k); else voiceOk('voices.' + k, vs[k]);
  }
  for (const id in chars) {
    const c = chars[id]; keys(id, c, CHAR_KEYS); sets(id, c);
    const jumps = [];
    for (const n in c.nodes || {}) { if (n !== '@leave' && n !== '@back') err(id, 'a character has only @leave and @back nodes, not ' + n); items(id + ' ' + n, c.nodes[n], jumps); }
    for (const [w, to] of jumps) if (to !== 'end' && !convIds.has(to)) err(w, 'unknown jump target ' + to + ' (another conversation or end)');
  }
  for (const v of convs) {
    total++;
    const where = v.id || 'a conversation without an id'; keys(where, v, CONV_KEYS); sets(where, v);
    if (!v.who) err(where, 'no who'); else if (!ids.has(v.who)) err(where, 'who: no character ' + v.who);
    if (v.when != null) js(where + ' when', v.when, 'expr');
    if (v.priority != null && typeof v.priority !== 'number') err(where, 'priority: a number');
    const nodes = v.nodes || {}, jumps = [];
    if (!nodes.start) err(where, 'no start node');
    for (const n in nodes) { if (n[0] === '@' && n !== '@leave' && n !== '@back') err(where, 'the only @ nodes are @leave and @back'); items(where + ' ' + n, nodes[n], jumps); }
    for (const [w, to] of jumps) if (to !== 'end' && !nodes[to] && !convIds.has(to)) err(w, 'unknown jump target ' + to + ' (a node of this conversation, another conversation, or end)');
    for (const n in nodes) if (n !== 'start' && n[0] !== '@' && !jumps.some(j => j[1] === n)) err(where, 'node ' + n + ' is never jumped to');
  }
}
if (errs.length) { console.error(errs.join('\n')); console.error(errs.length + ' mistake(s).'); process.exit(1); }
console.log('story: ' + files.join(', ') + ' are fine (' + total + ' conversations).');
