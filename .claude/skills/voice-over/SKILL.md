---
name: voice-over
description: Give a browser game (or any page) spoken dialogue with AI voices — writing lines that can be voiced, choosing a voice and a delivery style per speaker (the player in a male and a female voice), making the clips in a batch with OpenAI speech (silence trimmed, near-silent takes remade, words checked by transcription, about $0.001 a line), keeping them in step with the script by content-hashed names, and playing them in the game through Web Audio (one at a time, lines kept up while spoken, choices after, quick fade when cut off). Use when adding voice-over, voiced NPCs or narration, re-voicing changed lines, or fixing clips that are silent, cut off, padded or out of step with the text. Worked example: martin/dungeon-crawler-01 (Garrick the Hunter; README "Voice-over").
---

# Voice-over: AI-voiced dialogue for a browser game

```
SKILL.md                this workflow
learnings.md            what works and what doesn't (evidence, dated)
tools/make_voices.py    makes, checks and indexes a batch of clips (any project)
tools/voice-player.js   a reference Web Audio player to copy into a game
```

The speech itself comes from the **ai-media-generation** skill (in the `notes` repo,
`.claude/skills/ai-media-generation/`): `openai_media.py speak` makes a clip, `google_media.py transcribe` checks
one. Those scripts read their own API keys: **never open, print or copy the keys**, and never copy the scripts into
this (public) repo. Pass their paths with `--tts` / `--stt` (or `$TTS_SCRIPT` / `$STT_SCRIPT`). Cost rules are that
skill's: confirm any single call over $0.20, at most $3.00 a turn, report the spend.

## 1. Write lines that can be voiced

- **Nothing that changes** in a voiced line: no player name, numbers, item names filled in by the game. A clip is
  made once for a fixed text. Have characters use a generic address ("traveller", "friend", "stranger"; not
  "hero"). The game may still *show* the player's name as the speaker label.
- **The player's side is voiced too** when it speaks (dialogue choices, lines): write choices as things a person
  says ("Any advice?"), not menu labels ("Ask for advice (100 gold)"). Put prices and conditions in the UI
  instead.
- **One take per player voice:** if the player character can be male or female (or several looks), list each
  player line once per voice, under its own speaker name (`hero:m`, `hero:f`), and pick by the look at run time.
- Keep lines short (one or two sentences). Long lines take long to hear and can't be skipped half-way gracefully.

## 2. Choose the voices

A voice is `{ voice, style, speed }`: an OpenAI speech voice (`alloy ash ballad coral echo fable nova onyx sage
shimmer verse`), a **style** (the `instructions` of `gpt-4o-mini-tts`: who is speaking, age, accent, mood, how
loud), and optionally a speed (0.25-4). Write the style as a short character brief, e.g. "A weathered hunter in his
fifties: low, gravelly, unhurried, a rural northern English accent; dry humour with warmth underneath. Speak
quietly, as if outdoors at dusk." Keep the voices with the script (the worked example puts them in the dialogue
file's `voices`). Make one or two sample lines first and let the user listen before voicing everything: you can't
hear the clips, only check their words.

## 3. Make the clips

List every clip the game wants in a JSON file and run the tool:

```json
{"clips": [
  {"speaker": "garrick", "text": "Hold there, traveller.", "voice": {"voice": "ash", "style": "A weathered hunter ..."}},
  {"speaker": "hero:m",  "text": "Any advice?",            "voice": {"voice": "echo", "style": "..."}},
  {"speaker": "hero:f",  "text": "Any advice?",            "voice": {"voice": "shimmer", "style": "..."}}
]}
```

```
T=/home/user/notes/.claude/skills/ai-media-generation
python3 .claude/skills/voice-over/tools/make_voices.py --lines L.json --out <clips dir>          # what's missing, cost
python3 .claude/skills/voice-over/tools/make_voices.py --lines L.json --out <clips dir> \
    --index <index.js|.json> --prefix <path the game loads them by>/ \
    --go --tts $T/openai_media.py --verify --stt $T/google_media.py                              # make, check, index
```

What it does (see learnings.md for why):
- names each clip `<speaker>-<hash>.mp3`, the hash covering voice, style, speed and text: an unchanged line is
  never made again, a changed line or voice gets a new clip, and clips no line uses are **removed** from the folder
  (so give each project or story its own clips folder);
- makes each missing clip, **cuts the silence** before and after the voice (`ffmpeg silenceremove`, also on the
  reversed audio for the end), saves mono 64 kbit/s MP3 (about 30 KB a line);
- **remakes a clip that comes back too short** for its words (nearly silent), up to 3 takes;
- with `--verify`, **transcribes** the new clips and flags any whose words differ (the user still listens for tone);
- writes the **index**: `"speaker|text"` → `[path, seconds]`, as JSON or as a `.js` file
  (`var VOICE_CLIPS = VOICE_CLIPS || {}; Object.assign(VOICE_CLIPS, {...})`, loadable with a `<script src>`,
  which also works where `fetch` of a local JSON doesn't).

A project usually wraps it in its own small script that collects the lines from its script format, writes the JSON
and calls the tool (the worked example: `martin/dungeon-crawler-01/tools/story/voice.js`). **After changing any
voiced line or voice, run it again** and commit the clips, removals and index together.

## 4. Play them in the game

Copy `tools/voice-player.js` (or follow it): Web Audio, one clip at a time.
- Create the `AudioContext` in a click or key handler (browsers keep audio off until the player interacts); route
  voices through their own gain node (a Voices volume slider), not the effects'.
- Look a line up by `speaker|text` as it appears; play it 0.25 s after it appears.
- Keep the line on screen for **max(reading time, clip + 0.6 s)**, and show **choices only once the line has been
  spoken**; a voiced choice is said by the player first, shown as the current line while it plays.
- **Stop** (0.12 s fade) on the next line, a click that skips, walking away, the conversation ending.
- **Preload** a character's clips (and the player's) when a conversation with it starts; skip a clip still loading
  0.8 s after its line appeared rather than play it late.
- Lines without a clip simply aren't spoken: the game works with no clips at all.

If the game is also published as an artifact (artifact-sandbox skill), the clips go as separate asset files (they
are small), and the index can be inlined like any local script.

## 5. Document it

In the project README: the voices (voice and style per speaker), the tool command, where clips and index live, how
playback is timed, what was spent (date, number of clips, cost). Note the provenance of the clips like any AI asset.
