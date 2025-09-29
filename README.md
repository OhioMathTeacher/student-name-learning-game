# Student Name Learning Game 🎓📸

A simple, clean educational tool designed to help teachers learn student names through photo-based practice with text-to-speech feedback.

## 🌟 Features

### Core Functionality
- **Random Student Photos**: Displays student photos from organized folders
- **Text Input**: Type student names with immediate feedback
- **Text-to-Speech**: Provides audio feedback when you get names right
- **Simple Hints**: First letter hints when you're stuck
- **Streak Tracking**: Shows your current correct streak

### User Experience
- **Clean Interface**: Minimal, distraction-free design
- **Easy Photo Management**: Load different photo folders via File menu
- **Immediate Feedback**: Know right away if you got the name correct
- **Skip Option**: Move on when you're truly stuck

## 🚀 Quick Start

### Run the Application
```bash
# Clone the repository
git clone https://github.com/OhioMathTeacher/student-name-learning-game.git
cd student-name-learning-game

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
student-name-learning-game/
├── student_name_game.py          # Main application
├── student_name_game_simple.py   # Backup of simple version
├── requirements.txt              # Dependencies
├── README.md                     # This file
└── app_icon.png                  # Application icon
```

## 🎯 How to Use

### Basic Operation
1. **Load Photos**: Use File → Change Photo Folder to select your student photos
2. **View Photos**: Student photos appear one at a time
3. **Enter Names**: Type the student's first name in the text box
4. **Get Feedback**: The app tells you if you're correct and speaks the name
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
- pyttsx3 (Text-to-speech)

### System Requirements
- **Cross-platform**: Windows, macOS, or Linux
- **Display**: Minimum 800x600 resolution
- **Audio**: Speakers or headphones for text-to-speech feedback

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
- **No Text-to-Speech**: Audio drivers may need updating, but the app works fine without sound
- **App Slow to Start**: Large photo folders may take a moment to load initially

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