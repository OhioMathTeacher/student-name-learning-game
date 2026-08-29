"""Turn a saved Miami photo-roster page into a Name Game photo folder.

The registrar's photo roster sits behind CAS single sign-on with no API, so
there is nothing to automate a login against -- and nothing to ask a colleague
for a token for either. The reliable path is the one a browser already gives
you:

    open the roster page while logged in
    File -> Save Page As -> "Web Page, complete"

That writes `Photo Roster-something.html` next to a `Photo Roster-something_files`
folder holding every photo at full size. This module reads the pair and writes
`LastName_FirstName.jpg` files, which is the naming Name Game expects.

Nothing here touches the network. The photos are student records: they stay on
the machine that prepared them.
"""

import hashlib
import html as html_mod
import os
import re
import shutil

# The registrar serves this exact image for a student with no photo on file.
# Identified by content rather than by size, so a small real photo is not
# mistaken for it.
PLACEHOLDER_MD5 = "202107daf6f52ede9572188743374438"

IMG_TAG = re.compile(r'<img[^>]*id="student_photo_id_[^"]*"[^>]*>', re.I)
ATTR = re.compile(r'(\w+)\s*=\s*"([^"]*)"')
COURSE = re.compile(r'([A-Z]{2,4}\s*\d+[A-Z]?)\s*:\s*([^(<]+)\(CRN\s*(\d+)\)')
TERM = re.compile(r'\b(20\d{4})\b')


def files_dir(html_path):
    """The `..._files` folder the browser saved alongside the page."""
    return os.path.splitext(html_path)[0] + "_files"


def _attrs(tag):
    return {k.lower(): html_mod.unescape(v) for k, v in ATTR.findall(tag)}


def _safe(part):
    return re.sub(r'[\\/:*?"<>|]', "", part).strip()


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
    directory = files_dir(html_path)

    students = []
    for tag in IMG_TAG.findall(page):
        attrs = _attrs(tag)
        alt, src = attrs.get("alt", ""), attrs.get("src", "")
        if not alt or not src:
            continue
        last, _, first = alt.partition(",")
        students.append({
            "name": f"{_safe(first)} {_safe(last)}".strip(),
            "stem": f"{_safe(last)}_{_safe(first)}" if first.strip() else _safe(last),
            "source": os.path.join(directory, os.path.basename(
                src.replace("%20", " ").split("/")[-1])),
        })

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
        "files_dir_exists": os.path.isdir(directory),
    }


def is_placeholder(path):
    try:
        with open(path, "rb") as fh:
            return hashlib.md5(fh.read()).hexdigest() == PLACEHOLDER_MD5
    except OSError:
        return False


def prepare(html_path, out_root, label):
    """Copy the roster's photos into `out_root/label` with Name Game's naming.

    Returns the destination, how many were written, and the students who have
    no photo -- the registrar's placeholder is skipped rather than written, so
    the app never quizzes on a silhouette.
    """
    info = read(html_path)
    destination = os.path.join(out_root, _safe(label) or info["label"])
    os.makedirs(destination, exist_ok=True)

    written, missing, seen = 0, [], {}
    for student in info["students"]:
        source = student["source"]
        if not os.path.exists(source) or is_placeholder(source):
            missing.append(student["name"])
            continue
        stem = student["stem"]
        seen[stem] = seen.get(stem, 0) + 1
        if seen[stem] > 1:
            stem = f"{stem}-{seen[stem]}"
        shutil.copy2(source, os.path.join(destination, stem + os.path.splitext(source)[1]))
        written += 1

    if missing:
        with open(os.path.join(destination, "NO-PHOTO.txt"), "w", encoding="utf-8") as fh:
            fh.write(f"{len(missing)} students have no photo on the roster:\n\n")
            fh.write("\n".join(sorted(missing)) + "\n")

    return {
        "folder": destination,
        "written": written,
        "missing": missing,
        "total": len(info["students"]),
        "info": info,
    }


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
