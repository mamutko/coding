// =====================================================================================
//  The Rift (multiplayer.md; README, The Rift): the portal and its dial on the surface, realm ids and names, and the
//  Rift itself, a large one-level dungeon beyond the portal. Phase 2: played alone (no networking yet).
//  Loaded before the game's main script; everything here runs only once the game is up.
// =====================================================================================
// The portal on the surface: its arch stands on the line of tiles x + y = const, west to east, facing south (toward
// the crypt); `at` is the ground point in the middle of the arch's base line (world tiles), about 50 tiles north of
// the crypt. The dial lies in front of it (`dial`, its centre), META.portal.dialR tiles in radius. `clear`: no trees
// grow within this many tiles of the arch. The Rift: `size` tiles a side, `rooms` rooms.
const RIFT = { at: [-22, -22], dial: [-17.4, -17.4], clear: 9, size: 110, rooms: 34 };

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
function realmOf(items) {   // the realm a set of dial items opens
  const key = realmKey(items), hash = realmHash(key);
  return { id: 'v' + VERSION + '-' + hash, hash, name: realmName(hash), key, open: !items.length };
}
const currentRealm = () => realmOf(dialItems().map(d => d.fi.item));
// the dial's items go into the save (hero.dial) and lie on the dial again when the surface is built
function syncDial() { if (G && G.depth === 0 && !G.rift && G.surf) G.hero.dial = dialItems().map(d => d.fi.item); }
function restoreDial(sv) {
  const its = G.hero.dial || [], n = its.length;
  its.forEach((item, i) => { const a = i / Math.max(1, n) * Math.PI * 2 + 0.4, r = n > 1 ? 0.95 : 0;
    sv.items.push({ item, wx: RIFT.dial[0] + Math.cos(a) * r, wy: RIFT.dial[1] + Math.sin(a) * r, t: rnd() * 6 }); });
}

// ---- Going through: a question first
const RA = { o: null, away: true };   // the portal asked about; away: the hero has stepped off its gate since
function riftCheck() {   // every frame: the hero on a gate tile of a portal asks once, until it steps off again
  const h = G.hero; if (G.dead || !G.running) return;
  const o = G.objects.find(p => p.type === 'portal' && Math.abs(p.x - h.x) < 4 && Math.abs(p.y - h.y) < 4);
  const on = o && onGate(o, h);
  if (!on) { RA.away = true; return; }
  if (!RA.away || RA.o) return;
  RA.away = false; riftAsk(o);
}
function riftAsk(o) {
  RA.o = o; const el = $('riftAsk'), inside = !!G.rift;
  let html;
  if (inside) html = `<h2>The Rift of ${G.rift.name}</h2><div>Step back through the portal to the surface?</div><div class="ty">You will be saved there.</div>`;
  else { const r = currentRealm();
    html = `<h2>The Rift of ${r.name}</h2><div>${r.open ? 'The dial is empty: this is the open Rift, where strangers meet.' : 'The items on the dial have chosen this realm.'}</div>` +
      `<div>The Rift lies empty. You will be the first.</div><div class="ty">Realm ${r.id}. You are saved before you go. Nothing is saved inside: leave through this portal to keep what you win; die in there and you lose it.</div>`; }
  el.innerHTML = html + `<div class="btns"><button id="raGo">${inside ? 'Leave' : 'Enter'}</button><button id="raStay">Stay</button></div>`;
  el.classList.remove('hidden');
  $('raGo').onclick = () => { riftClose(); inside ? leaveRift() : enterRift(); };
  $('raStay').onclick = riftClose;
}
function riftClose() { RA.o = null; const el = $('riftAsk'); el.classList.add('hidden'); el.innerHTML = ''; }
const riftAskOpen = () => !!RA.o;

// ---- Entering and leaving
function enterRift() {
  if (G.rift || G.depth !== 0) return;
  const h = G.hero; syncDial();
  h.surfAt = 'portal';   // saved: resumed from this save, the hero stands before the portal
  if (saveHero()) log('Progress saved.', '#a99c86');
  h.surfAt = null;
  const r = currentRealm(); leaveLevel(); sfx('stairs');
  G.rift = { id: r.id, name: r.name, d: Math.max(1, h.maxDepth || 1) };
  G.depth = G.rift.d; buildLevel(G.depth);
  RA.away = false;   // arrived standing near the portal's gate: no question until the hero has stepped off it
  log('You step through the portal into the Rift of ' + r.name + '.', '#b49ae6');
  log('Monsters here match the deepest depth you have reached (' + G.depth + '). Nothing is saved until you leave through the portal.', '#a99c86');
  refreshUI();
}
function leaveRift() {
  if (!G.rift) return;
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
