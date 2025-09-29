#!/usr/bin/env python3
"""
Student Name Learning Game - Dynamic Version
A GUI application to help teachers learn student names using photos from any folder.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import random
from PIL import Image, ImageTk
import os
import sys
import json

def     def start_new_game(self):
        \"\"\"Start a new game with the current folder\"\"\"\n        if not self.students:\n            return\n            \n        # Reset game state\n        self.remaining_students = self.students.copy()\n        self.completed_students = []\n        self.current_streak = 0\n        self.longest_streak = 0\n        self.game_over = False\n        \n        # Shuffle the students for random order\n        random.shuffle(self.remaining_students)\n        \n        self.next_student()\n        self.update_display()\n    \n    def next_student(self):\n        \"\"\"Move to the next student or end game\"\"\"\n        if not self.remaining_students or self.game_over:\n            self.end_game()\n            return\n            \n        self.current_student = self.remaining_students[0]\n        self.used_hint = False\n        \n        self.load_and_display_image(self.current_student['image_path'])\n        \n        # Clear input and feedback\n        self.name_entry.delete(0, tk.END)\n        self.feedback_label.config(text=\"\", fg=self.text_color)\n        self.name_entry.focus_set()\n        \n        # Reset hint button\n        self.hint_btn.config(state=\"normal\")\n    \n    def end_game(self):\n        \"\"\"End the current game and show results\"\"\"\n        self.game_over = True\n        \n        total_students = len(self.students)\n        completed_perfect = len(self.completed_students)\n        \n        if completed_perfect == total_students:\n            # Perfect game!\n            result_text = f\"🎉 PERFECT GAME! 🎉\\n\\nYou completed all {total_students} students without using hints!\\nLongest streak: {self.longest_streak}\"\n            color = self.success_color\n        elif self.current_streak > 0:\n            # Game ended due to completing all students with some hints used\n            result_text = f\"🎯 Great job!\\n\\nCompleted: {completed_perfect}/{total_students} students without hints\\nLongest streak: {self.longest_streak}\"\n            color = self.accent_color\n        else:\n            # Game ended due to wrong answer\n            result_text = f\"💥 Game Over!\\n\\nYou missed: {self.current_student['name'] if self.current_student else 'Unknown'}\\nCompleted: {completed_perfect}/{total_students} students without hints\\nLongest streak: {self.longest_streak}\"\n            color = self.error_color\n        \n        self.feedback_label.config(text=result_text, fg=color)\n        \n        # Show restart button\n        self.restart_btn = tk.Button(\n            self.button_frame,\n            text=\"Start New Game\",\n            command=self.start_new_game,\n            font=(\"Arial\", 12, \"bold\"),\n            bg=self.success_color,\n            fg=\"white\",\n            activebackground=\"#1E8449\",\n            activeforeground=\"white\",\n            relief=\"flat\",\n            bd=0,\n            padx=20,\n            pady=10,\n            cursor=\"hand2\",\n            highlightthickness=0\n        )\n        self.restart_btn.pack(side=tk.LEFT, padx=10)\n        \n        # Disable other buttons\n        self.submit_btn.config(state=\"disabled\")\n        self.hint_btn.config(state=\"disabled\")\n        self.skip_btn.config(state=\"disabled\")esource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_config_path():
    """Get path for storing app configuration"""
    home_dir = os.path.expanduser("~")
    config_dir = os.path.join(home_dir, ".student_name_game")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    return os.path.join(config_dir, "config.json")

def get_folder_name(folder_path):
    """Extract a nice course name from folder path"""
    if not folder_path:
        return "Unknown"
    
    folder_name = os.path.basename(folder_path)
    
    # Clean up common folder patterns
    if not folder_name or folder_name == "." or folder_name == "..":
        # Use parent folder name if current is empty
        folder_name = os.path.basename(os.path.dirname(folder_path))
    
    # Limit length for UI
    if len(folder_name) > 25:
        folder_name = folder_name[:22] + "..."
    
    return folder_name

class StudentNameGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Student Name Learning Game")
        self.root.geometry("800x700")
        
        # Dark theme colors
        self.bg_color = "#2C3E50"  # Dark blue-gray
        self.text_color = "#ECF0F1"  # Light gray
        self.accent_color = "#3498DB"  # Blue
        self.success_color = "#27AE60"  # Green
        self.error_color = "#E74C3C"  # Red
        self.hint_color = "#F1C40F"  # Yellow
        
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
    
    def load_courses_config(self):
        """Load saved courses and current selection from config"""
        config_path = get_config_path()
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
                # Load courses (limit to 8)
                saved_courses = config.get('courses', {})
                self.courses = dict(list(saved_courses.items())[:8])  # Limit to 8
                
                # Set current course
                current_folder = config.get('current_folder')
                if current_folder and current_folder in self.courses:
                    self.image_folder = current_folder
                    self.current_course.set(current_folder)
                    
            except:
                pass
    
    def save_courses_config(self):
        """Save courses and current selection to config"""
        try:
            config = {
                'courses': self.courses,
                'current_folder': self.image_folder
            }
            config_path = get_config_path()
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except:
            pass  # Not critical if we can't save config
    
    def add_course(self, folder_path):
        """Add a new course folder"""
        if folder_path and os.path.exists(folder_path):
            course_name = get_folder_name(folder_path)
            self.courses[folder_path] = course_name
            
            # Limit to 8 courses - remove oldest if needed
            if len(self.courses) > 8:
                # Remove the first (oldest) entry
                oldest_key = next(iter(self.courses))
                del self.courses[oldest_key]
            
            self.save_courses_config()
        """Setup image folder - load from config or ask user to select"""
    def setup_image_folder(self):
        """Setup image folder - use saved courses or ask user to select"""
        # If we have saved courses, let user choose
        if self.courses:
            if self.image_folder and os.path.exists(self.image_folder):
                return True  # Use currently selected course
            
            # Ask user to select from saved courses or add new
            return self.show_course_selection_dialog()
        
        # No saved courses - ask for new folder
        return self.select_new_folder()
    
    def show_course_selection_dialog(self):
        """Show dialog to select from existing courses or add new"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Course")
        dialog.geometry("500x400")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        tk.Label(
            dialog, 
            text="Select a Course or Add New:", 
            font=("Arial", 14, "bold"), 
            bg=self.bg_color, 
            fg=self.text_color
        ).pack(pady=20)
        
        # Radio buttons for existing courses
        self.selected_folder = tk.StringVar()
        
        frame = tk.Frame(dialog, bg=self.bg_color)
        frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Add radio buttons for each course
        for folder_path, course_name in self.courses.items():
            if os.path.exists(folder_path):
                rb = tk.Radiobutton(
                    frame,
                    text=f"{course_name}\n({folder_path})",
                    variable=self.selected_folder,
                    value=folder_path,
                    bg=self.bg_color,
                    fg=self.text_color,
                    selectcolor=self.accent_color,
                    activebackground=self.bg_color,
                    activeforeground=self.text_color,
                    font=("Arial", 11),
                    wraplength=450,
                    justify="left"
                )
                rb.pack(anchor="w", pady=5, padx=10)
        
        # Buttons
        button_frame = tk.Frame(dialog, bg=self.bg_color)
        button_frame.pack(pady=20)
        
        def use_selected():
            selected = self.selected_folder.get()
            if selected and os.path.exists(selected):
                self.image_folder = selected
                self.current_course.set(selected)
                self.save_courses_config()
                dialog.destroy()
            else:
                messagebox.showerror("No Selection", "Please select a course or add a new folder.")
        
        def add_new():
            dialog.destroy()
            if self.select_new_folder():
                return
            else:
                # If they cancelled, show dialog again
                self.show_course_selection_dialog()
        
        def cancel():
            dialog.destroy()
            self.root.quit()  # Exit app if no selection
        
        tk.Button(
            button_frame, 
            text="Use Selected", 
            command=use_selected,
            bg=self.success_color, 
            fg="white", 
            font=("Arial", 12), 
            padx=20
        ).pack(side="left", padx=10)
        
        tk.Button(
            button_frame, 
            text="Add New Folder...", 
            command=add_new,
            bg=self.accent_color, 
            fg="white", 
            font=("Arial", 12), 
            padx=20
        ).pack(side="left", padx=10)
        
        tk.Button(
            button_frame, 
            text="Cancel", 
            command=cancel,
            bg=self.error_color, 
            fg="white", 
            font=("Arial", 12), 
            padx=20
        ).pack(side="left", padx=10)
        
        # Wait for dialog to close
        self.root.wait_window(dialog)
        
        return self.image_folder is not None
    
    def select_new_folder(self):
        """Ask user to select a new folder"""
        messagebox.showinfo(
            "Select Photo Folder", 
            "Please select the folder containing your student photos.\n\n" +
            "Photos should be named: LastName_FirstName.jpg"
        )
        
        folder = filedialog.askdirectory(
            title="Select folder containing student photos"
        )
        
        if folder:
            self.image_folder = folder
            self.current_course.set(folder)
            self.add_course(folder)
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
    
    def create_widgets(self):
        """Create the main GUI elements"""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Switch Course...", command=self.switch_course)
        file_menu.add_command(label="Add New Course...", command=self.add_new_course)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Course selector (radio buttons) - only show if multiple courses
        if len(self.courses) > 1:
            self.course_frame = tk.Frame(self.root, bg=self.bg_color)
            self.course_frame.pack(pady=5)
            
            tk.Label(
                self.course_frame,
                text="Current Course:",
                font=("Arial", 11),
                bg=self.bg_color,
                fg=self.text_color
            ).pack()
            
            # Create frame for radio buttons (horizontal layout for up to 4, vertical for more)
            courses_count = len(self.courses)
            if courses_count <= 4:
                radio_frame = tk.Frame(self.course_frame, bg=self.bg_color)
                radio_frame.pack()
                side = "left"
            else:
                radio_frame = tk.Frame(self.course_frame, bg=self.bg_color)
                radio_frame.pack()
                side = "top"
            
            for folder_path, course_name in list(self.courses.items())[:8]:  # Limit to 8
                if os.path.exists(folder_path):
                    rb = tk.Radiobutton(
                        radio_frame,
                        text=course_name,
                        variable=self.current_course,
                        value=folder_path,
                        command=lambda path=folder_path: self.switch_to_course(path),
                        bg=self.bg_color,
                        fg=self.text_color,
                        selectcolor=self.accent_color,
                        activebackground=self.bg_color,
                        activeforeground=self.text_color,
                        font=("Arial", 10)
                    )
                    rb.pack(side=side, padx=5, pady=2)
        
        # Score display
        self.score_frame = tk.Frame(self.root, bg=self.bg_color)
        self.score_frame.pack(pady=10)
        
        self.score_label = tk.Label(
            self.score_frame, 
            text="Score: 0/0", 
            font=("Arial", 16, "bold"), 
            bg=self.bg_color, 
            fg=self.text_color
        )
        self.score_label.pack()
        
        # Student photo display
        self.photo_frame = tk.Frame(self.root, bg=self.bg_color)
        self.photo_frame.pack(pady=20)
        
        self.photo_label = tk.Label(
            self.photo_frame, 
            bg=self.bg_color,
            text="Loading...",
            fg=self.text_color,
            font=("Arial", 12)
        )
        self.photo_label.pack()
        
        # Name input
        self.input_frame = tk.Frame(self.root, bg=self.bg_color)
        self.input_frame.pack(pady=20)
        
        tk.Label(
            self.input_frame, 
            text="Student's Name:", 
            font=("Arial", 14), 
            bg=self.bg_color, 
            fg=self.text_color
        ).pack()
        
        self.name_entry = tk.Entry(
            self.input_frame, 
            font=("Arial", 16),
            width=20,
            bg="#34495E",  # Slightly lighter than background
            fg=self.text_color,
            insertbackground=self.text_color,  # Cursor color
            relief="flat",
            bd=2
        )
        self.name_entry.pack(pady=10)
        self.name_entry.bind("<Return>", lambda e: self.check_answer())
        self.name_entry.bind("<FocusIn>", self.on_entry_focus_in)
        self.name_entry.bind("<FocusOut>", self.on_entry_focus_out)
        
        # Buttons
        self.button_frame = tk.Frame(self.root, bg=self.bg_color)
        self.button_frame.pack(pady=20)
        
        # Button style properties for consistency
        button_style = {
            "font": ("Arial", 12, "bold"),
            "bg": self.accent_color,
            "fg": "white",
            "activebackground": "#2980B9",  # Darker blue when pressed
            "activeforeground": "white",
            "relief": "flat",
            "bd": 0,
            "padx": 20,
            "pady": 10,
            "cursor": "hand2",
            "highlightthickness": 0
        }
        
        self.submit_btn = tk.Button(
            self.button_frame,
            text="Submit Answer",
            command=self.check_answer,
            **button_style
        )
        self.submit_btn.pack(side=tk.LEFT, padx=10)
        
        self.hint_btn = tk.Button(
            self.button_frame,
            text="Get Hint",
            command=self.show_hint,
            **button_style
        )
        self.hint_btn.pack(side=tk.LEFT, padx=10)
        
        self.skip_btn = tk.Button(
            self.button_frame,
            text="Skip",
            command=self.new_student,
            **button_style
        )
        self.skip_btn.pack(side=tk.LEFT, padx=10)
        
        # Feedback label
        self.feedback_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 14, "bold"),
            bg=self.bg_color,
            fg=self.text_color,
            wraplength=600
        )
        self.feedback_label.pack(pady=20)
        
        # Stats display
        self.stats_frame = tk.Frame(self.root, bg=self.bg_color)
        self.stats_frame.pack(pady=10)
        
        self.stats_label = tk.Label(
            self.stats_frame,
            text=f"Total Students: {len(self.students)} | Course: {self.courses.get(self.image_folder, 'Current Folder') if self.image_folder else 'No Course'}",
            font=("Arial", 10),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.stats_label.pack()
    
    def on_entry_focus_in(self, event):
        """Handle entry field focus in"""
        self.name_entry.configure(bg="#3E5871")  # Slightly brighter when focused
    
    def on_entry_focus_out(self, event):
        """Handle entry field focus out"""
        self.name_entry.configure(bg="#34495E")  # Back to normal
    
    def switch_to_course(self, folder_path):
        """Switch to a different course"""
        if folder_path and os.path.exists(folder_path) and folder_path != self.image_folder:
            self.image_folder = folder_path
            self.current_course.set(folder_path)
            self.save_courses_config()
            
            # Reload images
            self.load_images()
            
            if not self.students:
                messagebox.showerror("No Images", "No valid student images found in the selected course folder!")
                return
            
            # Reset game state and update stats
            self.score = 0
            self.attempts = 0
            self.stats_label.config(text=f"Total Students: {len(self.students)} | Course: {self.courses.get(folder_path, 'Unknown')}")
            self.new_student()
    
    def switch_course(self):
        """Show course selection dialog"""
        if self.show_course_selection_dialog():
            self.load_images()
            if self.students:
                self.score = 0
                self.attempts = 0
                self.stats_label.config(text=f"Total Students: {len(self.students)} | Course: {self.courses.get(self.image_folder, 'Unknown')}")
                self.new_student()
                # Recreate the course radio buttons
                self.root.destroy()
                main()
    
    def add_new_course(self):
        """Add a new course folder"""
        if self.select_new_folder():
            self.load_images()
            if self.students:
                self.score = 0
                self.attempts = 0
                self.stats_label.config(text=f"Total Students: {len(self.students)} | Course: {self.courses.get(self.image_folder, 'Unknown')}")
                self.new_student()
                # Recreate the course radio buttons
                self.root.destroy()
                main()
    
    def change_photo_folder(self):
        """Allow user to change the photo folder"""
        folder = filedialog.askdirectory(
            title="Select new folder containing student photos",
            initialdir=self.image_folder
        )
        
        if folder and folder != self.image_folder:
            self.image_folder = folder
            
            # Save new folder to config
            try:
                config = {'image_folder': folder}
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
            
            # Reset game state and update stats
            self.score = 0
            self.attempts = 0
            self.stats_label.config(text=f"Total Students: {len(self.students)}")
            self.new_student()
            messagebox.showinfo("Success", f"Loaded {len(self.students)} student photos from new folder!")
    
    def load_and_display_image(self, image_path):
        """Load and display a student image"""
        try:
            # Load and resize image
            image = Image.open(image_path)
            
            # Calculate size to fit in 400x400 while maintaining aspect ratio
            max_size = 400
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage for tkinter
            photo = ImageTk.PhotoImage(image)
            
            # Update the label
            self.photo_label.configure(image=photo, text="")
            self.photo_label.image = photo  # Keep a reference
            
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            self.photo_label.configure(
                image="",
                text=f"Could not load image\\n{os.path.basename(image_path)}",
                fg=self.error_color
            )
            self.photo_label.image = None
    
    def new_student(self):
        """Select a new random student"""
        if not self.students:
            return
            
        self.current_student = random.choice(self.students)
        self.load_and_display_image(self.current_student['image_path'])
        
        # Clear input and feedback
        self.name_entry.delete(0, tk.END)
        self.feedback_label.config(text="", fg=self.text_color)
        self.name_entry.focus_set()
        
        # Reset hint state
        self.hint_level = 0
        self.hint_btn.config(state="normal")
    
    def check_answer(self):
        """Check if the entered name is correct"""
        if not self.current_student:
            return
            
        user_answer = self.name_entry.get().strip().lower()
        correct_name = self.current_student['name'].lower()
        
        self.attempts += 1
        
        # Check for exact match or close match
        if user_answer == correct_name or self.is_close_match(user_answer, correct_name):
            self.score += 1
            self.feedback_label.config(
                text=f"✓ Correct! That's {self.current_student['name']}",
                fg=self.success_color
            )
            # Auto-advance after 2 seconds
            self.root.after(2000, self.new_student)
        else:
            self.feedback_label.config(
                text=f"✗ Not quite. Try again or click 'Get Hint'",
                fg=self.error_color
            )
        
        self.update_score_display()
    
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
        if not self.current_student:
            return
            
        name = self.current_student['name']
        
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
            self.hint_btn.config(state="disabled")
        
        self.feedback_label.config(text=hint_text, fg=self.hint_color)
    
    def update_score_display(self):
        """Update the score display"""
        if self.attempts > 0:
            percentage = (self.score / self.attempts) * 100
            self.score_label.config(
                text=f"Score: {self.score}/{self.attempts} ({percentage:.1f}%)"
            )
        else:
            self.score_label.config(text="Score: 0/0")
    
    def run(self):
        """Start the game"""
        self.root.mainloop()

def main():
    """Main function to start the application"""
    game = StudentNameGame()
    if hasattr(game, 'root') and game.root.winfo_exists():
        game.run()

if __name__ == "__main__":
    main()