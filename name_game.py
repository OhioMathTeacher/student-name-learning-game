#!/usr/bin/env python3
"""Name Game - learn your students' names from their photos.

One window, two screens. Study walks the roster showing each name; Quiz hides
it and asks. They were separate programs, and switching modes actually quit one
process and started another, which is why the window used to jump. Now they are
two frames in the same window and switching just raises one.

Photos are named LastName_FirstName.jpg in a folder per section. Building
those folders is Roster Prep's job, in roster_prep.py -- a separate app,
because it is a start-of-term task and this is a daily one.
"""

import os
import random
import webbrowser
import tkinter as tk
from tkinter import messagebox

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

        self.streaks_label = theme.label(self, "", size=theme.SIZE_SMALL,
                                         fg=theme.MUTED, justify="center")
        self.streaks_label.pack(pady=(20, 0))

        theme.label(self, "Space next  ·  ← previous  ·  S shuffle  ·  A auto-advance",
                    size=theme.SIZE_SMALL, fg=theme.MUTED).pack(pady=(22, 18))

    # -- data ---------------------------------------------------------
    def on_roster_changed(self):
        self.index = 0
        self.show()

    def on_show(self):
        self.show()
        self.refresh_streaks()

    def refresh_streaks(self):
        """Longest streak so far, per section, from finished quiz runs."""
        scores = theme.load_scores()
        if not scores:
            self.streaks_label.config(text="")
            return
        parts = [f"{name} last {v.get('last', 0)}, best {v.get('best', 0)}"
                 for name, v in sorted(scores.items())]
        self.streaks_label.config(text="Longest streaks  \u2014  " + "   \u00b7   ".join(parts))

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
        self.skips_left = 3
        self.restart_btn = None
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=theme.BG)
        header.pack(fill=tk.X, padx=32, pady=(24, 8))
        theme.label(header, "Quiz", size=theme.SIZE_TITLE, weight="bold").pack(anchor="w")
        self.streak_label = theme.label(header, "Streak 0  ·  this run 0  ·  all-time best 0",
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
        self.hint_btn = theme.button(controls, "Hint  (Ctrl+H)", self.hint)
        self.hint_btn.pack(side=tk.LEFT, padx=6)
        self.skip_btn = theme.button(controls, "Skip  (Esc)", self.skip)
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
        self.skips_left = 3
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
            # Bank it now: quitting mid-run used to lose the whole streak.
            theme.save_score(self.app.section, self.longest)
            self.app.study.refresh_streaks()
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
        """Three free skips a run; the fourth ends it.

        A skipped student goes to the back of the queue rather than away, so
        you still have to name them before the run is over.
        """
        if not self.current or self.game_over:
            return
        self.streak = 0
        name = self.current["name"]
        if self.skips_left > 0:
            self.skips_left -= 1
            self.remaining.append(self.remaining.pop(0))
            left = self.skips_left
            tail = (f"{left} skip{'s' if left != 1 else ''} left."
                    if left else "No skips left.")
            self.feedback.config(text=f"Skipped — that was {name}. {tail}",
                                 fg=theme.HINT)
            self.update_stats()
            self.after(1200, self.next_student)
            return
        self.feedback.config(text=f"Out of skips — that was {name}", fg=theme.STOP)
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
        theme.save_score(self.app.section, self.longest)
        self.app.study.refresh_streaks()
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
        all_time = theme.load_scores().get(self.app.section, {}).get("best", 0)
        self.streak_label.config(
            text=f"Streak {self.streak}  ·  this run {self.longest}"
                 f"  ·  all-time best {all_time}")
        self.progress.config(
            text=f"{done} of {total} named  ·  {len(self.perfect)} without a hint"
                 f"  ·  {self.skips_left} skip{'s' if self.skips_left != 1 else ''} left")
        self.skip_btn.config(
            text="Skip  (Esc)" if self.skips_left else "Skip ends run  (Esc)")

    def on_return(self):
        if self.game_over:
            self.start()
        else:
            self.check()


class WelcomeView(tk.Frame):
    """What Name Game shows before there are any photos to practise with.

    This used to be the whole import wizard. Preparing photos moved to Roster
    Prep, a separate app: it is a start-of-term job done once, and it was the
    largest screen in the app you open every day. What is left is the part
    someone with no photos yet actually needs -- where photos come from, and a
    way to try the thing without any.
    """

    def __init__(self, parent, app):
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self._build()

    def _link(self, parent, text, command, fg=None):
        link = theme.label(parent, text, size=theme.SIZE_SMALL,
                           fg=fg or theme.MUTED)
        link.configure(cursor="hand2")
        link.bind("<Button-1>", lambda _e: command())
        link.bind("<Enter>", lambda _e: link.configure(fg=theme.TEXT))
        link.bind("<Leave>", lambda _e: link.configure(fg=fg or theme.MUTED))
        return link

    def _build(self):
        inner = tk.Frame(self, bg=theme.BG)
        inner.place(relx=0.5, rely=0.42, anchor="center")

        theme.label(inner, "No photos yet", size=theme.SIZE_FEATURE,
                    weight="bold").pack()
        theme.label(inner,
                    "Name Game practises names from a folder of student photos.\n"
                    "Roster Prep builds those folders from your photo rosters.",
                    size=theme.SIZE_BODY, fg=theme.MUTED,
                    justify="center").pack(pady=(10, 0))

        card = tk.Frame(inner, bg=theme.SURFACE, highlightthickness=1,
                        highlightbackground=theme.BORDER)
        card.pack(fill=tk.X, pady=(26, 0))
        body = tk.Frame(card, bg=theme.SURFACE)
        body.pack(padx=30, pady=24)
        theme.label(body, "Prepare them in Roster Prep", size=theme.SIZE_LABEL,
                    weight="bold", bg=theme.SURFACE).pack()
        theme.label(body,
                    "Roster Prep came alongside this app. Point it at the rosters\n"
                    "you saved out of the browser and it prepares the whole term.",
                    size=theme.SIZE_SMALL, fg=theme.MUTED, bg=theme.SURFACE,
                    justify="center").pack(pady=(6, 16))
        theme.button(body, "Choose a photo folder\u2026", self.app.choose_folder,
                     primary=True).pack()
        theme.label(body, "\u2026if Roster Prep already made one.",
                    size=theme.SIZE_SMALL, fg=theme.MUTED,
                    bg=theme.SURFACE).pack(pady=(8, 0))

        foot = tk.Frame(inner, bg=theme.BG)
        foot.pack(pady=(20, 0))
        self._link(foot, "Where do my classes live?",
                   self.app.choose_photo_root).pack(side=tk.LEFT)
        if roster.sample_folder():
            self._link(foot, "Try it with 5 sample students", self.load_sample,
                       fg=theme.ACCENT).pack(side=tk.LEFT, padx=(24, 0))

    # -- lifecycle ----------------------------------------------------
    def on_show(self):
        pass

    def on_hide(self):
        pass

    def on_roster_changed(self):
        pass

    def handles_typing(self, _widget):
        return False

    def load_sample(self):
        """Open the bundled fictional roster, so the app can show what it does."""
        folder = roster.sample_folder()
        if folder:
            self.app.set_folder(folder)
            self.app.show("study")


class NameGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Name Game")
        self.root.configure(bg=theme.BG)
        self.students = []
        self.folder = None
        self.section = ""

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
        self.welcome = WelcomeView(container, self)
        for view in (self.study, self.quiz, self.welcome):
            view.grid(row=0, column=0, sticky="nsew")
        self.course_label.lift()   # the container is packed over it otherwise

        self.mode = tk.StringVar(value="study")
        self.photo_root = None
        self._build_menu()
        self._bind_keys()

        # Reopen last time's section outright. This used to be a yes/no dialog,
        # which made sense when changing section meant a folder picker; now that
        # File > Open section lists them all, the prompt was a keystroke asking
        # permission to do the only sensible thing.
        folder = roster.load_last_folder()
        if folder:
            self.set_folder(folder, announce=False)
        if not self.students:
            found = roster.discover(self.photo_root) if self.photo_root else []
            if len(found) == 1:
                self.set_folder(found[0]["path"], announce=False)

        # A colleague opening this for the first time has no photos yet, so
        # start them on the screen that makes some rather than an empty picker.
        self.show("study" if self.students else "welcome")
        theme.fit_window(self.root)

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Where photos come from\u2026",
                              command=lambda: self.show("welcome"))
        self.roster_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Open a roster in the browser",
                              menu=self.roster_menu)
        self.refresh_roster_menu()
        self.section_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Open section", menu=self.section_menu)
        self.refresh_section_menu()
        file_menu.add_command(label="Change photo folder", command=self.choose_folder)
        file_menu.add_command(label="Where classes live…",
                              command=self.choose_photo_root)
        file_menu.add_separator()
        file_menu.add_radiobutton(label="Study", variable=self.mode, value="study",
                                  command=lambda: self.show("study"))
        file_menu.add_radiobutton(label="Quiz", variable=self.mode, value="quiz",
                                  command=lambda: self.show("quiz"))
        file_menu.add_radiobutton(label="Welcome", variable=self.mode,
                                  value="welcome", command=lambda: self.show("welcome"))
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
        self.root.bind("<Control-h>", self._quiz_key(lambda: self.quiz.hint()))
        self.root.bind("<Control-H>", self._quiz_key(lambda: self.quiz.hint()))
        self.root.bind("<Escape>", self._quiz_key(lambda: self.quiz.skip()))
        self.root.bind("<Control-Tab>", lambda e: self.toggle_mode())

    def _quiz_key(self, action):
        """Run `action` only while the quiz is the visible screen.

        Bound on the window rather than the entry so they still fire while the
        answer box has focus -- Ctrl+H would otherwise be swallowed as a delete.
        """
        def handler(_event=None):
            if self.current_view() is not self.quiz:
                return None
            action()
            return "break"
        return handler

    def _on_return(self, _event=None):
        if self.current_view() is self.quiz:
            self.quiz.on_return()
        return "break"

    VIEWS = ("study", "quiz", "welcome")

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
        return {"quiz": self.quiz, "welcome": self.welcome}.get(
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

    def choose_photo_root(self):
        """Point the app at the folder your class folders sit in."""
        folder = theme.ask_folder(
            self.root, self.photo_root or self.folder,
            title="Folder holding your class folders")
        if not folder:
            return
        found = roster.discover(folder)
        if not found:
            messagebox.showwarning(
                "Name Game",
                "No sections found there.\n\n"
                "Expected a folder per class, each with a headshots folder "
                "inside it:\n\n    284/headshots\n    318P/headshots-oxford")
            return
        roster.save_photo_root(folder)
        self.refresh_section_menu()
        messagebox.showinfo(
            "Name Game",
            f"{len(found)} sections found:\n\n"
            + "\n".join(f"    {s['label']}  ({s['count']} photos)" for s in found))

    def refresh_section_menu(self):
        """Rebuild the section list from disk.

        Rebuilt on every open rather than cached at launch, so a section shows
        up the moment it is prepared instead of after a restart.
        """
        self.section_menu.delete(0, tk.END)
        root, found = roster.find_sections()
        self.photo_root = root
        if not found:
            self.section_menu.add_command(label="No sections found",
                                          state="disabled")
        for section in found:
            self.section_menu.add_command(
                label=f"{section['label']}   ({section['count']} photos)",
                command=lambda path=section["path"]: self.set_folder(path))
        self.section_menu.add_separator()
        self.section_menu.add_command(label="Look again",
                                      command=self.refresh_section_menu)

    def _recover_folder(self, folder):
        """Nothing loadable in `folder`: say what is there, and offer the fix.

        Usually the pick was one level too high. A thumbdrive holds
        `rosters/headshots-hamilton`, the folder picker lists only folder
        names -- no photos to confirm against -- so `rosters` looks right
        until the app reports it empty. Look below before failing, and name
        the path either way: "No photos found in that folder" was true and
        useless, because it never said which folder or what it saw.
        """
        found = roster.photo_subfolders(folder)

        if len(found) == 1:
            path, count = found[0]
            if messagebox.askyesno(
                "Name Game",
                f"No photos directly in:\n{folder}\n\n"
                f"But {count} photos are just below, in:\n{path}\n\n"
                "Use that folder instead?"
            ):
                return path
            return None

        if found:
            listing = "\n".join(f"\u2022  {path}  \u2014  {count} photos"
                                for path, count in found[:8])
            messagebox.showinfo(
                "Name Game",
                f"No photos directly in:\n{folder}\n\n"
                f"These folders inside it do have photos. "
                f"Choose one of them instead:\n\n{listing}"
            )
            return None

        try:
            entries = os.listdir(folder)
        except OSError as exc:
            messagebox.showwarning("Name Game", f"Could not read:\n{folder}\n\n{exc}")
            return None

        files = [e for e in entries if os.path.isfile(os.path.join(folder, e))]
        messagebox.showwarning(
            "Name Game",
            f"No photos found in:\n{folder}\n\n"
            f"It holds {len(files)} files and "
            f"{len(entries) - len(files)} folders, but nothing ending "
            ".jpg, .jpeg, .png, .gif or .bmp.\n\n"
            "Pick the folder that directly contains the photo files."
        )
        return None

    def set_folder(self, folder, announce=True):
        students = roster.load(folder)
        if not students:
            if not announce:
                return
            folder = self._recover_folder(folder)
            if not folder:
                return
            students = roster.load(folder)
            if not students:
                return
        self.folder = folder
        self.students = students
        roster.save_last_folder(folder)
        root = roster.root_for(folder)
        if root and roster.discover(root):
            roster.save_photo_root(root)
            self.photo_root = root
        self.section = roster.course_name(folder)
        self.course_label.config(text=self.section)
        for view in (self.study, self.quiz):
            view.on_roster_changed()


def main():
    root = tk.Tk()
    NameGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
