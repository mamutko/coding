// =====================================================================================
//  The Rift's network (multiplayer.md §4; README, The Rift: Playing together). Browsers in the same realm find each
//  other through Supabase Realtime (presence: who is in the realm; broadcast: the WebRTC handshake) and then talk
//  directly over WebRTC data channels: "ev" (reliable, ordered: hello, snapshot, bye) and "st" (unreliable,
//  unordered: each hero's state 15 times a second, pings). Phase 3: players see each other; no combat yet.
//  Loaded before the game's main script; nothing here runs until a hero comes to the portal.
// =====================================================================================
const NET_CFG = {
  url: 'https://qifgxysuhskscrjjwzfm.supabase.co', key: 'sb_publishable_dJ7DGbkXPYOiD4YipTXEog_vx_FhOot',   // the repo's shared project (public key)
  lib: 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.119.0/dist/umd/supabase.min.js',
  ice: [{ urls: 'stun:stun.l.google.com:19302' }],
  max: 6,            // players in one realm
  syncWait: 1500,    // ms to wait for the presence list after subscribing
  raceWait: 700,     // ms after showing ourselves, to spot someone who founded the same realm at the same moment
  connectWait: 10000,// ms to reach the realm's elder and get its snapshot
  rate: 66,          // ms between state messages (about 15 a second; also the heartbeat)
  drop: 3000,        // ms of silence after which a peer counts as gone
  ping: 2000,        // ms between clock pings
  delay: 100,
  away: 60000,       // ms a hidden tab stays in the Rift (its hero away) before it leaves        // ms other heroes are drawn in the past (interpolated between their states)
  chunk: 16000,      // characters per snapshot piece
};
const NET = { loot: new Map(), mons: new Map(), monN: 0, sb: null, libP: null, ch: null, topic: null, me: null, since: 0, peers: new Map(), on: false, timer: null, snapIn: null };
const netNow = () => performance.now();

function netLib() {   // load supabase-js once; resolves to the client, or null if it cannot be loaded
  if (NET.libP) return NET.libP;
  NET.libP = new Promise(res => {
    if (window.supabase) return res(window.supabase);
    const s = document.createElement('script'); s.src = NET_CFG.lib; s.onload = () => res(window.supabase || null); s.onerror = () => res(null);
    document.head.appendChild(s); setTimeout(() => res(window.supabase || null), 8000);
  }).then(lib => { if (lib && !NET.sb) try { NET.sb = lib.createClient(NET_CFG.url, NET_CFG.key); } catch (e) { NET.sb = null; } return NET.sb; });
  return NET.libP;
}
const presenceList = () => NET.ch ? Object.values(NET.ch.presenceState()).map(a => a[0]).filter(Boolean) : [];

// Open the realm's channel (without showing ourselves) and read who is there: resolves to the list of players
// ({ peer, name, lvl, look, depth, since }) or null when there is no connection. The channel stays open for netJoin.
async function netPeek(realmId) {
  const sb = await netLib(); if (!sb) return null;
  const topic = 'rift:' + realmId;
  if (NET.ch && NET.topic === topic) return presenceList();
  await netClose();
  if (!NET.me) NET.me = Math.random().toString(36).slice(2, 10);
  NET.topic = topic;
  const ch = NET.ch = sb.channel(topic, { config: { presence: { key: NET.me }, broadcast: { self: false } } });
  ch.on('broadcast', { event: 'sig' }, ({ payload: p }) => { if (p && p.to === NET.me) netSignal(p); });
  ch.on('presence', { event: 'sync' }, () => { NET.synced = true; });
  NET.synced = false;
  const ok = await new Promise(res => { ch.subscribe(st => { if (st === 'SUBSCRIBED') res(true); else if (st === 'CHANNEL_ERROR' || st === 'TIMED_OUT' || st === 'CLOSED') res(false); }); setTimeout(() => res(false), 6000); });
  if (!ok) { await netClose(); return null; }
  // the first sync can come before the list has arrived: wait the whole time, or until someone shows up
  const t0 = netNow(); while (netNow() - t0 < NET_CFG.syncWait && !presenceList().some(p => p.peer !== NET.me)) await new Promise(r => setTimeout(r, 50));
  return presenceList().filter(p => p.peer !== NET.me);
}
async function netClose() {   // leave the channel and every connection
  for (const p of NET.peers.values()) netDropPeer(p, true);
  NET.peers.clear(); NET.mons.clear(); NET.loot.clear(); NET.on = false; clearInterval(NET.timer); NET.timer = null;
  if (NET.ch) { const ch = NET.ch; NET.ch = null; NET.topic = null; try { await ch.untrack(); } catch (e) {} try { await NET.sb.removeChannel(ch); } catch (e) {} }
}

