---
name: user-accounts
description: How to add user login to a single-file HTML project using Supabase email OTP / magic links — sending the sign-in email, tracking auth state, showing logged-in/out UI, and protecting each user's data with row-level security on auth.uid(). Use when a project needs sign-in, accounts, or per-user private data. Worked example: martin/notebook-01.
---

# User accounts (Supabase email OTP)

Manage user login with **Supabase Auth using email OTP / magic links**
(`signInWithOtp`). There are no passwords: the user enters their email, receives
a sign-in link, clicks it, and returns to the app signed in. This builds on the
shared "coding" Supabase project — see the `database-backend` skill for the
project URL, key, and table/migration conventions.

## Load the client

```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
```
```js
const SUPABASE_URL = 'https://qifgxysuhskscrjjwzfm.supabase.co';
const SUPABASE_KEY = 'sb_publishable_dJ7DGbkXPYOiD4YipTXEog_vx_FhOot'; // publishable; safe to ship
const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
```

## Send the sign-in email

`emailRedirectTo` is where the magic link returns the user — use the app's own
URL so they land back in the app:

```js
const { error } = await sb.auth.signInWithOtp({
  email,
  options: { emailRedirectTo: window.location.href }
});
// On success, tell the user to check their email for the sign-in link.
```

## Track auth state (the single source of truth)

Drive **all** logged-in/out UI from `onAuthStateChange`. It fires on initial
load (`INITIAL_SESSION`), after the magic-link return (`SIGNED_IN`), on sign-out,
and on background token refreshes:

```js
let currentUser = null;

sb.auth.onAuthStateChange((_event, session) => {
  const user = session && session.user;
  if (user) {
    if (!currentUser || currentUser.id !== user.id) {
      enterLoggedIn(user);   // user actually changed → (re)load their data
    } else {
      currentUser = user;    // just a token refresh → DON'T reload their data
    }
  } else {
    enterLoggedOut();
  }
});
```

**Important:** only (re)load user data when the user's `id` actually changes. A
background token refresh fires this handler too, and reloading on every fire can
clobber what the user is currently editing.

Sign out (flush any unsaved work first):

```js
await sb.auth.signOut();
```

## Display name fallback

Magic-link users usually have no profile name, so fall back to the email:

```js
function displayName(user) {
  const m = user.user_metadata || {};
  return m.full_name || m.name || user.email || 'user';
}
```

## Protect each user's data with RLS

Store per-user rows keyed by the auth user id and let Postgres enforce isolation
— never rely on client checks alone. One row per user keyed by
`auth.users(id)`, with policies scoped to `auth.uid() = user_id` and **no**
privileges for `anon`:

```sql
create table if not exists public.mn1_notes (
    user_id    uuid        primary key references auth.users (id) on delete cascade,
    content    text        not null default '',
    updated_at timestamptz not null default now()
);
alter table public.mn1_notes enable row level security;

create policy "mn1_notes select own" on public.mn1_notes
    for select to authenticated using (auth.uid() = user_id);
create policy "mn1_notes insert own" on public.mn1_notes
    for insert to authenticated with check (auth.uid() = user_id);
create policy "mn1_notes update own" on public.mn1_notes
    for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "mn1_notes delete own" on public.mn1_notes
    for delete to authenticated using (auth.uid() = user_id);

grant select, insert, update, delete on public.mn1_notes to authenticated;
```

Then read/write scoped to the signed-in user (RLS makes the `eq` filter
mandatory anyway):

```js
const { data } = await sb.from('mn1_notes').select('content').eq('user_id', currentUser.id).maybeSingle();
await sb.from('mn1_notes').upsert({ user_id: currentUser.id, content, updated_at: new Date().toISOString() });
```

## Required Supabase dashboard setup (not in code)

These are configured in the Supabase dashboard, not in `index.html`:

- **Email auth must be enabled** (on by default). The built-in mailer is
  rate-limited — configure a custom SMTP provider for anything beyond light
  testing.
- The app must be served from a URL listed under **Authentication → URL
  Configuration** (Site URL / Redirect URLs), because the magic link redirects
  back to `window.location.href`. Opening the file via `file://` will **not**
  complete sign-in — serve it over `http(s)` (a local static server is fine) and
  add that URL to the allow list.

## Checklist for adding login

- [ ] Load the Supabase JS client from the CDN.
- [ ] Add a login dialog that calls `signInWithOtp({ email, options:{ emailRedirectTo } })`.
- [ ] Drive all UI from `onAuthStateChange`; reload user data only when the user id changes.
- [ ] Create a per-user table with RLS scoped to `auth.uid() = user_id` (migration under `supabase/migrations/`).
- [ ] Enable email auth and add the serving URL to the dashboard's redirect allow list.
- [ ] Document the auth flow in the project README (link back to this skill for the generic mechanics).
