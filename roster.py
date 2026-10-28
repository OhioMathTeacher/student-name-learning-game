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
import shutil
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

MARKER = "KEEP-DATA-HERE.txt"


def home_data_dir():
    return os.path.join(os.path.expanduser("~"), ".student_name_game")


def settings_dir():
    """Where hints, marks, scores, settings and the quiz log live.

    The home folder, unless the app-data folder beside the app holds MARKER.
    The choice is kept beside the app rather than in the home folder because
    it has to be read before the home folder is: on a lab PC the drive has
    never met, a choice saved at home would not be there to say "use the
    drive".
    """
    spare = app_data_dir()
    if spare and os.path.isfile(os.path.join(spare, MARKER)):
        return spare
    return home_data_dir()


def keeps_data_with_app():
    return settings_dir() != home_data_dir()


def app_data_dir():
    """The app-data folder that travels beside this copy, or None.

    Beside the Python files on the drive, or inside the name-game folder when
    the app is an exe at the top of the drive. An installed copy run from its
    git clone has none, and none is made for it: student data does not belong
    in a repository.
    """
    base = app_dir()
    for spare in (os.path.join(base, "app-data"),
                  os.path.join(base, "name-game", "app-data")):
        if os.path.isdir(spare):
            return spare
    return None


# -- carrying data between computers ----------------------------------------
#
# One .json file holds everything the game has learned: hints, marks, scores,
# the sections list and every quiz answer. Settings stay behind -- they say
# where this computer keeps its photos, which means nothing on another one.

EXPORT_FILES = ("hints.json", "difficult.json", "scores.json", "sections.json")
EXPORT_LOG = "quiz-log.jsonl"


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _read_log(path):
    entries = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if isinstance(entry, dict):
                    entries.append(entry)
    except OSError:
        pass
    return entries