// Join the realm: show ourselves in its presence; with nobody older there we found it (resolves { role: 'founder' }),
// else connect to everyone older than us and get the snapshot from the elder ({ role: 'joiner', snap }). Null: no
// connection (play alone).
async function netJoin(realmId, me) {
  const others0 = await netPeek(realmId); if (others0 == null) return null;
  NET.since = Date.now();
  try { await NET.ch.track(Object.assign({ peer: NET.me, since: NET.since }, me)); } catch (e) { await netClose(); return null; }
  await new Promise(r => setTimeout(r, NET_CFG.raceWait));
  const older = presenceList().filter(p => p.peer !== NET.me && (p.since < NET.since || p.since === NET.since && p.peer < NET.me));
  netStart();
  if (!older.length) return { role: 'founder' };
  if (older.length >= NET_CFG.max) { await netClose(); return { role: 'full' }; }
  // connect to every older player (younger ones connect to us), then ask the eldest for the snapshot
  for (const p of older) netConnect(p, true);
  const elder = older.slice().sort((a, b) => a.since - b.since || (a.peer < b.peer ? -1 : 1))[0];
  const snap = await new Promise(res => {
    NET.snapIn = { from: elder.peer, parts: [], res };
    const ask = setInterval(() => { const ep = NET.peers.get(elder.peer); if (ep && ep.ev && ep.ev.readyState === 'open') { clearInterval(ask); netSend(ep, { t: 'snapReq' }); } }, 100);
    setTimeout(() => { clearInterval(ask); res(null); }, NET_CFG.connectWait);
  });
  NET.snapIn = null;
  if (!snap) { await netClose(); return { role: 'unreachable', name: elder.name }; }
  return { role: 'joiner', snap };
}
const netLeave = () => { for (const p of NET.peers.values()) netSend(p, { t: 'bye' }); return netClose(); };

// ---- WebRTC: one connection per pair. The younger player makes the offer; the handshake goes over the channel.
function netPeer(info) {
  let p = NET.peers.get(info.peer);
  if (!p) { p = { id: info.peer, info, pc: null, ev: null, st: null, last: netNow(), off: 0, rtt: 0, hero: null, pend: [] }; NET.peers.set(info.peer, p); }
  return p;
}
function netConnect(info, offer) {
  const p = netPeer(info), pc = p.pc = new RTCPeerConnection({ iceServers: NET_CFG.ice });
  pc.onicecandidate = e => { if (e.candidate) netSig(p.id, 'ice', e.candidate.toJSON()); };
  pc.onconnectionstatechange = () => { if (pc.connectionState === 'failed') netDropPeer(p); };
  const wire = (dc) => { dc.onmessage = e => netMsg(p, e.data); if (dc.label === 'ev') { p.ev = dc; dc.onopen = () => netHello(p); if (dc.readyState === 'open') netHello(p); } else p.st = dc; };
  if (offer) {
    wire(pc.createDataChannel('ev')); wire(pc.createDataChannel('st', { ordered: false, maxRetransmits: 0 }));
    pc.createOffer().then(o => pc.setLocalDescription(o)).then(() => netSig(p.id, 'offer', pc.localDescription.toJSON())).catch(() => netDropPeer(p));
  } else pc.ondatachannel = e => wire(e.channel);
  return p;
}
const netSig = (to, k, d) => { if (NET.ch) NET.ch.send({ type: 'broadcast', event: 'sig', payload: { to, from: NET.me, k, d } }); };
async function netSignal(m) {   // a handshake message for us
  if (!NET.on) return;
  let p = NET.peers.get(m.from);
  try {
    if (m.k === 'offer') {
      if (NET.peers.size >= NET_CFG.max - 1 && !p) return;
      const info = presenceList().find(q => q.peer === m.from) || { peer: m.from, name: 'Someone' };
      p = netConnect(info, false);
      await p.pc.setRemoteDescription(m.d); const a = await p.pc.createAnswer(); await p.pc.setLocalDescription(a);
      netSig(m.from, 'answer', p.pc.localDescription.toJSON());
      for (const c of p.pend.splice(0)) await p.pc.addIceCandidate(c);
    } else if (m.k === 'answer' && p && p.pc) { await p.pc.setRemoteDescription(m.d); for (const c of p.pend.splice(0)) await p.pc.addIceCandidate(c); }
    else if (m.k === 'ice' && p && p.pc) { if (p.pc.remoteDescription) await p.pc.addIceCandidate(m.d); else p.pend.push(m.d); }
    else if (m.k === 'ice') netPeer({ peer: m.from }).pend.push(m.d);
  } catch (e) { console.warn('[net] signal', m.k, e); }
}
function netSend(p, m) { const dc = m.t === 'st' || m.t === 'ms' || m.t === 'ping' || m.t === 'pong' ? p.st : p.ev; if (dc && dc.readyState === 'open') try { dc.send(JSON.stringify(m)); } catch (e) {} }
function netDropPeer(p, quiet) {
  if (NET.peers.get(p.id) === p) NET.peers.delete(p.id);
  try { p.pc && p.pc.close(); } catch (e) {}
  if (p.hero && G && G.heroes) { const i = G.heroes.indexOf(p.hero); if (i >= 0) G.heroes.splice(i, 1);
    if (!quiet && G.rift) log(p.hero.name + ' has left the Rift.', '#b49ae6'); }
  p.hero = null;
  // its loot passes to the eldest player left (everyone works out the same one)
  if (G && G.rift) { const el = netElder(); for (const x of NET.loot.values()) if (x.owner === p.id) x.owner = el === NET.me ? undefined : el; }
  // its monsters: the eldest player left decides for everyone (handover): one fighting a hero still here passes to
  // that hero's player, the rest fade away. Until the decision comes they stand still (orphans).
  if (!quiet && G && G.rift && G.monsters) {
    const mine = G.monsters.filter(m => m.owner === p.id && !m.dead); for (const m of mine) m.orphan = netNow();
    if (mine.length && netElder() === NET.me) netHandover(mine.map(m => [m.nid, m.state === 'chase' && m.tg && (m.tg === NET.me || NET.peers.has(m.tg)) ? m.tg : null]));
  }
}
// Handing monsters over (multiplayer.md §7): [[id, new owner or null (fades away)], …], applied here and sent to all
function netHandover(a) { netEach({ t: 'handover', a }); netApplyHandover(a); }
function netApplyHandover(a) {
  let faded = 0, ours = 0;
  for (const [i, o] of a) {
    const m = NET.mons.get(i); if (!m || m.dead) continue; m.orphan = null;
    if (o === null) { m.dead = true; m.deathT = 0; m.faded = true; NET.mons.delete(i); faded++; }
    else if (o === NET.me) {   // ours now: its AI runs here, from where it stands, after whoever it was after
      delete m.owner; m.path = []; m.repath = 0; m.cd = Math.max(m.cd, 0.6); m.windup = 0; if (m.state !== 'chase') chase(m); ours++;
      if (m.tg) m.tgt = heroById(m.tg); }
    else { if (!m.owner) { m.ax = m.x; m.ay = m.y; m.at = netNow(); m.tx = m.ty = m.tg = null; m.sp = 0; } m.owner = o; }   // (one of ours handed away: a copy now)
  }
  if (faded && G.rift) log('The Rift reclaims its own: ' + (faded === 1 ? 'a monster fades' : faded + ' monsters fade') + ' away.', '#a99c86');
  if (ours && G.rift) log((ours === 1 ? 'A monster that was after you is' : ours + ' monsters that were after you are') + ' yours to fight now.', '#a99c86');
}
// Our tab hidden: a hidden tab cannot run its monsters, so it hands them all over at once (those fighting another
// hero to that hero's player, the rest to the eldest of the others); our hero is "away" (faded, left alone) until
// we come back; after NET_CFG.away ms it leaves the Rift (netTick).
function netHide(hidden) {
  if (!NET.on || !G || !G.rift) return;
  if (hidden) {
    if (NET.awaySince) return; NET.awaySince = netNow();
    const others = [...NET.peers.values()]; if (!others.length) return;
    let el = null, es = Infinity; for (const q of others) { const sn = q.info && q.info.since; if (sn != null && sn < es) { es = sn; el = q.id; } }
    if (!el) el = others[0].id;
    const a = G.monsters.filter(m => !m.owner && m.nid && !m.dead).map(m => { const t = tgtId(m.tgt); return [m.nid, m.state === 'chase' && t && t !== NET.me && NET.peers.has(t) ? t : el]; });
    if (a.length) netHandover(a);
  } else NET.awaySince = 0;
}
document.addEventListener('visibilitychange', () => netHide(document.hidden));

