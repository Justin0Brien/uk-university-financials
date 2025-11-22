#!/bin/bash

# Installation script for UK University Financial Statements Finder

echo "======================================"
echo "Installing dependencies..."
echo "======================================"

# Check if pip is available
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null
then
    echo "Error: pip is not installed. Please install Python and pip first."
    exit 1
fi

# Use pip3 if available, otherwise use pip
PIP_CMD=$(command -v pip3 || command -v pip)

echo "Using: $PIP_CMD"

# Install dependencies
$PIP_CMD install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✓ Installation completed successfully!"
    echo "======================================"
    echo ""
    echo "You can now run the script with:"
    echo "  python3 university_financials.py"
    echo ""
    echo "or:"
    echo "  python university_financials.py"
else
    echo ""
    echo "======================================"
    echo "✗ Installation failed"
    echo "======================================"
    echo "Please check the error messages above."
    exit 1
fi
