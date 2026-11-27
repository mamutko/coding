// =====================================================================================
//  The Rift (multiplayer.md; README, The Rift): the portal and its dial on the surface, realm ids and names, and the
//  Rift itself, a large one-level dungeon beyond the portal. Phase 2: played alone (no networking yet).
//  Loaded before the game's main script; everything here runs only once the game is up.
// =====================================================================================
// The portal on the surface: its arch stands on the line of tiles x + y = const, west to east, facing south (toward
// the crypt); `at` is the ground point in the middle of the arch's base line (world tiles), about 60 tiles north of
// the crypt. The dial lies in front of it (`dial`, its centre), META.portal.dialR tiles in radius. `clear`: no trees
// grow within this many tiles of the arch. The Rift: its rooms `size` tiles a side, `rooms` of them, and a strip `band`
// tiles deep beyond their north-east edge for the lake; `quiet`: rooms by its portal left (nearly) empty; `share`: the
// part of the ordinary rooms the founder fills, and each who joins of those still free; `great`: how many players' worth
// the lake and the big room are topped up to (riftRestock)
const RIFT = { at: [-29, -29], dial: [-23, -23], clear: 9, size: 110, band: 36, rooms: 34, quiet: 2, share: 1 / 3, great: 2 };

// The arch's four tiles, from west to east: [x, y, role] with role 'pillar' (blocked) or 'gate'. gx, gy (whole
// numbers): the ground point in the middle of its base line, which runs through the four tiles' centres.
function portalTiles(gx, gy) {
  return [-1.5, -0.5, 0.5, 1.5].map(t => [Math.floor(gx + t), Math.floor(gy - t), Math.abs(t) > 1 ? 'pillar' : 'gate']);
}
// in the gate: between the pillars (across: |(x − y) − (gx − gy)| < 1.6) and stepped onto the base line or past it
// (x + y less than 0.35 in front of it)
const onGate = (o, e) => Math.abs((e.x - e.y) - (o.x - o.y)) < 1.6 && e.x + e.y - (o.x + o.y) < 0.35 && e.x + e.y - (o.x + o.y) > -1.5;

// ---- The dial: which realm the portal opens
// Items lying on the dial (within its radius of its centre) choose the realm: the realm key is the sorted list of
// those items written out in full except their ids (base, rarity, name, affixes, count, a scroll of return's depth),
// so two ordinary items of the same type are the same, and a magic or rare one makes the realm private.
const dialHas = (wx, wy) => Math.hypot(wx - RIFT.dial[0], wy - RIFT.dial[1]) <= META.portal.dialR;
function dialItems() {   // the floor items on the dial, on the surface: [{ fi, wx, wy }]
  if (!G || G.depth !== 0 || G.rift || !G.surf) return [];
  const sv = G.surf, out = [];
  for (const fi of G.items) { const wx = fi.x + sv.ox, wy = fi.y + sv.oy; if (dialHas(wx, wy)) out.push({ fi, wx, wy }); }
  for (const fi of sv.items) if (!G.items.includes(fi) && dialHas(fi.wx, fi.wy)) out.push({ fi, wx: fi.wx, wy: fi.wy });
  return out;
}
function itemKey(it) {
  const st = it.stats || {}, stats = Object.keys(st).sort().map(k => k + st[k]).join(',');
  return [it.base, it.rarity, it.name, stats, it.count || 1, it.depth || ''].join('|');
}
const realmKey = items => items.map(itemKey).sort().join(';');
function realmHash(s) {   // 50 bits of cyrb53 in base 32 (10 characters)
  let h1 = 0xdeadbeef, h2 = 0x41c6ce57;
  for (let i = 0; i < s.length; i++) { const c = s.charCodeAt(i); h1 = Math.imul(h1 ^ c, 2654435761); h2 = Math.imul(h2 ^ c, 1597334677); }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
  const A = '0123456789abcdefghjkmnpqrstvwxyz'; let out = '', a = h1 >>> 0, b = h2 >>> 0;
  for (let i = 0; i < 10; i++) { out += A[(a ^ (b << (i % 5))) & 31]; a = (a >>> 5) | ((b & 31) << 27); b >>>= 5; }
  return out;
}
const RIFT_A = ['Ashen', 'Hollow', 'Weeping', 'Silent', 'Drowned', 'Burning', 'Frozen', 'Sunken', 'Shattered', 'Forgotten', 'Howling', 'Bleeding',
  'Gilded', 'Withered', 'Starless', 'Crimson', 'Pale', 'Iron', 'Bone', 'Shadowed', 'Broken', 'Endless', 'Hungry', 'Veiled', 'Thorned', 'Cinder',
  'Moonless', 'Rotting', 'Black', 'Grey', 'Whispering', 'Last'];
