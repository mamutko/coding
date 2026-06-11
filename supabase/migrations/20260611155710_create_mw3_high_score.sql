-- Shared high-score leaderboard table for the martin/worm/03 project.
--
-- Table names are prefixed with a per-project slug so multiple projects in the
-- "coding" repository can share one Supabase database without colliding. The
-- slug "mw3" stands for the project path martin/worm/03.
--
-- The worm game has no authentication: the leaderboard is intentionally world
-- read/write. RLS is enabled (required for tables exposed via the Data API),
-- with permissive policies that allow the anonymous role to read, insert and
-- delete rows. Delete access is needed because the client purges scores older
-- than one month after each insert.

create table if not exists public.mw3_high_score (
    id          bigint generated always as identity primary key,
    name        text        not null,
    score       integer     not null,
    "timestamp" timestamptz not null default now()
);

-- Speeds up the "top 10 by score" read.
create index if not exists mw3_high_score_score_idx
    on public.mw3_high_score (score desc);

alter table public.mw3_high_score enable row level security;

-- Public (unauthenticated) read access.
create policy "mw3_high_score public select"
    on public.mw3_high_score
    for select
    to anon, authenticated
    using (true);

-- Public (unauthenticated) insert access.
create policy "mw3_high_score public insert"
    on public.mw3_high_score
    for insert
    to anon, authenticated
    with check (true);

-- Public (unauthenticated) delete access (used to purge expired scores).
create policy "mw3_high_score public delete"
    on public.mw3_high_score
    for delete
    to anon, authenticated
    using (true);

-- Supabase grants table privileges to anon/authenticated on new public tables
-- via default privileges, but make the grants explicit so this migration is
-- self-contained.
grant select, insert, delete on public.mw3_high_score to anon, authenticated;