def export_data(path):
    """Write everything to `path`. Returns the bundle written."""
    import socket
    from datetime import datetime

    d = settings_dir()
    bundle = {
        "name_game_export": 1,
        "exported": datetime.now().isoformat(timespec="seconds"),
        "from": socket.gethostname(),
        "files": {name: _read_json(os.path.join(d, name)) for name in EXPORT_FILES},
        "quiz_log": _read_log(os.path.join(d, EXPORT_LOG)),
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(bundle, fh, indent=1, sort_keys=True)
    return bundle


def read_export(path):
    """The bundle at `path`, or ValueError if it is not one of ours."""
    with open(path, encoding="utf-8") as fh:
        bundle = json.load(fh)
    if not isinstance(bundle, dict) or bundle.get("name_game_export") != 1:
        raise ValueError("This is not a Name Game data file.")
    bundle.setdefault("files", {})
    bundle.setdefault("quiz_log", [])
    return bundle


def _same_answer(entry):
    """An answer's identity, leaving out its round: rounds are renumbered when
    logs are added together, and a second import of the same file must still
    recognise what it already brought in."""
    return json.dumps({k: v for k, v in entry.items() if k != "round"}, sort_keys=True)


def _renumber_rounds(groups):
    """Number rounds 1, 2, 3 ... in the order they were played.

    Every computer counts its own rounds from 1, so two logs added together
    both have a round 1. Recency is measured in rounds, so they are put back
    in time order: each group is one round from one source, placed by its
    first answer.
    """
    order = sorted(groups, key=lambda g: min(e.get("at", "") for e in groups[g]))
    entries = []
    for number, g in enumerate(order, start=1):
        for e in groups[g]:
            entries.append({**e, "round": number})
    return sorted(entries, key=lambda e: (e.get("at", ""), e.get("round", 0)))


def import_data(bundle, replace):
    """Bring a bundle in, replacing this computer's data or adding to it.

    Adding: hints, marks and sections are joined, the imported side winning
    where both have the same face; scores keep the better best streak per
    class; quiz answers from both are kept, a repeat import adding nothing.
    Whatever is replaced or added to is first copied aside as .before-import.
    """
    d = settings_dir()
    os.makedirs(d, exist_ok=True)
    for name in EXPORT_FILES + (EXPORT_LOG,):
        path = os.path.join(d, name)
        if os.path.exists(path):
            shutil.copy2(path, path + ".before-import")

    for name in EXPORT_FILES:
        new = bundle["files"].get(name) or {}
        if not isinstance(new, dict):
            new = {}
        path = os.path.join(d, name)
        old = {} if replace else _read_json(path)
        if name == "scores.json":
            merged = dict(old)
            for label, score in new.items():
                had = merged.get(label)
                if isinstance(had, dict) and isinstance(score, dict):
                    score = {**had, **score,
                             "best": max(had.get("best", 0), score.get("best", 0))}
                merged[label] = score
        else:
            merged = {**old, **new}
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(merged, fh, indent=2, sort_keys=True)

    imported = [e for e in bundle["quiz_log"] if isinstance(e, dict)]
    log_path = os.path.join(d, EXPORT_LOG)
    if replace:
        entries = imported
    else:
        mine = _read_log(log_path)
        seen = {_same_answer(e) for e in mine}
        groups = {}
        for e in mine:
            groups.setdefault(("here", e.get("round", 0)), []).append(e)
        for e in imported:
            if _same_answer(e) not in seen:
                groups.setdefault(("import", e.get("round", 0)), []).append(e)
        entries = _renumber_rounds(groups)
    with open(log_path, "w", encoding="utf-8") as fh:
        fh.write("".join(json.dumps(e, sort_keys=True) + "\n" for e in entries))


def keep_data_with_app(on, copy_over=False):
    """Switch where the data lives. With `copy_over`, bring the current files.

    Copying never overwrites silently: a file already at the destination is
    renamed with a .before-switch suffix first, so either side can be put back.
    """
    spare = app_data_dir()
    if spare is None:
        raise OSError("This copy has no app-data folder beside it.")
    source = settings_dir()
    target = spare if on else home_data_dir()
    if source == target:
        return
    if copy_over and os.path.isdir(source):
        os.makedirs(target, exist_ok=True)
        for name in os.listdir(source):
            if not (name.endswith(".json") or name.endswith(".jsonl")):
                continue
            dest = os.path.join(target, name)
            if os.path.exists(dest):
                os.replace(dest, dest + ".before-switch")
            shutil.copy2(os.path.join(source, name), dest)
    marker = os.path.join(spare, MARKER)
    if on:
        with open(marker, "w", encoding="utf-8") as fh:
            fh.write("Name Game keeps its hints, marks, scores, settings and quiz\n"
                     "log in this folder, on whatever computer it runs on.\n"
                     "Delete this file (or use Setup > Keep my data) to keep them\n"
                     "in each computer's home folder instead.\n")
    elif os.path.exists(marker):
        os.remove(marker)


def config_path():
    d = settings_dir()
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "config.json")


def app_dir():
    """The folder the app was started from: this file's, or the .exe's.

    PyInstaller unpacks a one-file build somewhere under the temp folder, so
    `__file__` says nothing about where the exe was double-clicked.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def restore_settings():
    """Bring hints, scores and the class list over, once, per computer.

    They travel on the drive as app-data, beside the app -- or, when the app
    is an exe at the top of the drive, inside the name-game folder next to
    it. Never overwrites: a machine that already has hints on it has better
    ones than the copy travelling on the drive.
    """
    if keeps_data_with_app() or os.path.isdir(settings_dir()):
        return
    spare = app_data_dir()
    if spare is None:
        return
    os.makedirs(settings_dir(), exist_ok=True)
    for name in os.listdir(spare):
        if name.endswith(".json"):
            try:
                shutil.copy2(os.path.join(spare, name),
                             os.path.join(settings_dir(), name))
            except OSError:
                pass


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
    """The sample photographs shipped with the app, or None if absent.

    People, places and presidents -- public domain throughout, in three classes.
    Lets someone try the app before they have prepared a real roster, and means a
    demo never needs a student's photograph on screen, which matters here: the
    app's whole promise is that the photos never leave your machine.
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
