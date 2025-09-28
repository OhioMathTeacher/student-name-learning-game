#!/bin/bash
echo "Student Name Learning Game Installer"
echo "====================================="
echo

echo "Installing Student Name Learning Game..."
echo

# Create application directory
mkdir -p "$HOME/StudentNameGame"

# Copy executable
cp "StudentNameLearningGame" "$HOME/StudentNameGame/"
chmod +x "$HOME/StudentNameGame/StudentNameLearningGame"

# Create desktop entry
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/student-name-game.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Student Name Learning Game
Comment=Learn student names with photos and speech recognition
Exec=$HOME/StudentNameGame/StudentNameLearningGame
Icon=application-x-executable
Terminal=false
Categories=Education;
EOF

echo
echo "✓ Installation complete!"
echo "✓ Application installed to ~/StudentNameGame/"
echo "✓ Desktop entry created"
echo "✓ You can now find 'Student Name Learning Game' in your applications menu"
echo

read -p "Press Enter to continue..."
