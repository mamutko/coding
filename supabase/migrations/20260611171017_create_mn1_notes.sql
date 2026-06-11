-- Per-user notes table for the martin/notebook-01 project.
--
-- Table names are prefixed with a per-project slug so multiple projects in the
-- "coding" repository can share one Supabase database. The slug "mn1" stands
-- for the project martin/notebook-01.
--
-- Unlike the worm leaderboard, this table is private: each authenticated user
-- can see and edit only their own row. There is exactly one row per user,
-- keyed by their auth user id, holding the full text of their notes.

create table if not exists public.mn1_notes (
    user_id    uuid        primary key references auth.users (id) on delete cascade,
    content    text        not null default '',
    updated_at timestamptz not null default now()
);

alter table public.mn1_notes enable row level security;

-- A user may only read their own row.
create policy "mn1_notes select own"
    on public.mn1_notes
    for select
    to authenticated
    using (auth.uid() = user_id);

-- A user may only create a row owned by themselves.
create policy "mn1_notes insert own"
    on public.mn1_notes
    for insert
    to authenticated
    with check (auth.uid() = user_id);

-- A user may only update their own row, and may not reassign it to someone else.
create policy "mn1_notes update own"
    on public.mn1_notes
    for update
    to authenticated
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- A user may delete their own row.
create policy "mn1_notes delete own"
    on public.mn1_notes
    for delete
    to authenticated
    using (auth.uid() = user_id);

-- Only authenticated users get table privileges; the anon role gets none, so
-- notes are never readable without signing in. RLS still scopes each
-- authenticated user to their own row.
grant select, insert, update, delete on public.mn1_notes to authenticated;