const RIFT_B = ['Deep', 'Halls', 'Hollow', 'Vault', 'Maw', 'Warren', 'Abyss', 'Barrow', 'Sanctum', 'Labyrinth', 'Depths', 'Catacombs', 'Pit', 'Crossing',
  'Gate', 'Throne', 'Reach', 'Chasm', 'Nest', 'Cellars', 'Wastes', 'Mire', 'Spire', 'Tombs', 'Rookery', 'Furnace', 'Garden', 'Archive', 'Well',
  'Gallows', 'Cradle', 'Choir'];
const realmName = hash => { const A = '0123456789abcdefghjkmnpqrstvwxyz', i = A.indexOf(hash[0]) ^ A.indexOf(hash[5]), j = A.indexOf(hash[1]) ^ A.indexOf(hash[6]);
  return RIFT_A[i] + ' ' + RIFT_B[j]; };
// pvp: a sword (any) on the dial draws blades: in that realm heroes can hurt each other (README, The Rift: Player
// against player)
const isSword = it => !!(BASES[it.base] && BASES[it.base].kind === 'sword');
function realmOf(items) {   // the realm a set of dial items opens
  const key = realmKey(items), hash = realmHash(key);
  return { id: 'v' + VERSION + '-' + hash, hash, name: realmName(hash), key, open: !items.length, pvp: items.some(isSword) };
}
const currentRealm = () => realmOf(dialItems().map(d => d.fi.item));
// the dial's items go into the save (hero.dial) and lie on the dial again when the surface is built
function syncDial() { if (G && G.depth === 0 && !G.rift && G.surf) G.hero.dial = dialItems().map(d => d.fi.item); }
function restoreDial(sv) {
  const its = G.hero.dial || [], n = its.length;
  its.forEach((item, i) => { const a = i / Math.max(1, n) * Math.PI * 2 + 0.4, r = n > 1 ? 0.95 : 0;
    sv.items.push({ item, wx: RIFT.dial[0] + Math.cos(a) * r, wy: RIFT.dial[1] + Math.sin(a) * r, t: rnd() * 6 }); });
}

// ---- Going through: no question. Stepping into a portal's gate (or clicking the portal) goes through at once:
// into the Rift from the surface, out of it from inside. Again only once the hero has stepped off the gate.
const RA = { o: null, away: true };   // away: the hero has stepped off the gate since; busy: connecting (riftWait)
function riftCheck() {   // every frame: the hero on a gate tile of a portal goes through, once, until it steps off again
  const h = G.hero; if (G.dead || !G.running || RA.busy) return;
  const o = G.objects.find(p => p.type === 'portal' && Math.abs(p.x - h.x) < 4 && Math.abs(p.y - h.y) < 4);
  const on = o && onGate(o, h);
  if (!on) { RA.away = true; return; }
  if (!RA.away) return;
  RA.away = false; riftGo();
}
function riftGo() { if (RA.busy) return; if (G.rift) leaveRift(); else enterRift(); }
function riftClose() { RA.o = null; }   // (leaving a level: nothing to close any more)
const riftAskOpen = () => false;

