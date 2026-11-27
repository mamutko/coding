-- martin/dungeon-crawler-01 (Crypt of Endless Night): heroes saved on the server by signed-in players.
-- One row per hero; each player sees and changes only their own (row-level security on auth.uid()).
-- hero: the save entry's hero data (the game's SAVED_FIELDS), as the browser keeps it in localStorage.
create table if not exists public.mdc1_heroes (
    id         uuid        primary key default gen_random_uuid(),
    user_id    uuid        not null default auth.uid() references auth.users (id) on delete cascade,
    name       text        not null check (char_length(name) between 1 and 20),
    lvl        integer     not null default 1 check (lvl >= 1),
    depth      integer     not null default 0 check (depth >= 0),
    hero       jsonb       not null check (pg_column_size(hero) < 1000000),
    saved_at   timestamptz not null default now()
);
create index if not exists mdc1_heroes_user_idx on public.mdc1_heroes (user_id);
alter table public.mdc1_heroes enable row level security;

drop policy if exists "mdc1_heroes select own" on public.mdc1_heroes;
drop policy if exists "mdc1_heroes insert own" on public.mdc1_heroes;
drop policy if exists "mdc1_heroes update own" on public.mdc1_heroes;
drop policy if exists "mdc1_heroes delete own" on public.mdc1_heroes;
create policy "mdc1_heroes select own" on public.mdc1_heroes
    for select to authenticated using (auth.uid() = user_id);
create policy "mdc1_heroes insert own" on public.mdc1_heroes
    for insert to authenticated with check (auth.uid() = user_id);
create policy "mdc1_heroes update own" on public.mdc1_heroes
    for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "mdc1_heroes delete own" on public.mdc1_heroes
    for delete to authenticated using (auth.uid() = user_id);

revoke all on public.mdc1_heroes from anon;
grant select, insert, update, delete on public.mdc1_heroes to authenticated;
