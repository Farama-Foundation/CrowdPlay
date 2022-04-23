---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
title: Usage
nav_order: 5
parent: CrowdPlay Atari Dataset
layout: default
---

## Using the CrowdPlay Dataset Engine

The CrowdPlay dataset package provides a powerful metadata engine that allows filtering of episodes by environment, recruitment channel, performance, behavioural statistics and other metadata. The following will simply load all the episodes in the dataset:

```python
from crowdplay_datasets.dataset import get_engine_and_session, EpisodeModel
P0 = 'game_0>player_0' # shorthand for first player in each game
_, session = get_engine_and_session("crowdplay_atari-v0") # start dataset session

all_episodes = session.query(EpisodeModel).all() # get all episodes
```

You could then filter episodes using standard python list comprehension:

```python
[e for e in all_episodes if 
    e.environment.keyword_data['all']['game'] == 'space_invaders' and 
    e.environment.keyword_data['all']['task'] == 'insideout' and 
    e.environment.keyword_data['all']['source'] == 'mturk' and 
    e.keyword_data[P0]['Score'] >= 100]
```

This selects all episodes where the game is Space Invaders, the participants were asked for follow a specific "insideout" behavior, participants were recruited on MTurk, and achieved an eppisode score of 100 or more.

It is also possible to filter episodes using SQL syntax, which comes at a slight performance benefit. This uses SQLAlchemy ORM syntax. The following filters for a specific environment ID and a minimum score:

```python
filtered_episodes = session.query(EpisodeModel)\
    .filter(EnvironmentModel.environment_id == EpisodeModel.environment_id)\
    .filter(EnvironmentModel.task_id == task)\
    .filter(EpisodeKeywordDataModel.episode_id == EpisodeModel.episode_id)\
    .filter(EpisodeKeywordDataModel.key == 'Score')\
    .filter(EpisodeKeywordDataModel.value >= 50)\
    .all()
```

### Loading Trajectories

`EpisodeModel` objects by themselves are a collection of relational metadata, but can also be used to access the actual trajectory. We provide two methods for this: `get_raw_trajectory()` returns the entire trajectory as-is, with all metadata and debug data intact, and with observations unprocessed and in CrowdPlay's multiagent nested Dict format. `get_processed_trajectory()` returns the trajectory with all observations processed, either in a format similar to the return values of a Gym `step()` function, or in a format that can be used directly for D3RL training.

* `get_processed_trajectory()` returns a trajectory as a list of numpy arrays, where each array is four stacked, downsampled frames, and has shape `(84, 84, 4)`. By default it returns the trajectory of the first agent's observation.
* `get_processed_trajectory(framestack_axis_first=False, stack_n=1)` returns the trajectory in a format that can be used directly for D3RL training. It differs from the default in that it does not stack frames (because D3RL provides its own framestacking), and it puts the framestacking axis first, result in observations of shape `(1, 84, 84)`.
* `get_processed_trajectory(agent='game_0>player_1')` and `get_processed_trajectory(agent='game_0>player_1', framestack_axis_first=False, stack_n=1)` return the trajectory of the second agent's observation in two-agent environments.

The raw trajectories contain observations and other information in the same format as is used in the `EnvProcess` episode loop. Much of this information is only useful for debug purposes. Notable exception are `trajectory[step_number]['info']['game_0>agent_0']['RAM']`, which contains the emulator RAM state at every frame; and `trajectory[step_number]['user_type']['game_0>agent_0']` which is set to `1` if the agent is controlled by a human, and `2` if the agent is controlled by an AI policy. This is useful in multiagent environments with fallback AIs, if you wish to distinguish parts of the episode where an AI took over control from a disconnected human.

### Episode Metadata

In the CrowdPlay Atari datset, for technical reasons agents are identified as `'game_0>player_0'` and `'game_0>player_1'`. Per-agent metadata is stored as key-value pairs in the `keyword_data[agent_id]` field of the `EpisodeModel` object. For instance `episode.keyword_data['game_0>player_0']['Active playtime']` returns the amount of time the agent was actively palying in the episode. Metadata stored in the `keyword_data` dictionary corresponds to the realtime statistics calculated using callables when the episode was recorded.

It is possible to calculate metadata offline as well, and `data_analysis/data_analysis.ipynb` and `data_analysis/batch_create_metadata` provide some examples of this. Such metadata can also be stored as part of the dataset database for later use.

### Integrating Into Offline Learning Pipelines

We provide a sample implementation of integrating the CrowdPlay Atari dataset into offline learning algorithms through the D3RL package in `offline/offline_atari.py`. This script can also be used to recreate the benchmarks in the CrowdPlay paper.
