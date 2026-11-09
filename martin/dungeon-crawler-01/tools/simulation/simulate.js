#!/usr/bin/env node
// Balance simulation for Dungeon Crawler 01: simulated heroes clear depths 1..N of the real game (loaded in a
// headless browser, so level generation, monster stats, loot, XP and gear stats are the game's own code) and
// equip the best gear they find. Only the fights are modelled. See README.md in this folder.
//
//   node tools/simulation/simulate.js [--runs 200] [--depths 6] [--travel 40] [--json out.json]
//
// Prints a Markdown report (hero vs. monsters per depth, whole-level outcome, damage sources) to stdout.
const http = require('http'), fs = require('fs'), path = require('path');
let chromium;
try { ({ chromium } = require('playwright')); } catch { console.error('Needs Playwright (npm i playwright; npx playwright install chromium).'); process.exit(1); }

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const RUNS = +arg('runs', 200), MAXD = +arg('depths', 6), JSON_OUT = arg('json', null);
// Fight-model parameters (see README.md): time step, walking time between rooms (s, regenerating life),
// health potion threshold (share of max life), max monsters fighting in melee at once, free time a bow gets
// before monsters reach the hero (s).
const P = { DT: 0.05, TRAVEL: +arg('travel', 40), POT_AT: +arg('pot', 0.35), MELEE_MAX: +arg('melee', 5), BOW_FREE: 1.5 };

