# "coding" repository

The purpose of this repository is to teach agentic coding to multiple users. It contains projects organized by user name and project name (e.g., Martin's project Worm would be in the `martin/worm` folder).

## MUST READ before working with any project

Before modifying any project files, read the **`working-with-projects` skill**
(`.claude/skills/working-with-projects/SKILL.md`). It is the canonical statement of the
repository's rules and workflow. The bullets below are only a quick summary.

## Core rules (summary)

- Each project lives in `user-name/project-name` and has its own README.
- Implement as a single self-contained `index.html` unless the user says otherwise.
- Keep the project README fully in sync with the code; update it in the same change as any code change. Describe the current state, not a changelog.
- Mark planned-but-unimplemented features with a **TODO** tag.
- Add a link in the root `index.html` for every new project.
- Work directly on `main`; only branch when the user explicitly asks.
