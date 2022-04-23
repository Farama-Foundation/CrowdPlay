import argparse
import os
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import d3rlpy
import gym
import numpy as np
from crowdplay_datasets.dataset import (
    EnvironmentModel,
    EpisodeKeywordDataModel,
    EpisodeModel,
    get_engine_and_session,
)
from crowdplay_datasets.deepmind import MaxAndSkipAndWarpAndScaleAndStackFrameBuffer
from d3rlpy.envs import ChannelFirst
from sklearn.model_selection import train_test_split


class DeepmindEverystep(gym.Wrapper):
    """
    Uses a framebuffer to replicate deepmind observation processing, but does so every step instead of every 4 steps.
    """

    def __init__(
        self,
        env,
        max_n: Optional[int] = 2,
        skip_n: Optional[int] = 4,
        stack_n: Optional[int] = 4,
        warp: bool = True,
        scale: bool = False,
        warp_width: Optional[int] = 84,
        warp_height: Optional[int] = 84,
    ):
        """
        Constructs a DeepmindEverystep wrapper object.

        Args:
            max_n (int, optional): Number of consecutive frames to take the maximum of, default 2.
            skip_n (int, optional): Number of frames to skip between stacked frames, i.e. return frames (0, skip_n, 2*skip_n, ...).
                For the default deepmind behavior of "max 2, skip 2", set this to 4. Default 4.
            stack_n (int, optional): How many consecutive frames to stack, spaced skip_n apart. Default 4.
            warp (bool, optional): Warp frames identified by image keys into 84x84 grayscale? Default True.
            scale (bool, optional): Scale pixel values to (0,1) float, or leave integers. Default False.
            warp_width, warp_height (int, optional): Resolution to scale the image frames to. Default 84x84.
            agents_to_exclude (list or None, optional): List of agents for which to not apply processing. Default None (applies processing to all agents).
        """
        super().__init__(env)
        # Reward counter
        self.total_reward = 0.0
        self.buffer = MaxAndSkipAndWarpAndScaleAndStackFrameBuffer(
            gym.spaces.Dict({"image": self.env.observation_space}),
            max_n,
            skip_n,
            stack_n,
            warp,
            scale,
            warp_width,
            warp_height,
        )

        self.observation_space = self.buffer.get_observation_space()["image"]

    def step(self, action):
        observation, reward, done, info = self.env.step(action)
        self.buffer.add_obs({"image": observation})
        self.total_reward += reward

        obs = self.buffer.get_obs()["image"]
        rew = self.total_reward
        self.total_reward = 0
        return obs, rew, done, info

    def reset(self, **kwargs):
        self.buffer.reset()
        observation = self.env.reset(**kwargs)
        self.buffer.add_obs({"image": observation})
        return self.buffer.get_obs()["image"]


class FireResetEnv(gym.Wrapper):
    """
    Take action on reset for environments that are fixed until firing.

    :param env: the environment to wrap
    """

    def __init__(self, env: gym.Env):
        gym.Wrapper.__init__(self, env)
        self.lives = 0

    def reset(self, **kwargs) -> np.ndarray:
        self.env.reset(**kwargs)
        self.lives = self.env.unwrapped._env.ale.lives()
        for __ in range(1200):
            obs, _, done, _ = self.env.step(0)
        obs, _, done, _ = self.env.step(1)
        if done:
            self.env.reset(**kwargs)
        obs, _, done, _ = self.env.step(2)
        if done:
            self.env.reset(**kwargs)
        return obs

    def step(self, ac):

        obs, reward, done, info = self.env.step(ac)
        lives = self.env.unwrapped._env.ale.lives()

        if 0 < lives < self.lives:
            self.env.step(0)
            self.env.step(1)
            obs, reward, done, info = self.env.step(2)
            self.lives = lives
        return obs, reward, done, info


