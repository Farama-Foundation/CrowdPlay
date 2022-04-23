import copy
import os
import pickle
from collections import OrderedDict
from xml.dom.domreg import registered

import cv2
import numpy as np
from gym import spaces
from ray.rllib.agents.dqn.distributional_q_tf_model import DistributionalQTFModel
from ray.rllib.models import ModelCatalog
from ray.rllib.models.tf.misc import normc_initializer
from ray.rllib.models.tf.tf_modelv2 import TFModelV2
from ray.rllib.models.tf.visionnet import VisionNetwork as MyVisionNetwork
from ray.rllib.utils.framework import try_import_tf

tf1, tf, tfv = try_import_tf()

registered_ai_policies = {}


def register_ai_policy(agent_name):
    def decorator(agent_class):
        registered_ai_policies[agent_name] = agent_class

    return decorator


registered_ai_framebuffers = {}


def register_ai_framebuffer(agent_name):
    def decorator(agent_class):
        registered_ai_framebuffers[agent_name] = agent_class

    return decorator


class PretrainedRLLibA2CPolicyCustomModel:
    """
    A container for a pretrained RLLib policy loaded from a checkpoint file.
    This class abstracts away from creating the model and loading the checkpoint,
    and provides an interace to compute an action from an observation.
    """

    def __init__(self, obs_space, ac_space, checkpoint_file, checkpoint_agent_id):
        """
        Creates a PretrainedRLLibPolicy object from a checkpoint file.
        Args:
            obs_space (gym.Space): The observation space of the agent, used for constructing the policy input layers.
            ac_space (gym.Space): The action space of the agent, used for mapping neural net outputs to actions.
            checkpoint_file (string): Filename of the checkpoint file to be loaded.
            checkpoint_agent_id (string): The agent id of the agent to load from the checkpoint file.
        """

        # Import prerequisites for creating RLLib policy object and loading weights.
        import ray

        tf1, tf, tfv = ray.rllib.utils.framework.try_import_tf()

        # Register model, load default config, and set configuration for custom model.
        # TODO: Does it matter if it's A2C?
        ray.rllib.models.ModelCatalog.register_custom_model("custom_nature_cnn", CustomNatureCnn)
        config = ray.rllib.agents.a3c.a2c.A2C_DEFAULT_CONFIG.copy()
        config["model"]["custom_model"] = "custom_nature_cnn"
        config["model"]["custom_model_config"] = {"obs_space_unflat": obs_space}

        # Get preprocessor for Dict space.
        # See rollout_worker.py:1080 for source.
        # Store preprocessor as self.preprocessor so we can call it in step() for the observation.
        self.preprocessor = ray.rllib.models.ModelCatalog.get_preprocessor_for_space(obs_space, config.get("model"))
        obs_space = self.preprocessor.observation_space

        # Create a policy object.
        # Create an A3CTFPolicy, with default config except custom model.
        # We need to set a TF variable scope so that all the TF variables have the right name.
        # This is both to avoid naming conflicts with other policies.
        with tf1.variable_scope("PretrainedRLLibPolicy" + str(id(self))):
            self.policy = ray.rllib.agents.a3c.a3c_tf_policy.A3CTFPolicy(
                obs_space=obs_space, action_space=ac_space, config=config
            )

            # Load checkpoint from file.
            # Source: trainer.py:696,1014, tf_policy:478
            with open(checkpoint_file, "rb") as f:
                checkpoint_data = pickle.load(f)
            model_data = pickle.loads(checkpoint_data["worker"])["state"][checkpoint_agent_id]

            # Now rename the keys. Replace checkpoint_agent_id with agent_id, and prepend our unique ID string.
            # Apparently some checkpoint files key this by 'weights' first and others don't. Let's handle both.
            if "weights" in model_data:
                renamed_model_data = copy.deepcopy(model_data)
                renamed_model_data["weights"] = OrderedDict()
                for key in model_data["weights"]:
                    if key.startswith(checkpoint_agent_id):
                        renamed_model_data["weights"][
                            key.replace(checkpoint_agent_id, "PretrainedRLLibPolicy" + str(id(self)))
                        ] = model_data["weights"][key]
                self.policy.set_state(renamed_model_data)
            else:
                renamed_model_data = OrderedDict()
                for key in model_data:
                    if key.startswith(checkpoint_agent_id):
                        renamed_model_data[
                            key.replace(checkpoint_agent_id, "PretrainedRLLibPolicy" + str(id(self)))
                        ] = model_data[key]
                self.policy.set_weights(renamed_model_data)

    def compute_action(self, obs):
        """
        Compute a single action given an observation.

        Args:
            obs: The observation for a single agent. Needs to match obs_space passed to the constructor.
        Returns:
            A single action for a single agent.
        """
        return self.policy.compute_single_action(self.preprocessor.transform(obs))[0]


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
    Keeps a ring buffer of recent observations and calculates max-and-skipped,
    warped, stacked 84x84x4 observations from it on demand.

    This keeps a deque of recent observations (in reverse order, i.e. 0 is the most recent frame,
    1 the one before that, etc.), and calculates the correct stacked and processed observation from it:
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
            skip_n (int, optional): Number of frames to skip between stacked frames, i.e. return frames
                (0, skip_n, 2*skip_n, ...). For the default deepmind behavior of "max 2, skip 2", set this to 4.
                Default 4.
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
        for key in new_observation_space.spaces.keys():
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


