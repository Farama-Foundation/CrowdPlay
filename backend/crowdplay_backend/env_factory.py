import gym

from .gym_wrappers import (
    GymToCrowdPlay,
    MaxFrameAndRAMWrapper,
    MaxFrameAndRAMWrapperMultiagent,
    RenderPendulum,
    RenderTaxi,
)
from .multiagent_atari import (
    MultiAgentAtariGame,
    SpaceInvadersLives,
    SpaceInvadersRandomInitialPositions,
    SumRewards,
)


def multiagent_make(env_id="space_invaders", num_players=1, mode=None, sicoop=False, sirandomstart=False):
    """Creates a possibly multiagent Atari game"""
    env = MultiAgentAtariGame(game=env_id, num_players=num_players, seed=1, rank=0)
    if mode is not None:
        env.ale.setMode(mode)
    if sirandomstart:
        env = SpaceInvadersRandomInitialPositions(env)
    if sicoop:
        env = SpaceInvadersLives(env, bonus=0, penalty=0)
        env = SumRewards(env)
    env = MaxFrameAndRAMWrapperMultiagent(env)
    return env


def gym_make(env_id, **kwargs):
    """Creates a gym environment wrapped in the right way for CrowdPlay"""
    env = gym.make(env_id, **kwargs)
    env = GymToCrowdPlay(env)
    env = MaxFrameAndRAMWrapper(env)
    return env


def gym_taxi_make(env_id="taxi_v3", **kwargs):
    """Creates a Gym Taxi-v3 game"""
    env = gym.make(env_id, **kwargs)
    # Format things in the right way
    # It is structed as a dictionary
    # And we would want a similar wrapper
    env = GymToCrowdPlay(env)
    env = RenderTaxi(env)
    return env


def gym_pendulum_make(env_id="Pendulum-v1", **kwargs):
    """Creates a Gym Pendulum-v1 game"""
    env = gym.make(env_id, **kwargs)
    # Change time limit
    env._max_episode_steps = 3600
    # Format things in the right way
    # It is structed as a dictionary
    # And we would want a similar wrapper
    env = GymToCrowdPlay(env)
    env = RenderPendulum(env)
    return env
