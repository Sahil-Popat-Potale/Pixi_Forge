from PIL import Image
from typing import List, Tuple, Literal


SliceMode = Literal["horizontal", "vertical", "grid"]


class ImageSlice:
    """
    Represents one sliced image and its position.
    """
    def __init__(self, image: Image.Image, index: int, box: Tuple[int, int, int, int]):
        self.image = image
        self.index = index
        self.box = box


class ImageSlicer:
    """
    Core image slicing engine.
    Supports horizontal, vertical, and grid slicing.
    """

    def __init__(self, image_path: str):
        self.image = Image.open(image_path)
        self.width, self.height = self.image.size
        self.info = self.image.info  # metadata preserved in memory

    @staticmethod
    def _compute_segments(total_pixels: int, n: int) -> List[int]:
        """
        Evenly split pixels into n segments.
        Distributes remainder pixels from the start.
        """
        if n <= 0:
            raise ValueError("Number of segments must be greater than zero.")
        if n > total_pixels:
            raise ValueError("Number of segments exceeds pixel dimension.")

        base = total_pixels // n
        remainder = total_pixels % n

        return [
            base + 1 if i < remainder else base
            for i in range(n)
        ]

    def slice(self, mode: SliceMode, n: int = None, rows: int = None, cols: int = None) -> List[ImageSlice]:
        """
        Unified slicing API.

        horizontal: n required
        vertical: n required
        grid: rows and cols required
        """
        if mode == "horizontal":
            if n is None:
                raise ValueError("Horizontal slicing requires n.")
            return self._slice_horizontal(n)

        if mode == "vertical":
            if n is None:
                raise ValueError("Vertical slicing requires n.")
            return self._slice_vertical(n)

        if mode == "grid":
            if rows is None or cols is None:
                raise ValueError("Grid slicing requires rows and cols.")
            return self._slice_grid(rows, cols)

        raise ValueError(f"Unsupported slicing mode: {mode}")

    def _slice_horizontal(self, n: int) -> List[ImageSlice]:
        widths = self._compute_segments(self.width, n)
        slices = []

        x = 0
        for i, w in enumerate(widths, start=1):
            box = (x, 0, x + w, self.height)
            cropped = self.image.crop(box)
            slices.append(ImageSlice(cropped, i, box))
            x += w

        return slices

    def _slice_vertical(self, n: int) -> List[ImageSlice]:
        heights = self._compute_segments(self.height, n)
        slices = []

        y = 0
        for i, h in enumerate(heights, start=1):
            box = (0, y, self.width, y + h)
            cropped = self.image.crop(box)
            slices.append(ImageSlice(cropped, i, box))
            y += h

        return slices

    def _slice_grid(self, rows: int, cols: int) -> List[ImageSlice]:
        """
        Slice image into a rows × cols grid.
        """
        row_heights = self._compute_segments(self.height, rows)
        col_widths = self._compute_segments(self.width, cols)

        slices = []
        index = 1
        y = 0

        for rh in row_heights:
            x = 0
            for cw in col_widths:
                box = (x, y, x + cw, y + rh)
                cropped = self.image.crop(box)
                slices.append(ImageSlice(cropped, index, box))
                index += 1
                x += cw
            y += rh

        return slices
