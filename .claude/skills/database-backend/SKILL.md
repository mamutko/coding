---
name: database-backend
description: How to give a single-file HTML project a shared/persistent backend with Supabase (hosted Postgres) — calling the data API from the browser, the per-project table naming convention, row-level security, and adding new tables via migrations under supabase/migrations that auto-apply on merge to main. Use when adding a database, leaderboard, shared state, or any persisted server-side data. Worked examples: martin/worm-03, martin/notebook-01.
---

# Database backend with Supabase

Projects in this repo get a backend from a **single shared Supabase project**
named **"coding"** (hosted Postgres + auto-generated REST API). The browser
talks to it directly; there is no custom server. Use this for leaderboards,
shared state, or per-user persisted data.

For login/authentication on top of this, see the `user-accounts` skill.

## The shared "coding" project

- **Dashboard:** <https://supabase.com/dashboard/project/qifgxysuhskscrjjwzfm>
  (administer by logging in with **Martin's GitHub account**).
- **Project ref / URL:** `https://qifgxysuhskscrjjwzfm.supabase.co`
- **REST (PostgREST) Data API base:** `https://qifgxysuhskscrjjwzfm.supabase.co/rest/v1/`
- **Publishable (anon) key:** `sb_publishable_dJ7DGbkXPYOiD4YipTXEog_vx_FhOot`
  — this is **designed to ship in client code**. Access is controlled by
  **row-level security (RLS)**, not by hiding the key, so it is fine to embed it
  in `index.html`.

## Table naming: per-project slug prefix

Because all projects share one database, **prefix every table with a short
per-project slug** derived from the project path so names don't collide:

- `mw3_high_score` → `martin/worm-03`
- `mn1_notes` → `martin/notebook-01`

Pick the slug as `<first-initial-of-user><project><version>` (or similar) and
use it consistently for every table the project owns.

## Two ways to call the backend from the browser

### A. Raw REST (fetch) — good for simple, unauthenticated tables

worm-03 uses plain `fetch` against PostgREST:

```js
const BASE = 'https://qifgxysuhskscrjjwzfm.supabase.co/rest/v1/mw3_high_score';
const KEY  = 'sb_publishable_dJ7DGbkXPYOiD4YipTXEog_vx_FhOot';
const HEADERS = { apikey: KEY, Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };

// Read: order + limit are query params
const res = await fetch(`${BASE}?select=name,score,timestamp&order=score.desc,id.desc&limit=20`, { headers: HEADERS });
const rows = await res.json();

// Insert
await fetch(BASE, { method: 'POST', headers: HEADERS, body: JSON.stringify({ name, score }) });

// Delete with a filter (e.g. prune everything outside the top 20)
await fetch(`${BASE}?id=not.in.(${ids})`, { method: 'DELETE', headers: HEADERS });
```

Make network calls **best-effort**: wrap in try/catch, log to console on
failure, and let the app keep working offline.

### B. Supabase JS client — good when you also use auth

notebook-01 loads the client from a CDN and uses its query builder (this is the
better choice when the project has user accounts, since it manages the auth
session/JWT automatically):

```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
```
```js
const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

const { data } = await sb.from('mn1_notes').select('content').eq('user_id', uid).maybeSingle();
await sb.from('mn1_notes').upsert({ user_id: uid, content, updated_at: new Date().toISOString() });
```

## Row-level security (RLS)

Any table exposed through the Data API **must have RLS enabled**; the policies
decide who can do what.

- **Public / unauthenticated data** (e.g. a world-readable leaderboard): enable
  RLS and add **permissive** policies granting `anon` (and `authenticated`) the
  operations you need (`select`/`insert`/`delete`). Add `CHECK` constraints to
  guard column contents since anyone can write.
- **Per-user private data**: grant privileges only to the `authenticated` role
  and scope every policy with `auth.uid() = user_id`, so each user only sees
  their own rows and `anon` gets nothing. (See `user-accounts`.)

## Adding a new table: migrations

Schema changes are SQL files under **`supabase/migrations/`** at the **repo
root** (not inside the project folder). Supabase's **GitHub integration applies
them automatically when merged to `main`** — so committing a migration to `main`
is effectively a deploy.

1. Create a file named `supabase/migrations/<UTC-timestamp>_<description>.sql`,
   e.g. `20260611171017_create_mn1_notes.sql`. Keep the timestamp prefix
   monotonically increasing (they apply in filename order).
2. Write idempotent-ish DDL: `create table if not exists`, enable RLS, create
   policies, and make the `grant`s explicit so the migration is self-contained.

Example (public, world read/write leaderboard):

```sql
create table if not exists public.mw3_high_score (
    id          bigint generated always as identity primary key,
    name        text        not null,
    score       integer     not null,
    "timestamp" timestamptz not null default now()
);
alter table public.mw3_high_score enable row level security;

create policy "mw3_high_score public select" on public.mw3_high_score
    for select to anon, authenticated using (true);
create policy "mw3_high_score public insert" on public.mw3_high_score
    for insert to anon, authenticated with check (true);
create policy "mw3_high_score public delete" on public.mw3_high_score
    for delete to anon, authenticated using (true);

grant select, insert, delete on public.mw3_high_score to anon, authenticated;
```

Add constraints in a **later** migration rather than editing an applied one;
clean up offending rows first so `ADD CONSTRAINT` can't fail on existing data:

```sql
delete from public.mw3_high_score where char_length(name) > 18 or name !~ '^[A-Za-z *-]+$';
alter table public.mw3_high_score
    add constraint mw3_high_score_name_len   check (char_length(name) between 1 and 18),
    add constraint mw3_high_score_name_chars check (name ~ '^[A-Za-z *-]+$');
```

`supabase/config.toml` pins `project_id = "coding"`; you normally don't touch it.

## Checklist for adding a backend

- [ ] Choose a per-project table slug; prefix all tables with it.
- [ ] Write a migration under `supabase/migrations/` (`create table` + RLS + policies + grants).
- [ ] Decide the access model (public permissive vs. per-user `auth.uid()`).
- [ ] Call the API from the browser (raw `fetch`, or the JS client if you use auth).
- [ ] Make network calls best-effort so the app survives an offline backend.
- [ ] Commit the migration to `main` to deploy it; document the table in the project README.
