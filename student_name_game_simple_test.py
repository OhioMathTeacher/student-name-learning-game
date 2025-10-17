#!/usr/bin/env python3
"""
Simple Test - Student Name Practice Mode
A minimal version to test if GUI works
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import json

def get_config_path():
    """Get path for storing app configuration"""
    home_dir = os.path.expanduser("~")
    config_dir = os.path.join(home_dir, ".student_name_game")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    return os.path.join(config_dir, "config.json")

def load_config():
    """Load saved configuration"""
    try:
        config_path = get_config_path()
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_config(config):
    """Save configuration"""
    try:
        config_path = get_config_path()
        with open(config_path, 'w') as f:
            json.dump(config, f)
    except:
        pass

def select_folder():
    """Select the folder containing student images"""
    config = load_config()
    saved_folder = config.get('image_folder')
    
    # If we have a saved folder that exists, ask if user wants to use it
    if saved_folder and os.path.exists(saved_folder):
        result = messagebox.askyesno(
            "Use Previous Folder?", 
            f"Use the previously selected folder?\n\n{saved_folder}\n\nClick 'No' to choose a different folder."
        )
        if result:
            return saved_folder
    
    # Show folder selection dialog
    initial_dir = saved_folder if saved_folder and os.path.exists(saved_folder) else os.path.expanduser("~")
    
    folder = filedialog.askdirectory(
        title="Select folder containing student photos",
        initialdir=initial_dir
    )
    
    # Save the selected folder
    if folder:
        config['image_folder'] = folder
        save_config(config)
    
    return folder

def load_images(folder):
    """Load images from folder"""
    if not folder:
        return []
    
    valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    students = []
    
    try:
        for filename in os.listdir(folder):
            if filename.lower().endswith(valid_extensions):
                name_part = os.path.splitext(filename)[0]
                # Extract both first and last name
                if '_' in name_part:
                    parts = name_part.split('_')
                    if len(parts) >= 2:
                        # Assume LastName_FirstName or FirstName_LastName
                        first_name = ''.join(c for c in parts[1] if c.isalpha())
                        last_name = ''.join(c for c in parts[0] if c.isalpha())
                        full_name = f"{first_name} {last_name}"
                    else:
                        full_name = ''.join(c for c in parts[0] if c.isalpha())
                elif ' ' in name_part:
                    parts = name_part.split(' ')
                    first_name = ''.join(c for c in parts[0] if c.isalpha())
                    last_name = ''.join(c for c in parts[-1] if c.isalpha()) if len(parts) > 1 else ''
                    full_name = f"{first_name} {last_name}".strip()
                else:
                    full_name = ''.join(c for c in name_part if c.isalpha())
                
                if full_name:
                    students.append({
                        'name': full_name,
                        'filename': filename,
                        'path': os.path.join(folder, filename)
                    })
    except Exception as e:
        print(f"Error loading images: {e}")
    
    return students

def main():
    # Create main window
    root = tk.Tk()
    root.title("Student Name Practice - Simple Test")
    root.geometry("700x600")
    root.configure(bg="white")
    
    # Variables
    students = []
    current_index = 0
    
    # UI Elements
    title_label = tk.Label(
        root, 
        text="🎓 Student Name Practice Mode", 
        font=("Arial", 18, "bold"), 
        bg="white", 
        fg="black"
    )
    title_label.pack(pady=20)
    
    photo_label = tk.Label(
        root, 
        bg="white",
        text="Click 'Load Photos' to start",
        fg="black",
        font=("Arial", 14)
    )
    photo_label.pack(pady=20)
    
    name_label = tk.Label(
        root, 
        text="", 
        font=("Arial", 24, "bold"), 
        bg="white", 
        fg="#E74C3C",
        relief="solid",
        bd=2,
        padx=20,
        pady=10
    )
    name_label.pack(pady=10)
    
    def load_photos():
        nonlocal students, current_index
        folder = select_folder()
        if folder:
            students = load_images(folder)
            if students:
                current_index = 0
                show_current_student()
                messagebox.showinfo("Success", f"Loaded {len(students)} photos!")
            else:
                messagebox.showerror("Error", "No valid photos found!")
    
    def show_current_student():
        if not students:
            return
        
        student = students[current_index]
        
        # Load and display photo
        try:
            image = Image.open(student['path'])
            image.thumbnail((350, 350), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            photo_label.configure(image=photo, text="")
            photo_label.image = photo  # Keep a reference
        except Exception as e:
            photo_label.configure(image="", text=f"Error loading:\n{student['filename']}")
            photo_label.image = None
        
        # Display student name
        name_label.config(text=student['name'])
        
        # Update progress
        progress_text = f"Student {current_index + 1} of {len(students)} (loops continuously)"
        title_label.config(text=f"🎓 Student Name Practice Mode - {progress_text}")
        
        # Update navigation buttons - now always enabled when we have students
        if students:
            prev_btn.config(state=tk.NORMAL, bg="#3498DB", fg="white")
            next_btn.config(state=tk.NORMAL, bg="#E74C3C", fg="white")
        else:
            prev_btn.config(state=tk.DISABLED, bg="#95A5A6", fg="#7F8C8D")
            next_btn.config(state=tk.DISABLED, bg="#95A5A6", fg="#7F8C8D")
    
    def show_next():
        nonlocal current_index
        if students:
            current_index = (current_index + 1) % len(students)  # Loop back to 0 after last student
            show_current_student()
    
    def show_previous():
        nonlocal current_index
        if students:
            current_index = (current_index - 1) % len(students)  # Loop to last student from first
            show_current_student()
    
    # Buttons
    button_frame = tk.Frame(root, bg="white")
    button_frame.pack(pady=20)
    
    load_btn = tk.Button(
        button_frame,
        text="📁 Load Photos",
        command=load_photos,
        font=("Arial", 16, "bold"),
        bg="#2ECC71",
        fg="white",
        activebackground="#27AE60",
        activeforeground="white",
        padx=30,
        pady=15,
        relief="raised",
        bd=4,
        cursor="hand2"
    )
    load_btn.pack(side=tk.LEFT, padx=10)
    
    prev_btn = tk.Button(
        button_frame,
        text="⬅️ Previous",
        command=show_previous,
        font=("Arial", 16, "bold"),
        bg="#3498DB",
        fg="white",
        activebackground="#2980B9",
        activeforeground="white",
        disabledforeground="#BDC3C7",
        padx=30,
        pady=15,
        relief="raised",
        bd=4,
        cursor="hand2",
        state=tk.DISABLED
    )
    prev_btn.pack(side=tk.LEFT, padx=10)
    
    next_btn = tk.Button(
        button_frame,
        text="Next ➡️",
        command=show_next,
        font=("Arial", 16, "bold"),
        bg="#E74C3C",
        fg="white",
        activebackground="#C0392B",
        activeforeground="white",
        disabledforeground="#BDC3C7",
        padx=30,
        pady=15,
        relief="raised",
        bd=4,
        cursor="hand2",
        state=tk.DISABLED
    )
    next_btn.pack(side=tk.LEFT, padx=10)
    
    # Add spacer and keyboard shortcuts
    spacer_frame = tk.Frame(root, bg="white", height=10)
    spacer_frame.pack()
    
    # Keyboard shortcuts info
    shortcuts_frame = tk.Frame(root, bg="white")
    shortcuts_frame.pack(pady=10)
    
    shortcuts_label = tk.Label(
        shortcuts_frame,
        text="⌨️ Keyboard: ← Previous | → Next | Space Load Photos",
        bg="white",
        fg="#7F8C8D",
        font=("Arial", 11)
    )
    shortcuts_label.pack()
    
    # Instructions
    instructions = tk.Label(
        root,
        text="1. Click 'Load Photos' to select your student photo folder\n2. Use Previous/Next or arrow keys to navigate",
        bg="white",
        fg="#34495E",
        font=("Arial", 12)
    )
    instructions.pack(pady=15)
    
    # Keyboard shortcuts
    def on_key_press(event):
        if event.keysym == 'Left' and students:
            show_previous()
        elif event.keysym == 'Right' and students:
            show_next()
        elif event.keysym == 'space':
            if not students:
                load_photos()
    
    # Bind keyboard events
    root.bind('<Key>', on_key_press)
    root.focus_set()  # Make sure window can receive key events
    
    # Auto-load photos if we have a saved folder
    def auto_load_on_startup():
        config = load_config()
        saved_folder = config.get('image_folder')
        if saved_folder and os.path.exists(saved_folder):
            nonlocal students, current_index
            students = load_images(saved_folder)
            if students:
                current_index = 0
                show_current_student()
                # Update title to show we auto-loaded
                root.title("Student Name Practice - Auto-loaded previous folder")
    
    # Auto-load after a short delay to let UI finish initializing
    root.after(500, auto_load_on_startup)
    
    # Bring window to front
    root.lift()
    root.attributes('-topmost', True)
    root.after(100, lambda: root.attributes('-topmost', False))
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    print("Starting Student Name Practice Mode...")
    main()
    print("Application closed.")