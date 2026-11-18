"""Render the committed default guide set into ../guides/ (run from anywhere; ~5 min with 6 processes).

  python default_guides.py [--only walk,jog] [--jobs 6]

Mocap guides (render_guide.py --shaded, adult 1.82 m, EU 43 feet), every direction, at the exact size they are painted:
  guides/<clip>/8f/<DIR>.png    4 x 2, 1536 x 1024 (cells 384 x 512)
  guides/<clip>/12f/<DIR>.png   6 x 2, 2304 x 1024 (cells 384 x 512; narrower cells cut off wide strides)
for clip = walk (Walk_Loop), formal-walk (Walk_Formal_Loop), jog (Jog_Fwd_Loop). Row 1 is the first step, row 2 the
second. render_guide shrinks a wide-striding clip (jog) so it keeps 16 px from its cell sides.
Stick-figure guides (walk_cycle.py guide hero <DIR> --magenta --limbs, colour per limb, 4 x 2, 1200 x 880):
  guides/stick-walk/8f/<DIR>.png for the five base directions (the script draws only S SW W NW N).
"""
import subprocess, sys, pathlib
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent / "guides"
GLB = HERE.parent / "datasets" / "quaternius-ual1" / "UAL1_Standard.glb"
CLIPS = {"walk": "Walk_Loop", "formal-walk": "Walk_Formal_Loop", "jog": "Jog_Fwd_Loop"}
LAYOUT = {8: ("4", "384x512"), 12: ("6", "384x512")}
DIRS = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]
BASE = ["S", "SW", "W", "NW", "N"]


def jobs(only):
    for name, clip in CLIPS.items():
        if only and name not in only:
            continue
        for n, (cols, cell) in LAYOUT.items():
            for d in DIRS:
                out = ROOT / name / f"{n}f" / f"{d}.png"
                yield out, [sys.executable, str(HERE / "render_guide.py"), str(GLB), d, str(out), "--shaded",
                            "--clip", clip, "--frames", str(n), "--cols", cols, "--cell", cell]
    if not only or "stick-walk" in only:
        for d in BASE:
            out = ROOT / "stick-walk" / "8f" / f"{d}.png"
            yield out, [sys.executable, str(HERE / "walk_cycle.py"), "guide", "hero", d, str(out), "--magenta", "--limbs"]


def run(job):
    out, cmd = job
    out.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    return out, r.returncode, (r.stderr or "")[-300:]


if __name__ == "__main__":
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
    n = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 6
    with ThreadPoolExecutor(n) as ex:
        for out, rc, err in ex.map(run, list(jobs(only))):
            print("ok " if rc == 0 else "FAIL", out.relative_to(ROOT), "" if rc == 0 else err)
