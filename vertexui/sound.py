"""Synthesised interface sounds - no asset files to ship.

Every cue is generated as WAV bytes on first use, so a frozen one-file exe
carries no audio assets and there is nothing to lose track of.

The default set was tuned by ear over several passes, and the lessons are
baked into the synthesis rather than left as taste:

  * pitch, not volume, is what makes a cue feel sharp. Quiet high beeps
    still cut through; the whole set sits low and is filtered.
  * a falling pitch reads as a physical knock. The same tone held flat
    reads as an alert.
  * raised-cosine fades at both ends. A waveform starting or stopping at
    non-zero amplitude clicks, and that click is most of "harsh".

    from vertexui import sound
    sfx = sound.SoundSet(volume=0.16)
    sfx.play("click")
"""

import io
import math
import queue
import struct
import threading
import time
import wave


# (segments, gain) - a segment is (start Hz, end Hz, milliseconds)
DEFAULT_SPECS = {
    "hover": ([(300.0, 240.0, 40)], 0.20),
    "click": ([(360.0, 150.0, 80)], 0.60),
    "ok":    ([(262.0, 262.0, 110), (330.0, 330.0, 180)], 0.50),
    "warn":  ([(247.0, 220.0, 130), (196.0, 185.0, 200)], 0.50),
    "error": ([(165.0, 150.0, 140), (124.0, 110.0, 230)], 0.55),
    # A toast arriving and leaving. Quieter and shorter than the five
    # above, because they fire on their own rather than in reply to
    # something you did - and rising in, falling out, so the pair reads as
    # one object entering and leaving the room.
    "toast_in":  ([(300.0, 380.0, 90)], 0.34),
    "toast_out": ([(380.0, 296.0, 90)], 0.26),
}

# A brighter alternative, to show the set is data. Swap with
# SoundSet(specs=sound.CRISP_SPECS).
CRISP_SPECS = {
    "hover": ([(720.0, 640.0, 26)], 0.16),
    "click": ([(880.0, 420.0, 55)], 0.50),
    "ok":    ([(523.0, 523.0, 80), (784.0, 784.0, 130)], 0.45),
    "warn":  ([(494.0, 440.0, 100), (392.0, 370.0, 150)], 0.45),
    "error": ([(330.0, 300.0, 110), (247.0, 220.0, 180)], 0.50),
    "toast_in":  ([(660.0, 880.0, 70)], 0.32),
    "toast_out": ([(880.0, 620.0, 70)], 0.26),
}

# Every cue a set is expected to carry. A set missing one is not broken -
# play() ignores names it does not have - but a set meaning to replace the
# defaults wants all seven.
CUE_NAMES = ("hover", "click", "ok", "warn", "error", "toast_in", "toast_out")


