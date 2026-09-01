"""Shared look and feel for the Student Name apps.

Quiz mode and study mode are two windows of one tool, so the palette, the
type scale and the buttons live here rather than being redefined (and drifting
apart) in each file.
"""

import tkinter as tk

# Palette: one dark ground, one raised surface, one accent. Everything else is
# text at three weights of emphasis.
BG = "#1B2733"             # window background
SURFACE = "#243447"        # cards, photo mat, secondary buttons
BORDER = "#354A63"         # hairlines
TEXT = "#E9EEF4"           # primary text
MUTED = "#93A6BA"          # captions, hints, shortcuts
ACCENT = "#4C9AFF"         # primary action -- lifted to read against the navy
ACCENT_ACTIVE = "#6FAEFF"
SURFACE_ACTIVE = "#2E415A"
OK = "#3FB068"             # correct answer
HINT = "#E0B341"           # hint text
STOP = "#C9524E"           # wrong answer, stop states
STOP_ACTIVE = "#D96460"

FAMILY = "Helvetica"       # Tk maps this to a sane sans on every platform

# Type scale. Quiz mode set the precedent at 14/16, so study mode follows it
# rather than running at its own much larger sizes.
SIZE_TITLE = 16     # window heading
SIZE_FEATURE = 20   # the student's name -- the one thing meant to dominate
SIZE_INPUT = 16     # entry field
SIZE_LABEL = 14     # field labels, streak line, feedback
SIZE_BODY = 12      # captions, counters, secondary controls
SIZE_SMALL = 11     # shortcut hints


def font(size, weight="normal"):
    return (FAMILY, size, weight)


def button(parent, text, command, primary=False, **kw):
    """A flat, evenly padded button.

    primary=True fills with the accent; otherwise it sits on the surface colour
    with a hairline border. Flat beats the old raised 3px bevel, which read as
    a 1990s dialog once the display scaling made it three pixels of chrome.
    """
    return tk.Button(
        parent,
        text=text,
        command=command,
        font=font(13, "bold"),
        bg=ACCENT if primary else SURFACE,
        fg=TEXT,
        activebackground=ACCENT_ACTIVE if primary else SURFACE_ACTIVE,
        activeforeground=TEXT,
        relief=tk.FLAT,
        bd=0,
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=BORDER,
        padx=18,
        pady=10,
        cursor="hand2",
        **kw
    )


def label(parent, text="", size=13, weight="normal", fg=None, **kw):
    return tk.Label(
        parent,
        text=text,
        font=font(size, weight),
        bg=kw.pop("bg", BG),
        fg=fg or TEXT,
        **kw
    )


def ask_folder(parent, current=None, title="Select folder with student photos"):
    """Folder picker that opens somewhere useful and stays in front.

    Without an initialdir Tk starts wherever the process was launched, which
    for these apps is the source folder. Without a parent the dialog can open
    behind the main window and look like the button did nothing.

    A mounted thumbdrive comes before anything under home, because that is
    where the photos actually live and Tk's folder chooser offers no sidebar
    of volumes to reach it with -- it opened under home, and getting to
    /run/media or a drive letter from there meant climbing to the filesystem
    root by hand. `~/Thumbdrive`, which this used to reach for, is not a real
    path on any of the three platforms.
    """
    import os
    from tkinter import filedialog

    import roster

    candidates = [
        current,
        *roster.removable_roots(),
        os.path.expanduser("~/Pictures/student-headshots"),
        os.path.expanduser("~"),
    ]
    initial = next((c for c in candidates if c and os.path.isdir(c)), None)

    return filedialog.askdirectory(
        parent=parent, title=title, initialdir=initial, mustexist=True
    )


PHOTO_BOX = 320  # every photo renders into a square of exactly this size


def photo(path, box=PHOTO_BOX, bg=SURFACE):
    """Render any image into a fixed square so the layout never shifts.

    The source photos are a mix of sizes (128 to 325 px square in practice) and
    PIL's thumbnail() only ever shrinks, so each student used to arrive at a
    different size and the window resized under the reader. Here the image is
    scaled to fit -- up or down -- and centred on a mat of the exact box size.
    """
    from PIL import Image, ImageTk

    img = Image.open(path).convert("RGB")
    scale = min(box / img.width, box / img.height)
    img = img.resize(
        (max(1, round(img.width * scale)), max(1, round(img.height * scale))),
        Image.Resampling.LANCZOS,
    )
    mat = Image.new("RGB", (box, box), bg)
    mat.paste(img, ((box - img.width) // 2, (box - img.height) // 2))
    return ImageTk.PhotoImage(mat)


# One window size for both modes, so switching between them does not resize.
WINDOW_W = 960
WINDOW_H = 1040


def hints_path():
    import os
    d = os.path.join(os.path.expanduser("~"), ".student_name_game")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "hints.json")


def load_hints():
    """Memory hints Todd writes in study mode, keyed by photo filename stem."""
    import json
    import os

    p = hints_path()
    if not os.path.exists(p):
        return {}
    try:
        with open(p, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (ValueError, OSError):
        return {}


def save_hint(key, text):
    import json

    hints = load_hints()
    text = (text or "").strip()
    if text:
        hints[key] = text
    else:
        hints.pop(key, None)
    try:
        with open(hints_path(), "w", encoding="utf-8") as fh:
            json.dump(hints, fh, indent=2, sort_keys=True)
    except OSError:
        pass
    return hints


def hint_key(filepath):
    """Stable per-student key: the filename stem, e.g. Smith_Alex."""
    import os

    return os.path.splitext(os.path.basename(filepath))[0]


def fit_window(root, min_w=None, min_h=None):
    """Give every window the same size and the same place on screen.

    Size: WINDOW_W x WINDOW_H, grown only if the content genuinely needs more,
    so quiz mode and study mode match and switching between them does not
    resize.

    Position: computed the same way every launch, so the window always opens
    where you last saw it rather than wandering. Deliberately NOT remembered
    between runs: this window manager reports a position ~870px away from the
    one it was given, so saving and restoring that value walked the window
    down the screen a little further on every launch.
    """
    min_w = WINDOW_W if min_w is None else min_w
    min_h = WINDOW_H if min_h is None else min_h

    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    w = min(max(root.winfo_reqwidth(), min_w), sw - 80)
    h = min(max(root.winfo_reqheight(), min_h), sh - 120)

    root.geometry(f"{w}x{h}+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 2)}")
    root.minsize(min(min_w, w), min(min_h, h))


def _scores_path():
    import os
    d = os.path.join(os.path.expanduser("~"), ".student_name_game")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "scores.json")


def load_scores():
    """{section: {'last': n, 'best': n}} from finished quiz runs."""
    import json
    import os

    p = _scores_path()
    if not os.path.exists(p):
        return {}
    try:
        with open(p, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_score(section, streak):
    """Record a finished run: its streak, and the best seen for that section."""
    import json

    if not section:
        return
    scores = load_scores()
    entry = scores.get(section) or {}
    entry["last"] = int(streak)
    entry["best"] = max(int(streak), int(entry.get("best", 0)))
    scores[section] = entry
    try:
        with open(_scores_path(), "w", encoding="utf-8") as fh:
            json.dump(scores, fh, indent=2, sort_keys=True)
    except OSError:
        pass
