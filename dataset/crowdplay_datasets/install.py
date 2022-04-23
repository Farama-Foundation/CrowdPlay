import argparse
import os
import tarfile
import zipfile

import requests
from tqdm import tqdm

from .dataset import get_data_dir


def download_url(url):
    """
    Download a file from a url.
    """
    local_filename = url.split("/")[-1]
    response = requests.get(url, stream=True)

    total_size = int(response.headers.get("content-length", 0))
    block_size = 1024 * 1024

    with open(local_filename, "wb") as handle:
        for data in tqdm(
            response.iter_content(block_size), total=total_size // block_size, unit="MB", unit_scale=False
        ):
            handle.write(data)

    return local_filename


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="This downloads and installs a specific version of the CrowdPlay Atari dataset", add_help=True
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="crowdplay_atari-v0",
        choices=["crowdplay_atari-v0"],
        help="The dataset version to install. Currently only crowdplay_atari-v0 is available.",
    )

    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt and just install the dataset.",
    )

    args = parser.parse_args()

    # Dataset URL
    urls = {"crowdplay_atari-v0": "http://crowdplay-atari.s3-website-us-east-1.amazonaws.com/data-v0.zip"}

    # Dataset names
    dataset_ids = {"crowdplay_atari-v0": "crowdplay_atari-v0"}

    # NB: To create this zip file from a local dataset directory, run `zip -0 ../data-v0.zip *` inside the dataset/data/[dataset_id] directory

    # TODO: Check for actual file size.
    print(
        """
        You are about to download and install the CrowdPlay Atari dataset.
        For v0, this takes about 30GB of space during installation, and 15GB of space permanently.
        """
    )

    if not args.yes:  # Ask for confirmation
        if not input("Do you want to continue? [y/N] ").lower().startswith("y"):
            print("Aborting.")
            exit(0)

    print("Downloading dataset...")

    # Download the dataset zip file
    local_file = download_url(urls[args.dataset])

    print("Extracting dataset...")

    # Create the dataset directory
    os.makedirs(f"{get_data_dir()}/{dataset_ids[args.dataset]}", exist_ok=True)

    # Extract the dataset zip file
    local_zipfile = zipfile.ZipFile(local_file, "r")
    local_zipfile.extractall(f"{get_data_dir()}/{dataset_ids[args.dataset]}")
    local_zipfile.close()

    # Delete the zip file
    os.remove(local_file)

    print(f"Successfully installed into directory {get_data_dir()}/{dataset_ids[args.dataset]}.")

    print(
        """
        The dataset has been installed.

        Now, check out example code in the CrowdPlay documentation, in the examples directory,
        and in the data_analysis and offline directories of the main project.

        Trajectories are compressed using bz2, which is space-efficient but slow. If you will load trajectories many times,
        you can re-pack the dataset into gzip using the script/convert_to_gzip.sh script. Note that this requires around 250GB
        of disk space. There is an additional script to unpack the dataset entirely, but this requires around 10TB of space and
        is not noticeably faster than gzip. Run either script inside the dataset directory shown just above.
        """
    )
