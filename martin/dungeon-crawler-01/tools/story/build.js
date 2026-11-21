#!/usr/bin/env node
// Compiles the story sources (story/*.md, written in the dialogue format described in README.md, Dialogue) into
// story/story.js, the browser-readable form the game loads: one STORIES entry per source file (story.md ->
// STORIES.story, demo.md -> STORIES.demo). Conditions, effects and {…} text are JavaScript: they become functions
// here and are syntax-checked. Any mistake (unknown speaker, jump target or character, a bad line) is reported with
// its file and line, and nothing is written.
//
//   node tools/story/build.js
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..', '..'), DIR = path.join(ROOT, 'story'), OUT = path.join(DIR, 'story.js');
const CHAR_KEYS = ['name', 'sprite', 'starts', 'talk', 'leave'], CONV_KEYS = ['who', 'when', 'priority', 'starts', 'repeat'];
const HERO = /^(hero|you)$/i, TICK = '`';

function compile(file) {
  const src = fs.readFileSync(file, 'utf8').replace(/<!--[\s\S]*?-->/g, m => m.replace(/[^\n]/g, ''));   // comments out, lines kept
  const lines = src.split('\n'), errs = [], chars = {}, convs = [];
  const err = (n, msg) => errs.push(`${path.basename(file)}:${n + 1}: ${msg}`);
  let sec = null, node = null, list = null, fence = null, pending = [];   // pending: speakers and targets checked at the end
  const fn = (n, body, what) => {   // a function of the scope S (sloppy mode: `with` puts S's names in reach)
    const b = /\n|\/\//.test(body) ? body + '\n' : body + ' ';   // a line comment needs the closing brace on its own line
    try { new Function('S', 'with (S) { ' + b + '}'); } catch (e) { err(n, `bad JavaScript in ${what}: ${e.message}`); }
    return { __fn: 'function (S) { with (S) { ' + b + '} }' };
  };
  const cond = (n, e) => fn(n, 'return (' + e + ');', 'condition `' + e + '`');
  const text = (n, s) => {   // {expr} inside text: a template literal; \{ is a literal brace
    if (!/(^|[^\\]){/.test(s)) return s.replace(/\\{/g, '{');
    const t = s.replace(/[`$]/g, c => '\\' + c).replace(/(^|[^\\]){([^}]*)}/g, (m, a, e) => a + '${' + e + '}').replace(/\\\\{/g, '{');
    return fn(n, 'return `' + t + '`;', 'text');
  };
  const push = (n, it) => { if (!node) return err(n, 'a line outside a conversation or a character\'s @leave / @back'); sec.nodes[node].push(it); };
  const lead = s => { const m = s.match(/^`if\s+([^`]+)`\s*/); return m ? [m[1], s.slice(m[0].length)] : [null, s]; };
  const flush = () => { list = null; };
  lines.forEach((raw, n) => {
    const l = raw.trim();
    if (fence) { if (/^```\s*$/.test(l)) { push(fence.n, { t: 'do', f: fn(fence.n, fence.body.join('\n'), 'code block') }); fence = null; } else fence.body.push(raw); return; }
    if (!l) return;
    if (/^```/.test(l)) { flush(); fence = { n, body: [] }; return; }
    if (/^>/.test(l) || /^# /.test(l)) return;   // notes and the title
    let m;
    if ((m = l.match(/^## (Character|Conversation):\s*([\w-]+)\s*$/i))) {
      flush(); const id = m[2];
      if (/^char/i.test(m[1])) { if (chars[id]) err(n, 'character ' + id + ' defined twice'); sec = chars[id] = { kind: 'char', id, n, nodes: {} }; node = null; }
      else { if (convs.some(c => c.id === id)) err(n, 'conversation ' + id + ' defined twice'); sec = { kind: 'conv', id, n, nodes: { start: [] } }; convs.push(sec); node = 'start'; }
      return;
    }
    if (/^## /.test(l)) { flush(); sec = null; node = null; return; }   // any other heading: a chapter heading, no section
    if ((m = l.match(/^### (.+)$/))) {
      flush(); const lab = m[1].trim();
      if (!sec) return err(n, 'a ### node outside a conversation or a character');
      if (!/^@?[\w-]+$/.test(lab)) return err(n, 'node names are letters, digits, - and _ (or @leave / @back): ' + lab);
      if (lab[0] === '@' && lab !== '@leave' && lab !== '@back') return err(n, 'the only @ nodes are @leave and @back');
      if (sec.kind === 'char' && lab[0] !== '@') return err(n, 'a character has only @leave and @back nodes');
      if (sec.nodes[lab]) return err(n, 'node ' + lab + ' defined twice');
      sec.nodes[lab] = []; node = lab; return;
    }
    if ((m = l.match(/^- (\w+)(?::\s*(.*))?$/)) && sec && (sec.kind === 'char' || (node === 'start' && !sec.nodes.start.length))) {
      const k = m[1], v = (m[2] || '').trim().replace(/^`(.*)`$/, '$1');
      if (!(sec.kind === 'char' ? CHAR_KEYS : CONV_KEYS).includes(k)) return err(n, `unknown ${sec.kind === 'char' ? 'character' : 'conversation'} setting "${k}"`);
      if (k === 'starts' && !/^(click|near\s+\d+(\.\d+)?)$/.test(v)) return err(n, 'starts: click or near <tiles>');
      if ((k === 'talk' || k === 'leave' || k === 'priority') && !/^-?\d+(\.\d+)?$/.test(v)) return err(n, k + ': a number');
      sec[k] = k === 'when' ? cond(n, v) : k === 'repeat' ? true : k === 'starts' ? (v === 'click' ? 'click' : +v.split(/\s+/)[1]) : /^(talk|leave|priority)$/.test(k) ? +v : v;
      return;
    }
    if ((m = l.match(/^\d+\.\s+(.*)$/))) {   // a choice
      let s = m[1], c, d = null, to = null;
      [c, s] = lead(s);
      s = s.replace(/`do:\s*([^`]+)`/, (x, e) => { d = e; return ''; }).trim();
      s = s.replace(/\s*(?:->|→)\s*([\w@-]+)\s*$/, (x, t) => { to = t; return ''; }).trim();
      if (!s) return err(n, 'a choice without text');
      const opt = { text: text(n, s), if: c && cond(n, c), do: d && fn(n, d, 'do'), to };
      if (to) pending.push({ n, sec, to });
      if (list) list.opts.push(opt); else { list = { t: 'choice', opts: [opt] }; push(n, list); }
      return;
    }
    flush();
    if ((m = l.match(/^\*\*(.+?):\*\*\s*(.*)$/))) {
      const [c, s] = lead(m[2]); if (!s) return err(n, 'a line without text');
      const it = { t: 'say', who: m[1].trim(), text: text(n, s), if: c && cond(n, c) }; pending.push({ n, sec, say: it }); return push(n, it);
    }
    if ((m = l.match(/^(?:(`if\s+[^`]+`)\s*)?`do:\s*(.+)`$/))) { const c = m[1] && lead(m[1])[0]; return push(n, { t: 'do', f: fn(n, m[2], 'do'), if: c && cond(n, c) }); }
    if ((m = l.match(/^(?:(`if\s+[^`]+`)\s*)?(?:->|→)\s*([\w@-]+)$/))) { const c = m[1] && lead(m[1])[0]; pending.push({ n, sec, to: m[2] }); return push(n, { t: 'go', to: m[2], if: c && cond(n, c) }); }
    err(n, 'not a story line (a **Speaker:** line, a numbered choice, `do: …`, → target, a ### node, a - setting or a > note): ' + l.slice(0, 60));
  });
  if (fence) err(fence.n, 'a ``` code block that is never closed');
  // checks that need everything: speakers, jump targets, who
  const names = {};
  for (const id in chars) { names[id.toLowerCase()] = id; const nm = chars[id].name; if (nm) { names[nm.toLowerCase()] = id; names[nm.split(/\s+/)[0].toLowerCase()] = names[nm.split(/\s+/)[0].toLowerCase()] || id; } }
  for (const c of convs) if (!c.who) err(c.n, 'conversation ' + c.id + ' has no "- who:"'); else if (!chars[c.who]) err(c.n, 'conversation ' + c.id + ': no character ' + c.who);
  for (const p of pending) {
    if (p.say) { const w = p.say.who; if (HERO.test(w)) p.say.who = 'hero'; else if (names[w.toLowerCase()]) p.say.who = names[w.toLowerCase()]; else err(p.n, 'unknown speaker ' + w + ' (a character id or name, or Hero)'); continue; }
    if (p.to === 'end') continue;
    const local = p.sec.kind === 'conv' && p.sec.nodes[p.to];
    if (!local && !convs.some(c => c.id === p.to)) err(p.n, 'unknown jump target ' + p.to + ' (a node of this conversation, another conversation, or end)');
  }
  for (const c of convs) for (const lab in c.nodes) if (lab !== 'start' && lab[0] !== '@' && !lines.some((l, i) => new RegExp('(->|→)\\s*' + lab + '\\b').test(l)))
    err(c.n, `conversation ${c.id}: node ${lab} is never jumped to`);
  const strip = o => { const r = {}; for (const k in o) if (!['kind', 'n'].includes(k) && o[k] != null && !(k === 'id' && o.kind === 'char')) r[k] = o[k]; return r; };
  return { errs, data: { chars: Object.fromEntries(Object.entries(chars).map(([k, v]) => [k, strip(v)])), convs: convs.map(strip) } };
}
function ser(v, ind = '') {   // JavaScript source for the data (functions as code)
  if (v && v.__fn) return v.__fn;
  if (Array.isArray(v)) return v.length ? '[\n' + v.map(x => ind + '  ' + ser(x, ind + '  ')).join(',\n') + '\n' + ind + ']' : '[]';
  if (v && typeof v === 'object') {
    const ks = Object.keys(v).filter(k => v[k] != null && v[k] !== false);
    return '{ ' + ks.map(k => (/^[A-Za-z_$][\w$]*$/.test(k) ? k : JSON.stringify(k)) + ': ' + ser(v[k], ind + '  ')).join(', ') + ' }';
  }
  return JSON.stringify(v);
}
const files = fs.readdirSync(DIR).filter(f => f.endsWith('.md')).sort();
let all = [], out = '// Generated by tools/story/build.js from ' + files.map(f => 'story/' + f).join(', ') + '. Do not edit: edit the .md and rebuild.\n' +
  '// See README.md, Dialogue, for the format.\nvar STORIES = {\n';
for (const f of files) {
  const { errs, data } = compile(path.join(DIR, f)); all = all.concat(errs);
  out += '  ' + JSON.stringify(f.replace(/\.md$/, '')) + ': ' + ser(data, '  ') + ',\n';
}
out += '};\n';
if (all.length) { console.error(all.join('\n')); console.error(all.length + ' error(s): story.js not written.'); process.exit(1); }
fs.writeFileSync(OUT, out);
console.log('story/story.js written from ' + files.join(', ') + ' (' + Math.round(out.length / 1024) + ' KB).');
