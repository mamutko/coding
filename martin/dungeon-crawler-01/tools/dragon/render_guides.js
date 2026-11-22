// Renders the painting guides for the dragon's parts from dragon-prototype.html's own placeholder body, so the
// painted parts fit the prototype exactly: grey shapes in the 8 game directions (S, SW, W, NW, N, NE, E, SE), 4 x 2
// cells of 384 x 512 on white. Writes art/characters/dragon/guide/<part>.png and guide/guides.json (cell size, scale,
// and where in each cell the part's anchor lands, for drawing the paintings back in the game).
//   node tools/dragon/render_guides.js            (from martin/dungeon-crawler-01; uses the pre-installed Playwright)
// Parts: torso (shoulders to hips with short neck and tail stumps, ×1.6), head (jaw closed, ×2.4), headopen (jaw open, ×2.4).
// Each part's middle is at its cell's middle; the anchor (its ground point) is below that, maybe outside the cell.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '../..'), out = path.join(root, 'art/characters/dragon/guide');
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch(), p = await b.newPage();
  await p.goto('file://' + path.join(root, 'dragon-prototype.html')); await p.waitForFunction(() => typeof DR !== 'undefined' && DR);
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