// ---- Entering and leaving
async function enterRift() {
  if (G.rift || G.depth !== 0 || RA.busy) return;
  const h = G.hero, g = G; syncDial();
  h.surfAt = 'portal';   // saved: resumed from this save, the hero stands before the portal
  if (saveHero()) log('Progress saved.', '#a99c86');
  h.surfAt = null;
  const r = currentRealm(), d = Math.max(1, h.maxDepth || 1);
  // join the realm (net.js): found it, join the players already in it, or (no connection) go in alone
  riftWait(true);   // connecting: the surface goes on, without the hero, the HUD or any input
  const res = await netJoin(r.id, { name: h.name, lvl: h.lvl, look: h.look || 'hero', depth: d });
  riftWait(false);
  if (G !== g || G.dead || G.rift || G.depth !== 0) { netLeave(); return; }   // gone meanwhile (died, another game)
  if (res && res.role === 'full') { log('The Rift of ' + r.name + ' is full. Try again later, or set the dial for another realm.', '#e06a5a'); return; }
  const others = res && res.role === 'joiner' ? presenceList().filter(q => q.peer !== NET.me) : [];
  leaveLevel(); sfx('stairs');
  G.rift = { id: r.id, name: r.name, d, pvp: r.pvp };
  G.depth = d;
  if (res && res.role === 'joiner') { buildRiftFromSnap(res.snap); netMapId(res.snap.mid); riftJoinSpawn(d); } else { buildLevel(G.depth); riftAdd(riftRestock(d)); netOwnAll(); netMapId(); }
  RA.away = false;   // arrived standing near the portal's gate: no question until the hero has stepped off it
  log('You step through the portal into the Rift of ' + r.name + '.', '#b49ae6');
  if (!res) log('The Rift is silent: no one else can reach you here.', '#a99c86');
  else if (res.role === 'unreachable') log('You could not reach ' + (res.name || 'the others') + ' in this Rift: you are alone in it.', '#e06a5a');
  else if (res.role === 'joiner') log((others.length ? others.map(q => q.name + ' (level ' + q.lvl + ')').join(', ') + (others.length === 1 ? ' walks' : ' walk') + ' this Rift.' : 'Others walk this Rift.') + ' Your coming woke more of its monsters: in rooms no one had claimed, over the lake, in the great hall, and a new guardian in the boss chamber.', '#a99c86');
  if (r.pvp) log('Blades are drawn in this realm: other heroes can hurt you, and you them.', '#ff6a5a');
  log('Monsters here match the deepest depth you have reached (' + G.depth + '). Nothing is saved until you leave through the portal.', '#a99c86');
  refreshUI();
}
function leaveRift() {
  if (!G.rift) return;
  netLeave(); G.heroes = [G.hero];
  leaveLevel(); sfx('stairs');
  const name = G.rift.name; G.rift = null; G.depth = 0; buildSurface('portal');
  RA.away = false;
  log('You step out of the Rift of ' + name + ' onto the grass before the portal.', '#b49ae6');
  if (saveHero()) log('Progress saved.', '#a99c86');
  refreshUI();
}

// ---- Drawing: the platform and the dial lie on the ground (drawn first), the arch is depth-sorted on its base line
function drawPortal(o, part) {
  const P = META.portal, img = IMG.portal; if (!P || !img) return;
  const [x, y, w, hh, ox, oy, gw, gh] = P[part], [sx, sy] = iso(o.x, o.y);
  ctx.drawImage(img, x, y, w, hh, sx + ox, sy + oy, gw, gh);
  if (part !== 'arch') return;
  // the vortex comes alive: a slow pulse of light and faint arms turning in it
  const [gx, gy, rx, ry] = P.glow, cx = sx + gx, cy = sy + gy, t = G.time;
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.beginPath(); ctx.ellipse(cx, cy, rx * 0.92, ry * 0.95, 0, 0, 7); ctx.clip();
  const pulse = 0.5 + 0.5 * Math.sin(t * 1.7), gr = ctx.createRadialGradient(cx, cy, 0, cx, cy, rx * 1.1);
  gr.addColorStop(0, `rgba(190,150,255,${0.10 + 0.12 * pulse})`); gr.addColorStop(1, 'rgba(120,90,255,0)');
  ctx.fillStyle = gr; ctx.fillRect(cx - rx, cy - ry, rx * 2, ry * 2);
  ctx.lineWidth = 3; ctx.lineCap = 'round';
  for (let i = 0; i < 5; i++) { const a0 = t * 0.9 + i * 1.2566;
    ctx.strokeStyle = `rgba(200,180,255,${0.10 + 0.06 * Math.sin(t * 2.3 + i)})`; ctx.beginPath();
    for (let k = 0; k <= 24; k++) { const u = k / 24, a = a0 + u * 3.2, r = u * rx * 0.95; const px = cx + Math.cos(a) * r, py = cy + Math.sin(a) * r * ry / rx;
      if (k) ctx.lineTo(px, py); else ctx.moveTo(px, py); }
    ctx.stroke(); }
  ctx.restore();
}
function pickPortal(o) {   // the hover / click box: the arch's opening
  const P = META.portal; if (!P) return; const [sx, sy] = iso(o.x, o.y), [gx, gy, rx, ry] = P.glow;
  G.pick.push({ kind: 'obj', r: o, x: sx + gx - rx, y: sy + gy - ry, w: rx * 2, h: ry * 2 + 20 });
}

