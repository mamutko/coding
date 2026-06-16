# Notebook (notebook-01)

A minimal single-user notes app built to investigate authentication and
per-user data protection with Supabase. Each signed-in user has one private
notes document that autosaves to the database and is visible only to them.

## Layout

- A header row across the top with the title **"Notebook"** on the left and a
  **Login** button on the right.
- Below the header, a single text area fills the entire remaining height and
  width of the screen. It holds the user's notes.
- Before the user logs in, the text area is **disabled** and shows a prompt to
  log in. After login it becomes editable.

## Authentication

Login uses **Supabase email OTP / magic links**. The generic mechanics — sending the link with
`signInWithOtp`, driving the UI from `onAuthStateChange`, the display-name fallback, protecting
per-user data with RLS on `auth.uid()`, and the required dashboard setup — are documented in the
**`user-accounts` skill** (`.claude/skills/user-accounts/`). Notebook-specific behaviour:

- Clicking **Login** opens a small dialog asking for an email address and sends
  a **magic link** via Supabase (`signInWithOtp`). The user clicks the link in
  their email and is returned to the app, now signed in.
- Once signed in, the header button changes to **"Logout: &lt;name&gt;"**. For
  magic-link sign-ins the user usually has no profile name, so the name falls
  back to their email address. Clicking the button signs the user out (after
  flushing any unsaved changes) and disables the text area again.
- Auth state is tracked with `supabase.auth.onAuthStateChange`, which handles
  the initial page load, the magic-link return, sign-out, and token refreshes.
  The note is only (re)loaded when the signed-in user actually changes, so a
  background token refresh never overwrites what the user is currently typing.

## Notes storage and autosave

- The note content is stored in the Supabase table `mn1_notes` (slug `mn1` =
  `martin/notebook-01`), one row per user, holding the full text of the field
  in a single `content` column.
- Editing schedules an **autosave 2 seconds after the last keystroke**. Each
  save upserts the user's row (`user_id`, `content`, `updated_at`).
- A **dirty indicator** — a small white circle in the header row — appears as
  soon as the content is modified and is hidden again once the content has been
  saved. If edits arrive while a save is in flight, the indicator stays on until
  the latest content is persisted.
- A best-effort save also runs when signing out and when the tab is closed with
  unsaved changes.

## Data protection (RLS)

- `mn1_notes` (slug `mn1` = `martin/notebook-01`) has row-level security enabled,
  with policies scoped to `auth.uid() = user_id` for the `authenticated` role and
  **no** privileges for `anon`, so each user can only ever see and edit their own
  row and notes are never readable without signing in. See the `user-accounts`
  skill for the policy pattern and the `database-backend` skill for the migration
  conventions.
- The table is created by a migration under `supabase/migrations/`.

## Implementation details

- The app is a single HTML5 file `index.html` using vanilla JavaScript.
- The Supabase JS client (v2) is loaded from a CDN `<script>` tag. The app uses
  the "coding" Supabase project and its publishable key, which is meant to ship
  in client code; access is gated by authentication and RLS rather than by
  hiding the key.

## Setup notes (Supabase dashboard)

This app needs the standard email-OTP dashboard setup — email auth enabled, and the
serving URL added to **Authentication → URL Configuration** so the magic link can
redirect back (it won't complete over `file://`). The details are in the
**`user-accounts` skill**.
