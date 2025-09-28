# Student Name Learning Game 🎓📸

A comprehensive educational tool designed to help teachers learn student names through interactive photo-based quizzes with voice recognition, progressive hints, and intelligent difficulty tracking.

## 🌟 Features

### Core Functionality
- **Random Student Photos**: Displays student photos from organized folders
- **Voice Recognition**: Speak student names aloud for hands-free learning
- **Text-to-Speech**: Provides audio feedback and spoken hints
- **Progressive Hints**: Gradual revelation system (first letter → syllables → full name)
- **Fuzzy Matching**: Intelligent name matching that handles variations and pronunciations

### Advanced Learning Features
- **Session Management**: Organized learning sessions with randomization
- **Review Mode**: Speed-controlled review of difficult students
- **Performance Tracking**: Tracks accuracy, attempts, and learning progress
- **Difficulty Analysis**: Identifies challenging names and suggests memory strategies
- **Smart Hints**: Context-aware hints based on student performance

### User Experience
- **Modern UI**: Clean, professional interface with intuitive controls
- **Responsive Design**: Automatically sized photos and adaptive layout
- **Visual Feedback**: Clear success/failure indicators and progress tracking
- **Pause & Resume**: Flexible session control for busy teaching schedules

## 🚀 Quick Start

### Option 1: Run the Executable (Recommended)
1. Download the latest release from the `dist/` folder
2. Double-click `StudentNameLearningGame` (Linux) or run `./install.sh`
3. The app launches immediately - no installation required!

### Option 2: Run from Source
```bash
# Clone the repository
git clone <your-repo-url>
cd TCE318P_Photos

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python student_name_game.py
```

## 📁 Project Structure

```
TCE318P_Photos/
├── student_name_game.py          # Main application
├── build_executable.py           # Executable build script
├── requirements.txt              # Runtime dependencies
├── requirements_build.txt        # Build dependencies
├── Section A/                    # Student photos folder
│   ├── Brown_Emma.jpeg
│   ├── DeVincentis_Celeste.jpeg
│   └── ...
├── Section B/                    # Additional student photos
│   ├── Ashkettle_Julia.jpeg
│   ├── Burzynski_Ethan.jpeg
│   └── ...
├── dist/                         # Built executable
│   ├── StudentNameLearningGame
│   ├── install.sh
│   └── README.txt
└── build/                        # Build artifacts
```

## 🎯 How to Use

### Basic Operation
1. **Start a Session**: Click "Start New Session" to begin
2. **View Photos**: Student photos appear automatically
3. **Enter Names**: Type or speak the student's name
4. **Get Hints**: Click "Give me a hint!" if you're stuck
5. **Track Progress**: Monitor your accuracy and learning curve

### Voice Recognition
- Click "🎤 Voice Input" to activate microphone
- Speak clearly and wait for recognition
- The recognized text appears in the input field
- Submit with Enter or click "Submit"

### Review Mode
- Access previously seen students for reinforcement
- Adjust speed from 1-10 seconds per photo
- Pause anytime to focus on difficult names
- Skip or return to specific students

### Performance Analytics
- View session statistics and overall progress
- Identify students requiring more practice
- Get memory strategy suggestions for difficult names
- Track improvement over multiple sessions

## 🛠️ Technical Requirements

### Runtime Dependencies
- Python 3.8+
- tkinter (GUI framework)
- Pillow 9.0.0+ (Image processing)
- speech_recognition 3.8.1+ (Voice input)
- pyttsx3 2.90+ (Text-to-speech)
- pyaudio 0.2.11+ (Microphone access)

### System Requirements
- **Linux**: Ubuntu/Debian with ALSA audio support
- **Audio**: Microphone for voice recognition
- **Display**: Minimum 1024x768 resolution

### Build Dependencies (for creating executables)
- PyInstaller 5.0.0+
- All runtime dependencies

## 🔧 Building Your Own Executable

```bash
# Install build dependencies
pip install -r requirements_build.txt

# Run the automated build script
python build_executable.py

# Find your executable in the dist/ folder
```

The build process:
- Creates a standalone executable with embedded photos
- Generates installation scripts
- Bundles all dependencies (no Python installation required)
- Results in a ~52MB portable application

## 🎨 Customization

### Adding New Students
1. Add photos to `Section A/` or `Section B/` folders
2. Use format: `LastName_FirstName.jpeg`
3. Photos are automatically resized and cropped to squares
4. Restart the application to load new photos

### Modifying Difficulty
Edit these variables in `student_name_game.py`:
- `SESSION_SIZE`: Number of students per session (default: 10)
- `REVIEW_SPEED`: Default review speed in seconds (default: 3)
- Voice recognition timeout and phrase time limits

### UI Customization
The app uses a modern color scheme:
- Primary: #2C3E50 (dark blue-gray)
- Secondary: #3498DB (bright blue)  
- Success: #27AE60 (green)
- Warning: #F39C12 (orange)
- Error: #E74C3C (red)

## 🔒 Privacy & Security

This is a **private repository** containing student photos. Please:
- ✅ Keep repository private at all times
- ✅ Only share with trusted educational colleagues
- ✅ Follow your institution's privacy policies
- ✅ Use secure authentication for GitHub access
- ❌ Never make this repository public
- ❌ Don't share executables containing student photos publicly

## 🐛 Troubleshooting

### Audio Issues
- **Linux**: Install `sudo apt install portaudio19-dev python3-dev`
- **ALSA Warnings**: Harmless system messages, functionality unaffected
- **No Microphone**: Voice input gracefully disabled, typing still works

### Photo Issues
- **Photos Not Loading**: Check file permissions and formats (JPEG recommended)
- **Sizing Problems**: Photos automatically cropped to squares and resized
- **New Photos Not Appearing**: Restart application after adding files

### Performance Issues  
- **Slow Loading**: Large photo files may cause delays during startup
- **Memory Usage**: ~50MB+ depending on number of photos loaded
- **Voice Recognition Lag**: Normal 1-2 second processing time

## 🤝 Contributing

Since this is a private educational tool:
1. Make changes in feature branches
2. Test thoroughly with sample data
3. Document any new features or changes
4. Respect student privacy in all modifications

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Python and tkinter for cross-platform compatibility
- Uses Google Speech Recognition for voice input
- Powered by open-source libraries and educational best practices
- Designed specifically for classroom environments

---

**🎓 Happy Teaching!** This tool is designed to make learning student names enjoyable and efficient. Your students will appreciate the personal connection that comes with you knowing their names quickly and confidently.