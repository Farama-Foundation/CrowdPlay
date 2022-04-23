---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
title: Custom Environments (Backend)
nav_order: 3
layout: default
parent: Customizing CrowdPlay
---


## Environment Configuration

Environments are defined in `backend/app/crowdplay_environments.py`, which contains a dictionary with settings for each environment. To add an additional environment, simply add an entry to this dictionary. Environments can then be accessed using their key in that dictionary, e.g. <http://127.0.0.1:9000/?task=gym_space_invaders>. It's also possible to group multiple environments together so that either users are assigned automatically to environments, or so that users get to choose an environment from a "game library"-style interface.

Environments are defined as entries in a dictionary, where each entry itself is a dictionary of various configuration options. A basic environment definition looks like this:

``` python
crowdplay_environments["gym_space_invaders"]= {
    # First define the unterlying gym or gym-like environment.
    # For Gym Atari environments, you generally want the NoFrameskip version.
    "make_env": lambda: gym_make(
        env_id="SpaceInvadersNoFrameskip-v4"
    ),
    # We next define the UI we would like to use for this environment.
    # The first of these settings defines a list of React components the frontend should render.
    # In this instance, this is one component to show the observations, and another to capture keypresses.
    # The second setting passes a dictionary of configuration options to the UI component.
    # Here, we use this to define the mapping of keys to actions.
    "ui_layout": ["atari", "keycatcher"],
    "ui_layout_options": {"keymap": "atari_leftrightfire"},
    # Optionally, you can define here what a "default" or noop action is for this environment.
    # If this is not defined here, CrowdPlay will look for a function env.get_noop_action(agent_id) and use that if it exists.
    # If this fails too, CrowdPlay will try to generate a null action based on the environment's action space.
    # Failing all this, it will use "0" as the default action.
    # This is only used at the very beginning of an episode, until actions are received from the frontend.
    "noop_action": 0,
    # Set the FPS of this env
    'fps': 60,
    'realtime': CROWDPLAY_REALTIME_REALTIME,
    # Define which, if any, agents are controlled by AIs.
    # This one defines agents that are always AI-controlled:
    "ai_agent_map_always": {},
    # This one defines agents where an AI can take over if needed if a human player disconnects mid-game:
    # This is useful for multiagent MTurk experiments, so that the remaining Turker can keep playing to fulfil their HIT.
    "ai_agent_map_fallback": {},
    # A mapping from agent ID strings to human-readable explanation of which player you control.
    # This is shown in the UI. Useful for multiplayer games.
    "human_player_map": {'agent_0': "green"},
    # Instructions for the players. These are shown before and during the experiment.
    "initial_message": {
        'agent_0': "In this task you will play the game Space Invaders."
    },
    # This is only relevant for tasks that are then grouped in an "auto" task.
    # It tells the system how many assignments we want for each task, so it can assign players accordingly.
    "target_complete_assignments": 0,
    # Task callables
    # These are callables that are called each step to determine if a task has been completed,
    # optionally bonus payments, and to give feedback to players.
    "task_callables": {
        "Score": lambda: ScoreCallable(['agent_0']),
        "Time played": lambda: TimeCallable(),
        "Active playtime": lambda: ActiveTimeCallable(['agent_0']),
    },
    # Here we define what is needed to complete the assignment, in terms of the callables defined just above.
    "task_requirements": {"Active playtime": timedelta(minutes=10), "Score": 1000},
}
```

The most important part is `"make_env": lambda: gym_make(env_id="SpaceInvadersNoFrameskip-v4")`, which defines the function that creates an environment. We provide a `gym_make` function that creates OpenAI Gym Atari environments and encapsulates them in appropriate wrappers to interface with CrowdPlay.

## Environment Groups

In addition, two special types of configurations are supported: `choose` and `auto`. These let the user choose among a group of environments, respectively automatically assign a user to one of several environments.

``` python
crowdplay_environments["let_me_choose"] = {
    "choose": [
        {
            "value": "space_invaders",
            "title": "Space Invaders",
            "description": "The classic Atari game Space Invaders. Defend earth from alien invaders! We recommend this for your first game.",
            "image": "space_invaders.jpg",
        },
        {
            "value": "riverraid",
            "title": "River Raid",
            "description": "The classic Atari game River Raid.",
            "image": "space_invaders.jpg",
        },
    ],
}
```

