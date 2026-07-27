"""Single-key input helper for narrow terminals with no physical
keyboard (iOS on-screen keyboard only): reads a line via `input()` and
acts on its first character, since raw single-char reads and
arrow-key/modifier chords aren't reliably available in this
environment.
"""


def normalize_key(raw):
    """Return the first non-whitespace character of `raw`, lowercased.

    Returns "" if `raw` has no non-whitespace characters.
    """
    stripped = raw.strip()
    return stripped[0].lower() if stripped else ""


def get_key(prompt=""):
    """Prompt for a line of input and return its normalized first key."""
    return normalize_key(input(prompt))


def prompt_choice(prompt, choices):
    """Repeatedly prompt until a key in `choices` is entered.

    `choices` is an iterable of single lowercase characters.
    """
    choices = set(choices)
    while True:
        key = get_key(prompt)
        if key in choices:
            return key
