from batch import BatchImageProcessor

processor = BatchImageProcessor(
    input_dir="input_images",
    output_dir="output_images",
    log_dir="logs"
)

print("Running batch slicing...")

result = processor.process(
    mode="horizontal",
    n=3,
    smart=True
)

print("\nBatch finished")
print("Processed files:", result.processed)
print("Failed files:", result.failed)