const ROOT = path.resolve(__dirname, '..', '..');   // the game folder (index.html, assets/)
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]).replace(/^\/$/, '/index.html'));
  if (!f.startsWith(ROOT) || !fs.existsSync(f)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(res);
});

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const url = `http://127.0.0.1:${server.address().port}/`;
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 900, height: 600 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(url); await p.waitForFunction(() => !document.getElementById('startBtn').disabled);
  await p.fill('#heroName', 'Sim'); await p.click('#startBtn'); await p.waitForTimeout(300);
  const res = await p.evaluate(([RUNS, MAXD, P]) => {
    window.sfx = () => {}; window.log = () => {};
    const { DT, TRAVEL, POT_AT, MELEE_MAX, BOW_FREE } = P;
    const ref = d => makeMonster('skeleton', 0, 0, d);   // reference monster for gear scoring
    function dpsVs(h, m) {   // expected single-target DPS of the hero's weapon against monster m
      const w = weaponOf(h), [mn, mx] = weaponDamageRange(h), c = Math.min(1, h.st.crit / 100);
      return (mn + mx) / 2 * (1 + 0.75 * c) * (1 - armorReduce(m.armor, h.lvl)) / w.cd;
    }
    const ehp = (h, d) => h.st.maxHp / (1 - armorReduce(h.st.armor, d));
    function score(h, d) { const m = ref(d), w = weaponOf(h); let s = dpsVs(h, m);
      if (w.kind === 'axe') s *= 1.25; else if (w.kind === 'sword') s *= 1.12; else if (w.kind === 'bow') s *= 1.15;
      return s * ehp(h, d); }
    function equipBest(h, d, bag) {
      const all = [...Object.values(h.equip).filter(Boolean), ...bag];
      const SL = ['weapon', 'head', 'chest', 'hands', 'feet', 'amulet', 'ring1', 'ring2'];
      for (let pass = 0; pass < 2; pass++) for (const sl of SL) {
        const want = sl.startsWith('ring') ? 'ring' : sl;
        let best = h.equip[sl], bs = -1;
        for (const it of [null, ...all.filter(x => x.slot === want)]) {
          if (it && Object.entries(h.equip).some(([k, v]) => v === it && k !== sl)) continue;
          if (!it && sl === 'weapon') continue;
          h.equip[sl] = it; recalc(); const s = score(h, d); if (s > bs + 1e-9) { bs = s; best = it; }
        }
        h.equip[sl] = best; recalc();
      }
      bag.length = 0;
    }
    function drink(h, pot, st) { const s = stackOf(pot); if (!s || s.count <= 0) return false;
      s.count--; if (!s.count) h.inv[h.inv.indexOf(s)] = null;
      if (pot === 'health') h.hp = Math.min(h.st.maxHp, h.hp + h.st.maxHp * 0.35); else { h.ironT = IRON.dur; recalc(); }
      st.pots[pot]++; return true; }
    function fight(group, d, st) {
      const h = G.hero, w0 = weaponOf(h), bow = w0.kind === 'bow';
      for (const m of group) m.simCd = rnd() * m.b.cd + (m.b.ranged ? 0.45 : 0.32) + (bow ? BOW_FREE : 0.3);
      if ((group.some(m => m.boss || m.champ) || group.length >= 6) && !(h.ironT > 0)) drink(h, 'ironskin', st);
      let atk = 0, t = 0;
      while (group.some(m => !m.dead) && t < 900) {
        t += DT; h.hp = Math.min(h.st.maxHp, h.hp + h.st.regen * DT);
        if (h.ironT > 0 && (h.ironT -= DT) <= 0) { h.ironT = 0; recalc(); }
        if (h.hp < h.st.maxHp * POT_AT && drink(h, 'health', st)) atk = Math.max(atk, USE_T);
        const alive = group.filter(m => !m.dead);
        if ((atk -= DT) <= 0) {
          const w = weaponOf(h), [mn, mx] = weaponDamageRange(h);
          const roll = () => { const c = rnd() * 100 < h.st.crit; return [(mn + rnd() * (mx - mn)) * (c ? 1.75 : 1), c]; };
          const tg = alive.reduce((a, m) => m.hp < a.hp ? m : a);   // focus the weakest
          const [dm, c] = roll(); damageMonster(tg, dm, c);
          if (w.kind !== 'bow') { const extra = alive.filter(m => m !== tg && !m.dead).slice(0, w.kind === 'axe' ? 2 : 1);
            for (const m of extra) { const [x, cc] = roll(); damageMonster(m, x * CLEAVE, cc); } }
          atk = w.cd;
        }
        let melee = 0;
        for (const m of alive) {
          if (m.dead) continue;
          if (!m.b.ranged && ++melee > MELEE_MAX) continue;
          if ((m.simCd -= DT) > 0) continue;
          m.simCd = m.b.cd;
          const raw = m.dmg[0] + rnd() * (m.dmg[1] - m.dmg[0]);
          const v = Math.max(1, Math.round(raw * (1 - armorReduce(h.st.armor, m.lvl))));
          h.hp -= v; st.taken += v; const cat = m.boss ? 'boss' : m.champ ? 'champ' : m.type; st.src[cat] = (st.src[cat] || 0) + v;
          if (h.hp <= 0) { st.deaths++; st.deathAt[st.room] = (st.deathAt[st.room] || 0) + 1; h.hp = h.st.maxHp; }
          st.minHp = Math.min(st.minHp, Math.max(0, h.hp) / h.st.maxHp);
        }
      }
      st.fightT += t;
    }
    function snap(h, d) {
      const m = ref(d), w = weaponOf(h), dm = makeMonster('demon', 0, 0, d), dps = dpsVs(h, m);
      const mDps = m2 => (m2.dmg[0] + m2.dmg[1]) / 2 * (1 - armorReduce(h.st.armor, m2.lvl)) / m2.b.cd;
      const [mn, mx] = weaponDamageRange(h);
      return { lvl: h.lvl, hp: h.st.maxHp, armor: h.st.armor, dr: armorReduce(h.st.armor, d), weapon: w.kind, wname: w.name,
        dmin: mn, dmax: mx, aps: 1 / w.cd, crit: h.st.crit, dps, score: score(h, d),
        skelTTK: m.maxHp / dps, skelKillsHero: h.st.maxHp / mDps(m), demonTTK: dm.maxHp / dpsVs(h, dm), demonKillsHero: h.st.maxHp / mDps(dm),
        rarity: Object.values(h.equip).filter(Boolean).map(i => i.rarity[0]).join('') };
    }
    const out = [];
    for (let run = 0; run < RUNS; run++) {
      G.hero = newHero(); recalc(); G.hero.hp = G.hero.st.maxHp; G.items = []; G.dead = false;
      const h = G.hero, runOut = [];
      for (let d = 1; d <= MAXD; d++) {
        G.depth = d; G.items = []; G.fx = []; G.texts = []; G.proj = [];
        buildLevel(d);
        const st = { d, enter: snap(h, d), deaths: 0, pots: { health: 0, ironskin: 0 }, taken: 0, minHp: 1, fightT: 0,
          mons: G.monsters.length, champs: G.monsters.filter(m => m.champ).length, boss: !!G.map.boss, potsFound: 0, items: 0, src: {}, groups: [], deathAt: {}, room: '' };
        const rooms = G.map.rooms.slice().sort((a, b) => (a === G.map.bossRoom) - (b === G.map.bossRoom));
        const bag = [];
        const loot = () => {
          for (const fi of G.items.splice(0)) {
            const it = fi.item;
            if (it.slot === 'use') { const s = stackOf(it.pot); if (s) s.count += it.count; else h.inv[h.inv.indexOf(null)] = it; st.potsFound += it.count; gainXp(1 + d); }
            else { bag.push(it); st.items++; gainXp(2 * d); }
          }
          equipBest(h, d, bag);
        };
        for (const r of rooms) {
          const group = G.monsters.filter(m => !m.dead && roomAt(m.x, m.y) === r);
          st.room = r === G.map.bossRoom ? 'boss' : G.objects.some(o => o.grey && roomAt(o.x, o.y) === r) ? 'big' : group.some(m => m.champ) ? 'champ' : 'normal';
          if (group.length) { st.groups.push(group.length); fight(group, d, st); }
          for (const o of G.objects.slice()) if (['chest', 'urn', 'bones', 'gold', 'door'].includes(o.type) && roomAt(o.x, o.y) === r) act({ kind: 'obj', r: o });
          loot();
          h.hp = Math.min(h.st.maxHp, h.hp + h.st.regen * TRAVEL);
        }
        for (const o of G.objects.slice()) if (['chest', 'urn', 'bones', 'gold', 'door'].includes(o.type)) act({ kind: 'obj', r: o });
        loot();
        st.exit = snap(h, d); st.potsLeft = { health: (stackOf('health') || { count: 0 }).count, ironskin: (stackOf('ironskin') || { count: 0 }).count };
        runOut.push(st);
      }
      out.push(runOut);
    }
    return { out, MON: { skeleton: MON.skeleton, demon: MON.demon } };
  }, [RUNS, MAXD, P]);
  await b.close(); server.close();
  if (errs.length) console.error('Page errors:', errs.slice(0, 3));
  if (JSON_OUT) fs.writeFileSync(JSON_OUT, JSON.stringify(res.out));
  report(res.out, res.MON);
})();