class SoundSet:
    """A named collection of cues, rendered on demand and played async."""

    def __init__(self, specs=None, volume=0.16, enabled=True,
                 harmonic=0.06, attack_ms=14.0, release_ms=34.0,
                 lowpass_hz=900.0, rate=44100):
        self.specs = dict(specs or DEFAULT_SPECS)
        self.volume = max(0.0, min(1.0, float(volume)))
        self.enabled = bool(enabled)
        self.harmonic = harmonic        # 2nd partial: body without loudness
        self.attack_ms = attack_ms      # long enough that no cue has an onset
        self.release_ms = release_ms
        self.lowpass_hz = lowpass_hz    # only filtering truly dulls a sound
        self.rate = rate
        self._cache = {}
        self._q = None
        self._last = 0.0
        self._fails = 0

    # -- rendering ------------------------------------------------------
    def render(self, name: str) -> bytes:
        segments, gain = self.specs[name]
        rate = self.rate
        total_ms = sum(seg[2] for seg in segments)
        frames = bytearray()
        phase = 0.0
        elapsed = 0.0
        lp = 0.0
        dt = 1.0 / rate
        rc = 1.0 / (2.0 * math.pi * self.lowpass_hz)
        alpha = dt / (rc + dt)

        for f0, f1, ms in segments:
            n = max(1, int(rate * ms / 1000))
            for i in range(n):
                u = i / n
                # Integrate phase rather than evaluating sin(2*pi*f*t) with
                # a moving f - the latter warps the wave and buzzes as the
                # pitch slides.
                phase += 2.0 * math.pi * (f0 + (f1 - f0) * u) / rate
                t_ms = elapsed + i * 1000.0 / rate

                env = 1.0
                if t_ms < self.attack_ms:
                    env = 0.5 * (1.0 - math.cos(math.pi * t_ms / self.attack_ms))
                left = total_ms - t_ms
                if left < self.release_ms:
                    env *= 0.5 * (1.0 - math.cos(math.pi * left / self.release_ms))
                env *= math.exp(-2.2 * t_ms / max(1.0, total_ms))

                v = math.sin(phase) + self.harmonic * math.sin(2.0 * phase)
                v /= (1.0 + self.harmonic)
                lp += alpha * (v - lp)
                s = lp * env * gain * self.volume
                frames += struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767))
            elapsed += ms

        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(bytes(frames))
        return buf.getvalue()

    def wav(self, name: str) -> bytes:
        if name not in self._cache:
            self._cache[name] = self.render(name)
        return self._cache[name]

    # -- playback -------------------------------------------------------
    def _worker(self):
        import winsound
        while True:
            name = self._q.get()
            if name is None:
                return
            try:
                # winsound refuses SND_MEMORY together with SND_ASYNC
                # ("Cannot play asynchronously from memory"), so playback is
                # synchronous - on this thread, where blocking for the
                # 40-370ms a cue lasts costs nothing. On the UI thread it
                # would stutter every frame that made a sound.
                winsound.PlaySound(self.wav(name),
                                   winsound.SND_MEMORY | winsound.SND_NODEFAULT)
            except Exception as e:
                self._fails += 1
                if self._fails == 1:
                    print(f"Interface sounds unavailable: {e!r}")
                if self._fails >= 3:
                    self.enabled = False
                    print("Interface sounds disabled after repeated failures.")
                    return

    def play(self, name: str = "click"):
        """Queue a cue. Never blocks, never raises."""
        if not self.enabled or name not in self.specs:
            return
        now = time.time()
        # Hover fires far more often than a click and needs more spacing,
        # or sweeping a toolbar becomes a burst rather than a series.
        gap = 0.07 if name == "hover" else 0.05
        if now - self._last < gap:
            return
        self._last = now
        if self._q is None:
            self._q = queue.Queue(maxsize=2)
            threading.Thread(target=self._worker, name="vertexui-sfx",
                             daemon=True).start()
        try:
            self._q.put_nowait(name)
        except queue.Full:
            pass          # one already in flight; dropping beats lagging


_active = None


def use(sound_set: SoundSet):
    """Make this the set every widget plays from.

    A set passed here directly is the application's own choice, and
    `Settings.apply()` will not replace it - see `install()`.
    """
    global _active
    _active = sound_set
    return _active


def active_set():
    """The installed set, or None if nothing has been installed yet.

    Unlike `current()` this does not create one, which is how a caller can
    tell "no set chosen" apart from "the default set".
    """
    return _active


def current() -> SoundSet:
    """The set widgets play from. Created silent-safe on first use."""
    global _active
    if _active is None:
        _active = SoundSet()
    return _active


def play(name: str = "click"):
    current().play(name)


# --- an airy alternative -----------------------------------------------
# The set above is tonal: sine partials with a falling pitch, which is what
# makes a cue read as a knock. That is right for a tool you are actively
# clicking through, and wrong for something that sits open beside you for
# nine hours, where every notification is a small tap on the shoulder.
#
# This one is *noise*, not tone. A band of filtered noise under a slow
# raised-cosine envelope reads as breath or wind and has no attack to
# flinch at. Pitch identity - which cue was that? - comes from where the
# band sits and which way it sweeps, plus a quiet sine underneath, rather
# than from a melody.
#
# The spec shape is deliberately the same `(segments, gain)`, so everything
# that reads `specs` still works. The numbers mean something different:
# they are the centre of the noise band in Hz, not an oscillator frequency.

BREEZE_SPECS = {
    # barely there; hover fires constantly, so it has to be something you
    # notice only by its absence
    "hover": ([(2900.0, 2400.0, 90)], 0.22),
    "click": ([(2000.0, 1150.0, 150)], 0.55),
    "ok":    ([(1150.0, 2050.0, 380), (2050.0, 1500.0, 220)], 0.50),
    "warn":  ([(1600.0, 850.0, 300), (850.0, 700.0, 260)], 0.52),
    "error": ([(900.0, 430.0, 340), (430.0, 330.0, 340)], 0.58),
    "toast_in":  ([(1300.0, 2100.0, 240)], 0.30),
    "toast_out": ([(1900.0, 1150.0, 210)], 0.22),
}

