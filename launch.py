"""Start Name Game on whatever computer this drive is plugged into.

This replaced three near-identical launchers, one per platform. They said the
same thing in three dialects and drifted apart anyway: the Linux one learned to
check tkinter before Pillow, the Windows one after, and the Mac one grew a
Homebrew path the others never got. The differences that actually exist --
where Python lives, what to say when it is missing, how to install Pillow --
are conditionals here, where they can be read side by side.

The two stubs beside this file exist only because no single filename is
double-clickable everywhere: Finder will not run a `.bat`, and Windows will not
run a `.command`. Each finds a Python and hands straight over to this, so
neither carries logic worth keeping in step.
"""

import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WINDOWS = os.name == "nt"
MAC = sys.platform == "darwin"
SETTINGS = os.path.join(os.path.expanduser("~"), ".student_name_game")


def pause(*lines):
    """Say why we stopped, and stay on screen long enough to be read.

    A launcher that exits silently is indistinguishable from one that did
    nothing, and on Windows the console window closes with it.
    """
    print()
    for line in lines:
        print("  " + line)
    print()
    try:
        input("  Press Enter to close. ")
    except (EOFError, KeyboardInterrupt):
        pass


def installed(module):
    try:
        __import__(module)
        return True
    except ImportError:
        return False


def python_help():
    """Where this computer's Python should come from, if it needs replacing."""
    if MAC:
        return ["Install Python from https://www.python.org/downloads/ --",
                "not the one Apple ships, which cannot open windows."]
    if WINDOWS:
        return ["Reinstall Python from https://www.python.org/downloads/",
                "and keep the default options."]
    return ["Fedora:        sudo dnf install python3-tkinter python3-pillow-tk",
            "Debian/Ubuntu: sudo apt install python3-tk python3-pil.imagetk"]


def restore_settings():
    """Bring hints, scores and the class list over, once, per computer.

    Never overwrites: a machine that already has hints on it has better ones
    than the copy travelling on the drive.
    """
    if os.path.isdir(SETTINGS):
        return
    spare = os.path.join(HERE, "app-data")
    if not os.path.isdir(spare):
        return
    print("  Restoring your saved hints and scores...")
    os.makedirs(SETTINGS, exist_ok=True)
    for name in os.listdir(spare):
        if name.endswith(".json"):
            try:
                shutil.copy2(os.path.join(spare, name), os.path.join(SETTINGS, name))
            except OSError:
                pass


def ensure_pillow():
    """Pillow, and on Linux specifically the ImageTk half of it.

    Fedora splits ImageTk into its own package, so `import PIL` succeeding
    proves nothing -- the old launchers checked exactly that and then died one
    line into the app. Ask for what is actually used.
    """
    if installed("PIL.ImageTk"):
        return True

    print("  Installing Pillow (one time, needs internet)...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "Pillow"],
                       check=True)
    except (OSError, subprocess.CalledProcessError):
        pass

    if installed("PIL.ImageTk"):
        return True
    pause("Pillow is missing and could not be installed automatically.",
          *python_help())
    return False


def main():
    os.chdir(HERE)
    sys.path.insert(0, HERE)

    prep = "--prep" in sys.argv[1:]
    title = "Roster Prep" if prep else "Name Game"
    print()
    print("  " + title + " - starting up")
    print("  " + "-" * (len(title) + 15))
    print()
    print("  Using: " + sys.executable)

    if not installed("tkinter"):
        pause("This Python cannot open windows (no tkinter).", *python_help())
        return 1

    restore_settings()
    if not ensure_pillow():
        return 1

    print("  Starting " + title + "...")
    print()
    module = __import__("roster_prep" if prep else "name_game")
    module.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
