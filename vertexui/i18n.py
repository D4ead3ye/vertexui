"""Strings in more than one language.

Small on purpose. A UI toolkit should not ship a translation framework,
but it should stop every project inventing the same dictionary-with-a-
fallback, and it should make the two decisions that are easy to get wrong:

  * a missing key returns the key, never an exception and never a blank.
    A panel with "orders.due" written on it is a bug you can see; one with
    an empty label is a bug you find from a screenshot three weeks later.
  * the fallback language is tried before the key is given up on, so a
    half-finished translation degrades to English rather than to debris.

    i18n.load("pt", {"save": "Salvar", "orders.due": "Vencimento"})
    i18n.use("pt")
    i18n.t("save")                       -> "Salvar"
    i18n.t("missing")                    -> "missing"
    i18n.t("greet", name="Ana")          -> formats with str.format

`t` is aliased as `tr` and `_`, so a project can use whichever reads best
at its call sites.
"""

__all__ = ["load", "use", "language", "languages", "t", "tr", "plural",
           "missing", "fallback"]

_catalogues = {}
_lang = "en"
_fallback = "en"
_missing = set()


def load(lang, strings, merge=True):
    """Add a catalogue. `strings` is a flat {key: text} mapping."""
    if merge and lang in _catalogues:
        _catalogues[lang].update(strings)
    else:
        _catalogues[lang] = dict(strings)
    return _catalogues[lang]


def use(lang):
    """Switch language. Unknown codes are kept rather than rejected, so a
    catalogue can be loaded after the preference is restored."""
    global _lang
    _lang = lang
    return _lang


def fallback(lang):
    global _fallback
    _fallback = lang
    return _fallback


def language():
    return _lang


def languages():
    return sorted(_catalogues)


def t(key, **fmt):
    """Look up `key`, falling back to the fallback language, then the key.

    Formatting failures return the unformatted string: a translator who
    typed `{nome}` where the code passes `name` should cost you a wrong
    label, not a crash in the middle of a frame.
    """
    s = _catalogues.get(_lang, {}).get(key)
    if s is None:
        s = _catalogues.get(_fallback, {}).get(key)
    if s is None:
        _missing.add(key)
        s = key
    if fmt:
        try:
            return s.format(**fmt)
        except Exception:
            return s
    return s


tr = t
_ = t


def plural(key, n, **fmt):
    """Pick `key.one` or `key.many` by count, with `{n}` available.

    Falls back to `key` itself when neither variant exists, so adding a
    plural form later is not a breaking change.
    """
    variant = f"{key}.one" if abs(n) == 1 else f"{key}.many"
    s = _catalogues.get(_lang, {}).get(variant) or \
        _catalogues.get(_fallback, {}).get(variant)
    if s is None:
        return t(key, n=n, **fmt)
    try:
        return s.format(n=n, **fmt)
    except Exception:
        return s


def missing():
    """Every key that has been asked for and not found.

    Print it at shutdown and the list of what still needs translating
    writes itself.
    """
    return sorted(_missing)
