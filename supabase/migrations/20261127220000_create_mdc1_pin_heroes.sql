-- martin/dungeon-crawler-01 (Crypt of Endless Night): heroes kept on the server under a PIN, for testing (no
-- account, no email): a PIN is two uppercase letters and four digits (e.g. initials + digits, "MI4821").
-- The table holds only a salted SHA-256 of the PIN, and nobody can read or write it directly: no privileges for
-- anon or authenticated, row-level security on with no policies. All access goes through the three functions
-- below (security definer), which only ever touch the rows of the PIN they are given, so the rows cannot be listed
-- and the PINs cannot be read. Weak by design (a PIN can be guessed; two players picking the same PIN share
-- heroes): the game says so and calls it a testing option that may be retired.
create table if not exists public.mdc1_pin_heroes (
    id         uuid        primary key default gen_random_uuid(),
    pin_hash   text        not null,
    name       text        not null check (char_length(name) between 1 and 20),
    lvl        integer     not null default 1 check (lvl >= 1),
    depth      integer     not null default 0 check (depth >= 0),
    hero       jsonb       not null check (pg_column_size(hero) < 1000000),
    saved_at   timestamptz not null default now()
);
create index if not exists mdc1_pin_heroes_pin_idx on public.mdc1_pin_heroes (pin_hash);
alter table public.mdc1_pin_heroes enable row level security;
revoke all on public.mdc1_pin_heroes from anon, authenticated;

-- the PIN's hash, after checking its form
create or replace function public.mdc1_pin_hash(p_pin text) returns text
language plpgsql immutable set search_path = public, pg_temp as $$
begin
  if p_pin is null or p_pin !~ '^[A-Z]{2}[0-9]{4}$' then raise exception 'invalid PIN' using errcode = '22023'; end if;
  return encode(sha256(convert_to('mdc1-pin:' || p_pin, 'UTF8')), 'hex');
end $$;

-- the heroes of a PIN
create or replace function public.mdc1_pin_list(p_pin text)
returns table (id uuid, name text, lvl integer, depth integer, hero jsonb, saved_at timestamptz)
language sql security definer set search_path = public, pg_temp as $$
  select h.id, h.name, h.lvl, h.depth, h.hero, h.saved_at from public.mdc1_pin_heroes h where h.pin_hash = public.mdc1_pin_hash(p_pin);
$$;

-- save (add or replace) one hero of a PIN; a hero id that belongs to another PIN is refused
create or replace function public.mdc1_pin_save(p_pin text, p_id uuid, p_name text, p_lvl integer, p_depth integer, p_hero jsonb, p_saved timestamptz)
returns void language plpgsql security definer set search_path = public, pg_temp as $$
declare h text := public.mdc1_pin_hash(p_pin); n integer;
begin
  update public.mdc1_pin_heroes set name = p_name, lvl = p_lvl, depth = p_depth, hero = p_hero, saved_at = coalesce(p_saved, now())
    where id = p_id and pin_hash = h;
  get diagnostics n = row_count;
  if n = 0 then
    if exists (select 1 from public.mdc1_pin_heroes where id = p_id) then raise exception 'not your hero' using errcode = '42501'; end if;
    insert into public.mdc1_pin_heroes (id, pin_hash, name, lvl, depth, hero, saved_at) values (p_id, h, p_name, p_lvl, p_depth, p_hero, coalesce(p_saved, now()));
  end if;
end $$;

-- delete one hero of a PIN
create or replace function public.mdc1_pin_delete(p_pin text, p_id uuid)
returns void language sql security definer set search_path = public, pg_temp as $$
  delete from public.mdc1_pin_heroes where id = p_id and pin_hash = public.mdc1_pin_hash(p_pin);
$$;

revoke all on function public.mdc1_pin_hash(text) from public;
revoke all on function public.mdc1_pin_list(text) from public;
revoke all on function public.mdc1_pin_save(text, uuid, text, integer, integer, jsonb, timestamptz) from public;
revoke all on function public.mdc1_pin_delete(text, uuid) from public;
grant execute on function public.mdc1_pin_list(text) to anon, authenticated;
grant execute on function public.mdc1_pin_save(text, uuid, text, integer, integer, jsonb, timestamptz) to anon, authenticated;
grant execute on function public.mdc1_pin_delete(text, uuid) to anon, authenticated;
