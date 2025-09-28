#!/bin/bash
# Setup script for Student Name Learning Game

echo "Setting up Student Name Learning Game..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 first."
    exit 1
fi

# Check if .venv already exists
if [ -d ".venv" ]; then
    echo "Using existing .venv virtual environment..."
    source .venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# Install required packages
echo "Installing required packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "To run the application:"
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Run the game: python3 student_name_game.py"
echo ""
echo "Note: Make sure your microphone is working for speech recognition features."
echo "The application will work without speech features if the libraries aren't available."