// ---- Messages
function netHello(p) {
  if (p.helloSent) return; p.helloSent = true;
  const h = G.hero; netSend(p, { t: 'hello', name: h.name, lvl: h.lvl, look: h.look || 'hero', since: NET.since });
}
function netMsg(p, data) {
  let m; try { m = JSON.parse(data); } catch (e) { return; }
  p.last = netNow();
  switch (m.t) {
    case 'hello': {
      p.info = Object.assign(p.info || {}, { name: m.name, lvl: m.lvl, look: m.look, since: m.since }); p.hello = m;   // (its hero appears in netFrame, once we are in the Rift)
      break; }
    case 'st': if (p.hero) remoteState(p, m); break;
    case 'ping': netSend(p, { t: 'pong', a: m.a, b: netNow() }); break;
    case 'pong': { const now = netNow(), rtt = now - m.a, off = m.b + rtt / 2 - now;   // their clock = ours + off
      p.rtt = p.rtt ? p.rtt * 0.8 + rtt * 0.2 : rtt; p.off = p.offN ? p.off * 0.8 + off * 0.2 : off; p.offN = (p.offN || 0) + 1; break; }
    case 'snapReq': { const s = JSON.stringify(riftSnapshot()), n = Math.ceil(s.length / NET_CFG.chunk);
      for (let i = 0; i < n; i++) netSend(p, { t: 'snap', i, n, d: s.slice(i * NET_CFG.chunk, (i + 1) * NET_CFG.chunk) }); break; }
    case 'snap': { const S = NET.snapIn; if (!S || S.from !== p.id) break; S.parts[m.i] = m.d;
      if (S.parts.filter(x => x != null).length === m.n) { try { S.res(JSON.parse(S.parts.join(''))); } catch (e) { S.res(null); } } break; }
    case 'bye': netDropPeer(p); break;
    case 'spawn': for (const d of m.a) netAddMonster(d, p.id); if (G.map && m.rooms) for (const r of m.rooms) G.map.claims.add(r);
      if (G.map) for (const o of m.objs || []) if (!NET.loot.has(o.nid)) { o.owner = p.id; G.objects.push(o); NET.loot.set(o.nid, o); if (o.block) G.map.block[o.y * G.map.w + o.x] = 1; }
      break;
    case 'ms': netMonStates(p, m); break;
    case 'hit': { const mo = NET.mons.get(m.i); if (mo && !mo.owner) netTakeHit(mo, m.v, m.c, m.f, p.id); break; }
    case 'died': { const mo = NET.mons.get(m.i); if (mo) netRemoteDied(mo, m.xp && m.xp[NET.me] || 0); break; }
    case 'frz': { const mo = NET.mons.get(m.i); if (!mo || mo.dead) break; freezeMonster(mo, m.dl, m.du);
      if (!mo.owner) for (const q of NET.peers.values()) if (q !== p) netSend(q, m);   // ours: tell the others too
      break; }
    case 'hh': if (G.rift && !G.dead && !NET.awaySince) damageHero(m.v, { lvl: m.lvl }); break;   // one of their monsters struck our hero
    case 'handover': netApplyHandover(m.a); break;
    case 'ice': if (G.map) { frostPatch(m.x, m.y, m.s); sfx('frostcast', { x: m.x, y: m.y }); } break;   // another player's scroll of frost: the same ice here
    case 'bomb': G.proj.push({ type: 'bomb', x: m.x0, y: m.y0, x0: m.x0, y0: m.y0, tx: m.tx, ty: m.ty, z: 44, t: 0, dur: m.dur, peak: m.pk, life: 1, rot: rnd() * 6, spin: 8, ghost: true }); break;   // seen only
    case 'fire': if (G.map) { const f = newFire(m.x, m.y); f.owner = p.id; G.fires.push(f); } break;   // its thrower decides what it burns
    case 'drop': netGotDrop(m, p.id); break;
    case 'take': netTakeReq(m, p); break;
    case 'took': netTook(m); break;
    case 'use': netUseReq(m, p); break;
    case 'used': netUsed(m); break;
    case 'door': { const o = G.objects.find(q => q.type === 'door' && q.x === m.x && q.y === m.y); if (o && !o.open) { o.open = true; G.map.t[o.y * G.map.w + o.x] = T_OPEN; sfx('door', { x: o.x, y: o.y }); } break; }
    case 'bolt': G.proj.push({ type: 'bolt', x: m.x, y: m.y, vx: m.vx, vy: m.vy, life: m.l, dmg: 0, friendly: false, ghost: true }); break;   // seen only: its owner decides what it hits
  }
}
// every NET_CFG.rate ms (a timer, so it goes on at least once a second in a background tab): our hero's state to
// everyone, clock pings, and dropping peers gone silent
function netStart() { NET.on = true; clearInterval(NET.timer); NET.timer = setInterval(netTick, NET_CFG.rate); }
function netTick() {
  if (!NET.on || RA.busy) return;
  if (!G || !G.rift || G.dead) { netLeave(); return; }   // died, or left for another game: out of the realm
  const h = G.hero, now = netNow();
  const st = { t: 'st', c: now, x: +h.x.toFixed(3), y: +h.y.toFixed(3), d: h.dir, m: h.moving ? 1 : 0, hp: Math.round(h.hp), mh: Math.round(h.st.maxHp),
    dy: h.dyingT != null ? 1 : 0, l: h.look || 'hero', lv: h.lvl, aw: NET.awaySince ? 1 : 0 };
  if (NET.awaySince && now - NET.awaySince > NET_CFG.away) {   // away too long: out of the Rift (saved on the surface)
    NET.awaySince = 0; log('The Rift let you go.', '#b49ae6'); leaveRift(); return; }
  for (const m of G.monsters) if (m.orphan && now - m.orphan > 4000) { m.orphan = null; m.dead = true; m.deathT = 0; m.faded = true; NET.mons.delete(m.nid); }   // no decision came: it fades
  for (const p of [...NET.peers.values()]) {
    if (now - p.last > NET_CFG.drop && (p.hero || now - p.last > NET_CFG.connectWait)) { netDropPeer(p); continue; }
    netSend(p, st);
    if (!p.pinged || now - p.pinged > NET_CFG.ping) { p.pinged = now; netSend(p, { t: 'ping', a: now }); }
    netSendMons(p, now);
  }
}
addEventListener('pagehide', () => { if (NET.on) { for (const p of NET.peers.values()) netSend(p, { t: 'bye' }); } });

