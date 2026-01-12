from smart import SmartVerticalSplitter

print("Loading image for smart slicing...")

splitter = SmartVerticalSplitter("input_images/test2.png")

print("Attempting smart split (n=3)...")
images = splitter.split(n=3)

print("Smart slices created:", len(images))

for i, img in enumerate(images, start=1):
    print(f"Part {i} -> size: {img.size}")
    img.save(f"outputs/smart_part_{i}.png") #type: ignore

print("Saved smart sliced images to outputs/")
