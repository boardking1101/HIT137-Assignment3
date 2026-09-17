# HIT137 Assignment 3 - Image Puzzle

## Setup

```powershell
python -m pip install -r requirements.txt
python main.py
```

## Controls

- Select `3 x 3`, `4 x 4`, or `5 x 5` before loading an image.
- Load a JPG, PNG, or BMP image.
- Left-click one tile and then another to swap them.
- Left-click the selected tile again to deselect it.
- Right-click a tile to rotate it 90 degrees clockwise.
- Shift + left-click a tile to flip it horizontally.
- Hint can be used at most three times per image.
- Solve restores the image and clears the move counter.

## Design

The project separates the Tkinter interface from the puzzle model. Random scramble
operations implement a common `Transformation` interface through swap, rotate, and
flip subclasses. Scrambling generates all operations before applying them, scales the
operation count with the selected grid, and never targets the same tile twice.
