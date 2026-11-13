---
name: version-tracking
description: Optional per-project version tracking — a VERSION number shown in the project and bumped before every push, and a versions.md that lists, newest first, what each version added as a short bullet list (small iterative follow-ups merged into one entry such as "v12–v18"), with the commit of each entry and the git commands to get any version back. Use when the user wants to start tracking versions in a project, when pushing a change to a project that has a versions.md, or when the user wants to see or go back to an earlier version. Worked example: martin/dungeon-crawler-01 (versions.md, README "Version").
---

# Version tracking (optional per project)

A project can choose to track versions, so the user can see what changed when and go back to any version through
git history. It is **opt-in**: start only when the user asks for it in a project. A project that tracks versions
has a `versions.md` next to its `index.html`; when it does, the rules below apply to every push of that project.

## The version number

- An integer constant near the top of the project's script, e.g. `const VERSION = 43;`, shown muted somewhere
  unobtrusive (the title screen, a footer, a debug panel), so the user can tell whether the page they have open
  (often a cached GitHub Pages copy) is up to date.
- **Bump it by one before every push** of the project, whatever the change (code, assets, docs of the project).
  One push = one version.
- Name the version in the commit message, e.g. `Dungeon crawler v43: ...`, so `git log` finds it.
- Describe the number in the project README (a "Version" section) and point to `versions.md`.

## versions.md

Newest entry first. Start the file with a short header (what it is, where the number is shown, that entries are
merged, how the commit line works) and end it with a "Going back to a version" section (below).

Each entry:

```markdown
## v44–v46 — combat music timing (2026-11-12)

Commit: 1a2b3c4

- Combat music lasts while any monster still pursues.
- Ends at once when the last pursuer is killed; 6 s after they lose interest.
```

- **Heading**: the version or range, a few words naming the change, the date (or date range).
- **Tags** (optional, set by the user): a line such as `Tags: Playable / Good Experience` under the heading,
  marking versions worth going back to. Keep the user's tags as they are; when an entry is widened, ask before
  carrying a tag over to the new range (the tag was given to the old state).
- **Commit**: the hash of the entry's last version. The commit hash isn't known before the commit is made, so
  the newest entry says it will be filled in, and **when the next version is recorded, fill in the previous
  entry's commit** (`git log -1 --format=%h`, taken before the new commit). Merged versions inside a range are
  found by their version number (below).
- **A bullet list of features**, written for the user: what one can now see or do, not how it is coded (the
  README covers that). Group bullets under bold sub-headings when a list is long.

**The first entry** (when a project starts tracking) is the whole project so far: heading like
`## v43 — the game so far (v1–v43, <first date> to <today>)`, with a full feature list grouped by area. It is long
once; later entries are short.

### Merging entries

When a new version is a **small, iterative change that builds on the previous version's change** (a tweak, a fix,
a follow-up to the same feature — e.g. "combat music lasts while anything pursues" right after "combat music"),
don't add a new entry: **widen the previous entry** (`v38` → `v38–v39`, `v38–v40`, ...), update its heading and
date, and rewrite its bullet list as **one list of what the range adds**, describing the end state (a later
version that changes an earlier bullet replaces it; no "then", no history inside the entry). Move its commit line
to the new version (fill it in at the next record, as above).

Start a **new entry** when the change is a different feature, or a big step of the same one that the user might
want to go back to separately. When unsure, keep it separate: merging later is easy, splitting isn't. Never merge
into the first ("so far") entry.

### Going back to a version

End `versions.md` with these commands (adjusted to the project's path):

```bash
git log --oneline -- user/project-NN                                   # versions are named in the messages
git log --oneline -S "const VERSION = 38;" -- user/project-NN/index.html   # the commit that set a version
git show <commit>:user/project-NN/index.html > /tmp/index-v38.html      # look at a file as it was
git checkout <commit> -- user/project-NN                               # bring the folder back to that version
```

Bringing a folder back is an ordinary change: commit and push it as a new version (its entry says it returns to
vN), or undo it before committing with `git checkout main -- user/project-NN`. When the user asks to "go back",
first show them the entry and the commit, and say whether they want to look at it (a temporary copy, or the
sandbox artifact built from that commit, see `artifact-sandbox`) or actually restore it.

## When pushing a project that tracks versions

1. Bump `VERSION`.
2. Fill in the commit of the previous newest entry (if still open), then add or widen the entry for this version.
3. Do whatever else the project's workflow asks (README, generated files, sandbox artifact republish).
4. Commit with the version in the message and push (`working-with-projects`).

## Starting it in a project

1. Add the `VERSION` constant and show it (if the project has none), and a "Version" section in the README.
2. Read the project's git history (`git log --reverse -- <project>`) and README to write the first entry: the
   whole project so far, grouped by area.
3. Add the "Going back" section, list `versions.md` in the README's file list, and push as the next version.
