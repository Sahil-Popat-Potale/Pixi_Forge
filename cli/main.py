import argparse
import sys
from batch.processor import BatchImageProcessor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pixelforge",
        description="PixelForge — Intelligent Image Slicing Tool"
    )

    parser.add_argument(
        "input_dir",
        help="Directory containing input images"
    )

    parser.add_argument(
        "output_dir",
        help="Directory to store output images"
    )

    parser.add_argument(
        "--mode",
        required=True,
        choices=["horizontal", "vertical", "grid"],
        help="Slicing mode"
    )

    parser.add_argument(
        "--n",
        type=int,
        help="Number of slices (horizontal or vertical)"
    )

    parser.add_argument(
        "--rows",
        type=int,
        help="Grid rows (grid mode only)"
    )

    parser.add_argument(
        "--cols",
        type=int,
        help="Grid columns (grid mode only)"
    )

    parser.add_argument(
        "--format",
        default="png",
        help="Output image format (default: png)"
    )

    parser.add_argument(
        "--logs",
        default=None,
        help="Directory to store log files"
    )

    parser.add_argument(
        "--smart",
        action="store_true",
        help="Enable smart slicing (horizontal only)"
    )
    return parser

def validate_args(args: argparse.Namespace):
    if args.mode in ("horizontal", "vertical") and args.n is None:
        raise ValueError("--n is required for horizontal/vertical mode")

    if args.mode == "grid" and (args.rows is None or args.cols is None):
        raise ValueError("--rows and --cols are required for grid mode")
    
    if args.smart and args.mode != "horizontal":
        raise ValueError("Smart slicing is supported only for horizontal mode")

def run():
    parser = build_parser()
    args = parser.parse_args()

    try:
        validate_args(args)

        processor = BatchImageProcessor(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            log_dir=args.logs
        )

        result = processor.process(
            mode=args.mode,
            n=args.n,
            rows=args.rows,
            cols=args.cols,
            output_format=args.format,
            smart=args.smart
        )
        sys.exit(1 if result.failed else 0)

    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(2)
