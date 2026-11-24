// The sandbox's demo dialogue (STORIES.demo), written from the description in story/demo.md. This file is the
// dialogue itself: the game plays exactly what is here. The format is in README.md, Dialogue; check it with
// `node tools/story/check.js`.
var STORIES = STORIES || {};
STORIES.demo = {
  chars: {
    tobias: { name: 'Old Tobias', starts: 4, talk: 3.5, leave: 6, nodes: {
      '@leave': [
        { say: 'tobias', if: 'N.offered', text: 'Walking off in the middle of a sentence. Charming.' },
        { say: 'tobias', if: '!N.offered', text: 'Wait, wait! Ten percent off, just for you. Come back and see.' },
        { if: '!N.offered', do: 'N.discount = Math.max(N.discount || 0, 0.1); N.offered = true' },
      ],
      '@back': [
        { say: 'tobias', text: 'Back, are you? Good. Where was I…' },
      ],
    } },
    vesper: { name: 'Vesper the Sorcerer', sprite: 'sorcerer', starts: 'click', talk: 3.5, leave: 6, nodes: {
      '@leave': [
        { say: 'vesper', if: 'N.warned', text: 'Go, then. The cold waits for no one, and neither do I.' },
        { say: 'vesper', if: '!N.warned', text: 'Stop! One more thing, and listen well: the ice cracks under the dead first. Never stand where a corpse lies.' },
        { if: '!N.warned', do: 'N.warned = true; P.knowsIceCracks = true' },
      ],
      '@back': [
        { say: 'vesper', text: 'You return. The stars said you might.' },
      ],
    } },
    champion: { starts: 6, leave: 12 },
  },

  convs: [
    // Tobias, the first meeting: he starts it himself as the hero comes near
    { id: 'tobias-first', who: 'tobias', when: "!met('tobias')", nodes: {
      start: [
        { say: 'tobias', text: 'Ah, a customer! Rare finds for rare folk. And whom do I have the pleasure of, hm?' },
        { say: 'hero', text: '{name}.' },
        { say: 'tobias', text: '{name}. A fine name for a long way down.' },
        { go: 'ask' },
      ],
      ask: [
        { say: 'tobias', if: '!N.asked', text: "Well? Don't just stand there dripping on my rug." },
        { do: 'N.asked = true' },
        { choose: [
          { text: 'Who are you?', to: 'who' },
          { text: 'What lives at the bottom of all this?', if: '!P.heardOfDragon', to: 'dragon' },
          { text: 'Show me your wares.', do: 'market()' },
          { text: 'Goodbye.', to: 'bye' },
        ] },
      ],
      who: [
        { say: 'tobias', text: 'Old Tobias. I sell to the living and I buy from the dead. Neither haggles much.' },
        { go: 'ask' },
      ],
      dragon: [
        { say: 'tobias', text: 'At the bottom? They say a wyrm sleeps there, curled around more gold than the crown ever saw.' },
        { say: 'tobias', text: 'Nobody I sold a torch to has come back up to say otherwise.' },
        { do: 'P.heardOfDragon = true' },
        { go: 'ask' },
      ],
      bye: [
        { say: 'tobias', if: 'N.discount', text: 'Remember: ten percent off. My word is good. Mostly.' },
        { say: 'tobias', text: 'Mind the stairs.' },
      ],
    } },

    // Tobias, every later visit: on a click
    { id: 'tobias-again', who: 'tobias', when: "met('tobias')", repeat: true, starts: 'click', nodes: {
      start: [
        { say: 'tobias', text: 'Back for more, {name}?' },
        { say: 'tobias', if: 'N.discount', text: 'My offer stands: ten percent off everything.' },
        { choose: [
          { text: 'Show me your wares.', do: 'market()' },
          { text: 'Tell me more about the wyrm.', if: 'P.heardOfDragon && !N.toldMore', to: 'more' },
          { text: 'Surely an old friend gets a better price? (100 gold)', if: 'gold >= 100 && !N.discount', to: 'bribe' },
          { text: 'Nothing. Goodbye.', to: 'end' },
        ] },
      ],
      more: [
        { say: 'tobias', text: 'Only what the drunks say: it hates the cold. Ice in its lungs, fire in its belly.' },
        { do: 'N.toldMore = true; P.dragonHatesCold = true' },
        { say: 'tobias', text: "Buy a scroll of frost or two. Or don't. I'm not your mother." },
      ],
      bribe: [
        { do: 'gold -= 100; N.discount = 0.2' },
        { say: 'tobias', text: "For an old friend? Twenty percent. Don't tell the others." },
      ],
    } },

    // Vesper: only on a click, any number of times
    { id: 'vesper-meet', who: 'vesper', repeat: true, nodes: {
      start: [
        { say: 'vesper', if: "!met('vesper')", text: 'Stand still. Let me look at you, {name}.' },
        { say: 'vesper', if: "met('vesper')", text: 'Again, {name}? Speak.' },
        { say: 'vesper', if: "has('frost')", text: 'You carry frost. I can smell it on your pack.' },
        { say: 'vesper', if: "!has('frost')", text: 'No frost on you. Pity. The deep belongs to those who carry winter.' },
        { choose: [
          { text: 'Teach me to read the frost. (200 gold)', if: 'gold >= 200', to: 'teach' },
          { text: 'Do you know Old Tobias?', if: "met('tobias') && !N.tobias", to: 'tobias' },
          { text: 'Tobias says the wyrm hates the cold.', if: 'P.dragonHatesCold', to: 'dragon' },
          { text: 'Farewell.', to: 'end' },
        ] },
      ],
      teach: [
        { do: "gold -= 200; give('frost', 2); N.taught = (N.taught || 0) + 1" },
        { say: 'vesper', text: 'Two scrolls. Speak the words as written, and do not stand on the water when it thaws.' },
      ],
      tobias: [
        { do: 'N.tobias = true' },
        { say: 'vesper', text: 'That old crow? He would sell his own shadow if it held still long enough.' },
        { say: 'vesper', text: 'Ask him nicely and he may lower his prices. Ask him rudely and he may lower them further.' },
      ],
      dragon: [
        { say: 'vesper', text: 'It does. Freeze it, and it cannot breathe its fire. For a little while.' },
        { do: 'P.dragonFreezes = true' },
      ],
    } },

    // The champion guarding the way: it speaks up when the hero comes within 6 tiles
    { id: 'guard', who: 'champion', when: '!N.done', nodes: {
      start: [
        { say: 'champion', text: 'Turn back, {name}. None pass while I stand.' },
        { choose: [
          { text: 'Then fall.', do: 'attack(); N.done = true' },
          { text: 'I carry the frost. Would you rather stand frozen?', if: "has('frost')", to: 'frost' },
          { text: 'I will go around.', to: 'end' },
        ] },
      ],
      frost: [
        { say: 'champion', text: '…The cold. I remember the cold.' },
        { say: 'champion', text: 'Pass, then. And may it find you before I do.' },
        { do: 'N.done = true; N.spared = true' },
      ],
    } },
  ],
};