function report(r, MONS) {
  const med = a => { a = a.filter(x => x != null).sort((x, y) => x - y); return a.length ? a[Math.floor(a.length / 2)] : null; };
  const mean = a => a.reduce((s, x) => s + x, 0) / a.length;
  const f = (x, n = 1) => x == null ? '—' : x.toFixed(n);
  // normal-tier stats at depth d, as makeMonster computes them (+22 % life and damage, +3 armor per depth)
  const mon = (k, d) => { const m = MONS[k], s = Math.pow(1.22, d - 1); return `${Math.round(m.hp * s)} / ${((m.dmg[0] + m.dmg[1]) / 2 * s).toFixed(1)} / ${m.armor + 3 * (d - 1)}`; };
  const DEM = MONS.demon.minD;
  const out = [];
  out.push(`Runs: ${r.length}, depths 1–${r[0].length}, travel ${P.TRAVEL} s between rooms, potion below ${P.POT_AT * 100} % life, max ${P.MELEE_MAX} in melee.`, '');
  out.push('### Hero vs. normal monsters (hero on arrival, medians)', '',
    '| Depth | Hero level | Life | Armor (damage cut) | Hero DPS | Skeleton life / hit / armor | Pit Demon life / hit / armor | Hero kills skeleton | Skeleton kills hero | Hero kills demon | Demon kills hero |',
    '|---|---|---|---|---|---|---|---|---|---|---|');
  for (let d = 0; d < r[0].length; d++) {
    const L = r.map(x => x[d]), e = k => med(L.map(x => x.enter[k])), D = d + 1;
    out.push(`| ${D} | ${e('lvl')} | ${e('hp')} | ${e('armor')} (${f(e('dr') * 100, 0)} %) | ${f(e('dps'))} | ${mon('skeleton', D)} | ${D >= DEM ? mon('demon', D) : '—'} | ${f(e('skelTTK'), 2)} s | ${f(e('skelKillsHero'), 0)} s | ${D >= DEM ? f(e('demonTTK')) + ' s' : '—'} | ${D >= DEM ? f(e('demonKillsHero'), 0) + ' s' : '—'} |`);
  }
  out.push('', '### Whole level (means)', '',
    '| Depth | Monsters | Champions | Avg / largest room pack | Damage taken (× max life) | Potions found | Health potions drunk | Iron skin drunk | Runs with a death | Deaths per run |',
    '|---|---|---|---|---|---|---|---|---|---|');
  for (let d = 0; d < r[0].length; d++) {
    const L = r.map(x => x[d]), g = L.flatMap(x => x.groups);
    out.push(`| ${d + 1} | ${f(mean(L.map(x => x.mons)), 0)} | ${f(mean(L.map(x => x.champs)))} | ${f(mean(g))} / ${Math.max(...g)} | ${f(mean(L.map(x => x.taken / x.enter.hp)))}× | ${f(mean(L.map(x => x.potsFound)))} | ${f(mean(L.map(x => x.pots.health)))} | ${f(mean(L.map(x => x.pots.ironskin)))} | ${f(L.filter(x => x.deaths).length / L.length * 100, 0)} % | ${f(mean(L.map(x => x.deaths)), 2)} |`);
  }
  out.push('', '### Share of damage taken, by source', '', '| Depth | Skeleton | Ghoul | Spider | Wraith | Pit Demon | Champions | Boss |', '|---|---|---|---|---|---|---|---|');
  for (let d = 0; d < r[0].length; d++) {
    const src = {}; let tot = 0; for (const x of r.map(x => x[d])) for (const k in x.src) { src[k] = (src[k] || 0) + x.src[k]; tot += x.src[k]; }
    out.push(`| ${d + 1} | ` + ['skeleton', 'ghoul', 'spider', 'wraith', 'demon', 'champ', 'boss'].map(k => src[k] ? f(src[k] / tot * 100, 0) + ' %' : '—').join(' | ') + ' |');
  }
  out.push('', '### Deaths per run, by room kind', '', '| Depth | Normal room | Room with a champion | Big room | Boss room |', '|---|---|---|---|---|');
  for (let d = 0; d < r[0].length; d++) {
    const L = r.map(x => x[d]), k = n => f(mean(L.map(x => x.deathAt[n] || 0)), 2);
    out.push(`| ${d + 1} | ${k('normal')} | ${k('champ')} | ${k('big')} | ${k('boss')} |`);
  }
  console.log(out.join('\n'));
}
