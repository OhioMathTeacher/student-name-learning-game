#!/usr/bin/env python3
"""Name Game - learn people's names from their photos.

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
import subprocess
import sys
import time
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox

import prepare
import progress
import roster
import theme


class DifficultyBox(tk.Label):
    """The small box on a photo's top-right corner: blank, 2, 3, then blank.

    The number is how many times that face comes up in a quiz round, at least:
    the quiz can raise it from how the face has gone, never lower it. Marking
    one during a quiz counts from the next round, since this one is already
    dealt.
    """

    CYCLE = {1: 2, 2: 3, 3: 1}

    def __init__(self, photo_label):
        super().__init__(photo_label, text="", width=2,
                         font=theme.font(theme.SIZE_BODY, "bold"),
                         bg=theme.SURFACE, fg=theme.HINT, cursor="hand2",
                         highlightthickness=2, highlightbackground=theme.MUTED, bd=0)
        self.key = None
        self.place(relx=1.0, x=-10, y=10, anchor="ne")
        self.bind("<Button-1>", lambda e: self.click())

    def show(self, key):
        self.key = key
        times = theme.load_difficulty().get(key, 1) if key else 1
        self.config(text=str(times) if times > 1 else "",
                    highlightbackground=theme.HINT if times > 1 else theme.MUTED)

    def click(self):
        if not self.key:
            return
        times = self.CYCLE[theme.load_difficulty().get(self.key, 1)]
        theme.save_difficulty(self.key, times)
        self.show(self.key)


def copies(key, marks, log):
    """How many times a face comes up in a round: 1, 2 or 3.

    From its index I, 1 + floor(3I): below 1/3 once, below 2/3 twice, above
    that three times. A face with no tries yet sits at 1/2, so a new class
    gets two looks at everyone until there is something to go on. The box on
    the photo is a floor under that.
    """
    from_index = 1 + min(2, int(3 * theme.difficulty_index(key, log)))
    return max(marks.get(key, 1), from_index)


def deal(students):
    """A quiz round: every face as many times as `copies` says.

    Each copy of a face is dropped somewhere in its own share of the round --
    the first or second half for a 2, a third each for a 3 -- and kept away
    from the edges of that share, so copies come up well apart. In a small
    class two can still land side by side; the last pass pulls the next
    different face in between them.
    """
    marks = theme.load_difficulty()
    log = theme.load_log()
    turns = []
    for s in students:
        times = copies(s["key"], marks, log)
        for i in range(times):
            turns.append(((i + 0.15 + 0.7 * random.random()) / times, s))
    turns.sort(key=lambda t: t[0])
    order = [s for _, s in turns]
    for i in range(1, len(order)):
        if order[i] is order[i - 1]:
            for j in range(i + 1, len(order)):
                if order[j] is not order[i]:
                    order.insert(i, order.pop(j))
                    break
    return order


def _describe_bundle(bundle):
    """`46 hints, 2 marks, 125 quiz answers from MacGuffey on 2026-10-28`."""
    files = bundle.get("files", {})
    def count(n, word):
        return f"{n} {word}{'' if n == 1 else 's'}"
    parts = [count(len(files.get("hints.json") or {}), "hint"),
             count(len(files.get("difficult.json") or {}), "mark"),
             count(len(bundle.get("quiz_log") or []), "quiz answer")]
    where = bundle.get("from")
    when = (bundle.get("exported") or "")[:10]
    return ", ".join(parts) + (f" from {where}" if where else "") + (f" on {when}" if when else "")


def _ask_import(root, bundle):
    """Add to, Replace, or Cancel: three plain buttons, since yes/no/cancel
    would make the reader work out which of those means which."""
    win = tk.Toplevel(root, bg=theme.BG)
    win.title("Import data")
    win.transient(root)
    win.resizable(False, False)
    choice = {"value": None}

    def pick(value):
        choice["value"] = value
        win.destroy()

    theme.label(win, "This file holds", size=theme.SIZE_BODY,
                fg=theme.MUTED).pack(padx=28, pady=(24, 2), anchor="w")
    theme.label(win, _describe_bundle(bundle), size=theme.SIZE_LABEL, weight="bold",
                wraplength=520, justify="left").pack(padx=28, anchor="w")
    theme.label(win, "Add it to the data on this computer, or replace that data "
                "with it? Either way, what is here now is kept as a .before-import copy.",
                size=theme.SIZE_BODY, wraplength=520,
                justify="left").pack(padx=28, pady=(14, 18), anchor="w")
    row = tk.Frame(win, bg=theme.BG)
    row.pack(padx=28, pady=(0, 24), anchor="e")
    theme.button(row, "Add to my data", lambda: pick("add"), primary=True).pack(side=tk.LEFT, padx=6)
    theme.button(row, "Replace my data", lambda: pick("replace")).pack(side=tk.LEFT, padx=6)
    theme.button(row, "Cancel", lambda: pick(None)).pack(side=tk.LEFT, padx=6)
    win.protocol("WM_DELETE_WINDOW", lambda: pick(None))
    win.bind("<Escape>", lambda e: pick(None))
    win.grab_set()
    root.wait_window(win)
    return choice["value"]


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
        self.difficulty = DifficultyBox(self.photo_label)

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
            self.difficulty.show(None)
            return
        self.index %= len(students)
        student = students[self.index]
        self.counter_label.config(text=f"Person {self.index + 1} of {len(students)}")
        try:
            photo = theme.photo(student["path"])
            self.photo_label.config(image=photo, text="")
            self.photo_label.image = photo
        except Exception as exc:                      # noqa: BLE001 - show, don't crash
            self.photo_label.config(image="", text=f"Could not open image\n{exc}")
        self.name_label.config(text=student["name"])
        self.difficulty.show(student["key"])
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
        self.answered = False
        self.round_total = 0
        self.shown_at = 0.0
        self.first_key = None       # seconds from photo to first keystroke
        self.round_no = None        # set by the first answer of a round
        self.turn = 0               # answers given this round, skips included
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
        self.difficulty = DifficultyBox(self.photo_label)

        theme.label(self, "Name", size=theme.SIZE_BODY, fg=theme.MUTED).pack()
        self.entry = tk.Entry(
            self, font=theme.font(theme.SIZE_INPUT), width=22, justify="center",
            bg=theme.SURFACE, fg=theme.TEXT, insertbackground=theme.TEXT,
            relief=tk.FLAT, bd=0, highlightthickness=1,
            highlightbackground=theme.BORDER, highlightcolor=theme.ACCENT
        )
        self.entry.pack(ipady=8, pady=(6, 18))
        self.entry.bind("<KeyPress>", self._first_key, add="+")

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
        # A round nobody has touched yet is dealt again, so faces marked in
        # Study since it was dealt come up as often as their box says.
        untouched = (len(self.remaining) == self.round_total
                     and self.skips_left == 3 and not self.answered)
        if not self.game_over and (not self.remaining or untouched):
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
        self.remaining = deal(self.app.students)
        self.round_no = None
        self.turn = 0
        self.round_total = len(self.remaining)
        self.perfect = []
        self.streak = 0
        self.longest = 0
        self.skips_left = 3
        self.game_over = False
        self.answered = False
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
        self.difficulty.show(self.current["key"])
        self.answered = False
        self.used_hint = False
        self.hint_level = 0
        self.shown_at = time.monotonic()
        self.first_key = None
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

    def record(self, result, typed=None):
        """Log this answer. A round takes its number from its first answer;
        a round dealt and never played (at launch, or re-dealt on the way into
        Quiz) would otherwise age every face's history for nothing."""
        if self.round_no is None:
            self.round_no = theme.last_round() + 1
        self.turn += 1
        theme.log_answer(
            key=self.current["key"], label=self.current["label"],
            round=self.round_no, turn=self.turn,
            of=self.round_total, result=result,
            seconds=None if self.first_key is None else round(self.first_key, 2),
            typed=typed)

    def _first_key(self, event):
        """Time to the first letter typed: recognising the face, not typing it."""
        if self.first_key is None and event.char and event.char.isprintable():
            self.first_key = time.monotonic() - self.shown_at

    def close_enough(self, answer, correct):
        given, want = answer.split(), correct.split()
        if not given or not want:
            return False
        return given[0] == want[0] or (len(want) >= 2 and given[-1] == want[-1])

    def check(self):
        if not self.current or self.game_over or self.answered:
            return
        answer = self.entry.get().strip().lower()
        if not answer:
            # Enter on an empty box is a stray keystroke, not a wrong answer.
            # It used to end the run, which is a cruel way to lose a streak of
            # nineteen.
            return
        correct = self.current["name"].lower()
        self.answered = True
        if answer == correct or self.close_enough(answer, correct):
            self.record("hint" if self.used_hint
                        else "slow" if theme.is_slow(self.first_key) else "correct")
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
            self.record("miss", typed=self.entry.get().strip())
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
        if not self.current or self.game_over or self.answered:
            return
        self.answered = True
        self.streak = 0
        self.record("skip")
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
        total = self.round_total
        people = len(self.app.students)
        done = total - len(self.remaining)
        if not self.remaining and len(self.perfect) == total:
            text, colour = (f"Perfect game\n\nAll {people} people, no hints used."
                            f"\nLongest streak {self.longest}", theme.OK)
        elif not self.remaining:
            text, colour = (f"Finished\n\nAll {people} people."
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
        total = self.round_total
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
                    "Name Game practises names from a folder of photos.\n"
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
                    "you saved out of the browser and it prepares the whole term\n"
                    "into one folder \u2014 every class together.",
                    size=theme.SIZE_SMALL, fg=theme.MUTED, bg=theme.SURFACE,
                    justify="center").pack(pady=(6, 16))
        theme.button(body, "Choose a photo folder\u2026", self.app.choose_folder,
                     primary=True).pack()
        theme.label(body, "\u2026if Roster Prep already made one.",
                    size=theme.SIZE_SMALL, fg=theme.MUTED,
                    bg=theme.SURFACE).pack(pady=(8, 0))

        foot = tk.Frame(inner, bg=theme.BG)
        foot.pack(pady=(20, 0))
        sample = roster.sample_folder()
        if sample:
            # Counted from the folder, never typed: the roster has changed size twice
            # already, and a label that lies about it is worse than no label.
            n = len(roster.load(sample))
            self._link(foot, "Try it with %d sample photos" % n, self.load_sample,
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
            self.app.show("quiz")


def _short_path(path, limit=46):
    """The tail of `path`, enough to recognise without widening the menu.

    A menu sizes itself to its longest entry, and the head of a photo folder
    path -- /run/media/todd/ -- is the uninteresting half. Whole components are
    kept so the result still reads as a path rather than a truncated string.
    """
    if not path:
        return "no folder chosen yet"
    if len(path) <= limit:
        return path
    parts = path.split(os.sep)
    tail = parts[-1]
    for part in reversed(parts[:-1]):
        wider = part + os.sep + tail
        if len(wider) + 2 > limit:
            break
        tail = wider
    return "\u2026" + os.sep + tail


class NameGame:
    def __init__(self, root):
        self.root = root
        theme.scale_to_display(root)
        self.root.title("Name Game")
        self.root.configure(bg=theme.BG)
        self.students = []          # the class in front of you
        self.all_students = []      # every photo in the folder
        self.folder = None
        self.klass = ""             # "" is all students
        self.section = ""           # what the header and the score file call it

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

        self.mode = tk.StringVar(value="quiz")
        self.class_var = tk.StringVar(value="")
        self.data_var = tk.StringVar(value="home")
        self._build_menu()
        self._bind_keys()

        # One folder holds every class, so opening is a matter of finding that
        # folder -- the remembered one, or whichever drive is mounted this time.
        # The class last practised is then a filter over what is already loaded,
        # not another folder to go and find.
        # The remembered path is a hint rather than an answer. A folder that
        # still exists can have been emptied, or belong to a different drive
        # that mounted where the last one did, so it has to earn its place by
        # actually holding photos -- otherwise go and look.
        remembered = roster.load_folder()
        folder = (remembered if remembered and roster.load(remembered)
                  else roster.find_folder())
        if folder:
            self.set_folder(folder, roster.load_last_class(), announce=False)

        # A colleague opening this for the first time has no photos yet, so
        # start them on the screen that makes some rather than an empty picker.
        self.show("quiz" if self.students else "welcome")
        theme.fit_window(self.root)

    def _build_menu(self):
        """Two menus: what you are doing, and where the photos come from.

        Finding photos used to sit in the middle of File, between the class
        list and the mode switches, with nothing anywhere saying which folder
        was in use. That is what made a remembered path feel like a hard-coded
        one. Setup answers "where is it reading from" before it offers to
        change it.
        """
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        self.class_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Class", menu=self.class_menu)
        self.refresh_class_menu()
        file_menu.add_separator()
        file_menu.add_radiobutton(label="Study", variable=self.mode, value="study",
                                  command=lambda: self.show("study"))
        file_menu.add_radiobutton(label="Quiz", variable=self.mode, value="quiz",
                                  command=lambda: self.show("quiz"))
        file_menu.add_radiobutton(label="Welcome", variable=self.mode,
                                  value="welcome", command=lambda: self.show("welcome"))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)

        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Data", menu=data_menu)
        data_menu.add_command(label="Your progress\u2026",
                              command=lambda: progress.ProgressWindow(self, copies))
        data_menu.add_separator()
        data_menu.add_command(label="Export data\u2026", command=self.export_data)
        data_menu.add_command(label="Import data\u2026", command=self.import_data)

        self.setup_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Setup", menu=self.setup_menu)
        self.roster_menu = tk.Menu(self.setup_menu, tearoff=0)
        self.refresh_roster_menu()
        self.refresh_setup_menu()

    def refresh_setup_menu(self):
        """Rebuild Setup so the folder it names is the one actually in use.

        Written out each time rather than cached: the folder changes from the
        picker, from looking again, and from Roster Prep writing a new one, and
        a menu still naming the old one is worse than no menu at all.
        """
        menu = self.setup_menu
        menu.delete(0, tk.END)
        menu.add_command(label="Photos are in:", state=tk.DISABLED)
        menu.add_command(label="    " + _short_path(self.folder), state=tk.DISABLED)
        if self.all_students:
            found = len(roster.classes(self.all_students))
            summary = f"    {len(self.all_students)} photos"
            if found:
                summary += f", {found} classes" if found > 1 else ", 1 class"
            menu.add_command(label=summary, state=tk.DISABLED)
        menu.add_separator()
        menu.add_command(label="Choose a different folder\u2026",
                         command=self.choose_folder)
        menu.add_command(label="Look for them automatically",
                         command=self.find_photos)
        menu.add_separator()
        menu.add_command(label="Add a section from a saved roster\u2026",
                         command=self.open_roster_prep)
        menu.add_cascade(label="Open a roster in the browser", menu=self.roster_menu)
        menu.add_command(label="Where photos come from\u2026",
                         command=lambda: self.show("welcome"))
        menu.add_separator()
        menu.add_command(label="Keep my data:", state=tk.DISABLED)
        menu.add_command(label="    " + _short_path(roster.settings_dir()), state=tk.DISABLED)
        self.data_var.set("app" if roster.keeps_data_with_app() else "home")
        menu.add_radiobutton(label="On this computer", value="home",
                             variable=self.data_var, command=self.switch_data)
        menu.add_radiobutton(label="With the app (travels on the drive)", value="app",
                             variable=self.data_var, command=self.switch_data,
                             state=tk.NORMAL if roster.app_data_dir() else tk.DISABLED)

    def export_data(self):
        """Save everything the game has learned into one .json file."""
        from datetime import date

        docs = os.path.join(os.path.expanduser("~"), "Documents")
        path = filedialog.asksaveasfilename(
            parent=self.root, title="Export Name Game data",
            defaultextension=".json", filetypes=[("Name Game data", "*.json")],
            initialdir=docs if os.path.isdir(docs) else os.path.expanduser("~"),
            initialfile=f"name-game-data-{date.today().isoformat()}.json")
        if not path:
            return
        try:
            bundle = roster.export_data(path)
        except OSError as exc:
            messagebox.showerror("Name Game", f"Could not save.\n\n{exc}")
            return
        messagebox.showinfo("Name Game", "Saved " + _describe_bundle(bundle)
                            + f"\n\nto {path}")

    def import_data(self):
        """Bring in a file from Export data, adding to or replacing what is here."""
        path = filedialog.askopenfilename(
            parent=self.root, title="Import Name Game data",
            filetypes=[("Name Game data", "*.json"), ("All files", "*")])
        if not path:
            return
        try:
            bundle = roster.read_export(path)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Name Game", f"Could not read that file.\n\n{exc}")
            return
        choice = _ask_import(self.root, bundle)
        if choice is None:
            return
        try:
            roster.import_data(bundle, replace=(choice == "replace"))
        except OSError as exc:
            messagebox.showerror("Name Game", f"Could not import.\n\n{exc}")
            return
        self.study.show()
        self.study.refresh_streaks()
        self.refresh_roster_menu()
        messagebox.showinfo(
            "Name Game",
            ("Replaced" if choice == "replace" else "Added") + " "
            + _describe_bundle(bundle) + ".\n\nWhat was here before is kept beside "
            "it with .before-import on the end.")

    def switch_data(self):
        """Move where hints, marks, scores and the quiz log are kept.

        The data comes along, and play carries on as though nothing happened.
        Anything already at the new place is set aside as .before-switch rather
        than mixed in, so nothing is lost and there is no merge to get wrong.
        """
        on = self.data_var.get() == "app"
        if on == roster.keeps_data_with_app():
            return
        try:
            roster.keep_data_with_app(on, copy_over=True)
        except OSError as exc:
            messagebox.showerror("Name Game", f"Could not switch.\n\n{exc}")
        self.study.show()
        self.study.refresh_streaks()
        self.refresh_setup_menu()

    def find_photos(self):
        """Look at whatever is mounted now, rather than trusting the memory.

        The remembered path is a hint: one drive is `/Volumes/NAME` on a Mac,
        `/run/media/<user>/NAME` here and a bare letter on a lab PC. This is
        what to reach for when the app has opened somewhere new.
        """
        folder = roster.find_folder()
        if not folder:
            volumes = roster.removable_roots()
            where = ("\n".join("    " + v for v in volumes) if volumes
                     else "    (no removable drive is mounted)")
            messagebox.showwarning(
                "Name Game",
                f"No photos found automatically.\n\n"
                f"Looked for a folder called {roster.FOLDER_NAME} at the top of:\n"
                f"{where}\n    ~/Pictures\n    ~\n\n"
                "Use \u201cChoose a different folder\u2026\u201d if they are "
                "somewhere else.")
            return
        if folder == self.folder:
            messagebox.showinfo(
                "Name Game", f"Already using the best match:\n\n{folder}")
            return
        self.set_folder(folder)

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
        """Point the app at the folder holding the photos."""
        folder = theme.ask_folder(self.root, self.folder)
        if folder:
            self.set_folder(folder)

    def refresh_class_menu(self):
        """Everyone, then one entry per class found in the folder.

        Rebuilt from what is loaded rather than cached, so a class shows up the
        moment Roster Prep writes it instead of after a restart. Every class
        lives in the same folder now, so this is a list of filters -- there is
        no folder to go and open, and nothing here can point somewhere wrong.
        """
        self.class_menu.delete(0, tk.END)
        found = roster.classes(self.all_students)
        self.class_menu.add_radiobutton(
            label=f"All people   ({len(self.all_students)})",
            variable=self.class_var, value="",
            command=lambda: self.set_class(""))
        if not found:
            return
        self.class_menu.add_separator()
        for label in found:
            count = len(roster.in_class(self.all_students, label))
            self.class_menu.add_radiobutton(
                label=f"{label}   ({count})", variable=self.class_var,
                value=label, command=lambda l=label: self.set_class(l))

    def set_class(self, label):
        """Show one class, or all of them when `label` is empty."""
        self.klass = label if label in roster.classes(self.all_students) else ""
        self.students = roster.in_class(self.all_students, self.klass)
        self.class_var.set(self.klass)
        roster.save_last_class(self.klass)

        # What the header shows is also what the streak is filed under, so
        # a best-ever streak belongs to one class rather than to whatever was
        # last open.
        self.section = self.klass or ("All students" if self.students else "")
        self.course_label.config(text=self.section)
        for view in (self.study, self.quiz):
            view.on_roster_changed()

    def open_roster_prep(self):
        """Start Roster Prep from in here, so it needs no launcher of its own.

        A separate process rather than another screen: the two have their own
        window sizing and their own idea of what is on show, and running them
        in one process is what used to make the window jump.
        """
        base = roster.app_dir()
        if getattr(sys, "frozen", False):
            # The Windows build ships as two exes side by side.
            exe = os.path.join(base, "RosterPrep.exe")
            command = [exe] if os.path.isfile(exe) else None
        else:
            script = os.path.join(base, "roster_prep.py")
            command = [sys.executable, script] if os.path.isfile(script) else None
        if not command:
            messagebox.showinfo(
                "Name Game",
                "Roster Prep is not installed beside this copy of Name Game.\n\n"
                "It travels on the thumbdrive, next to Name Game.")
            return
        try:
            subprocess.Popen(command, cwd=base)
        except OSError as exc:
            messagebox.showerror(
                "Name Game", f"Could not start Roster Prep.\n\n{exc}")

    def set_folder(self, folder, klass=None, announce=True):
        """Load every photo in `folder`, then show `klass` (or all of them)."""
        found = roster.load(folder)
        if not found:
            if announce:
                messagebox.showwarning(
                    "Name Game",
                    f"No photos in:\n{folder}\n\n{roster.describe(folder)}")
            return
        self.folder = folder
        self.all_students = found
        roster.save_folder(folder)
        self.refresh_class_menu()
        self.set_class(self.klass if klass is None else klass)
        self.refresh_setup_menu()


def main():
    roster.restore_settings()
    root = tk.Tk()
    NameGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
