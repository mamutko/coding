-- Shared leaderboard table for the martin/earth-science-01 quiz.
--
-- Table names are prefixed with a per-project slug so multiple projects in the
-- "coding" repository can share one Supabase database without colliding. The
-- slug "mes1" stands for the project path martin/earth-science-01.
--
-- The quiz has no authentication: the leaderboard is intentionally world
-- read/write. RLS is enabled (required for tables exposed via the Data API),
-- with permissive policies that allow the anonymous role to read, insert and
-- delete rows. Delete access is needed because the client prunes everything
-- outside the top 20 after each insert.
--
-- A row stores the player's name, the number of questions answered correctly
-- (score) out of the quiz length (total), so the board can show "18 / 20" even
-- if the quiz length changes later.

create table if not exists public.mes1_high_score (
    id          bigint generated always as identity primary key,
    name        text        not null,
    score       integer     not null,
    total       integer     not null,
    "timestamp" timestamptz not null default now()
);

-- Speeds up the "top 20 by score" read.
create index if not exists mes1_high_score_score_idx
    on public.mes1_high_score (score desc);

alter table public.mes1_high_score enable row level security;

-- Public (unauthenticated) read access.
create policy "mes1_high_score public select"
    on public.mes1_high_score
    for select
    to anon, authenticated
    using (true);

-- Public (unauthenticated) insert access.
create policy "mes1_high_score public insert"
    on public.mes1_high_score
    for insert
    to anon, authenticated
    with check (true);

-- Public (unauthenticated) delete access (used to prune to the top 20).
create policy "mes1_high_score public delete"
    on public.mes1_high_score
    for delete
    to anon, authenticated
    using (true);

-- Make the grants explicit so this migration is self-contained.
grant select, insert, delete on public.mes1_high_score to anon, authenticated;

-- Enforce the same name rules as the in-browser validation (a backstop), plus
-- sane score bounds. The '*' character is additionally allowed in names so the
-- owner can manually redact a published name directly in the table (the client
-- never submits '*'). This is a brand-new table, so there is no legacy data to
-- clean up before adding the constraints.
alter table public.mes1_high_score
    add constraint mes1_high_score_name_len
        check (char_length(name) between 1 and 18),
    add constraint mes1_high_score_name_chars
        check (name ~ '^[A-Za-z *-]+$'),
    add constraint mes1_high_score_total_pos
        check (total > 0),
    add constraint mes1_high_score_score_range
        check (score between 0 and total);