// "Entering the Rift…" while the realm is being joined
// While connecting to the realm (netJoin, a moment): the surface keeps being drawn and running, but the hero is not
// drawn (it has stepped into the portal), the HUD is hidden (body.portalWait) and all input is ignored (RA.busy:
// a blocker over the page takes the pointer, a key handler in the capture phase the keys).
function riftWait(on) {
  RA.busy = on; document.body.classList.toggle('portalWait', on);
  if (on) { const h = G.hero; h.path = []; h.intent = null; h.attackTarget = null; h.attackPending = false; h.pendingAt = null; h.queue = []; hideTip(); }
}
addEventListener('keydown', e => { if (RA.busy) { e.preventDefault(); e.stopImmediatePropagation(); } }, true);

// ---- The snapshot: what a player joining the realm gets from its elder (net.js): the map (tiles and blocked tiles,
// run-length encoded), its rooms and its lasting furnishings (doors, the portal, braziers, banners, pillars, …).
// Also every live monster, chest, urn, bones, gold and floor item, each with its owner (net.js; multiplayer.md §5).
const SNAP_SKIP = new Set(['stairs', 'keeper']);
function rle(a) { const o = []; for (let i = 0; i < a.length;) { let j = i; while (j < a.length && a[j] === a[i]) j++; o.push(a[i], j - i); i = j; } return o; }
function unrle(o, n) { const a = new Uint8Array(n); for (let i = 0, k = 0; i < o.length; i += 2) { a.fill(o[i], k, k + o[i + 1]); k += o[i + 1]; } return a; }
function riftSnapshot() {
  const m = G.map, b = m.block.slice(), objects = [];
  for (const o of G.objects) {
    if (SNAP_SKIP.has(o.type)) { if (o.block && o.type !== 'door') b[o.y * m.w + o.x] = 0; continue; }   // its tile is free for the joiner
    const c = {}; for (const k in o) if (k !== 'room' && k !== 'asked' && typeof o[k] !== 'function') c[k] = o[k];
    if (LOOT_OBJ.has(o.type) || o.type === 'door') c.owner = o.owner || NET.me;   // whose it is, seen from the joiner
    objects.push(c);
  }
  return { v: VERSION, mid: NET.mid, w: m.w, h: m.h, t: rle(m.t), b: rle(b), rooms: m.rooms.map(r => ({ x: r.x, y: r.y, w: r.w, h: r.h, cx: r.cx, cy: r.cy, big: r.big || false })), objects,
    claims: [...(m.claims || [])], mons: G.monsters.filter(q => !q.dead && q.nid && !q.parts).map(monDesc),
    items: G.items.filter(fi => fi.nid).map(fi => ({ i: fi.nid, o: fi.owner || NET.me, it: itemOut(fi.item), x: fi.x, y: fi.y })) };   // every live monster, with its owner (net.js)
}
function buildRiftFromSnap(s) {
  const w = s.w, h = s.h, t = unrle(s.t, w * h);
  const at = (x, y) => (x < 0 || y < 0 || x >= w || y >= h) ? T_VOID : t[y * w + x];
  const map = { w, h, t, at, seen: new Uint8Array(w * h), block: unrle(s.b, w * h), rooms: s.rooms, lake: null, lakeRoom: null, claims: new Set(s.claims || [0]) };
  G.lakeFx = null; G.map = map;
  map.lakeRoom = s.rooms.find(r => r.big === 'lake') || null; map.bossRoom = s.rooms.find(r => r.big === 'boss') || null;
  if (map.lakeRoom) map.lake = lakeGeom(map);   // the lake: its outline from the water tiles
  G.objects = s.objects; G.monsters = []; G.items = []; G.proj = []; G.fx = []; G.texts = [];
  stopFireSounds(); G.fires = [];
  const o = G.objects.find(q => q.type === 'portal'), hero = G.hero;
  hero.x = o.x + 1.6 + (rnd() - 0.5) * 1.2; hero.y = o.y + 1.6 + (rnd() - 0.5) * 1.2; hero.dir = 0;   // just come through, beside whoever else did
  if (!canStand(hero.x, hero.y, hero.r)) { hero.x = o.x + 1.6; hero.y = o.y + 1.6; }
  hero.path = []; hero.intent = null; hero.attackTarget = null; hero.swing = null;
  hero.queue = []; hero.pendingAt = null; hero.using = null; hero.burnLeft = 0; hero.burning = hero.inFire = false;
  G.fade = 1; updateMinimap(true);
  for (const d of s.mons || []) netAddMonster(d, d.o);   // the monsters already here, each predicted from its owner's states
  for (const o of G.objects) if (o.nid) NET.loot.set(o.nid, o);   // chests, urns, bones, gold: their owners grant them
  for (const d of s.items || []) { const fi = { item: d.it, x: d.x, y: d.y, t: rnd() * 6, nid: d.i, owner: d.o }; G.items.push(fi); NET.loot.set(d.i, fi); }
}
// A player joining a Rift brings its share of monsters (multiplayer.md §3): RIFT.share of the ordinary rooms no one
// has claimed (at least one while any is free), spread evenly over them from near the portal to far; and it restocks
// the lake, the big room and the boss room (riftRestock). Tells the others.
function riftJoinSpawn(d) {
  const m = G.map, o = G.objects.find(q => q.type === 'portal'), dist = bfs(Math.floor(o.fx), Math.floor(o.fy));
  const free = m.rooms.map((r, i) => i).filter(i => !m.claims.has(i) && !m.rooms[i].big);
  const n = free.length ? Math.max(1, Math.round(free.length * RIFT.share)) : 0;
  const D = i => dist[m.rooms[i].cy * m.w + m.rooms[i].cx] || 0;
  const mine = riftSpread(free.sort((a, b) => D(a) - D(b)), n);   // spread evenly over the free rooms, near to far
  const more = riftRestock(d);
  const mons = riftPopulate(mine.map(i => m.rooms[i]), d).concat(more.mons), objs = riftFurnish(mine.map(i => m.rooms[i]), d).concat(more.objs);
  riftAdd({ mons, objs });
  netOwnAll(); for (const i of mine) m.claims.add(i);
  netEach({ t: 'spawn', a: mons.map(monDesc), rooms: mine, objs: objs.map(o => Object.assign({}, o)) });
}
// A joiner's rooms get treasure as a crypt level's rooms do: a chest 38 % of the time, gold 20 % (of its depth)
function riftFurnish(rooms, d) {
  const out = [], map = G.map, used = new Set(G.objects.map(o => o.x + ',' + o.y));
  const spot = r => { for (let k = 0; k < 40; k++) { const x = ri(r.x + 1, r.x + r.w - 2), y = ri(r.y + 1, r.y + r.h - 2);
    if (map.at(x, y) !== T_FLOOR || map.block[y * map.w + x] || used.has(x + ',' + y)) continue; used.add(x + ',' + y); return [x, y]; } return null; };
  for (const r of rooms) {
    if (rnd() < 0.38) { const p = spot(r); if (p) out.push({ type: 'chest', x: p[0], y: p[1], used: false, block: true }); }
    if (rnd() < 0.2) { const p = spot(r); if (p) out.push({ type: 'gold', x: p[0], y: p[1], used: false, block: false, amount: Math.max(1, Math.round(ri(3, 12) * d * LOOT)) }); }
  }
  return out;
}
// Monsters for rooms, as on a crypt level of depth d: 1 to cap each (cap 3 at depths 1-2, +1 every 2 depths, at most
// 7), +1 half the time in a large room, each type within its room limit, champions with 2-3 escorts
function riftPopulate(rooms, d) {
  const weighted = []; for (const k in MON) if (MON[k].minD <= d) for (let i = 0; i < MON[k].w; i++) weighted.push(k);
  const out = [], taken = new Set(), map = G.map;
  const spot = (r) => { for (let k = 0; k < 40; k++) { const x = ri(r.x + 1, r.x + r.w - 2), y = ri(r.y + 1, r.y + r.h - 2);
    if (map.at(x, y) !== T_FLOOR || map.block[y * map.w + x] || taken.has(x + ',' + y)) continue; taken.add(x + ',' + y);
    return [x + 0.5 + (rnd() - 0.5) * 0.4, y + 0.5 + (rnd() - 0.5) * 0.4]; } return null; };
  for (const r of rooms) {
    const cap = Math.min(7, 3 + Math.floor((d - 1) / 2)), n = ri(1, cap) + (r.w * r.h >= 64 && rnd() < 0.5 ? 1 : 0), cnt = {};
    for (let i = 0; i < n; i++) {
      const p = spot(r); if (!p) break;
      let t = 'skeleton'; for (let k = 0; k < 30; k++) { const c = pick(weighted); if ((cnt[c] || 0) < roomLimit(c, d)) { t = c; break; } }
      cnt[t] = (cnt[t] || 0) + 1; const mo = makeMonster(t, p[0], p[1], d); out.push(mo);
      if (mo.champ) for (let e = Math.min(ri(2, 3), roomLimit(t, d) - cnt[t]); e > 0; e--) {
        const q = spot(r); if (!q) break; out.push(makeMonster(t, q[0], q[1], d, false, false, true)); cnt[t]++; }
    }
  }
  return out;
}

