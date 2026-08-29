#!/usr/bin/env python3
"""
Build script to create a standalone executable of the Student Name Learning Game
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("✅ PyInstaller already installed")
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed successfully")

def create_spec_file():
    """Create PyInstaller spec file with custom configuration"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Get the directory containing this spec file
spec_dir = Path(SPECPATH)

# Collect all image files
image_files = []
for section in ['Section A', 'Section B']:
    section_path = spec_dir / section
    if section_path.exists():
        for img_file in section_path.glob('*.jpeg'):
            image_files.append((str(img_file), section))
        for img_file in section_path.glob('*.jpg'):
            image_files.append((str(img_file), section))
        for img_file in section_path.glob('*.png'):
            image_files.append((str(img_file), section))

a = Analysis(
    ['name_game.py'],
    pathex=[],
    binaries=[],
    datas=image_files,  # Include all image files
    hiddenimports=[
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.ttk',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='StudentNameLearningGame',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico' if os.path.exists('app_icon.ico') else None,
)
'''
    
    with open('student_name_game.spec', 'w') as f:
        f.write(spec_content)
    
    print("✅ Created PyInstaller spec file")

def update_app_for_bundling():
    """Update the app to work with bundled resources"""
    
    # Create a modified version that works with PyInstaller
    with open('name_game.py', 'r') as f:
        content = f.read()
    
    # Add resource path helper at the top
    resource_helper = '''
import sys
import os

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Development mode - use the directory of this script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)

'''
    
    # Replace the photos_dir initialization
    old_line = "self.photos_dir = os.path.dirname(os.path.abspath(__file__))"
    new_line = "self.photos_dir = get_resource_path('.')"
    
    content = content.replace(old_line, new_line)
    
    # Insert the resource helper after the imports
    import_end = content.find('class StudentNameGame:')
    content = content[:import_end] + resource_helper + content[import_end:]
    
    # Save the modified version
    with open('student_name_game_bundled.py', 'w') as f:
        f.write(content)
    
    print("✅ Created bundled version of the app")

def create_simple_icon():
    """Create a simple icon for the app"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple icon
        size = (64, 64)
        img = Image.new('RGBA', size, (52, 152, 219, 255))  # Blue background
        draw = ImageDraw.Draw(img)
        
        # Draw a simple "S" for Student
        try:
            # Try to use a built-in font
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
        except:
            font = ImageFont.load_default()
        
        # Draw white "S"
        draw.text((20, 8), "S", fill=(255, 255, 255, 255), font=font)
        
        # Save as ICO (Windows) and PNG (Linux)
        img.save('app_icon.png')
        if sys.platform.startswith('win'):
            img.save('app_icon.ico')
        
        print("✅ Created app icon")
    except ImportError:
        print("⚠️ PIL not available for icon creation - app will use default icon")

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building executable...")
    
    # Use the bundled version
    cmd = [
        "pyinstaller",
        "--onefile",  # Create a single executable file
        "--windowed",  # No console window
        "--name", "StudentNameLearningGame",
        "student_name_game_bundled.py"
    ]
    
    # Add icon if available
    if os.path.exists('app_icon.ico') and sys.platform.startswith('win'):
        cmd.extend(["--icon", "app_icon.ico"])
    elif os.path.exists('app_icon.png'):
        cmd.extend(["--icon", "app_icon.png"])
    
    # Add image files
    for section in ['Section A', 'Section B']:
        if os.path.exists(section):
            for img_file in Path(section).glob('*.jpeg'):
                cmd.extend(["--add-data", f"{img_file}{os.pathsep}{section}"])
            for img_file in Path(section).glob('*.jpg'):
                cmd.extend(["--add-data", f"{img_file}{os.pathsep}{section}"])
            for img_file in Path(section).glob('*.png'):
                cmd.extend(["--add-data", f"{img_file}{os.pathsep}{section}"])
    
    try:
        subprocess.check_call(cmd)
        print("✅ Executable built successfully!")
        print(f"📁 Check the 'dist' folder for your executable")
        
        # Show the location
        if sys.platform.startswith('win'):
            exe_path = "dist/StudentNameLearningGame.exe"
        else:
            exe_path = "dist/StudentNameLearningGame"
        
        if os.path.exists(exe_path):
            print(f"🎉 Executable created at: {os.path.abspath(exe_path)}")
            print(f"📊 File size: {os.path.getsize(exe_path) / (1024*1024):.1f} MB")
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False
    
    return True

def create_installer_script():
    """Create a simple installer script"""
    if sys.platform.startswith('win'):
        # Windows batch file
        installer_content = '''@echo off
