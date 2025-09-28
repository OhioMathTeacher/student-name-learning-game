#!/usr/bin/env python3
"""
Student Name Learning Game
A GUI application to help teachers learn student names using photos,
with speech recognition and text-to-speech feedback.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import random
import threading
import time

# Speech libraries (will handle import errors gracefully)
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

class StudentNameGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Name Learning Game")
        self.root.geometry("1000x1050")  # Taller to show full image initially
        self.root.configure(bg='#f0f0f0')
        
        # Initialize variables
        self.photos_dir = os.path.dirname(os.path.abspath(__file__))
        self.students = {"Section A": [], "Section B": []}
        self.current_student = None
        self.current_section = "Both"
        self.attempt_count = 0
        self.max_attempts = 3
        self.hint_level = 0  # Track progressive hints
        
        # Progress tracking
        self.session_students = []  # Students for current session
        self.session_index = 0  # Current position in session
        self.correct_answers = 0
        self.total_attempts = 0
        self.high_scores = []  # Store high scores
        
        # Advanced tracking
        self.student_performance = {}  # Track performance per student
        self.current_session_results = {}  # Track this session's results
        self.difficult_students = []  # Students consistently missed
        
        # Review mode
        self.review_mode = False
        self.review_speed = 3.0  # seconds between images
        self.review_timer = None
        self.review_paused = False
        
        # Initialize speech components
        self.recognizer = sr.Recognizer() if SPEECH_RECOGNITION_AVAILABLE else None
        self.microphone = sr.Microphone() if SPEECH_RECOGNITION_AVAILABLE else None
        self.tts_engine = pyttsx3.init() if TTS_AVAILABLE else None
        
        if self.tts_engine:
            # Configure TTS voice
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Try to find a female voice, fall back to first available
                for voice in voices:
                    if 'female' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            self.tts_engine.setProperty('rate', 150)  # Slower speech rate
        
        # Load student data
        self.load_students()
        
        # Create GUI
        self.create_widgets()
        
        # Show initial instructions
        self.show_instructions()
        
        # Auto-start the first session
        self.root.after(500, self.auto_start_session)  # Small delay to let GUI load
    
    def load_students(self):
        """Load student photos and parse names from filenames"""
        for section in ["Section A", "Section B"]:
            section_path = os.path.join(self.photos_dir, section)
            if os.path.exists(section_path):
                for filename in os.listdir(section_path):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                        # Parse name from filename (Last_First.jpeg format)
                        name_part = os.path.splitext(filename)[0]
                        if '_' in name_part:
                            last_name, first_name = name_part.split('_', 1)
                            full_path = os.path.join(section_path, filename)
                            self.students[section].append({
                                'first_name': first_name,
                                'last_name': last_name,
                                'full_name': f"{first_name} {last_name}",
                                'photo_path': full_path,
                                'section': section
                            })
        
        print(f"Loaded {len(self.students['Section A'])} students from Section A")
        print(f"Loaded {len(self.students['Section B'])} students from Section B")
    
    def create_widgets(self):
        """Create the main GUI elements"""
        # Title
        title_label = tk.Label(
            self.root, 
            text="Student Name Learning Game", 
            font=("Arial", 20, "bold"),
            bg='#f0f0f0',
            fg='#333'
        )
        title_label.pack(pady=10)
        
        # Section selection frame
        section_frame = tk.Frame(self.root, bg='#f0f0f0')
        section_frame.pack(pady=10)
        
        tk.Label(section_frame, text="Select Section:", font=("Arial", 12), bg='#f0f0f0').pack(side=tk.LEFT, padx=5)
        
        self.section_var = tk.StringVar(value="Both")
        sections = ["Section A", "Section B", "Both"]
        
        for section in sections:
            rb = tk.Radiobutton(
                section_frame,
                text=section,
                variable=self.section_var,
                value=section,
                font=("Arial", 10),
                bg='#f0f0f0',
                command=self.on_section_change
            )
            rb.pack(side=tk.LEFT, padx=10)
        
        # Mode selection frame
        mode_frame = tk.Frame(self.root, bg='#f0f0f0')
        mode_frame.pack(pady=5)
        
        # Review mode toggle
        self.review_button = tk.Button(
            mode_frame,
            text="🔄 Start Review Mode",
            command=self.toggle_review_mode,
            font=("Arial", 11, "bold"),
            bg='#9C27B0',
            fg='white',
            padx=15,
            pady=3
        )
        self.review_button.pack(side=tk.LEFT, padx=10)
        
        # Pause button (initially hidden)
        self.pause_button = tk.Button(
            mode_frame,
            text="⏸️ Pause",
            command=self.toggle_pause,
            font=("Arial", 11),
            bg='#FF9800',
            fg='white',
            padx=12,
            pady=3
        )
        # Don't pack initially - will show in review mode
        
        # Speed control frame
        speed_frame = tk.Frame(mode_frame, bg='#f0f0f0')
        speed_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(speed_frame, text="Review Speed:", font=("Arial", 9), bg='#f0f0f0').pack(side=tk.LEFT)
        self.speed_var = tk.DoubleVar(value=3.0)
        self.speed_scale = tk.Scale(
            speed_frame,
            from_=0.5,
            to=10.0,
            resolution=0.5,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            command=self.on_speed_change,
            length=100,
            bg='#f0f0f0'
        )
        self.speed_scale.pack(side=tk.LEFT, padx=5)
        tk.Label(speed_frame, text="sec", font=("Arial", 9), bg='#f0f0f0').pack(side=tk.LEFT)
        
        # Photo display
        self.photo_frame = tk.Frame(self.root, bg='#f0f0f0', relief='raised', bd=2)
        self.photo_frame.pack(pady=15, padx=40, fill=tk.BOTH, expand=True)  # Larger area
        
        self.photo_label = tk.Label(
            self.photo_frame,
            text="Click 'New Student' to begin!",
            font=("Arial", 18),
            bg='white',
            fg='#666',
            width=40,  # Wider for better photo display
            height=30  # Much taller for better photo viewing
        )
        self.photo_label.pack(expand=True, fill=tk.BOTH, padx=15, pady=15)  # More padding
        
        # Control buttons frame
        self.controls_frame = tk.Frame(self.root, bg='#f0f0f0')
        self.controls_frame.pack(pady=10)
        
        # Voice input button
        if SPEECH_RECOGNITION_AVAILABLE:
            self.voice_button = tk.Button(
                self.controls_frame,
                text="🎤 Say Name",
                command=self.listen_for_name,
                font=("Arial", 12),
                bg='#2196F3',
                fg='white',
                padx=15,
                pady=5
            )
            self.voice_button.pack(side=tk.LEFT, padx=5)
        
        # Text input frame
        self.input_frame = tk.Frame(self.root, bg='#f0f0f0')
        self.input_frame.pack(pady=5)
        
        tk.Label(self.input_frame, text="Or type the name:", font=("Arial", 10), bg='#f0f0f0').pack()
        
        self.name_entry = tk.Entry(self.input_frame, font=("Arial", 12), width=30)
        self.name_entry.pack(pady=5)
        self.name_entry.bind('<Return>', self.check_name_entry)
        
        # Submit and hint buttons
        self.button_frame = tk.Frame(self.root, bg='#f0f0f0')
        self.button_frame.pack(pady=5)
        
        # Submit and hint buttons
        self.button_frame = tk.Frame(self.root, bg='#f0f0f0')
        self.button_frame.pack(pady=5)
        
        submit_button = tk.Button(
            self.button_frame,
            text="Submit",
            command=self.check_name_entry,
            font=("Arial", 10),
            bg='#FF9800',
            fg='white',
            padx=15
        )
        submit_button.pack(side=tk.LEFT, padx=5)
        
        self.hint_button = tk.Button(
            self.button_frame,
            text="Give Hint",
            command=self.give_hint,
            font=("Arial", 10),
            bg='#9C27B0',
            fg='white',
            padx=15
        )
        self.hint_button.pack(side=tk.LEFT, padx=5)
        
        # Difficulty analysis button
        self.analysis_button = tk.Button(
            self.button_frame,
            text="📊 Analysis",
            command=self.show_difficulty_analysis,
            font=("Arial", 10),
            bg='#607D8B',
            fg='white',
            padx=12
        )
        self.analysis_button.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = tk.Label(
            self.root,
            text="Ready to start!",
            font=("Arial", 11),
            bg='#f0f0f0',
            fg='#666'
        )
        self.status_label.pack(pady=5)
        
        # Progress label
        self.progress_label = tk.Label(
            self.root,
            text="Click 'New Student' to begin your session!",
            font=("Arial", 10, "bold"),
            bg='#f0f0f0',
            fg='#2196F3'
        )
        self.progress_label.pack(pady=5)
        
        # Instructions
        instructions = """