def run_algo(
    algorithm: str = "BC",
    seed: int = 123,
    task: str = "space_invaders",
    gpu: bool = False,
    output_dir: str = "./output",
    convert_trajectory: str = "downsample",
):

    # prepare dataset
    d3rlpy.seed(seed)
    try:
        import d4rl_atari  # need this import to use ChannelFirst to just get environment

        if task in [
            "space_invaders_left",
            "space_invaders_right",
            "space_invaders_insideout",
            "space_invaders_outsidein",
            "space_invaders_rowbyrow",
            "space_invaders_mturk",
        ]:
            env = ChannelFirst(gym.make("space-invaders-expert-v0"))
        elif task in ["riverraid_left", "riverraid_right", "riverraid_mturk"]:
            env = ChannelFirst(gym.make("riverraid-expert-v0"))
        elif task in ["qbert_mturk"]:
            env = ChannelFirst(gym.make("qbert-expert-v0"))
        elif task in ["beam_rider_mturk"]:
            env = ChannelFirst(gym.make("beam-rider-expert-v0"))
        else:
            env = None
            print("The specified task is not supported.")
            exit(0)
    except ImportError as err:
        raise ImportError(
            "d4rl-atari is not installed.\n" "pip install git+https://github.com/takuseno/d4rl-atari"
        ) from err

    env.seed(seed)

    # If we don't downsample the human trajectory, we instead evaluate without frameskipping (but we still max every two consecutive frames)
    if convert_trajectory == "evaluate_every_step":
        # To do this, we replace the default D3RL Atari preprocessin wrapper with our own
        env.unwrapped._env = DeepmindEverystep(env.unwrapped._env.env, stack_n=1)

    task_adherence_key = {
        "space_invaders_insideout": "Correct aliens shot (fraction)",
        "space_invaders_outsidein": "Correct aliens shot (fraction)",
        "space_invaders_rowbyrow": "Correct aliens shot (fraction)",
        "space_invaders_left": "Time spent on left side of screen (fraction)",
        "space_invaders_right": "Time spent on right side of screen (fraction)",
        "riverraid_left": "Time spent on left side of screen (fraction)",
        "riverraid_right": "Time spent on right side of screen (fraction)",
    }

    _, session = get_engine_and_session("crowdplay_atari-v0")
    player = "game_0>player_0"

    # Load all the episodes for this task that have score >= 50
    task_episodes = (
        session.query(EpisodeModel)
        .filter(EnvironmentModel.environment_id == EpisodeModel.environment_id)
        .filter(EnvironmentModel.task_id == task)
        .filter(EpisodeKeywordDataModel.episode_id == EpisodeModel.episode_id)
        .filter(EpisodeKeywordDataModel.key == "Score")
        .filter(EpisodeKeywordDataModel.value >= 50)
        .all()
    )

    # For some task further filter by qualitative behavior statistics
    if task in task_adherence_key:
        episodes = [e for e in task_episodes if e.keyword_data[player][task_adherence_key[task]] >= 0.8]
    else:
        episodes = task_episodes

    traj_obs = []
    traj_acs = []
    traj_rew = []
    traj_term = []

    # Remove episode models in task_episodes list as they are no longer needed.
    del task_episodes
    num_episodes = len(episodes)
    while num_episodes > 0:
        # Use episode list as a stack to keep removing already processed episodes. This avoids memory explosion
        # as full data gets stored in _raw_trajectory and _processed_trajectory atttributes of Episode Model
        ep = episodes.pop(0)
        # Processing happens in preprocess_obs_in_trajectory function which is called by the get_processed_trajectory
        # function. framestack_axis_first = True swaps axes to have framestacking as first axis
        if convert_trajectory == "downsample":
            (
                obs_this_trajectory,
                acs_this_trajectory,
                rew_this_trajectory,
                term_this_trajectory,
            ) = ep.get_processed_trajectory(
                framestack_axis_first=True, downsample_frequency=4, downsample_offset=0, stack_n=1
            )
            traj_obs.append(np.array(obs_this_trajectory))
            traj_acs.append(np.array(acs_this_trajectory))
            traj_rew.append(np.array(rew_this_trajectory))
            traj_term.append(np.array(term_this_trajectory))
        elif convert_trajectory == "downsample_with_augment":
            for i in range(4):
                (
                    obs_this_trajectory,
                    acs_this_trajectory,
                    rew_this_trajectory,
                    term_this_trajectory,
                ) = ep.get_processed_trajectory(
                    framestack_axis_first=True, downsample_frequency=4, downsample_offset=i, stack_n=1
                )
                traj_obs.append(np.array(obs_this_trajectory))
                traj_acs.append(np.array(acs_this_trajectory))
                traj_rew.append(np.array(rew_this_trajectory))
                traj_term.append(np.array(term_this_trajectory))
        elif convert_trajectory == "evaluate_every_step":
            (
                obs_this_trajectory,
                acs_this_trajectory,
                rew_this_trajectory,
                term_this_trajectory,
            ) = ep.get_processed_trajectory(framestack_axis_first=True, stack_n=1)
            traj_obs.append(np.array(obs_this_trajectory))
            traj_acs.append(np.array(acs_this_trajectory))
            traj_rew.append(np.array(rew_this_trajectory))
            traj_term.append(np.array(term_this_trajectory))
        else:
            (
                obs_this_trajectory,
                acs_this_trajectory,
                rew_this_trajectory,
                term_this_trajectory,
            ) = ep.get_processed_trajectory(framestack_axis_first=True, stack_n=1)
            traj_obs.append(np.array(obs_this_trajectory))
            traj_acs.append(np.array(acs_this_trajectory))
            traj_rew.append(np.array(rew_this_trajectory))
            traj_term.append(np.array(term_this_trajectory))

        num_episodes -= 1

    obs = np.concatenate(traj_obs)
    acs = np.concatenate(traj_acs)
    rew = np.concatenate(traj_rew)
    term = np.concatenate(traj_term)

    input_data = d3rlpy.dataset.MDPDataset(obs, acs, rew, term)

    # split dataset
    train_episodes, test_episodes = train_test_split(input_data, test_size=0.1)

    # prepare algorithm
    if algorithm == "BC":
        algo = d3rlpy.algos.DiscreteBC(
            learning_rate=3e-05,
            n_frames=4,
            q_func_factory="mean",
            batch_size=256,
            target_update_interval=2500,
            scaler="pixel",
            use_gpu=gpu,
        )
    elif algorithm == "BCQ":
        algo = d3rlpy.algos.DiscreteBCQ(
            learning_rate=1e-04,
            n_frames=4,
            q_func_factory="mean",
            batch_size=256,
            action_flexibility=0.5,
            target_update_interval=2500,
            scaler="pixel",
            use_gpu=gpu,
        )
    elif algorithm == "DQN":
        algo = d3rlpy.algos.DoubleDQN(
            learning_rate=3e-05,
            n_frames=4,
            q_func_factory="mean",
            batch_size=256,
            target_update_interval=2500,
            scaler="pixel",
            use_gpu=gpu,
        )
    elif algorithm == "IQN":
        algo = d3rlpy.algos.DQN(
            learning_rate=1e-04,
            n_frames=4,
            q_func_factory=d3rlpy.models.q_functions.IQNQFunctionFactory(
                n_quantiles=16, n_greedy_quantiles=16, embed_size=512
            ),
            batch_size=256,
            target_update_interval=2500,
            scaler="pixel",
            use_gpu=gpu,
        )
    elif algorithm == "CQL":
        algo = d3rlpy.algos.DiscreteCQL(
            n_frames=4, q_func_factory="qr", batch_size=256, target_update_interval=2500, scaler="pixel", use_gpu=gpu
        )
    elif algorithm == "SAC":
        algo = d3rlpy.algos.DiscreteSAC(
            n_frames=4, batch_size=256, target_update_interval=2500, scaler="pixel", use_gpu=gpu
        )
    else:
        algo = None
        print("The specified offline learning algorithm is not supported.")
        exit()

    scorers = {"environment": d3rlpy.metrics.evaluate_on_environment(FireResetEnv(env))}

    # start training
    algo.fit(
        train_episodes,
        eval_episodes=test_episodes,
        logdir=f"{output_dir}",
        experiment_name=f"{task}_{algorithm}_{seed}",
        n_steps=1000000,
        n_steps_per_epoch=1000,
        save_interval=100,
        scorers=scorers,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Offline RL benchmarks", add_help=False)
    parser.add_argument(
        "--algorithm",
        type=str,
        default="BC",
        choices=["BC", "BCQ", "CQL", "IQN", "DQN", "SAC"],
        help="The algorithm to run",
    )
    parser.add_argument("--seed", type=int, default=123, help="The seed, default: 123")
    parser.add_argument("--task", type=str, default="space_invaders", help="The task, default: 'space_invaders'")

    parser.add_argument("--gpu", type=bool, default=False, help="Use gpu, default: False")

    parser.add_argument(
        "--output_dir",
        type=str,
        default="./output",
        help="The directory to save output in",
    )

    parser.add_argument(
        "--input_dir",
        type=str,
        default="./input",
        help="The directory to find trajectory data in",
    )

    parser.add_argument(
        "--convert_trajectory",
        type=str,
        default="downsample",
        help="How do we convert trajectory to align it with frameskipped observatons. Default: downsample.",
    )

    args, remaining_cli = parser.parse_known_args()
    run_algo(args.algorithm, args.seed, args.task, args.gpu, args.output_dir, args.convert_trajectory)
    print("All Tasks Finished.")