BREEZE_RATE = 22050     # a noise band this soft has nothing above 11 kHz
_BLOCK = 512            # overlap-add window
_HOP = _BLOCK // 2

# Where a supplied file plays at the level it was recorded; below it the
# file is scaled down. Baking the volume slider in rather than ignoring it
# keeps one control honest for both kinds of set.
VOL_FULL = 0.6


class BreezeSet(SoundSet):
    """SoundSet with the oscillator replaced by moving air."""

    def __init__(self, specs=None, volume=0.16, enabled=True, **kw):
        kw.setdefault("rate", BREEZE_RATE)
        super().__init__(specs or BREEZE_SPECS, volume=volume,
                         enabled=enabled, **kw)
        # Long fades at both ends: an onset is the thing that makes a sound
        # feel like an alert, and a long tail is what makes it feel like it
        # belongs in the room.
        self.attack_frac = 0.28
        self.release_frac = 0.46
        self.body = 0.22          # the low sine under the noise
        self.breath_hz = 4.5      # slow shimmer, so it is not flat
        self.width = 0.62         # band width in octaves (gaussian sigma)

    def _centres(self, segments, n):
        """Band centre for every sample, in Hz, across the whole cue."""
        import numpy as np
        out = np.empty(n, np.float64)
        total = sum(seg[2] for seg in segments) or 1.0
        at = 0
        for f0, f1, ms in segments:
            k = min(max(1, int(round(n * ms / total))), n - at)
            if k <= 0:
                break
            # Interpolate in log space: pitch is logarithmic, so a linear
            # ramp from 2000 to 400 spends most of its time up high and the
            # sweep sounds like it falls off a cliff at the end.
            out[at:at + k] = np.geomspace(f0, max(f1, 1.0), k)
            at += k
        if at < n:
            out[at:] = out[at - 1] if at else segments[0][0]
        return out

    def _noise_band(self, centres, n):
        """White noise steered through a moving band, by overlap-add.

        Filtering in blocks rather than per sample is what makes this cheap
        enough to render on demand: each 512-sample window gets one real
        FFT, a gaussian gain curve around that window's centre frequency,
        and one inverse.
        """
        import numpy as np
        rng = np.random.default_rng(20250907)
        pad = n + _BLOCK * 2
        src = rng.standard_normal(pad)
        out = np.zeros(pad)
        win = np.hanning(_BLOCK)
        freqs = np.fft.rfftfreq(_BLOCK, 1.0 / self.rate)
        lf = np.log2(np.maximum(freqs, 1.0))   # guard the DC bin
        for start in range(0, n + _BLOCK, _HOP):
            block = src[start:start + _BLOCK]
            if len(block) < _BLOCK:
                break
            c = centres[min(start, n - 1)]
            gain = np.exp(-0.5 * ((lf - np.log2(c)) / self.width) ** 2)
            gain[0] = 0.0                      # no DC offset, ever
            out[start:start + _BLOCK] += np.fft.irfft(
                np.fft.rfft(block * win) * gain, _BLOCK)
        band = out[:n]
        return band / (float(np.max(np.abs(band))) or 1.0)

    def render(self, name: str) -> bytes:
        import numpy as np
        segments, gain = self.specs[name]
        total_ms = sum(seg[2] for seg in segments)
        n = max(1, int(self.rate * total_ms / 1000.0))
        t = np.arange(n) / self.rate

        centres = self._centres(segments, n)
        sig = self._noise_band(centres, n)

        # A quiet sine well below the band gives the cue a pitch you can
        # name. Without it every cue is a soft hiss and they differ only in
        # length.
        if self.body > 0.0:
            phase = 2.0 * np.pi * np.cumsum(centres / 6.0) / self.rate
            sig = (sig + self.body * np.sin(phase)) / (1.0 + self.body)

        env = np.ones(n)
        na = max(1, int(n * self.attack_frac))
        nr = max(1, int(n * self.release_frac))
        env[:na] = 0.5 * (1.0 - np.cos(np.pi * np.arange(na) / na))
        env[n - nr:] = 0.5 * (1.0 + np.cos(np.pi * np.arange(nr) / nr))
        env *= 1.0 + 0.12 * np.sin(2.0 * np.pi * self.breath_hz * t)

        pcm = (np.clip(sig * env * gain * self.volume, -1.0, 1.0)
               * 32767.0).astype("<i2")
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.rate)
            w.writeframes(pcm.tobytes())
        return buf.getvalue()


