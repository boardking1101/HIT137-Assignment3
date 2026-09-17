"""Tkinter interface for the HIT137 image puzzle."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
from PIL import Image, ImageTk

from puzzle_model import PuzzleError, PuzzleModel


class PuzzleApp:
    """Coordinates Tkinter events with the puzzle model."""

    CANVAS_SIZE = 500

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("HIT137 Image Puzzle")
        self.root.resizable(False, False)

        self.model = PuzzleModel(self.CANVAS_SIZE)
        self.selected_position: int | None = None
        self.original_photo: ImageTk.PhotoImage | None = None
        self.puzzle_photo: ImageTk.PhotoImage | None = None

        self.grid_var = tk.StringVar(value="3 x 3")
        self.moves_var = tk.StringVar(value="Moves: 0")
        self.incorrect_var = tk.StringVar(value="Tiles left: 0")
        self.hints_var = tk.StringVar(value="Hints: 3")

        self._build_interface()
        self._set_game_buttons(False)

    def _build_interface(self) -> None:
        controls = ttk.Frame(self.root, padding=10)
        controls.grid(row=0, column=0, columnspan=2, sticky="ew")

        ttk.Label(controls, text="Grid size:").grid(row=0, column=0, padx=5)
        grid_selector = ttk.Combobox(
            controls,
            textvariable=self.grid_var,
            values=("3 x 3", "4 x 4", "5 x 5"),
            state="readonly",
            width=8,
        )
        grid_selector.grid(row=0, column=1, padx=5)

        ttk.Button(
            controls,
            text="Load Image",
            command=self.load_image,
        ).grid(row=0, column=2, padx=8)

        self.hint_button = ttk.Button(
            controls,
            text="Hint",
            command=self.show_hint,
        )
        self.hint_button.grid(row=0, column=3, padx=5)

        self.solve_button = ttk.Button(
            controls,
            text="Solve",
            command=self.solve_puzzle,
        )
        self.solve_button.grid(row=0, column=4, padx=5)

        ttk.Label(controls, textvariable=self.moves_var).grid(row=0, column=5, padx=12)
        ttk.Label(controls, textvariable=self.incorrect_var).grid(row=0, column=6, padx=12)
        ttk.Label(controls, textvariable=self.hints_var).grid(row=0, column=7, padx=12)

        left_frame = ttk.Frame(self.root, padding=(10, 0, 5, 10))
        right_frame = ttk.Frame(self.root, padding=(5, 0, 10, 10))
        left_frame.grid(row=1, column=0)
        right_frame.grid(row=1, column=1)

        ttk.Label(left_frame, text="Original image").pack(pady=(0, 5))
        ttk.Label(right_frame, text="Puzzle").pack(pady=(0, 5))

        self.original_canvas = tk.Canvas(
            left_frame,
            width=self.CANVAS_SIZE,
            height=self.CANVAS_SIZE,
            background="#202020",
            highlightthickness=1,
        )
        self.original_canvas.pack()

        self.puzzle_canvas = tk.Canvas(
            right_frame,
            width=self.CANVAS_SIZE,
            height=self.CANVAS_SIZE,
            background="#202020",
            highlightthickness=1,
        )
        self.puzzle_canvas.pack()
        self.puzzle_canvas.bind("<Button-1>", self.handle_left_click)
        self.puzzle_canvas.bind("<Button-3>", self.handle_right_click)

    def _set_game_buttons(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.hint_button.configure(state=state)
        self.solve_button.configure(state=state)

    def _selected_grid_size(self) -> int:
        return int(self.grid_var.get().split()[0])

    def load_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=(
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("All files", "*.*"),
            ),
        )
        if not path:
            return

        try:
            self.model.load_image(path, self._selected_grid_size())
        except (PuzzleError, OSError, ValueError) as error:
            messagebox.showerror("Image Error", str(error))
            return
        except Exception as error:
            messagebox.showerror(
                "Image Error",
                f"The image could not be loaded: {error}",
            )
            return

        self.selected_position = None
        self._set_game_buttons(True)
        self.refresh_display()

    @staticmethod
    def _to_photo(image) -> ImageTk.PhotoImage:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return ImageTk.PhotoImage(Image.fromarray(rgb))

    def refresh_display(self) -> None:
        if self.model.original_image is None:
            return

        self.original_canvas.delete("all")
        self.puzzle_canvas.delete("all")

        self.original_photo = self._to_photo(self.model.original_image)
        self.puzzle_photo = self._to_photo(self.model.reassemble())
        self.original_canvas.create_image(0, 0, anchor="nw", image=self.original_photo)
        self.puzzle_canvas.create_image(0, 0, anchor="nw", image=self.puzzle_photo)

        self._draw_grid()
        self._draw_correct_ticks()
        self._draw_selection()
        self._draw_hint()
        self._update_status()

    def _draw_grid(self) -> None:
        tile_size = self.model.image_size // self.model.grid_size
        for index in range(1, self.model.grid_size):
            coordinate = index * tile_size
            self.puzzle_canvas.create_line(
                coordinate,
                0,
                coordinate,
                self.model.image_size,
                fill="#b0b0b0",
                width=1,
            )
            self.puzzle_canvas.create_line(
                0,
                coordinate,
                self.model.image_size,
                coordinate,
                fill="#b0b0b0",
                width=1,
            )

    def _tile_box(self, position: int) -> tuple[int, int, int, int]:
        tile_size = self.model.image_size // self.model.grid_size
        row, column = divmod(position, self.model.grid_size)
        x1 = column * tile_size
        y1 = row * tile_size
        return x1, y1, x1 + tile_size, y1 + tile_size

    def _draw_correct_ticks(self) -> None:
        for position in range(len(self.model.tiles)):
            if not self.model.tile_is_correct(position):
                continue
            x1, y1, x2, _ = self._tile_box(position)
            size = max(9, (x2 - x1) // 10)
            margin = max(6, size // 2)
            start_x = x2 - margin - size
            start_y = y1 + margin + size // 2
            self.puzzle_canvas.create_line(
                start_x,
                start_y,
                start_x + size // 2,
                start_y + size // 2,
                start_x + size,
                start_y - size // 2,
                fill="#00e676",
                width=3,
            )

    def _draw_selection(self) -> None:
        if self.selected_position is None:
            return
        x1, y1, x2, y2 = self._tile_box(self.selected_position)
        self.puzzle_canvas.create_rectangle(
            x1 + 2,
            y1 + 2,
            x2 - 2,
            y2 - 2,
            outline="#ffca28",
            width=4,
        )

    def _draw_hint(self) -> None:
        if self.model.active_hint is None:
            return
        current_position, home_position = self.model.active_hint
        for canvas, position in (
            (self.puzzle_canvas, current_position),
            (self.original_canvas, home_position),
        ):
            x1, y1, x2, y2 = self._tile_box(position)
            radius = max(10, (x2 - x1) // 7)
            centre_x = (x1 + x2) // 2
            centre_y = (y1 + y2) // 2
            canvas.create_oval(
                centre_x - radius,
                centre_y - radius,
                centre_x + radius,
                centre_y + radius,
                outline="#2196f3",
                width=4,
            )

    def _update_status(self) -> None:
        self.moves_var.set(f"Moves: {self.model.moves}")
        self.incorrect_var.set(f"Tiles left: {self.model.incorrect_count()}")
        self.hints_var.set(f"Hints: {3 - self.model.hints_used}")

        if self.model.hints_used >= 3 or self.model.completed:
            self.hint_button.configure(state="disabled")
        else:
            self.hint_button.configure(state="normal")

        if self.model.completed:
            self.solve_button.configure(state="disabled")

    def _event_position(self, event: tk.Event) -> int | None:
        if not self.model.tiles:
            return None
        if not (
            0 <= event.x < self.model.image_size
            and 0 <= event.y < self.model.image_size
        ):
            return None
        tile_size = self.model.image_size // self.model.grid_size
        column = event.x // tile_size
        row = event.y // tile_size
        return row * self.model.grid_size + column

    def handle_left_click(self, event: tk.Event) -> None:
        if self.model.completed:
            return
        position = self._event_position(event)
        if position is None:
            return

        shift_pressed = bool(event.state & 0x0001)
        if shift_pressed:
            self.model.flip_at(position)
            self.selected_position = None
            self._after_action()
            return

        if self.selected_position is None:
            self.selected_position = position
        elif self.selected_position == position:
            self.selected_position = None
        else:
            self.model.swap_positions(self.selected_position, position)
            self.selected_position = None
            self._after_action()
            return

        self.refresh_display()

    def handle_right_click(self, event: tk.Event) -> None:
        if self.model.completed:
            return
        position = self._event_position(event)
        if position is None:
            return
        self.model.rotate_at(position)
        self.selected_position = None
        self._after_action()

    def _after_action(self) -> None:
        self.refresh_display()
        if self.model.completed:
            messagebox.showinfo(
                "Puzzle Complete",
                f"Congratulations! You solved the puzzle in {self.model.moves} moves.",
            )

    def show_hint(self) -> None:
        if self.model.request_hint() is not None:
            self.refresh_display()

    def solve_puzzle(self) -> None:
        self.model.solve()
        self.selected_position = None
        self.refresh_display()
        messagebox.showinfo("Puzzle Solved", "The puzzle has been restored.")
