import copy

import cv2
import numpy as np
from gym import spaces


def partition(pred, iterable):
    trues = []
    falses = []
    for item in iterable:
        if pred(*item):
            trues.append(item[0])
        else:
            falses.append(item[0])
    return trues, falses


def get_image_keys(observation_dict, img_prefix="image"):
    return partition(
        lambda k, v: k.startswith(img_prefix) and len(v.shape) >= 3,
        observation_dict.items(),
    )


class MaxAndSkipAndWarpAndScaleAndStackFrameBuffer:
    """
    Keeps a ring buffer of recent observations and calculates max-and-skipped, warped, stacked 84x84x4 observations from it on demand.

    This keeps a deque of recent observations (in reverse order, i.e. 0 is the most recent frame, 1 the one before that, etc.),
    and calculates the correct stacked and processed observation from it:
    -------------------------------------------------------
    |  0  |  1  |  2  |  3  |  4  |  5  |  6  |  7  |  8  |
    -------------------------------------------------------
     [---max---],
           [---max---],
                  [---max---], ...

    In code: (
        max( 0, 1, ... , max_n - 1 ),
        max( skip_n, skip_n + 1, ... , skip_n + max_n - 1),
        ...,
        max( stack_n*skip_n, stack_n*skip_n + 1, ... , stack_n*skip_n + max_n - 1)
    )
    """

    def __init__(
        self,
        observation_space,
        max_n=2,
        skip_n=4,
        stack_n=4,
        warp=True,
        scale=False,
        warp_width=84,
        warp_height=84,
    ):
        """
        Constructs a MaxAndSkipAndWarpAndScaleAndStackFrameBuffer object.

        Args:
            observation_space (gym.Space): The observation space. Must be a Dict, does not support nested Dicts.
            max_n (int, optional): Number of consecutive frames to take the maximum of, default 2.
            skip_n (int, optional): Number of frames to skip between stacked frames, i.e. return frames (0, skip_n, 2*skip_n, ...).
                For the default deepmind behavior of "max 2, skip 2", set this to 4. Default 4.
            stack_n (int, optional): How many consecutive frames to stack, spaced skip_n apart. Default 4.
            warp (bool, optional): Warp frames identified by image keys into 84x84 grayscale? Default True.
            scale (bool, optional): Scale pixel values to (0,1) float, or leave integers. Default False.
            warp_width, warp_height (int, optional): Resolution to scale the image frames to. Default 84x84.
        """

        # Set object variables
        self.max_n = max_n
        self.skip_n = skip_n
        self.stack_n = stack_n
        self.length = (stack_n - 1) * skip_n + max_n
        self.warp = warp
        self.scale = scale
        self._unprocessed_observation_space = observation_space
        self.warp_width = warp_width
        self.warp_height = warp_height

        # Set image and other keys:
        self.image_keys, self.other_keys = get_image_keys(self._unprocessed_observation_space.spaces)

        # Create a buffer of size stack_n*skip_n + max_n for every key in the observation space
        self._obs_buffer = {
            key: np.zeros(
                ((self.length),) + self._unprocessed_observation_space[key].shape,
                dtype=np.uint8,
            )
            for key in self._unprocessed_observation_space.spaces
        }

        self._pointer = 0

    def get_observation_space(self):
        """
        This returns the processed observation space.
        """
        new_observation_space = copy.deepcopy(self._unprocessed_observation_space)
        # From warp frame:
        for image_key in self.image_keys:
            new_observation_space.spaces[image_key] = spaces.Box(
                low=0,
                high=255,
                shape=(self.warp_height, self.warp_width, 1),
                dtype=np.uint8,
            )
        # From frame stack:
        for key in new_observation_space.spaces:
            current_key_space = new_observation_space[key]
            new_key_shape = list(current_key_space.shape)
            new_key_shape[-1] *= self.stack_n
            new_key_shape = tuple(new_key_shape)
            if key in self.image_keys:
                new_key_low = 0
                new_key_high = 255
            else:
                new_key_low = np.repeat(current_key_space.low, self.stack_n)
                new_key_high = np.repeat(current_key_space.high, self.stack_n)
            new_key_space = spaces.Box(
                low=new_key_low,
                high=new_key_high,
                shape=new_key_shape,
                dtype=current_key_space.dtype,
            )
            new_observation_space.spaces[key] = new_key_space
        return new_observation_space

    def add_obs(self, observation):
        """
        Add a single unprocessed observation to the buffer.

        Args:
        observation (Dict): A single agent's observation, as a dict.
        """
        self._pointer = (self._pointer - 1) % self.length
        for key in observation:
            self._obs_buffer[key][self._pointer] = observation[key]

    def _warp_frame(self, frame):
        """Downsamples and grayscales an image."""
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        frame = cv2.resize(frame, (self.warp_width, self.warp_height), interpolation=cv2.INTER_AREA)
        frame = frame[:, :, None]
        return frame

    def _get_single_obs_from_key(self, key, index):
        """
        Returns a single observation for key `key` at index `index`, e.g. the max of two consecutive `image` frames.
        """
        if key in self.image_keys:
            frame = np.take(
                self._obs_buffer[key],
                range(index, index + self.max_n),
                axis=0,
                mode="wrap",
            ).max(axis=0)
            if self.warp:
                frame = self._warp_frame(frame)
            if self.scale:
                frame = np.array(frame).astype(np.float32) / 255.0
            return frame
        else:
            return self._obs_buffer[key][index % self.length, ...]

    def get_obs(self):
        """
        Returns the most recent processed and stacked observation, given the current state of the observation buffer.

        Returns:
            A processed observation.
        """
        return {
            key: np.concatenate(
                [
                    self._get_single_obs_from_key(
                        key,
                        self._pointer + ((self.stack_n - 1) * self.skip_n) - (i * self.skip_n),
                    )
                    for i in range(self.stack_n)
                ],
                axis=-1,
            )
            for key in self._unprocessed_observation_space.spaces
        }

    def reset(self):
        """Reset obs buffer at beginning of episode."""
        self._reset = True
        for key in self._unprocessed_observation_space.spaces:
            self._obs_buffer[key] = np.zeros(
                ((self.length),) + self._unprocessed_observation_space[key].shape,
                dtype=np.uint8,
            )
