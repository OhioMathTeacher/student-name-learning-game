# Name Game 🎓📸

A simple, clean tool for learning your students' names from their photos.

One window with two screens: **Study** walks the roster with each name shown and
lets you write a memory hint per face; **Quiz** hides the name and asks for it,
using your hint when you need one.

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

# Run it
python name_game.py
```

## 📁 Project Structure

```
student-name-learning-game/
├── name_game.py                     # Name Game: one window, Study + Quiz
├── roster_prep.py                   # Roster Prep: saved rosters -> photo folders
├── prepare.py                       # reads a saved roster page, copies its photos
├── theme.py                         # palette, type scale, photo box, hints
├── roster.py                        # folder -> students, last-folder memory
├── build_simple.py                  # Local build script for macOS
├── requirements.txt                 # Runtime dependencies
├── requirements_build.txt           # Build dependencies
├── .github/workflows/               # CI/CD automation
│   └── build-executables.yml        # Auto-build for Win/Mac/Linux
├── README.md                        # This file
└── app_icon.png                     # Application icon
```

## 🎮 Two Modes

### Quiz (File → Quiz)
Test yourself! See a student photo and type their name. Track your streak and progress.

### Study (File → Study)
Learn the names! View photos with names displayed. Auto-advance through students at your own pace.

**Switch between them**: File → Study / Quiz, or Ctrl+Tab. Same window, no restart.

## 📸 Getting your photos in

Two apps ship together. **Roster Prep** builds the photo folders; **Name Game**
practises from them. Roster Prep is a start-of-term job you do once.

1. Open **Roster Prep** and click *Open my photo rosters*. Your registrar's
   photo roster opens in the browser, where you are already signed in — there
   is no API behind it and nothing to log into from the app.
2. For each section: press **Ctrl+S** (**⌘S** on a Mac) and choose
   **“Web Page, complete”** as the format. That saves the photos alongside the
   page; *HTML only* does not. Save every section into one folder.
3. Back in Roster Prep, click *Choose the folder…* and point it at that folder.
   Every section under it is found at once.
4. Check the plan. Each row shows a **Course** and a **Location**, both
   editable, and an example of the filename they produce. **Two sections of one
   course must differ here** — the roster page never says which campus it is,
   so both arrive labelled `318P` and would merge into one class. Naming the
   saved page after its campus (`318p-hamilton-FA26.html`), or filing it under
   a folder called `Hamilton`, gets this right automatically.
5. Prepare them, then take the offer to delete the saved pages. Those pages
   carry internal student ID numbers, not just names and faces.

Every photo lands in **one folder**, named for the student and the class:

    student-photos/Naomi_Abernathy_318P_Hamilton.jpg
    student-photos/Challis_Alfred_318P_Oxford.jpg
    student-photos/Lina_Backus_284_Oxford.jpg

    FirstName_LastName_Course_Location.jpg

That filename is all Name Game needs, so there is no folder structure to get
right and nothing to point at wrongly. Every class shares the folder, and
picking one in *File → Class* filters what is already loaded. The folder sits
outside the app — on a thumbdrive, or under Pictures — so the app can be
rebuilt, moved or replaced without going near a student photo.

Nothing is uploaded. Neither app touches the network except to open your
roster in your own browser.

## 🎯 How to Use

### Basic Operation
1. **Load Photos**: File → Change photo folder, then File → Class to pick one
   class or *All students*
2. **View Photos**: Student photos appear one at a time
3. **Enter Names**: Type the student's first name in the text box
4. **Get Feedback**: The app tells you right away whether you got the name right
5. **Use Hints**: Click "Get Hint" for the first letter of the name
6. **Track Progress**: Your current streak is displayed at the top

### Photo Organization
- One folder holds every class
- Name photos `FirstName_LastName_Course_Location.jpg` — underscores separate
  the four fields, so spaces are fine inside a name (`Mary Jane_Smith_284_Oxford.jpg`)
- Leave the location off if there is only one section of a course
  (`Mary Jane_Smith_284.jpg`); a photo named `Alex.jpg` still shows, just with
  no class attached
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
1. Drop the photo into the folder the other photos are in
2. Name it `FirstName_LastName_Course_Location.jpg` to file it under a class
3. File → Class → *Look again* is not needed — reopen the folder, or restart

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