# Voice-over: learnings

Evidence from making clips for real, newest last. Each entry: what happened, what it taught, what the tool does
about it.

## 2026-11-24 — Garrick the Hunter (martin/dungeon-crawler-01), 26 clips, OpenAI gpt-4o-mini-tts

- **Very short lines can come back (nearly) silent.** "Any advice?" in the male hero voice (`echo`) came back
  0.41 s long, 0.36 s of it silence: a breath, no words. Remaking it once gave a clean 0.96 s clip. The same line in
  the female voice was fine. → `make_voices.py` measures every clip after trimming and remakes one shorter than
  `0.3 s + 0.1 s per word`, up to 3 takes.
- **Clips carry dead air**, mostly at the end: up to 1.6 s after the last word ("Mind the dark, then." was 3.31 s,
  2.26 s trimmed; the female "Any advice?" 2.62 s → 1.06 s). Anything timed to the clip (the line staying up,
  choices appearing) then waits on silence. → every clip is trimmed with `ffmpeg silenceremove` (threshold -45 dB),
  keeping 0.05 s before the voice and 0.15 s after it. `silenceremove` only trims the start reliably, so the end is
  trimmed on the reversed audio (`areverse`, trim, `areverse`).
- **You can't hear the clips; transcription checks the words, not the voice.** Google transcription of 4 clips
  (a fraction of a cent) gave the exact text, except "traveller" → "traveler" (US spelling). → `--verify` compares
  word lists with a similarity ratio (≥ 0.8 passes), not exact strings. Tone, accent and pacing still need the
  user's ears: make a sample or two first.
- **Cost:** gpt-4o-mini-tts is about $0.015 per minute of speech, and the script charges at least about 3 s (0.05
  min) per call, so one-word and one-sentence lines cost about the same, about $0.001. 26 clips (including one
  remake) cost about $0.035. Mono 64 kbit/s MP3: 0.8 MB for the 26 (about 30 KB a line).
- **Content-hashed names keep clips in step with the script.** The name hashes voice, style, speed and text, so
  editing a line or a voice's style makes a new clip and the stale one is removed on the next run; nothing is made
  twice. The hash is computed the same way in JavaScript and Python (`JSON.stringify` of `[voice, style, speed,
  text]`, no spaces, unicode kept; an integer speed written as `1`, not `1.0`), so a project script in either
  language finds the same files.
- **Write for the voice.** The hero's name can't be voiced (it is typed by the player), so the character says
  "traveller"; the hero's choices are written as spoken sentences ("Can you help me?"), and they are voiced in
  both hero voices (male `echo`, female `shimmer`), picked by the hero's look.
- **Timing in the game:** a line stays up for the longer of its reading time and its clip + 0.6 s; choices under a
  line appear only once the line has been spoken (players otherwise click ahead and cut the voice off); a voiced
  choice is first said by the hero, shown as the current line. A clip starts 0.25 s after its line appears, and is
  skipped if still loading 0.8 s later (better silent than late). Clips of a character and the hero load when a
  conversation with it starts.
- **Running the scripts from a tool:** `make_voices.py` runs the speech and transcription scripts from their own
  folder (where their keys live), so it passes them, and the clips, as absolute paths. A first `--verify` run passed
  a relative clip path from that folder and got an empty transcript for every clip.
