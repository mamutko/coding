# Dialogue demo (sandbox only)

> A showcase of the dialogue system, played in the sandbox's "Dialogue" scenario. It is not part of the game's story
> (that is story.md). The format is described in README.md, Dialogue. Build story.js with `node tools/story/build.js`.
>
> What it shows: a keeper who starts talking as you come near, a sorcerer who only talks when clicked, a monster
> that taunts you; choices that depend on what you carry and on what you said before; consequences (a discount at
> the market, gold for scrolls, a guard that lets you pass); reactions to walking away (a discount offer, an
> important warning, a plain complaint) and picking the conversation up again when you come back.

## Character: tobias
- name: Old Tobias
- starts: near 4
- talk: 3.5
- leave: 6

### @leave
**Tobias:** `if N.offered` Walking off in the middle of a sentence. Charming.
**Tobias:** `if !N.offered` Wait, wait! Ten percent off, just for you. Come back and see.
`if !N.offered` `do: N.discount = Math.max(N.discount || 0, 0.1); N.offered = true`

### @back
**Tobias:** Back, are you? Good. Where was I…

## Conversation: tobias-first
- who: tobias
- when: `!met('tobias')`

**Tobias:** Ah, a customer! Rare finds for rare folk. And whom do I have the pleasure of, hm?
**Hero:** {name}.
**Tobias:** {name}. A fine name for a long way down.
→ ask

### ask
**Tobias:** `if !N.asked` Well? Don't just stand there dripping on my rug.
`do: N.asked = true`
1. Who are you? → who
2. `if !P.heardOfDragon` What lives at the bottom of all this? → dragon
3. Show me your wares. `do: market()`
4. Goodbye. → bye

### who
**Tobias:** Old Tobias. I sell to the living and I buy from the dead. Neither haggles much.
→ ask

### dragon
**Tobias:** At the bottom? They say a wyrm sleeps there, curled around more gold than the crown ever saw.
**Tobias:** Nobody I sold a torch to has come back up to say otherwise.
`do: P.heardOfDragon = true`
→ ask

### bye
**Tobias:** `if N.discount` Remember: ten percent off. My word is good. Mostly.
**Tobias:** Mind the stairs.

## Conversation: tobias-again
- who: tobias
- when: `met('tobias')`
- repeat
- starts: click

**Tobias:** Back for more, {name}?
**Tobias:** `if N.discount` My offer stands: ten percent off everything.
1. Show me your wares. `do: market()`
2. `if P.heardOfDragon && !N.toldMore` Tell me more about the wyrm. → more
3. `if gold >= 100 && !N.discount` Surely an old friend gets a better price? (100 gold) → bribe
4. Nothing. Goodbye. → end

### more
**Tobias:** Only what the drunks say: it hates the cold. Ice in its lungs, fire in its belly.
`do: N.toldMore = true; P.dragonHatesCold = true`
**Tobias:** Buy a scroll of frost or two. Or don't. I'm not your mother.

### bribe
`do: gold -= 100; N.discount = 0.2`
**Tobias:** For an old friend? Twenty percent. Don't tell the others.

## Character: vesper
- name: Vesper the Sorcerer
- sprite: sorcerer
- starts: click
- talk: 3.5
- leave: 6

### @leave
**Vesper:** `if N.warned` Go, then. The cold waits for no one, and neither do I.
**Vesper:** `if !N.warned` Stop! One more thing, and listen well: the ice cracks under the dead first. Never stand where a corpse lies.
`if !N.warned` `do: N.warned = true; P.knowsIceCracks = true`

### @back
**Vesper:** You return. The stars said you might.

## Conversation: vesper-meet
- who: vesper
- repeat

**Vesper:** `if !met('vesper')` Stand still. Let me look at you, {name}.
**Vesper:** `if met('vesper')` Again, {name}? Speak.
**Vesper:** `if has('frost')` You carry frost. I can smell it on your pack.
**Vesper:** `if !has('frost')` No frost on you. Pity. The deep belongs to those who carry winter.
1. `if gold >= 200` Teach me to read the frost. (200 gold) → teach
2. `if met('tobias') && !N.tobias` Do you know Old Tobias? → tobias
3. `if P.dragonHatesCold` Tobias says the wyrm hates the cold. → dragon
4. Farewell. → end

### teach
`do: gold -= 200; give('frost', 2); N.taught = (N.taught || 0) + 1`
**Vesper:** Two scrolls. Speak the words as written, and do not stand on the water when it thaws.

### tobias
`do: N.tobias = true`
**Vesper:** That old crow? He would sell his own shadow if it held still long enough.
**Vesper:** Ask him nicely and he may lower his prices. Ask him rudely and he may lower them further.

### dragon
**Vesper:** It does. Freeze it, and it cannot breathe its fire. For a little while.
`do: P.dragonFreezes = true`

## Character: champion
- starts: near 6
- leave: 12

## Conversation: guard
- who: champion
- when: `!N.done`

**Champion:** Turn back, {name}. None pass while I stand.
1. Then fall. `do: attack(); N.done = true`
2. `if has('frost')` I carry the frost. Would you rather stand frozen? → frost
3. I will go around. → end

### frost
**Champion:** …The cold. I remember the cold.
**Champion:** Pass, then. And may it find you before I do.
`do: N.done = true; N.spared = true`
