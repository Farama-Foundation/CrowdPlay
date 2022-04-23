from collections import OrderedDict

import numpy as np
from gym import Wrapper, spaces

from .multiagent_atari import MultiAgentEnvWrapper


class MaxFrameAndRAMWrapper(MultiAgentEnvWrapper):
    """This wrapper takes the pixel-wise maximum of every two consecutive frames,
    which improves visual performance for end users.
    Additionally, it stores the ALE RAM array into the info object for each agent every frame.
    This version assumes that the observation is an image as a numpy array."""

    def __init__(self, env):
        MultiAgentEnvWrapper.__init__(self, env)
        self.previous_frame = {agent: np.zeros(self.env.observation_space[agent].shape) for agent in env.list_of_agents}

        self.processed_obs = {agent: {} for agent in env.list_of_agents}

    def reset(self, **kwargs):
        obs = self.env.reset(**kwargs)
        for agent in obs:
            maxed_frame = np.maximum(obs[agent], self.previous_frame[agent])
            self.previous_frame[agent] = obs[agent]
            self.processed_obs[agent] = obs[agent].copy()
            self.processed_obs[agent] = maxed_frame
        return obs

    def step(self, ac):
        obs, reward, done, info = self.env.step(ac)
        for agent in obs:
            maxed_frame = np.maximum(obs[agent], self.previous_frame[agent])
            self.previous_frame[agent] = obs[agent]
            self.processed_obs[agent] = obs[agent].copy()
            self.processed_obs[agent] = maxed_frame
            info[agent]["RAM"] = self.unwrapped.ale.getRAM().tolist()
        return obs, reward, done, info

    def crowdplay_render(self):
        return self.processed_obs


class MaxFrameAndRAMWrapperMultiagent(MultiAgentEnvWrapper):
    """This wrapper takes the pixel-wise maximum of every two consecutive frames,
    which improves visual performance for end users.
    Additionally, it stores the ALE RAM array into the info object for each agent every frame.
    This version assumes that the observation is a dictionary. Pixel-wise maxing is done on the 'image' key."""

    def __init__(self, env):
        MultiAgentEnvWrapper.__init__(self, env)
        self.previous_frame = {
            agent: np.zeros(self.env.observation_space[agent]["image"].shape) for agent in env.list_of_agents
        }

        self.processed_obs = {agent: {} for agent in env.list_of_agents}

    def reset(self, **kwargs):
        obs = self.env.reset(**kwargs)
        for agent in obs:
            maxed_frame = np.maximum(obs[agent]["image"], self.previous_frame[agent])
            self.previous_frame[agent] = obs[agent]["image"]
            self.processed_obs[agent] = obs[agent].copy()
            self.processed_obs[agent]["image"] = maxed_frame
        return obs

    def step(self, ac):
        obs, reward, done, info = self.env.step(ac)
        for agent in obs:
            maxed_frame = np.maximum(obs[agent]["image"], self.previous_frame[agent])
            self.previous_frame[agent] = obs[agent]["image"]
            self.processed_obs[agent] = obs[agent].copy()
            self.processed_obs[agent]["image"] = maxed_frame
            info[agent]["RAM"] = self.unwrapped.ale.getRAM().tolist()
        return obs, reward, done, info

    def crowdplay_render(self):
        return self.processed_obs


def is_atari(env):
    if (
        hasattr(env.observation_space, "shape")
        and env.observation_space.shape is not None
        and len(env.observation_space.shape) <= 2
    ):
        return False
    return hasattr(env, "unwrapped") and hasattr(env.unwrapped, "ale")


class GymToCrowdPlay(Wrapper):
    """This wrapper wraps Gym environments so that the actions and
    observations are the right (dict) format for CrowdPlay"""

    def __init__(self, env):
        super().__init__(env)
        # TODO check other observation types
        self.obs_key = "image" if is_atari(env) else "obs"
        self.observation_space = {"agent_0": self.env.observation_space}
        self.action_space = {"agent_0": env.action_space}

        self.num_players = 1
        self.list_of_agents = [
            "agent_0",
        ]

        self.obs = self.env.reset()

    def reset(self):
        obs = self.env.reset()
        self.obs = obs
        return {"agent_0": obs}

    def step(self, action):
        obs, reward, done, info = self.env.step(action["agent_0"])
        self.obs = obs
        return (
            {"agent_0": obs},
            {"agent_0": reward},
            {"agent_0": done},
            {"agent_0": info},
        )

    def crowdplay_render(self):
        # Override render function of Gym base env, which doesn't work with CrowdPlay
        return {"agent_0": OrderedDict({self.obs_key: self.obs})}

    def get_noop_action(self, agent):
        def get_noop_for_space(space):
            if isinstance(space, spaces.Box):
                return np.zeros(space.shape)
            if isinstance(space, spaces.Discrete):
                return 0
            if isinstance(space, spaces.Dict):
                return {key: get_noop_for_space(space.spaces[key]) for key in space}
            if isinstance(space, spaces.MultiDiscrete):
                return np.zeros(space.shape)
            if isinstance(space, spaces.MultiBinary):
                return np.zeros(space.n)
            if isinstance(space, spaces.Tuple):
                return [get_noop_for_space(s) for s in space.spaces]
            return 0

        return get_noop_for_space(self.action_space[agent])


class RenderTaxi(Wrapper):
    """This returns the rendered output from the unwrapped environment, useful for Taxi-v3"""

    def crowdplay_render(self):
        return {"agent_0": self.unwrapped.render(mode="ansi")}


class RenderPendulum(Wrapper):
    """This returns the rendered output from the unwrapped environment, useful for e.g. Pendulum"""

    def crowdplay_render(self):
        return {"agent_0": self.unwrapped.render(mode="rgb_array")}
