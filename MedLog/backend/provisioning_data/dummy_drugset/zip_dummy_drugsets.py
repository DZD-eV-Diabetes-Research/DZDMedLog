import os
import zipfile
from pathlib import Path


def zip_drugset_directories():
    """
    Helperscript for dev/debuging/testing. To emulate remote update-downloading of the drug database, we zip the drugset and serve it on a local FTP Server.
    This script just zip the dummy drugdata.
    Its zips the content of each directory in dummy_drugset into separate zip files.
    Each zip file is placed in a subdirectory within 'zipped' that matches the source directory name.
    The zip file itself also has the same name as the source directory.
    Existing zip files are overwritten.
    """
    # Define paths
    source_dir = Path(
        Path(__file__).parent.parent.parent, "provisioning_data/dummy_drugset"
    )
    zipped_base_dir = source_dir / "zipped"
    print(f"ZIP Dummy drugdataset to {zipped_base_dir.absolute()}...")

    # Create base zipped directory if it doesn't exist
    zipped_base_dir.mkdir(parents=True, exist_ok=True)

    # Iterate through items in the source directory
    for item in source_dir.iterdir():
        # Skip if not a directory or if it's the zipped directory itself
        if not item.is_dir() or item.name == "zipped":
            continue

        # Create subdirectory in zipped folder named after the source directory
        output_subdir = zipped_base_dir / item.name
        output_subdir.mkdir(parents=True, exist_ok=True)

        # Create zip file path
        zip_path = output_subdir / f"{item.name}.zip"

        # Remove existing zip file if it exists
        if zip_path.exists():
            print(f"Overwriting existing {zip_path}...")
            zip_path.unlink()
        else:
            print(f"Zipping {item.name}...")

        # Create zip file
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the directory
            for root, dirs, files in os.walk(item):
                for file in files:
                    file_path = Path(root) / file
                    # Calculate relative path from the directory being zipped
                    arcname = file_path.relative_to(item)
                    zipf.write(file_path, arcname)

        print(f"Created {zip_path}")

    print("All directories zipped successfully!")


if __name__ == "__main__":
    zip_drugset_directories()
