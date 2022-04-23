import os
from collections import OrderedDict, defaultdict
from numbers import Number
from typing import Callable, List, Optional, Tuple, Union

import gym
import multi_agent_ale_py
import numpy as np
from gym import spaces, utils
from gym.utils import seeding
from ray.rllib.env.multi_agent_env import MultiAgentEnv
from ray.rllib.utils.typing import AgentID, MultiAgentDict

"""
This file contains a basic multiagent Atari environment and several useful wrappers for it.
The code for this is taken from a separate research project and will be released as a standalone package soon.
In the mean time, we include it here to allow for recreation of the environments we used in the CrowdPLay ICLR paper,
and to serve as a demonstration of multiagent environments in CrowdPlay.
"""

ACTION_MEANING = {
    0: "NOOP",
    1: "FIRE",
    2: "UP",
    3: "RIGHT",
    4: "LEFT",
    5: "DOWN",
    6: "UPRIGHT",
    7: "UPLEFT",
    8: "DOWNRIGHT",
    9: "DOWNLEFT",
    10: "UPFIRE",
    11: "RIGHTFIRE",
    12: "LEFTFIRE",
    13: "DOWNFIRE",
    14: "UPRIGHTFIRE",
    15: "UPLEFTFIRE",
    16: "DOWNRIGHTFIRE",
    17: "DOWNLEFTFIRE",
}
GAME_ACTION_KEY = "game"
RAM_OBS_KEY = "ram"
IMAGE_OBS_KEY = "image"
OBS_TYPES = [RAM_OBS_KEY, IMAGE_OBS_KEY]


