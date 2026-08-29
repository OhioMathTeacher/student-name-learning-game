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
ACCENT = "#2F80ED"         # primary action
ACCENT_ACTIVE = "#4B94F2"
SURFACE_ACTIVE = "#2E415A"
STOP = "#C9524E"           # the one destructive/stop state
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
    """
    import os
    from tkinter import filedialog

    candidates = [
        current,
        os.path.expanduser("~/Pictures/student-headshots"),
        os.path.expanduser("~/Thumbdrive"),
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


def course_name(folder):
    """Human label for the loaded section, from its folder path.

    Handles both layouts in use:
        .../student-headshots/284              -> "284"
        .../student-headshots/318P-Oxford      -> "318P Oxford"
        .../Untitled/284/headshots             -> "284"
        .../Untitled/318P/headshots-oxford     -> "318P Hamilton"/"318P Oxford"
    """
    import os

    if not folder:
        return ""
    folder = os.path.normpath(folder)
    base = os.path.basename(folder)
    parent = os.path.basename(os.path.dirname(folder))

    if base == "headshots":
        return parent
    if base.startswith("headshots-"):
        return f"{parent} {base.split('-', 1)[1].capitalize()}".strip()
    return base.replace("-", " ").replace("_", " ")