// ---- Other heroes: drawn like the hero, interpolated NET_CFG.delay ms in the past between their last states
function remoteHero(p, m) {
  const o = G.objects.find(q => q.type === 'portal');
  const e = { remote: true, peer: p.id, name: m.name, lvl: m.lvl, look: m.look, x: o ? o.x + 1.6 : 1, y: o ? o.y + 1.6 : 1, r: 0.28, dir: 0, anim: 0,
    moving: false, hp: 1, maxHp: 1, dyingT: null, lunge: 0, hitT: 0, ironT: 0, buf: [], swing: null, using: null };
  if (m.look && m.look !== 'hero') loadCast(m.look);
  return e;
}
function remoteState(p, m) {
  const e = p.hero; e.buf.push(m); if (e.buf.length > 30) e.buf.shift();
  e.hp = m.hp; e.maxHp = m.mh; e.lvl = m.lv; if (m.l !== e.look) { e.look = m.l; if (m.l !== 'hero') loadCast(m.l); }
  e.dyingT = m.dy ? 0.5 : null; e.away = !!m.aw;
}
function netFrame(dt) {   // every frame: move the other heroes to where they were NET_CFG.delay ms ago (their clock)
  if (!G || !G.heroes) return;
  for (const p of NET.peers.values()) {
    if (!p.hero && p.hello && G.rift && G.map) { p.hero = remoteHero(p, p.hello); G.heroes.push(p.hero); log(p.hello.name + ' (level ' + p.hello.lvl + ') is in the Rift.', '#b49ae6'); }
    const e = p.hero; if (!e || !e.buf.length) continue;
    const t = netNow() + p.off - NET_CFG.delay, b = e.buf;
    let i = b.length - 1; while (i > 0 && b[i - 1].c > t) i--;
    let x, y, s = b[i];
    if (i > 0 && b[i].c >= t) { const a = b[i - 1], k = Math.max(0, Math.min(1, (t - a.c) / Math.max(1, b[i].c - a.c))); x = a.x + (b[i].x - a.x) * k; y = a.y + (b[i].y - a.y) * k; s = k < 0.5 ? a : b[i]; }
    else { const a = b[Math.max(0, i - 1)], dtm = Math.min(250, t - s.c), v = s.c > a.c ? (dtm / (s.c - a.c)) : 0; x = s.x + (s.x - a.x) * v; y = s.y + (s.y - a.y) * v; }   // late: carry on for at most 250 ms
    const step = Math.hypot(x - e.x, y - e.y); e.x = x; e.y = y; e.dir = s.d; e.moving = !!s.m;
    if (e.moving) { const lk = heroLook(e); e.anim += step * (META.characters[lk].fpt || 2) / lookScale(lk); }
  }
}
function drawRemoteLabels() {   // a name and a small life bar over each other hero (after the light)
  if (!G || !G.heroes) return;
  for (const e of G.heroes) if (e.remote) {
    const [sx, sy] = iso(e.x, e.y), y = sy - 128;
    ctx.font = '13px "IM Fell English", serif'; ctx.textAlign = 'center'; ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(0,0,0,0.85)';
    ctx.strokeText(e.name, sx, y); ctx.fillStyle = '#c9b0f0'; ctx.fillText(e.name, sx, y);
    const k = Math.max(0, Math.min(1, e.hp / Math.max(1, e.maxHp)));
    ctx.fillStyle = 'rgba(0,0,0,0.7)'; ctx.fillRect(sx - 20, y + 4, 40, 4); ctx.fillStyle = e.dyingT != null ? '#ff3020' : '#7fd17f'; ctx.fillRect(sx - 20, y + 4, 40 * k, 4);
  }
}

