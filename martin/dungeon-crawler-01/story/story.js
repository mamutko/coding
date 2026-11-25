// The game's dialogue (STORIES.story), written from the description in story/story.md. This file is the dialogue
// itself: the game plays exactly what is here. The format is in README.md, Dialogue; check it with
// `node tools/story/check.js`; its voice clips are made with `node tools/story/voice.js`.
var STORIES = STORIES || {};
STORIES.story = {
  chars: {
    // Garrick, the hunter at the crypt (the surface, a few steps from the crypt's door)
    garrick: { name: 'Garrick the Hunter', wander: true, nodes: {
      '@leave': [ { say: 'garrick', text: 'Mind the dark, then.' } ],
      '@back': [ { say: 'garrick', text: 'Where were we, traveller?' } ],
    } },
  },

  // the voices the lines are spoken in (tools/story/voice.js; README, Dialogue: Voice-over)
  voices: {
    garrick: { voice: 'ash', style: 'A weathered hunter in his fifties: low, gravelly, unhurried, a rural northern English accent; dry humour with warmth underneath. Speak quietly, as if outdoors at dusk.' },
    hero: {
      m: { voice: 'echo', style: 'A young adventurer, male: steady, earnest, a little wary. Natural and quiet, not theatrical.' },
      f: { voice: 'shimmer', style: 'A young adventurer, female: steady, earnest, a little wary. Natural and quiet, not theatrical.' },
    },
  },

  convs: [
    // the first meeting: he calls out and walks over
    { id: 'garrick-first', who: 'garrick', hail: 5, walkUp: true, nodes: {
      start: [
        { say: 'garrick', text: "Hold there, traveller. You've the look of someone about to do something foolish." },
        { say: 'garrick', text: "That's the Crypt of Endless Night. Folk go down those stairs. Few come back up." },
        { say: 'garrick', text: "If you're set on it, take this. Read it aloud down there, and it'll carry you back up into the light." },
        { do: "give('escape', 1); N.scroll = true" },
        { say: 'garrick', text: "Mind, it takes a few breaths to read. Don't leave it till you're bleeding out." },
        { go: 'garrick-ask' },
      ],
    } },
    // later: on a click
    { id: 'garrick-again', who: 'garrick', when: "met('garrick')", repeat: true, nodes: {
      start: [
        { say: 'garrick', text: 'Back again, traveller? Still in one piece, I see. Good.' },
        { go: 'garrick-ask' },
      ],
    } },
    // the questions (never starts by itself: the two above jump here)
    { id: 'garrick-ask', who: 'garrick', when: 'false', repeat: true, nodes: {
      start: [
        { choose: [
          { text: "What's down there?", to: 'below' },
          { text: 'Have you been inside?', to: 'inside' },
          { text: 'Any advice?', to: 'advice' },
          { text: 'Can you help me?', if: '!N.potion', to: 'help' },
          { text: 'Could you spare another potion?', if: 'N.potion', to: 'more' },
          { text: 'Do you have another of those scrolls?', if: "N.scroll && !has('escape') && !has('return')", to: 'scroll' },
          { text: 'Goodbye.', to: 'bye' },
        ] },
      ],
      below: [
        { say: 'garrick', text: "Only stories. The dead don't rest easy down there. Things that walk, things that crawl." },
        { say: 'garrick', text: "Worse, the deeper you go. And a dark that eats the light. That's all I know, and I'd rather not know more." },
        { go: 'start' },
      ],
      inside: [
        { say: 'garrick', text: 'Once. As far as the first stair. That was far enough.' },
        { say: 'garrick', text: 'I heard something breathing down there. Something big.' },
        { go: 'start' },
      ],
      advice: [
        { say: 'garrick', text: "Keep a wall at your back. Don't take them all on at once." },
        { say: 'garrick', text: "And not everything in the dark wants you dead. Some of it would rather trade." },
        { go: 'start' },
      ],
      help: [
        { say: 'garrick', text: "Here. Brewed it myself, from the moss on the north stones. It'll close a wound or two." },
        { do: "give('health', 1); N.potion = true" },
        { go: 'start' },
      ],
      scroll: [
        { say: 'garrick', text: "Used it already? Good. It means you came back. Here's another." },
        { do: "give('escape', 1)" },
        { say: 'garrick', text: "The keepers below sell them too, I hear, for those who can pay." },
        { go: 'start' },
      ],
      more: [
        { say: 'garrick', text: "That was the only one I could spare, traveller. The rest are for my own hide." },
        { go: 'start' },
      ],
      bye: [
        { say: 'garrick', text: "Luck go with you, then. I'd like to see you come back out." },
      ],
    } },
  ],
};
