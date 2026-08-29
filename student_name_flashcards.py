#!/usr/bin/env python3
"""
Student Name Flashcards - Study Mode
Shows student photos with their names so you can learn them
"""

import tkinter as tk

import theme
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import random
import json

def get_config_path():
    """Get path for storing app configuration"""
    home_dir = os.path.expanduser("~")
    config_dir = os.path.join(home_dir, ".student_name_game")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    return os.path.join(config_dir, "config.json")

def save_folder(folder):
    """Save the current folder to config"""
    config_path = get_config_path()
    try:
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        config['last_folder'] = folder
        with open(config_path, 'w') as f:
            json.dump(config, f)
    except Exception as e:
        print(f"Error saving folder: {e}")

def load_folder():
    """Load the last used folder from config"""
    config_path = get_config_path()
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('last_folder')
    except Exception as e:
        print(f"Error loading folder: {e}")
    return None

class StudentFlashcards:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Name Flashcards - Study Mode")
        self.root.geometry("800x900")
        self.root.configure(bg=theme.BG)
        
        # Data
        self.students = []
        self.current_index = 0
        self.auto_advance = False
        self.auto_delay = 3000  # 3 seconds default
        self.after_id = None
        
        # Create UI
        self.create_widgets()
        
        # Try to load last used folder, or default folder
        last_folder = load_folder()
        if last_folder and os.path.exists(last_folder):
            self.load_photos(last_folder)
        else:
            default_folder = os.path.expanduser("~/Desktop/Section A")
            if os.path.exists(default_folder):
                self.load_photos(default_folder)
            else:
                self.choose_folder()

        theme.fit_window(self.root)

    def create_widgets(self):
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Change Photo Folder", command=self.choose_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Switch to Quiz Mode", command=self.switch_to_quiz)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # ---- header -------------------------------------------------
        header = tk.Frame(self.root, bg=theme.BG)
        header.pack(fill=tk.X, padx=32, pady=(24, 8))

        theme.label(header, "Study Mode", size=theme.SIZE_TITLE, weight="bold").pack(anchor="w")
        theme.label(header, "Look at the face, then read the name.",
                    size=theme.SIZE_BODY, fg=theme.MUTED).pack(anchor="w", pady=(2, 0))

        self.course_label = theme.label(header, "", size=theme.SIZE_LABEL,
                                        weight="bold", fg=theme.ACCENT)
        self.course_label.place(relx=1.0, rely=0.0, anchor="ne")

        tk.Frame(self.root, bg=theme.BORDER, height=1).pack(fill=tk.X, padx=32, pady=(12, 0))

        # ---- photo ----------------------------------------------------
        self.photo_frame = tk.Frame(self.root, bg=theme.BG)
        self.photo_frame.pack(pady=(28, 0))

        self.photo_label = tk.Label(
            self.photo_frame,
            bg=theme.SURFACE,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground=theme.BORDER
        )
        self.photo_label.pack()

        self.name_label = tk.Label(
            self.root,
            text="",
            font=theme.font(theme.SIZE_FEATURE, "bold"),
            bg=theme.BG,
            fg=theme.TEXT
        )
        self.name_label.pack(pady=(22, 4))

        self.counter_label = theme.label(self.root, "Student 0 of 0",
                                         size=theme.SIZE_BODY, fg=theme.MUTED)
        self.counter_label.pack(pady=(0, 24))

        # ---- memory hint ---------------------------------------------
        hint_frame = tk.Frame(self.root, bg=theme.BG)
        hint_frame.pack(fill=tk.X, padx=90, pady=(0, 18))

        theme.label(hint_frame, "Memory hint", size=theme.SIZE_SMALL,
                    fg=theme.MUTED).pack(anchor="w")

        self.hint_entry = tk.Entry(
            hint_frame,
            font=theme.font(theme.SIZE_BODY),
            bg=theme.SURFACE, fg=theme.TEXT,
            insertbackground=theme.TEXT,
            relief=tk.FLAT, bd=0,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
            highlightcolor=theme.ACCENT
        )
        self.hint_entry.pack(fill=tk.X, ipady=6, pady=(4, 2))
        self.hint_entry.bind("<Return>", lambda e: self.save_current_hint())
        self.hint_entry.bind("<FocusOut>", lambda e: self.save_current_hint())

        self.hint_status = theme.label(hint_frame, "", size=theme.SIZE_SMALL,
                                       fg=theme.MUTED)
        self.hint_status.pack(anchor="w")

        # ---- primary controls ----------------------------------------
        button_frame = tk.Frame(self.root, bg=theme.BG)
        button_frame.pack()

        self.prev_btn = theme.button(button_frame, "\u2039  Previous", self.previous_student)
        self.prev_btn.pack(side=tk.LEFT, padx=6)

        self.next_btn = theme.button(button_frame, "Next  \u203a", self.next_student, primary=True)
        self.next_btn.pack(side=tk.LEFT, padx=6)

        self.shuffle_btn = theme.button(button_frame, "Shuffle", self.shuffle_students)
        self.shuffle_btn.pack(side=tk.LEFT, padx=6)

        self.folder_btn = theme.button(button_frame, "Change folder", self.choose_folder)
        self.folder_btn.pack(side=tk.LEFT, padx=6)

        # ---- auto-advance --------------------------------------------
        auto_frame = tk.Frame(self.root, bg=theme.BG)
        auto_frame.pack(pady=(18, 0))

        self.auto_btn = theme.button(auto_frame, "Auto-advance", self.toggle_auto_advance)
        self.auto_btn.pack(side=tk.LEFT, padx=(0, 12))

        theme.label(auto_frame, "every", size=theme.SIZE_BODY, fg=theme.MUTED).pack(side=tk.LEFT)

        self.speed_var = tk.StringVar(value="3")
        self.speed_menu = tk.OptionMenu(auto_frame, self.speed_var,
                                        *["1", "2", "3", "4", "5", "7", "10"],
                                        command=self.update_speed)
        self.speed_menu.config(
            font=theme.font(theme.SIZE_BODY), bg=theme.SURFACE, fg=theme.TEXT,
            activebackground=theme.SURFACE_ACTIVE, activeforeground=theme.TEXT,
            relief=tk.FLAT, bd=0, highlightthickness=1,
            highlightbackground=theme.BORDER, cursor="hand2"
        )
        self.speed_menu["menu"].config(bg=theme.SURFACE, fg=theme.TEXT,
                                       activebackground=theme.ACCENT,
                                       activeforeground=theme.TEXT, bd=0)
        self.speed_menu.pack(side=tk.LEFT, padx=8)

        theme.label(auto_frame, "seconds", size=theme.SIZE_BODY, fg=theme.MUTED).pack(side=tk.LEFT)

        # ---- footer ---------------------------------------------------
        theme.label(
            self.root,
            "Space next  \u00b7  \u2190 previous  \u00b7  S shuffle  \u00b7  A auto-advance",
            size=theme.SIZE_SMALL, fg=theme.MUTED
        ).pack(pady=(22, 18))

        # Bind keyboard shortcuts
        self.root.bind('<space>', self._shortcut(self.next_student))
        self.root.bind('<Left>', lambda e: self.previous_student())
        self.root.bind('<Right>', lambda e: self.next_student())
        self.root.bind('s', self._shortcut(self.shuffle_students))
        self.root.bind('a', self._shortcut(self.toggle_auto_advance))
    
    def choose_folder(self):
        folder = theme.ask_folder(self.root, load_folder())
        if folder:
            self.load_photos(folder)
    
    def load_photos(self, folder):
        self.students = []
        supported_formats = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
        
        for filename in os.listdir(folder):
            if filename.lower().endswith(supported_formats):
                filepath = os.path.join(folder, filename)
                # Extract name from filename (handle both formats)
                name_part = os.path.splitext(filename)[0]
                if '_' in name_part:
                    # Files are written LastName_FirstName, so show "First Last".
                    last, _, first = name_part.partition('_')
                    name = f"{first} {last}".strip() if first else last
                else:
                    name = name_part
                
                self.students.append({
                    'name': name,
                    'filepath': filepath
                })
        
        if self.students:
            # Save this folder as the last used
            save_folder(folder)
            self.course_label.config(text=theme.course_name(folder))
            self.current_index = 0
            self.show_current_student()
        else:
            messagebox.showwarning("No Photos", "No photos found in the selected folder.")
    
    def _shortcut(self, action):
        """Ignore single-key shortcuts while the hint box has focus."""
        def handler(event):
            if event.widget is getattr(self, 'hint_entry', None):
                return None
            action()
            return "break"
        return handler

    def save_current_hint(self):
        if not self.students:
            return
        key = theme.hint_key(self.students[self.current_index]['filepath'])
        theme.save_hint(key, self.hint_entry.get())
        self.hint_status.config(text="Saved")
        self.root.after(1200, lambda: self.hint_status.config(text=""))

    def show_current_student(self):
        if not self.students:
            return
        
        student = self.students[self.current_index]
        
        # Update counter
        self.counter_label.config(
            text=f"Student {self.current_index + 1} of {len(self.students)}"
        )
        
        # Load and display photo
        try:
            photo = theme.photo(student['filepath'])
            self.photo_label.config(image=photo)
            self.photo_label.image = photo  # Keep a reference
        except Exception as e:
            print(f"Error loading image: {e}")
            self.photo_label.config(text="Error loading image")
        
        # Display name
        self.name_label.config(text=student['name'])

        # Load this student's memory hint
        self.hint_entry.delete(0, tk.END)
        self.hint_entry.insert(0, theme.load_hints().get(theme.hint_key(student['filepath']), ""))
        self.hint_status.config(text="")
    
    def next_student(self):
        if not self.students:
            return
        self.save_current_hint()
        
        self.current_index = (self.current_index + 1) % len(self.students)
        self.show_current_student()
    
    def previous_student(self):
        if not self.students:
            return
        self.save_current_hint()
        
        self.current_index = (self.current_index - 1) % len(self.students)
        self.show_current_student()
    
    def shuffle_students(self):
        if not self.students:
            return
        self.save_current_hint()
        
        random.shuffle(self.students)
        self.current_index = 0
        self.show_current_student()
    
    def toggle_auto_advance(self):
        self.auto_advance = not self.auto_advance
        
        if self.auto_advance:
            self.auto_btn.config(text="Stop", bg=theme.STOP,
                                 activebackground=theme.STOP_ACTIVE)
            self.auto_advance_step()
        else:
            self.auto_btn.config(text="Auto-advance", bg=theme.SURFACE,
                                 activebackground=theme.SURFACE_ACTIVE)
            if self.after_id:
                self.root.after_cancel(self.after_id)
                self.after_id = None
    
    def auto_advance_step(self):
        if self.auto_advance and self.students:
            self.next_student()
            self.after_id = self.root.after(self.auto_delay, self.auto_advance_step)
    
    def update_speed(self, value):
        self.auto_delay = int(value) * 1000  # Convert to milliseconds
    
    def switch_to_quiz(self):
        """Launch the quiz mode app"""
        import subprocess
        import sys
        
        # Determine the path to the quiz app
        # This works for both development and PyInstaller bundled apps
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            base_path = sys._MEIPASS
            quiz_app = os.path.join(base_path, 'student_name_game.py')
        else:
            # Running in normal Python
            quiz_app = os.path.join(os.path.dirname(__file__), 'student_name_game.py')
        
        python_exe = sys.executable
        
        # Launch the quiz app
        subprocess.Popen([python_exe, quiz_app])
        
        # Close this app
        self.root.quit()

def main():
    root = tk.Tk()
    app = StudentFlashcards(root)
    root.mainloop()

if __name__ == "__main__":
    main()