Instructions:
1. Select a section - photos start automatically!
2. Click 🎤 to speak (text will appear below) OR type directly
3. Press Enter or click Submit to check your answer
4. Get hints if you need help!
5. Try Review Mode for quick name/face memorization!
        """
        
        self.instructions_label = tk.Label(
            self.root,
            text=instructions,
            font=("Arial", 9),
            bg='#f0f0f0',
            fg='#555',
            justify=tk.LEFT
        )
        self.instructions_label.pack(pady=5)
    
    def show_instructions(self):
        """Show initial instructions and check for dependencies"""
        messages = []
        
        if not SPEECH_RECOGNITION_AVAILABLE:
            messages.append("Speech recognition not available. Install with: pip install SpeechRecognition pyaudio")
        
        if not TTS_AVAILABLE:
            messages.append("Text-to-speech not available. Install with: pip install pyttsx3")
        
        if messages:
            messagebox.showwarning("Missing Dependencies", "\n\n".join(messages))
    
    def auto_start_session(self):
        """Automatically start a session when the app loads"""
        if self.start_new_session():
            self.new_student()
        else:
            self.status_label.config(text="No students found. Check your photo folders.")
    
    def toggle_review_mode(self):
        """Toggle between quiz mode and review mode"""
        self.review_mode = not self.review_mode
        
        if self.review_mode:
            self.start_review_mode()
        else:
            self.stop_review_mode()
    
    def start_review_mode(self):
        """Start review mode - shows names with photos automatically"""
        self.review_button.config(text="🎯 Stop Review Mode", bg='#f44336')
        self.review_paused = False
        
        # Show pause button
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        # Hide input controls
        self.controls_frame.pack_forget()
        self.input_frame.pack_forget()
        self.button_frame.pack_forget()
        
        # Start new session for review
        if self.start_new_session():
            # Immediately show the first student (don't wait for timer)
            self.show_review_student()
        
        self.update_progress_display()
    
    def stop_review_mode(self):
        """Stop review mode and return to quiz mode"""
        self.review_button.config(text="🔄 Start Review Mode", bg='#9C27B0')
        self.review_paused = False
        
        # Hide pause button
        self.pause_button.pack_forget()
        
        # Cancel any pending review timer
        if self.review_timer:
            self.root.after_cancel(self.review_timer)
            self.review_timer = None
        
        # Show input controls
        self.controls_frame.pack(pady=10)
        self.input_frame.pack(pady=5)
        self.button_frame.pack(pady=5)
        
        # Restart quiz session
        self.auto_start_session()
    
    def on_speed_change(self, value):
        """Handle speed slider change"""
        self.review_speed = float(value)
        if self.review_mode and self.review_timer:
            # Speed changed during review - it will take effect on next advance
            pass
    
    def toggle_pause(self):
        """Toggle pause/resume in review mode"""
        if not self.review_mode:
            return
            
        self.review_paused = not self.review_paused
        
        if self.review_paused:
            # Pause - cancel timer and update button
            if self.review_timer:
                self.root.after_cancel(self.review_timer)
                self.review_timer = None
            self.pause_button.config(text="▶️ Resume", bg='#4CAF50')
            # Update status to show paused
            current_name = self.current_student['full_name'] if self.current_student else "Unknown"
            current_section = self.current_student['section'] if self.current_student else "Unknown"
            self.status_label.config(
                text=f"⏸️ PAUSED - {current_name} ({current_section})",
                fg='#FF9800',
                font=("Arial", 14, "bold")
            )
        else:
            # Resume - update button and schedule next advance
            self.pause_button.config(text="⏸️ Pause", bg='#FF9800')
            # Show current student name normally
            if self.current_student:
                student_name = self.current_student['full_name']
                student_section = self.current_student['section']
                self.status_label.config(
                    text=f"📖 {student_name} ({student_section})",
                    fg='#2196F3',
                    font=("Arial", 14, "bold")
                )
            # Schedule next advance
            self.review_timer = self.root.after(
                int(self.review_speed * 1000), 
                self.show_review_student
            )
    
    def show_review_student(self):
        """Show current student in review mode with name displayed"""
        if not self.session_students or not self.review_mode:
            return
            
        if self.session_index >= len(self.session_students):
            # Review session complete - restart
            self.session_index = 0
            random.shuffle(self.session_students)  # Re-shuffle for variety
        
        self.current_student = self.session_students[self.session_index]
        
        # Load and display photo
        try:
            image = Image.open(self.current_student['photo_path'])
            # Resize image to consistent dimensions
            image = image.convert('RGB')
            width, height = image.size
            size = min(width, height)
            left = (width - size) // 2
            top = (height - size) // 2
            image = image.crop((left, top, left + size, top + size))
            image = image.resize((600, 600), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            self.photo_label.config(image=photo, text="")
            self.photo_label.image = photo
            
            # Show the student's name prominently
            student_name = self.current_student['full_name']
            student_section = self.current_student['section']
            
            if self.review_paused:
                self.status_label.config(
                    text=f"⏸️ PAUSED - {student_name} ({student_section})",
                    fg='#FF9800',
                    font=("Arial", 14, "bold")
                )
            else:
                self.status_label.config(
                    text=f"📖 {student_name} ({student_section})",
                    fg='#2196F3',
                    font=("Arial", 14, "bold")
                )
            
        except Exception as e:
            self.status_label.config(text=f"Error loading image: {e}")
            
        self.session_index += 1
        self.update_progress_display()
        
        # Schedule next student only if not paused
        if self.review_mode and not self.review_paused:
            self.review_timer = self.root.after(
                int(self.review_speed * 1000), 
                self.show_review_student
            )
    
    def track_student_performance(self, student_id, success, attempts):
        """Track individual student performance for difficulty analysis"""
        if student_id not in self.student_performance:
            self.student_performance[student_id] = {
                'total_attempts': 0,
                'first_try_success': 0,
                'partial_success': 0,
                'failures': 0,
                'average_attempts': 0,
                'last_attempts': []  # Track recent attempt counts
            }
        
        perf = self.student_performance[student_id]
        perf['total_attempts'] += 1
        perf['last_attempts'].append(attempts)
        
        # Keep only last 10 attempts for recent performance
        if len(perf['last_attempts']) > 10:
            perf['last_attempts'].pop(0)
        
        if success == True:
            perf['first_try_success'] += 1
        elif success == "partial":
            perf['partial_success'] += 1
        else:
            perf['failures'] += 1
        
        # Calculate average attempts
        perf['average_attempts'] = sum(perf['last_attempts']) / len(perf['last_attempts'])
    
    def show_difficulty_analysis(self):
        """Show analysis of difficult students with memory strategies"""
        if not self.student_performance:
            messagebox.showinfo("Analysis", "No performance data yet. Complete some quiz sessions first!")
            return
        
        # Analyze difficulty
        difficult_students = []
        struggling_students = []
        
        for student_id, perf in self.student_performance.items():
            if perf['total_attempts'] >= 3:  # Need at least 3 attempts for analysis
                success_rate = (perf['first_try_success'] + perf['partial_success'] * 0.5) / perf['total_attempts']
                
                if success_rate < 0.3:  # Less than 30% success
                    difficult_students.append((student_id, perf, success_rate))
                elif success_rate < 0.6 or perf['average_attempts'] > 2:  # Less than 60% success or takes many tries
                    struggling_students.append((student_id, perf, success_rate))
        
        # Sort by difficulty (lowest success rate first)
        difficult_students.sort(key=lambda x: x[2])
        struggling_students.sort(key=lambda x: x[2])
        
        self.show_analysis_window(difficult_students, struggling_students)
    
    def show_analysis_window(self, difficult_students, struggling_students):
        """Show detailed analysis window with memory strategies"""
        analysis_window = tk.Toplevel(self.root)
        analysis_window.title("Student Difficulty Analysis & Memory Strategies")
        analysis_window.geometry("700x600")
        analysis_window.configure(bg='#2C3E50')  # Dark blue-grey background
        
        # Add a nice header
        header_frame = tk.Frame(analysis_window, bg='#34495E', height=60)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(
            header_frame, 
            text="📊 Student Performance Analysis",
            font=("Arial", 16, "bold"),
            bg='#34495E',
            fg='#ECF0F1',
            pady=15
        )
        header_label.pack()
        
        # Create scrollable text area with better styling
        frame = tk.Frame(analysis_window, bg='#2C3E50')
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(frame, bg='#34495E', troughcolor='#2C3E50')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_area = tk.Text(
            frame, 
            wrap=tk.WORD, 
            yscrollcommand=scrollbar.set, 
            font=("Arial", 11), 
            bg='#ECF0F1',  # Light grey background for text
            fg='#2C3E50',  # Dark text
            selectbackground='#3498DB',  # Blue selection
            selectforeground='white',
            relief=tk.FLAT,
            borderwidth=0,
            padx=15,
            pady=15
        )
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_area.yview)
        
        # Add close button with nice styling
        button_frame = tk.Frame(analysis_window, bg='#2C3E50')
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        close_button = tk.Button(
            button_frame,
            text="✕ Close Analysis",
            command=analysis_window.destroy,
            font=("Arial", 11, "bold"),
            bg='#E74C3C',
            fg='white',
            activebackground='#C0392B',
            activeforeground='white',
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        close_button.pack(side=tk.RIGHT)
        
        # Build analysis content
        content = "📊 STUDENT DIFFICULTY ANALYSIS & MEMORY STRATEGIES\n"
        content += "=" * 60 + "\n\n"
        
        if difficult_students:
            content += "🚨 MOST CHALLENGING STUDENTS:\n"
            content += "-" * 40 + "\n"
            for student_id, perf, success_rate in difficult_students:
                name = student_id.replace('_', ' ')
                content += f"\n👤 {name}\n"
                content += f"   Success Rate: {success_rate:.1%}\n"
                content += f"   Average Attempts: {perf['average_attempts']:.1f}\n"
                content += f"   Total Attempts: {perf['total_attempts']}\n"
                content += f"   💡 MEMORY STRATEGIES:\n"
                content += self.get_memory_strategies(name, student_id)
                content += "\n" + "-" * 30 + "\n"
        
        if struggling_students:
            content += "\n⚠️ STUDENTS NEEDING PRACTICE:\n"
            content += "-" * 40 + "\n"
            for student_id, perf, success_rate in struggling_students:
                name = student_id.replace('_', ' ')
                content += f"\n👤 {name}\n"
                content += f"   Success Rate: {success_rate:.1%}\n"
                content += f"   Average Attempts: {perf['average_attempts']:.1f}\n"
                content += f"   💡 QUICK TIPS:\n"
                content += self.get_memory_strategies(name, student_id, brief=True)
                content += "\n" + "-" * 20 + "\n"
        
        if not difficult_students and not struggling_students:
            content += "🎉 EXCELLENT WORK!\n\n"
            content += "You don't have any consistently difficult students.\n"
            content += "Your student name recognition is strong!\n\n"
            content += "Keep practicing to maintain your skills."
        
        # General memory tips
        content += "\n\n🧠 GENERAL MEMORY TECHNIQUES:\n"
        content += "=" * 40 + "\n"
        content += "• Name Association: Connect names to people you know\n"
        content += "• Physical Features: Link names to distinctive features\n"
        content += "• Rhyming: Create rhymes with names (Katie = 'Great-y')\n"
        content += "• Story Method: Create short stories about students\n"
        content += "• Repetition: Use their names frequently in conversation\n"
        content += "• Visual Anchors: Connect names to objects or places\n"
        
        text_area.insert('1.0', content)
        text_area.config(state=tk.DISABLED)  # Make read-only
    
    def get_memory_strategies(self, name, student_id, brief=False):
        """Generate personalized memory strategies for a student"""
        first_name, last_name = name.split(' ', 1) if ' ' in name else (name, '')
        
        strategies = []
        
        # Name-based strategies
        if first_name:
            # Rhyme strategy
            rhymes = {
                'Katie': 'Great-y', 'Emma': 'Lemma', 'Grace': 'Ace', 'Sarah': 'Stair-ah',
                'Mike': 'Bike', 'John': 'Gone', 'Anna': 'Banana', 'Lisa': 'Pizza',
                'David': 'Gravid', 'Chris': 'Swiss', 'Amy': 'Game-y'
            }
            if first_name in rhymes:
                strategies.append(f"🎵 Rhyme: '{first_name} the {rhymes[first_name]}'")
            
            # Famous person association
            famous = {
                'Emma': 'Emma Watson', 'Grace': 'Grace Kelly', 'Sarah': 'Sarah Jessica Parker',
                'Katie': 'Katie Holmes', 'Anna': 'Anna Kendrick', 'Lisa': 'Lisa Simpson',
                'Mike': 'Mike Tyson', 'David': 'David Bowie', 'Chris': 'Chris Evans'
            }
            if first_name in famous:
                strategies.append(f"⭐ Celebrity: Think '{famous[first_name]}'")
            
            # Letter/sound association
            if first_name.startswith(('A', 'E', 'I', 'O', 'U')):
                strategies.append(f"🔤 Vowel name: '{first_name}' starts with a vowel - easy to remember!")
            
            # Name meaning
            meanings = {
                'Grace': 'elegance', 'Emma': 'universal', 'Sarah': 'princess',
                'David': 'beloved', 'Anna': 'grace', 'Lisa': 'God is my oath'
            }
            if first_name in meanings:
                strategies.append(f"💭 Meaning: '{first_name}' means '{meanings[first_name]}'")
        
        # Add general strategies
        strategies.extend([
            "👀 Focus on their most distinctive feature when you see them",
            "🗣️ Use their name 3 times when you first meet them",
            "📝 Write their name down while looking at their photo"
        ])
        
        if brief:
            return "      • " + "\n      • ".join(strategies[:2]) + "\n"
        else:
            return "      • " + "\n      • ".join(strategies) + "\n"
    
    def on_section_change(self):
        """Handle section selection change"""
        self.current_section = self.section_var.get()
        self.status_label.config(text=f"Section changed to: {self.current_section} - Loading students...")
        # Reset session when section changes and auto-start
        self.session_students = []
        self.session_index = 0
        self.correct_answers = 0
        self.total_attempts = 0
        self.update_progress_display()
        
        # Auto-start new session with small delay
        self.root.after(300, self.auto_start_session)
    
    def start_new_session(self):
        """Start a new session with all students from selected section"""
        if self.current_section == "Both":
            self.session_students = (self.students["Section A"] + self.students["Section B"]).copy()
        else:
            self.session_students = self.students[self.current_section].copy()
        
        # Ensure proper randomization every time
        random.shuffle(self.session_students)
        random.shuffle(self.session_students)  # Double shuffle for extra randomness
        
        self.session_index = 0
        self.correct_answers = 0
        self.total_attempts = 0
        
        self.update_progress_display()
        return len(self.session_students) > 0
    
    def update_progress_display(self):
        """Update the progress display"""
        if not self.session_students:
            self.progress_label.config(text="Loading session...")
            return
            
        progress_text = f"Student {self.session_index + 1} of {len(self.session_students)}"
        if self.total_attempts > 0:
            percentage = (self.correct_answers / self.total_attempts) * 100
            progress_text += f" | Session Score: {percentage:.1f}% ({self.correct_answers}/{self.total_attempts})"
        
        # Show high score
        if self.high_scores:
            best_score = max(self.high_scores)
            progress_text += f" | Best: {best_score:.1f}%"
            
        self.progress_label.config(text=progress_text)
    
    def get_available_students(self):
        """Get list of students based on current section selection"""
        if self.current_section == "Both":
            return self.students["Section A"] + self.students["Section B"]
        else:
            return self.students[self.current_section]
    
    def new_student(self):
        """Display the next student in the session"""
        # Check if session is complete
        if self.session_students and self.session_index >= len(self.session_students):
            # Session completed - show final score
            self.show_session_complete()
            return
        
        # Start new session if needed
        if not self.session_students:
            if not self.start_new_session():
                self.status_label.config(text=f"No students found in {self.current_section}")
                return
        
        # Get current student
        self.current_student = self.session_students[self.session_index]
        self.attempt_count = 0
        self.hint_level = 0  # Reset hints for new student
        
        # Load and display photo
        try:
            image = Image.open(self.current_student['photo_path'])
            # Resize image to consistent dimensions (square format for uniformity)
            image = image.convert('RGB')  # Ensure consistent color mode
            # Create a square crop from the center of the image
            width, height = image.size
            size = min(width, height)
            left = (width - size) // 2
            top = (height - size) // 2
            image = image.crop((left, top, left + size, top + size))
            # Resize to consistent size - much larger for better viewing
            image = image.resize((600, 600), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            self.photo_label.config(image=photo, text="")
            self.photo_label.image = photo  # Keep a reference
            
            self.status_label.config(
                text=f"Who is this student from {self.current_student['section']}?",
                fg='#666'
            )
            self.name_entry.delete(0, tk.END)
            self.name_entry.focus()
            
            self.update_progress_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image: {e}")
    
    def show_session_complete(self):
        """Show session completion dialog and start new session"""
        if self.total_attempts > 0:
            percentage = (self.correct_answers / self.total_attempts) * 100
            self.high_scores.append(percentage)
            
            message = f"Session Complete!\n\n"
            message += f"Final Score: {percentage:.1f}%\n"
            message += f"Correct: {self.correct_answers}/{self.total_attempts}\n\n"
            
            if percentage >= 90:
                message += "🏆 Excellent work! Outstanding performance!"
            elif percentage >= 80:
                message += "🎉 Great job! You're getting to know your students!"
            elif percentage >= 70:
                message += "👍 Good progress! Keep practicing!"
            else:
                message += "📚 Keep practicing - you'll get there!"
                
            message += f"\n\nBest score this session: {max(self.high_scores):.1f}%"
            message += "\n\nStarting a new session automatically..."
            
            messagebox.showinfo("Session Complete", message)
        
        # Auto-start new session
        self.root.after(500, self.auto_start_session)
    
    def listen_for_name(self):
        """Listen for voice input in a separate thread"""
        if not SPEECH_RECOGNITION_AVAILABLE:
            messagebox.showwarning("Speech Recognition", "Speech recognition not available")
            return
        
        if not self.current_student:
            messagebox.showinfo("Info", "Please select a new student first")
            return
        
        # Run speech recognition in a separate thread to avoid freezing GUI
        threading.Thread(target=self._speech_recognition_thread, daemon=True).start()
    
    def _speech_recognition_thread(self):
        """Speech recognition thread"""
        try:
            self.voice_button.config(state='disabled', text="🎤 Listening...")
            self.status_label.config(text="🎤 Listening... Speak now!", fg='blue')
            
            with self.microphone as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
            
            # Recognize speech
            try:
                text = self.recognizer.recognize_google(audio)
                self.root.after(0, self._handle_voice_input, text)
            except sr.UnknownValueError:
                self.root.after(0, self._handle_voice_error, "Could not understand audio")
            except sr.RequestError as e:
                self.root.after(0, self._handle_voice_error, f"Speech service error: {e}")
                
        except sr.WaitTimeoutError:
            self.root.after(0, self._handle_voice_error, "Listening timeout")
        except Exception as e:
            self.root.after(0, self._handle_voice_error, f"Error: {e}")
        finally:
            self.root.after(0, lambda: self.voice_button.config(state='normal', text="🎤 Say Name"))
    
    def _handle_voice_input(self, text):
        """Handle successful voice input"""
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, text)
        self.status_label.config(text=f"I heard: '{text}' - Press Enter or click Submit to check!", fg='blue')
        self.name_entry.focus()  # Focus on the text field for easy Enter press
    
    def _handle_voice_error(self, error_message):
        """Handle voice input error"""
        self.status_label.config(text=f"Voice error: {error_message} - Try again or type the name.", fg='red')
    
    def check_name_entry(self, event=None):
        """Check the name from text entry"""
        name = self.name_entry.get().strip()
        if name:
            self.check_name(name)
    
    def check_name(self, guess):
        """Check if the guessed name is correct"""
        if not self.current_student:
            messagebox.showinfo("Info", "Please select a new student first")
            return
        
        self.attempt_count += 1
        
        # Clean up the guess for comparison
        guess_clean = guess.lower().strip()
        first_name = self.current_student['first_name'].lower()
        last_name = self.current_student['last_name'].lower()
        full_name = self.current_student['full_name'].lower()
        
        # Check various name combinations
        exact_match = (
            guess_clean == first_name or
            guess_clean == last_name or
            guess_clean == full_name or
            guess_clean == f"{last_name} {first_name}" or
            guess_clean == f"{first_name} {last_name}"
        )
        
        # Check for close matches (fuzzy matching)
        close_first = self.is_close_match(guess_clean, first_name)
        close_last = self.is_close_match(guess_clean, last_name)
        close_full = (
            self.is_close_match(guess_clean, full_name) or
            self.is_close_match(guess_clean, f"{last_name} {first_name}") or
            self.is_close_match(guess_clean, f"{first_name} {last_name}")
        )
        
        if exact_match:
            # Only count as correct if it's the first attempt
            if self.attempt_count == 1:
                self.handle_correct_answer()
            else:
                self.handle_late_correct_answer()
        elif close_first or close_last or close_full:
            self.handle_close_answer(guess)
        else:
            self.handle_incorrect_answer(guess)
    
    def is_close_match(self, guess, target):
        """Check if guess is close to target (handles common variations)"""
        if not guess or not target:
            return False
        
        # Handle common name variations
        variations = {
            'gracie': ['grace'],
            'grace': ['gracie'], 
            'katie': ['kate', 'kathryn', 'katherine'],
            'kate': ['katie', 'kathryn', 'katherine'],
            'kathryn': ['katie', 'kate', 'katherine'],
            'katherine': ['katie', 'kate', 'kathryn'],
            'mike': ['michael'],
            'michael': ['mike'],
            'joe': ['joseph'],
            'joseph': ['joe'],
            'bob': ['robert'],
            'robert': ['bob'],
            'bill': ['william'],
            'william': ['bill'],
            'jim': ['james'],
            'james': ['jim'],
            'tom': ['thomas'],
            'thomas': ['tom'],
            'nick': ['nicholas'],
            'nicholas': ['nick'],
            'chris': ['christopher', 'christine', 'christina'],
            'christopher': ['chris'],
            'christine': ['chris'],
            'christina': ['chris']
        }
        
        # Check if guess is a known variation of target
        if target in variations and guess in variations[target]:
            return True
        if guess in variations and target in variations[guess]:
            return True
            
        # Check for partial matches (at least 3 characters and 80% similar)
        if len(guess) >= 3 and len(target) >= 3:
            # Simple similarity check
            if guess in target or target in guess:
                return True
            # Check if they start the same and are close in length
            if guess[:3] == target[:3] and abs(len(guess) - len(target)) <= 2:
                return True
                
        return False
    
    def handle_close_answer(self, guess):
        """Handle when the answer is close but not exact"""
        correct_name = self.current_student['full_name']
        remaining = self.max_attempts - self.attempt_count
        
        if remaining > 0:
            self.status_label.config(
                text=f"🎯 Very close! '{guess}' is almost right. Try the exact spelling? ({remaining} attempts left)",
                fg='orange'
            )
            
            if self.tts_engine:
                threading.Thread(
                    target=lambda: self.speak(f"Very close! Try the exact spelling."),
                    daemon=True
                ).start()
        else:
            # Out of attempts
            self.total_attempts += 1
            self.session_index += 1
            
            self.status_label.config(
                text=f"🎯 Close! You said '{guess}' - the exact answer is: {correct_name}",
                fg='red'
            )
            
            if self.tts_engine:
                threading.Thread(
                    target=lambda: self.speak(f"Close! The exact answer is {correct_name}"),
                    daemon=True
                ).start()
            
            self.update_progress_display()
            self.root.after(2500, self.new_student)
    
    def handle_late_correct_answer(self):
        """Handle correct answer that wasn't on first try"""
        correct_name = self.current_student['full_name']
        student_id = f"{self.current_student['last_name']}_{self.current_student['first_name']}"
        
        # Update progress tracking (correct but not first try)
        self.total_attempts += 1
        self.session_index += 1
        
        # Track as partial success (correct but took multiple tries)
        self.track_student_performance(student_id, "partial", self.attempt_count)
        
        self.status_label.config(
            text=f"✅ Correct! This is {correct_name} (but it took {self.attempt_count} tries)",
            fg='green'
        )
        
        # Text-to-speech feedback
        if self.tts_engine:
            threading.Thread(
                target=lambda: self.speak(f"Correct! This is {correct_name}"),
                daemon=True
            ).start()
        
        self.name_entry.delete(0, tk.END)
        self.update_progress_display()
        
        # Auto-advance to next student
        self.root.after(1500, self.new_student)
    
    def handle_correct_answer(self):
        """Handle correct answer"""
        congratulations = [
            "Excellent! Well done!",
            "Perfect! You got it right!",
            "Great job! Correct!",
            "Wonderful! That's right!",
            "Outstanding! You remembered!"
        ]
        
        message = random.choice(congratulations)
        correct_name = self.current_student['full_name']
        student_id = f"{self.current_student['last_name']}_{self.current_student['first_name']}"
        
        # Update progress tracking
        self.correct_answers += 1
        self.total_attempts += 1
        self.session_index += 1
        
        # Track individual student performance
        self.track_student_performance(student_id, True, self.attempt_count)
        
        self.status_label.config(
            text=f"✅ {message} This is {correct_name}",
            fg='green'
        )
        
        # Text-to-speech feedback
        if self.tts_engine:
            threading.Thread(
                target=lambda: self.speak(f"{message} This is {correct_name}"),
                daemon=True
            ).start()
        
        self.name_entry.delete(0, tk.END)
        self.update_progress_display()
        
        # Auto-advance immediately to next student
        self.root.after(1500, self.new_student)  # Shorter delay for quicker flow
    
    def handle_incorrect_answer(self, guess):
        """Handle incorrect answer"""
        if self.attempt_count >= self.max_attempts:
            # Show correct answer after max attempts
            correct_name = self.current_student['full_name']
            student_id = f"{self.current_student['last_name']}_{self.current_student['first_name']}"
            
            # Update progress tracking (incorrect answer)
            self.total_attempts += 1
            self.session_index += 1
            
            # Track individual student performance (failed)
            self.track_student_performance(student_id, False, self.attempt_count)
            
            self.status_label.config(
                text=f"❌ The correct answer is: {correct_name}",
                fg='red'
            )
            
            if self.tts_engine:
                threading.Thread(
                    target=lambda: self.speak(f"The correct answer is {correct_name}"),
                    daemon=True
                ).start()
            
            self.update_progress_display()
            self.root.after(2000, self.new_student)
        else:
            remaining = self.max_attempts - self.attempt_count
            self.status_label.config(
                text=f"❌ Not quite right. {remaining} attempts remaining. Try again or ask for a hint!",
                fg='orange'
            )
            
            if self.tts_engine:
                threading.Thread(
                    target=lambda: self.speak("Not quite right. Try again or ask for a hint."),
                    daemon=True
                ).start()
    
    def give_hint(self):
        """Provide progressive hints for the current student"""
        if not self.current_student:
            messagebox.showinfo("Info", "Please select a new student first")
            return
        
        first_name = self.current_student['first_name']
        last_name = self.current_student['last_name']
        
        # Progressive hints based on hint_level (skip section info)
        if self.hint_level == 0:
            hint = f"First name starts with '{first_name[0]}'"
        elif self.hint_level == 1:
            hint = f"Last name starts with '{last_name[0]}'"
        elif self.hint_level == 2:
            if len(first_name) >= 3:
                hint = f"First name starts with '{first_name[:3]}'"
            else:
                hint = f"First name is '{first_name}'"
        elif self.hint_level == 3:
            if len(last_name) >= 3:
                hint = f"Last name starts with '{last_name[:3]}'"
            else:
                hint = f"Last name is '{last_name}'"
        elif self.hint_level == 4:
            hint = f"Last name is '{last_name}' - what's the first name?"
        else:
            # Final hint - give the full name
            hint = f"The answer is {first_name} {last_name}"
        
        self.hint_level += 1
        self.status_label.config(text=f"💡 Hint {self.hint_level}: {hint}", fg='blue')
        
        if self.tts_engine:
            threading.Thread(target=lambda: self.speak(f"Hint: {hint}"), daemon=True).start()
    
    def speak(self, text):
        """Text-to-speech output"""
        if self.tts_engine:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {e}")

def main():
    root = tk.Tk()
    app = StudentNameGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()