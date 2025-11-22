#!/bin/bash

# Activation helper script for the virtual environment

echo "======================================"
echo "Activating virtual environment..."
echo "======================================"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found."
    echo "Please run ./install.sh first to create it."
    exit 1
fi

# Activate the virtual environment
source venv/bin/activate

echo "✓ Virtual environment activated!"
echo ""
echo "You can now run:"
echo "  python university_financials.py"
echo ""
echo "To deactivate when done, type: deactivate"
echo ""

# Start a new shell with the venv activated
exec bash