// =====================================================================================
//  Monsters in the Rift (multiplayer.md §5–6). Each monster has a network id (m.nid, "<peer>.<n>"); one we own has
//  no m.owner and runs its AI here; one another player owns has m.owner (their peer id) and is only predicted from
//  their states (remoteMonster). Hits on it go to its owner, who decides its life and its death (and shares out
//  its experience); its owner's monsters strike other heroes by telling those heroes' players.
// =====================================================================================
const MON_NET = { batch: 25, near: 14, mid: 30, wNear: 1, wMid: 0.3, wFar: 0.05, snap: 2, blend: 8, share: 0.25, credit: 30 };
const netOn = () => NET.on && G && G.rift && NET.peers.size > 0;
function netOwnAll() {   // our monsters, floor items and loot objects (chests, urns, bones, gold) get ids
  for (const m of G.monsters) if (!m.nid) { m.nid = NET.me + '.' + (++NET.monN); NET.mons.set(m.nid, m); }
  for (const fi of G.items) if (!fi.nid) { fi.nid = NET.me + '.' + (++NET.monN); NET.loot.set(fi.nid, fi); }
  for (const o of G.objects) if (LOOT_OBJ.has(o.type) && !o.nid) { o.nid = NET.me + '.' + (++NET.monN); NET.loot.set(o.nid, o); }
}
const monDesc = m => ({ i: m.nid, o: m.owner || NET.me, ty: m.type, x: +m.x.toFixed(2), y: +m.y.toFixed(2), d: m.lvl, c: m.champ ? 1 : 0, b: m.boss ? 1 : 0,
  n: m.name, mh: m.maxHp, hp: Math.round(m.hp), st: m.state });
