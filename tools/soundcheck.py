"""Cue timing, against a fake winsound: nothing here makes a noise.

    python tools/soundcheck.py

The two ends of the same rule: a sweep across a toolbar must go quiet, and a
slow, deliberate sequence of hovers and clicks must still all be heard.
"""

import sys
import time
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CUE_S = 0.06
played = []
fake = types.ModuleType("winsound")
fake.SND_MEMORY = fake.SND_NODEFAULT = 0


def play_sound(data, flags):
    played.append(time.time())
    time.sleep(CUE_S)


fake.PlaySound = play_sound
sys.modules["winsound"] = fake

from vertexui import sound  # noqa: E402

failed = 0


def check(name, ok, detail=""):
    global failed
    failed += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {name} {detail}")


def fresh():
    played.clear()
    s = sound.SoundSet()
    s.wav = lambda name: b""
    return s


s = fresh()
for _ in range(40):                 # 40 buttons in 400ms
    s.play("hover")
    time.sleep(0.01)
time.sleep(0.2)
check("sweep goes quiet", len(played) <= 3, f"{len(played)} cues")
last = played[-1]

s = fresh()
for _ in range(4):
    s.play("hover")
    time.sleep(0.25)
time.sleep(0.1)
check("slow hovers are all heard", len(played) == 4, f"{len(played)} cues")

s = fresh()
for _ in range(30):                 # frantic clicking
    s.play("click")
    time.sleep(0.01)
stopped = time.time()
time.sleep(0.3)
tail = played[-1] - stopped
check("nothing starts after the hand stops", tail <= sound.STALE_S, f"{tail * 1000:.0f}ms")

s = fresh()
s.play("hover")
time.sleep(0.01)
s.play("click")
time.sleep(0.2)
check("a click still follows a hover", len(played) == 2, f"{len(played)} cues")

s = fresh()
s.play("click")
time.sleep(0.01)
s._last = 0.0
s.play("hover")
time.sleep(0.2)
check("hover never waits behind a cue", len(played) == 1, f"{len(played)} cues")

for name, specs in (("soft taps", sound.DEFAULT_SPECS), ("crisp", sound.CRISP_SPECS), ("breeze", sound.BREEZE_SPECS)):
    ms = sum(seg[2] for seg in specs["hover"][0])
    check(f"{name} hover is short", ms <= 50, f"{ms}ms")

print(f"{failed} failed")
sys.exit(1 if failed else 0)
