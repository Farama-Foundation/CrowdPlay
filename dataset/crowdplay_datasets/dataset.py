import bz2
import gzip
import os
import pickle
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from gym import spaces
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    PickleType,
    String,
    Table,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, reconstructor, relation, relationship, sessionmaker
from sqlalchemy.orm.collections import attribute_mapped_collection

from .deepmind import MaxAndSkipAndWarpAndScaleAndStackFrameBuffer

# Default agent key
DEFAULT_AGENT_KEY = "game_0>player_0"

# Local SQLite for storage
Base = declarative_base()


@lru_cache(maxsize=16)
def preprocess_obs_in_trajectory(
    trajectory,
    agent=DEFAULT_AGENT_KEY,
    framestack_axis_first=False,
    downsample_frequency=1,
    downsample_offset=0,
    **kwargs,
):
    """Returns the preprocessed trajectory in a gym-like or similar format for a single agent

    Args:
        - agent: Which agent to return the trajectory for?
        - framestack_axis_first: If True, return k stacked frames of size nxn as a (k,n,n)-shaped numpy array (e.g. for D3RL).
            If False, return them as a (n,n,k)-shaped array (e.g. as used by Gym and Baselines).
        - downsample_frequency: Return an observation only every k-th frame.
        - downsample_offset: Return frames (n*k)+offset when downsampling.
        - **kwargs: keyword arguments for the deepmind framebuffer. Use stack_n=1 to disable framestacking
            (still get (1,n,n) or (n,n,1) array for observation)."""
    framebuffer = MaxAndSkipAndWarpAndScaleAndStackFrameBuffer(
        spaces.Dict({"image": spaces.Box(0, 255, (210, 160, 3))}), **kwargs
    )
    obs = []
    acs = []
    rew = []
    term = []
    reward_this_obs = 0
    for i in range(len(trajectory)):
        step = trajectory[i]

        # Add obs to framebuffer every step
        framebuffer.add_obs(step["prev_obs"][agent])

        # We sum the rewards in all the steps, including one's we don't see due to downsampling
        reward_this_obs += step["reward"][agent]

        # Append observations to processed trajectory, but only at downsampled frequency (e.g. every 4th frame)
        if i % downsample_frequency == downsample_offset or i % downsample_frequency == len(trajectory) - 1:
            # Added this flag to support special processing for input to MDPDataset when this function is called from offline
            # RL modules.
            if framestack_axis_first:
                # For preparing data for offline RL algorithms, MDPDataset class requires unstacked frames as input.
                # This is already handled by stack_n=1 passed via **kwargs, here make the channel to be the first axes
                obs.append(np.moveaxis(framebuffer.get_obs()["image"], 2, 0))
            else:
                obs.append(framebuffer.get_obs()["image"])
            acs.append(step["action"][agent]["game"])
            rew.append(reward_this_obs)
            term.append(int(step["done"][agent]))
            reward_this_obs = 0

    return (obs, acs, rew, term)


class EpisodeModel(Base):
    __tablename__ = "episodes"
    episode_id = Column(String(255), primary_key=True)
    # filename = Column(String(255), nullable=False)
    environment_id = Column(
        String(255),
        ForeignKey("environments.environment_id"),
        nullable=False,
    )
    keyword_data_list = relationship("EpisodeKeywordDataModel", back_populates="episode")
    environment = relationship("EnvironmentModel", back_populates="episodes")

    def get_raw_trajectory(self):
        return get_trajectory_by_id(self.episode_id)

    def get_processed_trajectory(self, agent=DEFAULT_AGENT_KEY, framestack_axis_first=False, **kwargs):
        """Gets the episode trajectory in a preprocessed format.

        Args:
            agent: In multiagent environments, which agent's trajectory to return
            framestack_axis_first: If set to true, observations consisting of n stacked frames are returnes as nx84x84 numpy arrays.
                If false, they are returned as 84x84xn arrays.
            **kwargs: Additional arguments to pass to the preprocessor framebuffer. E.g. stack_n = 1 to disable framestacking.
        """
        return preprocess_obs_in_trajectory(self.get_raw_trajectory(), agent, framestack_axis_first, **kwargs)

    def __repr__(self):
        return (
            f"<Episode(episode_id={self.episode_id}, environment_id={self.environment_id}, kwdata={self.keyword_data}>"
        )

    def __str__(self):
        return (
            f"<Episode(episode_id={self.episode_id}, environment_id={self.environment_id}, kwdata={self.keyword_data}>"
        )

    @reconstructor
    def init_on_load(self):
        k = {}
        for row in self.keyword_data_list:
            k[row.agent_id] = {}
        for row in self.keyword_data_list:
            k[row.agent_id][row.key] = row.value
        self.keyword_data = k

    def update_kwdata(self, agent, key, value):
        """Update keyword data."""
        # First update in nested dict
        if agent not in self.keyword_data:
            self.keyword_data[agent] = {}
        self.keyword_data[agent][key] = value
        # Now update in database
        # First check if the agent and key already exist, if so update value
        kw_exists = False
        for kwmodel in self.keyword_data_list:
            if kwmodel.agent_id == agent and kwmodel.key == key:
                kwmodel.value = value
                kw_exists = True
        # Otherwise append a new kwmodel
        if not kw_exists:
            kwmodel = EpisodeKeywordDataModel(episode_id=self.episode_id, agent_id=agent, key=key, value=value)
            self.keyword_data_list.append(kwmodel)

    def run_callable(self, callable, key):
        """Runs an episode callable and stores the result as keyword metadata."""
        trajectory = self.get_raw_trajectory()
        for step in trajectory:
            result = callable(step)
        for agent in result:
            self.update_kwdata(agent, key, result[agent])