function netAddMonster(d, from) {   // a monster another player brought (or, in a snapshot, any monster not ours)
  if (NET.mons.has(d.i) || !G.map) return;
  const m = makeMonster(d.ty, d.x, d.y, d.d, !!d.b, !!d.c, !d.c);
  Object.assign(m, { nid: d.i, owner: d.o === NET.me ? from : d.o, name: d.n, maxHp: d.mh, hp: d.hp, state: d.st || 'idle', ax: d.x, ay: d.y, at: netNow() });
  G.monsters.push(m); NET.mons.set(d.i, m);
}
// ---- Sending our monsters' states: for each player, the most stale ones, weighted by how near they are to that
// player's hero; one whose intent changed (state, path step, target) goes first
const tgtId = e => !e ? null : e === G.hero ? NET.me : e.peer;
function monIntent(m) {   // where it is heading: its next path step, or (walking straight at a hero) that hero
  const tg = m.state === 'chase' ? m.tgt : null;
  const wp = m.path && m.path.length ? m.path[0] : null;
  return { tx: wp ? +wp[0].toFixed(2) : null, ty: wp ? +wp[1].toFixed(2) : null, tg: tgtId(tg) };
}
function netSendMons(p, now) {
  if (!G.rift || !p.ev || p.ev.readyState !== 'open') return;
  const e = p.hero, sent = p.monSent || (p.monSent = new Map()), cand = [];
  for (const m of G.monsters) {
    if (m.owner || !m.nid || m.dead) continue;
    const it = monIntent(m), sig = m.state + '|' + it.tx + '|' + it.ty + '|' + it.tg + '|' + (m.windup > 0 ? 1 : 0) + '|' + (m.frozen ? 1 : 0);
    const last = sent.get(m.nid), dd = e ? Math.hypot(m.x - e.x, m.y - e.y) : 99;
    const w = dd < MON_NET.near ? MON_NET.wNear : dd < MON_NET.mid ? MON_NET.wMid : MON_NET.wFar;
    const pr = !last || last.sig !== sig ? Infinity : (now - last.t) * w;
    cand.push([pr, m, it, sig]);
  }
  cand.sort((a, b) => b[0] - a[0]);
  const a = [];
  for (const [pr, m, it, sig] of cand.slice(0, MON_NET.batch)) {
    if (pr < 60) break;   // sent less than 60 ms·weight ago: nothing new
    sent.set(m.nid, { t: now, sig });
    a.push([m.nid, +m.x.toFixed(2), +m.y.toFixed(2), Math.round(m.hp), m.state === 'chase' ? 1 : 0, it.tx, it.ty, it.tg, +(m.speed * (m.chargeT > 0 ? CHARGE.mult : 1)).toFixed(2), m.windup > 0 ? 1 : 0, m.dir]);
  }
  if (a.length) netSend(p, { t: 'ms', c: now, a });
}
// ---- Receiving: the owner's latest state; the copy is drawn where that state says it would be by now
function netMonStates(p, msg) {
  for (const [i, x, y, hp, ch, tx, ty, tg, sp, wu, dir] of msg.a) {
    const m = NET.mons.get(i); if (!m || !m.owner || m.dead) continue;
    m.ax = x; m.ay = y; m.at = netNow(); m.tx = tx; m.ty = ty; m.tg = tg; m.sp = sp; m.hp = hp; m.wu = wu; m.netDir = dir;
    m.state = ch ? 'chase' : 'idle';
    if (Math.hypot(m.x - x, m.y - y) > MON_NET.snap) { m.x = x; m.y = y; }
  }
}
const heroById = id => id == null ? null : id === NET.me ? G.hero : G.heroes.find(e => e.remote && e.peer === id) || null;
function monReckon(m, t) {   // its state's position carried on along its intent for t seconds
  let x = m.ax, y = m.ay, gx = m.tx, gy = m.ty, stop = 0.05;
  if (gx == null && m.tg) { const e = heroById(m.tg); if (e) { gx = e.x; gy = e.y; stop = m.r + 0.28 + (m.b.reach || 0.5) * 0.8; } }
  if (gx == null || !m.sp) return [x, y, false];
  const dx = gx - x, dy = gy - y, d = Math.hypot(dx, dy), go = Math.min(Math.max(0, d - stop), m.sp * t);
  return go > 0.01 ? [x + dx / d * go, y + dy / d * go, true] : [x, y, false];
}
function remoteMonster(m, dt) {   // called from updateMonster for a monster another player owns
  m.hitT = Math.max(0, m.hitT - dt); m.lunge = Math.max(0, m.lunge - dt * 4);
  if (m.dead) { m.deathT += dt; return; }
  if (m.orphan) { m.moving = false; return; }   // its owner left: it waits for the handover
  if (m.thaw > 0) m.thaw -= dt;
  if (frozenTick(m, dt)) return;
  if (m.ax == null) return;
  const t = Math.min(1, (netNow() - m.at) / 1000), [x, y, mv] = monReckon(m, t), k = Math.min(1, dt * MON_NET.blend);
  const ox = m.x, oy = m.y; m.x += (x - m.x) * k; m.y += (y - m.y) * k;
  m.moving = mv && Math.hypot(m.x - ox, m.y - oy) > 0.002;
  if (m.moving) setDir(m, m.x - ox, m.y - oy); else if (m.netDir != null) m.dir = m.netDir;
  m.windup = m.wu ? 0.1 : 0;
}
// ---- Hits
function netHit(m, v, crit, fire) {   // our hero struck a monster another player owns: its owner applies it
  const p = NET.peers.get(m.owner); if (p) netSend(p, { t: 'hit', i: m.nid, v, c: crit ? 1 : 0, f: fire ? 1 : 0 });
  m.hp = Math.max(1, m.hp - v);   // until its owner's next state says
}
function credit(m, who, v) { const c = m.dmgBy || (m.dmgBy = {}), e = c[who] || (c[who] = { v: 0, t: 0 }); e.v += v; e.t = G.time; }
function netTakeHit(m, v, crit, fire, from) {   // another player's hero struck one of our monsters (already through its armor)
  if (m.dead) return;
  m.hp -= v; m.hitT = fire ? 0.1 : 0.14; m.lastHit = G.time; credit(m, from, v);
  floatText(m.x, m.y, crit ? v + '!' : '' + v, fire ? '#ff9a40' : crit ? '#ffd36a' : '#f2e6d0', 0.8, crit ? 20 : 15);
  if (m.hp > 0) monsterVoice(m, 'hurt');
  alert(m, true);
  if (m.hp <= 0) killMonster(m);
}
// The experience of a monster we own that died: shared by those who hurt it in the last MON_NET.credit s, each by
// its share of the damage, but at least MON_NET.share of it. Returns our own share (all of it with no one else).
function netKillShares(m) {
  const c = m.dmgBy || {}, live = Object.entries(c).filter(([k, e]) => G.time - e.t <= MON_NET.credit && (k === 'me' || NET.peers.has(k)));
  const tot = live.reduce((s, [, e]) => s + e.v, 0);
  if (!netOn() || !live.some(([k]) => k !== 'me') || tot <= 0) { if (netOn() && m.nid) netEach({ t: 'died', i: m.nid }); return m.xp; }
  const xp = {}; for (const [k, e] of live) xp[k === 'me' ? NET.me : k] = Math.max(1, Math.round(m.xp * Math.max(MON_NET.share, e.v / tot)));
  netEach({ t: 'died', i: m.nid, xp });
  return xp[NET.me] || 0;
}
const netEach = msg => { for (const p of NET.peers.values()) netSend(p, msg); };
function netRemoteDied(m, xp) {   // a monster another player owns died (its owner says)
  if (m.dead) return;
  m.dead = true; m.deathT = 0; m.hp = 0; m.frozen = null; m.windup = 0;
  if (m.type === 'skeleton' || m.type === 'ghoul') monsterVoice(m, 'die'); else sfx('die', { x: m.x, y: m.y });
  if (xp > 0) { G.hero.kills++; gainXp(xp); floatText(m.x, m.y - 0.3, '+' + xp + ' xp', '#c9b37a', 1.1, 13); }
  NET.mons.delete(m.nid);
}
// Which hero a monster we own goes for: the one it is after while it still can (alive, in the Rift, within 20
// tiles), unless another is less than 60 % as far; when choosing, the nearest it can see within 8.5 tiles, else
// the nearest. Our own hero when alone.
function pickTarget(m) {
  const hs = G.heroes.filter(e => e === G.hero ? !G.dead && !NET.awaySince : e.remote && !e.away);   // (an away hero is left alone)
  if (!hs.length) return G.hero;
  if (hs.length === 1) return hs[0];
  const d = e => Math.hypot(e.x - m.x, e.y - m.y);
  let best = null, bd = 1e9; for (const e of hs) { const v = d(e); if (v < bd) { bd = v; best = e; } }
  const cur = m.tgt && hs.includes(m.tgt) ? m.tgt : null;
  if (cur && d(cur) < 20 && !(bd < 0.6 * d(cur))) return cur;
  if (!cur) { let seen = null, sd = 1e9; for (const e of hs) { const v = d(e); if (v < 8.5 && v < sd && los(m.x, m.y, e.x, e.y)) { sd = v; seen = e; } } if (seen) best = seen; }
  return best;
}
function hitHero(e, raw, m) {   // a monster we own strikes a hero: ours, or another player's (their browser applies it)
  if (!e.remote) return damageHero(raw, m);
  const p = NET.peers.get(e.peer); if (p) netSend(p, { t: 'hh', v: raw, lvl: m.lvl });
}
function netFreeze(m, dl, du) {   // our frost froze a monster: tell its owner (who tells the others), or, ours, everyone
  if (!netOn() || !m.nid) return;
  const msg = { t: 'frz', i: m.nid, dl, du };
  if (m.owner) { const p = NET.peers.get(m.owner); if (p) netSend(p, msg); } else netEach(msg);
}

