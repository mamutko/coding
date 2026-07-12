---
name: working-with-projects
description: Conventions for working in the "coding" teaching repository — project folder layout, keeping README.md fully in sync with the code, and the main-branch git workflow. Use whenever creating a new project, modifying project code, or deciding where files go and how to commit.
---

# Working with projects in the "coding" repo

The "coding" repository teaches agentic coding through small, self-contained
projects. **This skill is the canonical, must-read reference for the
repository's rules and workflow — read it before modifying any project files.**
The root `README.md` keeps only a brief summary and points here. Each project
folder has a project specific `README.md`. Read that one as well before working
with that project.

## Folder structure

- Every project lives in `user-name/project-name`. For example Martin's project
  "Worm" version 03 is in `martin/worm-03`. The user name is the lowercased
  first name; the project name is a lowercase, dash-separated slug that **must**
  end in a two-digit version suffix (`-01`, `-02`, …).
- Unless the user says otherwise, a project is implemented as a **single
  self-contained `index.html`** (vanilla JavaScript, inline CSS/JS, no build
  step). External libraries are pulled from a CDN `<script>` tag.
- Each project has a README (`README.md` or `readme.md`) at its root.
- The repository root has an `index.html` that links to every project. **When
  you create a new project, add a card/link for it in the root `index.html`** —
  refer to the `README.md` in the root of the repository for details on how to
  update the root `index.html`.
- Shared backend assets live at the repo root, not inside a project — notably
  `supabase/migrations/` (see the `database-backend` skill).

## Keep README.md in sync with the code — the core rule

The project README must **fully describe the current implementation**. Anyone
should be able to regenerate `index.html` from the README alone and get a
substantially equivalent project.

- **Anytime you modify project code, update the README in the same change.**
  Add the new behavior to the relevant section, or create a new section if none
  fits.
- Describe the **current state**, not a changelog. Write "## Two Player Mode"
  with details of how it works — do **not** write "implemented two-player mode"
  or other status/progress notes.
- The README may describe planned-but-unimplemented features; mark each with a
  **TODO** tag. When you implement a TODO feature, remove the TODO label and
  update the description. If you implement only part of it, keep a TODO note for
  the unimplemented remainder.
- Rare exception: a project may deliberately choose **not** to document a
  specific detail (e.g. worm-03's bad-word list is intentionally undocumented).
  Only do this when the README itself explains why.

When a project uses a cross-cutting concept covered by another skill
(multiplayer, presentations, Supabase backend, user accounts), keep the
**project-specific** details in the project README and link to the relevant
skill for the generic mechanics, rather than duplicating the generic
explanation in every project.

## Git workflow

- **Work directly on `main` with no branching** unless the user explicitly asks
  you to create a branch. This repo favors a simple linear history.
- **Commit or push only when the user asks.** Don't auto-commit after edits.
- Commits to `main` also drive Supabase migrations (the GitHub integration
  applies new files under `supabase/migrations/` on merge to `main`), so treat
  pushing to `main` as a deploy for any backend changes.

## Creating a project

When creating a new project:

- create a folder for the project under `user-name/project-name-01`
- use `-01` as a version suffix unless creating a new version of an already present project
- always ask the user which `user-name` to use, and confirm it with them — even if the conversation context already seems to contain a name, do not assume it is the right one
- create an empty README.md in the project folder, with just a title and a "TODO" note noting that the project has not been implemented, yet
- implement a placeholder `index.html` containing just the project name (e.g.
  a single heading with the project name), so there is something to deploy and
  open before any real work is done
- if the user didn't provide details on what the project should be, instruct the user to edit README.md to provide details about the project and then prompt AI to implement it
- if the user provided details in the initial prompt, put them in README.md
- commit and push the new project to `main` so GitHub Pages deploys it — this
  is an explicit exception to the "push only when the user asks" rule above; the
  initial scaffold (README + placeholder `index.html`) is always pushed as part
  of creating the project
- after pushing, give the user **both** links so they can open the project:
  - **Local copy** — a link to the project's local `index.html` file on disk
    (e.g. `user-name/project-name-01/index.html`), so they can open it directly
    in a browser without waiting for a deploy
  - **Deployed (web-facing) version** — the GitHub Pages URL, which for this
    repo is `https://mamutko.github.io/coding/user-name/project-name-01/`
    (GitHub Pages serves the repo root, so the path mirrors the folder
    structure). Note it may take a minute or two after the push for the deploy
    to go live
- refer to project-type-specific skills for specific project types:
  - the project is a multiplayer game (multiplayer-game skill)
  - the project needs a storage backend (database-backend skill)
  - the project is a presentation or a quiz (presentation skill)
  - the project needs users to be able to sign-up and login (user-accounts skill)
