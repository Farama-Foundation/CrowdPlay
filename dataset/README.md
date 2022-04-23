# The CrowdPlay Atari Dataset

The CrowdPlay Atari dataset is a collection of over 300 hours of human Atari 2600 demonstrations. In addition to vanilla gameplay, it includes substantial amounts of multiagent data, including human-human and human-AI data, as well as multimodal behavioral data, where participants were asked to follow a specific behavior in the game.

## Installing the CrowdPlay Atari Dataset

### 1. Installing the Python Package

Run ```pip install crowdplay_datasets``` to install the dataset package.

### 2. Downloading and Extracting the Dataset

Then, run `python -m crowdplay_datasets.install --dataset=crowdplay_atari-v0` to download and extract the actual dataset. The dataset is about 15GB in size, but during installation will temporarily require about 30GB of disk space.

### 3. Optional: Re-pack into Gzip

Trajectories are compressed using bzip, which is space-efficient but slow. If you will load trajectories many times, you can re-pack the dataset into gzip using the `scripts/convert_to_gzip.sh` script. Note that this requires around 250GB of disk space. There is an additional script to unpack the dataset entirely, but this requires around 10TB of space and is not noticeably faster than gzip. Run either script inside the dataset directory (shown during installation).

## More Information

For more information see [https://mgerstgrasser.github.io/crowdplay/](https://mgerstgrasser.github.io/crowdplay/).
