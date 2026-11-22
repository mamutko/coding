// Renders the painting guides for the dragon's parts from dragon-prototype.html's own placeholder body, so the
// painted parts fit the prototype exactly: grey shapes in the 8 game directions (S, SW, W, NW, N, NE, E, SE), 4 x 2
// cells of 384 x 512 on white. Writes art/characters/dragon/guide/<part>.png and guide/guides.json (cell size, scale,
// and where in each cell the part's anchor lands, for drawing the paintings back in the game).
//   node tools/dragon/render_guides.js            (from martin/dungeon-crawler-01; uses the pre-installed Playwright)
//   node tools/dragon/render_guides.js body16          the body for the game: guide/body16.png, body16.full.png, limbs.png,
//                                                 feet.png and body16.json (see "body16" below)
// Parts: torso (shoulders to hips with short neck and tail stumps, ×1.6), head (jaw closed, ×2.4), headopen (jaw open, ×2.4).
// Each part's middle is at its cell's middle; the anchor (its ground point) is below that, maybe outside the cell.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '../..'), out = path.join(root, 'art/characters/dragon/guide');
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch(), p = await b.newPage();
  await p.goto('file://' + path.join(root, 'dragon-prototype.html')); await p.waitForFunction(() => typeof DR !== 'undefined' && DR);
  if (process.argv[2] === 'body16') return body16(b, p);
  const res = await p.evaluate(() => {
    const CW = 384, CH = 512, DIRS = ['S', 'SW', 'W', 'NW', 'N', 'NE', 'E', 'SE'];
    Object.assign(COL, { hi: '#e2e2e2', mid: '#9a9a9a', lo: '#454545', rim: '#5a5a5a', spike: '#c8c8c8', bone: '#555', claw: '#eee' });
    O.mode = 'still'; O.spine = 'body'; O.size = 1; O.look = 'shapes';
    const parts = {
      torso: { scale: 1.6, jaw: 0, nodes: [SH - 1, SH, SH + 1, SH + 2, HIPS, HIPS + 1] },
      head: { scale: 2.4, jaw: 0, nodes: [0] },
      headopen: { scale: 2.4, jaw: 1, nodes: [0] } };
    const meta = { cell: [CW, CH], cols: 4, rows: 2, dirs: DIRS, parts: {} };
    const urls = {};
    for (const [name, P] of Object.entries(parts)) {
      const c = document.createElement('canvas'); c.width = CW * 4; c.height = CH * 2;
      const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height);
      meta.parts[name] = { scale: P.scale, anchor: [], note: name === 'torso' ? 'anchor = the ground point under the torso centre' : 'anchor = the ground point under the head node' };
      DIRS.forEach((d, i) => {
        makeDragon(); DR.state = 'awake'; DR.cx = 12; DR.cy = 11; DR.th = Math.PI / 4 + i * Math.PI / 4; DR.turn = 0;
        DR.look = [DR.cx + Math.cos(DR.th) * 9, DR.cy + Math.sin(DR.th) * 9]; DR.na = 0; DR.headZ = 72; DR.jaw = P.jaw; DR.eyes = 1; DR.act = null; DR.flash = 0;
        layout(0.0001, true); DR.ha = DR.th;
        const n = DR.n, c0 = name === 'torso' ? { x: (n[SH].x + n[HIPS].x) / 2, y: (n[SH].y + n[HIPS].y) / 2 } : n[0];
        const zc = name === 'torso' ? (n[SH].z + n[HIPS].z) / 2 : n[0].z;   // the part's middle goes to the cell's middle
        const [ox, oy] = S3(c0.x, c0.y, 0), cx = (i % 4) * CW + CW / 2, cy = Math.floor(i / 4) * CH + CH / 2 + zc * P.scale;
        g.save(); g.beginPath(); g.rect((i % 4) * CW, Math.floor(i / 4) * CH, CW, CH); g.clip();
        g.translate(cx, cy); g.scale(P.scale, P.scale); g.translate(-ox, -oy);
        P.nodes.slice().sort((a, b) => n[a].x + n[a].y - n[b].x - n[b].y).forEach(k => {
          if (k === 0) drawHead(g, n[0]); else { const q = n[k], [x, y] = S3(q.x, q.y, q.z); blob(g, x, y, q.R, null); if (P.nodes.includes(k - 1)) capsule(g, q, n[k - 1]); blob(g, x, y, q.R * 0.999, null); }
        });
        g.restore();
        meta.parts[name].anchor.push([cx, cy]);
      });
      urls[name] = c.toDataURL('image/png');
    }
    return { meta, urls };
  });
  for (const [k, u] of Object.entries(res.urls)) fs.writeFileSync(path.join(out, k + '.png'), Buffer.from(u.split(',')[1], 'base64'));
  fs.writeFileSync(path.join(out, 'guides.json'), JSON.stringify(res.meta, null, 1));
  console.log('wrote', Object.keys(res.urls).join(', '), 'to', out);
  await b.close();
})();
// ---- body16: the body for separate legs, 16 directions; and the leg pieces (limbs, feet)
// guide/body16.png: the torso (with short neck and tail stumps and the tops of the four legs, which the painted
// thigh pieces cover) standing still, in the 9 directions S, SSW, SW, WSW, W, WNW, NW, NNW, N (the other 7 are
// mirrored), heading th = PI/4 + i * PI/8, in 3 x 3 cells of 512 x 341, ×BODY.scale; anchor = the ground point
// under the torso centre. guide/limbs.png: the leg bones upright, top joint up (front upper, front lower, hind upper,
// hind lower), ×LEGS.scale, in 4 columns of 384 x 1024. guide/feet.png: a clawed foot in the 8 directions (S, SW, W ...
// SE, the way the body faces), ×LEGS.scale, 4 x 2 cells of 384 x 512; anchor = the ankle's ground point.
// The leg geometry (also in the game): the hip at the side of the shoulders or hips node (r × 0.7 out, R × 0.25
// below its centre), upper bone LEG.l1, lower bone LEG.l2 (px), the knee bending back on the front legs, forward on
// the hind legs; the foot 0.08 tile wide of the ground point under the hip and a little ahead.
const BODY = { scale: 1.3, cw: 512, ch: 341, stub: 0.3 };
// the leg bones: [front?, name, -, width at the top, at the bottom (× the shoulders' or hips' node R)]
const LIMBS = [[true, 'front upper', 0, 0.8, 0.55], [true, 'front lower', 0, 0.55, 0.4], [false, 'hind upper', 0, 0.95, 0.58], [false, 'hind lower', 0, 0.56, 0.4]];
const LEGS = { scale: 7, foot: 0.85 };
async function body16(b, p) {
  const res = await p.evaluate(([B, LG, LIMBS]) => {
    function taper(gg, a, b, w0, w1) {   // a bone from a to b (screen), w0 wide at a, w1 at b, round ends, lit from the left
      const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1, nx = -dy / l, ny = dx / l;
      const gr = gg.createLinearGradient(a[0] - Math.abs(nx) * w0, a[1], a[0] + Math.abs(nx) * w0, a[1]); gr.addColorStop(0, '#d8d8d8'); gr.addColorStop(0.45, '#9a9a9a'); gr.addColorStop(1, '#404040');
      gg.fillStyle = Math.abs(nx) > 0.3 ? gr : '#9a9a9a'; gg.beginPath(); gg.moveTo(a[0] + nx * w0 / 2, a[1] + ny * w0 / 2); gg.lineTo(b[0] + nx * w1 / 2, b[1] + ny * w1 / 2); gg.lineTo(b[0] - nx * w1 / 2, b[1] - ny * w1 / 2); gg.lineTo(a[0] - nx * w0 / 2, a[1] - ny * w0 / 2); gg.closePath(); gg.fill();
      gg.beginPath(); gg.arc(a[0], a[1], w0 / 2, 0, 7); gg.fill(); gg.beginPath(); gg.arc(b[0], b[1], w1 / 2, 0, 7); gg.fill();
    }
    Object.assign(COL, { hi: '#e2e2e2', mid: '#9a9a9a', lo: '#454545', rim: '#5a5a5a', spike: '#c8c8c8', bone: '#555', claw: '#eee' });
    O.mode = 'still'; O.spine = 'body'; O.size = 1; O.look = 'shapes'; O.legs = true;
    const urls = {}, meta = { body: { cell: [B.cw, B.ch], cols: 3, rows: 3, scale: B.scale, dirs: ['S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW', 'N'], anchor: [] } };
    function ik(L) {   // the leg's hip, knee and ankle in 3D (tiles * P, px), as drawLeg works them out
      const fr = legFrame(L), H = [fr.attach[0] * P, fr.attach[1] * P, fr.az], F = [L.foot[0] * P, L.foot[1] * P, 0], L1 = 44, L2 = 42;
      let dx = F[0] - H[0], dy = F[1] - H[1], dz = F[2] - H[2], d = Math.hypot(dx, dy, dz);
      const u = [dx / d, dy / d, dz / d]; d = Math.min(d, L1 + L2 - 0.01);
      const a = (L1 * L1 - L2 * L2 + d * d) / (2 * d), hg = Math.sqrt(Math.max(0, L1 * L1 - a * a)), fb = L.front ? -0.8 : 0.8;
      let bb = [fr.f[0] * fb + fr.nr[0] * L.side * 0.5, fr.f[1] * fb + fr.nr[1] * L.side * 0.5, 0.25];
      const bd = bb[0] * u[0] + bb[1] * u[1] + bb[2] * u[2]; bb = [bb[0] - u[0] * bd, bb[1] - u[1] * bd, bb[2] - u[2] * bd];
      const bl = Math.hypot(...bb) || 1; bb = bb.map(v => v / bl);
      const K = [H[0] + u[0] * a + bb[0] * hg, H[1] + u[1] * a + bb[1] * hg, H[2] + u[2] * a + bb[2] * hg];
      const s = q => S3(q[0] / P, q[1] / P, q[2]);
      return { H, K, F, pH: s(H), pK: s(K), pF: s(F), fr };
    }
    // the body
    const c = document.createElement('canvas'); c.width = B.cw * 3; c.height = 1024;
    const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height);
    const full = document.createElement('canvas'); full.width = c.width; full.height = c.height;   // with whole legs, to check
    const gf = full.getContext('2d'); gf.fillStyle = '#fff'; gf.fillRect(0, 0, c.width, c.height);
    for (let i = 0; i < 9; i++) {
      makeDragon(); DR.state = 'awake'; DR.cx = 12; DR.cy = 11; DR.th = Math.PI / 4 + i * Math.PI / 8; DR.turn = 0; DR.vel = [0, 0]; DR.t = 0;
      DR.look = [DR.cx + Math.cos(DR.th) * 9, DR.cy + Math.sin(DR.th) * 9]; DR.na = 0; DR.act = null; DR.flash = 0;
      layout(0.0001, true);
      for (const L of DR.legs) L.foot = legFrame(L).home.slice();
      const n = DR.n, c0 = { x: (n[SH].x + n[HIPS].x) / 2, y: (n[SH].y + n[HIPS].y) / 2 }, zc = (n[SH].z + n[HIPS].z) / 2 * 0.6;
      const [ox, oy] = S3(c0.x, c0.y, 0), cx = (i % 3) * B.cw + B.cw / 2, cy = Math.floor(i / 3) * B.ch + B.ch / 2 + zc * B.scale;
      for (const [gg, whole] of [[g, false], [gf, true]]) {
        gg.save(); gg.beginPath(); gg.rect((i % 3) * B.cw, Math.floor(i / 3) * B.ch, B.cw, B.ch); gg.clip();
        gg.translate(cx, cy); gg.scale(B.scale, B.scale); gg.translate(-ox, -oy);
        const dl = [];
        for (let k = SH - 1; k <= HIPS + 1; k++) dl.push({ k: n[k].x + n[k].y, f: () => { const q = n[k], [x, y] = S3(q.x, q.y, q.z); blob(gg, x, y, q.R, null); if (k > SH - 1) capsule(gg, q, n[k - 1]); blob(gg, x, y, q.R * 0.999, null); } });
        for (const L of DR.legs) {
          const r = ik(L), R = r.fr.node.R;
          dl.push({ k: (r.fr.attach[0] + r.fr.attach[1] + L.foot[0] + L.foot[1]) / 2 + 0.02, f: () => {
            if (whole) return LIMBS.forEach(([fr, a, b, w0, w1], j) => (fr === L.front) && taper(gg, j % 2 ? r.pK : r.pH, j % 2 ? r.pF : r.pK, w0 * R, w1 * R));
            // the top of the leg: a shoulder / haunch muscle on the flank, which the painted upper bone covers
            const e = [r.pH[0] + (r.pK[0] - r.pH[0]) * B.stub, r.pH[1] + (r.pK[1] - r.pH[1]) * B.stub];
            blob(gg, e[0], e[1], R * (L.front ? 0.44 : 0.52), null);
          } });
        }
        dl.sort((a, b) => a.k - b.k).forEach(x => x.f());
        gg.restore();
      }
      meta.body.anchor.push([cx, cy]);
    }
    urls.body16 = c.toDataURL('image/png'); urls['body16.full'] = full.toDataURL('image/png');
    // the limbs, upright: [length px, width px (× the node's R)]
    const lc = document.createElement('canvas'); lc.width = 1536; lc.height = 1024; const l = lc.getContext('2d'); l.fillStyle = '#fff'; l.fillRect(0, 0, 1536, 1024);
    meta.limbs = { scale: LG.scale, pieces: [] };
    LIMBS.forEach(([front, name, , w0, w1], j) => {
      const R = DR.n[front ? SH : HIPS].R, len = j % 2 ? 42 : 44, x = j * 384 + 192, y0 = 512 - len * LG.scale / 2, y1 = 512 + len * LG.scale / 2;
      taper(l, [x, y0], [x, y1], w0 * R * LG.scale, w1 * R * LG.scale);
      meta.limbs.pieces.push({ name, len, w0: +(w0 * R).toFixed(1), w1: +(w1 * R).toFixed(1), top: [x, y0], bottom: [x, y1] });
    });
    urls.limbs = lc.toDataURL('image/png');
    // the feet: toes on the floor from the ankle's ground point, an ankle stub up to the lower bone
    const fc = document.createElement('canvas'); fc.width = 1536; fc.height = 1024; const fg = fc.getContext('2d'); fg.fillStyle = '#fff'; fg.fillRect(0, 0, 1536, 1024);
    meta.feet = { cell: [384, 512], scale: LG.scale * LG.foot, size: LG.foot, dirs: ['S', 'SW', 'W', 'NW', 'N', 'NE', 'E', 'SE'], anchor: [], ankle: 16 };
    for (let i = 0; i < 8; i++) {
      const th = Math.PI / 4 + i * Math.PI / 4, f = [Math.cos(th), Math.sin(th)], nr = [-f[1], f[0]];
      const cx = (i % 4) * 384 + 192, cy = Math.floor(i / 4) * 512 + 330, sc = LG.scale * LG.foot;
      const S = (x, y, z) => { const [a, bq] = S3(x, y, z); return [cx + a * sc, cy + bq * sc]; };
      const parts = [];
      for (const [a, len, w] of [[-0.55, 0.2, 8], [0, 0.24, 9], [0.55, 0.2, 8], [Math.PI, 0.09, 6]]) {
        const dx = f[0] * Math.cos(a) + nr[0] * Math.sin(a), dy = f[1] * Math.cos(a) + nr[1] * Math.sin(a);
        parts.push({ k: dx + dy, f: () => {
          const p0 = S(0, 0, 4), p1 = S(dx * len, dy * len, 3), p2 = S(dx * (len + 0.08), dy * (len + 0.08), 0);
          fg.lineCap = 'round'; fg.strokeStyle = '#5a5a5a'; fg.lineWidth = w * sc; fg.beginPath(); fg.moveTo(...p0); fg.lineTo(...p1); fg.stroke();
          fg.strokeStyle = '#a0a0a0'; fg.lineWidth = w * sc * 0.55; fg.beginPath(); fg.moveTo(p0[0], p0[1] - 2 * sc); fg.lineTo(p1[0], p1[1] - 2 * sc); fg.stroke();
          fg.strokeStyle = '#f0f0f0'; fg.lineWidth = w * sc * 0.35; fg.beginPath(); fg.moveTo(...p1); fg.lineTo(...p2); fg.stroke();   // the claw
        } });
      }
      parts.push({ k: 0.01, f: () => {   // the pad and the ankle
        const a = S(0, 0, 0); fg.fillStyle = '#6a6a6a'; fg.beginPath(); fg.ellipse(a[0], a[1] - 3 * sc, 11 * sc, 6 * sc, 0, 0, 7); fg.fill();
        const t = S(0, 0, 16); fg.lineCap = 'round'; fg.strokeStyle = '#7a7a7a'; fg.lineWidth = 11 * sc; fg.beginPath(); fg.moveTo(a[0], a[1] - 4 * sc); fg.lineTo(...t); fg.stroke();
        fg.strokeStyle = '#b0b0b0'; fg.lineWidth = 5 * sc; fg.beginPath(); fg.moveTo(a[0] - 2 * sc, a[1] - 5 * sc); fg.lineTo(t[0] - 2 * sc, t[1]); fg.stroke();
      } });
      parts.sort((a, b) => a.k - b.k).forEach(q => q.f());
      meta.feet.anchor.push([cx, cy]);
    }
    urls.feet = fc.toDataURL('image/png');
    return { meta, urls };
  }, [BODY, LEGS, LIMBS]);
  for (const [k, u] of Object.entries(res.urls)) fs.writeFileSync(path.join(out, k + '.png'), Buffer.from(u.split(',')[1], 'base64'));
  fs.writeFileSync(path.join(out, 'body16.json'), JSON.stringify(res.meta, null, 1));
  console.log('wrote', Object.keys(res.urls).join(', '));
  await b.close();
}
