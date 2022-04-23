---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
title: Installation
nav_order: 1
parent: CrowdPlay Atari Dataset
layout: default
---

## Installing the CrowdPlay Atari Dataset

### 1. Installing the Python Package

Run ```pip install crowdplay_datasets``` to install the dataset package.

### 2. Downloading and Extracting the Dataset

Then, run `python -m crowdplay_datasets.install --dataset=crowdplay_atari-v0` to download and extract the actual dataset. The dataset is about 15GB in size, but during installation will temporarily require about 30GB of disk space.

### 3. Optional: Re-pack into Gzip

Trajectories are compressed using bzip, which is space-efficient but slow. If you will load trajectories many times, you can re-pack the dataset into gzip using the `scripts/convert_to_gzip.sh` script. Note that this requires around 250GB of disk space. There is an additional script to unpack the dataset entirely, but this requires around 10TB of space and is not noticeably faster than gzip. Run either script inside the dataset directory (shown during installation).
