"""Cut the AI-voiced ghoul sounds into short clips for the game.

Usage:  python tools/cut_sfx.py            (run from the game folder; needs NumPy and ffmpeg)

The raw takes (tools/raw/sfx/*.wav, 24 kHz mono) are Google gemini-3.8-flash-lite-tts with wordless text and a
style prompt (see README "Sound"). Each take holds one to three moans or grunts separated by quiet gaps; every
part louder than -30 dB and longer than 0.25 s becomes a clip, trimmed with 40 ms of fade in and 120 ms of fade
out, peak-normalised to -1 dB, and saved as assets/sfx/<name><n>.mp3 (64 kbit/s mono).
"""
import pathlib, subprocess, wave
import numpy as np

GAME = pathlib.Path(__file__).parent.parent
RAW = GAME / "tools" / "raw" / "sfx"
OUT = GAME / "assets" / "sfx"
TAKES = {"moan": ["moan1.wav", "moan2.wav"], "grunt": ["grunt.wav"]}


def parts(a, sr):
    win = sr // 50
    env = np.array([np.sqrt((a[i:i + win] ** 2).mean()) for i in range(0, len(a) - win, win)])
    loud = env > env.max() * 10 ** (-30 / 20)
    out, start = [], None
    for i, l in enumerate(np.append(loud, False)):
        if l and start is None: start = i
        if not l and start is not None:
            if (i - start) * win > 0.25 * sr: out.append((start * win, i * win))
            start = None
    # merge parts closer than 0.15 s (one moan with a breath in it)
    merged = []
    for s, e in out:
        if merged and s - merged[-1][1] < 0.15 * sr: merged[-1] = (merged[-1][0], e)
        else: merged.append((s, e))
    return merged


def main():
    OUT.mkdir(exist_ok=True)
    for name, files in TAKES.items():
        n = 0
        for f in files:
            w = wave.open(str(RAW / f)); sr = w.getframerate()
            a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
            for s, e in parts(a, sr):
                c = a[s:e].copy(); fi, fo = int(0.04 * sr), int(0.12 * sr)
                c[:fi] *= np.linspace(0, 1, fi); c[-fo:] *= np.linspace(1, 0, fo)
                c *= 10 ** (-1 / 20) / np.abs(c).max()
                n += 1
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-",
                                "-b:a", "64k", str(OUT / f"{name}{n}.mp3")], input=c.tobytes(), check=True)
                print(f"{name}{n}.mp3  {(e - s) / sr:.2f} s")


if __name__ == "__main__":
    main()
