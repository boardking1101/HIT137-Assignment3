"""Polymorphic transformations used to scramble puzzle tiles."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from puzzle_model import PuzzleModel, Tile


class Transformation(ABC):
    """Base class for every transformation applied during scrambling."""

    @abstractmethod
    def apply(self, puzzle: "PuzzleModel") -> None:
        """Apply this transformation to a puzzle."""


class SwapTransformation(Transformation):
    """Exchange the positions of two unique tile objects."""

    def __init__(self, first_tile: "Tile", second_tile: "Tile") -> None:
        self.first_tile = first_tile
        self.second_tile = second_tile

    def apply(self, puzzle: "PuzzleModel") -> None:
        puzzle.swap_tile_objects(self.first_tile, self.second_tile)


class RotateTransformation(Transformation):
    """Rotate one tile clockwise by 90, 180, or 270 degrees."""

    def __init__(self, tile: "Tile", angle: int) -> None:
        self.tile = tile
        self.angle = angle

    def apply(self, puzzle: "PuzzleModel") -> None:
        self.tile.rotate(self.angle)


class FlipTransformation(Transformation):
    """Flip one tile horizontally or vertically."""

    def __init__(self, tile: "Tile", direction: str) -> None:
        self.tile = tile
        self.direction = direction

    def apply(self, puzzle: "PuzzleModel") -> None:
        if self.direction == "horizontal":
            self.tile.flip_horizontal()
        else:
            self.tile.flip_vertical()
