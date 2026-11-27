// =====================================================================================
//  Accounts and server heroes (README, Heroes and saving: Accounts). A player can sign in with an email code
//  (Supabase Auth, signInWithOtp + verifyOtp; the email's link signs in too) and then keep heroes on the server as
//  well as in this browser: the table mdc1_heroes of the repo's shared Supabase project, one row per hero, each
//  player seeing only their own (row-level security on auth.uid(); supabase/migrations/…_create_mdc1_heroes.sql).
//  A server hero's id is 's:' + its row id; a local hero's id is 'h…' (index.html, readSave). Everything here is
//  best-effort: without a connection the game goes on with its local heroes.
//  Loaded before the game's main script, after net.js (whose netLib loads supabase-js once for both).
// =====================================================================================
const ACC = { sb: null, user: null, heroes: {}, loaded: false, ready: false, email: '', err: '' };
const ACC_TABLE = 'mdc1_heroes';
const isServerId = id => typeof id === 'string' && id.startsWith('s:');
const accName = () => ACC.user ? ACC.user.email || 'signed in' : '';

// Load supabase-js and follow the sign-in state: a stored session comes back on load (INITIAL_SESSION), a code or
// the email's link signs in (SIGNED_IN), signing out clears the server heroes. Their list is (re)loaded only when
// the user actually changes (a token refresh fires this too).
async function accInit() {
  const sb = await netLib(); ACC.ready = true;
  if (!sb) { ACC.err = 'offline'; accChanged(); return; }
  ACC.sb = sb;
  sb.auth.onAuthStateChange((_ev, session) => {
    const u = session && session.user;
    if (u) { const changed = !ACC.user || ACC.user.id !== u.id; ACC.user = u; if (changed) accLoad(); }
    else { ACC.user = null; ACC.heroes = {}; ACC.loaded = false; accChanged(); }
  });
  accChanged();
}
function accChanged() { if (typeof titleRefresh === 'function') titleRefresh(); }

// Send the code (and link) to an email address; then check the code typed in.
async function accSendCode(email) {
  if (!ACC.sb) return 'No connection to the server.';
  const { error } = await ACC.sb.auth.signInWithOtp({ email, options: { shouldCreateUser: true, emailRedirectTo: location.origin + location.pathname } });
  if (error) return error.message || 'The code could not be sent.';
  ACC.email = email; return '';
}
async function accVerify(email, code) {
  if (!ACC.sb) return 'No connection to the server.';
  const { error } = await ACC.sb.auth.verifyOtp({ email, token: code.trim(), type: 'email' });
  return error ? (error.message || 'That code did not work.') : '';
}
async function accSignOut() { if (ACC.sb) try { await ACC.sb.auth.signOut(); } catch (e) {} }

// The server heroes, as save entries ({ id, name, depth, lvl, saved, hero }) keyed by id, like readSave().heroes
const rowEntry = r => ({ id: 's:' + r.id, name: r.name, depth: r.depth, lvl: r.lvl, saved: Date.parse(r.saved_at) || 0, hero: r.hero });
async function accLoad() {
  ACC.loaded = false; ACC.err = ''; accChanged();
  const { data, error } = await ACC.sb.from(ACC_TABLE).select('id,name,lvl,depth,hero,saved_at');
  if (error) { ACC.err = error.message || 'The server heroes could not be loaded.'; console.warn('[acc] load', error); }
  ACC.heroes = {}; for (const r of data || []) { const e = rowEntry(r); ACC.heroes[e.id] = e; }
  ACC.loaded = true; accChanged();
}
// Write one (new or changed) server hero: kept here at once, sent to the server; resolves true when it is stored
async function accPut(e) {
  ACC.heroes[e.id] = e;
  if (!ACC.sb || !ACC.user) return false;
  const { error } = await ACC.sb.from(ACC_TABLE).upsert({ id: e.id.slice(2), name: e.name, lvl: e.lvl, depth: e.depth, hero: e.hero, saved_at: new Date(e.saved || Date.now()).toISOString() });
  if (error) { console.warn('[acc] save', error); return false; }
  return true;
}
async function accDel(id) {
  delete ACC.heroes[id];
  if (!ACC.sb || !ACC.user) return false;
  const { error } = await ACC.sb.from(ACC_TABLE).delete().eq('id', id.slice(2));
  if (error) { console.warn('[acc] delete', error); return false; }
  return true;
}
const newServerId = () => 's:' + (crypto.randomUUID ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => { const r = Math.random() * 16 | 0; return (c === 'x' ? r : r & 3 | 8).toString(16); }));
