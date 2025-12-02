import sys
from pathlib import Path
import tkinter as tk

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from gui import iniciar_aplicacion


def main():
    """Main entry point for the application"""
    try:
        iniciar_aplicacion()
        
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()