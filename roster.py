"""Loading a section's photos, and remembering which section was last open.

Both screens used to carry their own copy of this, which is how they drifted:
study mode showed one part of the name while quiz mode showed both.
"""

import json
import os

IMAGE_TYPES = (".jpg", ".jpeg", ".jpe", ".jfif", ".png", ".gif", ".bmp", ".webp",
               ".tif", ".tiff")

# Formats Pillow will not open without an extra plugin. Recognised only so the
# folder report can name them, rather than calling an iPhone photo "not an image".
UNREADABLE_TYPES = (".heic", ".heif", ".avif")


def sniff(path):
    """The image format of `path` read from its first bytes, as an extension.

    Needed because the registrar serves photos from URLs carrying no extension,
    so a browser-saved roster writes them to disk as bare `photo_12345`. Rosters
    prepared before that was handled hold whole folders of extensionless files;
    they are real JPEGs, and skipping them was why a folder full of photos
    reported "No photos found in that folder."
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
        # to look at its first bytes cost nine seconds on a cold thumbdrive,
        # which is most of a section menu's budget spent proving that a disk
        # image is not a headshot.
        return False
    return sniff(path) in IMAGE_TYPES


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
    """Merge into config.json rather than replacing it.

    The file holds the photo root as well as the last section now, and writing
    one key used to clobber the other.
    """
    data = _read_config()
    data.update(updates)
    try:
        with open(config_path(), "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
    except OSError:
        pass


def load_last_folder():
    folder = _read_config().get("last_folder")
    return folder if folder and os.path.isdir(folder) else None


def save_last_folder(folder):
    _write_config(last_folder=folder)


def load_photo_root():
    """The folder holding one subfolder per class. See `discover`."""
    root = _read_config().get("photo_root")
    return root if root and os.path.isdir(root) else None


def save_photo_root(root):
    _write_config(photo_root=root)


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

    try:
        entries = sorted(os.listdir(folder), key=str.lower)
    except OSError:
        return []

    students = []
    for filename in entries:
        path = os.path.join(folder, filename)
        if not is_photo(path, filename):
            continue
        stem = os.path.splitext(filename)[0]
        students.append({
            "name": display_name(stem),
            "path": path,
            "key": stem,
        })
    return students


def describe(folder):
    """Why `folder` produced no photos, in a sentence worth showing the user.

    "No photos found in that folder" is a dead end when the folder plainly has
    photos in it. Counting what is actually there turns the message into
    something that names the real problem.
    """
    if not folder:
        return "No folder was chosen."
    if not os.path.isdir(folder):
        return "That folder no longer exists."
    try:
        entries = sorted(os.listdir(folder), key=str.lower)
    except OSError as exc:
        return f"That folder could not be read.\n\n{exc}"

    photos = load(folder)
    if photos:
        return f"{len(photos)} photos are readable here after all -- try again."

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


SECTION_DIR = "headshots"

# Never worth walking into looking for a class. A thumbdrive carries music and
# Windows bookkeeping too, and those run to thousands of entries apiece.
SKIP_DIRS = {"music", "system volume information", "winpython", "$recycle.bin",
             "found.000", "node_modules", "__pycache__"}


def is_section_dir(name):
    """`headshots`, or `headshots-oxford`: what a class keeps its faces in."""
    lowered = name.lower()
    return lowered == SECTION_DIR or lowered.startswith(SECTION_DIR + "-")


def course_name(folder):
    """Human label for a section, from its folder path.

    Handles the layouts in use:
        .../student-headshots/284              -> "284"
        .../student-headshots/318P-Oxford      -> "318P Oxford"
        .../Untitled/284/headshots             -> "284"
        .../Untitled/318P/headshots-oxford     -> "318P Oxford"

    Lives here rather than in theme.py because it is path arithmetic, not look
    and feel -- and because discovery needs it without dragging tkinter in.
    """
    if not folder:
        return ""
    folder = os.path.normpath(folder)
    base = os.path.basename(folder)
    parent = os.path.basename(os.path.dirname(folder))

    if base.lower() == SECTION_DIR:
        return parent
    if is_section_dir(base):
        return f"{parent} {base.split('-', 1)[1].capitalize()}".strip()
    return base.replace("-", " ").replace("_", " ")


def discover(root):
    """Every section under `root`, as {'label', 'path', 'count'}.

    One folder per class, each holding its own headshots:

        <root>/284/headshots            -> "284"
        <root>/318P/headshots-oxford    -> "318P Oxford"
        <root>/318P/headshots-hamilton  -> "318P Hamilton"

    Photos sit with the rest of a class's material rather than inside the
    application folder, so the app stays disposable: it can be rebuilt, moved or
    replaced without going anywhere near a student photo.
    """
    if not root or not os.path.isdir(root):
        return []

    def children(path):
        try:
            return sorted((n for n in os.listdir(path) if not n.startswith(".")),
                          key=str.lower)
        except OSError:
            return []

    sections = {}

    def add(path):
        path = os.path.normpath(path)
        if path in sections or not os.path.isdir(path):
            return
        students = load(path)
        if students:
            sections[path] = {"label": course_name(path) or os.path.basename(path),
                              "path": path, "count": len(students)}

    add(root)                       # pointed straight at one section's photos
    for name in children(root):
        classdir = os.path.join(root, name)
        if not os.path.isdir(classdir) or name.lower() in SKIP_DIRS:
            continue
        add(classdir)               # a section folder sitting at the root
        for sub in children(classdir):
            if is_section_dir(sub):
                add(os.path.join(classdir, sub))

    return sorted(sections.values(), key=lambda s: s["label"].lower())


def root_for(section_path):
    """The folder holding the class folders, given one section's photo folder.

    `<root>/318P/headshots-oxford` -> `<root>`, so opening one section teaches
    the app where the rest of them live.
    """
    if not section_path:
        return None
    section_path = os.path.normpath(section_path)
    if is_section_dir(os.path.basename(section_path)):
        return os.path.dirname(os.path.dirname(section_path))
    return os.path.dirname(section_path)


def candidate_roots():
    """Where to look for class folders, best guess first.

    A thumbdrive that moves between a Mac and a Windows lab machine mounts at a
    different path on each, so a remembered absolute path is a hint rather than
    an answer -- hence falling back to whatever is mounted now.
    """
    import glob

    roots, seen = [], set()

    def offer(path):
        if path and os.path.isdir(path) and path not in seen:
            seen.add(path)
            roots.append(path)

    offer(load_photo_root())
    offer(root_for(load_last_folder()))
    for volume in sorted(glob.glob("/Volumes/*")):
        offer(volume)
    for name in ("student-headshots", "Documents", "Desktop"):
        offer(os.path.join(os.path.expanduser("~"), name))
    offer(os.path.join(os.path.expanduser("~"), "Pictures", "student-headshots"))
    return roots


def find_sections():
    """Sections from the first candidate root that has any."""
    for root in candidate_roots():
        found = discover(root)
        if found:
            return root, found
    return None, []


def section_dir(class_folder, campus=""):
    """Where a class's photos belong: `<class_folder>/headshots[-campus]`."""
    name = SECTION_DIR + (f"-{campus.strip().lower()}" if campus.strip() else "")
    return os.path.join(class_folder, name)


