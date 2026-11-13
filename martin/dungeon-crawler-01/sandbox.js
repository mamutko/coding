// Sandbox: test scenarios for the game in index.html (see README, Sandbox). Loaded by index.html only when the
// address has ?sandbox, and inlined into the Claude artifact by the artifact-sandbox skill's build.py. It runs after the game's
// script and uses its globals; it changes nothing in the game itself. Instead of the title screen it shows a
// scenario picker; a scenario makes a strong test hero (never saved) and drops it into a prepared situation.
(() => {
  const css = document.createElement('style');
  css.textContent = `
  #sbPick { position: fixed; inset: 0; z-index: 60; display: flex; align-items: center; justify-content: center; background: rgba(5,2,4,0.82);
    padding: 16px max(16px, env(safe-area-inset-left, 0px)); overflow-y: auto; }
  #sbPick .box { max-width: 560px; width: 100%; border: 1px solid #5a4528; background: #120c0e; padding: 22px; box-shadow: 0 0 40px #000; }
  #sbPick h1 { font-family: Cinzel, serif; color: #c9a45c; font-size: 22px; letter-spacing: 2px; margin: 0 0 6px; text-wrap: balance; }
  #sbPick p { color: #b3aba0; font: 15px/1.45 'IM Fell English', Georgia, serif; margin: 0 0 14px; }
  #sbPick button.sc { display: block; width: 100%; text-align: left; margin: 0 0 10px; padding: 12px 14px; background: #1c1316; border: 1px solid #5a4528;
    color: #e8dcc4; font: 15px/1.4 'IM Fell English', Georgia, serif; cursor: pointer; }
  #sbPick[hidden], #sbBar[hidden] { display: none !important; }
  #sbPick button.sc:disabled { opacity: 0.5; cursor: wait; }
  #sbPick button.sc:hover, #sbPick button.sc:focus-visible { border-color: #c9a45c; background: #26191c; outline: none; }
  #sbPick button.sc b { display: block; font-family: Cinzel, serif; color: #c9a45c; letter-spacing: 1px; font-size: 15px; margin-bottom: 2px; }
  #sbBar { position: fixed; z-index: 55; left: 50%; transform: translateX(-50%); top: calc(8px + env(safe-area-inset-top, 0px));
    background: rgba(12,8,10,0.85); border: 1px solid #5a4528; color: #e8dcc4; font: 13px/1.35 Georgia, serif; padding: 6px 10px;
    display: flex; gap: 10px; align-items: center; flex-wrap: wrap; justify-content: center; max-width: calc(100vw - 32px); font-variant-numeric: tabular-nums; }
  #sbBar .mood { font-family: Cinzel, serif; color: #c9a45c; letter-spacing: 1px; }
  #sbBar .choir { color: #f3dc8a; text-shadow: 0 0 6px rgba(230,200,74,0.8); }
  #sbBar .burn { color: #ff9a40; text-shadow: 0 0 6px rgba(255,120,40,0.8); }
  #sbLooks { display: flex; gap: 4px; align-items: center; }
  #sbLooks[hidden] { display: none !important; }
  #sbBar #sbLooks button.on { border-color: #e8893a; color: #fff; background: #3a1f12; }
  #sbPick h2 { font-family: Cinzel, serif; color: #8c7650; font-size: 13px; letter-spacing: 2px; margin: 16px 0 8px; }
  #sbBar button { background: #1c1316; border: 1px solid #5a4528; color: #e8dcc4; font: 12px Georgia, serif; padding: 3px 8px; cursor: pointer; }
  #sbBar button:hover, #sbOpen:hover { border-color: #c9a45c; }
  #sbOpen { position: fixed; z-index: 55; left: calc(12px + env(safe-area-inset-left, 0px)); bottom: calc(12px + env(safe-area-inset-bottom, 0px));
    background: #1c1316; border: 1px solid #5a4528; color: #c9a45c; font: 13px Cinzel, serif; letter-spacing: 1px; padding: 6px 12px; cursor: pointer; }
  #sbOpen[hidden] { display: none !important; }
  body.narrow #sbBar { top: auto; bottom: calc(150px + env(safe-area-inset-bottom, 0px)); font-size: 12px; }`;
  document.head.appendChild(css);
  const pick = document.createElement('div'); pick.id = 'sbPick'; pick.innerHTML = `<div class="box">
    <h1>Crypt Sandbox</h1>
    <p>The current game (v${VERSION}) with a strong test hero (never saved), dropped straight into a situation. Sound starts when you pick one. A bar at the top shows what the scenario is about.</p>
    <h2>Fire bombs</h2>
    <button class="sc" id="sbFirePack"><b>Fire bombs: pack fight</b>Depth 3, 15 fire bombs equipped, four skeletons and three ghouls rushing in. Right-click to throw at a monster or a spot (up to 7 tiles). Key 1 is your longsword, 2 the bombs. Mind the flames: they burn you too.</button>
    <button class="sc" id="sbFireLast"><b>Fire bombs: the last two</b>Only two bombs equipped and three skeletons coming. After the second throw your hands are empty until you equip the longsword (key 1).</button>
    <button class="sc" id="sbFireYard"><b>Fire bombs: practice yard</b>30 bombs, a quiet room: three sleeping skeletons to burn (a burn wakes them) and two small stacks of bombs on the floor to pick up (they join your stack). Switch the fire's look in the bar to compare.</button>
    <h2>Music</h2>
    <button class="sc" id="sbPack"><b>Pack fight</b>Five skeletons rush you at depth 3. Four or more pursuers start the combat track. Kill them all and it switches back at once; run until they lose interest and it holds 6 s.</button>
    <button class="sc" id="sbDemon"><b>Pit Demon level</b>Depth 8 with a Pit Demon boss, next to its boss room. The 2nd, 5th and 9th play of each track is the choir version (use Next loop to skip ahead); stepping into the boss room plays the choir combat track.</button>
    <button class="sc" id="sbNormal"><b>Normal game</b>The usual title screen; the Sandbox scenarios button at its bottom left brings this list back.</button></div>`;
  const bar = document.createElement('div'); bar.id = 'sbBar'; bar.hidden = true;
  bar.innerHTML = '<span id="sbInfo">–</span><span id="sbLooks" hidden>Fire look:' + [[1, 'Blaze'], [2, 'Ember bed'], [3, 'Oil pool']].map(([n, l]) => `<button data-look="${n}">${l}</button>`).join('') + '</span>'
    + '<button id="sbNext" title="Start the next play of this track now">Next loop</button><button id="sbBack">Scenarios</button>';
  let mode = 'music';   // what the bar shows: 'music' or 'fire'
  // on the normal title screen (after Normal game, or a real hero's death) a button brings the picker back
  const open = document.createElement('button'); open.id = 'sbOpen'; open.textContent = 'Sandbox scenarios'; open.hidden = true;
  open.onclick = () => { pick.hidden = false; };
  document.body.append(pick, bar, open);
  const mk = (base, rar, d) => { let it; for (let i = 0; i < 300; i++) { it = genItem(d, 0.3, base, rar, d + 2); if (it.rarity === rar) break; } return it; };
  function testHero(d, bombs = 0) {
    newGame(null);
    const h = G.hero; h.name = 'Tester'; h.saveId = 'sandbox'; h.lvl = 12; h.base.str += 35; h.base.dex += 25; h.base.vit += 45;
    G.depth = d; buildLevel(d);
    h.equip.weapon = mk('longsword', 'rare', d); h.equip.chest = mk('chainmail', 'rare', d); h.equip.head = mk('ironhelm', 'magic', d);
    h.hotkeys[0] = { type: 'item', id: h.equip.weapon.id };
    const st = h.inv.find(it => it && it.pot === 'health'); if (st) st.count = 12;
    if (bombs) {   // the bombs in the weapon slot, the longsword in the pack (key 1), the bombs on key 2
      h.inv[h.inv.indexOf(null)] = h.equip.weapon; h.equip.weapon = makeBombs(bombs); h.hotkeys[1] = { type: 'bomb' };
    }
    recalc(); h.hp = h.st.maxHp; refreshUI();
  }
  // the test hero is never saved (it would show up among the real heroes, which share the browser storage);
  // its death goes back to the scenario picker instead of the title screen
  const isTest = () => G && G.hero && G.hero.saveId === 'sandbox';
  const realSave = saveHero, realDeath = showDeath;
  saveHero = () => isTest() ? false : realSave();
  showDeath = () => { if (!isTest()) return realDeath(); G.running = false; pick.hidden = false; bar.hidden = true; };
  const floorAt = (x, y) => G.map.t[y * G.map.w + x] === T_FLOOR && !G.objects.some(o => o.x === x && o.y === y && !o.walk);
  function start(m = 'music') {
    mode = m; $('sbLooks').hidden = m !== 'fire'; $('sbNext').hidden = m !== 'music'; lookButtons();
    audio(); pick.hidden = true; bar.hidden = false;
    G.running = true; G.camSnap = true; G.deathShown = false;
    $('screen').classList.add('hidden'); $('equip').classList.add('hidden'); $('heroCfg').classList.add('hidden'); hideTip();
  }
  // monsters placed rd[0]-rd[1] tiles from the hero on free floor; chasing, or asleep (a calm that never ends:
  // they ignore the hero until a hit or a burn wakes them)
  function place(types, rd, asleep) {
    const h = G.hero, spots = [];
    for (let y = Math.floor(h.y) - 9; y <= h.y + 9; y++) for (let x = Math.floor(h.x) - 9; x <= h.x + 9; x++) {
      const dd = Math.hypot(x + 0.5 - h.x, y + 0.5 - h.y); if (dd >= rd[0] && dd <= rd[1] && floorAt(x, y) && los(h.x, h.y, x + 0.5, y + 0.5)) spots.push([x, y]); }
    for (const t of types) { if (!spots.length) break; const [x, y] = spots.splice(Math.floor(Math.random() * spots.length), 1)[0];
      const m = makeMonster(t, x + 0.5, y + 0.5, G.depth, false, false, true); G.monsters.push(m);
      if (asleep) m.calm = { walked: -1e9, t: 1e9 }; else chase(m); }
  }
  const clearAround = r => { const h = G.hero; G.monsters = G.monsters.filter(m => Math.hypot(m.x - h.x, m.y - h.y) > r); };
  $('sbFirePack').onclick = () => {
    testHero(3, 15); clearAround(18); place(['skeleton', 'skeleton', 'skeleton', 'skeleton', 'ghoul', 'ghoul', 'ghoul'], [5, 8], false);
    start('fire'); log('Test: seven monsters rush you. Right-click to throw a fire bomb.', BOMB.color);
  };
  $('sbFireLast').onclick = () => {
    testHero(3, 2); clearAround(18); place(['skeleton', 'skeleton', 'skeleton'], [5, 8], false);
    start('fire'); log('Test: two fire bombs left. Key 1 is your longsword.', BOMB.color);
  };
  $('sbFireYard').onclick = () => {
    testHero(2, 30); clearAround(22); place(['skeleton', 'skeleton', 'skeleton'], [4, 6.5], true);
    const h = G.hero; for (const n of [2, 3]) { const it = makeBombs(n); dropItem(it, h.x, h.y); }
    start('fire'); log('Test: a quiet room. The skeletons sleep until burned.', BOMB.color);
  };
  function lookButtons() { $('sbLooks').querySelectorAll('button').forEach(b => b.classList.toggle('on', +b.dataset.look === LOOK.fire)); }
  $('sbLooks').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; setLook('fire', +b.dataset.look); lookButtons(); b.blur(); });
  $('sbPack').onclick = () => {
    testHero(3); const h = G.hero;
    // clear the start room's surroundings, then five skeletons 4-6 tiles away, already pursuing
    G.monsters = G.monsters.filter(m => Math.hypot(m.x - h.x, m.y - h.y) > 18);
    const spots = []; for (let y = Math.floor(h.y) - 7; y <= h.y + 7; y++) for (let x = Math.floor(h.x) - 7; x <= h.x + 7; x++) {
      const dd = Math.hypot(x + 0.5 - h.x, y + 0.5 - h.y); if (dd >= 3.5 && dd <= 6.5 && floorAt(x, y)) spots.push([x, y]); }
    for (let i = 0; i < 5 && spots.length; i++) { const [x, y] = spots.splice(Math.floor(Math.random() * spots.length), 1)[0];
      const m = makeMonster('skeleton', x + 0.5, y + 0.5, 3, false, false, true); G.monsters.push(m); chase(m); }
    start(); log('Test: five skeletons are on you.', '#c9a45c');
  };
  $('sbDemon').onclick = () => {
    for (let i = 0; i < 300; i++) { testHero(8); if (G.map.boss && G.map.boss.type === 'demon' && G.map.bossRoom) break; }
    const h = G.hero, br = G.map.bossRoom; let best = null;
    // the nearest floor tile 3-5 tiles outside the boss room's edge
    for (let y = br.y - 6; y < br.y + br.h + 6; y++) for (let x = br.x - 6; x < br.x + br.w + 6; x++) {
      if (x >= br.x - 2 && x < br.x + br.w + 2 && y >= br.y - 2 && y < br.y + br.h + 2) continue;
      if (x < 0 || y < 0 || x >= G.map.w || y >= G.map.h || !floorAt(x, y)) continue;
      const out = Math.max(br.x - x, x - (br.x + br.w - 1), br.y - y, y - (br.y + br.h - 1)); if (out < 3 || out > 5) continue;
      if (!best || out < best[2]) best = [x, y, out]; }
    if (best) { h.x = best[0] + 0.5; h.y = best[1] + 0.5; h.path = []; }
    G.monsters = G.monsters.filter(m => m.bossRoom || m.boss || Math.hypot(m.x - h.x, m.y - h.y) > 10);
    start(); log('Test: a Pit Demon level. Its boss room is close by.', '#7fe08a');
  };
  $('sbNormal').onclick = () => { audio(); pick.hidden = true; bar.hidden = true; };
  $('sbBack').onclick = () => { G.running = false; pick.hidden = false; bar.hidden = true; };
  $('sbNext').onclick = () => { if (MUSIC.cur) MUSIC.cur.loopAt = 0; };
  setInterval(() => {
    open.hidden = !pick.hidden || $('screen').classList.contains('hidden');
    if (bar.hidden || !G) return;
    if (mode === 'fire') {
      const n = bombCount(), lit = G.fires.filter(f => f.t < f.dur).length, foes = G.monsters.filter(m => !m.dead && m.burning).length;
      $('sbInfo').innerHTML = `<span class="mood">Fire bombs ${n}</span>` + (isBomb(G.hero.equip.weapon) ? '' : ` · <span class="burn">${G.hero.equip.weapon ? G.hero.equip.weapon.name : 'bare hands'}</span>`)
        + ` · fires ${lit}` + (G.hero.burning ? ' · <span class="burn">you are burning</span>' : '') + (foes ? ` · ${foes} burning` : '');
      return;
    }
    const c = MUSIC.cur, n = G.monsters.filter(m => !m.dead && m.state === 'chase').length;
    const choir = c && /Choir/.test(c.name);
    $('sbInfo').innerHTML = (c ? `<span class="mood">${c.mood}</span> · <span class="${choir ? 'choir' : ''}">${choir ? 'choir' : 'instrumental'}</span>${c.n ? ' · play ' + c.n : ''}` : 'no music')
      + ` · pursuing ${n}` + (MUSIC.combatT > 0 && n === 0 ? ` · hold ${MUSIC.combatT.toFixed(1)} s` : '') + (demonLevel() ? ' · Pit Demon level' : '');
  }, 200);
  // the scenario buttons work once the game's own start-up (art loaded, first level built) is done
  const SC = ['sbFirePack', 'sbFireLast', 'sbFireYard', 'sbPack', 'sbDemon'];
  for (const id of SC) $(id).disabled = true;
  const ready = setInterval(() => { if (G && floorPat) { clearInterval(ready); for (const id of SC) $(id).disabled = false; $('sbFirePack').focus(); } }, 100);
})();
