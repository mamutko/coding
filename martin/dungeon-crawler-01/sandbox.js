// Sandbox: test scenarios for the game in index.html (see README, Sandbox). Loaded by index.html only when the
// address has ?sandbox, and inlined into the Claude artifact by the artifact-sandbox skill's build.py. It runs after the game's
// script and uses its globals; it changes nothing in the game itself. Instead of the title screen it shows a
// scenario picker; a scenario makes a strong test hero (never saved) and drops it into a prepared situation.
(() => {
  const css = document.createElement('style');
  css.textContent = `
  #sbPick { position: fixed; inset: 0; z-index: 60; display: flex; background: rgba(5,2,4,0.82);   /* the box centres with margin: auto, so a tall list scrolls from its top */
    padding: 16px max(16px, env(safe-area-inset-left, 0px)); overflow-y: auto; }
  #sbPick .box { margin: auto; max-width: 560px; width: 100%; border: 1px solid #5a4528; background: #120c0e; padding: 22px; box-shadow: 0 0 40px #000; }
  #sbPick h1 { font-family: Cinzel, serif; color: #c9a45c; font-size: 22px; letter-spacing: 2px; margin: 0 0 6px; text-wrap: balance; }
  #sbPick p { color: #b3aba0; font: 15px/1.45 'IM Fell English', Georgia, serif; margin: 0 0 14px; }
  #sbPick p.status { color: #c9a45c; font-size: 14px; }
  #sbPick p.status.err { color: #e07a6a; }
  #sbPick p.status[hidden] { display: none; }
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
  #sbKeepers { display: flex; gap: 4px; align-items: center; } #sbKeepers[hidden] { display: none !important; }
  #sbLookPick { display: flex; gap: 6px; align-items: center; } #sbLookPick[hidden] { display: none !important; }
  #sbBar select { background: #1c1316; border: 1px solid #5a4528; color: #e8dcc4; font: 13px Georgia, serif; padding: 3px 6px; }
  .sbSounds { display: flex; gap: 4px; align-items: center; } .sbSounds[hidden] { display: none !important; }
  #sbBar .sbSounds button.on { border-color: #8fb6d0; color: #fff; background: #13263a; }
  #sbBar #sbKeepers button.on { border-color: #e3c060; color: #fff; background: #3a2c12; }
  #sbBar #sbLooks button.on { border-color: #e8893a; color: #fff; background: #3a1f12; }
  #sbPick h2 { font-family: Cinzel, serif; color: #8c7650; font-size: 13px; letter-spacing: 2px; margin: 16px 0 8px; }
  #sbBar button { background: #1c1316; border: 1px solid #5a4528; color: #e8dcc4; font: 12px Georgia, serif; padding: 3px 8px; cursor: pointer; }
  #sbBar button:hover { border-color: #c9a45c; }
  body.narrow #sbBar { top: auto; bottom: calc(150px + env(safe-area-inset-bottom, 0px)); font-size: 12px; }
  body.narrow #sbBar.top { top: calc(8px + env(safe-area-inset-top, 0px)); bottom: auto; z-index: 56; }   /* the character viewer: out of the hero's way */`;
  document.head.appendChild(css);
  const pick = document.createElement('div'); pick.id = 'sbPick'; pick.innerHTML = `<div class="box">
    <h1>Crypt Sandbox</h1>
    <p>The current game (v${VERSION}) with a strong test hero (never saved), dropped straight into a situation. Sound starts when you pick one. A bar at the top shows what the scenario is about.</p>
    <p id="sbStatus" class="status">Loading the game…</p>
    <h2>Surface</h2>
    <button class="sc" id="sbSurface"><b>The surface</b>A new level-1 hero at depth 0, a few steps from the crypt's entrance. Walk the endless woods around it (the land is made as you go), then click the dark doorway to go down to depth 1.</button>
    <h2>Fire bombs</h2>
    <button class="sc" id="sbFirePack"><b>Fire bombs: pack fight</b>Depth 3, 15 fire bombs equipped, four skeletons and three ghouls rushing in. Right-click to throw at a monster or a spot (up to 7 tiles). Key 1 is your longsword, 2 the bombs. Mind the flames: they burn you too.</button>
    <button class="sc" id="sbFireLast"><b>Fire bombs: the last two</b>Only two bombs equipped and three skeletons coming. After the second throw your hands are empty until you equip the longsword (key 1).</button>
    <button class="sc" id="sbFireYard"><b>Fire bombs: practice yard</b>30 bombs, a quiet room: three sleeping skeletons to burn (a burn wakes them) and two small stacks of bombs on the floor to pick up (they join your stack). Switch the fire's look in the bar to compare.</button>
    <h2>Market</h2>
    <button class="sc" id="sbMarket"><b>Keeper of the Crypt</b>Depth 6, in a keeper's furnished room, a few steps from the keeper (who walks up to you), with 3000 gold and things to sell or trade (a helm, an axe, a magic ring, potions, fire bombs). Click the keeper to open the market. Switch between the four keepers in the bar.</button>
    <h2>Kiting</h2>
    <button class="sc" id="sbKite"><b>Kiting with a bow</b>Depth 7, a common hunting bow, in the middle of the level's big room, grown to 1.5 times its size (about 20–24 tiles a side): four cave spiders and two Pit Demons sleep around you (only a hit wakes them). Shoot one from more than 2.5 tiles away and it charges for 2 s, trailing dust. Key 1 is your longsword.</button>
    <h2>Characters</h2>
    <button class="sc" id="sbLooks2"><b>Character viewer</b>Walk around an empty big room as any character that has a sprite sheet: the hero, the monsters and the Keepers of the Crypt. Pick the look in the bar; click to walk, and watch every direction.</button>
    <h2>Lakes</h2>
    <button class="sc" id="sbLake"><b>The underground lake</b>Depth 8, on the shore of the huge lake room. The lake reaches out of sight; its far shores are the room's walls. Wraiths hover over the water in a loose group (only they can cross it). You carry 15 fire bombs (key 4): one that lands in the water sinks, but fire on the shore spreads its burning oil over the water. Drops fall from the ceiling now and then; watch the reflections ripple.</button>
    <h2>Music</h2>
    <button class="sc" id="sbPack"><b>Pack fight</b>Five skeletons rush you at depth 3. Four or more pursuers start the combat track. Kill them all and it switches back at once; run until they lose interest and it holds 6 s.</button>
    <button class="sc" id="sbDemon"><b>Pit Demon level</b>Depth 8 with a Pit Demon boss, next to its boss room. The 2nd, 5th and 9th play of each track is the choir version (use Next loop to skip ahead); stepping into the boss room plays the choir combat track.</button>
    <button class="sc" id="sbNormal"><b>Normal game</b>The usual title screen; its Scenarios button at the bottom left brings this list back.</button></div>`;
  const bar = document.createElement('div'); bar.id = 'sbBar'; bar.hidden = true;
  bar.innerHTML = '<span id="sbInfo">–</span><span id="sbKeepers" hidden>Keeper:' + [1, 2, 3, 4].map(n => `<button data-keeper="${n}">${KEEPERS[n].name.split(' ')[0]}</button>`).join('') + '</span><span id="sbLooks" hidden>Fire look:' + [[1, 'Blaze'], [2, 'Ember bed'], [3, 'Oil pool']].map(([n, l]) => `<button data-look="${n}">${l}</button>`).join('') + '</span>'
    + '<span id="sbLookPick" hidden>Look: <select id="sbLookSel"></select></span>'
    + '<span id="sbDrips" class="sbSounds" hidden>Drip:' + [[1, 'Plink'], [2, 'Hollow'], [3, 'Glassy'], [4, 'Echo']].map(([n, l]) => `<button data-drip="${n}">${l}</button>`).join('') + '</span>'
    + '<span id="sbSplash" class="sbSounds" hidden>Bomb splash:' + [[1, 'Plunge'], [2, 'Heavy'], [3, 'Gurgle']].map(([n, l]) => `<button data-splash="${n}">${l}</button>`).join('') + '</span>'
    + '<button id="sbNext" title="Start the next play of this track now">Next loop</button><button id="sbBack">Scenarios</button>';
  let mode = 'music';   // what the bar shows: 'music' or 'fire'
  // on the normal title screen (after Normal game, or a real hero's death) its Scenarios button (index.html) brings
  // the picker back through this
  window.sandboxOpen = () => { pick.hidden = false; };
  document.body.append(pick, bar);
  const mk = (base, rar, d) => { let it; for (let i = 0; i < 300; i++) { it = genItem(d, 0.3, base, rar, d + 2); if (it.rarity === rar) break; } return it; };
  function testHero(d, bombs = 0) {
    newGame(null);
    const h = G.hero; h.name = 'Tester'; h.saveId = 'sandbox'; h.lvl = 12; h.base.str += 35; h.base.dex += 25; h.base.vit += 45;
    G.depth = d; buildLevel(d); logEl.innerHTML = '';   // newGame logged depth 1's name
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
    mode = m; $('sbLooks').hidden = m !== 'fire'; $('sbKeepers').hidden = m !== 'market'; $('sbDrips').hidden = $('sbSplash').hidden = m !== 'lake'; soundButtons(); $('sbLookPick').hidden = m !== 'looks'; bar.classList.toggle('top', m === 'looks'); $('sbNext').hidden = m !== 'music' && m !== 'surface'; lookButtons();
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
  // Sandbox only: grow a room to `factor` times its area (sides × √factor, centred, kept inside the map). Everything
  // in the new rectangle becomes floor (walls, doors and other rooms it overlaps open up; door objects there are
  // removed, other props stay), and the floor's new edge gets walls, as buildLevel makes them.
  function enlargeRoom(room, factor) {
    const m = G.map, k = Math.sqrt(factor), nw = Math.min(m.w - 6, Math.round(room.w * k)), nh = Math.min(m.h - 6, Math.round(room.h * k));
    const x0 = Math.max(3, Math.min(m.w - 3 - nw, room.cx - (nw >> 1))), y0 = Math.max(3, Math.min(m.h - 3 - nh, room.cy - (nh >> 1)));
    const inR = (x, y) => x >= x0 && x < x0 + nw && y >= y0 && y < y0 + nh;
    G.objects = G.objects.filter(o => !(o.type === 'door' && inR(o.x, o.y)));
    for (let y = y0; y < y0 + nh; y++) for (let x = x0; x < x0 + nw; x++) { const i = y * m.w + x; if (m.t[i] !== T_FLOOR) { m.t[i] = T_FLOOR; m.block[i] = 0; } }
    for (let y = y0 - 1; y <= y0 + nh; y++) for (let x = x0 - 1; x <= x0 + nw; x++) {
      const i = y * m.w + x; if (m.t[i] !== T_VOID) continue;
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) if (m.t[(y + dy) * m.w + x + dx] === T_FLOOR) m.t[i] = T_WALL;
    }
    Object.assign(room, { x: x0, y: y0, w: nw, h: nh, cx: x0 + (nw >> 1), cy: y0 + (nh >> 1) });
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
  // the lake scenario's sound pickers: a click picks a version (SOUND_LOOK, for this page's session) and plays it
  function soundButtons() {
    $('sbDrips').querySelectorAll('button').forEach(b => b.classList.toggle('on', +b.dataset.drip === SOUND_LOOK.drip));
    $('sbSplash').querySelectorAll('button').forEach(b => b.classList.toggle('on', +b.dataset.splash === SOUND_LOOK.splash));
  }
  $('sbDrips').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; SOUND_LOOK.drip = +b.dataset.drip; soundButtons(); sfx('drip'); b.blur(); });
  $('sbSplash').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; SOUND_LOOK.splash = +b.dataset.splash; soundButtons(); sfx('plunge'); b.blur(); });
  function lookButtons() { $('sbLooks').querySelectorAll('button').forEach(b => b.classList.toggle('on', +b.dataset.look === LOOK.fire)); }
  $('sbLooks').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; setLook('fire', +b.dataset.look); lookButtons(); b.blur(); });
  $('sbSurface').onclick = () => {
    newGame(null); G.hero.name = 'Tester'; G.hero.saveId = 'sandbox'; refreshUI();
    start('surface'); log('Test: the surface. The crypt is right ahead.', '#c9a45c');
  };
  $('sbMarket').onclick = () => {
    for (let i = 0; i < 50; i++) { testHero(6); if (G.objects.some(o => o.type === 'keeper')) break; }
    const h = G.hero, k = G.objects.find(o => o.type === 'keeper');
    h.gold = 3000; h.hp = Math.round(h.st.maxHp * 0.6);
    for (const it of [genItem(4, 0, 'ironhelm', 'common', 4), genItem(5, 0, 'battleaxe', 'common', 5), genItem(6, 0, 'rubyring', 'magic', 6), makeBombs(3)])
      h.inv[h.inv.indexOf(null)] = it;
    // stand in the keeper's room about 4.5 tiles from it (or as near as there is floor), so it walks up to the hero;
    // the keeper's room cleared of anything else
    const kr = k.room; let best = null; for (let y = kr.y; y < kr.y + kr.h; y++) for (let x = kr.x; x < kr.x + kr.w; x++) {
      if (!floorAt(x, y) || G.map.block[y * G.map.w + x]) continue; const dd = Math.abs(Math.hypot(x - k.x, y - k.y) - 4.5); if (!best || dd < best[2]) best = [x, y, dd]; }
    if (best) { h.x = best[0] + 0.5; h.y = best[1] + 0.5; h.path = []; }
    G.monsters = G.monsters.filter(m => Math.hypot(m.x - h.x, m.y - h.y) > 16); refreshUI();
    start('market'); keeperButtons(); log('Test: a Keeper of the Crypt. Click it to trade.', '#e3c060');
  };
  function keeperButtons() { const k = G.objects.find(o => o.type === 'keeper'); $('sbKeepers').querySelectorAll('button').forEach(b => b.classList.toggle('on', k && +b.dataset.keeper === k.look)); }
  $('sbKeepers').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; const k = G.objects.find(o => o.type === 'keeper');
    if (k) { k.look = +b.dataset.keeper; if (marketOpen()) openMarket(k); } keeperButtons(); b.blur(); });
  $('sbKite').onclick = () => {
    for (let i = 0; i < 100; i++) { testHero(7); if (G.map.rooms.some(r => r.big === 'horde')) break; }
    const h = G.hero, bow = genItem(7, 0, 'huntingbow', 'common', 7), room = G.map.rooms.find(r => r.big === 'horde') || G.map.rooms[1];
    enlargeRoom(room, 1.5);   // the big room (16-20) to about 20-24 tiles a side
    h.inv[h.inv.indexOf(null)] = h.equip.weapon; h.equip.weapon = bow; h.hotkeys[1] = { type: 'item', id: bow.id }; recalc(); refreshUI();
    // the hero in the middle of the big room, which holds only sleeping spiders and Pit Demons
    let best = null; for (let y = room.y; y < room.y + room.h; y++) for (let x = room.x; x < room.x + room.w; x++)
      if (floorAt(x, y)) { const dd = Math.hypot(x - room.cx, y - room.cy); if (!best || dd < best[2]) best = [x, y, dd]; }
    h.x = best[0] + 0.5; h.y = best[1] + 0.5; h.path = []; G.camSnap = true;
    const inRoom = m => m.x >= room.x - 1 && m.x < room.x + room.w + 1 && m.y >= room.y - 1 && m.y < room.y + room.h + 1;
    G.monsters = G.monsters.filter(m => !inRoom(m) && Math.hypot(m.x - h.x, m.y - h.y) > 22);
    const spots = []; for (let y = room.y; y < room.y + room.h; y++) for (let x = room.x; x < room.x + room.w; x++)
      if (floorAt(x, y) && Math.hypot(x + 0.5 - h.x, y + 0.5 - h.y) >= 5) spots.push([x, y]);
    for (const t of ['spider', 'spider', 'spider', 'spider', 'demon', 'demon']) { if (!spots.length) break;
      const [x, y] = spots.splice(Math.floor(Math.random() * spots.length), 1)[0];
      const m = makeMonster(t, x + 0.5, y + 0.5, 7, false, false, true); m.calm = { walked: -1e9, t: 1e9 }; G.monsters.push(m); }
    start('kite'); log('Test: the big room. Shoot a sleeper from afar and watch it charge.', '#c9a45c');
  };
  $('sbLake').onclick = () => {
    testHero(LAKE_AT); const h = G.hero, r = G.map.lakeRoom, m = G.map;
    // the hero on the dry shore where it faces the middle of the lake: the shore tile nearest the room's diagonal,
    // one tile back from the water; other monsters within 14 tiles (not the lake's wraiths) are removed
    let best = null;
    for (let y = r.y; y < r.y + r.h; y++) for (let x = r.x; x < r.x + r.w; x++) {
      if (!floorAt(x, y) || !floorAt(x + 1, y + 1) || m.block[(y + 1) * m.w + x + 1] || m.at(x - 1, y - 1) !== T_WATER) continue;
      const dd = Math.abs((x - r.x) - (y - r.y)); if (!best || dd < best[2]) best = [x + 1, y + 1, dd]; }
    if (best) { h.x = best[0] + 0.5; h.y = best[1] + 0.5; h.path = []; h.dir = 5; }
    h.inv[h.inv.indexOf(null)] = makeBombs(15); h.hotkeys[3] = { type: 'bomb' }; refreshUI();   // 15 fire bombs in the pack, on key 4
    G.monsters = G.monsters.filter(mo => mo.lake || Math.hypot(mo.x - h.x, mo.y - h.y) > 14);
    start('lake'); log('Test: the underground lake. Wraiths hover over the water.', '#9fb6c8');
  };
  // Character viewer: every sheet in META.characters, named; the hero takes the picked look (G.hero.look, see
  // heroLook in the game), in an empty big room
  const lookName = k => k === 'hero' ? 'The hero (knight)' : MON[k] ? MON[k].name : /^keeper\d$/.test(k) ? KEEPERS[+k.slice(6)].name : CAST_NAMES[k] || k;
  function fillLooks() {
    const keys = Object.keys(META.characters), grp = k => k === 'hero' ? 'Hero' : MON[k] ? 'Monsters' : /^keeper\d$/.test(k) ? 'Keepers of the Crypt' : 'Villagers and nobles';
    const sel = $('sbLookSel'); sel.innerHTML = [...new Set(keys.map(grp))].map(g => `<optgroup label="${g}">` + keys.filter(k => grp(k) === g).map(k => `<option value="${k}">${lookName(k)}</option>`).join('') + '</optgroup>').join('');
    sel.value = heroLook(G.hero);
  }
  $('sbLookSel').addEventListener('change', e => { const k = e.target.value; G.hero.look = k; loadCast(k); e.target.blur(); });   // a cast sheet loads on first pick
  $('sbLooks2').onclick = () => {
    for (let i = 0; i < 100; i++) { testHero(3); if (G.map.rooms.some(r => r.big === 'horde')) break; }
    const h = G.hero, room = G.map.rooms.find(r => r.big === 'horde') || G.map.rooms[1];
    let best = null; for (let y = room.y; y < room.y + room.h; y++) for (let x = room.x; x < room.x + room.w; x++)
      if (floorAt(x, y)) { const dd = Math.hypot(x - room.cx, y - room.cy); if (!best || dd < best[2]) best = [x, y, dd]; }
    h.x = best[0] + 0.5; h.y = best[1] + 0.5; h.path = []; G.camSnap = true; G.monsters = [];
    start('looks'); fillLooks(); log('Test: the character viewer. Pick a look in the bar and walk around.', '#c9a45c');
  };
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
  $('sbNormal').onclick = () => { audio(); setLook('fire', 1); SOUND_LOOK.drip = SOUND_LOOK.splash = 1; if (G && G.hero) G.hero.look = null; pick.hidden = true; bar.hidden = true; };   // the normal game: the settled look (Blaze)
  $('sbBack').onclick = () => { G.running = false; pick.hidden = false; bar.hidden = true; };
  $('sbNext').onclick = () => { if (MUSIC.cur) MUSIC.cur.loopAt = 0; };
  setInterval(() => {
    if (bar.hidden || !G) return;
    if (mode === 'surface') {
      const h = G.hero, sv = G.surf, c = MUSIC.cur, tune = c ? ` · music ${MUSIC_FILES[c.name]}${c.n ? ' (play ' + c.n + ')' : ''}` : ' · no music';
      $('sbInfo').innerHTML = (sv && G.map.surface ? `<span class="mood">The surface</span> · world tile ${Math.floor(h.x + sv.ox)}, ${Math.floor(h.y + sv.oy)} · super tile ${sv.cx}, ${sv.cy}` : `<span class="mood">${depthName(G.depth)}</span> · depth ${G.depth}`) + tune;
      return;
    }
    if (mode === 'market') {
      const k = G.objects.find(o => o.type === 'keeper');
      $('sbInfo').innerHTML = `<span class="mood">${k ? KEEPERS[k.look].name : 'no keeper'}</span> · ${G.hero.gold} gold · life ${Math.ceil(G.hero.hp)} / ${G.hero.st.maxHp}` + (marketOpen() ? ' · trading' : '');
      return;
    }
    if (mode === 'kite') {
      const h = G.hero, w = weaponOf(h), near = G.monsters.filter(m => !m.dead && m.state === 'chase');
      const ch = near.filter(m => m.chargeT > 0).map(m => MON[m.type].name);
      const gap = near.length ? Math.min(...near.map(m => Math.hypot(m.x - h.x, m.y - h.y))).toFixed(1) : '–';
      $('sbInfo').innerHTML = `<span class="mood">${w.name}</span>` + (w.kind === 'bow' ? ` · draw ${drawTime(w).toFixed(2)} s` : '')
        + (h.draw ? ' · <span class="choir">drawing</span>' : '') + ` · nearest pursuer ${gap} tiles`
        + (ch.length ? ` · <span class="burn">charging: ${ch.join(', ')}</span>` : '');
      return;
    }
    if (mode === 'looks') {
      const h = G.hero, k = heroLook(h), md = META.characters[k];
      $('sbInfo').innerHTML = `<span class="mood">${lookName(k)}</span> · ${md.frames} frames × 8 directions · row ${['S', 'SW', 'W', 'NW', 'N', 'NE', 'E', 'SE'][h.dir]}`
        + ` · frame ${h.moving ? Math.floor(h.anim) % md.frames : (md.idle || 0) + ' (idle)'} · scale ${lookScale(k)}`;
      return;
    }
    if (mode === 'lake') {
      const h = G.hero, w = G.monsters.filter(mo => mo.lake && !mo.dead), pur = w.filter(mo => mo.state === 'chase').length;
      const near = w.length ? Math.min(...w.map(mo => Math.hypot(mo.x - h.x, mo.y - h.y))).toFixed(1) : '–';
      $('sbInfo').innerHTML = `<span class="mood">The lake</span> · wraiths ${w.length}` + (pur ? ` · <span class="burn">${pur} pursuing</span>` : '') + ` · nearest ${near} tiles`
        + ` · ripples: rings${REFRACT ? ' + refraction' : ' (refraction off: under 28 fps)'}` + (PERF.fps ? ` · ${PERF.fps} fps` : '');
      return;
    }
    if (mode === 'fire') {
      const n = bombCount(), lit = G.fires.filter(f => f.t < f.dur).length, foes = G.monsters.filter(m => !m.dead && m.burning).length;
      $('sbInfo').innerHTML = `<span class="mood">Fire bombs ${n}</span>` + (isBomb(G.hero.equip.weapon) ? '' : ` · <span class="burn">${G.hero.equip.weapon ? G.hero.equip.weapon.name : 'bare hands'}</span>`)
        + ` · fires ${lit}` + (G.hero.burning ? ` · <span class="burn">you are burning${G.hero.inFire ? ' (in the fire)' : ' (' + G.hero.burnLeft.toFixed(1) + ' s)'}</span>` : '') + (foes ? ` · ${foes} burning` : '');
      return;
    }
    const c = MUSIC.cur, n = G.monsters.filter(m => !m.dead && m.state === 'chase').length;
    const choir = c && /Choir/.test(c.name);
    $('sbInfo').innerHTML = (c ? `<span class="mood">${c.mood}</span> · <span class="${choir ? 'choir' : ''}">${choir ? 'choir' : 'instrumental'}</span>${c.n ? ' · play ' + c.n : ''}` : 'no music')
      + ` · pursuing ${n}` + (MUSIC.combatT > 0 && n === 0 ? ` · hold ${MUSIC.combatT.toFixed(1)} s` : '') + (demonLevel() ? ' · Pit Demon level' : '');
  }, 200);
  // the scenario buttons work once the game's own start-up (art loaded, first level built) is done
  const SC = ['sbLooks2', 'sbSurface', 'sbFirePack', 'sbFireLast', 'sbFireYard', 'sbMarket', 'sbKite', 'sbLake', 'sbPack', 'sbDemon'];
  for (const id of SC) $(id).disabled = true;
  // until then the picker says how far loading got, or why start-up failed (the title screen's start button shows
  // the same, but the picker covers it); errors thrown later are listed there too
  const status = $('sbStatus'), errs = []; let probe = null;
  addEventListener('error', e => { errs.push(e.message || String(e.error || e)); });
  addEventListener('unhandledrejection', e => { errs.push('unhandled: ' + (e.reason && e.reason.message || e.reason)); });
  const ready = setInterval(() => {
    const sb = $('startBtn').textContent, failed = /fail/i.test(sb);
    if (G && floorPat && !failed) { clearInterval(ready); for (const id of SC) $(id).disabled = false; $('sbFirePack').focus(); }
    status.classList.toggle('err', failed || errs.length > 0);
    if (failed && probe === null) {   // ask the server directly what it answers for that file, to show why
      probe = ''; const url = (sb.match(/Failed to load (\S+)/) || [])[1];
      if (url) fetch(url, { cache: 'no-store' }).then(r => { probe = ` The server answered HTTP ${r.status}${r.statusText ? ' ' + r.statusText : ''}.`; })
        .catch(e => { probe = ` Fetching it fails too: ${e.message || e}.`; });
    }
    status.textContent = failed ? sb + ' — the scenarios stay off.' + (probe || '') : G && floorPat ? (errs.length ? 'Errors: ' + errs.slice(-3).join(' · ') : '')
      : `Loading the game: ${LOADED.n} / ${LOADED.of} images…` + (LOADED.retries ? ` (${LOADED.retries} retried)` : '') + (errs.length ? ' Errors: ' + errs.slice(-3).join(' · ') : '');
    status.hidden = !status.textContent;
    if (G && floorPat && !failed && !errs.length) status.hidden = true;
  }, 100);
  setInterval(() => { if (errs.length && G && floorPat) { status.hidden = false; status.classList.add('err'); status.textContent = 'Errors: ' + errs.slice(-3).join(' · '); } }, 1000);
})();