``` python
crowdplay_environments["automatic"] = {
    "auto": [
        "space_invaders", 
        "riverraid",
    ],
}
```

## Adding new environment types

We provide sample code for OpenAI Gym Atari environments. If you wish to add additional types of environments, you may have to add a few lines of "glue" code to interface them with CrowdPlay. CrowdPlay largely follows the OpenAI Gym-style API for environments, meaning your environment mainly needs to define a `step()` and a `reset()` method. The only strictly required difference is that CrowdPlay expects all environments to look like multiagent environments, meaning actions are passed in as dictionaries of the form `{agent_id: action}`, and all values returned from `step()` and `reset()` are similar multi-agent dictionaries. We provide a wrapper that transforms single-agent environments into this format, and in principle you could directly call your own environment generator function in the CrowdPlay environment specification:

``` python
    "make_env": lambda: GymToCrowdPlay(gym.make('Pendulum-v1')),
```

However, there are a few additional considerations:

1. By default, the backend uses a heuristic to determine if the output of your environment is an image, or any other data type, by checking its shape. The heuristic works slighlty differently for basic data types and for dictionaries:
  a. For basic types including arrays: If the output is an array with shape `(x,y,3)`, it is assumed to be an image, and is encoded using jpeg before being streamed to the frontend. Otherwise it is sent as-is.
  b. For dictionaries, CrowdPlay processes them by element. Elements with a key that starts with the string 'image' are assumed to be images. Any other keys are sent as-is.
Generally, for complex observation spaces, we recommend working with dictionaries, as it also makes it easier to decode the output in the frontend if you plan on [creating your own UI layout](custom_environments_frontend.markdown).
2. CrowdPlay can process observations differently for humans than you would for AIs, for instance showing a visual rendering instead of a state vector. In order to enable this, your environment should provide a `env.crowdplay_render()` method. Many environments already provide such a functionality, and only need to be wrapped with a single line of code. For instance, we implement this in a wrapper for Gym environments:

``` python
class RenderPendulum(Wrapper):
    """This returns the rendered output from the unwrapped environment, useful for e.g. Pendulum"""

    def crowdplay_render(self):
        return {"agent_0": self.unwrapped.render(mode="rgb_array")}
```

For such environment, it is still the output from `env.step()` that is saved into the database, and the rendered output is only used to display the environment to humans.
3. Some environments may require additional software packages not already installed in the CrowdPlay docker image.
  a. For Python packages, these can be added to `backend/requirements.txt` and Docker will install them automatically on the next rebuild.
  b. System packages and any other set-up commands would need to be added to the backend Dockerfile, e.g. using `RUN apt-get install package-name -y`.

## Incentives and Statistics

Finally, you may wish to define additional callables in `backend/app/environment_callables.py`. These are used to compute realtime statistics and user feedback, and referenced by the entries in the dictionary in `crowdplay_environments.py`. Essentially, these are called by the environment process at every step; they receive as input the current action, observation, reward, emulator state, and essentially all other information that the environment process maintains; and they return a dictionary of essentially arbitrary information. This information is saved into the trajectory at every step (which can be used to calculate various statistics on-the-fly), it is stored to the metadata database at both an episode and a cumulative session level, and it can optionally be displayed to the user and be used to define both minimum required conditions to complete the experiment or bonus payments for MTurk workers. In principle these could be simple functions, but often you might want to use a python Callable so as to be able to maintain state between steps. For instance, you could use an environment callable to maintain a cumulative count of the user reward:

``` python
class ScoreCallable:
    def __init__(self, agents):
        self.reward = {agent: 0 for agent in agents}

    def __call__(self, step):
        for agent in step["reward"]:
            if agent in self.reward:
                self.reward[agent] += step["reward"][agent]
        return {agent: self.reward[agent] for agent in self.reward}
```

## ICLR paper environments

We also provide the full list of environments that were used in the CrowdPlay Atari dataset and the CrowdPlay ICLR paper. These have two particular quirks:

1. All Atari environments, even single-agent ones, use a multiagent environment, for consistency throughout the dataset.
2. All environments assume that both the action as well as the observation for each agent are dictionaries. This was a technical limitation in an earlier version of the CrowdPlay platform. We have opted to leave the environment as it was in order to enable reproducibility of the exact environments as were used to collect the dataset.

By default, these environments are not enabled; if you wish to enable them, uncomment the last line of `crowdplay_environments.py`.
