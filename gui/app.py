import os
import threading
import subprocess
import shutil
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
from typing import Any, Optional

from batch import BatchImageProcessor
from core import ImageSlicer

PREVIEW_SIZE = (420, 260)


class PixelForgeGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Pixi Forge — Intelligent Image Slicer")
        self.root.geometry("820x680")
        self.root.minsize(760, 620)

        # -------- State --------
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.mode = tk.StringVar(value="horizontal")
        self.n = tk.StringVar()
        self.rows = tk.StringVar()
        self.cols = tk.StringVar()
        self.smart = tk.BooleanVar()
        self.status = tk.StringVar(value="Select an input folder")

        self.original_image: Optional[Image.Image] = None
        self.preview_image: Optional[ImageTk.PhotoImage] = None
        self.image_path: Optional[str] = None

        # Extraction worker state
        self._extract_thread: Optional[threading.Thread] = None
        self._extract_cancel = threading.Event()
        self._extract_process: Optional[subprocess.Popen] = None
        self._extract_count_var = tk.StringVar(value="Frames: 0")

        self._build_ui()
        self._bind_reactivity()

    # ---------------- UI ----------------

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 4}

        # -------- Input / Output --------
        io_frame = tk.Frame(self.root)
        io_frame.pack(fill="x")

        tk.Label(io_frame, text="Input Folder").pack(**pad)
        tk.Entry(io_frame, textvariable=self.input_dir, width=80).pack()
        tk.Button(io_frame, text="Browse", command=self.select_input).pack(**pad)

        tk.Label(io_frame, text="Output Folder").pack(**pad)
        tk.Entry(io_frame, textvariable=self.output_dir, width=80).pack()
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

        # -------- Run / Tools --------
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(pady=12)

        tk.Button(
            buttons_frame,
            text="Run Batch Processing",
            bg="#2ecc71",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            command=self.run_processing,
            width=22
        ).grid(row=0, column=0, padx=6, pady=4)

        # Video extractor controls
        tk.Button(
            buttons_frame,
            text="Extract Frames (Video → Images)",
            bg="#3b82f6",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            command=self.ask_and_extract,
            width=26
        ).grid(row=0, column=1, padx=6, pady=4)

        tk.Button(
            buttons_frame,
            text="Cancel Extraction",
            bg="#ef4444",
            fg="white",
            command=self.cancel_extraction,
            width=14
        ).grid(row=0, column=2, padx=6, pady=4)

        tk.Label(buttons_frame, textvariable=self._extract_count_var).grid(row=0, column=3, padx=8)

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

    def _bind_reactivity(self) -> None:
        # bind a real callback so type checkers understand it
        def _trace_callback(*args: Any) -> None:
            self.on_state_change()

        for var in (self.mode, self.n, self.rows, self.cols, self.smart):
            var.trace_add("write", _trace_callback)

    def on_state_change(self) -> None:
        self.update_field_states()
        self.update_preview()

    def update_field_states(self) -> None:
        mode = self.mode.get()

        self.n_entry.config(state="normal" if mode in ("horizontal", "vertical") else "disabled")
        self.rows_entry.config(state="normal" if mode == "grid" else "disabled")
        self.cols_entry.config(state="normal" if mode == "grid" else "disabled")
        self.smart_check.config(state="normal" if mode == "horizontal" else "disabled")

    # ---------------- Preview ----------------

    def select_input(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.input_dir.set(path)
            self.load_preview_image()

    def select_output(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.output_dir.set(path)

    def load_preview_image(self) -> None:
        try:
            images = [
                f for f in os.listdir(self.input_dir.get() or ".")
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

    def update_preview(self) -> None:
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

            # Smart overlay (horizontal only) - draw first so deterministic lines sit on top
            if self.smart.get() and self.mode.get() == "horizontal" and self.n.get():
                self.draw_smart_overlay(img, scale_x)

            if self.mode.get() == "horizontal" and self.n.get():
                widths = slicer.compute_segments(slicer.width, int(self.n.get()))
                x = 0
                for w in widths[:-1]:
                    x += w
                    self.preview_canvas.create_line(
                        x * scale_x, 0, x * scale_x, img.height,
                        fill="white", width=2
                    )

            elif self.mode.get() == "vertical" and self.n.get():
                heights = slicer.compute_segments(slicer.height, int(self.n.get()))
                y = 0
                for h in heights[:-1]:
                    y += h
                    self.preview_canvas.create_line(
                        0, y * scale_y, img.width, y * scale_y,
                        fill="white", width=2
                    )

            elif self.mode.get() == "grid" and self.rows.get() and self.cols.get():
                widths = slicer.compute_segments(slicer.width, int(self.cols.get()))
                heights = slicer.compute_segments(slicer.height, int(self.rows.get()))

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

    def draw_smart_overlay(self, preview_img: Image.Image, scale_x: float) -> None:
        """
        Draws an adaptive smart slicing heatmap + candidate markers.
        Uses local imports for OpenCV and numpy to avoid top-level unused-import warnings.
        The drawing samples image columns into canvas columns for efficiency.
        """
        try:
            import cv2  # local import
            import numpy as np  # local import
        except Exception:
            # OpenCV / numpy not available; skip overlay silently
            return

        if not self.image_path:
            return

        cv_img = cv2.imread(self.image_path)
        if cv_img is None:
            return

        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        # Column-wise edge energy
        energy = np.sum(edges, axis=0).astype(float)
        if energy.size == 0:
            return
        energy /= energy.max() + 1e-6

        width = self.original_image.width
        preview_w = preview_img.width

        # Adaptive thresholds (percentiles)
        low_t = float(np.percentile(energy, 20))
        mid_t = float(np.percentile(energy, 50))
        high_t = float(np.percentile(energy, 80))

        # To avoid drawing one line per pixel (slow), sample columns to preview width
        cols_per_pixel = max(1, width // preview_w)

        for i in range(preview_w):
            start = i * cols_per_pixel
            end = min(width, (i + 1) * cols_per_pixel)
            block = energy[start:end]
            if block.size == 0:
                continue
            e = float(np.mean(block))

            if e <= low_t:
                color = "#3b82f6"   # blue
            elif e <= mid_t:
                color = "#22c55e"   # green
            elif e <= high_t:
                color = "#eab308"   # yellow
            else:
                color = "#ef4444"   # red

            x1 = i
            x2 = i + 1
            # Draw thin vertical rectangle representing this sample column
            self.preview_canvas.create_rectangle(
                x1, 0, x2, preview_img.height,
                fill=color, outline=color
            )

        # Candidate split markers (best-effort)
        try:
            n = int(self.n.get())
            if n <= 1:
                return

            min_gap = width // n
            sorted_indices = np.argsort(energy)

            candidates = []
            for idx in sorted_indices:
                if idx < min_gap or idx > width - min_gap:
                    continue
                if all(abs(int(idx) - int(c)) >= min_gap for c in candidates):
                    candidates.append(int(idx))
                if len(candidates) == n - 1:
                    break

            # draw candidate markers (thick green) scaled to preview
            for x in candidates:
                px = int((x / width) * preview_w)
                self.preview_canvas.create_line(
                    px, 0, px, preview_img.height,
                    fill="#16a34a", width=3
                )
        except Exception:
            # silent best-effort candidate selection
            pass

    # ---------------- Video extraction (GUI) ----------------

    @staticmethod
    def _ffmpeg_available() -> bool:
        return shutil.which("ffmpeg") is not None

    def ask_and_extract(self) -> None:
        """
        UI flow for selecting a video and starting extraction.
        Runs extraction in a background thread; provides cancel support.
        """
        video_file = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.mov *.mkv *.avi *.webm *.mpg"), ("All files", "*.*")]
        )
        if not video_file:
            return

        outdir = filedialog.askdirectory(title="Select output folder for frames")
        if not outdir:
            return

        fmt = simpledialog.askstring("Format", "Image format (png/jpg/tiff)", initialvalue="png")
        if not fmt:
            fmt = "png"

        # choose backend automatically (prefers ffmpeg)
        backend = "ffmpeg" if self._ffmpeg_available() else "opencv"

        # reset cancel flag and count
        self._extract_cancel.clear()
        self._extract_count_var.set("Frames: 0")
        self.status.set("Starting frame extraction...")
        self._extract_thread = threading.Thread(
            target=self._extract_worker,
            args=(video_file, outdir, fmt.lower(), backend),
            daemon=True
        )
        self._extract_thread.start()

    def cancel_extraction(self) -> None:
        """
        Request extraction cancellation; this will kill ffmpeg subprocess or stop OpenCV loop.
        """
        if self._extract_thread and self._extract_thread.is_alive():
            self._extract_cancel.set()
            # kill ffmpeg if running
            if self._extract_process:
                try:
                    self._extract_process.kill()
                except Exception:
                    pass
            self.status.set("Extraction cancellation requested")
        else:
            self.status.set("No active extraction to cancel")

    def _extract_worker(self, video_path: str, outdir: str, fmt: str, backend: str) -> None:
        """
        Worker that runs in a background thread. For ffmpeg we spawn a subprocess and
        monitor the output directory to show extracted frame count. For OpenCV we perform
        frame-by-frame extraction and update the counter each frame. Support cancellation.
        """
        try:
            os.makedirs(outdir, exist_ok=True)
            prefix = "frame"

            # Remove previous frames from outdir that match the pattern? We leave them to avoid data loss.
            # Instead, we count only matching files created during this run by tracking initial set.
            initial_files = set(f for f in os.listdir(outdir) if f.lower().endswith("." + fmt.lower()) and f.startswith(prefix + "_"))

            if backend == "ffmpeg" and self._ffmpeg_available():
                # Run ffmpeg with progress to stdout and monitor created files
                out_pattern = os.path.join(outdir, f"{prefix}_%06d.{fmt}")
                cmd = ["ffmpeg", "-hide_banner", "-progress", "-", "-i", video_path, "-vsync", "0", "-y", out_pattern]

                # spawn
                self._extract_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )

                # While ffmpeg runs, poll the output directory for new frames and handle cancel
                last_count = 0
                while True:
                    if self._extract_cancel.is_set():
                        # kill process and exit
                        try:
                            if self._extract_process:
                                self._extract_process.kill()
                        except Exception:
                            pass
                        break

                    # non-blocking check if process has ended
                    retcode = self._extract_process.poll()
                    # count new files
                    cur_files = [f for f in os.listdir(outdir) if f.startswith(prefix + "_") and f.lower().endswith("." + fmt.lower())]
                    cur_count = len([f for f in cur_files if f not in initial_files])
                    if cur_count != last_count:
                        last_count = cur_count
                        # schedule UI update on main thread
                        self.root.after(0, lambda c=cur_count: self._extract_count_var.set(f"Frames: {c}"))

                    if retcode is not None:
                        # process finished
                        break

                    # small sleep to avoid busy loop
                    time.sleep(0.2)

                # after exit, read returncode and stderr for errors
                if self._extract_cancel.is_set():
                    self.root.after(0, lambda: self.status.set("Extraction canceled"))
                    self._extract_process = None
                    return

                ret = self._extract_process.wait()
                stderr = self._extract_process.stderr.read() if self._extract_process.stderr else ""
                self._extract_process = None

                if ret != 0:
                    # ffmpeg failed; surface error
                    self.root.after(0, lambda: self.status.set("Extraction failed"))
                    self.root.after(0, lambda: messagebox.showerror("Extraction error", f"ffmpeg failed:\n{stderr}"))
                    return

                # final count
                final_files = [f for f in os.listdir(outdir) if f.startswith(prefix + "_") and f.lower().endswith("." + fmt.lower())]
                final_count = len([f for f in final_files if f not in initial_files])
                self.root.after(0, lambda: self._extract_count_var.set(f"Frames: {final_count}"))
                self.root.after(0, lambda: self.status.set(f"Extracted {final_count} frames (ffmpeg)"))
                return

            # Fallback: OpenCV extraction implemented inline so we can report progress and cancel
            try:
                import cv2
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Extraction error", "OpenCV not installed and ffmpeg not available."))
                self.root.after(0, lambda: self.status.set("Extraction failed"))
                return

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self.root.after(0, lambda: messagebox.showerror("Extraction error", f"Failed to open video: {video_path}"))
                self.root.after(0, lambda: self.status.set("Extraction failed"))
                return

            idx = 0
            written = 0
            while True:
                if self._extract_cancel.is_set():
                    break
                ret, frame = cap.read()
                if not ret:
                    break
                idx += 1
                out_name = f"{prefix}_{idx:06d}.{fmt}"
                out_path = os.path.join(outdir, out_name)

                # write with best available params
                if fmt.lower() in ("jpg", "jpeg"):
                    ok = cv2.imwrite(out_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
                elif fmt.lower() == "png":
                    ok = cv2.imwrite(out_path, frame, [int(cv2.IMWRITE_PNG_COMPRESSION), 0])
                else:
                    ok = cv2.imwrite(out_path, frame)

                if not ok:
                    cap.release()
                    self.root.after(0, lambda: messagebox.showerror("Extraction error", f"Failed to write frame {out_path}"))
                    self.root.after(0, lambda: self.status.set("Extraction failed"))
                    return

                written += 1
                # update UI
                if written % 1 == 0:
                    self.root.after(0, lambda c=written: self._extract_count_var.set(f"Frames: {c}"))
                # small sleep to be cooperative
                time.sleep(0.001)

            cap.release()
            if self._extract_cancel.is_set():
                self.root.after(0, lambda: self.status.set("Extraction canceled"))
            else:
                self.root.after(0, lambda: self.status.set(f"Extracted {written} frames (opencv)"))
            self.root.after(0, lambda w=written: self._extract_count_var.set(f"Frames: {w}"))

        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror("Extraction error", str(exc)))
            self.root.after(0, lambda: self.status.set("Extraction failed"))

    # ---------------- Batch ----------------

    def run_processing(self) -> None:
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


def launch() -> None:
    root = tk.Tk()
    PixelForgeGUI(root)
    root.mainloop()
