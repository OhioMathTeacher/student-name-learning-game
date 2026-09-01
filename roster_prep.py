#!/usr/bin/env python3
"""Roster Prep - turn saved photo-roster pages into Name Game photo folders.

Split out of Name Game, which is now only about practising names. Preparing
photos is a start-of-term job done once for a whole term; practising is done
every day for a fortnight. Carrying the import wizard around inside the app you
open daily meant the busiest screen was the one you needed least often.

Point this at the folder holding the pages you saved out of the browser and it
does every section in one pass: reads the names off each page, copies each
photo as LastName_FirstName, and files it under the class folder it belongs to.

Nothing here touches the network. The photos are student records: they stay on
the machine that prepared them.
"""

import os
import sys
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox

import prepare
import roster
import theme

SAVE_KEY = "⌘S" if sys.platform == "darwin" else "Ctrl+S"

HOW_TO = (
    "In the browser — not in this app — with your photo roster open:\n\n"
    f"Press {SAVE_KEY}, then choose “Web Page, complete” as the format. "
    "That saves the photos alongside the page; “HTML only” does not.\n\n"
    "Some browsers also offer this as File → Save Page As, but most hide "
    "that menu, so the keyboard shortcut is the reliable route.\n\n"
    "Save every section of the term into one folder — a subfolder per campus "
    "is ideal, because the campus is read back off the folder name. Then point "
    "this app at that folder once."
)


def default_photos():
    """The one folder prepared photos go into.

    Whatever Name Game last used, so both apps agree on where the photos live
    without the two of them being told separately.
    """
    return roster.load_folder() or roster.default_folder()