// =====================================================================================
//  Loot in the Rift (multiplayer.md §5): floor items, gold, chests, urns and bones belong to whoever brought them
//  (dropped, rolled from their monster or chest, or placed in their rooms) and are seen by all. Taking or opening one
//  another player owns asks that player first; the first to ask gets it. The owner tells everyone the outcome.
// =====================================================================================
const LOOT_OBJ = new Set(['chest', 'urn', 'bones', 'gold']);
const itemOut = it => JSON.parse(JSON.stringify(it));
function netElder() {   // the player in the Rift longest (ourselves included)
  let id = NET.me, since = NET.since;
  for (const p of NET.peers.values()) { const s = p.info && p.info.since; if (s != null && (s < since || s === since && p.id < id)) { since = s; id = p.id; } }
  return id;
}
function netDropped(fi, o) {   // dropItem / dropGold made something of ours: an id, and the others see it
  if (!G || !G.rift || !NET.me) return;
  const x = fi || o; x.nid = NET.me + '.' + (++NET.monN); NET.loot.set(x.nid, x);
  if (!netOn()) return;
  if (fi) netEach({ t: 'drop', i: fi.nid, it: itemOut(fi.item), x: +fi.x.toFixed(2), y: +fi.y.toFixed(2) });
  else netEach({ t: 'drop', i: o.nid, gold: o.amount, x: +o.fx.toFixed(2), y: +o.fy.toFixed(2) });
}
function netGotDrop(m, owner) {   // something another player dropped
  if (!G.map || NET.loot.has(m.i)) return;
  if (m.gold != null) { const o = { type: 'gold', x: Math.floor(m.x), y: Math.floor(m.y), fx: m.x, fy: m.y, amount: m.gold, used: false, block: false, nid: m.i, owner }; G.objects.push(o); NET.loot.set(m.i, o); }
  else { const fi = { item: m.it, x: m.x, y: m.y, t: rnd() * 6, nid: m.i, owner }; G.items.push(fi); NET.loot.set(m.i, fi); }
}
const lootHere = x => G.items.includes(x) || G.objects.includes(x);
function lootGone(x) {   // off the floor everywhere it shows
  const i = G.items.indexOf(x); if (i >= 0) G.items.splice(i, 1);
  if (x.type === 'gold') { const j = G.objects.indexOf(x); if (j >= 0) G.objects.splice(j, 1); }
  NET.loot.delete(x.nid);
}
// Before act0: true when the deed is another player's to grant (we asked), or must not happen
function netAct(ref) {
  if (!netOn()) return false;
  const x = ref.r; if (!x || !x.nid || !x.owner) return false;
  if (ref.kind === 'item') {
    if (!G.items.includes(x)) return true;
    const it = x.item, fits = h => h.inv.includes(null) || (it.slot === 'use' && stackOf(it.pot, it.depth)) || (isBomb(it) && bombStack());
    if (!fits(G.hero)) { log('Your pack is full.', '#e06a5a'); return true; }
    if (!x.asked || G.time - x.asked > 2) { x.asked = G.time; x.equip = !!ref.equip; netSendOwner(x, { t: 'take', i: x.nid }); }
    return true;
  }
  if (x.type === 'gold') { if (!x.asked || G.time - x.asked > 2) { x.asked = G.time; netSendOwner(x, { t: 'take', i: x.nid }); } return true; }
  if (LOOT_OBJ.has(x.type)) {
    if (x.used) return true;
    if (x.type === 'chest' && x.boss && G.map.boss && !G.map.boss.dead) return false;   // (sealed: act0 says so)
    if (!x.asked || G.time - x.asked > 2) { x.asked = G.time; netSendOwner(x, { t: 'use', i: x.nid }); }
    return true;
  }
  return false;
}
function netSendOwner(x, msg) { const p = NET.peers.get(x.owner); if (p) netSend(p, msg); }
// After act0 on something of ours (or nobody's): tell the others what changed
function netActed(ref, was) {
  if (!netOn()) return;
  const x = ref.r; if (!x) return;
  if (ref.kind === 'item') { if (was && !G.items.includes(x) && x.nid) { netEach({ t: 'took', i: x.nid, to: NET.me }); NET.loot.delete(x.nid); } return; }
  if (x.type === 'gold') { if (was.here && !G.objects.includes(x) && x.nid) { netEach({ t: 'took', i: x.nid, to: NET.me }); NET.loot.delete(x.nid); } return; }
  if (x.type === 'door') { if (!was.open && x.open) netEach({ t: 'door', x: x.x, y: x.y }); return; }
  if (LOOT_OBJ.has(x.type) && !was.used && x.used && x.nid) netEach({ t: 'used', i: x.nid, by: NET.me });
}
function netTakeReq(m, p) {   // another player asks for something of ours lying on the floor: the first to ask gets it
  const x = NET.loot.get(m.i);
  if (!x || x.owner || !lootHere(x)) { netSend(p, { t: 'took', i: m.i, to: null }); return; }
  lootGone(x); netEach({ t: 'took', i: m.i, to: p.id });
  if (x.type !== 'gold') log((p.info && p.info.name || 'Someone') + ' picked up ' + x.item.name + '.', '#a99c86');
}
function netTook(m) {   // the owner says who got it
  const x = NET.loot.get(m.i); if (!x) return;
  if (m.to === null) { x.asked = 0; if (!lootHere(x)) NET.loot.delete(m.i); log('Someone was quicker.', '#a99c86'); return; }
  if (m.to !== NET.me) { lootGone(x); return; }
  if (x.type === 'gold') { lootGone(x); G.hero.gold += x.amount; sfx('gold'); floatText(G.hero.x, G.hero.y, '+' + x.amount + ' gold', '#e3c060', 0.9, 14); refreshUI(); return; }
  x.item.id = nextId++;   // ours now: an id of our own
  NET.loot.delete(m.i); act0({ kind: 'item', r: x, equip: x.equip });
  if (G.items.includes(x)) { delete x.owner; x.asked = 0; netDropped(x); }   // no room after all: it lies at our feet, ours
}
function netUseReq(m, p) {   // another player opens one of our chests (breaks an urn, searches bones): the first one does
  const o = NET.loot.get(m.i); if (!o || o.owner || o.used || !lootHere(o)) return;
  act0({ kind: 'obj', r: o }, true);   // we roll what is in it (and drop it: the drops are ours, seen by all)
  if (o.used) netEach({ t: 'used', i: o.nid, by: p.id });
}
function netUsed(m) {   // someone opened a chest, broke an urn or searched bones
  const o = NET.loot.get(m.i); if (!o || o.used) return;
  o.used = true; o.asked = 0;
  const d = G.depth, mine = m.by === NET.me;
  if (o.type === 'chest') { sfx('chest', { x: o.x, y: o.y }); if (mine) { gainXp((o.boss ? 15 : 6) * d); log('The chest creaks open.', '#c9a45c'); } }
  else if (o.type === 'urn') { G.map.block[o.y * G.map.w + o.x] = 0; sfx('urn', { x: o.x, y: o.y }); if (mine) gainXp(2 * d);
    for (let i = 0; i < 8; i++) G.fx.push({ type: 'spark', x: o.x + 0.5, y: o.y + 0.5, vx: (rnd() - 0.5) * 3, vy: (rnd() - 0.5) * 3, z: 20, vz: 80, t: 0, dur: 0.5, color: '140,120,90' }); }
  else if (o.type === 'bones' && mine) { gainXp(d); log('You search the bones.', '#a99c86'); }
}
