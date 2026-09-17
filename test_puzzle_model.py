"""Core tests that do not start the Tkinter interface."""

import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from puzzle_model import PuzzleModel, Tile
from transformations import FlipTransformation, RotateTransformation, SwapTransformation


class PuzzleModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.image_path = Path(self.temp_directory.name) / "sample.png"
        y, x = np.indices((360, 640))
        image = np.dstack(
            (
                (x % 256).astype(np.uint8),
                (y % 256).astype(np.uint8),
                ((x + y) % 256).astype(np.uint8),
            )
        )
        cv2.imwrite(str(self.image_path), image)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_all_grid_sizes_and_scramble_rules(self) -> None:
        for grid_size, expected_count in PuzzleModel.TRANSFORM_COUNTS.items():
            with self.subTest(grid_size=grid_size):
                model = PuzzleModel()
                model.load_image(str(self.image_path), grid_size)
                self.assertEqual(len(model.last_scramble), expected_count)
                self.assertEqual(model.image_size % grid_size, 0)
                self.assertEqual(len(model.tiles), grid_size**2)

                target_ids = []
                operation_types = set()
                for operation in model.last_scramble:
                    operation_types.add(type(operation))
                    if isinstance(operation, SwapTransformation):
                        target_ids.extend(
                            (operation.first_tile.tile_id, operation.second_tile.tile_id)
                        )
                    else:
                        target_ids.append(operation.tile.tile_id)

                self.assertEqual(len(target_ids), len(set(target_ids)))
                self.assertEqual(
                    operation_types,
                    {SwapTransformation, RotateTransformation, FlipTransformation},
                )

    def test_solve_restores_every_tile_and_clears_moves(self) -> None:
        model = PuzzleModel()
        model.load_image(str(self.image_path), 3)
        model.moves = 12
        model.solve()
        self.assertEqual(model.moves, 0)
        self.assertEqual(model.incorrect_count(), 0)
        self.assertTrue(model.completed)

    def test_orientation_state_does_not_depend_on_pixel_symmetry(self) -> None:
        tile = Tile(0, np.zeros((20, 20, 3), dtype=np.uint8))

        tile.rotate_clockwise()
        self.assertFalse(tile.orientation_is_correct())

        for _ in range(3):
            tile.rotate_clockwise()
        self.assertTrue(tile.orientation_is_correct())

        tile.flip_horizontal()
        self.assertFalse(tile.orientation_is_correct())
        tile.flip_horizontal()
        self.assertTrue(tile.orientation_is_correct())


if __name__ == "__main__":
    unittest.main()
