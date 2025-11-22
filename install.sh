#!/bin/bash

# Installation script for UK University Financial Statements Finder

echo "======================================"
echo "UK University Financials Setup"
echo "======================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null
then
    echo "Error: Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    
    if [ $? -eq 0 ]; then
        echo "✓ Virtual environment created"
    else
        echo "✗ Failed to create virtual environment"
        exit 1
    fi
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✓ Installation completed successfully!"
    echo "======================================"
    echo ""
    echo "To use the virtual environment:"
    echo ""
    echo "  1. Activate it:"
    echo "     source venv/bin/activate"
    echo ""
    echo "  2. Run the script:"
    echo "     python university_financials.py"
    echo ""
    echo "  3. Deactivate when done:"
    echo "     deactivate"
    echo ""
    echo "Tip: You can also use ./activate.sh for easier activation"
    echo "======================================"
else
    echo ""
    echo "======================================"
    echo "✗ Installation failed"
    echo "======================================"
    echo "Please check the error messages above."
    exit 1
fi
