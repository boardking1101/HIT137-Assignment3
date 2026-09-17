"""Core image-puzzle model with no dependency on the Tkinter interface."""

from __future__ import annotations

import random
from pathlib import Path

import cv2
import numpy as np

from transformations import (
    FlipTransformation,
    RotateTransformation,
    SwapTransformation,
    Transformation,
)


class PuzzleError(Exception):
    """Raised when an image cannot be loaded or prepared safely."""


class Tile:
    """Encapsulates a tile's identity, pixels, and orientation."""

    _IDENTITY = np.eye(2, dtype=np.int8)
    _ROTATE_CLOCKWISE = np.array([[0, -1], [1, 0]], dtype=np.int8)
    _FLIP_HORIZONTAL = np.array([[-1, 0], [0, 1]], dtype=np.int8)
    _FLIP_VERTICAL = np.array([[1, 0], [0, -1]], dtype=np.int8)

    def __init__(self, tile_id: int, image: np.ndarray) -> None:
        self._tile_id = tile_id
        self._original_image = image.copy()
        self._current_image = image.copy()
        self._orientation = self._IDENTITY.copy()

    @property
    def tile_id(self) -> int:
        return self._tile_id

    @property
    def image(self) -> np.ndarray:
        return self._current_image

    def rotate_clockwise(self) -> None:
        self._current_image = cv2.rotate(
            self._current_image,
            cv2.ROTATE_90_CLOCKWISE,
        )
        self._orientation = self._ROTATE_CLOCKWISE @ self._orientation

    def rotate(self, angle: int) -> None:
        if angle not in (90, 180, 270):
            raise ValueError("Rotation angle must be 90, 180, or 270 degrees.")
        for _ in range(angle // 90):
            self.rotate_clockwise()

    def flip_horizontal(self) -> None:
        self._current_image = cv2.flip(self._current_image, 1)
        self._orientation = self._FLIP_HORIZONTAL @ self._orientation

    def flip_vertical(self) -> None:
        self._current_image = cv2.flip(self._current_image, 0)
        self._orientation = self._FLIP_VERTICAL @ self._orientation

    def reset_orientation(self) -> None:
        self._current_image = self._original_image.copy()
        self._orientation = self._IDENTITY.copy()

    def orientation_is_correct(self) -> bool:
        return bool(np.array_equal(self._orientation, self._IDENTITY))


class PuzzleModel:
    """Owns puzzle state and implements all game rules."""

    TRANSFORM_COUNTS = {3: 6, 4: 12, 5: 20}
    SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}

    def __init__(self, maximum_image_size: int = 500) -> None:
        self.maximum_image_size = maximum_image_size
        self.grid_size = 3
        self.image_size = 0
        self.original_image: np.ndarray | None = None
        self.tiles: list[Tile] = []
        self.moves = 0
        self.hints_used = 0
        self.completed = False
        self.active_hint: tuple[int, int] | None = None
        self.last_scramble: list[Transformation] = []

    def load_image(self, path: str, grid_size: int) -> None:
        """Load an image, create tiles, and start a newly scrambled round."""
        if grid_size not in self.TRANSFORM_COUNTS:
            raise PuzzleError("Grid size must be 3, 4, or 5.")

        image_path = Path(path)
        if image_path.suffix.lower() not in self.SUPPORTED_SUFFIXES:
            raise PuzzleError("Please select a JPG, PNG, or BMP image.")

        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None or image.size == 0:
            raise PuzzleError("The selected file could not be opened as an image.")

        self.grid_size = grid_size
        self.original_image = self._resize_and_pad(image)
        self.image_size = self.original_image.shape[0]
        self.tiles = self._create_tiles(self.original_image)
        self.moves = 0
        self.hints_used = 0
        self.completed = False
        self.active_hint = None

        self.last_scramble = self._generate_transformations()
        for transformation in self.last_scramble:
            transformation.apply(self)

    def _resize_and_pad(self, image: np.ndarray) -> np.ndarray:
        """Preserve aspect ratio and pad to a square divisible by the grid."""
        target = (self.maximum_image_size // self.grid_size) * self.grid_size
        height, width = image.shape[:2]
        scale = min(target / width, target / height)
        new_width = max(1, int(round(width * scale)))
        new_height = max(1, int(round(height * scale)))

        interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
        resized = cv2.resize(
            image,
            (new_width, new_height),
            interpolation=interpolation,
        )

        canvas = np.full((target, target, 3), 32, dtype=np.uint8)
        x_offset = (target - new_width) // 2
        y_offset = (target - new_height) // 2
        canvas[
            y_offset : y_offset + new_height,
            x_offset : x_offset + new_width,
        ] = resized
        return canvas

    def _create_tiles(self, image: np.ndarray) -> list[Tile]:
        tile_size = image.shape[0] // self.grid_size
        tiles: list[Tile] = []
        tile_id = 0
        for row in range(self.grid_size):
            for column in range(self.grid_size):
                y1 = row * tile_size
                x1 = column * tile_size
                tile_image = image[
                    y1 : y1 + tile_size,
                    x1 : x1 + tile_size,
                ]
                tiles.append(Tile(tile_id, tile_image))
                tile_id += 1
        return tiles

    def _generate_transformations(self) -> list[Transformation]:
        """Generate all random operations without targeting any tile twice."""
        total = self.TRANSFORM_COUNTS[self.grid_size]
        tile_count = self.grid_size**2
        max_swaps = min(tile_count - total, total - 2)
        swap_count = random.randint(1, max_swaps)
        rotate_count = random.randint(1, total - swap_count - 1)
        flip_count = total - swap_count - rotate_count

        required_tiles = swap_count * 2 + rotate_count + flip_count
        targets = random.sample(self.tiles, required_tiles)
        transformations: list[Transformation] = []
        cursor = 0

        for _ in range(swap_count):
            transformations.append(
                SwapTransformation(targets[cursor], targets[cursor + 1])
            )
            cursor += 2

        for _ in range(rotate_count):
            transformations.append(
                RotateTransformation(
                    targets[cursor],
                    random.choice((90, 180, 270)),
                )
            )
            cursor += 1

        for _ in range(flip_count):
            transformations.append(
                FlipTransformation(
                    targets[cursor],
                    random.choice(("horizontal", "vertical")),
                )
            )
            cursor += 1

        random.shuffle(transformations)
        return transformations

    def swap_tile_objects(self, first: Tile, second: Tile) -> None:
        first_position = self.tiles.index(first)
        second_position = self.tiles.index(second)
        self.tiles[first_position], self.tiles[second_position] = (
            self.tiles[second_position],
            self.tiles[first_position],
        )

    def tile_is_correct(self, position: int) -> bool:
        tile = self.tiles[position]
        return tile.tile_id == position and tile.orientation_is_correct()

    def incorrect_positions(self) -> list[int]:
        return [
            position
            for position in range(len(self.tiles))
            if not self.tile_is_correct(position)
        ]

    def incorrect_count(self) -> int:
        return len(self.incorrect_positions())

    def reassemble(self) -> np.ndarray:
        if not self.tiles:
            raise PuzzleError("No puzzle has been loaded.")
        rows = []
        for row in range(self.grid_size):
            start = row * self.grid_size
            rows.append(np.hstack([tile.image for tile in self.tiles[start:start + self.grid_size]]))
        return np.vstack(rows)

    def _finish_user_move(self) -> None:
        self.moves += 1
        self.active_hint = None
        self.completed = self.incorrect_count() == 0

    def swap_positions(self, first: int, second: int) -> None:
        if self.completed:
            return
        self.tiles[first], self.tiles[second] = self.tiles[second], self.tiles[first]
        self._finish_user_move()

    def rotate_at(self, position: int) -> None:
        if self.completed:
            return
        self.tiles[position].rotate_clockwise()
        self._finish_user_move()

    def flip_at(self, position: int) -> None:
        if self.completed:
            return
        self.tiles[position].flip_horizontal()
        self._finish_user_move()

    def request_hint(self) -> tuple[int, int] | None:
        if self.completed or self.hints_used >= 3:
            return None
        incorrect = self.incorrect_positions()
        if not incorrect:
            return None
        current_position = random.choice(incorrect)
        home_position = self.tiles[current_position].tile_id
        self.hints_used += 1
        self.active_hint = (current_position, home_position)
        return self.active_hint

    def solve(self) -> None:
        if not self.tiles:
            return
        self.tiles.sort(key=lambda tile: tile.tile_id)
        for tile in self.tiles:
            tile.reset_orientation()
        self.moves = 0
        self.active_hint = None
        self.completed = True
