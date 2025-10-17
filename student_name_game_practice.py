#!/usr/bin/env python3
"""
Student Name Learning Game - Practice Mode
A review mode that shows student photos with their names for learning faces.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import random
from PIL import Image, ImageTk
import os
import sys
import json

def get_config_path():
    """Get path for storing app configuration"""
    home_dir = os.path.expanduser("~")
    config_dir = os.path.join(home_dir, ".student_name_game")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    return os.path.join(config_dir, "config.json")

class StudentNameGamePractice:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Student Name Learning Game - Practice Mode")
        self.root.geometry("900x800")
        
        # Dark theme colors
        self.bg_color = "#2C3E50"  # Dark blue-gray
        self.text_color = "#ECF0F1"  # Light gray
        self.accent_color = "#3498DB"  # Blue
        self.success_color = "#27AE60"  # Green
        self.name_color = "#F39C12"  # Orange for student names
        
        self.root.configure(bg=self.bg_color)
        
        # Initialize image data
        self.students = []
        self.image_folder = None
        self.current_index = 0
        self.auto_advance = False
        self.auto_advance_speed = 3000  # 3 seconds
        self.auto_advance_job = None
        
        # Load or select image folder
        if not self.select_folder():
            self.root.destroy()
            return
            
        # Load student images
        self.load_images()
        
        if not self.students:
            messagebox.showerror("Error", f"No valid student images found in the selected folder!\n\nFolder: {self.image_folder}\n\nPlease make sure the folder contains image files (.jpg, .jpeg, .png, .gif, .bmp)")
            self.root.destroy()
            return
        else:
            print(f"✅ Loaded {len(self.students)} student photos from: {self.image_folder}")
            for student in self.students[:5]:  # Show first 5 as examples
                print(f"  - {student['name']} ({student['filename']})")
        
        # Shuffle the students for variety
        random.shuffle(self.students)
        
        # Create GUI
        self.create_widgets()
        
        # Show first student
        self.show_current_student()
        
    def select_folder(self):
        """Select the folder containing student images"""
        # Try to load from config first
        config_path = get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    saved_folder = config.get('image_folder')
                    if saved_folder and os.path.exists(saved_folder):
                        result = messagebox.askyesno(
                            "Use Saved Folder?", 
                            f"Use previously selected folder?\n\n{saved_folder}"
                        )
                        if result:
                            self.image_folder = saved_folder
                            return True
            except:
                pass
        
        # Show folder selection dialog
        folder = filedialog.askdirectory(
            title="Select folder containing student photos",
            initialdir=os.path.expanduser("~")
        )
        
        if folder:
            self.image_folder = folder
            # Save to config
            try:
                with open(config_path, 'w') as f:
                    json.dump({'image_folder': folder}, f)
            except:
                pass
            return True
        return False
    
    def load_images(self):
        """Load and process all student images from the selected folder"""
        if not self.image_folder:
            print("❌ No image folder selected")
            return
        
        print(f"📁 Loading images from: {self.image_folder}")
        
        valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
        all_files = os.listdir(self.image_folder)
        print(f"📄 Found {len(all_files)} total files in folder")
        
        image_files = [f for f in all_files if f.lower().endswith(valid_extensions)]
        print(f"🖼️  Found {len(image_files)} image files: {image_files[:5]}{'...' if len(image_files) > 5 else ''}")
        
        for filename in image_files:
            # Extract student name from filename
            name_part = os.path.splitext(filename)[0]
            
            # Try different naming conventions
            if '_' in name_part:
                parts = name_part.split('_')
                if len(parts) >= 2:
                    # Could be LastName_FirstName or FirstName_LastName
                    first_name = parts[1] if parts[1] else parts[0]
                else:
                    first_name = parts[0]
            elif ' ' in name_part:
                parts = name_part.split(' ')
                first_name = parts[0]  # Use first part as first name
            else:
                first_name = name_part
            
            # Clean up the name
            first_name = ''.join(c for c in first_name if c.isalpha())
            
            if first_name:
                self.students.append({
                    'name': first_name,
                    'filename': filename,
                    'path': os.path.join(self.image_folder, filename)
                })
                print(f"  ➕ Added: {first_name} ({filename})")
            else:
                print(f"  ❌ Skipped: {filename} (couldn't extract name)")
        
        print(f"✅ Successfully loaded {len(self.students)} students total")
    
    def create_widgets(self):
        """Create the main GUI elements"""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Change Photo Folder...", command=self.change_photo_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Practice mode info
        self.info_frame = tk.Frame(self.root, bg=self.bg_color)
        self.info_frame.pack(pady=10)
        
        self.title_label = tk.Label(
            self.info_frame, 
            text="🎓 PRACTICE MODE - Learn Student Faces & Names", 
            font=("Arial", 18, "bold"), 
            bg=self.bg_color, 
            fg=self.success_color
        )
        self.title_label.pack()
        
        self.progress_label = tk.Label(
            self.info_frame, 
            text="", 
            font=("Arial", 14), 
            bg=self.bg_color, 
            fg=self.text_color
        )
        self.progress_label.pack(pady=5)
        
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
        
        # Student name display
        self.name_frame = tk.Frame(self.root, bg=self.bg_color)
        self.name_frame.pack(pady=20)
        
        self.name_display = tk.Label(
            self.name_frame, 
            text="", 
            font=("Arial", 24, "bold"), 
            bg=self.bg_color, 
            fg=self.name_color,
            relief="solid",
            bd=2,
            padx=20,
            pady=10
        )
        self.name_display.pack()
        
        # Navigation buttons
        self.nav_frame = tk.Frame(self.root, bg=self.bg_color)
        self.nav_frame.pack(pady=20)
        
        # Button style
        button_style = {
            "font": ("Arial", 12, "bold"),
            "relief": "raised",
            "bd": 2,
            "padx": 20,
            "pady": 10,
            "cursor": "hand2"
        }
        
        self.prev_btn = tk.Button(
            self.nav_frame,
            text="⬅️ Previous",
            command=self.show_previous,
            bg="#9B59B6",  # Purple
            fg="white",
            activebackground="#8E44AD",
            activeforeground="white",
            **button_style
        )
        self.prev_btn.pack(side=tk.LEFT, padx=10)
        
        self.next_btn = tk.Button(
            self.nav_frame,
            text="Next ➡️",
            command=self.show_next,
            bg=self.accent_color,
            fg="white",
            activebackground="#2980B9",
            activeforeground="white",
            **button_style
        )
        self.next_btn.pack(side=tk.LEFT, padx=10)
        
        self.shuffle_btn = tk.Button(
            self.nav_frame,
            text="🔀 Shuffle",
            command=self.shuffle_students,
            bg="#E67E22",  # Orange
            fg="white",
            activebackground="#D35400",
            activeforeground="white",
            **button_style
        )
        self.shuffle_btn.pack(side=tk.LEFT, padx=10)
        
        # Auto-advance controls
        self.auto_frame = tk.Frame(self.root, bg=self.bg_color)
        self.auto_frame.pack(pady=20)
        
        self.auto_advance_var = tk.BooleanVar()
        self.auto_check = tk.Checkbutton(
            self.auto_frame,
            text="Auto-advance",
            variable=self.auto_advance_var,
            command=self.toggle_auto_advance,
            bg=self.bg_color,
            fg=self.text_color,
            selectcolor=self.bg_color,
            activebackground=self.bg_color,
            activeforeground=self.text_color,
            font=("Arial", 12)
        )
        self.auto_check.pack(side=tk.LEFT, padx=10)
        
        tk.Label(
            self.auto_frame,
            text="Speed:",
            bg=self.bg_color,
            fg=self.text_color,
            font=("Arial", 12)
        ).pack(side=tk.LEFT, padx=(20, 5))
        
        self.speed_var = tk.StringVar(value="3")
        self.speed_combo = ttk.Combobox(
            self.auto_frame,
            textvariable=self.speed_var,
            values=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
            width=5,
            state="readonly"
        )
        self.speed_combo.pack(side=tk.LEFT, padx=5)
        self.speed_combo.bind("<<ComboboxSelected>>", self.update_speed)
        
        tk.Label(
            self.auto_frame,
            text="seconds",
            bg=self.bg_color,
            fg=self.text_color,
            font=("Arial", 12)
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Keyboard shortcuts info
        self.shortcut_frame = tk.Frame(self.root, bg=self.bg_color)
        self.shortcut_frame.pack(pady=10)
        
        shortcuts_text = "Keyboard: ← Previous | → Next | Space Auto-advance | R Shuffle"
        self.shortcuts_label = tk.Label(
            self.shortcut_frame,
            text=shortcuts_text,
            bg=self.bg_color,
            fg="#95A5A6",  # Light gray
            font=("Arial", 10)
        )
        self.shortcuts_label.pack()
        
        # Bind keyboard shortcuts
        self.root.bind('<Left>', lambda e: self.show_previous())
        self.root.bind('<Right>', lambda e: self.show_next())
        self.root.bind('<space>', lambda e: self.toggle_auto_advance())
        self.root.bind('<r>', lambda e: self.shuffle_students())
        self.root.bind('<R>', lambda e: self.shuffle_students())
        
        # Make window focusable for keyboard shortcuts
        self.root.focus_set()
    
    def show_current_student(self):
        """Display the current student's photo and name"""
        if not self.students:
            return
        
        student = self.students[self.current_index]
        
        # Update progress
        progress_text = f"Student {self.current_index + 1} of {len(self.students)}"
        self.progress_label.config(text=progress_text)
        
        # Load and display photo
        try:
            image = Image.open(student['path'])
            
            # Calculate size to fit in window while maintaining aspect ratio
            max_width, max_height = 400, 400
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)
            self.photo_label.configure(image=photo, text="")
            self.photo_label.image = photo  # Keep a reference
            
        except Exception as e:
            self.photo_label.configure(
                image="",
                text=f"Error loading image:\n{student['filename']}",
                fg=self.text_color
            )
            self.photo_label.image = None
        
        # Display student name
        self.name_display.config(text=student['name'])
        
        # Update button states
        self.prev_btn.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if self.current_index < len(self.students) - 1 else tk.DISABLED)
    
    def show_next(self):
        """Show the next student"""
        if self.current_index < len(self.students) - 1:
            self.current_index += 1
            self.show_current_student()
        else:
            # At the end, offer to restart
            result = messagebox.askyesno(
                "End Reached", 
                "You've reached the end of all students!\n\nWould you like to start over from the beginning?"
            )
            if result:
                self.current_index = 0
                self.show_current_student()
    
    def show_previous(self):
        """Show the previous student"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_student()
    
    def shuffle_students(self):
        """Shuffle the order of students"""
        current_student = self.students[self.current_index]
        random.shuffle(self.students)
        
        # Try to find the current student in the new order
        try:
            self.current_index = self.students.index(current_student)
        except ValueError:
            self.current_index = 0
        
        self.show_current_student()
        messagebox.showinfo("Shuffled", "Student order has been shuffled!")
    
    def toggle_auto_advance(self):
        """Toggle auto-advance mode"""
        self.auto_advance = self.auto_advance_var.get()
        
        if self.auto_advance:
            self.start_auto_advance()
        else:
            self.stop_auto_advance()
    
    def start_auto_advance(self):
        """Start auto-advancing through students"""
        if self.auto_advance_job:
            self.root.after_cancel(self.auto_advance_job)
        
        self.auto_advance_job = self.root.after(self.auto_advance_speed, self.auto_advance_next)
    
    def stop_auto_advance(self):
        """Stop auto-advancing"""
        if self.auto_advance_job:
            self.root.after_cancel(self.auto_advance_job)
            self.auto_advance_job = None
    
    def auto_advance_next(self):
        """Auto-advance to next student"""
        if not self.auto_advance:
            return
        
        if self.current_index < len(self.students) - 1:
            self.current_index += 1
            self.show_current_student()
            self.start_auto_advance()  # Schedule next advance
        else:
            # At the end, loop back to beginning
            self.current_index = 0
            self.show_current_student()
            self.start_auto_advance()
    
    def update_speed(self, event=None):
        """Update auto-advance speed"""
        try:
            speed_seconds = int(self.speed_var.get())
            self.auto_advance_speed = speed_seconds * 1000  # Convert to milliseconds
            
            # If auto-advance is running, restart with new speed
            if self.auto_advance:
                self.stop_auto_advance()
                self.start_auto_advance()
        except ValueError:
            pass
    
    def change_photo_folder(self):
        """Change the photo folder"""
        folder = filedialog.askdirectory(
            title="Select new folder containing student photos",
            initialdir=self.image_folder or os.path.expanduser("~")
        )
        
        if folder:
            self.image_folder = folder
            
            # Save to config
            try:
                config_path = get_config_path()
                with open(config_path, 'w') as f:
                    json.dump({'image_folder': folder}, f)
            except:
                pass
            
            # Reload images
            self.students = []
            self.load_images()
            
            if not self.students:
                messagebox.showerror("Error", "No valid student images found in the selected folder!")
                return
            
            # Shuffle and restart
            random.shuffle(self.students)
            self.current_index = 0
            self.show_current_student()
            messagebox.showinfo("Success", f"Loaded {len(self.students)} student photos!")

def main():
    try:
        app = StudentNameGamePractice()
        app.root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")

if __name__ == "__main__":
    main()