#!/usr/bin/env python3
"""Name Game - learn your students' names from their photos.

One window, two screens. Study walks the roster showing each name; Quiz hides
it and asks. They were separate programs, and switching modes actually quit one
process and started another, which is why the window used to jump. Now they are
two frames in the same window and switching just raises one.

Photos are named LastName_FirstName.jpg in a folder per section.
"""

import os
import random
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox

import prepare
import roster
import theme


class StudyView(tk.Frame):
    """Walk the roster with names visible, and write a memory hint per face."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self.index = 0
        self.auto = False
        self.auto_delay = 3000
        self.after_id = None
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=theme.BG)
        header.pack(fill=tk.X, padx=32, pady=(24, 8))
        theme.label(header, "Study", size=theme.SIZE_TITLE, weight="bold").pack(anchor="w")
        theme.label(header, "Look at the face, then read the name.",
                    size=theme.SIZE_BODY, fg=theme.MUTED).pack(anchor="w", pady=(2, 0))

        tk.Frame(self, bg=theme.BORDER, height=1).pack(fill=tk.X, padx=32, pady=(12, 0))

        self.photo_label = tk.Label(self, bg=theme.SURFACE, bd=0, relief=tk.FLAT,
                                    highlightthickness=1, highlightbackground=theme.BORDER)
        self.photo_label.pack(pady=(28, 0))

        self.name_label = tk.Label(self, text="", font=theme.font(theme.SIZE_FEATURE, "bold"),
                                   bg=theme.BG, fg=theme.TEXT)
        self.name_label.pack(pady=(22, 4))

        self.counter_label = theme.label(self, "", size=theme.SIZE_BODY, fg=theme.MUTED)
        self.counter_label.pack(pady=(0, 20))

        hint_frame = tk.Frame(self, bg=theme.BG)
        hint_frame.pack(fill=tk.X, padx=90, pady=(0, 18))
        theme.label(hint_frame, "Memory hint", size=theme.SIZE_SMALL,
                    fg=theme.MUTED).pack(anchor="w")
        self.hint_entry = tk.Entry(
            hint_frame, font=theme.font(theme.SIZE_BODY),
            bg=theme.SURFACE, fg=theme.TEXT, insertbackground=theme.TEXT,
            relief=tk.FLAT, bd=0, highlightthickness=1,
            highlightbackground=theme.BORDER, highlightcolor=theme.ACCENT
        )
        self.hint_entry.pack(fill=tk.X, ipady=6, pady=(4, 2))
        self.hint_entry.bind("<Return>", lambda e: self.save_hint())
        self.hint_entry.bind("<FocusOut>", lambda e: self.save_hint())
        self.hint_status = theme.label(hint_frame, "", size=theme.SIZE_SMALL, fg=theme.MUTED)
        self.hint_status.pack(anchor="w")

        controls = tk.Frame(self, bg=theme.BG)
        controls.pack()
        theme.button(controls, "‹  Previous", self.previous).pack(side=tk.LEFT, padx=6)
        theme.button(controls, "Next  ›", self.next, primary=True).pack(side=tk.LEFT, padx=6)
        theme.button(controls, "Shuffle", self.shuffle).pack(side=tk.LEFT, padx=6)
        theme.button(controls, "Change folder", self.app.choose_folder).pack(side=tk.LEFT, padx=6)

        auto_frame = tk.Frame(self, bg=theme.BG)
        auto_frame.pack(pady=(18, 0))
        self.auto_btn = theme.button(auto_frame, "Auto-advance", self.toggle_auto)
        self.auto_btn.pack(side=tk.LEFT, padx=(0, 12))
        theme.label(auto_frame, "every", size=theme.SIZE_BODY, fg=theme.MUTED).pack(side=tk.LEFT)
        self.speed_var = tk.StringVar(value="3")
        speed = tk.OptionMenu(auto_frame, self.speed_var, *["1", "2", "3", "4", "5", "7", "10"],
                              command=self.set_speed)
        speed.config(font=theme.font(theme.SIZE_BODY), bg=theme.SURFACE, fg=theme.TEXT,
                     activebackground=theme.SURFACE_ACTIVE, activeforeground=theme.TEXT,
                     relief=tk.FLAT, bd=0, highlightthickness=1,
                     highlightbackground=theme.BORDER, cursor="hand2")
        speed["menu"].config(bg=theme.SURFACE, fg=theme.TEXT, activebackground=theme.ACCENT,
                             activeforeground=theme.TEXT, bd=0)
        speed.pack(side=tk.LEFT, padx=8)
        theme.label(auto_frame, "seconds", size=theme.SIZE_BODY, fg=theme.MUTED).pack(side=tk.LEFT)

        theme.label(self, "Space next  ·  ← previous  ·  S shuffle  ·  A auto-advance",
                    size=theme.SIZE_SMALL, fg=theme.MUTED).pack(pady=(22, 18))

    # -- data ---------------------------------------------------------
    def on_roster_changed(self):
        self.index = 0
        self.show()

    def on_show(self):
        self.show()

    def on_hide(self):
        self.save_hint()
        self.stop_auto()

    def show(self):
        students = self.app.students
        if not students:
            self.name_label.config(text="No photos loaded")
            self.counter_label.config(text="")
            return
        self.index %= len(students)
        student = students[self.index]
        self.counter_label.config(text=f"Student {self.index + 1} of {len(students)}")
        try:
            photo = theme.photo(student["path"])
            self.photo_label.config(image=photo, text="")
            self.photo_label.image = photo
        except Exception as exc:                      # noqa: BLE001 - show, don't crash
            self.photo_label.config(image="", text=f"Could not open image\n{exc}")
        self.name_label.config(text=student["name"])
        self.hint_entry.delete(0, tk.END)
        self.hint_entry.insert(0, theme.load_hints().get(student["key"], ""))
        self.hint_status.config(text="")

    def save_hint(self):
        if not self.app.students:
            return
        theme.save_hint(self.app.students[self.index]["key"], self.hint_entry.get())
        self.hint_status.config(text="Saved")
        self.after(1200, lambda: self.hint_status.config(text=""))

    # -- navigation ---------------------------------------------------
    def next(self):
        if not self.app.students:
            return
        self.save_hint()
        self.index += 1
        self.show()

    def previous(self):
        if not self.app.students:
            return
        self.save_hint()
        self.index -= 1
        self.show()

    def shuffle(self):
        if not self.app.students:
            return
        self.save_hint()
        random.shuffle(self.app.students)
        self.index = 0
        self.show()

    def set_speed(self, value):
        self.auto_delay = int(value) * 1000

    def toggle_auto(self):
        self.auto = not self.auto
        if self.auto:
            self.auto_btn.config(text="Stop", bg=theme.STOP, activebackground=theme.STOP_ACTIVE)
            self.auto_step()
        else:
            self.stop_auto()

    def stop_auto(self):
        self.auto = False
        self.auto_btn.config(text="Auto-advance", bg=theme.SURFACE,
                             activebackground=theme.SURFACE_ACTIVE)
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None

    def auto_step(self):
        if self.auto and self.app.students:
            self.next()
            self.after_id = self.after(self.auto_delay, self.auto_step)

    def handles_typing(self, widget):
        return widget is self.hint_entry


class QuizView(tk.Frame):
    """Hide the name and ask for it. One wrong answer ends the run."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self.current = None
        self.remaining = []
        self.perfect = []
        self.streak = 0
        self.longest = 0
        self.used_hint = False
        self.hint_level = 0
        self.game_over = False
        self.restart_btn = None
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=theme.BG)
        header.pack(fill=tk.X, padx=32, pady=(24, 8))
        theme.label(header, "Quiz", size=theme.SIZE_TITLE, weight="bold").pack(anchor="w")
        self.streak_label = theme.label(header, "Current streak 0  ·  longest 0",
                                        size=theme.SIZE_BODY, fg=theme.MUTED)
        self.streak_label.pack(anchor="w", pady=(2, 0))

        tk.Frame(self, bg=theme.BORDER, height=1).pack(fill=tk.X, padx=32, pady=(12, 0))

        self.photo_label = tk.Label(self, bg=theme.SURFACE, bd=0, relief=tk.FLAT,
                                    highlightthickness=1, highlightbackground=theme.BORDER)
        self.photo_label.pack(pady=(28, 18))

        theme.label(self, "Student's name", size=theme.SIZE_BODY, fg=theme.MUTED).pack()
        self.entry = tk.Entry(
            self, font=theme.font(theme.SIZE_INPUT), width=22, justify="center",
            bg=theme.SURFACE, fg=theme.TEXT, insertbackground=theme.TEXT,
            relief=tk.FLAT, bd=0, highlightthickness=1,
            highlightbackground=theme.BORDER, highlightcolor=theme.ACCENT
        )
        self.entry.pack(ipady=8, pady=(6, 18))

        controls = tk.Frame(self, bg=theme.BG)
        controls.pack()
        self.buttons = controls
        self.submit_btn = theme.button(controls, "Submit", self.check, primary=True)
        self.submit_btn.pack(side=tk.LEFT, padx=6)
        self.hint_btn = theme.button(controls, "Hint", self.hint)
        self.hint_btn.pack(side=tk.LEFT, padx=6)
        self.skip_btn = theme.button(controls, "Skip", self.skip)
        self.skip_btn.pack(side=tk.LEFT, padx=6)

        self.feedback = theme.label(self, "", size=theme.SIZE_LABEL, weight="bold",
                                    wraplength=760, justify="center")
        self.feedback.pack(pady=18)

        self.progress = theme.label(self, "", size=theme.SIZE_SMALL, fg=theme.MUTED)
        self.progress.pack(side=tk.BOTTOM, pady=18)

    # -- lifecycle ----------------------------------------------------
    def on_roster_changed(self):
        self.start()

    def on_show(self):
        if not self.remaining and not self.game_over:
            self.start()
        self.entry.focus_set()

    def on_hide(self):
        pass

    def handles_typing(self, widget):
        return widget is self.entry

    # -- game ---------------------------------------------------------
    def start(self):
        if not self.app.students:
            return
        self.remaining = self.app.students.copy()
        random.shuffle(self.remaining)
        self.perfect = []
        self.streak = 0
        self.longest = 0
        self.game_over = False
        if self.restart_btn is not None:
            self.restart_btn.destroy()
            self.restart_btn = None
        for btn, primary in ((self.submit_btn, True), (self.hint_btn, False), (self.skip_btn, False)):
            btn.config(state="normal", fg=theme.TEXT,
                       bg=theme.ACCENT if primary else theme.SURFACE)
        self.next_student()
        self.update_stats()

    def next_student(self):
        if self.game_over:
            return
        if not self.remaining:
            self.finish()
            return
        self.current = self.remaining[0]
        self.used_hint = False
        self.hint_level = 0
        try:
            photo = theme.photo(self.current["path"])
            self.photo_label.config(image=photo, text="")
            self.photo_label.image = photo
        except Exception as exc:                      # noqa: BLE001
            self.photo_label.config(image="", text=f"Could not open image\n{exc}")
        self.entry.delete(0, tk.END)
        self.feedback.config(text="", fg=theme.TEXT)
        self.hint_btn.config(state="normal")
        self.entry.focus_set()

    def close_enough(self, answer, correct):
        given, want = answer.split(), correct.split()
        if not given or not want:
            return False
        return given[0] == want[0] or (len(want) >= 2 and given[-1] == want[-1])

    def check(self):
        if not self.current or self.game_over:
            return
        answer = self.entry.get().strip().lower()
        correct = self.current["name"].lower()
        if answer and (answer == correct or self.close_enough(answer, correct)):
            self.streak += 1
            self.longest = max(self.longest, self.streak)
            self.remaining.remove(self.current)
            if not self.used_hint:
                self.perfect.append(self.current)
            self.feedback.config(text=f"Correct — {self.current['name']}", fg=theme.OK)
            self.update_stats()
            self.after(1200, self.next_student)
        else:
            self.streak = 0
            self.feedback.config(text=f"Not quite — that was {self.current['name']}",
                                 fg=theme.STOP)
            self.after(1800, self.finish)

    def hint(self):
        if not self.current or self.game_over:
            return
        self.used_hint = True
        name = self.current["name"]
        own = theme.load_hints().get(self.current["key"])
        if self.hint_level == 0 and own:
            text = own
        elif self.hint_level <= 1:
            text = f"Their first name starts with '{name.split()[0][0].upper()}'"
        else:
            text = f"The answer is {name}"
            self.hint_btn.config(state="disabled")
        self.hint_level += 1
        self.feedback.config(text=text, fg=theme.HINT)

    def skip(self):
        if not self.current or self.game_over:
            return
        self.streak = 0
        self.feedback.config(text=f"Skipped — that was {self.current['name']}", fg=theme.STOP)
        self.after(1500, self.finish)

    def finish(self):
        if self.game_over:
            return
        self.game_over = True
        total = len(self.app.students)
        done = total - len(self.remaining)
        if not self.remaining and len(self.perfect) == total:
            text, colour = (f"Perfect game\n\nAll {total} students, no hints used."
                            f"\nLongest streak {self.longest}", theme.OK)
        elif not self.remaining:
            text, colour = (f"Finished\n\nAll {total} students."
                            f"\nWithout hints {len(self.perfect)}"
                            f"\nLongest streak {self.longest}", theme.ACCENT)
        else:
            missed = self.current["name"] if self.current else "unknown"
            text, colour = (f"Game over\n\nMissed {missed}\nCompleted {done} of {total}"
                            f"\nWithout hints {len(self.perfect)}"
                            f"\nLongest streak {self.longest}", theme.STOP)
        self.feedback.config(text=text, fg=colour)
        for btn in (self.submit_btn, self.hint_btn, self.skip_btn):
            btn.config(state="disabled", fg=theme.MUTED, bg=theme.SURFACE)
        if self.restart_btn is None:
            self.restart_btn = theme.button(self.buttons, "Start new game",
                                            self.start, primary=True)
            self.restart_btn.pack(side=tk.LEFT, padx=6)
        self.update_stats()

    def update_stats(self):
        total = len(self.app.students)
        done = total - len(self.remaining)
        self.streak_label.config(
            text=f"Current streak {self.streak}  ·  longest {self.longest}")
        self.progress.config(
            text=f"{done} of {total} named  ·  {len(self.perfect)} without a hint")

    def on_return(self):
        if self.game_over:
            self.start()
        else:
            self.check()


