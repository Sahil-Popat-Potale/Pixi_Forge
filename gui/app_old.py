import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np

from batch import BatchImageProcessor
from core import ImageSlicer


PREVIEW_SIZE = (400, 250)


class PixelForgeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PixelForge — Image Slicer")
        self.root.geometry("700x600")

        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.mode = tk.StringVar(value="horizontal")
        self.n = tk.StringVar()
        self.rows = tk.StringVar()
        self.cols = tk.StringVar()
        self.smart = tk.BooleanVar()

        self.preview_canvas = None
        self.preview_image = None
        self.original_image = None

        self._build_ui()

    # ---------------- UI ----------------

    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}

        tk.Label(self.root, text="Input Folder").pack(**pad)
        tk.Entry(self.root, textvariable=self.input_dir, width=65).pack()
        tk.Button(self.root, text="Browse", command=self.select_input).pack(**pad)

        tk.Label(self.root, text="Output Folder").pack(**pad)
        tk.Entry(self.root, textvariable=self.output_dir, width=65).pack()
        tk.Button(self.root, text="Browse", command=self.select_output).pack(**pad)

        tk.Label(self.root, text="Preview (Red = noisy, Green = candidate)").pack(**pad)
        self.preview_canvas = tk.Canvas(
            self.root,
            width=PREVIEW_SIZE[0],
            height=PREVIEW_SIZE[1],
            bg="gray"
        )
        self.preview_canvas.pack()

        tk.Label(self.root, text="Mode").pack(**pad)
        for m in ("horizontal", "vertical", "grid"):
            tk.Radiobutton(
                self.root, text=m.capitalize(),
                variable=self.mode, value=m,
                command=self.update_preview
            ).pack()

        tk.Label(self.root, text="Parameters").pack(**pad)

        tk.Label(self.root, text="n (horizontal / vertical)").pack()
        tk.Entry(self.root, textvariable=self.n).pack()

        tk.Label(self.root, text="Rows (grid)").pack()
        tk.Entry(self.root, textvariable=self.rows).pack()

        tk.Label(self.root, text="Cols (grid)").pack()
        tk.Entry(self.root, textvariable=self.cols).pack()

        tk.Checkbutton(
            self.root,
            text="Enable Smart Slicing (preview + processing)",
            variable=self.smart,
            command=self.update_preview
        ).pack(**pad)

        tk.Button(
            self.root,
            text="Run Batch Processing",
            bg="green", fg="white",
            command=self.run_processing
        ).pack(pady=12)

    # ---------------- Folder selection ----------------

    def select_input(self):
        path = filedialog.askdirectory()
        if path:
            self.input_dir.set(path)
            self.load_preview_image()

    def select_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_dir.set(path)

    # ---------------- Preview logic ----------------

    def load_preview_image(self):
        try:
            files = os.listdir(self.input_dir.get())
            images = [
                f for f in files
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".tiff"))
            ]
            if not images:
                raise ValueError("No images found.")

            self.image_path = os.path.join(self.input_dir.get(), images[0])
            self.original_image = Image.open(self.image_path)

            self.update_preview()

        except Exception as e:
            messagebox.showerror("Preview Error", str(e))

    def update_preview(self):
        if not self.original_image:
            return

        self.preview_canvas.delete("all")

        img = self.original_image.copy()
        img.thumbnail(PREVIEW_SIZE)
        self.preview_image = ImageTk.PhotoImage(img)

        self.preview_canvas.create_image(
            PREVIEW_SIZE[0] // 2,
            PREVIEW_SIZE[1] // 2,
            image=self.preview_image
        )

        scale_x = img.width / self.original_image.width
        scale_y = img.height / self.original_image.height

        # -------- Smart overlay (horizontal only) --------
        if self.smart.get() and self.mode.get() == "horizontal" and self.n.get():
            self.draw_smart_overlay(img, scale_x)

        # -------- Deterministic lines --------
        try:
            slicer = ImageSlicer.__new__(ImageSlicer)
            slicer.width, slicer.height = self.original_image.size

            if self.mode.get() == "horizontal" and self.n.get():
                widths = slicer._compute_segments(slicer.width, int(self.n.get()))
                x = 0
                for w in widths[:-1]:
                    x += w
                    self.preview_canvas.create_line(
                        x * scale_x, 0,
                        x * scale_x, img.height,
                        fill="white", width=2
                    )
        except Exception:
            pass

    def draw_smart_overlay(self, preview_img, scale_x):
        cv_img = cv2.imread(self.image_path)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        energy = np.sum(edges, axis=0).astype(float)
        energy /= energy.max() + 1e-6

        width = self.original_image.width
        threshold = 0.25  # lower = quieter

        for x in range(width):
            e = energy[x]
            color = "green" if e < threshold else "red"
            self.preview_canvas.create_line(
                x * scale_x, 0,
                x * scale_x, preview_img.height,
                fill=color,
                stipple="gray50"
            )

    # ---------------- Batch processing ----------------

    def run_processing(self):
        try:
            processor = BatchImageProcessor(
                input_dir=self.input_dir.get(),
                output_dir=self.output_dir.get(),
                log_dir="logs"
            )

            result = processor.process(
                mode=self.mode.get(),
                n=int(self.n.get()) if self.n.get() else None,
                rows=int(self.rows.get()) if self.rows.get() else None,
                cols=int(self.cols.get()) if self.cols.get() else None,
                smart=self.smart.get()
            )

            messagebox.showinfo(
                "Done",
                f"Processed: {len(result.processed)}\nFailed: {len(result.failed)}"
            )

        except Exception as e:
            messagebox.showerror("Error", str(e))


def launch():
    root = tk.Tk()
    PixelForgeGUI(root)
    root.mainloop()
