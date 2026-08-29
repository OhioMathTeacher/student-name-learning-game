"""Loading a section's photos, and remembering which section was last open.

Both screens used to carry their own copy of this, which is how they drifted:
study mode showed one part of the name while quiz mode showed both.
"""

import json
import os

IMAGE_TYPES = (".jpg", ".jpeg", ".png", ".gif", ".bmp")


def config_path():
    d = os.path.join(os.path.expanduser("~"), ".student_name_game")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "config.json")


def load_last_folder():
    try:
        with open(config_path(), encoding="utf-8") as fh:
            folder = json.load(fh).get("last_folder")
        return folder if folder and os.path.isdir(folder) else None
    except (OSError, ValueError, AttributeError):
        return None


def save_last_folder(folder):
    try:
        with open(config_path(), "w", encoding="utf-8") as fh:
            json.dump({"last_folder": folder}, fh, indent=2)
    except OSError:
        pass


def display_name(stem):
    """`Smith_Alex` -> `Alex Smith`. Files without an underscore pass through."""
    if "_" in stem:
        last, _, first = stem.partition("_")
        return f"{first} {last}".strip() if first else last
    return stem


def load(folder):
    """Every photo in `folder` as {'name', 'path', 'key'}, ordered by surname.

    Ordering is by filename, which is LastName_FirstName, so the roster reads
    like a class list instead of whatever order the filesystem returned.
    """
    if not folder or not os.path.isdir(folder):
        return []

    students = []
    for filename in sorted(os.listdir(folder), key=str.lower):
        if not filename.lower().endswith(IMAGE_TYPES):
            continue
        stem = os.path.splitext(filename)[0]
        students.append({
            "name": display_name(stem),
            "path": os.path.join(folder, filename),
            "key": stem,
        })
    return students


def sample_folder():
    """The five fictional students shipped with the app, or None if absent.

    Lets someone try the app before they have prepared a real roster -- and
    means a demo never needs student photos on screen.
    """
    import sys

    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    folder = os.path.join(base, "sample-roster")
    return folder if os.path.isdir(folder) and load(folder) else None
