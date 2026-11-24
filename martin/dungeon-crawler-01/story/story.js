// The game's dialogue (STORIES.story), written from the description in story/story.md. This file is the dialogue
// itself: the game plays exactly what is here. The format is in README.md, Dialogue; check it with
// `node tools/story/check.js`. Nothing is written yet: with no conversations the game behaves as before.
var STORIES = STORIES || {};
STORIES.story = {
  chars: {},
  convs: [],
};