class PrepareView(tk.Frame):
    """Build a photo folder from a roster page saved out of the browser.

    Three states, one at a time: choose a roster, confirm what was found, see
    the result. Showing all three at once made a wall of text.
    """

    HOW_TO = (
        "Open your photo roster in the browser, signed in as usual.\n\n"
        "Then File \u2192 Save Page As, and choose \u201cWeb Page, complete\u201d "
        "so the photos are saved too.\n\n"
        "Point this at whatever it saved \u2014 the page or the folder beside it."
    )

    def __init__(self, parent, app):
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self.html_path = None
        self.info = None
        self.prepared_folder = None
        self._build()
        self._go("get")

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
        """A panel so the content reads as an object, not text adrift on navy."""
        card = tk.Frame(parent, bg=theme.SURFACE, highlightthickness=1,
                        highlightbackground=theme.BORDER)
        card.pack(fill=tk.X, padx=40, pady=(28, 0))
        inner = tk.Frame(card, bg=theme.SURFACE)
        inner.pack(fill=tk.X, padx=30, pady=26)
        return inner

    def _build(self):
        header = tk.Frame(self, bg=theme.BG)
        header.pack(fill=tk.X, padx=32, pady=(24, 8))
        theme.label(header, "Prepare photos", size=theme.SIZE_TITLE,
                    weight="bold").pack(anchor="w")
        self.subtitle = theme.label(header, "", size=theme.SIZE_BODY, fg=theme.MUTED)
        self.subtitle.pack(anchor="w", pady=(2, 0))

        tk.Frame(self, bg=theme.BORDER, height=1).pack(fill=tk.X, padx=32, pady=(12, 0))

        body = tk.Frame(self, bg=theme.BG)
        body.pack(fill=tk.BOTH, expand=True)
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)

        self.steps = {}
        for name in ("get", "import", "confirm", "done"):
            frame = tk.Frame(body, bg=theme.BG)
            frame.grid(row=0, column=0, sticky="nsew")
            self.steps[name] = frame

        # --- choose
        # --- step 1: get the roster out of the browser
        card = self._card(self.steps["get"])
        theme.label(card, "Step 1", size=theme.SIZE_SMALL, fg=theme.ACCENT,
                    bg=theme.SURFACE).pack(anchor="w")
        theme.label(card, "Get your roster", size=theme.SIZE_LABEL, weight="bold",
                    bg=theme.SURFACE).pack(anchor="w", pady=(2, 8))
        theme.label(card,
                    "Opens the registrar's photo roster in your browser, where you are\n"
                    "already signed in. Save it there with File \u2192 Save Page As.",
                    size=theme.SIZE_SMALL, fg=theme.MUTED, bg=theme.SURFACE,
                    justify="left").pack(anchor="w", pady=(0, 16))
        theme.button(card, "Open my photo rosters", self.open_roster_app,
                     primary=True).pack(anchor="w")

        foot = tk.Frame(self.steps["get"], bg=theme.BG)
        foot.pack(fill=tk.X, padx=40, pady=(14, 0))
        self._link(foot, "What exactly do I save?",
                   lambda: messagebox.showinfo("Saving the roster", self.HOW_TO)
                   ).pack(side=tk.LEFT)
        self._link(foot, "I already saved it  \u2192", lambda: self._go("import"),
                   fg=theme.ACCENT).pack(side=tk.RIGHT)

        # --- step 2: import what the browser saved
        card = self._card(self.steps["import"])
        theme.label(card, "Step 2", size=theme.SIZE_SMALL, fg=theme.ACCENT,
                    bg=theme.SURFACE).pack(anchor="w")
        theme.label(card, "Import it here", size=theme.SIZE_LABEL, weight="bold",
                    bg=theme.SURFACE).pack(anchor="w", pady=(2, 8))
        theme.label(card,
                    "Point this at the page your browser saved, or the folder beside it.",
                    size=theme.SIZE_SMALL, fg=theme.MUTED, bg=theme.SURFACE,
                    justify="left").pack(anchor="w", pady=(0, 16))
        theme.button(card, "Choose saved roster\u2026", self.choose_page,
                     primary=True).pack(anchor="w")

        foot = tk.Frame(self.steps["import"], bg=theme.BG)
        foot.pack(fill=tk.X, padx=40, pady=(14, 0))
        self._link(foot, "\u2190  back to step 1", lambda: self._go("get")).pack(side=tk.LEFT)

        # --- confirm
        confirm = self.steps["confirm"]
        inner = tk.Frame(confirm, bg=theme.BG)
        inner.place(relx=0.5, rely=0.42, anchor="center")
        self.course_line = theme.label(inner, "", size=theme.SIZE_LABEL, weight="bold")
        self.course_line.pack()
        self.detail_line = theme.label(inner, "", size=theme.SIZE_BODY, fg=theme.MUTED)
        self.detail_line.pack(pady=(4, 22))

        theme.label(inner, "Save these photos as", size=theme.SIZE_SMALL,
                    fg=theme.MUTED).pack()
        self.label_var = tk.StringVar()
        self.label_entry = tk.Entry(
            inner, textvariable=self.label_var, width=26, justify="center",
            font=theme.font(theme.SIZE_BODY), bg=theme.SURFACE, fg=theme.TEXT,
            insertbackground=theme.TEXT, relief=tk.FLAT, bd=0, highlightthickness=1,
            highlightbackground=theme.BORDER, highlightcolor=theme.ACCENT
        )
        self.label_entry.pack(ipady=6, pady=(6, 4))
        self.campus_hint = theme.label(inner, "", size=theme.SIZE_SMALL, fg=theme.MUTED)
        self.campus_hint.pack()

        steps_text = (
            "Reads the names off the page, copies each photo as "
            "LastName_FirstName,\nskips anyone the roster has no photo for, and "
            "writes them to your Pictures folder."
        )
        theme.label(inner, steps_text, size=theme.SIZE_SMALL, fg=theme.MUTED,
                    justify="center").pack(pady=(18, 0))
        theme.button(inner, "Prepare photos", self.run, primary=True).pack(pady=(14, 0))
        self._link(inner, "Choose a different roster", self.choose_page).pack(pady=(12, 0))

        # --- done
        done = self.steps["done"]
        inner = tk.Frame(done, bg=theme.BG)
        inner.place(relx=0.5, rely=0.42, anchor="center")
        self.result_headline = theme.label(inner, "", size=theme.SIZE_FEATURE,
                                           weight="bold")
        self.result_headline.pack()
        self.result_path = theme.label(inner, "", size=theme.SIZE_SMALL, fg=theme.MUTED,
                                       wraplength=700, justify="center")
        self.result_path.pack(pady=(8, 0))
        self.result_missing = theme.label(inner, "", size=theme.SIZE_SMALL,
                                          fg=theme.MUTED, wraplength=700,
                                          justify="center")
        self.result_missing.pack(pady=(14, 0))
        theme.button(inner, "Open it in Study", self.open_result,
                     primary=True).pack(pady=(24, 0))

        self.tidy_note = theme.label(
            inner,
            "The saved roster page also holds student ID numbers.\n"
            "You do not need it any more.",
            size=theme.SIZE_SMALL, fg=theme.MUTED, justify="center")
        self.tidy_note.pack(pady=(22, 4))
        self.tidy_link = self._link(inner, "Delete the saved roster page",
                                    self.discard_source)
        self.tidy_link.pack()

        self._link(inner, "Prepare another section",
                   lambda: self._go("get")).pack(pady=(16, 0))

        theme.label(self, "Photos stay on this computer. Nothing is uploaded.",
                    size=theme.SIZE_SMALL, fg=theme.MUTED).pack(side=tk.BOTTOM, pady=18)

    def _go(self, step):
        self.subtitle.config(text={
            "get": "First, save your roster out of the browser.",
            "import": "Now bring that saved roster in here.",
            "confirm": "Check this is the right section, then name the folder.",
            "done": "Ready to practise.",
        }[step])
        self.steps[step].tkraise()

    # -- lifecycle ----------------------------------------------------
    def on_show(self):
        pass

    def on_hide(self):
        pass

    def on_roster_changed(self):
        pass

    def handles_typing(self, widget):
        return widget is self.label_entry

    # -- actions ------------------------------------------------------
    def open_roster_app(self):
        webbrowser.open(prepare.ROSTER_APP)
        # They have gone to the browser to save it; be waiting on step 2.
        self._go("import")

    def choose_page(self):
        picked = filedialog.askopenfilename(
            parent=self.app.root,
            title="Choose the saved roster",
            initialdir=next((d for d in (
                os.path.expanduser("~/Desktop"), os.path.expanduser("~/Downloads"),
                os.path.expanduser("~")) if os.path.isdir(d)), None),
            filetypes=[("Saved web page", "*.html *.htm"), ("All files", "*.*")],
        )
        if not picked:
            return

        path = prepare.resolve(picked)
        if not path:
            messagebox.showwarning(
                "Prepare photos",
                "That does not look like a saved roster.\n\n"
                "Choose the .html file the browser saved, or the folder next to it."
            )
            return

        try:
            info = prepare.read(path)
        except OSError as exc:
            messagebox.showerror("Prepare photos", f"Could not read that page.\n\n{exc}")
            return

        if not info["students"] or not info["files_dir_exists"]:
            messagebox.showwarning(
                "Prepare photos",
                "No photos found with that page.\n\n"
                "It needs to be saved as \u201cWeb Page, complete\u201d, which also "
                "saves a folder of images beside it."
            )
            return

        self.html_path, self.info = path, info
        self.course_line.config(
            text=f"{info['number']}: {info['title']}" if info["number"] else "Roster")
        bits = [f"CRN {info['crn']}"] if info["crn"] else []
        if info["term"]:
            bits.append(f"term {info['term']}")
        bits.append(f"{len(info['students'])} students")
        self.detail_line.config(text="  \u00b7  ".join(bits))
        self.label_var.set(info["label"])
        self.campus_hint.config(
            text=f"Teaching two sections of {info['number'] or 'this course'}? "
                 "Add the campus." if info["number"] else "")
        self._go("confirm")

    def run(self):
        if not self.html_path:
            return
        out_root = os.path.join(os.path.expanduser("~"), "Pictures", "student-headshots")
        try:
            outcome = prepare.prepare(self.html_path, out_root, self.label_var.get())
        except OSError as exc:
            messagebox.showerror("Prepare photos", f"Could not write the photos.\n\n{exc}")
            return

        self.prepared_folder = outcome["folder"]
        prepare.remember_section(os.path.basename(outcome["folder"]),
                                 self.info.get("term"), self.info.get("crn"))
        self.app.refresh_roster_menu()
        self.result_headline.config(
            text=f"{outcome['written']} photos ready", fg=theme.OK)
        self.tidy_note.config(text="The saved roster page also holds student ID "
                                   "numbers.\nYou do not need it any more.")
        self.tidy_link.pack()
        self.result_path.config(text=outcome["folder"])
        if outcome["missing"]:
            self.result_missing.config(
                text="No photo on the roster for "
                     + ", ".join(sorted(outcome["missing"]))
                     + ". Listed in NO-PHOTO.txt.")
        else:
            self.result_missing.config(text="")
        self._go("done")

    def discard_source(self):
        """Offer to remove the saved page now the photos are copied out."""
        if not self.html_path or not os.path.exists(self.html_path):
            return
        page, folder = prepare.saved_pair(self.html_path)
        if not messagebox.askyesno(
            "Delete the saved roster",
            "Delete these? The photos you just prepared are not affected.\n\n"
            f"{page}\n{folder}\n\n"
            "The page holds student ID numbers as well as names and photos, "
            "so it is worth not leaving it around."
        ):
            return
        try:
            prepare.discard(self.html_path)
        except OSError as exc:
            messagebox.showerror("Delete the saved roster",
                                 f"Could not delete it.\n\n{exc}")
            return
        self.html_path = None
        self.tidy_note.config(text="Saved roster deleted.")
        self.tidy_link.pack_forget()

    def open_result(self):
        if self.prepared_folder:
            self.app.set_folder(self.prepared_folder)
            self.app.show("study")


class NameGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Name Game")
        self.root.configure(bg=theme.BG)
        self.students = []
        self.folder = None

        self.course_label = theme.label(root, "", size=theme.SIZE_LABEL,
                                        weight="bold", fg=theme.ACCENT)
        self.course_label.place(relx=1.0, y=18, anchor="ne", x=-32)

        # Both screens share one cell, so the window is sized for the larger of
        # the two and never resizes when you switch.
        container = tk.Frame(root, bg=theme.BG)
        container.pack(fill=tk.BOTH, expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.study = StudyView(container, self)
        self.quiz = QuizView(container, self)
        self.prepare_view = PrepareView(container, self)
        for view in (self.study, self.quiz, self.prepare_view):
            view.grid(row=0, column=0, sticky="nsew")
        self.course_label.lift()   # the container is packed over it otherwise

        self.mode = tk.StringVar(value="study")
        self._build_menu()
        self._bind_keys()

        folder = roster.load_last_folder()
        if folder and messagebox.askyesno(
            "Photo folder", f"Use the same photo folder as last time?\n\n{folder}"
        ):
            self.set_folder(folder)

        # A colleague opening this for the first time has no photos yet, so
        # start them on the screen that makes some rather than an empty picker.
        self.show("study" if self.students else "prepare")
        theme.fit_window(self.root)

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Prepare photos from a saved roster\u2026",
                              command=lambda: self.show("prepare"))
        self.roster_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Open a roster in the browser",
                              menu=self.roster_menu)
        self.refresh_roster_menu()
        file_menu.add_command(label="Change photo folder", command=self.choose_folder)
        file_menu.add_separator()
        file_menu.add_radiobutton(label="Study", variable=self.mode, value="study",
                                  command=lambda: self.show("study"))
        file_menu.add_radiobutton(label="Quiz", variable=self.mode, value="quiz",
                                  command=lambda: self.show("quiz"))
        file_menu.add_radiobutton(label="Prepare photos", variable=self.mode,
                                  value="prepare", command=lambda: self.show("prepare"))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)

    def _bind_keys(self):
        def shortcut(action):
            def handler(event):
                view = self.current_view()
                if view.handles_typing(event.widget):
                    return None
                action()
                return "break"
            return handler

        self.root.bind("<space>", shortcut(lambda: self.study.next()))
        self.root.bind("<Left>", shortcut(lambda: self.study.previous()))
        self.root.bind("<Right>", shortcut(lambda: self.study.next()))
        self.root.bind("s", shortcut(lambda: self.study.shuffle()))
        self.root.bind("a", shortcut(lambda: self.study.toggle_auto()))
        self.root.bind("<Return>", self._on_return)
        self.root.bind("<Control-Tab>", lambda e: self.toggle_mode())

    def _on_return(self, _event=None):
        if self.current_view() is self.quiz:
            self.quiz.on_return()
        return "break"

    VIEWS = ("study", "quiz", "prepare")

    def refresh_roster_menu(self):
        """List sections already imported, so their roster is one click away."""
        self.roster_menu.delete(0, "end")
        known = sorted(prepare.known_sections().items())
        if not known:
            self.roster_menu.add_command(label="None imported yet", state="disabled")
            return
        for label, where in known:
            self.roster_menu.add_command(
                label=f"{label}  \u00b7  CRN {where['crn']}",
                command=lambda w=where: webbrowser.open(
                    prepare.roster_url(w["term"], w["crn"]))
            )

    def current_view(self):
        return {"quiz": self.quiz, "prepare": self.prepare_view}.get(
            self.mode.get(), self.study)

    def show(self, mode):
        leaving = self.current_view()
        self.mode.set(mode)
        entering = self.current_view()
        if leaving is not entering:
            leaving.on_hide()
        entering.tkraise()
        entering.on_show()

    def toggle_mode(self):
        """Ctrl+Tab flips between the two practice screens only."""
        self.show("quiz" if self.mode.get() == "study" else "study")

    def choose_folder(self):
        folder = theme.ask_folder(self.root, self.folder)
        if folder:
            self.set_folder(folder)

    def set_folder(self, folder):
        students = roster.load(folder)
        if not students:
            messagebox.showwarning("Name Game", "No photos found in that folder.")
            return
        self.folder = folder
        self.students = students
        roster.save_last_folder(folder)
        self.course_label.config(text=theme.course_name(folder))
        for view in (self.study, self.quiz):
            view.on_roster_changed()


def main():
    root = tk.Tk()
    NameGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
