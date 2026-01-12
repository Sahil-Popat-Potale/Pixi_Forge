# Changelog

All notable changes to Pixi Forge will be documented in this file.

## [1.0.0] - 2026-01-05
### Added
- Core deterministic image slicing (horizontal, vertical, grid).
- Smart OpenCV-based slicing with adaptive heatmap preview.
- Responsive Tkinter GUI with live preview and explainable smart overlay.
- Batch processing with logging and CLI.
- Video → Frames extraction feature (ffmpeg preferred, OpenCV fallback).
- Packaging guidance and PyInstaller configuration notes.
- Requirements, VERSION and CHANGELOG files.

### Fixed
- Pylance/linting issues: removed unused top-level imports, added typed callbacks, made compute_segments public, updated BatchImageProcessor typing.
- Smart preview performance improvement (sampled heatmap).

### Notes
- For best video extraction results install ffmpeg and add to PATH.