echo Student Name Learning Game Installer
echo =====================================
echo.
echo Installing Student Name Learning Game...
echo.

if not exist "%USERPROFILE%\\StudentNameGame" (
    mkdir "%USERPROFILE%\\StudentNameGame"
)

copy "StudentNameLearningGame.exe" "%USERPROFILE%\\StudentNameGame\\"
copy "README.txt" "%USERPROFILE%\\StudentNameGame\\" 2>nul

echo.
echo Creating desktop shortcut...
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\\Desktop\\Student Name Learning Game.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%USERPROFILE%\\StudentNameGame\\StudentNameLearningGame.exe" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript CreateShortcut.vbs
del CreateShortcut.vbs

echo.
echo ✓ Installation complete!
echo ✓ Desktop shortcut created
echo ✓ You can now run "Student Name Learning Game" from your desktop
echo.
pause
'''
        with open('install.bat', 'w') as f:
            f.write(installer_content)
        print("✅ Created Windows installer (install.bat)")
    else:
        # Linux shell script
        installer_content = '''#!/bin/bash
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
Comment=Learn student names from photos
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
'''
        with open('install.sh', 'w') as f:
            f.write(installer_content)
        os.chmod('install.sh', 0o755)
        print("✅ Created Linux installer (install.sh)")

def create_readme():
    """Create a README file for the executable"""
    readme_content = '''# Student Name Learning Game

A comprehensive application to help teachers learn student names from their photos.

## Features

✅ **Quiz Mode**: Test your knowledge with scoring and progress tracking
✅ **Review Mode**: Auto-advancing slideshow with speed control and pause/resume
✅ **Smart Hints**: Progressive hints that get more specific

## How to Use

1. **Select Section**: Choose Section A, Section B, or Both
2. **Take Quiz**: Answer for each student - get scored on first-try accuracy
3. **Check Analysis**: Click "📊 Analysis" to see which students are challenging
4. **Study Strategies**: Get personalized memory tips for difficult faces
5. **Practice Review**: Use Review Mode to study at your own pace
6. **Improve Scores**: Take another quiz and watch your success rate grow!

## System Requirements

- Windows 10+ / Linux (Ubuntu 18.04+)

## Installation

Run the installer script (install.bat on Windows, install.sh on Linux)
or simply double-click the executable to run directly.

## Troubleshooting

- If no student photos appear, ensure image files are in the correct folders

## Version 1.0 - Created with ❤️ for educators
'''
    
    with open('README.txt', 'w') as f:
        f.write(readme_content)
    print("✅ Created README file")

def main():
    """Main build process"""
    print("🚀 Student Name Learning Game - Build Process")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('name_game.py'):
        print("❌ Error: name_game.py not found in current directory")
        print("Please run this script from the same directory as name_game.py")
        return
    
    # Check for image folders
    if not (os.path.exists('Section A') or os.path.exists('Section B')):
        print("⚠️ Warning: No 'Section A' or 'Section B' folders found")
        print("The executable will be created but won't have any student photos")
    
    try:
        # Step 1: Install PyInstaller
        install_pyinstaller()
        
        # Step 2: Create app icon
        create_simple_icon()
        
        # Step 3: Update app for bundling
        update_app_for_bundling()
        
        # Step 4: Build executable
        if build_executable():
            # Step 5: Create installer and README
            create_installer_script()
            create_readme()
            
            print("\n🎉 BUILD COMPLETE!")
            print("=" * 30)
            print("📁 Your files:")
            print("   • dist/StudentNameLearningGame.exe (or StudentNameLearningGame on Linux)")
            print("   • install.bat (Windows) or install.sh (Linux)")
            print("   • README.txt")
            print("\n🚀 To distribute:")
            print("   1. Copy the executable and installer to target computer")
            print("   2. Run the installer, or double-click the executable")
            print("\n✨ Your students' photos are embedded in the executable!")
        
    except Exception as e:
        print(f"❌ Build failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())