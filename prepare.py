"""Turn a saved Miami photo-roster page into a Name Game photo folder.

The registrar's photo roster sits behind CAS single sign-on with no API, so
there is nothing to automate a login against -- and nothing to ask a colleague
for a token for either. The reliable path is the one a browser already gives
you:

    open the roster page while logged in
    File -> Save Page As -> "Web Page, complete"

That writes `Photo Roster-something.html` next to a `Photo Roster-something_files`
folder holding every photo at full size. This module reads the pair and writes
`First_Last_Course_Location.jpg` files into one folder, which is all Name Game
needs: the name and the class are both in the filename, so every section can
share a folder and picking a class is a filter rather than a different folder.

Nothing here touches the network. The photos are student records: they stay on
the machine that prepared them.
"""

import hashlib
import html as html_mod
import os
import re
import shutil

import roster

# The registrar serves this exact image for a student with no photo on file.
# Identified by content rather than by size, so a small real photo is not
# mistaken for it.
PLACEHOLDER_MD5 = "202107daf6f52ede9572188743374438"

IMG_TAG = re.compile(r'<img[^>]*id="student_photo_id_[^"]*"[^>]*>', re.I)
ATTR = re.compile(r'(\w+)\s*=\s*"([^"]*)"')
COURSE = re.compile(r'([A-Z]{2,4}\s*\d+[A-Z]?)\s*:\s*([^(<]+)\(CRN\s*(\d+)\)')
TERM = re.compile(r'\b(20\d{4})\b')

# A roster page of 30 students runs to about 80KB. Anything far past that is
# not one, and reading it is pure cost: a thumbdrive carrying an editor build
# also carries multi-megabyte licence pages, and every page found has to be
# read to know whether it is a roster.
MAX_PAGE_BYTES = 4 * 1024 * 1024


def files_dir(html_path):
    """The `..._files` folder the browser saved alongside the page."""
    return os.path.splitext(html_path)[0] + "_files"


def image_dir(html_path, wanted=None):
    """Where this page's photos actually are.

    `<stem>_files` beside the page is what the browser writes, and what this
    assumed. It stops being true the moment anyone tidies up: renaming the
    page to say which campus leaves the folder named after the old title, and
    dragging the page into its own images folder leaves the photos sitting
    beside it rather than below. Both are ordinary things to do to two saved
    rosters that would otherwise both be called "Photo Roster", and both made
    a roster of 28 students unreadable.

    So the page is asked instead of assumed: `wanted` is a filename it refers
    to, and the directory that actually holds it wins. Falls back to the old
    guess when the page names nothing.
    """
    beside = files_dir(html_path)
    here = os.path.dirname(html_path)

    candidates = [beside, here]
    try:
        candidates += sorted(
            os.path.join(here, name) for name in os.listdir(here)
            if name.endswith("_files") and os.path.isdir(os.path.join(here, name)))
    except OSError:
        pass

    if wanted:
        for candidate in candidates:
            if os.path.isfile(os.path.join(candidate, wanted)):
                return candidate
    return beside if os.path.isdir(beside) else here


def _attrs(tag):
    return {k.lower(): html_mod.unescape(v) for k, v in ATTR.findall(tag)}


def _extension(source):
    """What to name the copy, when the saved photo has no extension of its own.

    The registrar's image URLs carry no extension, so the browser writes bare
    filenames and passing `splitext(source)[1]` through produced extensionless
    copies. The app filtered those out by name, which is how a folder full of
    faces reported "No photos found in that folder". Read the format out of the
    bytes instead; JPEG is the registrar's format and the safe default.
    """
    extension = os.path.splitext(source)[1].lower()
    if extension in roster.IMAGE_TYPES:
        return extension
    return roster.sniff(source) or ".jpg"


