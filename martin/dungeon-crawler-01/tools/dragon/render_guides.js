// Renders the painting guides for the dragon's parts from dragon-prototype.html's own placeholder body, so the
// painted parts fit the prototype exactly: grey shapes in the 8 game directions (S, SW, W, NW, N, NE, E, SE), 4 x 2
// cells of 384 x 512 on white. Writes art/characters/dragon/guide/<part>.png and guide/guides.json (cell size, scale,
// and where in each cell the part's anchor lands, for drawing the paintings back in the game).
//   node tools/dragon/render_guides.js            (from martin/dungeon-crawler-01; uses the pre-installed Playwright)
//   node tools/dragon/render_guides.js walk       the body's walk cycle instead: guide/walk/<DIR>.png for S, SW, W, NW, N
//                                                 and <DIR>.legs.png (the legs alone, for tools/dragon/steady_walk.py)
//                                                 (E, NE, SE are mirrored), 8 frames each in 4 x 2 cells of 384 x 512
// The walk: the torso (with short neck and tail stumps) and the 4 legs, ×1.4; diagonal pairs (front left + hind right,
// then the other two) half a cycle apart; each foot is planted for 60 % of the cycle and swings forward (lifted up to
// 16 px) for 40 %; the body travels WALK.cycle tiles per cycle (frames per tile = 8 / WALK.cycle) and bobs 2 px.
// Parts: torso (shoulders to hips with short neck and tail stumps, ×1.6), head (jaw closed, ×2.4), headopen (jaw open, ×2.4).
// Each part's middle is at its cell's middle; the anchor (its ground point) is below that, maybe outside the cell.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '../..'), out = path.join(root, 'art/characters/dragon/guide');
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch(), p = await b.newPage();
  await p.goto('file://' + path.join(root, 'dragon-prototype.html')); await p.waitForFunction(() => typeof DR !== 'undefined' && DR);
  if (process.argv[2] === 'walk') return walk(b, p);
  const res = await p.evaluate(() => {
    const CW = 384, CH = 512, DIRS = ['S', 'SW', 'W', 'NW', 'N', 'NE', 'E', 'SE'];
    Object.assign(COL, { hi: '#e2e2e2', mid: '#9a9a9a', lo: '#454545', rim: '#5a5a5a', spike: '#c8c8c8', bone: '#555', claw: '#eee' });
    O.mode = 'still'; O.spine = 'body'; O.size = 1;
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
const WALK = { cycle: 1.2, duty: 0.6, scale: 1.4, dirs: ['S', 'SW', 'W', 'NW', 'N'] };
async function walk(b, p) {
  fs.mkdirSync(path.join(out, 'walk'), { recursive: true });
  const res = await p.evaluate(W => {
    const CW = 384, CH = 512, ALL = ['S', 'SW', 'W', 'NW', 'N', 'NE', 'E', 'SE'];
    Object.assign(COL, { hi: '#e2e2e2', mid: '#9a9a9a', lo: '#454545', rim: '#5a5a5a', spike: '#c8c8c8', bone: '#555', claw: '#eee' });
    O.mode = 'still'; O.spine = 'body'; O.size = 1; O.legs = true;
    const meta = { cell: [CW, CH], cols: 4, rows: 2, frames: 8, scale: W.scale, cycle: W.cycle, fpt: 8 / W.cycle, duty: W.duty,
      note: 'anchor = the ground point under the torso centre, the same in every cell of a direction', anchor: {} }, urls = {};
    for (const d of W.dirs) {
      const i = ALL.indexOf(d), c = document.createElement('canvas'); c.width = CW * 4; c.height = CH * 2;
      const mc = document.createElement('canvas'); mc.width = c.width; mc.height = c.height; const mg = mc.getContext('2d'); mg.fillStyle = '#fff'; mg.fillRect(0, 0, mc.width, mc.height);
      const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height);
      meta.anchor[d] = [];
      for (let f = 0; f < 8; f++) {
        makeDragon(); DR.state = 'awake'; DR.cx = 12; DR.cy = 11; DR.th = Math.PI / 4 + i * Math.PI / 4; DR.turn = 0; DR.vel = [0, 0]; DR.t = 0;
        DR.look = [DR.cx + Math.cos(DR.th) * 9, DR.cy + Math.sin(DR.th) * 9]; DR.na = 0; DR.act = null; DR.flash = 0;
        layout(0.0001, true);
        const n = DR.n, bob = 2 * Math.abs(Math.sin(Math.PI * 2 * f / 8));
        for (let k = SH - 1; k <= HIPS + 1; k++) n[k].z += bob;
        for (const L of DR.legs) {
          const fr = legFrame(L), ph = (f / 8 + (L.group ? 0.5 : 0)) % 1, D = W.cycle, st = D * W.duty;
          let off, s = -1;
          if (ph < W.duty) off = st / 2 - ph / W.duty * st; else { const u = (ph - W.duty) / (1 - W.duty); off = -st / 2 + u * st; s = u; }
          L.foot = [fr.home[0] + fr.f[0] * off, fr.home[1] + fr.f[1] * off]; L.st = s;
        }
        const c0 = { x: (n[SH].x + n[HIPS].x) / 2, y: (n[SH].y + n[HIPS].y) / 2 }, zc = (n[SH].z + n[HIPS].z) / 2 * 0.6;
        const [ox, oy] = S3(c0.x, c0.y, 0), cx = (f % 4) * CW + CW / 2, cy = Math.floor(f / 4) * CH + CH / 2 + zc * W.scale;
        g.save(); g.beginPath(); g.rect((f % 4) * CW, Math.floor(f / 4) * CH, CW, CH); g.clip();
        g.translate(cx, cy); g.scale(W.scale, W.scale); g.translate(-ox, -oy);
        const dl = [];
        for (let k = SH - 1; k <= HIPS + 1; k++) dl.push({ k: n[k].x + n[k].y, f: () => { const q = n[k], [x, y] = S3(q.x, q.y, q.z); blob(g, x, y, q.R, null); if (k > SH - 1) capsule(g, q, n[k - 1]); blob(g, x, y, q.R * 0.999, null); } });
        for (const L of DR.legs) { const fr = legFrame(L); dl.push({ k: (fr.attach[0] + fr.attach[1] + L.foot[0] + L.foot[1]) / 2 + 0.02, f: () => drawLeg(g, L) }); }
        dl.sort((a, b) => a.k - b.k).forEach(x => x.f());
        g.restore();
        // the legs alone, for the mask that keeps the rest of the body still (tools/dragon/steady_walk.py)
        mg.save(); mg.translate(cx, cy); mg.scale(W.scale, W.scale); mg.translate(-ox, -oy); for (const L of DR.legs) drawLeg(mg, L); mg.restore();
        meta.anchor[d].push([cx, cy]);
      }
      urls[d] = c.toDataURL('image/png'); urls[d + '.legs'] = mc.toDataURL('image/png');
    }
    return { meta, urls };
  }, WALK);
  for (const [k, u] of Object.entries(res.urls)) fs.writeFileSync(path.join(out, 'walk', k + '.png'), Buffer.from(u.split(',')[1], 'base64'));
  fs.writeFileSync(path.join(out, 'walk', 'walk.json'), JSON.stringify(res.meta, null, 1));
  console.log('wrote walk guides', Object.keys(res.urls).join(', '));
  await b.close();
}
