import math
import multiprocessing
import os
from datetime import datetime, timedelta
from typing import Iterable

import numpy as np
from crowdplay_backend.environment_callables import (
    SpaceInvadersInsideOut,
    SpaceInvadersLeftRightCallable,
    SpaceInvadersOutsideIn,
    SpaceInvadersRowsByRow,
)
from crowdplay_datasets.dataset import (
    EnvironmentKeywordDataModel,
    EnvironmentModel,
    EpisodeKeywordDataModel,
    EpisodeModel,
    UserModel,
    get_engine_and_session,
    get_trajectory_by_id,
)

"""
This script calculates metadata for episodes offline.
In particular we use this to calculate action distributions and multimodal behavioural statistics for t-SNE embeddings.
"""

_, session = get_engine_and_session("crowdplay_atari-v0")


P1 = "game_0>player_0"
P2 = "game_0>player_1"

# All the episodes, users and environments, for further filtering in Python
all_episodes = session.query(EpisodeModel).all()


class LatencyCallable:
    """Calculates the latency (delta between current step counter and step counter at client when keypress was sent) at every step."""

    def __init__(self):
        self.latencies = []
        self.prev_step = None

    def __call__(self, step_info):
        if self.prev_step is None:
            self.prev_step = step_info
        for agent in step_info["action_step_iter"]:
            if (
                step_info["action_step_iter"][agent] != self.prev_step["action_step_iter"][agent]
                and step_info["user_type"][agent] == 1
            ):
                self.latencies.append(step_info["step_iter"] - step_info["action_step_iter"][agent])
        self.prev_step = step_info
        return {"all": self.latencies}


def one_hot(x, length):
    o = np.zeros(length)
    o[x] = 1
    return o


class ActionDistributionCallable:
    """Returns action distribution."""

    def __init__(self):
        self.action_dist = {}
        self.i = 0

    def __call__(self, step_info):
        ret = {}
        for agent in step_info["action_step_iter"]:
            if agent not in self.action_dist:
                self.action_dist[agent] = one_hot(step_info["action"][agent]["game"], 18)
                ret[agent] = self.action_dist[agent]
            else:
                ret[agent] = self.i / (self.i + 1) * self.action_dist[agent] + 1 / (self.i + 1) * one_hot(
                    step_info["action"][agent]["game"], 18
                )
        self.i += 1
        return ret


def calc_latencies(episode_id):
    _, local_session = get_engine_and_session("crowdplay_atari-v0")
    ep = local_session.query(EpisodeModel).filter(EpisodeModel.episode_id == episode_id).first()
    if not ("all" in ep.keyword_data and "latencies" in ep.keyword_data["all"]):
        print(f"Computing latencies now for episode {ep.episode_id}")
        ep.run_callable(LatencyCallable(), "latencies")
        local_session.commit()
    else:
        print(f"Latencies already computed for episode {ep.episode_id}")


def action_dist_for_episode(episode, player):
    """Calculates action distribution for entire trajectory at once, easier than callable in this instance."""
    actions = []
    trajectory = get_trajectory_by_id(episode.episode_id)
    for i in range(len(trajectory)):
        if isinstance(trajectory[i]["action"][player], Iterable) and "game" in trajectory[i]["action"][player]:
            actions.append(one_hot(trajectory[i]["action"][player]["game"], 18))
        else:
            actions.append(one_hot(trajectory[i]["action"][player], 18))
    actions_frequency = {}
    for a in range(len(actions[0])):
        actions_frequency[f"action_{a}"] = sum([actions[i][a] for i in range(len(trajectory))]) / len(trajectory)
    data = {}
    data.update(actions_frequency)
    data["episode_length"] = len(trajectory)
    # data['score'] = episode.keyword_data[player]['Score']
    return data


def calc_multimodal_and_actiondist_metadata(episode):
    _, local_session = get_engine_and_session("crowdplay_atari-v0")
    ep = local_session.query(EpisodeModel).filter(EpisodeModel.episode_id == episode.episode_id).first()
    print(f"Computing metadata now for episode {ep.episode_id} with task {ep.environment.task_id}.")
    if P1 not in ep.keyword_data or "left" not in ep.keyword_data[P1]:
        print(f"Computing left now for episode {ep.episode_id}")
        ep.run_callable(SpaceInvadersLeftRightCallable({P1: {"min": 0, "max": 0.5}}), "left")
    if P1 not in ep.keyword_data or "right" not in ep.keyword_data[P1]:
        print(f"Computing right now for episode {ep.episode_id}")
        ep.run_callable(SpaceInvadersLeftRightCallable({P1: {"min": 0.5, "max": 1}}), "right")
    if P1 not in ep.keyword_data or "rowbyrow" not in ep.keyword_data[P1]:
        print(f"Computing rowbyrow now for episode {ep.episode_id}")
        ep.run_callable(
            SpaceInvadersRowsByRow(
                [
                    P1,
                ]
            ),
            "rowbyrow",
        )
    if P1 not in ep.keyword_data or "insideout" not in ep.keyword_data[P1]:
        print(f"Computing insideout now for episode {ep.episode_id}")
        ep.run_callable(
            SpaceInvadersInsideOut(
                [
                    P1,
                ]
            ),
            "insideout",
        )
    if P1 not in ep.keyword_data or "outsidein" not in ep.keyword_data[P1]:
        print(f"Computing outsidein now for episode {ep.episode_id}")
        ep.run_callable(
            SpaceInvadersOutsideIn(
                [
                    P1,
                ]
            ),
            "outsidein",
        )
    local_session.commit()
    # for player in ep.environment.users:
    for player in [
        P1,
    ]:
        if player not in episode.keyword_data:
            episode.keyword_data[player] = {}
        if player in episode.keyword_data and not ("action_dist_data" in episode.keyword_data[player]):
            print(f"Computing action distribution now for episode {ep.episode_id} and player {player}.")
            data = action_dist_for_episode(ep, player)
            ep.update_kwdata(player, "action_dist_data", data)
            local_session.commit()
        else:
            print(
                f"Action distribution already computed for episode {ep.episode_id} and player {player} or player not in episode."
            )
    local_session.commit()


# We calculate action distyribution and multimodal statistics for all episodes in these tasks:
tasks = [
    "space_invaders_left",
    "space_invaders_right",
    "space_invaders_rowbyrow",
    "space_invaders_insideout",
    "space_invaders_outsidein",
    "BC_space_invaders_left",
    "BC_space_invaders_right",
    "BC_space_invaders_rowbyrow",
    "BC_space_invaders_insideout",
    "BC_space_invaders_outsidein",
]

episodes = [ep for ep in all_episodes if ep.environment.task_id in tasks]


pool = multiprocessing.Pool(12)
pool.map(calc_multimodal_and_actiondist_metadata, episodes)