def cues_dir(app: str = "vertexui"):
    """Where a user drops their own cues."""
    from pathlib import Path

    from . import settings as _settings          # lazy: settings imports us
    return Path(_settings.config_dir(app)) / "sounds"


class FileSet(SoundSet):
    """Plays `<cue>.wav` from a folder, per cue, with a fallback.

    Per cue, not all-or-nothing: replacing just the click and leaving the
    rest synthesised is the common case, and a set that stayed silent until
    all seven files existed would be useless for it.
    """

    def __init__(self, folder=None, app="vertexui", volume=0.16,
                 enabled=True, fallback=None, **kw):
        super().__init__({k: ([], 1.0) for k in CUE_NAMES},
                         volume=volume, enabled=enabled, **kw)
        from pathlib import Path
        self.folder = Path(folder) if folder else cues_dir(app)
        self.fallback = fallback or BreezeSet(volume=volume, enabled=enabled)
        self.bad = {}                 # cue -> why the file was unusable

    def path(self, name):
        return self.folder / f"{name}.wav"

    def found(self):
        """{cue: True/False} - what a settings panel reports."""
        return {n: self.path(n).is_file() for n in CUE_NAMES}

    def _scaled(self, raw: bytes) -> bytes:
        """Apply the volume slider to a supplied file.

        Only 16-bit PCM is rescaled; anything else is passed through
        untouched rather than mangled, because winsound will happily play a
        great many things this code has no business rewriting.
        """
        import numpy as np
        with wave.open(io.BytesIO(raw)) as w:
            p = w.getparams()
            frames = w.readframes(w.getnframes())
        gain = max(0.0, min(1.0, self.volume / VOL_FULL))
        if p.sampwidth == 2 and gain < 0.999:
            a = np.frombuffer(frames, "<i2").astype(np.float32) * gain
            frames = np.clip(a, -32768, 32767).astype("<i2").tobytes()
        out = io.BytesIO()
        with wave.open(out, "wb") as w:
            w.setnchannels(p.nchannels)
            w.setsampwidth(p.sampwidth)
            w.setframerate(p.framerate)
            w.writeframes(frames)
        return out.getvalue()

    def render(self, name: str) -> bytes:
        p = self.path(name)
        if p.is_file():
            try:
                data = self._scaled(p.read_bytes())
                self.bad.pop(name, None)
                return data
            except Exception as exc:
                # A file that is not really a WAV - an mp3 renamed, or
                # 24-bit out of an editor - must not take the interface
                # silent.
                self.bad[name] = f"{type(exc).__name__}: {exc}"
        self.fallback.volume = self.volume
        return self.fallback.render(name)

    def export(self) -> int:
        """Write the synthesised cues into the folder as starter files.

        Hearing the shape you are replacing is most of knowing what to
        record, and it saves guessing at the file names.
        """
        self.folder.mkdir(parents=True, exist_ok=True)
        ref = BreezeSet(volume=VOL_FULL)
        n = 0
        for name in CUE_NAMES:
            dst = self.path(name)
            if dst.exists():
                continue
            dst.write_bytes(ref.render(name))
            n += 1
        self._cache.clear()
        return n

    def reveal(self):
        """Open the folder in the file manager."""
        import os
        self.folder.mkdir(parents=True, exist_ok=True)
        os.startfile(str(self.folder))       # noqa - Windows only


# Named sets a settings panel can offer. Add your own by putting a factory
# in here; `install()` and the settings panel pick it up with no other
# change.
SETS = {
    "soft taps": lambda **kw: SoundSet(DEFAULT_SPECS, **kw),
    "breeze": lambda **kw: BreezeSet(**kw),
    "crisp": lambda **kw: SoundSet(CRISP_SPECS, **kw),
    "custom .wav": lambda **kw: FileSet(**kw),
}
SET_ORDER = ["soft taps", "breeze", "crisp", "custom .wav"]
CUSTOM_SET = "custom .wav"
DEFAULT_SET = "soft taps"


def install(name: str, volume: float = 0.16, enabled: bool = True, **kw):
    """Make the named set from `SETS` the one every widget plays from.

    The instance is tagged with the name it came from, which is what lets
    `Settings.apply()` tell a set it chose from one the application built
    and installed itself - and leave the latter alone.
    """
    make = SETS.get(name) or SETS[DEFAULT_SET]
    if name != CUSTOM_SET:
        kw.pop("app", None)          # only FileSet knows what to do with it
    s = make(volume=volume, enabled=enabled, **kw)
    s.set_name = name
    return use(s)
