#!/usr/bin/env python3
"""
Simple macOS Build script for Student Name Learning Game
Creates a .app bundle with both quiz and study modes
"""

import os
import subprocess
import sys
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if needed"""
    try:
        import PyInstaller
        print("✅ PyInstaller already installed")
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed")

def build_app():
    """Build the macOS .app bundle"""
    print("🔨 Building Student Name Learning Game.app...")
    
    # PyInstaller command - start with quiz mode as main entry point
    cmd = [
        "pyinstaller",
        "--onedir",
        "--windowed",
        "--name", "Student Name Learning Game",
        "--osx-bundle-identifier", "com.educator.studentnamegame",
        "--clean",
        "--noconfirm",
        # Add both Python files
        "--add-data", "student_name_flashcards.py:.",
        # Add icon if it exists
    ]
    
    if os.path.exists('app_icon.png'):
        cmd.extend(["--icon", "app_icon.png"])
    
    # Hidden imports for tkinter and PIL
    hidden_imports = [
        'tkinter',
        'tkinter.ttk',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'pyttsx3',
    ]
    
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])
    
    # Main script
    cmd.append("student_name_game.py")
    
    try:
        subprocess.check_call(cmd)
        
        app_path = "dist/Student Name Learning Game.app"
        if os.path.exists(app_path):
            # Calculate size
            def get_size(start_path):
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(start_path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if os.path.exists(fp):
                            total_size += os.path.getsize(fp)
                return total_size
            
            size_mb = get_size(app_path) / (1024 * 1024)
            print(f"\\n✅ .app bundle created successfully!")
            print(f"📁 Location: {app_path}")
            print(f"📊 Size: {size_mb:.1f} MB")
            print(f"\\n🎯 Your app includes:")
            print(f"   • Quiz Mode (main app)")
            print(f"   • Study Mode (via File → Switch to Study Mode)")
            print(f"   • Shared folder persistence")
            print(f"\\n🚀 To use:")
            print(f"   1. Double-click 'Student Name Learning Game.app'")
            print(f"   2. Select your photo folder")
            print(f"   3. Switch between modes via File menu")
            return True
        else:
            print("❌ .app bundle not found after build")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False

def main():
    """Main build process"""
    print("🍎 Student Name Learning Game - Simple Build")
    print("=" * 50)
    
    if not sys.platform == 'darwin':
        print("❌ This script is for macOS only")
        return 1
    
    if not os.path.exists('student_name_game.py'):
        print("❌ student_name_game.py not found")
        return 1
    
    if not os.path.exists('student_name_flashcards.py'):
        print("❌ student_name_flashcards.py not found")
        return 1
    
    try:
        install_pyinstaller()
        if build_app():
            print("\\n🎉 BUILD COMPLETE!")
            return 0
        else:
            return 1
    except KeyboardInterrupt:
        print("\\n🛑 Build cancelled")
        return 1
    except Exception as e:
        print(f"❌ Build failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
