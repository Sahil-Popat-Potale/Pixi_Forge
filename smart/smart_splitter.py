import cv2
import numpy as np
from PIL import Image
from typing import List


class SmartVerticalSplitter:
    """
    Content-aware vertical image splitter using OpenCV.
    """

    def __init__(self, image_path: str):
        self.image_path = image_path
        self.cv_image = cv2.imread(image_path)

        if self.cv_image is None:
            raise ValueError("Failed to load image with OpenCV.")

        self.height, self.width = self.cv_image.shape[:2]

    def find_split_positions(self, n: int) -> List[int]:
        """
        Find n-1 smart vertical split positions.
        """
        if n <= 1:
            raise ValueError("n must be greater than 1 for smart splitting.")
        if n > self.width:
            raise ValueError("n exceeds image width.")

        gray = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, threshold1=50, threshold2=150)

        # Sum edge strength column-wise
        column_energy = np.sum(edges, axis=0)

        # Normalize for stability
        column_energy = column_energy.astype(np.float32)
        column_energy /= column_energy.max() + 1e-6

        # We want LOW-energy columns (less visual content)
        sorted_indices = np.argsort(column_energy)

        split_positions = []
        min_gap = self.width // n

        for idx in sorted_indices:
            if idx < min_gap or idx > self.width - min_gap:
                continue

            if all(abs(idx - s) >= min_gap for s in split_positions):
                split_positions.append(idx)

            if len(split_positions) == n - 1:
                break

        if len(split_positions) < n - 1:
            raise RuntimeError("Unable to find enough smart split positions.")

        split_positions.sort()
        return split_positions

    def split(self, n: int) -> List[Image.Image]:
        """
        Perform smart vertical slicing.
        """
        split_positions = self.find_split_positions(n)

        pil_image = Image.open(self.image_path)
        slices = []

        prev_x = 0
        index = 1

        for x in split_positions + [self.width]:
            box = (prev_x, 0, x, self.height)
            slices.append(pil_image.crop(box))
            prev_x = x
            index += 1

        return slices