// ---- The three great rooms, restocked by each player who comes in (the founder too), at that player's depth d. The
// lake and the big room are topped up to RIFT.great players' worth (counting what still lives there): wraiths over
// the lake (one player's worth: LAKE_WRAITHS, as on a crypt lake) and a horde in the big room (one player's worth:
// twice a crypt big room's pack, as the room is twice the size); so they always feel full, but never grow past that
// however many come. In the boss room, every player adds a boss of depth d + 1 with a
// guardian's chest of its own, sealed while that boss lives (gm: the boss; its id, guard, once it has one: netOwnAll).
// Returns { mons, objs }, not yet in the level (riftAdd).
const inRoom = (r, q) => q.x >= r.x && q.x < r.x + r.w && q.y >= r.y && q.y < r.y + r.h;
function riftRestock(d) {
  const m = G.map, mons = [], objs = [], room = k => m.rooms.find(r => r.big === k);
  const used = new Set(G.objects.map(o => o.x + ',' + o.y));
  const near = (x, y, r) => G.monsters.concat(mons).some(q => !q.dead && Math.hypot(q.x - x, q.y - y) < r);
  const free = (x, y) => m.at(x, y) === T_FLOOR && !m.block[y * m.w + x] && !used.has(x + ',' + y) && !near(x + 0.5, y + 0.5, 0.9);
  const inner = r => { for (let k = 0; k < 60; k++) { const x = ri(r.x + 1, r.x + r.w - 2), y = ri(r.y + 1, r.y + r.h - 2);
    if (free(x, y)) return [x + 0.5 + (rnd() - 0.5) * 0.4, y + 0.5 + (rnd() - 0.5) * 0.4]; } return null; };
  const typeFor = (pool, cnt, dd) => { for (let k = 0; k < 30; k++) { const t = pick(pool); if ((cnt[t] || 0) < roomLimit(t, dd)) return t; } return 'skeleton'; };
  const lake = room('lake');
  if (lake) {   // around a point 45 % of the way from the lake's north corner to its shore, on tiles with water all around
    const gx = lake.x + (lake.w - LAKE_SHORE) * 0.45, gy = lake.y + (lake.h - LAKE_SHORE) * 0.45, spots = [];
    for (let y = Math.floor(gy - 7); y <= gy + 7; y++) for (let x = Math.floor(gx - 7); x <= gx + 7; x++) {
      if (Math.hypot(x + 0.5 - gx, y + 0.5 - gy) > 6.5) continue;
      let wet = true; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) if (m.at(x + dx, y + dy) !== T_WATER) wet = false;
      if (wet) spots.push([x, y]);
    }
    const have = G.monsters.filter(q => !q.dead && q.type === 'wraith' && inRoom(lake, q)).length;
    for (let n = Math.max(0, RIFT.great * ri(...LAKE_WRAITHS) - have), k = 0; n > 0 && k < 300 + 20 * n && spots.length; k++) {
      const [x, y] = pick(spots), px = x + 0.3 + rnd() * 0.4, py = y + 0.3 + rnd() * 0.4;
      if (near(px, py, k < 150 ? 1.6 : 0.9)) continue;   // (a crowded lake: closer together)
      const q = makeMonster('wraith', px, py, d, false, false, true); q.lake = true; mons.push(q); n--;
    }
  }
  const hall = room('horde');
  if (hall) {   // the crypt big room's pack (skeletons x3 and the types of depth d - 4 or earlier, no champions), twice over
    const pool = []; for (const k in MON) if (k === 'skeleton' || MON[k].minD <= d - 4) for (let i = 0; i < MON[k].w * (k === 'skeleton' ? 3 : 1); i++) pool.push(k);
    const cnt = {}, have = G.monsters.filter(q => !q.dead && inRoom(hall, q)).length;
    for (const q of G.monsters) if (!q.dead && inRoom(hall, q)) cnt[q.type] = (cnt[q.type] || 0) + 1;
    for (let i = Math.max(0, RIFT.great * 2 * Math.round((ri(5, 7) + Math.floor((d - 3) / 2)) * 1.5) - have); i > 0; i--) { const p = inner(hall); if (!p) break;
      const t = typeFor(pool, cnt, d); cnt[t] = (cnt[t] || 0) + 1; mons.push(makeMonster(t, p[0], p[1], d, false, false, true)); }
  }
  const br = room('boss');
  if (br) {
    // the boss: on the free tile nearest the room's middle at least 3 tiles from every other boss there; its type
    // drawn by weight from those unlocked at its depth + 1, as a crypt boss's
    const bd = d + 1, bosses = G.monsters.filter(q => q.boss && !q.dead), mx = br.x + br.w / 2, my = br.y + br.h / 2;
    let best = null;
    for (let y = br.y + 1; y < br.y + br.h - 1; y++) for (let x = br.x + 1; x < br.x + br.w - 1; x++) {
      if (!free(x, y) || bosses.some(q => Math.hypot(q.x - x - 0.5, q.y - y - 0.5) < 3)) continue;
      const dd = Math.hypot(x + 0.5 - mx, y + 0.5 - my); if (!best || dd < best[2]) best = [x, y, dd];
    }
    if (best) {
      const pool = []; for (const k in MON) if (MON[k].minD <= bd + 1) for (let i = 0; i < MON[k].w; i++) pool.push(k);
      const boss = makeMonster(pick(pool), best[0] + 0.5, best[1] + 0.5, bd, true); mons.push(boss);
      // its chest: against the north-east or north-west wall (in view), clear of doorways, a solid wall behind it
      const spots = [];
      for (let y = br.y; y <= br.y + br.h - 3; y++) for (let x = br.x; x <= br.x + br.w - 3; x++) {
        if (x !== br.x && y !== br.y || !free(x, y)) continue;
        let ok = true;
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const v = m.at(x + dx, y + dy); if (v === T_DOOR || v === T_OPEN) ok = false; }
        for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const nx = x + dx, ny = y + dy;
          if (!(nx >= br.x && nx < br.x + br.w && ny >= br.y && ny < br.y + br.h) && m.at(nx, ny) !== T_WALL) ok = false; }
        if (ok) spots.push([x, y]);
      }
      if (spots.length) { const [x, y] = pick(spots); used.add(x + ',' + y);
        const c = { type: 'chest', x, y, used: false, block: true, boss: true }; Object.defineProperty(c, 'gm', { value: boss, enumerable: false }); objs.push(c); }
    }
  }
  return { mons, objs };
}
function riftAdd({ mons, objs }) {
  for (const q of mons) G.monsters.push(q);
  for (const o of objs) { G.objects.push(o); if (o.block) G.map.block[o.y * G.map.w + o.x] = 1; }
}

// n of a list (sorted near to far) spread evenly over it: the middles of n equal stretches (all of it if n ≥ its length)
function riftSpread(list, n) { if (n >= list.length) return list.slice(); return Array.from({ length: n }, (_, i) => list[Math.floor((i + 0.5) * list.length / n)]); }
