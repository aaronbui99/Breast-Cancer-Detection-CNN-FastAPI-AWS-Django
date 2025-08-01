import os
import subprocess
import shutil
import sys
import zipfile
import tempfile

def create_torch_layer():
    print("Creating PyTorch Lambda layer...")

    # Correct structure: python/lib/python3.10/site-packages
    temp_dir = tempfile.mkdtemp()
    site_packages_dir = os.path.join(temp_dir, "python", "lib", "python3.10", "site-packages")
    os.makedirs(site_packages_dir, exist_ok=True)

    # Install into site-packages directly
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "--extra-index-url", "https://download.pytorch.org/whl/cpu",
        "torch==2.0.0+cpu", "torchvision==0.15.0+cpu",
        "--no-deps", "--target", site_packages_dir
    ])

    # Clean-up (optional, same as before)
    # ... (you can keep your clean-up code here)

    # Zip the folder
    zip_path = "torch_layer.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, temp_dir)
                zipf.write(full_path, rel_path)

    print(f"Layer created: {zip_path}")
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    create_torch_layer()