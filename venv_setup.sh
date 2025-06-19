#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "🔍 Checking for Python 3..."
if ! command_exists python3; then
    echo "🚀 Python3 not found. Installing..."
    sudo apt update && sudo apt install -y python3
fi

echo "🔍 Checking for python3-venv..."
if ! dpkg -s python3-venv >/dev/null 2>&1; then
    echo "🚀 python3-venv not found. Installing..."
    sudo apt install -y python3-venv
fi

VENV_DIR="venv"

echo "🔍 Checking for virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    echo "🚧 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "✅ Activating virtual environment..."
source "$VENV_DIR/bin/activate"

if [ ! -f "requirements.txt" ]; then
    echo "⚠️ No requirements.txt found!"
else
    echo "📦 Installing packages from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

echo "🎉 Setup complete. Virtual environment activated."
exec "$SHELL"