class DummyFramebuffer:
    """
    A dummy "framebuffer" that just returns the current observation
    """

    def __init__(
        self,
        observation_space,
    ):
        # Create a dummy obs in case get_obs() is called before add_obs()
        self.obs = {
            key: np.zeros(
                observation_space[key].shape,
                dtype=np.uint8,
            )
            for key in observation_space.spaces
        }

    def add_obs(self, observation):
        self.obs = observation

    def get_obs(self):
        return self.obs


class CustomNatureCnn(TFModelV2):
    """
    Custom model replicating the baselines Nature CNN model.
    This uses a CNN for each image input, and then concatenates all CNN outputs plus any non-image inputs.
    TODO: settle on a way to identify image inputs. For now: keys starting with "image"
    """

    def __init__(self, obs_space, action_space, num_outputs, model_config, name, **customized_model_kwargs):
        super(CustomNatureCnn, self).__init__(obs_space, action_space, num_outputs, model_config, name)

        # We do get the unflattened observation space from RLLib as obs_space.original_space.
        if hasattr(obs_space, "original_space"):
            obs_space_unflat = obs_space.original_space
        else:
            obs_space_unflat = obs_space

        activation = tf.nn.relu

        def cnn(input_layer):
            conv1 = tf.keras.layers.Conv2D(
                32,
                [8, 8],
                strides=(4, 4),
                activation=activation,
                padding="same",
                data_format="channels_last",
                name="conv1",
            )(input_layer)
            conv2 = tf.keras.layers.Conv2D(
                64,
                [4, 4],
                strides=(2, 2),
                activation=activation,
                padding="same",  # TODO same or valid?
                data_format="channels_last",
                name="conv2",
            )(conv1)
            conv3 = tf.keras.layers.Conv2D(
                64,
                [3, 3],
                strides=(1, 1),
                activation=activation,
                padding="valid",
                data_format="channels_last",
                name="conv3",
            )(conv2)
            conv_to_fc = tf.keras.layers.Flatten()(conv3)
            return conv_to_fc

        # Create input or input+CNN layers for each item in obs_space dict.
        # TODO how do we detect CNN vs plain input? By shape, or by name? For now by name starting with "image"
        inputs = {}
        post_cnn = []
        for name in obs_space_unflat.spaces.keys():
            space = obs_space_unflat[name]
            inputs[name] = tf.keras.layers.Input(shape=space.shape, name="input_{}".format(name))
            if name.startswith("image"):
                post_cnn.append(cnn(inputs[name]))
            else:
                post_cnn.append(inputs[name])
        # Concatenate all CNN outputs and non-image inputs.
        # If there is only a single item in the post_cnn list, TF Concatenate()
        # fails, so we handle that case separately.
        if len(post_cnn) > 1:
            conv_and_bvals = tf.keras.layers.Concatenate()(post_cnn)
        else:
            conv_and_bvals = post_cnn[0]
        fc1 = tf.keras.layers.Dense(
            512,
            name="fc_1",
            activation=activation,
            kernel_initializer=normc_initializer(1.0),
        )(conv_and_bvals)
        # End of nature_cnn in baselines code
        value_out = tf.keras.layers.Dense(
            1,
            name="value_out",
            activation=None,
            kernel_initializer=normc_initializer(0.01),
        )(fc1)
        action_out = tf.keras.layers.Dense(
            num_outputs,
            name="action_out",
            activation=None,
            kernel_initializer=normc_initializer(0.01),
        )(fc1)
        input_list = list(inputs.values())

        self.base_model = tf.keras.Model(input_list, [action_out, value_out])
        self.register_variables(self.base_model.variables)

    def forward(self, input_dict, state, seq_lens):
        action_out, self._value_out = self.base_model(
            [tf.cast(input_dict["obs"][name], tf.float32) for name in input_dict["obs"]]
        )
        return action_out, state

    def value_function(self):
        return tf.reshape(self._value_out, [-1])


