import os

for root, dirs, files in os.walk("."):
    for file in files:
        path = os.path.join(root, file)
        size = os.path.getsize(path)
        if size > 50 * 1024 * 1024:  # Show files larger than 50MB
            print(f"{path}: {size / (1024 * 1024):.2f} MB")
