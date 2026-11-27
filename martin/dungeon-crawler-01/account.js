// =====================================================================================
//  Accounts and server heroes (README, Saving: Accounts). A player signs in with a link sent by email (Supabase
//  Auth, signInWithOtp; the link brings them back to the game's page, where supabase-js picks up the session) and then keep heroes on the server as
//  well as in this browser: the table mdc1_heroes of the repo's shared Supabase project, one row per hero, each
//  player seeing only their own (row-level security on auth.uid(); supabase/migrations/…_create_mdc1_heroes.sql).
//  Or, for testing, with a PIN (two uppercase letters and four digits, e.g. initials + digits, JS4821): no account, no email;
//  the heroes of that PIN live in the table mdc1_pin_heroes, reached only through database functions that touch the
//  rows of the PIN they are given (…_create_mdc1_pin_heroes.sql). Weak by design (guessable, shared by whoever picks
//  the same PIN); the sign-in box says so. The PIN is kept in this browser until signing out, or until the player
//  comes back more than PIN_IDLE after last playing (then it is forgotten, silently).
//  A server hero's id is 's:' + its row id; a local hero's id is 'h…' (index.html, readSave). Everything here is
//  best-effort: without a connection the game goes on with its local heroes.
//  Loaded before the game's main script, after net.js (whose netLib loads supabase-js once for both).
// =====================================================================================
const ACC = { sb: null, user: null, heroes: {}, loaded: false, ready: false, email: '', err: '' };
const ACC_TABLE = 'mdc1_heroes';
const isServerId = id => typeof id === 'string' && id.startsWith('s:');
const accName = () => !ACC.user ? '' : ACC.user.pin ? ACC.user.pin.slice(0, 2) + ' (PIN)' : ACC.user.email || 'signed in';
const PIN_KEY = 'crypt-of-endless-night.pin', PIN_IDLE = 48 * 3600 * 1000, PIN_RE = /^[A-Z]{2}[0-9]{4}$/;
const pinRead = () => { try { return JSON.parse(localStorage.getItem(PIN_KEY)) || null; } catch (e) { return null; } };
const pinWrite = v => { try { if (v) localStorage.setItem(PIN_KEY, JSON.stringify(v)); else localStorage.removeItem(PIN_KEY); } catch (e) {} };
// playing with a PIN: note the time (the 48 h are counted from the last time the game was played)
function accTouch() { if (ACC.user && ACC.user.pin) pinWrite({ pin: ACC.user.pin, last: Date.now() }); }

// Load supabase-js and follow the sign-in state: a stored session comes back on load (INITIAL_SESSION), coming back
// from the email's link signs in (SIGNED_IN), signing out clears the server heroes. Their list is (re)loaded only when
// the user actually changes (a token refresh fires this too).
async function accInit() {
  const p = pinRead();   // a PIN kept from before: forgotten when the last play was more than PIN_IDLE ago
  if (p && (!PIN_RE.test(p.pin) || !(Date.now() - (p.last || 0) <= PIN_IDLE))) pinWrite(null);
  const sb = await netLib(); ACC.ready = true;
  if (!sb) { ACC.err = 'offline'; accChanged(); return; }
  ACC.sb = sb;
  const kept = pinRead(); if (kept) { ACC.user = { id: 'pin', pin: kept.pin }; accLoad(); }
  sb.auth.onAuthStateChange((_ev, session) => {
    const u = session && session.user;
    if (u) { const changed = !ACC.user || ACC.user.id !== u.id; if (ACC.user && ACC.user.pin) pinWrite(null); ACC.user = u; if (changed) accLoad(); }
    else if (!(ACC.user && ACC.user.pin)) { ACC.user = null; ACC.heroes = {}; ACC.loaded = false; accChanged(); }   // (a PIN stays)
  });
  accChanged();
}
// Use a PIN: its heroes are loaded (a new PIN simply has none yet); an email session is ended first
async function accUsePin(pin) {
  pin = (pin || '').trim().toUpperCase();
  if (!PIN_RE.test(pin)) return 'A PIN is two letters and four digits, like JS4821.';
  if (!ACC.sb) return 'No connection to the server.';
  if (ACC.user && !ACC.user.pin) try { await ACC.sb.auth.signOut(); } catch (e) {}
  ACC.user = { id: 'pin', pin }; accTouch(); await accLoad();
  return ACC.err ? 'The server could not be reached: ' + ACC.err : '';
}
function accChanged() { if (typeof titleRefresh === 'function') titleRefresh(); }

