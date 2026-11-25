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
  delay: 100,        // ms other heroes are drawn in the past (interpolated between their states)
  chunk: 16000,      // characters per snapshot piece
};
const NET = { sb: null, libP: null, ch: null, topic: null, me: null, since: 0, peers: new Map(), on: false, timer: null, snapIn: null };
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
  NET.peers.clear(); NET.on = false; clearInterval(NET.timer); NET.timer = null;
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
function netSend(p, m) { const dc = m.t === 'st' || m.t === 'ping' || m.t === 'pong' ? p.st : p.ev; if (dc && dc.readyState === 'open') try { dc.send(JSON.stringify(m)); } catch (e) {} }
function netDropPeer(p, quiet) {
  if (NET.peers.get(p.id) === p) NET.peers.delete(p.id);
  try { p.pc && p.pc.close(); } catch (e) {}
  if (p.hero && G && G.heroes) { const i = G.heroes.indexOf(p.hero); if (i >= 0) G.heroes.splice(i, 1);
    if (!quiet && G.rift) log(p.hero.name + ' has left the Rift.', '#b49ae6'); }
  p.hero = null;
}

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
    dy: h.dyingT != null ? 1 : 0, l: h.look || 'hero', lv: h.lvl };
  for (const p of [...NET.peers.values()]) {
    if (now - p.last > NET_CFG.drop && (p.hero || now - p.last > NET_CFG.connectWait)) { netDropPeer(p); continue; }
    netSend(p, st);
    if (!p.pinged || now - p.pinged > NET_CFG.ping) { p.pinged = now; netSend(p, { t: 'ping', a: now }); }
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
  e.dyingT = m.dy ? 0.5 : null;
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