class MultiAgentAtariGame(MultiAgentEnv, gym.Env, utils.EzPickle):

    metadata = {"render.modes": ["human", "rgb_array"]}

    def __init__(
        self,
        game: Optional[str] = "space_invaders",
        num_players: Optional[int] = 1,
        repeat_action_probability: Optional[float] = 0.0,
        obs_type: Optional[str] = IMAGE_OBS_KEY,
        max_frames: Optional[int] = 100000,
        seed: Optional[int] = None,
        rank: Optional[int] = 0,
    ):
        utils.EzPickle.__init__(
            self,
            game,
            num_players,
            repeat_action_probability,
            obs_type,
            max_frames,
            seed,
        )

        assert obs_type in OBS_TYPES, f"obs_type must either be one of {OBS_TYPES}"
        self.obs_type = obs_type
        self.max_frames = max_frames
        self.games = [self]
        self.num_games = 1

        multi_agent_ale_py.ALEInterface.setLoggerMode("error")
        self.ale = multi_agent_ale_py.ALEInterface()

        self.ale.setFloat(b"repeat_action_probability", repeat_action_probability)

        pathstart = os.path.dirname(multi_agent_ale_py.__file__)
        final_path = os.path.join(pathstart, "roms", game + ".bin")
        if not os.path.exists(final_path):
            raise IOError(
                "rom {} is not installed. Please install roms using AutoROM tool"
                " (https://github.com/PettingZoo-Team/AutoROM)".format(game)
            )

        self.rom_path = final_path
        self.ale.loadROM(self.rom_path)

        all_modes = self.ale.getAvailableModes(num_players)
        if len(all_modes) == 0:
            raise IOError(f"rom {game} does not support num_players = {num_players}")
        self.mode = all_modes[0]
        self.ale.setMode(self.mode)
        assert num_players == self.ale.numPlayersActive()

        action_mapping = self.ale.getMinimalActionSet()
        action_size = len(action_mapping)

        self.action_mapping = action_mapping

        if obs_type == RAM_OBS_KEY:
            observation_space = spaces.Box(low=0, high=255, dtype=np.uint8, shape=(128,))
        else:
            (screen_width, screen_height) = self.ale.getScreenDims()
            num_channels = 3
            observation_space = spaces.Box(
                low=0,
                high=255,
                shape=(screen_height, screen_width, num_channels),
                dtype=np.uint8,
            )

        self.rank = rank
        self.num_players = num_players
        self.list_of_agents = [f"game_{rank}>player_{n}" for n in range(self.num_players)]

        self.action_space = {
            player: spaces.Dict({GAME_ACTION_KEY: spaces.Discrete(action_size)}) for player in self.list_of_agents
        }
        self.observation_space = {
            player: spaces.Dict({self.obs_type: observation_space}) for player in self.list_of_agents
        }

        self._screen = None
        self.seed(seed)

    def seed(self, seed: Optional[int] = None):
        if seed is None:
            seed = seeding.create_seed(seed, max_bytes=4)
        self.ale.setInt(b"random_seed", seed)
        self.ale.loadROM(self.rom_path)
        self.ale.setMode(self.mode)

    def reset(self) -> MultiAgentDict:
        self.ale.reset_game()
        self.frame = 0

        obs = self._observe()
        return {player: OrderedDict([(self.obs_type, obs)]) for player in self.list_of_agents}

    def _observe(self):
        if self.obs_type == RAM_OBS_KEY:
            ram_bytes = self.ale.getRAM()
            return ram_bytes
        elif self.obs_type == IMAGE_OBS_KEY:
            return self.ale.getScreenRGB()

    def step(
        self, action_dict: MultiAgentDict
    ) -> Tuple[MultiAgentDict, MultiAgentDict, MultiAgentDict, MultiAgentDict]:
        actions = np.zeros(self.num_players, dtype=np.int32)
        for i, player in enumerate(self.list_of_agents):
            if player in action_dict:
                actions[i] = action_dict[player][GAME_ACTION_KEY]

        actions = self.parse_action(actions)
        rewards = self.ale.act(actions)
        if self.ale.game_over() or self.frame >= self.max_frames:
            dones = {player: True for player in self.list_of_agents}
            dones["__all__"] = True
        else:
            lives = self.ale.allLives()
            # an inactive player in ale gets a -1 life.
            dones = {player: int(life) < 0 for (player, life) in zip(self.list_of_agents, lives)}
            dones["__all__"] = False

        self.frame += 1
        obs = self._observe()
        observations = {player: OrderedDict([(self.obs_type, obs)]) for player in self.list_of_agents}
        rewards = {player: reward for (player, reward) in zip(self.list_of_agents, rewards)}
        infos = {player: {"ale.lives": life} for (player, life) in zip(self.list_of_agents, self.ale.allLives())}
        return observations, rewards, dones, infos

    def render(self, mode: Optional[str] = "human", zoom_factor: Optional[int] = 4):
        assert mode in self.metadata["render.modes"], f"Unsupported render mode: {mode}"
        image = self.ale.getScreenRGB()
        if mode == "human":
            (screen_width, screen_height) = self.ale.getScreenDims()

            import pygame

            if self._screen is None:
                pygame.init()
                self._screen = pygame.display.set_mode((screen_width * zoom_factor, screen_height * zoom_factor))

            game_surface = pygame.image.fromstring(image.tobytes(), image.shape[:2][::-1], "RGB")
            game_surface = pygame.transform.scale(
                game_surface, (screen_width * zoom_factor, screen_height * zoom_factor)
            )
            self._screen.blit(game_surface, (0, 0))

            pygame.display.flip()
        else:
            # rgb_array
            return image

    def close(self) -> None:
        if self._screen is not None:
            import pygame

            pygame.quit()
            self._screen = None

    def parse_action(self, actions: List[int]) -> List[int]:
        """Translate a list of incoming action indices to valid ALE actions

        Args:
            actions: A list of incoming action indices.

        Returns:
            A list of valid actions to play the game.
        """
        return self.action_mapping[actions]

    def get_ale_action_index(self, actions: List[int]) -> List[int]:
        """Get the corresponding action indices of ALE actions
        Args:
            action: A list of ALE actions

        Returns:
            A list of action indices
        """
        return [np.flatnonzero(a == self.action_mapping)[0] for a in actions]

    def get_action_meanings(self) -> List[str]:
        return [ACTION_MEANING[i] for i in self.action_mapping]

    @property
    def unwrapped(self) -> MultiAgentEnv:
        return self

    def __getitem__(self, index: int) -> MultiAgentEnv:
        return self.games[index]


class MultiAgentEnvWrapper(MultiAgentEnv):
    """Base wrapper class of MultiAgentEnv"""

    def __init__(self, env: MultiAgentEnv, stats_descriptor: Optional[str] = None):
        """Initializes a new MultiAgentEnvWrapper

        Args:
            env (MultiAgentEnv): The environment to wrap.
            stats_descriptor (Optional[str]): The descriptor of wrapper's statistics.
        """
        self.env = env
        self.stats_descriptor = stats_descriptor
        self.action_space = self.env.action_space
        self.observation_space = self.env.observation_space
        self.metadata = self.env.metadata
        self.num_players = self.env.num_players
        self.list_of_agents = self.env.list_of_agents

    def __getattr__(self, name: str):
        return getattr(self.env, name)

    def step(self, actions: MultiAgentDict) -> Tuple[MultiAgentDict, MultiAgentDict, MultiAgentDict, MultiAgentDict]:
        return self.env.step(actions)

    def _reset(self) -> MultiAgentDict:
        self._wrapper_stats.clear()
        self._stats_aggregation_type.clear()

    def reset(self) -> MultiAgentDict:
        self._reset()
        return self.env.reset()

    def render(self, mode: Optional[str] = "human", zoom_factor: Optional[int] = 2):
        return self.env.render(mode, zoom_factor)

    def close(self) -> None:
        return self.env.close()

    def __str__(self) -> str:
        return "<{}{}>".format(type(self).__name__, self.env)

    def __repr__(self) -> str:
        return str(self)

    @property
    def unwrapped(self) -> MultiAgentEnv:
        return self.env.unwrapped

    def get_game_rank(self, player_name: AgentID) -> int:
        game_rank = player_name.split(">")[0]
        rank = int(game_rank.split("_")[-1])
        return rank

    def get_player_number(self, player_name: AgentID) -> int:
        player_number = player_name.split(">")[-1]
        number = int(player_number.split("_")[-1])
        return number