def sample_folder():
    """The five fictional students shipped with the app, or None if absent.

    Lets someone try the app before they have prepared a real roster -- and
    means a demo never needs student photos on screen.
    """
    import sys

    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    folder = os.path.join(base, "sample-roster")
    return folder if os.path.isdir(folder) and load(folder) else None


def count_photos(folder):
    """How many loadable photos sit directly in `folder`.

    Counted with `is_photo`, the same test `load` uses. Matching on extension
    alone was a quieter version of the bug `sniff` exists to fix: the registrar
    serves photos from URLs carrying no extension, so a prepared section is a
    folder of bare `Smith_Alex` files. `load` opens them and finds a roster;
    this counted zero, and the folder that photo_subfolders should have offered
    was never mentioned.
    """
    if not folder or not os.path.isdir(folder):
        return 0
    try:
        return sum(1 for f in os.listdir(folder)
                   if is_photo(os.path.join(folder, f), f))
    except OSError:
        return 0


def photo_subfolders(folder, depth=2):
    """Folders beneath `folder` that do hold photos, as (path, count).

    Picking the parent by mistake is the easy slip: a thumbdrive holds
    `rosters/headshots-hamilton`, the picker shows only folder names, and
    `rosters` looks like the destination right up until the app reports
    nothing in it. Rather than make someone guess which level was wrong,
    look down a couple of levels and offer what is actually there.
    """
    found = []
    if not folder or not os.path.isdir(folder) or depth < 1:
        return found
    try:
        entries = sorted(os.listdir(folder), key=str.lower)
    except OSError:
        return found

    for entry in entries:
        path = os.path.join(folder, entry)
        if not os.path.isdir(path):
            continue
        count = count_photos(path)
        if count:
            found.append((path, count))
        else:
            found.extend(photo_subfolders(path, depth - 1))
    return found