class EpisodeKeywordDataModel(Base):
    __tablename__ = "episodekeyworddata"
    episode_id = Column(String(255), ForeignKey("episodes.episode_id"), primary_key=True)
    agent_id = Column(String(255), nullable=False, primary_key=True)
    key = Column(String(255), nullable=False, primary_key=True)
    value = Column(
        PickleType,
        nullable=False,
    )
    episode = relationship("EpisodeModel", back_populates="keyword_data_list")


class EnvironmentModel(Base):
    __tablename__ = "environments"
    environment_id = Column(String(255), primary_key=True)
    task_id = Column(String(255), nullable=False)
    episodes = relationship("EpisodeModel", back_populates="environment")
    users = relationship(
        "UserModel", back_populates="environment", collection_class=attribute_mapped_collection("agent_id")
    )
    keyword_data_list = relationship("EnvironmentKeywordDataModel", back_populates="environment")

    @reconstructor
    def init_on_load(self):
        k = {}
        for row in self.keyword_data_list:
            k[row.agent_id] = {}
        for row in self.keyword_data_list:
            k[row.agent_id][row.key] = row.value
        self.keyword_data = k


class EnvironmentKeywordDataModel(Base):
    __tablename__ = "environmentkeyworddata"
    environment_id = Column(String(255), ForeignKey("environments.environment_id"), primary_key=True)
    agent_id = Column(String(255), nullable=False, primary_key=True)
    key = Column(String(255), nullable=False, primary_key=True)
    value = Column(
        PickleType,
        nullable=False,
    )
    environment = relationship("EnvironmentModel", back_populates="keyword_data_list")


class UserModel(Base):
    __tablename__ = "users"
    user_id = Column(String(255), primary_key=True)
    permanent_user_id = Column(String(255), nullable=False)
    # user_type = Column(String(255), nullable=False)
    task_id = Column(String(255), nullable=False)
    environment_id = Column(String(255), ForeignKey("environments.environment_id"), nullable=False)
    agent_id = Column(String(255), nullable=False)
    environment = relationship("EnvironmentModel", back_populates="users")


def get_engine_and_session(dataset_id, create=False):
    # Local SQLite DB
    engine = create_engine(f"sqlite:///{Path(__file__).parent.parent}/data/{dataset_id}/dataset.sqlite")
    if create:
        Base.metadata.create_all(engine)
    Session = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )
    session = Session()
    return engine, session


@lru_cache(maxsize=4)
def get_trajectory_by_id(id):
    """Returns trajectory for given episode ID."""
    filename = get_trajectory_filename_by_id(id)
    if filename.endswith(".pickle"):
        with open(filename, "rb") as file:
            data = pickle.load(file)
            return data
    if filename.endswith(".gz"):
        with gzip.open(filename, "rb") as file:
            data = pickle.load(file)
            return data
    if filename.endswith(".bz2"):
        with bz2.open(filename, "rb") as file:
            data = pickle.load(file)
        return data
    raise ValueError(f"Trajectory {id} not found.")


def get_data_dir():
    """Gets the path to the dataset trajectory files."""
    return f"{Path(__file__).parent.parent}/data/"


def get_trajectory_filename_by_id(id):
    """Returns trajectory filename for given episode ID."""
    # We find the trajectory filename in all subdirectories.
    # Extremely unlikely any two uuids will ever collide, so this is probably OK.
    # If we wanted to guard against this, we could use self._sa_instance_state.dict['_sa_instance_state'].session.bind.engine.url
    # to get the correct subdirectory with certainty.
    for subdir in os.listdir(f"{Path(__file__).parent.parent}/data/"):
        if os.path.isdir(f"{Path(__file__).parent.parent}/data/{subdir}"):
            if os.path.isfile(f"{Path(__file__).parent.parent}/data/{subdir}/{id}.pickle"):
                return f"{Path(__file__).parent.parent}/data/{subdir}/{id}.pickle"
            elif os.path.isfile(f"{Path(__file__).parent.parent}/data/{subdir}/{id}.pickle.gz"):
                return f"{Path(__file__).parent.parent}/data/{subdir}/{id}.pickle.gz"
            elif os.path.isfile(f"{Path(__file__).parent.parent}/data/{subdir}/{id}.pickle.bz2"):
                return f"{Path(__file__).parent.parent}/data/{subdir}/{id}.pickle.bz2"
    raise ValueError(f"Trajectory {id} not found.")
