"""Turning numbers into something a person reads at a glance.

Three projects built their own duration formatter before this module
existed, and all three made the same two decisions: drop the units that
are zero, and never show more precision than the reader can act on. So
they are here, once.

    fmt.duration(4512)      -> "1h 15m"
    fmt.bytes(1536000)      -> "1.5 MB"
    fmt.count(28400)        -> "28.4k"
    fmt.ago(then)           -> "4 min ago"
    fmt.ellipsis(s, 180)    -> "a long label that did not fi..."

Nothing here touches ImGui except `ellipsis`, which has to measure text in
the current font.
"""

import math
import time

__all__ = ["duration", "clock", "bytes", "count", "ago", "plural", "ratio",
           "signed", "si", "ellipsis", "fit"]


def duration(seconds, parts=2, short=True):
    """A length of time, biggest units first.

    `parts` caps how many units appear: "1h 15m" rather than
    "1h 15m 12s", because the seconds are noise next to the hour.
    """
    if seconds is None:
        return "-"
    seconds = float(seconds)
    if seconds < 0:
        return "-" + duration(-seconds, parts, short)
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms" if short else "under a second"
    units = (("d", 86400), ("h", 3600), ("m", 60), ("s", 1))
    long_names = {"d": " day", "h": " hour", "m": " minute", "s": " second"}
    out, left = [], seconds
    for suffix, size in units:
        if left >= size or (out and len(out) < parts):
            n = int(left // size)
            left -= n * size
            if n or out:
                if short:
                    out.append(f"{n}{suffix}")
                else:
                    out.append(f"{n}{long_names[suffix]}" + ("s" if n != 1 else ""))
        if len(out) >= parts:
            break
    return " ".join(out) if out else ("0s" if short else "0 seconds")


def clock(seconds):
    """h:mm:ss, or m:ss under an hour - for anything counting down."""
    if seconds is None:
        return "--:--"
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def bytes(n, binary=False):            # noqa: A001 - the name people reach for
    """A size. `binary=True` uses KiB/MiB and powers of 1024."""
    if n is None:
        return "-"
    n = float(n)
    sign = "-" if n < 0 else ""
    n = abs(n)
    step = 1024.0 if binary else 1000.0
    names = ("B", "KiB", "MiB", "GiB", "TiB", "PiB") if binary else \
            ("B", "KB", "MB", "GB", "TB", "PB")
    i = 0
    while n >= step and i < len(names) - 1:
        n /= step
        i += 1
    if i == 0:
        return f"{sign}{n:.0f} {names[0]}"
    return f"{sign}{n:.1f} {names[i]}" if n < 100 else f"{sign}{n:.0f} {names[i]}"


def count(n, places=1):
    """28400 -> 28.4k. For anything that stops being read digit by digit."""
    if n is None:
        return "-"
    n = float(n)
    sign = "-" if n < 0 else ""
    n = abs(n)
    for size, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if n >= size:
            v = n / size
            return f"{sign}{v:.{places}f}".rstrip("0").rstrip(".") + suffix
    return f"{sign}{n:.0f}"


def si(value, unit="", places=2):
    """Engineering notation with an SI prefix - 0.0042 -> 4.2 m."""
    if value is None:
        return "-"
    if value == 0:
        return f"0 {unit}".strip()
    prefixes = {-9: "n", -6: "u", -3: "m", 0: "", 3: "k", 6: "M", 9: "G"}
    exp = int(math.floor(math.log10(abs(value)) / 3) * 3)
    exp = max(-9, min(9, exp))
    v = value / (10 ** exp)
    return f"{v:.{places}g} {prefixes[exp]}{unit}".strip()


def ago(when, now=None, short=True):
    """How long since a timestamp. 'just now' below five seconds, because
    '3 seconds ago' is a number nobody needed."""
    if when is None:
        return "-"
    delta = (now if now is not None else time.time()) - float(when)
    if delta < 0:
        return "in " + duration(-delta, 1, short)
    if delta < 5:
        return "just now"
    return duration(delta, 1, short) + " ago"


def plural(n, one, many=None):
    """`plural(1, "retry", "retries")` -> "1 retry"."""
    many = many if many is not None else one + "s"
    return f"{n:,} {one if abs(n) == 1 else many}"


def ratio(part, whole, places=0):
    """A percentage that does not divide by zero."""
    if not whole:
        return "-"
    return f"{part / whole * 100:.{places}f}%"


def signed(value, places=1, suffix=""):
    """Always carries its sign, so a delta reads as a direction."""
    if value is None:
        return "-"
    return f"{value:+.{places}f}{suffix}"


def ellipsis(text, max_width, tail="…"):
    """Trim to fit a pixel width in the current font.

    Measures rather than counting characters: a proportional face makes
    "WWWW" twice the width of "iiii", and a character budget truncates one
    of them far too early and the other not at all.
    """
    from imgui_bundle import imgui
    if imgui.calc_text_size(text).x <= max_width:
        return text
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if imgui.calc_text_size(text[:mid] + tail).x <= max_width:
            lo = mid
        else:
            hi = mid - 1
    return (text[:lo] + tail) if lo else tail


def fit(text, max_width, tail="…"):
    """Alias for `ellipsis`, for call sites that read better this way."""
    return ellipsis(text, max_width, tail)
