import bz2
import gzip
import multiprocessing
import os
import pickle
import pickle as pkl
from pathlib import Path
from typing import Any, Callable, Iterator, List, Optional, Tuple, Union, cast
from uuid import uuid4

import crowdplay_datasets
import d3rlpy
import d4rl_atari
import gym
import numpy as np
import torch
from crowdplay_datasets.dataset import (
    EnvironmentModel,
    EpisodeModel,
    get_data_dir,
    get_engine_and_session,
)
from d3rlpy.envs import ChannelFirst
from d3rlpy.metrics.scorer import AlgoProtocol, evaluate_on_environment
from d3rlpy.preprocessing.stack import StackedObservation
from sklearn.model_selection import train_test_split

"""
This is a script that rolls out D3RL checkpoints on 20 episodes each, and saves the trajectories to the local dataset package.
This is used in creating the t-SNE embeddings of BC agents vs human agents.
Note that this script only saves a bare minimal trajectory for each episode, without any metadata or real-time statistics.
See also the batch_create_metadata.py script in data_analysis/, which is used to calculate realtime statistics after the fact.
"""


def custom_evaluate_on_environment(
    env: gym.Env, n_trials: int = 10, epsilon: float = 0.0, render: bool = False, task_id: str = "d3rl_test"
) -> Callable[..., float]:
    """Returns scorer function of evaluation on environment.

    This function returns scorer function, which is suitable to the standard
    scikit-learn scorer function style.
    The metrics of the scorer function is ideal metrics to evaluate the
    resulted policies.

    .. code-block:: python

        import gym

        from d3rlpy.algos import DQN
        from d3rlpy.metrics.scorer import evaluate_on_environment


        env = gym.make('CartPole-v0')

        scorer = evaluate_on_environment(env)

        cql = CQL()

        mean_episode_return = scorer(cql)


    Args:
        env: gym-styled environment.
        n_trials: the number of trials.
        epsilon: noise factor for epsilon-greedy policy.
        render: flag to render environment.

    Returns:
        scoerer function.


    """

    # for image observation
    observation_shape = env.observation_space.shape
    is_image = len(observation_shape) == 3

    def scorer(algo: AlgoProtocol, *args: Any) -> float:
        _, session = get_engine_and_session("crowdplay_atari-v0")
        if is_image:
            stacked_observation = StackedObservation(observation_shape, algo.n_frames)

        episode_rewards = []

        environment_db = EnvironmentModel(environment_id=uuid4().hex, task_id=task_id)
        session.merge(environment_db)

        for _ in range(n_trials):
            observation = env.reset()
            episode_reward = 0.0
            trajectory = []
            reward = 0
            done = False

            # frame stacking
            if is_image:
                stacked_observation.clear()
                stacked_observation.append(observation)

            while True:
                # take action
                if np.random.random() < epsilon:
                    action = env.action_space.sample()
                else:
                    if is_image:
                        action = algo.predict([stacked_observation.eval()])[0]
                    else:
                        action = algo.predict([observation])[0]

                # TODO Add dataset here
                step_info = {
                    "prev_obs": {"game_0>player_0": observation},
                    "action": {"game_0>player_0": action},
                    "reward": {"game_0>player_0": reward},
                    "done": {"game_0>player_0": done},
                    "info": {"game_0>player_0": {"RAM": env.unwrapped._env.ale.getRAM().tolist()}},
                }
                trajectory.append(step_info)

                observation, reward, done, _ = env.step(action)
                episode_reward += reward

                if is_image:
                    stacked_observation.append(observation)

                if render:
                    env.render()

                if done:
                    break
            episode_rewards.append(episode_reward)
            bzipped_trajectory = gzip.compress(pickle.dumps(trajectory))
            episode_id = uuid4().hex
            with open(
                f"{get_data_dir()}/{episode_id}.pickle.gz",
                "wb",
            ) as f:
                f.write(bzipped_trajectory)
                f.close()
            episode_model = EpisodeModel(episode_id=episode_id, environment_id=environment_db.environment_id)
            session.merge(episode_model)
        session.commit()
        return float(np.mean(episode_rewards))

    return scorer


tasks = {
    0: "bc_left",
    1: "bc_right",
    2: "bc_insideout",
    3: "bc_outsidein",
    4: "bc_rowbyrow",
    100: "bc_left_synth",
    101: "bc_right_synth",
    102: "bc_insideout_synth",
    103: "bc_outsidein_synth",
    104: "bc_rowbyrow_synth",
}


def run_algo(task, seed_id):
    print(f"Running now for task {task}, seed {seed_id}")

    # Make env. Need to make special offline Atari env so that all the dimensions are the same
    env = ChannelFirst(gym.make("space-invaders-expert-v0"))

    # Create BC algorithm
    bc = d3rlpy.algos.DiscreteBC(n_frames=4, scaler="pixel", use_gpu=False)

    # Initialize BC with the env
    bc.build_with_env(env)

    folders = os.listdir(f"{Path(__file__).parent}/BC_models/")

    model_file = None
    for folder in folders:
        if folder.startswith(f"{task}_BC_{seed_id}"):
            if os.path.isfile(f"{Path(__file__).parent}/BC_models/{folder}/model_1000000.pt"):
                if model_file is not None:
                    print("Warning, found multiple checkpoints for this task and seed!")
                model_file = f"{Path(__file__).parent}/BC_models/{folder}/model_1000000.pt"
                print(f"Found checkpoint file {Path(__file__).parent}/BC_models/{folder}/model_1000000.pt")

    # Load checkpoint
    bc.load_model(model_file)

    # Create our custom scorer
    scorer = custom_evaluate_on_environment(env, n_trials=20, task_id=f"BC_{task}")

    # Run it
    scorer(bc)


def run_algo_onearg(a):
    run_algo(a[0], a[1])


if __name__ == "__main__":
    # args = []
    for task in [
        "space_invaders_left",
        "space_invaders_right",
        "space_invaders_insideout",
        "space_invaders_outsidein",
        "space_invaders_rowbyrow",
    ]:
        for seed in [123, 234, 456, 789]:
            run_algo(task, seed)
        # args.append((task, seed))

    # pool = multiprocessing.Pool(12)
    # pool.map(run_algo_onearg, args)
    print("All Tasks Finished.")
