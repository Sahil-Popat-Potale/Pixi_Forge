import os
from typing import List
from core.slicer import ImageSlicer
from smart.smart_splitter import SmartVerticalSplitter
from batch.logger import setup_logger


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tiff"}


class BatchResult:
    def __init__(self):
        self.processed: List[str] = []
        self.failed: List[str] = []


class BatchImageProcessor:
    """
    Batch processor with optional smart slicing and safe fallback.
    """

    def __init__(self, input_dir: str, output_dir: str, log_dir: str = None):
        if not os.path.isdir(input_dir):
            raise ValueError(f"Input directory does not exist: {input_dir}")

        self.input_dir = input_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.logger = setup_logger(log_dir)

    def _is_image_file(self, filename: str) -> bool:
        return os.path.splitext(filename.lower())[1] in SUPPORTED_EXTENSIONS

    def process(
        self,
        mode: str,
        n: int = None,
        rows: int = None,
        cols: int = None,
        output_format: str = "png",
        smart: bool = False
    ) -> BatchResult:

        result = BatchResult()
        files = os.listdir(self.input_dir)

        self.logger.info(
            f"Batch started | mode={mode} | smart={smart} | files={len(files)}"
        )

        for filename in files:
            if not self._is_image_file(filename):
                continue

            input_path = os.path.join(self.input_dir, filename)
            base_name = os.path.splitext(filename)[0]
            image_output_dir = os.path.join(self.output_dir, base_name)
            os.makedirs(image_output_dir, exist_ok=True)

            try:
                self.logger.info(f"Processing: {filename}")

                # --- SMART PATH (only vertical slicing supported) ---
                if smart and mode == "horizontal":
                    try:
                        self.logger.info("Attempting smart slicing")
                        splitter = SmartVerticalSplitter(input_path)
                        images = splitter.split(n)

                        for i, img in enumerate(images, start=1):
                            out_name = f"{base_name}_part{i}.{output_format}"
                            img.save(os.path.join(image_output_dir, out_name))

                        self.logger.info(
                            f"Smart slicing succeeded: {filename}"
                        )
                        result.processed.append(filename)
                        continue

                    except Exception as smart_error:
                        self.logger.warning(
                            f"Smart slicing failed, falling back: {smart_error}"
                        )

                # --- FALLBACK / NORMAL PATH ---
                slicer = ImageSlicer(input_path)
                slices = slicer.slice(
                    mode=mode,
                    n=n,
                    rows=rows,
                    cols=cols
                )

                for s in slices:
                    out_name = f"{base_name}_part{s.index}.{output_format}"
                    s.image.save(os.path.join(image_output_dir, out_name))

                result.processed.append(filename)
                self.logger.info(f"Completed: {filename}")

            except Exception as e:
                error_msg = f"{filename} | ERROR: {str(e)}"
                result.failed.append(error_msg)
                self.logger.error(error_msg)

        self._log_summary(result)
        return result

    def _log_summary(self, result: BatchResult):
        self.logger.info("Batch completed")
        self.logger.info(f"Successful: {len(result.processed)}")
        self.logger.info(f"Failed: {len(result.failed)}")

        if result.failed:
            self.logger.info("Failed files:")
            for f in result.failed:
                self.logger.info(f"  - {f}")