def read(html_path):
    """Parse a saved roster page. Returns course details and the student list."""
    with open(html_path, encoding="utf-8", errors="replace") as fh:
        page = fh.read()

    course = number = title = crn = ""
    match = COURSE.search(page)
    if match:
        number, title, crn = match.group(1).strip(), match.group(2).strip(), match.group(3)
        course = f"{number}: {title} (CRN {crn})"

    term = TERM.search(page)

    found = []
    for tag in IMG_TAG.findall(page):
        attrs = _attrs(tag)
        alt, src = attrs.get("alt", ""), attrs.get("src", "")
        if not alt or not src:
            continue
        last, _, first = alt.partition(",")
        found.append((roster.clean(first), roster.clean(last),
                      os.path.basename(src.replace("%20", " ").split("/")[-1])))

    directory = image_dir(html_path, found[0][2] if found else None)

    students = [{"first": first, "last": last,
                 "name": f"{first} {last}".strip(),
                 "source": os.path.join(directory, image)}
                for first, last, image in found]

    # Default folder name: the course number alone. Two sections of the same
    # course differ only by CRN on this page -- no campus anywhere in it -- so
    # the caller lets the user edit this.
    label = re.sub(r'^[A-Z]{2,4}\s*', "", number) or "section"

    return {
        "course": course,
        "number": number,
        "title": title,
        "crn": crn,
        "term": term.group(1) if term else "",
        "label": label,
        "students": students,
        "files_dir": directory,
        "files_dir_exists": bool(students) and os.path.isfile(students[0]["source"]),
    }


def is_placeholder(path):
    try:
        with open(path, "rb") as fh:
            return hashlib.md5(fh.read()).hexdigest() == PLACEHOLDER_MD5
    except OSError:
        return False


# The page names the course but never the campus: two sections of one course
# differ on it only by CRN. The folder someone saved the page into usually says.
CAMPUSES = ("oxford", "hamilton", "middletown", "west chester", "luxembourg")


def suggest_location(html_path):
    """`Hamilton`, read off where the page was saved or what it was called.

    The page itself never says: two sections of one course differ on it only by
    CRN. But naming the saved file `318p-hamilton-FA26.html`, or filing it under
    a folder called Hamilton, is what people already do -- so read it back
    rather than making them retype it. Getting this wrong merges two sections
    into one class, which looks perfectly normal until November.
    """
    stem = os.path.splitext(os.path.basename(html_path))[0].lower()
    for campus in CAMPUSES:
        if campus in stem:
            return campus.title()

    parts = os.path.normpath(os.path.dirname(os.path.abspath(html_path))).split(os.sep)
    for part in reversed(parts[-3:]):
        if part.lower() in CAMPUSES:
            return part.title()
    return ""


def find_pages(root, max_depth=4):
    """Every saved roster page under `root`, page and image folder both intact.

    People save a term's sections into one tree -- `Desktop/318P/Hamilton`,
    `Desktop/318P/Oxford`, `Desktop/284` -- and then had to walk the import
    wizard once per section. Finding them all lets that be one pass.
    """
    found = []
    root = os.path.abspath(root)
    depth0 = root.rstrip(os.sep).count(os.sep)
    for dirpath, dirnames, filenames in os.walk(root):
        # `_files` folders are walked into rather than pruned: a page dragged
        # inside its own images folder is still a page, and pruning them was
        # why a saved roster sitting there was invisible.
        dirnames[:] = [d for d in dirnames if not d.startswith(".")
                       and d.lower() not in roster.SKIP_DIRS]
        if dirpath.count(os.sep) - depth0 >= max_depth:
            dirnames[:] = []
        for name in sorted(filenames):
            if not name.lower().endswith((".html", ".htm")):
                continue
            page = os.path.join(dirpath, name)
            try:
                if os.path.getsize(page) > MAX_PAGE_BYTES:
                    continue
                info = read(page)
            except OSError:
                continue
            # Its photos have to be findable, which is what separates a saved
            # roster from every other page that happens to be lying about.
            if info["students"] and info["files_dir_exists"]:
                found.append(page)
    return found


def plan(root, folder):
    """What a batch import would do, worked out before anything is written.

    One job per saved page. `course` and `location` are what go into every
    filename the job writes, and the caller lets them be edited first: the
    campus is a guess read off the path, and a wrong guess quietly merges two
    sections into one class.
    """
    jobs = []
    for page in find_pages(root):
        try:
            info = read(page)
        except OSError:
            continue
        if not info["students"]:
            continue
        jobs.append({
            "page": page,
            "course": info["label"],
            "location": suggest_location(page),
            "info": info,
            "folder": folder,
            "students": len(info["students"]),
        })
    return jobs


def prepare_all(jobs):
    """Run a plan. Returns each job with its outcome attached."""
    done = []
    for job in jobs:
        try:
            outcome = prepare(job["page"], job["folder"],
                              job["course"], job["location"])
            done.append({**job, "outcome": outcome, "error": None})
        except OSError as exc:
            done.append({**job, "outcome": None, "error": str(exc)})
    return done


