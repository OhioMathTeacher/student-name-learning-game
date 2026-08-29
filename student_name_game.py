#!/usr/bin/env python3
"""
Student Name Learning Game - Simple Version
A proper game that ends when you miss one or complete all students without hints.
"""

import tkinter as tk
import traceback

import theme
from tkinter import ttk, filedialog, messagebox
import random
from PIL import Image, ImageTk
import os
import sys
import json

def fit_window(root, min_w=800, min_h=700):
    """Size the window to its content, then centre it.

    The old hardcoded geometry assumed ~96 DPI. On a HiDPI display Tk scales
    fonts up but not a fixed "800x900", so headers and buttons were clipped
    outside the window and could not be clicked. Asking Tk how much room the
    widgets actually need gets this right at any scaling factor.
    """
    root.update_idletasks()
    w = max(root.winfo_reqwidth(), min_w)
    h = max(root.winfo_reqheight(), min_h)
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    w, h = min(w, sw - 80), min(h, sh - 120)
    root.geometry(f"{w}x{h}+{max(0,(sw-w)//2)}+{max(0,(sh-h)//2)}")
    root.minsize(min(min_w, w), min(min_h, h))

def get_config_path():
    """Get path for storing app configuration"""
    home_dir = os.path.expanduser("~")
    config_dir = os.path.join(home_dir, ".student_name_game")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    return os.path.join(config_dir, "config.json")

class StudentNameGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Student Name Learning Game")
        self.root.geometry("800x700")
        
        # Shared palette (see theme.py) so quiz and study mode match
        self.bg_color = theme.BG
        self.text_color = theme.TEXT
        self.accent_color = theme.ACCENT
        self.success_color = "#3FB068"  # Green
        self.error_color = theme.STOP
        self.hint_color = "#E0B341"  # Amber
        
        self.root.configure(bg=self.bg_color)
        
        # Initialize image data
        self.students = []
        self.image_folder = None
        self.remaining_students = []  # Students not yet completed
        self.completed_students = []  # Students completed without hints
        
        # Load or select image folder
        if not self.select_folder():
            self.root.destroy()
            return
            
        # Load student images
        self.load_images()
        
        if not self.students:
            messagebox.showerror("No Images", "No valid student images found in the selected folder!")
            self.root.destroy()
            return
        
        # Game state
        self.current_student = None
        self.current_streak = 0
        self.longest_streak = 0
        self.used_hint = False
        self.game_over = False
        
        self.create_widgets()
        self.start_new_game()
    
    def select_folder(self):
        """Simple folder selection"""
        # Try to load last used folder first
        config_path = get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    saved_folder = config.get('last_folder')
                    
                if saved_folder and os.path.exists(saved_folder):
                    # Ask if user wants to use the same folder
                    use_saved = messagebox.askyesno(
                        "Use Previous Folder?", 
                        f"Use the same photo folder as last time?\n\n{saved_folder}"
                    )
                    if use_saved:
                        self.image_folder = saved_folder
                        return True
            except:
                pass
        
        # Ask user to select folder
        messagebox.showinfo(
            "Select Photo Folder", 
            "Please select the folder containing your student photos.\n\n" +
            "Photos should be named: LastName_FirstName.jpg"
        )
        
        folder = theme.ask_folder(
            self.root, locals().get('saved_folder'),
            "Select folder containing student photos"
        )
        
        if folder:
            self.image_folder = folder
            # Save for next time
            try:
                config = {'last_folder': folder}
                with open(config_path, 'w') as f:
                    json.dump(config, f)
            except:
                pass
            return True
        
        return False
    
    def load_images(self):
        """Load all student images from the selected folder"""
        self.students = []
        
        if not self.image_folder or not os.path.exists(self.image_folder):
            return
            
        for filename in os.listdir(self.image_folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                # Extract name from filename (remove extension)
                name_part = os.path.splitext(filename)[0]
                
                # Split by underscore and format as "First Last"
                if '_' in name_part:
                    parts = name_part.split('_', 1)
                    if len(parts) == 2:
                        last_name, first_name = parts
                        display_name = f"{first_name} {last_name}"
                    else:
                        display_name = name_part.replace('_', ' ')
                else:
                    display_name = name_part.replace('_', ' ')
                
                image_path = os.path.join(self.image_folder, filename)
                self.students.append({
                    'name': display_name,
                    'image_path': image_path
                })
        
        print(f"Loaded {len(self.students)} student images from {self.image_folder}")
    
    def start_new_game(self):
        """Start a new game with the current folder"""
        if not self.students:
            return
            
        # Reset game state
        self.remaining_students = self.students.copy()
        self.completed_students = []
        self.current_streak = 0
        self.longest_streak = 0
        self.game_over = False
        
        # Shuffle the students for random order
        random.shuffle(self.remaining_students)
        
        # Re-enable the buttons; the theme owns their colours
        for name, primary in (('submit_btn', True), ('hint_btn', False), ('skip_btn', False)):
            btn = getattr(self, name, None)
            if btn is not None:
                btn.config(
                    state="normal",
                    bg=theme.ACCENT if primary else theme.SURFACE,
                    fg=theme.TEXT,
                    activebackground=theme.ACCENT_ACTIVE if primary else theme.SURFACE_ACTIVE,
                    activeforeground=theme.TEXT
                )
        
        # Remove restart button if it exists
        if hasattr(self, 'restart_btn'):
            self.restart_btn.destroy()
            
        self.next_student()
        self.update_display()
    
    def next_student(self):
        """Move to the next student or end game"""
        if not self.remaining_students or self.game_over:
            self.end_game()
            return
            
        self.current_student = self.remaining_students[0]
        self.used_hint = False
        
        self.load_and_display_image(self.current_student['image_path'])
        
        # Clear input and feedback
        self.name_entry.delete(0, tk.END)
        self.feedback_label.config(text="", fg=self.text_color)
        self.name_entry.focus_force()  # Use focus_force for better visibility
        
        # Reset hint button and level
        self.hint_btn.config(state="normal")
        self.hint_level = 0
    
    def end_game(self):
        """End the current game and show results"""
        self.game_over = True
        
        total_students = len(self.students)
        completed_perfect = len(self.completed_students)
        
        if completed_perfect == total_students:
            # Perfect game!
            result_text = f"Perfect game\n\nYou completed all {total_students} students without using hints!\nLongest streak: {self.longest_streak}"
            color = self.success_color
        elif len(self.remaining_students) == 0:
            # Completed all but used some hints
            result_text = f"Great job\n\nCompleted all {total_students} students!\nPerfect (no hints): {completed_perfect}\nLongest streak: {self.longest_streak}"
            color = self.accent_color
        else:
            # Game ended due to wrong answer
            wrong_name = self.current_student['name'] if self.current_student else 'Unknown'
            result_text = f"Game over\n\nYou missed: {wrong_name}\nCompleted: {total_students - len(self.remaining_students)}/{total_students}\nPerfect (no hints): {completed_perfect}\nLongest streak: {self.longest_streak}"
            color = self.error_color
        
        self.feedback_label.config(text=result_text, fg=color)
        self.root.after_idle(lambda: fit_window(self.root, 800, 700))
        
        # Show restart button
        if getattr(self, 'restart_btn', None) is not None:
            self.restart_btn.destroy()
        self.restart_btn = theme.button(
            self.button_frame, "Start new game", self.start_new_game, primary=True
        )
        self.restart_btn.pack(side=tk.LEFT, padx=6)
        
        # Disable other buttons with proper styling
        self.submit_btn.config(
            state="disabled",
            bg=theme.SURFACE,
            fg="#666666",  # Dark gray text when disabled
            disabledforeground="#666666"
        )
        self.hint_btn.config(
            state="disabled", 
            bg=theme.SURFACE,
            fg="#666666",  # Dark gray text when disabled
            disabledforeground="#666666"
        )
        self.skip_btn.config(
            state="disabled",
            bg=theme.SURFACE,
            fg="#666666",  # Dark gray text when disabled
            disabledforeground="#666666"
        )
    
    def create_widgets(self):
        """Create the main GUI elements"""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Change Photo Folder...", command=self.change_photo_folder)
        file_menu.add_separator()
        file_menu.add_command(label="📚 Switch to Study Mode", command=self.switch_to_study)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Game info display
        self.info_frame = tk.Frame(self.root, bg=self.bg_color)
        self.info_frame.pack(pady=10)
        
        self.streak_label = tk.Label(
            self.info_frame, 
            text="Current Streak: 0 | Longest: 0", 
            font=theme.font(theme.SIZE_LABEL, "bold"), 
            bg=self.bg_color, 
            fg=self.text_color
        )
        self.streak_label.pack()

        self.course_label = theme.label(
            self.info_frame, theme.course_name(self.image_folder),
            size=theme.SIZE_BODY, fg=theme.ACCENT
        )
        self.course_label.pack(pady=(2, 0))
        
        # Student photo display
        self.photo_frame = tk.Frame(self.root, bg=self.bg_color)
        self.photo_frame.pack(pady=20)
        
        self.photo_label = tk.Label(
            self.photo_frame, 
            bg=self.bg_color,
            text="Loading...",
            fg=self.text_color,
            font=theme.font(theme.SIZE_BODY)
        )
        self.photo_label.pack()
        
        # Name input
        self.input_frame = tk.Frame(self.root, bg=self.bg_color)
        self.input_frame.pack(pady=20)
        
        tk.Label(
            self.input_frame, 
            text="Student's Name:", 
            font=theme.font(theme.SIZE_LABEL), 
            bg=self.bg_color, 
            fg=self.text_color
        ).pack()
        
        self.name_entry = tk.Entry(
            self.input_frame, 
            font=theme.font(theme.SIZE_INPUT),
            width=20,
            bg=theme.SURFACE,
            fg=theme.TEXT,
            insertbackground=theme.TEXT,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=2,
            highlightcolor=theme.ACCENT,
            highlightbackground=theme.BORDER
        )
        self.name_entry.pack(pady=10)
        self.name_entry.bind("<Return>", lambda e: self.check_answer())
        
        # Force initial focus and visibility
        self.root.after(100, lambda: self.name_entry.focus_force())
        
        # Buttons
        self.button_frame = tk.Frame(self.root, bg=self.bg_color)
        self.button_frame.pack(pady=20)
        
        # Button style properties for consistency
        button_style = {
            "font": theme.font(theme.SIZE_BODY, "bold"),
            "bg": self.accent_color,
            "fg": "white",
            "activebackground": "#2980B9",  # Darker blue when pressed
            "activeforeground": "white",
            "disabledforeground": theme.MUTED,
            "relief": "flat",
            "bd": 0,
            "padx": 20,
            "pady": 10,
            "cursor": "hand2",
            "highlightthickness": 0,
            "highlightbackground": self.bg_color,
            "highlightcolor": "white"
        }
        
        self.submit_btn = theme.button(
            self.button_frame, "Submit", self.check_answer, primary=True,
            disabledforeground=theme.MUTED
        )
        self.submit_btn.pack(side=tk.LEFT, padx=6)

        self.hint_btn = theme.button(
            self.button_frame, "Hint", self.show_hint, primary=False,
            disabledforeground=theme.MUTED
        )
        self.hint_btn.pack(side=tk.LEFT, padx=6)

        self.skip_btn = theme.button(
            self.button_frame, "Skip", self.skip_student, primary=False,
            disabledforeground=theme.MUTED
        )
        self.skip_btn.pack(side=tk.LEFT, padx=6)

        # Feedback label
        self.feedback_label = tk.Label(
            self.root,
            text="",
            font=theme.font(theme.SIZE_LABEL, "bold"),
            bg=self.bg_color,
            fg=self.text_color,
            wraplength=600
        )
        self.feedback_label.pack(pady=20)        # Stats display
        self.stats_frame = tk.Frame(self.root, bg=self.bg_color)
        self.stats_frame.pack(pady=10)
        
        self.stats_label = tk.Label(
            self.stats_frame,
            text=f"Total Students: {len(self.students)}",
            font=theme.font(theme.SIZE_SMALL),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.stats_label.pack()
    
    def change_photo_folder(self):
        """Allow user to change the photo folder"""
        folder = theme.ask_folder(
            self.root, self.image_folder,
            "Select new folder containing student photos"
        )
        
        if folder and folder != self.image_folder:
            self.image_folder = folder
            if hasattr(self, 'course_label'):
                self.course_label.config(text=theme.course_name(folder))
            
            # Save new folder
            try:
                config = {'last_folder': folder}
                config_path = get_config_path()
                with open(config_path, 'w') as f:
                    json.dump(config, f)
            except:
                pass
            
            # Reload images
            self.load_images()
            
            if not self.students:
                messagebox.showerror("No Images", "No valid student images found in the selected folder!")
                return
            
            # Update stats and start new game
            self.stats_label.config(text=f"Total Students: {len(self.students)}")
            self.start_new_game()
            messagebox.showinfo("Success", f"Loaded {len(self.students)} student photos from new folder!")
    
    def load_and_display_image(self, image_path):
        """Load and display a student image"""
        try:
            # Fixed square so the layout does not shift between students
            photo = theme.photo(image_path)
            
            # Update the label
            self.photo_label.configure(image=photo, text="")
            self.photo_label.image = photo  # Keep a reference
            
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            self.photo_label.configure(
                image="",
                text=f"Could not load image\n{os.path.basename(image_path)}",
                fg=self.error_color
            )
            self.photo_label.image = None
    
    def check_answer(self):
        """Check if the entered name is correct"""
        if not self.current_student or self.game_over:
            return
            
        user_answer = self.name_entry.get().strip().lower()
        correct_name = self.current_student['name'].lower()
        
        # Check for exact match or close match
        if user_answer == correct_name or self.is_close_match(user_answer, correct_name):
            # Correct answer!
            self.current_streak += 1
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak
            
            # Remove from remaining students
            self.remaining_students.remove(self.current_student)
            
            # Add to completed if no hint was used
            if not self.used_hint:
                self.completed_students.append(self.current_student)
            
            self.feedback_label.config(
                text=f"✓ Correct! That's {self.current_student['name']}",
                fg=self.success_color
            )
            
            self.update_display()
            
            # Auto-advance after 1.5 seconds
            self.root.after(1500, self.next_student)
        else:
            # Wrong answer - game over!
            self.current_streak = 0
            self.feedback_label.config(
                text=f"✗ Wrong! The correct answer was: {self.current_student['name']}",
                fg=self.error_color
            )
            self.root.after(2000, self.end_game)
    
    def is_close_match(self, user_input, correct_name):
        """Check if user input is close enough to the correct name"""
        # Split names into parts
        user_parts = user_input.split()
        correct_parts = correct_name.split()
        
        # Check if first name matches (most common case)
        if len(user_parts) >= 1 and len(correct_parts) >= 1:
            if user_parts[0] == correct_parts[0]:
                return True
        
        # Check if last name matches
        if len(user_parts) >= 1 and len(correct_parts) >= 2:
            if user_parts[-1] == correct_parts[-1]:
                return True
                
        return False
    
    def show_hint(self):
        """Show a progressive hint"""
        if not self.current_student or self.game_over:
            return
            
        self.used_hint = True  # Mark that hint was used
        
        name = self.current_student['name']
        
        if not hasattr(self, 'hint_level'):
            self.hint_level = 0
        
        if self.hint_level == 0:
            # First hint: number of letters
            hint_text = f"💡 This student's name has {len(name.replace(' ', ''))} letters"
            self.hint_level += 1
        elif self.hint_level == 1:
            # Second hint: first letter of first name
            first_name = name.split()[0]
            hint_text = f"💡 Their first name starts with '{first_name[0].upper()}'"
            self.hint_level += 1
        else:
            # Final hint: show the answer
            hint_text = f"💡 The answer is: {name}"
            self.hint_btn.config(
                state="disabled",
                bg=theme.SURFACE,
                fg="#666666",  # Dark gray text when disabled
                disabledforeground="#666666"
            )
        
        self.feedback_label.config(text=hint_text, fg=self.hint_color)
    
    def skip_student(self):
        """Skip current student - ends the game"""
        if not self.current_student or self.game_over:
            return
            
        self.feedback_label.config(
            text=f"⏭️ Skipped: {self.current_student['name']}",
            fg=self.error_color
        )
        self.current_streak = 0
        self.root.after(2000, self.end_game)
    
    def update_display(self):
        """Update the game display"""
        remaining = len(self.remaining_students)
        completed = len(self.students) - remaining
        perfect = len(self.completed_students)
        
        self.streak_label.config(
            text=f"Current Streak: {self.current_streak} | Longest: {self.longest_streak}"
        )
        
        self.stats_label.config(
            text=f"Progress: {completed}/{len(self.students)} | Perfect (no hints): {perfect}"
        )
    
    def switch_to_study(self):
        """Launch the study mode app"""
        import subprocess
        
        # Determine the path to the flashcards app
        # This works for both development and PyInstaller bundled apps
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            base_path = sys._MEIPASS
            flashcards_app = os.path.join(base_path, 'student_name_flashcards.py')
        else:
            # Running in normal Python
            flashcards_app = os.path.join(os.path.dirname(__file__), 'student_name_flashcards.py')
        
        python_exe = sys.executable
        
        # Launch the flashcards app
        subprocess.Popen([python_exe, flashcards_app])
        
        # Close this app
        self.root.quit()
    
    def run(self):
        """Start the game"""
        fit_window(self.root, 800, 700)
        self.root.mainloop()

def main():
    """Main function to start the application"""
    game = StudentNameGame()
    if hasattr(game, 'root'):
        try:
            if game.root.winfo_exists():
                game.run()
        except tk.TclError as exc:
            # A destroyed window during start-up is expected; anything else
            # was being swallowed here and looked like the app just vanishing.
            if "application has been destroyed" not in str(exc):
                traceback.print_exc()

if __name__ == "__main__":
    main()