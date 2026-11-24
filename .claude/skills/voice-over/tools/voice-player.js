// A reference voice-over player for a browser game (the voice-over skill; see ../SKILL.md). Copy it into the game
// and adapt; the worked example is martin/dungeon-crawler-01 (index.html, "Voice-over").
//
// It plays clips from an index made by make_voices.py (CLIPS["speaker|text"] = [file, seconds]) through Web Audio:
// one clip at a time, a short lead after the line appears, a quick fade when cut off, clips loaded ahead per
// speaker, and a clip that is still loading when its moment has passed skipped rather than played late.
//
//   const vo = voicePlayer({ ctx: audioContext, out: voicesGainNode, clips: VOICE_CLIPS });
//   vo.preload('garrick|', 'hero:');           // when a conversation with garrick starts (key prefixes)
//   const secs = vo.play('garrick|' + text);   // as the line appears: 0 if it has no clip
//   line.stays = Math.max(readingTime, secs && secs + 0.6);   // keep the line up until it has been spoken
//   vo.stop();                                 // moving on, walking away, the conversation ending
//
// Create the AudioContext in a click or key handler (browsers keep audio off until the player interacts).
function voicePlayer({ ctx, out, clips, lead = 0.25, late = 0.8, fade = 0.12 }) {
  const bufs = {};   // file -> AudioBuffer, or a Promise while it loads, or null if it failed
  let cur = null;
  const load = file => bufs[file] !== undefined ? bufs[file] : (bufs[file] = fetch(file).then(r => r.arrayBuffer())
    .then(b => new Promise((res, rej) => ctx.decodeAudioData(b, res, rej)))   // (the callback form works in old Safari too)
    .then(buf => (bufs[file] = buf)).catch(() => (bufs[file] = null)));
  function stop() {
    const v = cur; cur = null; if (!v || !v.src) return;
    try { v.g.gain.setTargetAtTime(0, ctx.currentTime, fade / 3); v.src.stop(ctx.currentTime + fade); } catch (e) {}
  }
  function play(key) {   // returns the clip's length plus the lead (s), or 0 when there is no clip
    stop(); const c = clips[key]; if (!c) return 0;
    const [file, dur] = c, v = cur = { t0: ctx.currentTime, src: null, g: null };
    const go = buf => {
      if (cur !== v || !buf || ctx.currentTime - v.t0 > late) return;   // replaced, failed, or too late now
      const s = ctx.createBufferSource(), g = ctx.createGain(); s.buffer = buf; s.connect(g); g.connect(out);
      s.start(Math.max(ctx.currentTime, v.t0 + lead)); v.src = s; v.g = g;
    };
    const b = load(file); if (b && b.then) b.then(go); else go(b);
    return dur + lead;
  }
  function preload(...prefixes) { for (const k in clips) if (prefixes.some(p => k.startsWith(p))) load(clips[k][0]); }
  return { play, stop, preload };
}
if (typeof module !== 'undefined') module.exports = { voicePlayer };
