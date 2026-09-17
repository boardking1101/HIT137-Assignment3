"""Application entry point for the HIT137 image puzzle."""

import tkinter as tk

from puzzle_gui import PuzzleApp


def main() -> None:
    root = tk.Tk()
    PuzzleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
