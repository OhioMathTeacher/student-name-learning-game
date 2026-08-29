#!/usr/bin/env python3
"""Name Game - learn your students' names from their photos.

One window, two screens. Study walks the roster showing each name; Quiz hides
it and asks. They were separate programs, and switching modes actually quit one
process and started another, which is why the window used to jump. Now they are
two frames in the same window and switching just raises one.

Photos are named LastName_FirstName.jpg in a folder per section.
"""

import random
import tkinter as tk
from tkinter import messagebox

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
        for view in (self.study, self.quiz):
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
        else:
            self.choose_folder()

        self.show("study")
        theme.fit_window(self.root)

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Change photo folder", command=self.choose_folder)
        file_menu.add_separator()
        file_menu.add_radiobutton(label="Study", variable=self.mode, value="study",
                                  command=lambda: self.show("study"))
        file_menu.add_radiobutton(label="Quiz", variable=self.mode, value="quiz",
                                  command=lambda: self.show("quiz"))
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

    def current_view(self):
        return self.quiz if self.mode.get() == "quiz" else self.study

    def show(self, mode):
        leaving = self.current_view()
        self.mode.set(mode)
        entering = self.current_view()
        if leaving is not entering:
            leaving.on_hide()
        entering.tkraise()
        entering.on_show()

    def toggle_mode(self):
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
    app = NameGame(root)
    if app.students:
        root.mainloop()
    else:
        root.destroy()


if __name__ == "__main__":
    main()
