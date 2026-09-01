"""One folder of photos, each named for the student and the class.

    Ryan_Wagers_318P_Oxford.jpg

Everything the app needs is in that name: who it is, which course, which
campus. So there is one folder, not a tree, and picking a class is a filter
over what is already loaded rather than a different folder to go and find.

What this replaced was a layout -- `<root>/318P/headshots-oxford` -- that made
the app carry a photo root, a section folder, a naming convention for section
folders, and a discovery walk to find them. Four ideas to express one thing,
and every one of them a way to point at the wrong folder.
"""

import json
import os
import re
import sys

IMAGE_TYPES = (".jpg", ".jpeg", ".jpe", ".jfif", ".png", ".gif", ".bmp", ".webp",
               ".tif", ".tiff")

# Formats Pillow will not open without an extra plugin. Recognised only so the
# folder report can name them, rather than calling an iPhone photo "not an image".
UNREADABLE_TYPES = (".heic", ".heif", ".avif")

FOLDER_NAME = "student-photos"

# Never worth walking into looking for photos. A thumbdrive carries music and
# Windows bookkeeping too, and those run to thousands of entries apiece.
SKIP_DIRS = {"music", "system volume information", "winpython", "$recycle.bin",
             "found.000", "node_modules", "__pycache__"}


def sniff(path):
    """The image format of `path` read from its first bytes, as an extension.

    Needed because the registrar serves photos from URLs carrying no extension,
    so a browser-saved roster writes them to disk as bare `photo_12345`.
    """
    try:
        with open(path, "rb") as fh:
            head = fh.read(32)
    except OSError:
        return None

    if head.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if head.startswith(b"BM"):
        return ".bmp"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ".webp"
    if head.startswith((b"II*\x00", b"MM\x00*")):
        return ".tif"
    if head[4:8] == b"ftyp" and head[8:12] in (b"heic", b"heix", b"mif1", b"avif"):
        return ".heic"
    return None


def is_photo(path, filename):
    """Whether to treat this directory entry as a student photo.

    Extension first, because it is free; file contents only when the name gives
    nothing to go on. macOS writes a `._Name.jpg` companion beside every file on
    a FAT-formatted thumbdrive -- those match the extension test but hold no
    image, so they are dropped by name before anything reads them.
    """
    if filename.startswith(".") or filename.startswith("._"):
        return False
    if not os.path.isfile(path):
        return False

    extension = os.path.splitext(filename)[1].lower()
    if extension in IMAGE_TYPES:
        return True
    if extension:
        # A stated extension is taken at its word. Opening every .zip and .dmg
        # to look at its first bytes cost nine seconds on a cold thumbdrive.
        return False
    return sniff(path) in IMAGE_TYPES


# -- the filename -----------------------------------------------------------

def clean(part):
    """A name part fit for a filename field.

    Underscores go because they separate the fields; the characters after them
    go because Windows will not have them in a filename. Spaces stay -- "Mary
    Jane" is a first name, and mangling it to `Mary-Jane` would come back out
    of `display_name` wrong.
    """
    return re.sub(r'[\\/:*?"<>|_]', " ", part or "").strip()


def filename(first, last, course, location, extension=".jpg"):
    """`Ryan_Wagers_318P_Oxford.jpg`, with each field cleaned of separators."""
    fields = [clean(first), clean(last), clean(course), clean(location)]
    while fields and not fields[-1]:
        fields.pop()
    return "_".join(fields) + extension


def parse(name):
    """A photo filename back into {'first', 'last', 'course', 'location'}.

    Four fields is what Roster Prep writes. Three -- no campus known -- and two
    -- a photo somebody named by hand -- are read as far as they go, because
    refusing to show a photo whose name is short is worse than showing it with
    no class attached.
    """
    stem = os.path.splitext(name)[0]
    fields = [f.strip() for f in stem.split("_")]
    fields += [""] * (4 - len(fields))
    first, last, course, location = fields[:4]
    if len(stem.split("_")) == 1:            # no underscore at all: one name
        first, last = "", stem.strip()
    return {"first": first, "last": last, "course": course, "location": location}


def class_of(record):
    """`318P Oxford`, the label a class is picked by. Empty if the name said none."""
    return f"{record['course']} {record['location']}".strip()


def display_name(record):
    """`Ryan Wagers`. A photo with only one name shows that name."""
    return f"{record['first']} {record['last']}".strip()


def sort_key(student):
    """By surname, so a class reads like a class list."""
    return (student["last"].lower(), student["first"].lower())


def load(folder):
    """Every photo in `folder`, as student records ordered by surname.

    One flat folder holding every class. Filtering to one of them is `in_class`,
    over this list -- nothing goes back to disk to change class.
    """
    if not folder or not os.path.isdir(folder):
        return []
    try:
        entries = os.listdir(folder)
    except OSError:
        return []

    students = []
    for name in entries:
        path = os.path.join(folder, name)
        if not is_photo(path, name):
            continue
        record = parse(name)
        record["path"] = path
        record["key"] = os.path.splitext(name)[0]   # what a saved hint is filed under
        record["name"] = display_name(record)
        record["label"] = class_of(record)
        students.append(record)
    return sorted(students, key=sort_key)


