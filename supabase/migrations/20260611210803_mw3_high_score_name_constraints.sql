-- Enforce the worm-03 name rules at the database level, as a backstop to the
-- in-browser validation: names are 1..18 characters and contain only letters,
-- spaces, and dashes. The '*' character is additionally allowed so the owner
-- can manually redact a published name directly in the table (the client never
-- submits '*').

-- Remove any pre-existing rows that would violate the new constraints, so the
-- ALTER ... ADD CONSTRAINT cannot fail on legacy data. The leaderboard is
-- ephemeral (pruned to the top 20), so dropping invalid rows is acceptable.
delete from public.mw3_high_score
where char_length(name) > 18
   or name !~ '^[A-Za-z *-]+$';

alter table public.mw3_high_score
    add constraint mw3_high_score_name_len
        check (char_length(name) between 1 and 18),
    add constraint mw3_high_score_name_chars
        check (name ~ '^[A-Za-z *-]+$');