// Send a sign-in link to an email address; it returns to this page (the address must be among the project's allowed
// redirect URLs: Supabase dashboard, Authentication, URL Configuration)
async function accSendLink(email) {
  if (!ACC.sb) return 'No connection to the server.';
  const { error } = await ACC.sb.auth.signInWithOtp({ email, options: { shouldCreateUser: true, emailRedirectTo: location.origin + location.pathname } });
  if (error) return error.message || 'The link could not be sent.';
  ACC.email = email; return '';
}
async function accSignOut() {
  if (ACC.user && ACC.user.pin) { pinWrite(null); ACC.user = null; ACC.heroes = {}; ACC.loaded = false; accChanged(); return; }
  if (ACC.sb) try { await ACC.sb.auth.signOut(); } catch (e) {}
}

// The server heroes, as save entries ({ id, name, depth, lvl, saved, hero }) keyed by id, like readSave().heroes
const rowEntry = r => ({ id: 's:' + r.id, name: r.name, depth: r.depth, lvl: r.lvl, saved: Date.parse(r.saved_at) || 0, hero: r.hero });
async function accLoad() {
  ACC.loaded = false; ACC.err = ''; accChanged();
  const pin = ACC.user && ACC.user.pin;
  const { data, error } = pin ? await ACC.sb.rpc('mdc1_pin_list', { p_pin: pin }) : await ACC.sb.from(ACC_TABLE).select('id,name,lvl,depth,hero,saved_at');
  if (ACC.user && ACC.user.pin !== pin) return;   // (signed out or switched meanwhile)
  if (error) { ACC.err = error.message || 'The server heroes could not be loaded.'; console.warn('[acc] load', error); }
  ACC.heroes = {}; for (const r of data || []) { const e = rowEntry(r); ACC.heroes[e.id] = e; }
  ACC.loaded = true; accChanged();
}
// Write one (new or changed) server hero: kept here at once, sent to the server; resolves true when it is stored
async function accPut(e) {
  ACC.heroes[e.id] = e;
  if (!ACC.sb || !ACC.user) return false;
  const saved_at = new Date(e.saved || Date.now()).toISOString();
  const { error } = ACC.user.pin
    ? await ACC.sb.rpc('mdc1_pin_save', { p_pin: ACC.user.pin, p_id: e.id.slice(2), p_name: e.name, p_lvl: e.lvl, p_depth: e.depth, p_hero: e.hero, p_saved: saved_at })
    : await ACC.sb.from(ACC_TABLE).upsert({ id: e.id.slice(2), name: e.name, lvl: e.lvl, depth: e.depth, hero: e.hero, saved_at });
  accTouch();
  if (error) { console.warn('[acc] save', error); return false; }
  return true;
}
async function accDel(id) {
  delete ACC.heroes[id];
  if (!ACC.sb || !ACC.user) return false;
  const { error } = ACC.user.pin ? await ACC.sb.rpc('mdc1_pin_delete', { p_pin: ACC.user.pin, p_id: id.slice(2) })
    : await ACC.sb.from(ACC_TABLE).delete().eq('id', id.slice(2));
  if (error) { console.warn('[acc] delete', error); return false; }
  return true;
}
const newServerId = () => 's:' + (crypto.randomUUID ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => { const r = Math.random() * 16 | 0; return (c === 'x' ? r : r & 3 | 8).toString(16); }));
// while playing with a PIN, the time of the last play is kept up to date (once a minute)
setInterval(() => { if (typeof G !== 'undefined' && G && G.running) accTouch(); }, 60000);
