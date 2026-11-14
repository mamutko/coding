#!/usr/bin/env node
// Builds catalog.html (the monster and item catalog) from the game's own data. It loads index.html in a headless
// browser (like tools/simulation), reads the monster, item, affix and potion tables and computes the monster stats
// per depth with makeMonster, then writes the data into template.html. See README.md in this folder.
//
//   node tools/catalog/build.js
const http = require('http'), fs = require('fs'), path = require('path');
let chromium;
try { ({ chromium } = require('playwright')); } catch { console.error('Needs Playwright (npm i playwright; npx playwright install chromium).'); process.exit(1); }

const ROOT = path.resolve(__dirname, '..', '..');   // the game folder (index.html, assets/)
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]).replace(/^\/$/, '/index.html'));
  if (!f.startsWith(ROOT) || !fs.existsSync(f)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(res);
});
const DEPTHS = 12;   // monster stats are listed for depths 1..DEPTHS

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const b = await chromium.launch(); const p = await b.newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(`http://127.0.0.1:${server.address().port}/`);
  await p.waitForSelector('#heroName');   // a fresh browser has no saved heroes: the New Hero name field is open
  await p.fill('#heroName', 'Catalog'); await p.press('#heroName', 'Enter'); await p.click('#startBtn'); await p.waitForTimeout(200);
  const data = await p.evaluate(DEPTHS => {
    G.running = false;
    const mons = {};
    for (const k in MON) {
      const perDepth = [];
      for (let d = 1; d <= DEPTHS; d++) {   // normal tier, exactly as makeMonster builds it
        const m = makeMonster(k, 0, 0, d, false, false, true);
        perDepth.push({ hp: m.maxHp, dmg: m.dmg.map(v => +v.toFixed(1)), armor: m.armor, speed: +m.speed.toFixed(2), xp: m.xp,
          limit: roomLimit(k, d) === Infinity ? null : roomLimit(k, d), champ: canChamp(k, d) });
      }
      mons[k] = { ...MON[k], perDepth };
    }
    return { version: VERSION, mons, tier: TIER, monBase: MON_BASE, monScale: MON_SCALE, monSpeed: MON_SPEED,
      newLimit: NEW_LIMIT, champAfter: CHAMP_AFTER, bossFrom: BOSS_FROM, bossRoomFrom: BOSS_ROOM_FROM, loneAt: LONE_AT,
      bases: BASES, kinds: KIND_INFO, slotLabel: SLOT_LABEL, statLabel: STAT_LABEL, affix: AFFIX, affixFrom: AFFIX_FROM,
      affixW: AFFIX_W, jewelMult: JEWEL_MULT, potions: POTIONS, bomb: BOMB, fire: FIRE, iron: IRON, heal: HEAL, magicFrom: MAGIC_FROM,
      rareFrom: RARE_FROM, ringFrom: RING_FROM, amuletFrom: AMULET_FROM, magicOdds: MAGIC_ODDS, rareOdds: RARE_ODDS,
      meta: META, heroSpeed: 4.2, depths: DEPTHS, propsW: IMG.props.width, itemsW: IMG.items.width,
      levels: Array.from({ length: DEPTHS }, (_, i) => ({ bossRoom: bossRoomAt(i + 1), boss: i + 1 >= BOSS_FROM, big: bigRoomAt(i + 1) })) };
  }, DEPTHS);
  await b.close(); server.close();
  if (errs.length) { console.error('Page errors:', errs); process.exit(1); }
  const tpl = fs.readFileSync(path.join(__dirname, 'template.html'), 'utf8');
  const out = tpl.replace('/*DATA*/null', JSON.stringify(data));
  fs.writeFileSync(path.join(ROOT, 'catalog.html'), out);
  console.log(`catalog.html written (game v${data.version}, ${Object.keys(data.mons).length} monsters, ${Object.keys(data.bases).length} item types).`);
})();
