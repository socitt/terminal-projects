"""Terminal rendering helpers for narrow (~30-40 col) screens."""

DEFAULT_WIDTH = 36


def clear_screen():
    print("\033[2J\033[H", end="")


def pad_line(text, width=DEFAULT_WIDTH):
    """Pad or truncate text to exactly `width` characters."""
    text = text[:width]
    return text + " " * (width - len(text))


def center_line(text, width=DEFAULT_WIDTH):
    """Center text within `width` characters, padding with spaces."""
    text = text[:width]
    left = (width - len(text)) // 2
    right = width - len(text) - left
    return " " * left + text + " " * right


def hr(width=DEFAULT_WIDTH, char="-"):
    """Return a horizontal rule `width` characters wide."""
    return char * width
