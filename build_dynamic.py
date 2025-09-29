#!/usr/bin/env python3
"""
macOS Build script for the Dynamic Student Name Learning Game
Creates a .app bundle that can use any photo folder
"""

import os
import subprocess
import sys

def main():
    print("🚀 Building Dynamic Student Name Learning Game...")
    
    # Install build requirements
    print("📦 Installing build requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "pillow"])
        print("✅ Build requirements installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install build requirements")
        return False
    
    # Build the app
    print("🔨 Building macOS .app bundle...")
    
    # PyInstaller command for the dynamic version
    cmd = [
        "pyinstaller",
        "--onedir",  # Create a directory instead of a single file
        "--windowed",  # Don't show console
        "--name", "Student Name Learning Game",
        "--icon", "app_icon.png",  # Use existing icon
        "--clean",
        "--noconfirm",
        "student_name_game_simple.py"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ .app bundle created successfully!")
        
        # Show the result
        app_path = "dist/Student Name Learning Game.app"
        if os.path.exists(app_path):
            # Get app bundle size
            result = subprocess.run(['du', '-sh', app_path], capture_output=True, text=True)
            if result.returncode == 0:
                size = result.stdout.split()[0]
                print(f"✅ .app bundle created at: {app_path}")
                print(f"📊 App bundle size: {size}")
            
            print("\\n🎉 BUILD COMPLETE!")
            print("==============================")
            print(f"📁 Your dynamic app: {app_path}")
            print("\\n🚀 How to use:")
            print("   1. Double-click the app to launch")
            print("   2. Select a folder containing student photos")  
            print("   3. Photos should be named: LastName_FirstName.jpg")
            print("\\n✨ Much smaller app size - no photos embedded!")
            
        else:
            print("❌ App bundle not found after build")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        if e.stdout:
            print("stdout:", e.stdout)
        if e.stderr:
            print("stderr:", e.stderr)
        return False
    
    return True

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)