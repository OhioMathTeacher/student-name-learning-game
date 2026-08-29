# Student Name Learning Game 🎓📸

A simple, clean educational tool designed to help teachers learn student names through photo-based practice.

## 🌟 Features

### Core Functionality
- **Random Student Photos**: Displays student photos from organized folders
- **Text Input**: Type student names with immediate feedback
- **Simple Hints**: First letter hints when you're stuck
- **Streak Tracking**: Shows your current correct streak

### User Experience
- **Clean Interface**: Minimal, distraction-free design
- **Easy Photo Management**: Load different photo folders via File menu
- **Immediate Feedback**: Know right away if you got the name correct
- **Skip Option**: Move on when you're truly stuck

## 🚀 Quick Start

### Download Pre-Built Executables (Easiest!)

**No Python installation required!** Download and run immediately:

**📥 Direct Downloads:**

| Platform | Download Link | Size |
|----------|--------------|------|
| 🪟 **Windows** | [StudentNameGame.exe](https://github.com/OhioMathTeacher/student-name-learning-game/releases/download/v1.0.0/StudentNameGame.exe) | 17 MB |
| 🍎 **macOS** | [StudentNameGame-macOS.dmg](https://github.com/OhioMathTeacher/student-name-learning-game/releases/download/v1.0.0/StudentNameGame-macOS.dmg) | 16 MB |
| 🐧 **Linux** | [StudentNameGame-Linux.AppImage](https://github.com/OhioMathTeacher/student-name-learning-game/releases/download/v1.0.0/StudentNameGame-Linux.AppImage) | 28 MB |

**How to run:**
- **Windows**: Click to download the .exe file, then double-click to run
- **macOS**: Download the .dmg file, open it, and drag to Applications
- **Linux**: Download the AppImage, make it executable (`chmod +x StudentNameGame-Linux.AppImage`), then run

**All Releases:**
- [View All Releases](https://github.com/OhioMathTeacher/student-name-learning-game/releases)

### Run from Source

If you prefer to run from source code:

```bash
# Clone the repository
git clone https://github.com/OhioMathTeacher/student-name-learning-game.git
cd student-name-learning-game

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the quiz mode
python student_name_game.py

# Or run the study/flashcard mode
python student_name_flashcards.py
```

## 📁 Project Structure

```
student-name-learning-game/
├── student_name_game.py             # Quiz mode application
├── student_name_flashcards.py       # Study/flashcard mode
├── build_simple.py                  # Local build script for macOS
├── requirements.txt                 # Runtime dependencies
├── requirements_build.txt           # Build dependencies
├── .github/workflows/               # CI/CD automation
│   └── build-executables.yml        # Auto-build for Win/Mac/Linux
├── README.md                        # This file
└── app_icon.png                     # Application icon
```

## 🎮 Two Modes

### Quiz Mode (`student_name_game.py`)
Test yourself! See a student photo and type their name. Track your streak and progress.

### Study Mode (`student_name_flashcards.py`)
Learn the names! View photos with names displayed. Auto-advance through students at your own pace.

**Switch between modes**: Use File → Switch to Quiz/Study Mode in either app!

## 🎯 How to Use

### Basic Operation
1. **Load Photos**: Use File → Change Photo Folder to select your student photos
2. **View Photos**: Student photos appear one at a time
3. **Enter Names**: Type the student's first name in the text box
4. **Get Feedback**: The app tells you right away whether you got the name right
5. **Use Hints**: Click "Get Hint" for the first letter of the name
6. **Track Progress**: Your current streak is displayed at the top

### Photo Organization
- Organize photos in folders (e.g., "Section A", "Section B")
- Name photos as `LastName_FirstName.jpg` or `FirstName_LastName.jpg`
- The app will extract the first name automatically
- Supported formats: JPG, JPEG, PNG, GIF, BMP

## 🛠️ Technical Requirements

### Dependencies
- Python 3.8+
- tkinter (GUI framework - usually included with Python)
- Pillow (Image processing)

### System Requirements
- **Cross-platform**: Windows, macOS, or Linux
- **Display**: Minimum 800x600 resolution

## 🎨 Customization

### Adding New Students
1. Create a folder with your student photos
2. Name photos as `LastName_FirstName.jpg` or similar
3. Use File → Change Photo Folder to select the new folder
4. The app automatically loads all images from the selected folder

### Photo Formats
- Supported: JPG, JPEG, PNG, GIF, BMP
- Photos are automatically resized to fit the display
- No specific resolution requirements

## 🔒 Privacy & Security

This tool is designed for educational use with student photos. Please:
- ✅ Follow your institution's privacy policies
- ✅ Keep student photos secure
- ✅ Only use photos you have permission to use
- ❌ Don't share student photos without proper authorization

## 🐛 Troubleshooting

### Common Issues
- **Photos Not Loading**: Check that photos are in supported formats (JPG, PNG, etc.)
- **App Slow to Start**: Large photo folders may take a moment to load initially

## 🏗️ Building Executables

### Automated Builds via GitHub Actions

Executables are automatically built on every push to `main`:
- **Windows** `.exe` 
- **macOS** `.app` and `.dmg`
- **Linux** AppImage

**To download the latest builds:**
1. Go to the [Actions tab](https://github.com/OhioMathTeacher/student-name-learning-game/actions)
2. Click on the latest successful "Build Cross-Platform Executables" workflow
3. Scroll down to "Artifacts" section
4. Download:
   - `windows-executable` for Windows .exe
   - `macos-dmg` for macOS installer
   - `linux-appimage` for Linux AppImage

*Note: Artifacts are kept for 30 days. For permanent downloads, create a release (see below).*

### Creating a Release with Downloadable Executables

To create an official release with permanent download links:

```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0

# Or use GitHub CLI
gh release create v1.0.0 --title "Version 1.0.0" --notes "Release notes here"
```

Once you push a tag or create a release on GitHub, the workflow will automatically:
1. Build executables for all platforms
2. Attach them to the release
3. Make them available on the [Releases page](https://github.com/OhioMathTeacher/student-name-learning-game/releases)

### Manual Local Build (macOS only)

```bash
# Activate your virtual environment first
source .venv/bin/activate

# Run the build script
python build_simple.py

# Find your .app in dist/
open dist/
```

The build script creates a complete macOS `.app` bundle with both quiz and study modes included.

## 🤝 Contributing

This is a simple educational tool. Feel free to:
1. Fork the repository
2. Make improvements
3. Submit pull requests
4. Report issues or suggest features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**🎓 Happy Teaching!** This simple tool helps you learn student names quickly and efficiently.