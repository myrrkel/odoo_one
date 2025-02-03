#!/bin/bash

# Set the path to the Python executable
PYTHON_EXE=python3

# Set the path to the Odoo One source code
SOURCE_CODE_DIR=.

# Set the path to the output directory
OUTPUT_DIR=dist

# Create the output directory if it doesn't exist
mkdir -p $OUTPUT_DIR

# Change into the source code directory
cd $SOURCE_CODE_DIR

# Run PyInstaller to build the executable
wine pyinstaller odoo_one_win.spec


# Clean up
cd ..