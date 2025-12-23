import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np

from batch import BatchImageProcessor
from core import ImageSlicer

PREVIEW_SIZE = (420, 260)


class PixelForgeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PixelForge — Intelligent Image Slicer")
        self.root.geometry("750x620")
        self.root.minsize(720, 600)

        # -------- State --------
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.mode = tk.StringVar(value="horizontal")
        self.n = tk.StringVar()
        self.rows = tk.StringVar()
        self.cols = tk.StringVar()
        self.smart = tk.BooleanVar()
        self.status = tk.StringVar(value="Select an input folder")

        self.original_image = None
        self.preview_image = None
        self.image_path = None

        self._build_ui()
        self._bind_reactivity()

    # ---------------- UI ----------------

    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}

        # -------- Input / Output --------
        io_frame = tk.Frame(self.root)
        io_frame.pack(fill="x")

        tk.Label(io_frame, text="Input Folder").pack(**pad)
        tk.Entry(io_frame, textvariable=self.input_dir, width=70).pack()
        tk.Button(io_frame, text="Browse", command=self.select_input).pack(**pad)

        tk.Label(io_frame, text="Output Folder").pack(**pad)
        tk.Entry(io_frame, textvariable=self.output_dir, width=70).pack()
        tk.Button(io_frame, text="Browse", command=self.select_output).pack(**pad)

        # -------- Preview --------
        preview_frame = tk.Frame(self.root)
        preview_frame.pack(pady=10)

        tk.Label(preview_frame, text="Preview (live)").pack()
        self.preview_canvas = tk.Canvas(
            preview_frame,
            width=PREVIEW_SIZE[0],
            height=PREVIEW_SIZE[1],
            bg="#444"
        )
        self.preview_canvas.pack()

        # -------- Controls --------
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill="x", pady=10)

        tk.Label(control_frame, text="Mode").grid(row=0, column=0, sticky="w")
        for i, m in enumerate(("horizontal", "vertical", "grid")):
            tk.Radiobutton(
                control_frame,
                text=m.capitalize(),
                variable=self.mode,
                value=m
            ).grid(row=0, column=i + 1, sticky="w")

        tk.Label(control_frame, text="n").grid(row=1, column=0, sticky="w")
        self.n_entry = tk.Entry(control_frame, textvariable=self.n, width=10)
        self.n_entry.grid(row=1, column=1, sticky="w")

        tk.Label(control_frame, text="Rows").grid(row=2, column=0, sticky="w")
        self.rows_entry = tk.Entry(control_frame, textvariable=self.rows, width=10)
        self.rows_entry.grid(row=2, column=1, sticky="w")

        tk.Label(control_frame, text="Cols").grid(row=2, column=2, sticky="w")
        self.cols_entry = tk.Entry(control_frame, textvariable=self.cols, width=10)
        self.cols_entry.grid(row=2, column=3, sticky="w")

        self.smart_check = tk.Checkbutton(
            control_frame,
            text="Smart slicing (horizontal only)",
            variable=self.smart
        )
        self.smart_check.grid(row=3, column=0, columnspan=3, sticky="w")

        # -------- Run --------
        tk.Button(
            self.root,
            text="Run Batch Processing",
            bg="#2ecc71",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            command=self.run_processing
        ).pack(pady=12)

        # -------- Status --------
        status_bar = tk.Label(
            self.root,
            textvariable=self.status,
            anchor="w",
            bg="#222",
            fg="white",
            padx=10
        )
        status_bar.pack(fill="x", side="bottom")

    # ---------------- Reactivity ----------------

    def _bind_reactivity(self):
        for var in (self.mode, self.n, self.rows, self.cols, self.smart):
            var.trace_add("write", lambda *_: self.on_state_change())

    def on_state_change(self):
        self.update_field_states()
        self.update_preview()

    def update_field_states(self):
        mode = self.mode.get()

        self.n_entry.config(state="normal" if mode in ("horizontal", "vertical") else "disabled")
        self.rows_entry.config(state="normal" if mode == "grid" else "disabled")
        self.cols_entry.config(state="normal" if mode == "grid" else "disabled")
        self.smart_check.config(state="normal" if mode == "horizontal" else "disabled")

    # ---------------- Preview ----------------

    def select_input(self):
        path = filedialog.askdirectory()
        if path:
            self.input_dir.set(path)
            self.load_preview_image()

    def select_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_dir.set(path)

    def load_preview_image(self):
        try:
            images = [
                f for f in os.listdir(self.input_dir.get())
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".tiff"))
            ]
            if not images:
                raise ValueError("No images found in folder")

            self.image_path = os.path.join(self.input_dir.get(), images[0])
            self.original_image = Image.open(self.image_path)
            self.status.set("Preview loaded")
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

        try:
            slicer = ImageSlicer.__new__(ImageSlicer)
            slicer.width, slicer.height = self.original_image.size

            scale_x = img.width / slicer.width
            scale_y = img.height / slicer.height

            if self.mode.get() == "horizontal" and self.n.get():
                widths = slicer._compute_segments(slicer.width, int(self.n.get()))
                x = 0
                for w in widths[:-1]:
                    x += w
                    self.preview_canvas.create_line(
                        x * scale_x, 0, x * scale_x, img.height,
                        fill="white", width=2
                    )

            elif self.mode.get() == "vertical" and self.n.get():
                heights = slicer._compute_segments(slicer.height, int(self.n.get()))
                y = 0
                for h in heights[:-1]:
                    y += h
                    self.preview_canvas.create_line(
                        0, y * scale_y, img.width, y * scale_y,
                        fill="white", width=2
                    )

            elif self.mode.get() == "grid" and self.rows.get() and self.cols.get():
                widths = slicer._compute_segments(slicer.width, int(self.cols.get()))
                heights = slicer._compute_segments(slicer.height, int(self.rows.get()))

                x = 0
                for w in widths[:-1]:
                    x += w
                    self.preview_canvas.create_line(
                        x * scale_x, 0, x * scale_x, img.height,
                        fill="white", width=2
                    )

                y = 0
                for h in heights[:-1]:
                    y += h
                    self.preview_canvas.create_line(
                        0, y * scale_y, img.width, y * scale_y,
                        fill="white", width=2
                    )

            self.status.set("Preview updated")

        except Exception:
            self.status.set("Invalid parameters")

    # ---------------- Batch ----------------

    def run_processing(self):
        try:
            self.status.set("Running batch...")
            self.root.update_idletasks()

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

            self.status.set("Batch completed")
            messagebox.showinfo(
                "Done",
                f"Processed: {len(result.processed)}\nFailed: {len(result.failed)}"
            )

        except Exception as e:
            self.status.set("Error")
            messagebox.showerror("Error", str(e))


def launch():
    root = tk.Tk()
    PixelForgeGUI(root)
    root.mainloop()
