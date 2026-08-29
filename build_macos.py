#!/usr/bin/env python3
"""
macOS Build script to create a .app bundle and .dmg installer 
for the Student Name Learning Game
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def install_build_requirements():
    """Install build requirements"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_build.txt"])
        print("✅ Build requirements installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install build requirements")
        return False
    return True

def create_app_icon():
    """Create a proper .icns icon for macOS"""
    try:
        from PIL import Image, ImageDraw
        
        # Create icon at multiple sizes for .icns
        sizes = [16, 32, 64, 128, 256, 512, 1024]
        images = []
        
        for size in sizes:
            # Create a nice gradient background
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw gradient background
            for y in range(size):
                # Blue to purple gradient
                r = int(52 + (156 - 52) * y / size)  # 52 to 156
                g = int(152 - 100 * y / size)        # 152 to 52
                b = int(219 - 43 * y / size)         # 219 to 176
                draw.line([(0, y), (size-1, y)], fill=(r, g, b, 255))
            
            # Draw a large "S" for Student
            font_size = int(size * 0.7)
            
            # Create text bounds
            text = "S"
            bbox = draw.textbbox((0, 0), text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center the text
            x = (size - text_width) // 2
            y = (size - text_height) // 2 - int(size * 0.1)
            
            # Draw white text with slight shadow
            draw.text((x+2, y+2), text, fill=(0, 0, 0, 100))  # Shadow
            draw.text((x, y), text, fill=(255, 255, 255, 255))  # White text
            
            images.append(img)
        
        # Save individual sizes
        icon_dir = Path("icon_temp")
        icon_dir.mkdir(exist_ok=True)
        
        for size, img in zip(sizes, images):
            img.save(icon_dir / f"icon_{size}x{size}.png")
        
        # Create .icns file using macOS iconutil
        subprocess.check_call([
            "iconutil", "-c", "icns", "-o", "app_icon.icns", str(icon_dir)
        ])
        
        # Clean up temp directory
        shutil.rmtree(icon_dir)
        print("✅ Created macOS app icon (app_icon.icns)")
        return True
        
    except Exception as e:
        print(f"⚠️ Could not create app icon: {e}")
        return False

def update_app_for_bundling():
    """Create a version of the app that works with PyInstaller bundling"""
    with open('student_name_game.py', 'r') as f:
        content = f.read()
    
    # Add resource path helper
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
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        
        # Insert the resource helper after the imports
        import_end = content.find('class StudentNameGame:')
        content = content[:import_end] + resource_helper + content[import_end:]
        
        # Save the modified version
        with open('student_name_game_bundled.py', 'w') as f:
            f.write(content)
        
        print("✅ Created bundled version of the app")
        return True
    else:
        print("⚠️ Could not find photos_dir line to replace")
        return False

def build_app():
    """Build the macOS .app bundle using PyInstaller"""
    print("🔨 Building macOS .app bundle...")
    
    # Collect all image files
    data_files = []
    for section in ['Section A', 'Section B']:
        section_path = Path(section)
        if section_path.exists():
            for img_file in section_path.glob('*.jpeg'):
                data_files.extend(["--add-data", f"{img_file}:{section}"])
            for img_file in section_path.glob('*.jpg'):
                data_files.extend(["--add-data", f"{img_file}:{section}"])
            for img_file in section_path.glob('*.png'):
                data_files.extend(["--add-data", f"{img_file}:{section}"])
    
    # Add the flashcards app as a bundled resource
    if os.path.exists('student_name_flashcards.py'):
        data_files.extend(["--add-data", "student_name_flashcards.py:."])
        print("✅ Including flashcards/study mode in bundle")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onedir",  # Create a directory bundle (required for .app)
        "--windowed",  # No console window
        "--name", "Student Name Learning Game",
        "--osx-bundle-identifier", "com.educator.studentnamegame",
        "student_name_game_bundled.py"
    ]
    
    # Add icon if available
    if os.path.exists('app_icon.icns'):
        cmd.extend(["--icon", "app_icon.icns"])
    
    # Add data files
    cmd.extend(data_files)
    
    # Add hidden imports
    hidden_imports = [
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.ttk',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk'
    ]
    
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])
    
    try:
        subprocess.check_call(cmd)
        
        app_path = "dist/Student Name Learning Game.app"
        if os.path.exists(app_path):
            print(f"✅ .app bundle created at: {app_path}")
            
            # Calculate size
            def get_size(start_path):
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(start_path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        total_size += os.path.getsize(fp)
                return total_size
            
            size_mb = get_size(app_path) / (1024 * 1024)
            print(f"📊 App bundle size: {size_mb:.1f} MB")
            return True
        else:
            print("❌ .app bundle not found after build")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False

def create_dmg():
    """Create a .dmg installer for macOS"""
    print("📦 Creating .dmg installer...")
    
    app_path = "dist/Student Name Learning Game.app"
    dmg_path = "Student_Name_Learning_Game.dmg"
    
    # Remove existing DMG
    if os.path.exists(dmg_path):
        os.remove(dmg_path)
    
    try:
        # Create DMG using hdiutil
        subprocess.check_call([
            "hdiutil", "create",
            "-volname", "Student Name Learning Game",
            "-srcfolder", "dist",
            "-ov", "-format", "UDZO",
            dmg_path
        ])
        
        if os.path.exists(dmg_path):
            size_mb = os.path.getsize(dmg_path) / (1024 * 1024)
            print(f"✅ DMG installer created: {dmg_path}")
            print(f"📊 DMG size: {size_mb:.1f} MB")
            return True
        else:
            print("❌ DMG file not created")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ DMG creation failed: {e}")
        return False

def create_readme():
    """Create installation instructions"""
    readme_content = '''# Student Name Learning Game - macOS Installation

## Quick Install
1. Double-click "Student_Name_Learning_Game.dmg"
2. Drag "Student Name Learning Game.app" to your Applications folder
3. Launch from Applications or Launchpad

## First Run
- You may see a security warning - this is normal for unsigned apps
- Right-click the app and select "Open" to bypass the warning

## Features
✅ Quiz Mode with scoring and progress tracking
✅ Review Mode with auto-advancing slideshow  
✅ Smart progressive hints
✅ Difficulty analysis with memory strategies
✅ Fuzzy name matching (recognizes variations)
✅ High score tracking

## Usage
1. Select Section A, Section B, or Both
2. Answer for each student photo
3. Use "Give Hint" if you need help
4. Check "📊 Analysis" to see challenging students
5. Try Review Mode for quick memorization

## System Requirements
- macOS 10.14 or later

## Troubleshooting
- If the app won't open: Right-click → Open → Open anyway
- If no photos appear: Ensure your image files were included in the build

Created with ❤️ for educators
'''
    
    with open('README_macOS.txt', 'w') as f:
        f.write(readme_content)
    print("✅ Created macOS README")

def main():
    """Main build process for macOS"""
    print("🍎 Student Name Learning Game - macOS Build Process")
    print("=" * 55)
    
    # Check if we're on macOS
    if not sys.platform == 'darwin':
        print("❌ This script is designed for macOS only")
        return 1
    
    # Check if we're in the right directory
    if not os.path.exists('student_name_game.py'):
        print("❌ Error: student_name_game.py not found in current directory")
        return 1
    
    # Check for image folders
    has_images = os.path.exists('Section A') or os.path.exists('Section B')
    if not has_images:
        print("⚠️ Warning: No 'Section A' or 'Section B' folders found")
        print("The app will be created but won't have any student photos")
    else:
        # Count images
        image_count = 0
        for section in ['Section A', 'Section B']:
            if os.path.exists(section):
                image_count += len(list(Path(section).glob('*.jpeg')))
                image_count += len(list(Path(section).glob('*.jpg')))
                image_count += len(list(Path(section).glob('*.png')))
        print(f"📸 Found {image_count} student photos to include")
    
    try:
        # Step 1: Install requirements
        if not install_build_requirements():
            return 1
        
        # Step 2: Create app icon
        create_app_icon()
        
        # Step 3: Prepare app for bundling
        if not update_app_for_bundling():
            return 1
        
        # Step 4: Build the .app bundle
        if not build_app():
            return 1
        
        # Step 5: Create DMG installer
        if not create_dmg():
            return 1
        
        # Step 6: Create documentation
        create_readme()
        
        print("\\n🎉 BUILD COMPLETE!")
        print("=" * 30)
        print("📁 Your distributable files:")
        print(f"   • Student_Name_Learning_Game.dmg (installer)")
        print(f"   • dist/Student Name Learning Game.app (app bundle)")
        print(f"   • README_macOS.txt (installation instructions)")
        
        print("\\n🚀 To distribute to your classroom:")
        print("   1. Copy the .dmg file to a USB drive")
        print("   2. On each Mac: Double-click .dmg → Drag app to Applications")
        print("   3. Launch from Applications folder")
        
        if has_images:
            print(f"\\n✨ Your {image_count} student photos are embedded in the app!")
        
        return 0
        
    except KeyboardInterrupt:
        print("\\n🛑 Build cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Build failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())