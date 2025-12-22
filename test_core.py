from core import ImageSlicer

print("Loading image...")
slicer = ImageSlicer("input_images/test.png")

print("Image size:", slicer.width, "x", slicer.height)

print("\n--- Horizontal slicing (n=3) ---")
h_slices = slicer.slice("horizontal", n=3)
for s in h_slices:
    print(f"Part {s.index} -> size: {s.image.size}")

print("\n--- Vertical slicing (n=2) ---")
v_slices = slicer.slice("vertical", n=2)
for s in v_slices:
    print(f"Part {s.index} -> size: {s.image.size}")

print("\n--- Grid slicing (2 x 2) ---")
g_slices = slicer.slice("grid", rows=2, cols=2)
print("Total grid parts:", len(g_slices))
for s in g_slices:
    print(f"Part {s.index} -> size: {s.image.size}")
