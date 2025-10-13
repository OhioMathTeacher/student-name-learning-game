#!/usr/bin/env python3
"""
Student Name Flashcards - Study Mode
Shows student photos with their names so you can learn them
"""

import tkinter as tk
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
        self.root.configure(bg='#2C3E50')
        
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
    
    def create_widgets(self):
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Change Photo Folder", command=self.choose_folder)
        file_menu.add_separator()
        file_menu.add_command(label="🎯 Switch to Quiz Mode", command=self.switch_to_quiz)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Title
        title_label = tk.Label(
            self.root,
            text="📚 Study Mode - Learn Student Names",
            font=('Arial', 24, 'bold'),
            bg='#2C3E50',
            fg='white'
        )
        title_label.pack(pady=20)
        
        # Counter
        self.counter_label = tk.Label(
            self.root,
            text="Student 0 of 0",
            font=('Arial', 14),
            bg='#2C3E50',
            fg='#ECF0F1'
        )
        self.counter_label.pack(pady=5)
        
        # Photo frame
        self.photo_frame = tk.Frame(self.root, bg='#2C3E50')
        self.photo_frame.pack(pady=20)
        
        self.photo_label = tk.Label(
            self.photo_frame,
            bg='#34495E',
            relief=tk.RAISED,
            borderwidth=3
        )
        self.photo_label.pack()
        
        # Name label (large and prominent)
        self.name_label = tk.Label(
            self.root,
            text="",
            font=('Arial', 32, 'bold'),
            bg='#2C3E50',
            fg='#3498DB',
            pady=20
        )
        self.name_label.pack()
        
        # Control buttons frame
        button_frame = tk.Frame(self.root, bg='#2C3E50')
        button_frame.pack(pady=20)
        
        # Previous button
        self.prev_btn = tk.Button(
            button_frame,
            text="◀ Previous",
            command=self.previous_student,
            font=('Arial', 14, 'bold'),
            bg='#95A5A6',
            fg='black',
            padx=20,
            pady=10,
            relief=tk.RAISED,
            borderwidth=3
        )
        self.prev_btn.pack(side=tk.LEFT, padx=10)
        
        # Next button
        self.next_btn = tk.Button(
            button_frame,
            text="Next ▶",
            command=self.next_student,
            font=('Arial', 14, 'bold'),
            bg='#3498DB',
            fg='black',
            padx=20,
            pady=10,
            relief=tk.RAISED,
            borderwidth=3
        )
        self.next_btn.pack(side=tk.LEFT, padx=10)
        
        # Shuffle button
        self.shuffle_btn = tk.Button(
            button_frame,
            text="🔀 Shuffle",
            command=self.shuffle_students,
            font=('Arial', 14, 'bold'),
            bg='#9B59B6',
            fg='black',
            padx=20,
            pady=10,
            relief=tk.RAISED,
            borderwidth=3
        )
        self.shuffle_btn.pack(side=tk.LEFT, padx=10)
        
        # Change Folder button
        self.folder_btn = tk.Button(
            button_frame,
            text="📁 Change Folder",
            command=self.choose_folder,
            font=('Arial', 14, 'bold'),
            bg='#F39C12',
            fg='black',
            padx=20,
            pady=10,
            relief=tk.RAISED,
            borderwidth=3
        )
        self.folder_btn.pack(side=tk.LEFT, padx=10)
        
        # Auto-advance controls
        auto_frame = tk.Frame(self.root, bg='#2C3E50')
        auto_frame.pack(pady=10)
        
        self.auto_btn = tk.Button(
            auto_frame,
            text="▶ Auto-Advance",
            command=self.toggle_auto_advance,
            font=('Arial', 12, 'bold'),
            bg='#27AE60',
            fg='black',
            padx=15,
            pady=8,
            relief=tk.RAISED,
            borderwidth=2
        )
        self.auto_btn.pack(side=tk.LEFT, padx=10)
        
        # Speed control
        tk.Label(
            auto_frame,
            text="Speed:",
            font=('Arial', 12),
            bg='#2C3E50',
            fg='white'
        ).pack(side=tk.LEFT, padx=5)
        
        self.speed_var = tk.StringVar(value="3")
        speed_options = ["1", "2", "3", "4", "5", "7", "10"]
        self.speed_menu = tk.OptionMenu(
            auto_frame,
            self.speed_var,
            *speed_options,
            command=self.update_speed
        )
        self.speed_menu.config(font=('Arial', 12), bg='#34495E', fg='white')
        self.speed_menu.pack(side=tk.LEFT, padx=5)
        
        tk.Label(
            auto_frame,
            text="seconds",
            font=('Arial', 12),
            bg='#2C3E50',
            fg='white'
        ).pack(side=tk.LEFT)
        
        # Keyboard shortcuts info
        info_label = tk.Label(
            self.root,
            text="⌨️ Shortcuts: Space=Next | Left Arrow=Previous | S=Shuffle | A=Auto",
            font=('Arial', 11),
            bg='#2C3E50',
            fg='#95A5A6'
        )
        info_label.pack(pady=10)
        
        # Bind keyboard shortcuts
        self.root.bind('<space>', lambda e: self.next_student())
        self.root.bind('<Left>', lambda e: self.previous_student())
        self.root.bind('<Right>', lambda e: self.next_student())
        self.root.bind('s', lambda e: self.shuffle_students())
        self.root.bind('a', lambda e: self.toggle_auto_advance())
    
    def choose_folder(self):
        folder = filedialog.askdirectory(title="Select folder with student photos")
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
                    parts = name_part.split('_')
                    # Could be LastName_FirstName or FirstName_LastName
                    # We'll use the last part as the display name
                    name = parts[-1] if len(parts) > 1 else parts[0]
                else:
                    name = name_part
                
                self.students.append({
                    'name': name,
                    'filepath': filepath
                })
        
        if self.students:
            # Save this folder as the last used
            save_folder(folder)
            self.current_index = 0
            self.show_current_student()
            messagebox.showinfo("Success", f"Loaded {len(self.students)} student photos!")
        else:
            messagebox.showwarning("No Photos", "No photos found in the selected folder.")
    
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
            img = Image.open(student['filepath'])
            # Resize to fit (max 500x500)
            img.thumbnail((500, 500), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.photo_label.config(image=photo)
            self.photo_label.image = photo  # Keep a reference
        except Exception as e:
            print(f"Error loading image: {e}")
            self.photo_label.config(text="Error loading image")
        
        # Display name
        self.name_label.config(text=student['name'])
    
    def next_student(self):
        if not self.students:
            return
        
        self.current_index = (self.current_index + 1) % len(self.students)
        self.show_current_student()
    
    def previous_student(self):
        if not self.students:
            return
        
        self.current_index = (self.current_index - 1) % len(self.students)
        self.show_current_student()
    
    def shuffle_students(self):
        if not self.students:
            return
        
        random.shuffle(self.students)
        self.current_index = 0
        self.show_current_student()
        messagebox.showinfo("Shuffled", "Students have been shuffled!")
    
    def toggle_auto_advance(self):
        self.auto_advance = not self.auto_advance
        
        if self.auto_advance:
            self.auto_btn.config(text="⏸ Stop Auto", bg='#E74C3C')
            self.auto_advance_step()
        else:
            self.auto_btn.config(text="▶ Auto-Advance", bg='#27AE60')
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
