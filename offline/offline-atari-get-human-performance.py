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
from crowdplay_datasets.deepmind import (
    MaxAndSkipAndWarpAndScaleAndStackFrameBuffer,
)
from d3rlpy.envs import ChannelFirst
from sklearn.model_selection import train_test_split


def get_human_performance(task: str = "space_invaders"):

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

    max_human_performance = max([e.keyword_data[player]["Score"] for e in episodes])

    print(f"Best human performance for task {task} is {max_human_performance}")


if __name__ == "__main__":
    for task in [
        "space_invaders_left",
        "space_invaders_right",
        "space_invaders_insideout",
        "space_invaders_outsidein",
        "space_invaders_rowbyrow",
        "space_invaders_mturk",
        "riverraid_left",
        "riverraid_right",
        "riverraid_mturk",
        "qbert_mturk",
        "beam_rider_mturk",
    ]:
        get_human_performance(task)
    print("All Tasks Finished.")