class SpaceInvadersLives(MultiAgentEnvWrapper):
    """This wrapper penalizes an agent for losing a life, and awards a bonus to other agent
    in that SpaceInvaders instance if it is a two player game."""

    # This wrapper should be placed before clip reward wrapper in env.py
    def __init__(self, env: MultiAgentEnv, bonus: Optional[int] = 200, penalty: Optional[int] = 0):
        assert bonus >= 0 and penalty >= 0, "Bonus and penalty both should be nonnegative numbers."
        super(SpaceInvadersLives, self).__init__(env)
        assert (
            len(self.list_of_agents) == 1 or len(self.list_of_agents) == 2
        ), "The SpaceInvadersLives wrapper only supports a single one player/two player game"
        self.lives = dict(zip(self.list_of_agents, self.ale.allLives()))
        self.penalty = penalty
        self.bonus = bonus

    def step(self, ac: MultiAgentDict) -> Tuple[MultiAgentDict, MultiAgentDict, MultiAgentDict, MultiAgentDict]:
        obs, reward, done, info = self.env.step(ac)
        # If it's a single two player game
        if len(self.list_of_agents) == 2:
            for player in self.list_of_agents:
                # The only case where a higher than 200 unclipped reward occurs
                # is the other agent being shot in a two player game
                if reward[player] >= 200:
                    for agent in self.list_of_agents:
                        if agent == player:
                            reward[agent] += self.bonus - 200  # 200 is the default bonus
                        else:
                            reward[agent] -= self.penalty
        # If it's a single one player game
        elif len(self.list_of_agents) == 1:
            for player, life in zip(self.list_of_agents, self.ale.allLives()):
                if life != self.lives[player]:
                    self.lives[player] = life
                    # Penalize lives lost
                    reward[player] -= self.penalty
        return obs, reward, done, info

    def reset(self) -> MultiAgentDict:
        # Call the wrapped environments reset function.
        obs = self.env.reset()
        self.lives = dict(zip(self.list_of_agents, self.ale.allLives()))
        # Return the observations.
        return obs


class SpaceInvadersRandomInitialPositions(MultiAgentEnvWrapper):
    def __init__(self, env):
        super(SpaceInvadersRandomInitialPositions, self).__init__(env)
        rand_pos1 = np.random.randint(0x23, 0x76)
        rand_pos2 = np.random.randint(0x23, 0x76)
        self.unwrapped.ale.setRAM(0x1C, rand_pos1)
        self.unwrapped.ale.setRAM(0x1D, rand_pos2)

        # Keep track of lives so we can randomise positions after a live is lost too (SI resets them at that point.)
        self._lives = 0

    def reset(self):
        # Call the wrapped environments reset function.
        obs = self.env.reset()

        rand_pos1 = np.random.randint(0x23, 0x76)
        rand_pos2 = np.random.randint(0x23, 0x76)
        self.unwrapped.ale.setRAM(0x1C, rand_pos1)
        self.unwrapped.ale.setRAM(0x1D, rand_pos2)

        self._lives = self.ale.lives()

        # Return the observations.
        return obs

    def step(self, ac):
        # Randomise positions after live is lost.
        if self.ale.lives() < self._lives:
            self._lives = self.ale.lives()
            rand_pos1 = np.random.randint(0x23, 0x76)
            rand_pos2 = np.random.randint(0x23, 0x76)
            self.unwrapped.ale.setRAM(0x1C, rand_pos1)
            self.unwrapped.ale.setRAM(0x1D, rand_pos2)
        return self.env.step(ac)


class SumRewards(MultiAgentEnvWrapper):
    """Return sum of rewards to all agents."""

    def step(self, ac: MultiAgentDict) -> Tuple[MultiAgentDict, MultiAgentDict, MultiAgentDict, MultiAgentDict]:
        obs, reward, done, info = self.env.step(ac)
        reward_sum = sum(reward.values())
        for key in reward:
            reward[key] = reward_sum
        return obs, reward, done, info