def classes(students):
    """Every class present, as labels, in the order they should be offered."""
    seen = {s["label"] for s in students if s["label"]}
    return sorted(seen, key=str.lower)


def in_class(students, label):
    """The students in one class, or all of them when `label` is falsy."""
    if not label:
        return list(students)
    return [s for s in students if s["label"] == label]


# -- where the folder is ----------------------------------------------------

def config_path():
    d = os.path.join(os.path.expanduser("~"), ".student_name_game")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "config.json")


def _read_config():
    try:
        with open(config_path(), encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_config(**updates):
    data = _read_config()
    data.update(updates)
    try:
        with open(config_path(), "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
    except OSError:
        pass


def load_folder():
    folder = _read_config().get("folder")
    return folder if folder and os.path.isdir(folder) else None


def save_folder(folder):
    _write_config(folder=folder)


def load_last_class():
    return _read_config().get("last_class") or ""


def save_last_class(label):
    _write_config(last_class=label or "")


def removable_roots():
    """Every mounted drive that is not the system disk, best guess first.

    The photos travel on a thumbdrive, and where that appears is entirely a
    matter of platform: `/Volumes/NAME` on a Mac, `/run/media/todd/NAME` or
    `/media/todd/NAME` on Linux, a bare drive letter on Windows.
    """
    import glob
    import string

    found = []

    def offer(path):
        if (path and os.path.isdir(path) and path not in found
                and os.path.basename(path.rstrip(os.sep)).lower() not in SKIP_DIRS):
            found.append(path)

    if sys.platform == "darwin":
        for volume in sorted(glob.glob("/Volumes/*")):
            offer(volume)
    elif os.name == "nt":
        for letter in string.ascii_uppercase[3:]:      # D: onward; C: is the system disk
            offer(f"{letter}:\\")
    else:
        user = os.path.basename(os.path.expanduser("~"))
        # Per-user mounts first: that is where a desktop actually mounts a
        # thumbdrive. Bare /media/* last, because it also holds fixed disks.
        for pattern in (f"/run/media/{user}/*", f"/media/{user}/*", "/media/*"):
            for volume in sorted(glob.glob(pattern)):
                offer(volume)
    return found


def candidate_folders():
    """Where the photo folder might be, best guess first.

    A thumbdrive that moves between a Mac and a Windows lab machine mounts at a
    different path on each, so a remembered absolute path is a hint rather than
    an answer -- hence looking again at whatever is mounted now.
    """
    found, seen = [], set()

    def offer(path):
        if path and os.path.isdir(path) and path not in seen:
            seen.add(path)
            found.append(path)

    offer(load_folder())
    for volume in removable_roots():
        offer(os.path.join(volume, FOLDER_NAME))
    offer(os.path.join(os.path.expanduser("~"), "Pictures", FOLDER_NAME))
    offer(os.path.join(os.path.expanduser("~"), FOLDER_NAME))
    return found


def find_folder():
    """The first candidate folder that actually holds photos."""
    for folder in candidate_folders():
        if load(folder):
            return folder
    return None


def default_folder():
    """Where to write photos when nothing has been chosen yet.

    The thumbdrive if one is mounted -- the photos travel between a laptop and
    a lab machine, and that is what the drive is for -- otherwise under
    Pictures.
    """
    volumes = removable_roots()
    base = volumes[0] if volumes else os.path.join(os.path.expanduser("~"), "Pictures")
    return os.path.join(base, FOLDER_NAME)


def sample_folder():
    """The five fictional students shipped with the app, or None if absent.

    Lets someone try the app before they have prepared a real roster -- and
    means a demo never needs student photos on screen.
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    folder = os.path.join(base, "sample-roster")
    return folder if os.path.isdir(folder) and load(folder) else None


def describe(folder):
    """Why `folder` produced no photos, in a sentence worth showing the user."""
    if not folder:
        return "No folder was chosen."
    if not os.path.isdir(folder):
        return "That folder no longer exists."
    try:
        entries = sorted(os.listdir(folder), key=str.lower)
    except OSError as exc:
        return f"That folder could not be read.\n\n{exc}"

    files = [f for f in entries
             if os.path.isfile(os.path.join(folder, f)) and not f.startswith(".")]
    unreadable = [f for f in files
                  if os.path.splitext(f)[1].lower() in UNREADABLE_TYPES]
    subfolders = [f for f in entries
                  if os.path.isdir(os.path.join(folder, f)) and not f.startswith(".")]
    withphotos = [f for f in subfolders if load(os.path.join(folder, f))]

    if withphotos:
        listed = ", ".join(withphotos[:6]) + ("..." if len(withphotos) > 6 else "")
        return ("That folder holds other folders rather than photos.\n\n"
                f"Choose one of these instead: {listed}")
    if unreadable:
        return (f"{len(unreadable)} of those files are HEIC/AVIF photos, which "
                "this app cannot open yet.\n\nRe-save them as JPEG and try again.")
    if not files:
        return "That folder is empty."
    return (f"{len(files)} files are there, but none of them are images this app "
            "can read.\n\nIf your photos are in a subfolder, choose that instead.")