class RosterPrep(tk.Frame):
    """Three states, one at a time: choose, confirm the plan, see the result.

    The plan step exists because the failure worth preventing is silent: two
    sections of one course whose saved pages sit in folders that do not name a
    campus both come out labelled `318P`, land in the same folder, and merge
    into one roster of double length that looks perfectly normal. Working every
    destination out before writing anything means that collision can be shown
    and corrected rather than discovered in November.
    """

    def __init__(self, parent):
        super().__init__(parent, bg=theme.BG)
        self.root = parent
        self.photos = default_photos()
        self.jobs = []
        self.rows = []
        self.done_jobs = []
        self.searched = None
        self._build()
        self._build_menu()
        self._go("start")

    # -- construction -------------------------------------------------
    def _link(self, parent, text, command, bg=None, fg=None):
        link = theme.label(parent, text, size=theme.SIZE_SMALL,
                           fg=fg or theme.MUTED, bg=bg or theme.BG)
        link.configure(cursor="hand2")
        link.bind("<Button-1>", lambda _e: command())
        link.bind("<Enter>", lambda _e: link.configure(fg=theme.TEXT))
        link.bind("<Leave>", lambda _e: link.configure(fg=fg or theme.MUTED))
        return link

    def _card(self, parent):
        card = tk.Frame(parent, bg=theme.SURFACE, highlightthickness=1,
                        highlightbackground=theme.BORDER)
        card.pack(fill=tk.X, padx=40, pady=(24, 0))
        inner = tk.Frame(card, bg=theme.SURFACE)
        inner.pack(fill=tk.X, padx=30, pady=24)
        return inner

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Choose a photo folder…",
                              command=self.choose_folder)
        file_menu.add_command(label="Prepare one saved page…",
                              command=self.choose_single)
        file_menu.add_separator()
        file_menu.add_command(label="Where classes live…",
                              command=self.choose_photos)
        self.roster_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Open a roster in the browser",
                              menu=self.roster_menu)
        self.refresh_roster_menu()
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)

    def _build(self):
        header = tk.Frame(self, bg=theme.BG)
        header.pack(fill=tk.X, padx=32, pady=(24, 8))
        theme.label(header, "Roster Prep", size=theme.SIZE_TITLE,
                    weight="bold").pack(anchor="w")
        self.subtitle = theme.label(header, "", size=theme.SIZE_BODY, fg=theme.MUTED)
        self.subtitle.pack(anchor="w", pady=(2, 0))

        tk.Frame(self, bg=theme.BORDER, height=1).pack(fill=tk.X, padx=32, pady=(12, 0))

        body = tk.Frame(self, bg=theme.BG)
        body.pack(fill=tk.BOTH, expand=True)
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)

        self.steps = {}
        for name in ("start", "plan", "done"):
            frame = tk.Frame(body, bg=theme.BG)
            frame.grid(row=0, column=0, sticky="nsew")
            self.steps[name] = frame

        self._build_start()
        self._build_plan()
        self._build_done()

        self.destination_line = theme.label(self, "", size=theme.SIZE_SMALL,
                                            fg=theme.MUTED, justify="center",
                                            wraplength=760)
        self.destination_line.pack(side=tk.BOTTOM, pady=(0, 16))
        theme.label(self, "Photos stay on this computer. Nothing is uploaded.",
                    size=theme.SIZE_SMALL, fg=theme.MUTED).pack(side=tk.BOTTOM,
                                                                pady=(0, 4))
        self.refresh_destination()

    def _build_start(self):
        card = self._card(self.steps["start"])
        theme.label(card, "Step 1", size=theme.SIZE_SMALL, fg=theme.ACCENT,
                    bg=theme.SURFACE).pack(anchor="w")
        theme.label(card, "Need photos? Save your rosters out of the browser",
                    size=theme.SIZE_LABEL, weight="bold",
                    bg=theme.SURFACE).pack(anchor="w", pady=(2, 8))
        theme.label(card,
                    "Opens the registrar's photo rosters, where you are already "
                    "signed in.\n"
                    f"Save each section there with {SAVE_KEY}, choosing "
                    "“Web Page, complete” —\n"
                    "all of them into one folder.",
                    size=theme.SIZE_SMALL, fg=theme.MUTED, bg=theme.SURFACE,
                    justify="left").pack(anchor="w", pady=(0, 16))
        theme.button(card, "Open my photo rosters", self.open_roster_app,
                     primary=True).pack(anchor="w")

        card = self._card(self.steps["start"])
        theme.label(card, "Step 2", size=theme.SIZE_SMALL, fg=theme.ACCENT,
                    bg=theme.SURFACE).pack(anchor="w")
        theme.label(card, "Tell me where your photos are",
                    size=theme.SIZE_LABEL, weight="bold",
                    bg=theme.SURFACE).pack(anchor="w", pady=(2, 8))
        theme.label(card,
                    "Any folder. Rosters you saved from the browser get prepared \u2014 "
                    "every\n"
                    "section under it, in one pass, with the plan shown first. Photos "
                    "that are\n"
                    "already prepared are simply used.",
                    size=theme.SIZE_SMALL, fg=theme.MUTED, bg=theme.SURFACE,
                    justify="left").pack(anchor="w", pady=(0, 16))
        theme.button(card, "Choose the folder…", self.choose_folder,
                     primary=True).pack(anchor="w")

        foot = tk.Frame(self.steps["start"], bg=theme.BG)
        foot.pack(fill=tk.X, padx=40, pady=(16, 0))
        self._link(foot, "What exactly do I save?",
                   lambda: messagebox.showinfo("Saving the roster", HOW_TO)
                   ).pack(side=tk.LEFT)
        self._link(foot, "Just one section…", self.choose_single,
                   fg=theme.ACCENT).pack(side=tk.RIGHT)

    def _build_plan(self):
        frame = self.steps["plan"]
        self.plan_headline = theme.label(frame, "", size=theme.SIZE_LABEL,
                                         weight="bold")
        self.plan_headline.pack(pady=(24, 2))
        self.plan_note = theme.label(frame, "", size=theme.SIZE_SMALL,
                                     fg=theme.MUTED, wraplength=760,
                                     justify="center")
        self.plan_note.pack(pady=(0, 12))

        # Scrolled, because a term can be six sections and the window is a
        # fixed size shared with Name Game.
        holder = tk.Frame(frame, bg=theme.BG)
        holder.pack(fill=tk.BOTH, expand=True, padx=40)
        self.canvas = tk.Canvas(holder, bg=theme.BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(holder, orient="vertical",
                                 command=self.canvas.yview)
        self.plan_list = tk.Frame(self.canvas, bg=theme.BG)
        self.plan_list.bind(
            "<Configure>",
            lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.plan_window = self.canvas.create_window((0, 0), window=self.plan_list,
                                                     anchor="nw")
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(self.plan_window, width=e.width))
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.collision_note = theme.label(frame, "", size=theme.SIZE_SMALL,
                                          fg=theme.HINT, wraplength=760,
                                          justify="center")
        self.collision_note.pack(pady=(10, 0))

        buttons = tk.Frame(frame, bg=theme.BG)
        buttons.pack(pady=(12, 18))
        self.run_button = theme.button(buttons, "Prepare all of them", self.run,
                                       primary=True)
        self.run_button.pack(side=tk.LEFT)
        theme.button(buttons, "Back", lambda: self._go("start")).pack(
            side=tk.LEFT, padx=(12, 0))

    def _build_done(self):
        frame = self.steps["done"]
        inner = tk.Frame(frame, bg=theme.BG)
        inner.pack(fill=tk.BOTH, expand=True)

        self.result_headline = theme.label(inner, "", size=theme.SIZE_FEATURE,
                                           weight="bold")
        self.result_headline.pack(pady=(30, 4))
        self.result_summary = theme.label(inner, "", size=theme.SIZE_SMALL,
                                          fg=theme.MUTED, wraplength=760,
                                          justify="center")
        self.result_summary.pack()

        self.result_list = tk.Frame(inner, bg=theme.BG)
        self.result_list.pack(fill=tk.X, padx=40, pady=(20, 0))

        self.tidy_note = theme.label(
            inner,
            "The saved roster pages also hold student ID numbers.\n"
            "You do not need them any more.",
            size=theme.SIZE_SMALL, fg=theme.MUTED, justify="center")
        self.tidy_note.pack(pady=(24, 6))
        self.tidy_link = self._link(inner, "Delete the saved roster pages",
                                    self.discard_sources)
        self.tidy_link.pack()

        self._link(inner, "Prepare another term",
                   lambda: self._go("start")).pack(pady=(18, 0))

    # -- state --------------------------------------------------------
    def _go(self, step):
        self.subtitle.config(text={
            "start": "Build photo folders from your saved rosters.",
            "plan": "Check this is right before anything is written.",
            "done": "Ready to practise in Name Game.",
        }[step])
        self.steps[step].tkraise()

    def shorten(self, path):
        """A destination as it reads under the root, which is already on screen.

        The absolute path is mostly the root repeated once per row, and it
        overflowed the row rather than wrapping -- so the end, which is the
        part that differs and the part being checked, was the part cut off.
        """
        root = os.path.normpath(self.photos)
        path = os.path.normpath(path)
        if path.startswith(root + os.sep):
            return os.path.relpath(path, root)
        return path

    def refresh_destination(self):
        self.destination_line.config(
            text=f"Photos go to:  {self.photos}")

    def refresh_roster_menu(self):
        """List sections already imported, so their roster is one click away."""
        self.roster_menu.delete(0, "end")
        known = sorted(prepare.known_sections().items())
        if not known:
            self.roster_menu.add_command(label="None imported yet", state="disabled")
            return
        for label, where in known:
            self.roster_menu.add_command(
                label=f"{label}  ·  CRN {where['crn']}",
                command=lambda w=where: webbrowser.open(
                    prepare.roster_url(w["term"], w["crn"])))

    # -- actions ------------------------------------------------------
    def open_roster_app(self):
        """Say what to do over there before sending them over there.

        The instruction is useless once the browser is in front and this window
        is behind it, so it goes up first.
        """
        if not messagebox.askokcancel(
            "Opening your rosters",
            "Your photo rosters open in the browser next.\n\n"
            "For each section you teach: open it, press "
            f"{SAVE_KEY}, and choose “Web Page, complete” as the "
            "format — that saves the photos as well as the page.\n\n"
            "Save them all into one folder, then come back here.",
            icon=messagebox.INFO,
        ):
            return
        webbrowser.open(prepare.ROSTER_APP)

    def choose_photos(self):
        """Point both apps at the one folder the photos are kept in."""
        folder = theme.ask_folder(self.root, self.photos,
                                  title="Where should the photos be kept?")
        if not folder:
            return
        self.photos = folder
        roster.save_folder(folder)
        self.refresh_destination()
        if self.jobs:
            self.rebuild_plan()

    def choose_folder(self):
        """Ask where the photos are, and take whatever is there.

        One question, not two. A folder can hold photos already prepared or
        rosters saved out of the browser, and which one it is was never the
        user's problem to answer -- the app can look. Sorting that out here,
        before anything is refused, is why "no saved roster pages" no longer
        greets a folder full of faces.
        """
        folder = theme.ask_folder(
            self.root, self.searched, title="Where are your photos?")
        if not folder:
            return
        self.searched = folder

        if self.take_prepared(folder):
            return

        jobs = prepare.plan(folder, self.photos)
        if not jobs:
            self.report_nothing_found(folder)
            return
        self.jobs = jobs
        self.rebuild_plan()
        self._go("plan")

    # Kept: the File menu and the old wording both reached for this name.
    choose_batch = choose_folder

    def take_prepared(self, folder):
        """Photos already prepared: accept them and say so. True if taken.

        `Ryan_Wagers_318P_Oxford.jpg` says which class it belongs to, so a
        folder of them needs no arranging -- it is already the answer. There is
        no root to work out any more, which is what used to go wrong here: the
        drive's parent got written into the config and every class on it was
        lost.
        """
        students = roster.load(folder)
        classes = roster.classes(students)
        if not classes:
            return False

        roster.save_folder(folder)
        self.photos = folder
        self.refresh_destination()
        listing = "\n".join(
            f"\u2022  {label} \u2014 {len(roster.in_class(students, label))} photos"
            for label in classes[:8])
        messagebox.showinfo(
            "Roster Prep",
            f"Using these. Name Game opens them now.\n\n{listing}")
        return True

    def choose_single(self):
        """One saved page, for adding a section mid-term."""
        picked = filedialog.askopenfilename(
            parent=self.root,
            title="Choose the saved roster",
            initialdir=next((d for d in (
                self.searched, os.path.expanduser("~/Desktop"),
                os.path.expanduser("~/Downloads"), os.path.expanduser("~"))
                if d and os.path.isdir(d)), None),
            filetypes=[("Saved web page", "*.html *.htm"), ("All files", "*.*")],
        )
        if not picked:
            return

        page = prepare.resolve(picked)
        if not page:
            messagebox.showwarning(
                "Roster Prep",
                "That does not look like a saved roster.\n\n"
                "Choose the .html file the browser saved, or the folder beside it.")
            return

        try:
            info = prepare.read(page)
        except OSError as exc:
            messagebox.showerror("Roster Prep", f"Could not read that page.\n\n{exc}")
            return

        if not info["students"] or not info["files_dir_exists"]:
            messagebox.showwarning(
                "Roster Prep",
                "No photos found with that page.\n\n"
                "It needs to be saved as “Web Page, complete”, which "
                "also saves a folder of images beside it.")
            return

        self.searched = os.path.dirname(page)
        self.jobs = [{
            "page": page,
            "course": info["label"],
            "location": prepare.suggest_location(page),
            "info": info,
            "folder": self.photos,
            "students": len(info["students"]),
        }]
        self.rebuild_plan()
        self._go("plan")

    def report_nothing_found(self, folder):
        """Say what was actually in there, rather than just "nothing".

        Photos that are already prepared come first, because that message was
        the worst one this app produced: pointed at a folder of twenty-one
        correctly named faces it said "no saved roster pages", which is true
        and reads as a lie. There is nothing to prepare there because the work
        is done, and saying so is the whole answer.

        After that the likely slips are picking the folder above the one
        holding the pages, and saving as "HTML only" -- which writes a page
        with no images beside it. Both look identical from a bare "no rosters
        found", and neither is guessable from it.
        """
        pages = []
        for dirpath, dirnames, filenames in os.walk(folder):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            pages += [os.path.join(dirpath, f) for f in filenames
                      if f.lower().endswith((".html", ".htm"))]

        if pages:
            listed = "\n".join(f"•  {os.path.basename(p)}" for p in pages[:6])
            messagebox.showwarning(
                "Roster Prep",
                f"Found {len(pages)} saved pages under:\n{folder}\n\n"
                f"{listed}\n\n"
                "But none has its folder of images beside it, so the photos are "
                "not there. That happens when the page is saved as “HTML "
                "only”.\n\n"
                f"Save it again with {SAVE_KEY}, choosing “Web Page, "
                "complete”.")
            return

        messagebox.showwarning(
            "Roster Prep",
            f"Nothing to prepare under:\n{folder}\n\n"
            "No saved roster pages, and no photos either.\n\n"
            "This step wants the folder your browser saved the rosters into \u2014 "
            "the .html files and their image folders. If you are looking for "
            "photos you have already prepared, open those in Name Game instead.")

    # -- the plan -----------------------------------------------------
    def rebuild_plan(self):
        """Draw one editable row per section, and re-check for collisions."""
        for child in self.plan_list.winfo_children():
            child.destroy()
        self.rows = []

        for job in self.jobs:
            row = tk.Frame(self.plan_list, bg=theme.SURFACE, highlightthickness=1,
                           highlightbackground=theme.BORDER)
            row.pack(fill=tk.X, pady=(0, 8))
            inner = tk.Frame(row, bg=theme.SURFACE)
            inner.pack(fill=tk.X, padx=16, pady=12)

            top = tk.Frame(inner, bg=theme.SURFACE)
            top.pack(fill=tk.X)
            info = job["info"]
            title = f"{info['number']}: {info['title']}" if info["number"] else \
                os.path.basename(job["page"])
            theme.label(top, title.strip(), size=theme.SIZE_BODY, weight="bold",
                        bg=theme.SURFACE).pack(side=tk.LEFT)
            bits = [f"{job['students']} student"
                    + ("" if job["students"] == 1 else "s")]
            if info["crn"]:
                bits.append(f"CRN {info['crn']}")
            theme.label(top, "  ·  ".join(bits), size=theme.SIZE_SMALL,
                        fg=theme.MUTED, bg=theme.SURFACE).pack(side=tk.RIGHT)

            middle = tk.Frame(inner, bg=theme.SURFACE)
            middle.pack(fill=tk.X, pady=(8, 0))

            def field(caption, value, width):
                theme.label(middle, caption, size=theme.SIZE_SMALL,
                            fg=theme.MUTED,
                            bg=theme.SURFACE).pack(side=tk.LEFT, padx=(0, 6))
                var = tk.StringVar(value=value)
                tk.Entry(middle, textvariable=var, width=width,
                         font=theme.font(theme.SIZE_SMALL), bg=theme.BG,
                         fg=theme.TEXT, insertbackground=theme.TEXT,
                         relief=tk.FLAT, bd=0, highlightthickness=1,
                         highlightbackground=theme.BORDER,
                         highlightcolor=theme.ACCENT
                         ).pack(side=tk.LEFT, ipady=3, padx=(0, 16))
                var.trace_add("write", lambda *_a: self.recheck())
                return var

            course = field("Course", job["course"], 10)
            location = field("Location", job["location"], 14)

            # An example filename rather than a folder path: the filename is
            # where the class now lives, so it is the thing worth checking
            # before 29 copies of it are written.
            example = theme.label(inner, "", size=theme.SIZE_SMALL,
                                  fg=theme.MUTED, bg=theme.SURFACE,
                                  anchor="w", justify="left")
            example.pack(fill=tk.X, pady=(8, 0))

            self.rows.append({"job": job, "course": course,
                              "location": location, "example": example})

        self.plan_headline.config(
            text=f"{len(self.jobs)} sections ready to prepare")
        self.plan_note.config(
            text="Course and location go into every filename, and are how you "
                 "pick a class in Name Game. Two sections of one course must "
                 "differ here — the roster page itself never says which "
                 "campus it is.")
        self.recheck()

    def recheck(self):
        """Rebuild the example filenames, and flag two sections sharing a class.

        Two jobs writing one class is the whole reason this screen exists: the
        two rosters merge into one class of double length, and nothing about
        the result looks wrong afterwards. It used to be two sections sharing a
        folder; now they share a name, and the same photo can be overwritten
        outright, so it matters more rather than less.
        """
        counts = {}
        for row in self.rows:
            job = row["job"]
            course = row["course"].get().strip() or job["course"]
            location = row["location"].get().strip()
            row["label"] = f"{course} {location}".strip()
            counts[row["label"]] = counts.get(row["label"], 0) + 1

        clashing = {label for label, n in counts.items() if n > 1}
        for row in self.rows:
            job = row["job"]
            student = job["info"]["students"][0] if job["info"]["students"] else None
            shown = roster.filename(
                student["first"] if student else "First",
                student["last"] if student else "Last",
                row["course"].get().strip() or job["course"],
                row["location"].get().strip())
            clash = row["label"] in clashing
            row["example"].config(
                text=("\u26a0  " if clash else "") + shown,
                fg=theme.STOP if clash else theme.MUTED)

        if clashing:
            self.collision_note.config(
                text="Two sections would be given the same class name and "
                     "merged into one roster. Give them different locations — "
                     "Oxford and Hamilton.")
            self.run_button.config(state=tk.DISABLED)
        else:
            self.collision_note.config(text="")
            self.run_button.config(state=tk.NORMAL)

    def run(self):
        jobs = [{**row["job"],
                 "course": row["course"].get().strip() or row["job"]["course"],
                 "location": row["location"].get().strip(),
                 "label": row["label"],
                 "folder": self.photos}
                for row in self.rows]

        done = prepare.prepare_all(jobs)
        self.done_jobs = done

        written = sum(j["outcome"]["written"] for j in done if j["outcome"])
        failed = [j for j in done if j["error"]]
        missing = sorted(name for j in done if j["outcome"]
                         for name in j["outcome"]["missing"])

        for job in done:
            if not job["outcome"]:
                continue
            info = job["info"]
            prepare.remember_section(job["label"], info.get("term"),
                                     info.get("crn"))
        self.refresh_roster_menu()
        roster.save_folder(self.photos)

        self.result_headline.config(
            text=f"{written} photos ready",
            fg=theme.STOP if failed else theme.OK)
        summary = [f"{len(done) - len(failed)} of {len(done)} sections prepared"]
        if missing:
            # Said here rather than written to a NO-PHOTO.txt beside the
            # photos. The folder holds photos; a text file in it is one more
            # thing to wonder about, and this is the moment the answer is
            # actually wanted.
            summary.append(f"{len(missing)} with no photo on the roster: "
                           + ", ".join(missing[:4])
                           + ("\u2026" if len(missing) > 4 else ""))
        self.result_summary.config(text="  ·  ".join(summary))

        for child in self.result_list.winfo_children():
            child.destroy()
        for job in done:
            line = tk.Frame(self.result_list, bg=theme.BG)
            line.pack(fill=tk.X, pady=2)
            if job["error"]:
                text, colour = f"✗  {job['label']} — {job['error']}", theme.STOP
            else:
                outcome = job["outcome"]
                text = (f"✓  {job['label']} — {outcome['written']} photos "
                        f"→ {self.shorten(outcome['folder'])}")
                colour = theme.MUTED
            theme.label(line, text, size=theme.SIZE_SMALL, fg=colour,
                        anchor="w", justify="left").pack(fill=tk.X)

        self.tidy_link.pack()
        self.tidy_note.config(
            text="The saved roster pages also hold student ID numbers.\n"
                 "You do not need them any more.")
        self._go("done")

    def discard_sources(self):
        """Offer to remove the saved pages now the photos are copied out.

        Worth offering: every student row on those pages carries a
        `drop-student/pidm/<id>` link, so the saved file holds internal student
        ID numbers as well as names and faces.
        """
        pages = [j["page"] for j in self.done_jobs
                 if not j["error"] and os.path.exists(j["page"])]
        if not pages:
            return

        listed = "\n".join(pages[:6]) + ("\n…" if len(pages) > 6 else "")
        if not messagebox.askyesno(
            "Delete the saved rosters",
            f"Delete these {len(pages)} saved pages and their image folders?\n\n"
            f"{listed}\n\n"
            "The photos you just prepared are not affected. The pages hold "
            "student ID numbers as well as names and photos, so they are worth "
            "not leaving around."
        ):
            return

        failed = []
        for page in pages:
            try:
                prepare.discard(page)
                if self.searched:
                    prepare.prune_empty(os.path.dirname(page), self.searched)
            except OSError as exc:
                failed.append(f"{os.path.basename(page)}: {exc}")

        if failed:
            messagebox.showerror("Delete the saved rosters",
                                 "Some could not be deleted.\n\n"
                                 + "\n".join(failed))
            return
        self.tidy_note.config(text=f"{len(pages)} saved rosters deleted.")
        self.tidy_link.pack_forget()


def main():
    root = tk.Tk()
    root.title("Roster Prep")
    root.configure(bg=theme.BG)
    RosterPrep(root).pack(fill=tk.BOTH, expand=True)
    theme.fit_window(root, min_w=820, min_h=720)
    root.mainloop()


if __name__ == "__main__":
    main()
