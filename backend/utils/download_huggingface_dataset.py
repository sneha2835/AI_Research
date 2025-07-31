import subprocess
import os

def download_and_extract_huggingface():
    # Define paths relative to this script (adjust if running from elsewhere)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    datasets_dir = os.path.join(base_dir, "datasets")
    extract_dir = os.path.join(datasets_dir, "research-papers")

    os.makedirs(datasets_dir, exist_ok=True)
    os.makedirs(extract_dir, exist_ok=True)

    tar_path = os.path.join(datasets_dir, "research-papers.tar")

    print("Downloading HuggingFace research papers tarball...")
    subprocess.run([
        'curl', '-L',
        'https://huggingface.co/datasets/khushwant04/Research-Papers/resolve/main/research-papers.tar?download=true',
        '-o', tar_path
    ], check=True)
    
    print(f"Extracting tarball into {extract_dir} ...")
    subprocess.run([
        'tar', '-xf', tar_path,
        '-C', extract_dir
    ], check=True)

    print("Download and extraction complete.")

if __name__ == "__main__":
    download_and_extract_huggingface()
