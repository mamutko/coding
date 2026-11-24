# Dialogue demo (sandbox only)

A showcase of the dialogue system, played in the sandbox's **Dialogue** scenario. It isn't part of the game's
story (that is `story.md`). This file describes the demo; the dialogue itself, with every line, condition and
effect, is `demo.js`, written from this description (see README.md, Dialogue).

The demo is written at different levels of detail on purpose, to show what a description can be: some lines are
given word for word, some scenes only say what happens, and one part describes its logic in technical terms.

What it shows: a character who starts talking as you come near, one who only talks when clicked, a monster that
speaks up; choices that depend on what you carry and on what you said before; consequences (a discount at the
market, gold for scrolls, a guard that lets you pass); reactions to walking away and picking the conversation up
again when you come back.

## The cast

- **Old Tobias**, the Keeper of the Crypt at the market stall. A miser with a dry humour, fond of regulars. The
  first time, he hails the hero as they come within about 4 tiles and comes over; after that he waits to be
  approached.
- **Vesper the Sorcerer** (drawn with the cast's sorcerer sheet). Aloof, speaks in portents. She paces about the
  room, lost in thought, and never calls out: the hero has to go up to her.
- **The champion** guarding the way: grim, few words. It stands its ground and challenges the hero when they come
  within 6 tiles, and doesn't count them as gone until they are a few tiles farther off.

## Tobias

### Meeting him

Tobias greets the hero as a rare customer and asks their name. The hero gives it, and he remarks on it with a
little gallows humour about how deep the crypt goes.

Then he waits for the hero to say something. The first time he grumbles: *"Well? Don't just stand there dripping on
my rug."* The hero can:

- ask who he is: he sells to the living and buys from the dead, and neither haggles much;
- ask what lives at the bottom of the crypt (only until they have heard it): a dragon sleeping on a hoard, and
  nobody he sold a torch to came back to say otherwise. From then on the hero **has heard of the dragon**;
- ask for his wares: the market opens;
- say goodbye: he says *"Mind the stairs."*, reminding them of his discount first if they have one.

After each answer they come back to these choices.

### Every later visit

When the hero comes up to him. He welcomes the hero back by name and repeats his offer if they have a discount. Choices:

- his wares;
- *"Tell me more about the wyrm."* (only once they have heard of the dragon, and only once): it hates the cold,
  "ice in its lungs, fire in its belly"; buy a frost scroll or two. The hero now **knows the dragon hates cold**;
- a better price for an old friend, for 100 gold (only with 100 gold and no discount yet): he takes the gold and
  gives **20 % off**, "don't tell the others";
- goodbye.

### Walking away

If the hero walks off mid-conversation the first time, he calls after them: *"Wait, wait! Ten percent off, just for
you. Come back and see."*, and they have **10 % off** from then on. Any later time he is just sarcastic about it.
When they come back he picks up where he left off: *"Back, are you? Good. Where was I…"*

## Vesper

On a click, any number of times. She greets the hero by name (more curtly once they have met), then remarks on
whether they carry a frost scroll: she can smell it, or it's a pity, since "the deep belongs to those who carry
winter". Choices:

- to be taught to read the frost, for 200 gold (only with the gold): she gives **two frost scrolls** and a warning
  not to stand on water when it thaws;
- whether she knows Old Tobias (only once the hero has met him, and only once): an old crow who would sell his own
  shadow; ask him nicely and he may lower his prices, rudely and he may lower them further;
- that Tobias says the dragon hates the cold (only if he told them): it does, and frozen it can't breathe fire for
  a while. The hero now **knows freezing stops the dragon's fire**;
- farewell.

Walking away: the first time she calls out an important warning, *the ice cracks under the dead first; never stand
where a corpse lies*, and the hero **knows the ice cracks**. Later she just lets them go coldly. Coming back she
says the stars said they might.

## The champion's challenge

Played until it is settled, one way or the other.

**Champion:** Turn back, [the hero's name]. None pass while I stand.

1. *"Then fall."* — it attacks, and the challenge is settled.
2. *"I carry the frost. Would you rather stand frozen?"* (only with a frost scroll) — **Champion:** …The cold. I
   remember the cold. **Champion:** Pass, then. And may it find you before I do. — Settled, and the champion is
   **spared** (it remembers).
3. *"I will go around."* — nothing settled; it challenges them again next time.

## The state this demo keeps

In technical terms, for the curious:

- About the hero, across characters: `heardOfDragon`, `dragonHatesCold`, `dragonFreezes`, `knowsIceCracks`.
- Tobias remembers: whether he has made his walk-away offer, the discount (0.1 or 0.2, never lowered by the
  offer), whether he grumbled already, whether he told more about the dragon.
- Vesper remembers: whether she warned the hero, whether she spoke of Tobias, how many times she taught them.
- The champion remembers: settled, spared.