@register_ai_policy("si-coop-0")
class SICoopAgent0(PretrainedRLLibA2CPolicyCustomModel):
    def __init__(self):
        super().__init__(
            spaces.Dict({"image": spaces.Box(0, 255, (84, 84, 4), np.uint8)}),
            spaces.Dict({"game": spaces.Discrete(6)}),
            os.path.dirname(os.path.realpath(__file__)) + "/checkpoint/" + "si-coop.checkpoint",
            "game_0>player_0",
        )


@register_ai_policy("si-coop-1")
class SICoopAgent1(PretrainedRLLibA2CPolicyCustomModel):
    def __init__(self):
        super().__init__(
            spaces.Dict({"image": spaces.Box(0, 255, (84, 84, 4), np.uint8)}),
            spaces.Dict({"game": spaces.Discrete(6)}),
            os.path.dirname(os.path.realpath(__file__)) + "/checkpoint/" + "si-coop.checkpoint",
            "game_0>player_1",
        )


@register_ai_policy("si-comp-0")
class SICompAgent0(PretrainedRLLibA2CPolicyCustomModel):
    def __init__(self):
        super().__init__(
            spaces.Dict({"image": spaces.Box(0, 255, (84, 84, 4), np.uint8)}),
            spaces.Dict({"game": spaces.Discrete(6)}),
            os.path.dirname(os.path.realpath(__file__)) + "/checkpoint/" + "si-comp.checkpoint",
            "game_0>player_0",
        )


@register_ai_policy("si-comp-1")
class SICompAgent1(PretrainedRLLibA2CPolicyCustomModel):
    def __init__(self):
        super().__init__(
            spaces.Dict({"image": spaces.Box(0, 255, (84, 84, 4), np.uint8)}),
            spaces.Dict({"game": spaces.Discrete(6)}),
            os.path.dirname(os.path.realpath(__file__)) + "/checkpoint/" + "si-comp.checkpoint",
            "game_0>player_1",
        )


@register_ai_framebuffer("si-coop-0")
@register_ai_framebuffer("si-coop-1")
@register_ai_framebuffer("si-comp-0")
@register_ai_framebuffer("si-comp-1")
class AtariFB(MaxAndSkipAndWarpAndScaleAndStackFrameBuffer):
    def __init__(self):
        super().__init__(spaces.Dict({"image": spaces.Box(0, 255, (210, 160, 3), np.uint8)}))
