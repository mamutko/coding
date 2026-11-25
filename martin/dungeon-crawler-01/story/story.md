# Crypt of Endless Night — the story

This file describes the game's story: who the characters are, what they say and why, and what follows from it. It
is free writing, at whatever level of detail suits each scene: exact lines where the words matter, a sentence
("Tobias greets the hero and grumbles about the cold") where they don't, and, where a scene's logic is intricate,
a description of it in technical terms. The dialogue the game plays is `story.js`, written from this file and kept
in step with it (see README.md, Dialogue). `demo.md` is an example of the range.

So far the story has one character, Garrick at the crypt's door. A character without conversations behaves as the
game has it (a click on a Keeper of the Crypt opens the market).

Characters the game already places:
- the Keepers of the Crypt: Aldric, Borin, Mirela and Tobias (one per stall, every third depth);
- any boss, any champion, or a kind of monster: skeletons, ghouls, spiders, wraiths, demons.

New characters (story NPCs) can be added; describe them, and how and where they appear.

## Garrick, the hunter at the crypt

A hunter who lives in the woods around the crypt and keeps an eye on its door. Weathered, wry, kind underneath; he
has watched too many people go down and not come back. He calls the hero "traveller" (never by name: every line is
voiced). Drawn with the cast's hunter sheet; he stands on the lawn a few steps from the crypt's door and wanders
about there.

**Voice:** a man in his fifties, low and gravelly, unhurried, a rural northern accent; dry humour, warmth under it.

### The first meeting

The first time the hero comes within about 5 tiles he calls out and walks over. He warns them that this is the
Crypt of Endless Night, that people go down and few come back. If they're set on going, he gives them a **scroll of
surface escape**: read aloud down there, it carries them back up into the light; but it takes a few breaths to
read, so they shouldn't leave it till they're bleeding out. Then the hero can ask:

- **What's down there?** He has only stories: the dead don't rest easy below; things that walk and things that
  crawl, and worse the deeper you go; and a darkness that eats the light. Nothing specific.
- **Have you been inside?** Once, only as far as the first stair; that was far enough. He heard something breathing
  down there, something big. (A hint of the dragon, never named.)
- **Any advice?** Keep a wall at your back, don't take them all on at once, and not everything in the dark wants
  you dead: some of it trades. (A hint of the Keepers of the Crypt.)
- **Can you help me?** He gives the hero **one health potion**, brewed himself. Only once: asked again, he has none
  to spare (the rest are for his own hide).
- **Do you have another of those scrolls?** (only while the hero carries no scroll of surface escape and no scroll of
  return) He is glad it was used: it means they came back. He gives another, as often as they ask, and mentions
  that the keepers below sell them too, for those who can pay.
- **Goodbye.** He wishes them luck: he'd like to see them come back out.

After each answer the hero can ask another.

### Later

On a click (he doesn't call out again): he is glad to see the hero still in one piece, and the same questions are
open.

### Walking away

Mid-conversation, he lets the hero go with a dry remark ("Mind the dark, then."); coming back, he picks up
("Where were we?").

The hero's side is voiced too, in both hero voices (male and female, by the hero's look).
