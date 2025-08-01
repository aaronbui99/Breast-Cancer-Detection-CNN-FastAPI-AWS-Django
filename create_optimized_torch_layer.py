import os
import subprocess
import shutil
import sys
import zipfile
import tempfile

def create_optimized_torch_layer():
    print("Creating optimized PyTorch Lambda layer...")

    # Create temporary directory with correct Lambda layer structure
    temp_dir = tempfile.mkdtemp()
    site_packages_dir = os.path.join(temp_dir, "python", "lib", "python3.10", "site-packages")
    os.makedirs(site_packages_dir, exist_ok=True)

    # Install CPU-only versions with minimal dependencies
    print("Installing PyTorch CPU version...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "--extra-index-url", "https://download.pytorch.org/whl/cpu",
        "torch==2.0.0+cpu", "torchvision==0.15.0+cpu",
        "--no-deps", "--target", site_packages_dir,
        "--force-reinstall"
    ])

    # Aggressive cleanup to reduce size
    print("Cleaning up unnecessary files...")
    
    # Remove test files and documentation
    for root, dirs, files in os.walk(site_packages_dir):
        # Remove test directories
        dirs[:] = [d for d in dirs if not d.startswith('test') and d != '__pycache__']
        
        for file in files:
            file_path = os.path.join(root, file)
            
            # Remove test files, documentation, and unnecessary files
            if (file.endswith(('.pyx', '.pxi', '.pxd', '.c', '.cpp', '.h')) or
                file.startswith('test_') or
                file in ['METADATA', 'RECORD', 'INSTALLER', 'WHEEL'] or
                file.endswith('.dist-info') or
                'test' in file.lower()):
                try:
                    os.remove(file_path)
                except:
                    pass

    # Remove specific large directories that aren't needed for inference
    dirs_to_remove = [
        'torch/test', 'torch/testing', 'torch/_dynamo', 'torch/profiler',
        'torchvision/datasets', 'torchvision/models/detection',
        'torchvision/models/segmentation', 'torchvision/models/video'
    ]
    
    for dir_name in dirs_to_remove:
        dir_path = os.path.join(site_packages_dir, dir_name)
        if os.path.exists(dir_path):
            print(f"Removing {dir_name}...")
            shutil.rmtree(dir_path, ignore_errors=True)

    # Remove .pyc files and __pycache__ directories
    for root, dirs, files in os.walk(site_packages_dir):
        for file in files:
            if file.endswith(('.pyc', '.pyo')):
                os.remove(os.path.join(root, file))
        
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            shutil.rmtree(os.path.join(root, '__pycache__'), ignore_errors=True)

    # Check size before zipping
    def get_size(start_path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):  # Guard against broken symlinks
                    total_size += os.path.getsize(fp)
        return total_size

    unzipped_size = get_size(temp_dir)
    print(f"Unzipped layer size: {unzipped_size / (1024*1024):.2f} MB")
    
    if unzipped_size > 250 * 1024 * 1024:  # 250MB limit
        print("WARNING: Layer might still be too large. Consider using Solution 2.")

    # Create the zip file
    zip_path = "torch_layer_optimized.zip"
    print("Creating zip file...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, temp_dir)
                zipf.write(full_path, rel_path)

    # Check final zip size
    zip_size = os.path.getsize(zip_path)
    print(f"Compressed layer size: {zip_size / (1024*1024):.2f} MB")
    print(f"Layer created: {zip_path}")
    
    shutil.rmtree(temp_dir)
    return zip_path

if __name__ == "__main__":
    create_optimized_torch_layer()