def prepare(html_path, folder, course, location):
    """Copy the roster's photos into `folder`, named for student and class.

    Every section writes into the same folder -- the class is in the filename,
    so there is nowhere else for it to go. Returns where they went, how many
    were written, and the students who have no photo: the registrar's
    placeholder is skipped rather than copied, so the app never quizzes on a
    silhouette.
    """
    info = read(html_path)
    course = course or info["label"]
    os.makedirs(folder, exist_ok=True)

    written, missing, seen = 0, [], {}
    for student in info["students"]:
        source = student["source"]
        if not os.path.exists(source) or is_placeholder(source):
            missing.append(student["name"])
            continue
        name = roster.filename(student["first"], student["last"],
                               course, location, _extension(source))
        # Two students of one name in one class: the second gets a numbered
        # copy rather than overwriting the first, who would then be quizzed
        # on twice under one face.
        seen[name] = seen.get(name, 0) + 1
        if seen[name] > 1:
            stem, extension = os.path.splitext(name)
            name = f"{stem}-{seen[name]}{extension}"
        shutil.copy2(source, os.path.join(folder, name))
        written += 1

    return {
        "folder": folder,
        "written": written,
        "missing": missing,
        "total": len(info["students"]),
        "info": info,
    }


def prune_empty(folder, stop_at):
    """Remove folders left behind empty by `discard`, up to but not past `stop_at`.

    Deleting a page out of `Desktop/318P/Hamilton` otherwise leaves a pair of
    empty folders sitting on the desktop looking like they still hold a roster.
    Only genuinely empty folders go: anything still holding a file stays put.
    """
    stop_at = os.path.abspath(stop_at)
    folder = os.path.abspath(folder)
    removed = []
    while folder != stop_at and folder.startswith(stop_at + os.sep):
        try:
            if os.listdir(folder):
                break
            os.rmdir(folder)
        except OSError:
            break
        removed.append(folder)
        folder = os.path.dirname(folder)
    return removed


def resolve(path):
    """Accept whatever the user points at and find the saved page.

    People reach for the folder the browser made, or a photo inside it, as
    readily as the .html file. Only the page carries the names, so resolve any
    of those back to it rather than making the user guess.
    """
    if not path:
        return None
    path = os.path.abspath(path)

    if os.path.isfile(path) and path.lower().endswith((".html", ".htm")):
        return path

    # A "..._files" folder, or something inside it: the page sits alongside.
    folder = path if os.path.isdir(path) else os.path.dirname(path)
    if folder.endswith("_files"):
        for ext in (".html", ".htm"):
            candidate = folder[: -len("_files")] + ext
            if os.path.isfile(candidate):
                return candidate

    # A plain folder: take the only saved page in it, if there is exactly one.
    if os.path.isdir(folder):
        pages = [f for f in sorted(os.listdir(folder))
                 if f.lower().endswith((".html", ".htm"))
                 and os.path.isdir(files_dir(os.path.join(folder, f)))]
        if len(pages) == 1:
            return os.path.join(folder, pages[0])
    return None


ROSTER_APP = "https://www.apps.miamioh.edu/registrar/photoroster/"


def roster_url(term, crn):
    """Direct link to one section's photo roster."""
    return (f"https://www.apps.miamioh.edu/registrar/photoroster/roster/"
            f"term/{term}/crn/{crn}/photos/1/show-attendance/0")


def _sections_path():
    d = os.path.join(os.path.expanduser("~"), ".student_name_game")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "sections.json")


def remember_section(label, term, crn):
    """Keep term+CRN of an imported section so it can be reopened later."""
    import json

    if not (term and crn):
        return
    try:
        with open(_sections_path(), encoding="utf-8") as fh:
            known = json.load(fh)
    except (OSError, ValueError):
        known = {}
    known[label] = {"term": term, "crn": crn}
    try:
        with open(_sections_path(), "w", encoding="utf-8") as fh:
            json.dump(known, fh, indent=2, sort_keys=True)
    except OSError:
        pass


def known_sections():
    import json

    try:
        with open(_sections_path(), encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def saved_pair(html_path):
    """The two things the browser wrote: the page and its images folder."""
    return html_path, files_dir(html_path)


def discard(html_path):
    """Delete the saved page and its images folder.

    Worth offering once the photos are copied out: the page is not just
    pictures. Every student row carries a `drop-student/pidm/<id>` link, so the
    saved file holds internal student ID numbers as well as names and faces.
    Never called without asking first.
    """
    removed = []
    folder = files_dir(html_path)
    if os.path.isdir(folder):
        shutil.rmtree(folder)
        removed.append(folder)
    if os.path.isfile(html_path):
        os.remove(html_path)
        removed.append(html_path)
    return removed
