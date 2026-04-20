"""Launcher for Clipboard Flash — run with pythonw for no console window."""
import os
import sys

# Ensure we run from the script's directory so relative imports work
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main
main()
