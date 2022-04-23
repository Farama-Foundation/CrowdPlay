from datetime import datetime, timedelta

from .env_factory import gym_make, gym_pendulum_make, gym_taxi_make, multiagent_make
from .environment_callables import (
    ActiveTimeCallable,
    ConstantCallable,
    RiverraidLeftRightCallable,
    ScoreCallable,
    SpaceInvadersAccuracy,
    SpaceInvadersAliensHit,
    SpaceInvadersInsideOut,
    SpaceInvadersLeftRightCallable,
    SpaceInvadersOutsideIn,
    SpaceInvadersRows135,
    SpaceInvadersRowsByRow,
    TimeCallable,
)

"""
Structure of this file:
- a few static strings for filenames etc
- crowdplay_environments dict, defines all of the base tasks and variants.
- afterwards, we define specific tasks based on these and tailored to recruitment channel
    mostly, these just copy the base task, but modify the requirements and add bonus payments for MTurk.


"""

CROWDPLAY_REALTIME_REALTIME = 0
CROWDPLAY_REALTIME_TURNBASED_WAITFORNEWKEY = 1
CROWDPLAY_REALTIME_TURNBASED_HOLDDOWNKEYS = 2


FIRSTPLAYER = "game_0>player_0"
SECONDPLAYER = "game_0>player_1"
AGENTS1P = [
    FIRSTPLAYER,
]
AGENTS2P = [FIRSTPLAYER, SECONDPLAYER]

TIME1MINREQ = {
    "Time played": timedelta(minutes=1),
}
TIME1MINCALL1P = {
    "Score": lambda: ScoreCallable(AGENTS1P),
    "Time played": lambda: TimeCallable(),
}
TIME1MINCALL2P = {
    "Score": lambda: ScoreCallable(AGENTS2P),
    "Time played": lambda: TimeCallable(),
}

SIIMAGE = "space_invaders.jpg"
SI2PIMAGE = "si2p.jpg"
RRIMAGE = "riverraid.jpg"
MONTEZUMAIMAGE = "montezuma_revenge.jpg"
QBERTIMAGE = "qbert.jpg"
ENTOMBEDIMAGE = "entombed.jpg"

crowdplay_environments = {
    "gym_space_invaders": {
        # First define the unterlying gym or gym-like environment.
        # For Gym Atari environments, you generally want the NoFrameskip version.
        "make_env": lambda: gym_make(env_id="SpaceInvadersNoFrameskip-v4"),
        # Which UI layout to use on the frontend.
        # "ui_layout": ["atari_joystick"],
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "atari_leftrightfire"},
        # Set the FPS of this env
        "fps": 60,
        "realtime": CROWDPLAY_REALTIME_REALTIME,
        # Define which, if any, agents are controlled by AIs.
        # This one defines agents that are always AI-controlled:
        "ai_agent_map_always": {},
        # This one defines agents where an AI can take over if needed if a human player disconnects mid-game:
        # This is useful for multiagent MTurk experiments, so that the remaining Turker can keep playing to fulfil their HIT.
        "ai_agent_map_fallback": {},
        # A mapping from agent ID strings to human-readable explanation of which player you control.
        # This is shown in the UI. Useful for multiplayer-player games.
        "human_player_map": {"agent_0": "green"},
        # Instructions for the players. These are shown before and during the experiment.
        "initial_message": {"agent_0": "In this task you will play the game Space Invaders."},
        # This is only relevant for tasks that are then grouped in an "auto" task.
        # It tells the system how many assignments we want for each task, so it can assign players accordingly.
        "target_complete_assignments": 0,
        # Task callables
        # These are callables that are called each step to determine if a task has been completed,
        # optionally bonus payments, and to give feedback to players.
        "task_callables": {
            "Score": lambda: ScoreCallable(["agent_0"]),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(["agent_0"]),
        },
        # Here we define what is needed to complete the assignment, in terms of the callables defined just above.
        "task_requirements": {"Active playtime": timedelta(seconds=30), "Score": 10},
    },
    "gym_riverraid": {
        # First define the unterlying gym or gym-like environment.
        # For Gym Atari environments, you generally want the NoFrameskip version.
        "make_env": lambda: gym_make(env_id="RiverraidNoFrameskip-v4"),
        # Which UI layout to use on the frontend.
        # "ui_layout": ["atari_joystick"],
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "atari_updownleftrightfire"},
        # Set the FPS of this env
        "fps": 60,
        "realtime": CROWDPLAY_REALTIME_REALTIME,
        # Define which, if any, agents are controlled by AIs.
        # This one defines agents that are always AI-controlled:
        "ai_agent_map_always": {},
        # This one defines agents where an AI can take over if needed if a human player disconnects mid-game:
        # This is useful for multiagent MTurk experiments, so that the remaining Turker can keep playing to fulfil their HIT.
        "ai_agent_map_fallback": {},
        # A mapping from agent ID strings to human-readable explanation of which player you control.
        # This is shown in the UI. Useful for multiplayer-player games.
        "human_player_map": {"agent_0": "green"},
        # Instructions for the players. These are shown before and during the experiment.
        "initial_message": {"agent_0": "In this task you will play the game River Raid."},
        # This is only relevant for tasks that are then grouped in an "auto" task.
        # It tells the system how many assignments we want for each task, so it can assign players accordingly.
        "target_complete_assignments": 0,
        # Task callables
        # These are callables that are called each step to determine if a task has been completed,
        # optionally bonus payments, and to give feedback to players.
        "task_callables": {
            "Score": lambda: ScoreCallable(["agent_0"]),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(["agent_0"]),
        },
        # Here we define what is needed to complete the assignment, in terms of the callables defined just above.
        "task_requirements": {"Active playtime": timedelta(minutes=1), "Score": 100},
    },
    "taxi_v3": {
        "make_env": lambda: gym_taxi_make(env_id="Taxi-v3"),
        "ui_layout": ["taxi", "keycatcher"],
        "ui_layout_options": {"keymap": "taxi"},
        "fps": 60,
        "realtime": CROWDPLAY_REALTIME_TURNBASED_HOLDDOWNKEYS,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        "initial_message": {
            "agent_0": "In this task you will play the game Taxi. Use the arrow keys to move the taxi (yellow square). \
                Use 'q' to pick up a passenger (blue letter), 'a' to drop off a passenger (at the red letter)."
        },
        "target_complete_assignments": 0,
        "task_callables": {},
        "task_requirements": {},
    },
    "pendulum": {
        "make_env": lambda: gym_pendulum_make(env_id="Pendulum-v1"),
        "ui_layout": ["pendulum"],
        "fps": 30,
        "realtime": CROWDPLAY_REALTIME_REALTIME,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        "initial_message": {
            "agent_0": "In this task you will interact with the gym environment Pendulum. Use the joystick to move left and right."
        },
        "target_complete_assignments": 0,
        "task_callables": {},
        "task_requirements": {},
    },
    "demo_si_2p": {
        "make_env": lambda: multiagent_make(env_id="space_invaders", num_players=2),
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {
            FIRSTPLAYER: "si-comp-0",
            SECONDPLAYER: "si-comp-1",
        },
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: "In this task you will play the game Space Invaders.\n Your goal is to shoot as many alien invaders as possible.\n",
            SECONDPLAYER: "In this task you will play the game Space Invaders.\n Your goal is to shoot as many alien invaders as possible.\n",
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS2P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS2P, timeout=60 * 60 * 60),
        },
        "task_requirements": {"Active playtime": timedelta(minutes=10)},
    },
    "choice": {
        "choose": [
            {
                "value": "gym_space_invaders",
                "title": "Space Invaders",
                "description": "The classic Atari game Space Invaders. Defend earth from alien invaders!",
                "label": "Space Invaders",
                "image": SIIMAGE,
            },
            {
                "value": "gym_riverraid",
                "title": "River Raid",
                "description": "The classic Atari game River Raid. Fly down a river full of enemies!",
                "label": "River Raid",
                "image": RRIMAGE,
            },
            {
                "value": "taxi_v3",
                "title": "Taxi Version 3 (Auto-Advance)",
                "description": "Transport passengers and be the best taxi driver! Can keep key pressed to advance multiple turns.",
                "label": "Taxi",
                "image": "taxi.png",
            },
            {
                "value": "taxi_v3_waitforkey",
                "title": "Taxi Version 3 (Wait for key)",
                "description": "Transport passengers and be the best taxi driver! Must press and release key each turn.",
                "label": "Taxi",
                "image": "taxi.png",
            },
            {
                "value": "pendulum",
                "title": "Pendulum",
                "description": "Can you get the pendulum upright? Continuous control with a joystick.",
                "label": "Pendulum",
                "image": "pendulum.png",
            },
            {
                "value": "demo_si_2p",
                "title": "Multiplayer Space Invaders",
                "description": "The classic Atari game Space Invaders. Defend earth from alien invaders, together with a friend!",
                "label": "Space Invaders",
                "image": SI2PIMAGE,
            },
            {
                "value": "demo_si_ai",
                "title": "AI Space Invaders",
                "description": "The classic Atari game Space Invaders. Defend earth from alien invaders, together with an AI!",
                "label": "Space Invaders",
                "image": SI2PIMAGE,
            },
        ]
    },
}

crowdplay_environments["taxi_v3_waitforkey"] = dict(
    crowdplay_environments["taxi_v3"],
    realtime=CROWDPLAY_REALTIME_TURNBASED_WAITFORNEWKEY,
    ui_layout_options={"keymap": "taxi_waitforkey"},
)

crowdplay_environments["demo_si_ai"] = dict(
    crowdplay_environments["demo_si_2p"],
    task_requirements={},
    task_callables=TIME1MINCALL2P,
    ai_agent_map_fallback={},
    ai_agent_map_always={SECONDPLAYER: "si-comp-1"},
)

# Set a default task.
crowdplay_environments["default"] = crowdplay_environments["choice"]


# ==============
# Below are the environments used in the CrowdPlay ICLR paper, for reference.
# ==============

iclr_environments = {
    # Meta-tasks that automatically assign a task from those listed.
    "auto": {"auto": ["space_invaders", "riverraid"]},
    "test_choose": {
        "choose": [
            {
                "value": "space_invaders",
                "title": "Space Invaders",
                "description": "The classic Atari game Space Invaders. Defend earth from alien invaders!",
                "label": "Space Invaders",
                "image": SIIMAGE,
            },
            {
                "value": "space_invaders_randomstart",
                "title": "Space Invaders: Variant",
                "description": "The classic Atari game Space Invaders. but with a twist: You start at a random position.",
                "label": "Space Invaders, but with a random starting position.",
                "image": SIIMAGE,
            },
            {
                "value": "space_invaders_rowbyrow",
                "title": "Space Invaders: Challenge",
                "description": "Is plain Space Invaders getting boring? Try our advanced challenge! \
                    Can you win the game by shooting the aliens in row order from the bottom up?",
                "label": "Space Invaders, but can you shoot the aliens in a specific order?",
                "image": SIIMAGE,
            },
            {
                "value": "riverraid",
                "title": "Riverraid",
                "description": "The classic Atari game Riverraid. Fly up a river, defeat or evade enemies, and keep an eye on your fuel gauge!",
                "label": "Riverraid",
                "image": RRIMAGE,
            },
            {
                "value": "riverraid_left",
                "title": "Riverraid: Challenge",
                "description": "Riverraid, but with a twist: How far can you get if you only ever stay on the left side of the river?",
                "label": "Riverraid, but can you finish the game always staying on the left half of the screen?",
                "image": RRIMAGE,
            },
            {
                "value": "riverraid_right",
                "title": "Riverraid: Challenge",
                "description": "Riverraid, but with a twist: How far can you get if you only ever stay on the right side of the river?",
                "label": "Riverraid, but can you finish the game always staying on the right half of the screen?",
                "image": RRIMAGE,
            },
            {
                "value": "taxi_v3",
                "title": "Taxi",
                "description": "Pick up passengers and drop them off at their destinations",
                "label": "Pick up passengers and drop them off at their destinations",
                "image": QBERTIMAGE,
            },
        ]
    },
    "email_1_auto": {
        "auto": [
            "space_invaders",
            "space_invaders_randomstart",
            "space_invaders_135",
            "space_invaders_rowbyrow",
            "space_invaders_left",
            "space_invaders_right",
            "riverraid",
            "riverraid_left",
            "riverraid_right",
        ]
    },
    # =================================================
    #
    # Base 1p game definitions.
    #
    # =================================================
    # These define the basic environments we use.
    # In the CrowdPlay-Atari dataset these weren't used directly, but we later base specific tasks off them.
    "space_invaders": {
        # First define the unterlying gym or gym-like environment.
        "make_env": lambda: multiagent_make(env_id="space_invaders", num_players=1),
        # Define how to map keypresses to actions.
        # We define a few Atari keymaps already, and other keymaps can easily be added.
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},
        # Set the FPS of this env
        "fps": 60,
        # Define which, if any, agents are controlled by AIs.
        # This one defines agents that are always AI-controlled:
        "ai_agent_map_always": {},
        # This one defines agents where an AI can take over if needed if a human player disconnects mid-game:
        # This is useful for multiagent MTurk experiments, so that the remaining Turker can keep playing to fulfil their HIT.
        "ai_agent_map_fallback": {},
        # A mapping from agent ID strings to human-readable explanation of which player you control.
        # This is shown in the UI. Useful for multiplayer-player games.
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        # Instructions for the players. These are shown before and during the experiment.
        "initial_message": {FIRSTPLAYER: "In this task you will play the game Space Invaders."},
        # This is only relevant for tasks that are then grouped in an "auto" task.
        # It tells the system how many assignments we want for each task, so it can assign players accordingly.
        "target_complete_assignments": 0,
        # Task callables
        # These are callables that are called each step to determine if a task has been completed,
        # optionally bonus payments, and to give feedback to players.
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        # Here we define what is needed to complete the assignment, in terms of the callables defined just above.
        "task_requirements": {"Active playtime": timedelta(minutes=10), "Score": 1000},
    },
    "riverraid": {
        "make_env": lambda: multiagent_make(env_id="riverraid", num_players=1),
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_updownleftrightfire"},
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        "initial_message": {FIRSTPLAYER: "In this task you will play the game Riverraid."},
        "target_complete_assignments": 0,
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {"Active playtime": timedelta(minutes=10), "Score": 100},
    },
    "montezuma_revenge": {
        "make_env": lambda: multiagent_make(env_id="montezuma_revenge", num_players=1),
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_updownleftrightfire"},
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        "initial_message": {
            FIRSTPLAYER: "In this task you will play the game Montezuma's revenge. You play an explorer in an underground labyrinth of Montezuma's temple. \
                Collect keys and equipment and avoid enemies and traps. Your goal is to explore the labyrinth, \
                and to eventually reach the treasure chamber of the temple. \
                Control your player using your keyboards arrow keys to move, and the spacebar to jump."
        },
        "target_complete_assignments": 0,
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Time played": lambda: TimeCallable(),
        },
        "task_requirements": {},
    },
    "qbert": {
        "make_env": lambda: multiagent_make(env_id="qbert", num_players=1),
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_updownleftrightfire"},
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        "initial_message": {
            FIRSTPLAYER: "In this task you will play the game Q*bert. You play a figure on a 3D cube world. \
                Your goal is to jump on every cube once to change its color. Once all the cubes have changed color, \
                you advance to the next level. In later levels, you might have to jump on each cube more than \
                once to change its color. Avoid the purple snake, as you will lose a live if you run into it. \
                You control the player using your keyboard's arrow keys, but at a 45 degree angle: \
                The down key makes you jump to the down-left cube. Right makes you jump to the down-right cube, etc. \
                If you are able to, you might want to angle your keyboard. After you lose a live, you can press the space bar to restart."
        },
        "target_complete_assignments": 0,
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Time played": lambda: TimeCallable(),
        },
        "task_requirements": {},
    },
    # =================================================
    #
    # Variant 1p game definitions.
    #
    # =================================================
    # ----- Space Invaders ------
    # Space Invaders, but with a random starting position.
    # TODO remove?
    "space_invaders_randomstart": {
        # underlying gym(-like) environment
        "make_env": lambda: multiagent_make(env_id="space_invaders", num_players=1, sirandomstart=True),
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},  # mapping of keypresses to actions
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        # A mapping from agent ID strings to human-readable explanation of which player you control
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {FIRSTPLAYER: "In this task you will play the game Space Invaders."},
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {"Active playtime": timedelta(minutes=10), "Score": 1000},
    },
    # SpaceInvaders, but shoot only columns 1, 3 and 5.
    "space_invaders_135": {
        "make_env": lambda: multiagent_make(
            env_id="space_invaders", num_players=1
        ),  # underlying gym(-like) environment
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},  # mapping of keypresses to actions
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        # A mapping from agent ID strings to human-readable explanation of which player you control
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: "In this task you will play the game Space Invaders. \
                Please shoot only aliens in columns 1, 3 and 5 (from the left). Do not shoot aliens in other columns."
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Correct aliens shot (fraction)": lambda: SpaceInvadersRows135(AGENTS1P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {
            "Active playtime": timedelta(minutes=10),
            "Correct aliens shot (fraction)": 0.9,
        },
    },
    # SI, but shoot aliens row by row
    "space_invaders_rowbyrow": {
        "make_env": lambda: multiagent_make(
            env_id="space_invaders", num_players=1
        ),  # underlying gym(-like) environment
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},  # mapping of keypresses to actions
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        # A mapping from agent ID strings to human-readable explanation of which player you control
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: "In this task you will play the game Space Invaders. \
                Please shoot aliens in order starting with the bottom-most row, then the second row from the bottom, etc. \
                Do not shoot aliens in rows above the lowest row that still has aliens left."
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Correct aliens shot (total)": lambda: SpaceInvadersRowsByRow(AGENTS1P, kind="total"),
            "Correct aliens shot (fraction)": lambda: SpaceInvadersRowsByRow(AGENTS1P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {
            "Active playtime": timedelta(minutes=10),
            "Correct aliens shot (fraction)": 0.8,
            "Correct aliens shot (total)": 50,
        },
        "task_bonus_target": {
            "Correct aliens shot (fraction)": 1.0,
            "Correct aliens shot (total)": 500,
        },
        "task_bonus_value": lambda agent, x, task_callables_state: 3 * min(x, 1),
    },
    # SI, but shoot aliens outside in
    "space_invaders_outsidein": {
        "make_env": lambda: multiagent_make(
            env_id="space_invaders", num_players=1
        ),  # underlying gym(-like) environment
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},  # mapping of keypresses to actions
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        # A mapping from agent ID strings to human-readable explanation of which player you control
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: 'In this task you will play the game Space Invaders. Please shoot aliens in order "outside in" \
                starting with the outer-most columns (columns 1 and 6), then the second two columns from the outside \
                (columns 2 and 5), then finally the innermost two columns (columns 3 and 4). Do not shoot aliens except in this order.'
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Correct aliens shot (total)": lambda: SpaceInvadersOutsideIn(AGENTS1P, kind="total"),
            "Correct aliens shot (fraction)": lambda: SpaceInvadersOutsideIn(AGENTS1P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {
            "Active playtime": timedelta(minutes=10),
            "Correct aliens shot (fraction)": 0.8,
            "Correct aliens shot (total)": 50,
        },
        "task_bonus_target": {
            "Correct aliens shot (fraction)": 1.0,
            "Correct aliens shot (total)": 400,
        },
        "task_bonus_value": lambda agent, x, task_callables_state: 3 * min(x, 1),
    },
    # SI, but shoot aliens inside out
    "space_invaders_insideout": {
        "make_env": lambda: multiagent_make(
            env_id="space_invaders", num_players=1
        ),  # underlying gym(-like) environment
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},  # mapping of keypresses to actions
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        # A mapping from agent ID strings to human-readable explanation of which player you control
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: 'In this task you will play the game Space Invaders. Please shoot aliens in order "inside out" \
                starting with the inner-most columns (columns 3 and 4), then the second two columns from the inside \
                (columns 2 and 5), then finally the outermost two columns (columns 1 and 6). Do not shoot aliens except in this order.'
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Correct aliens shot (total)": lambda: SpaceInvadersInsideOut(AGENTS1P, kind="total"),
            "Correct aliens shot (fraction)": lambda: SpaceInvadersInsideOut(AGENTS1P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {
            "Active playtime": timedelta(minutes=10),
            "Correct aliens shot (fraction)": 0.8,
            "Correct aliens shot (total)": 50,
        },
        "task_bonus_target": {
            "Correct aliens shot (fraction)": 1.0,
            "Correct aliens shot (total)": 400,
        },
        "task_bonus_value": lambda agent, x, task_callables_state: 3 * min(x, 1),
    },
    # SI, but stay on left half of screen
    "space_invaders_left": {
        "make_env": lambda: multiagent_make(
            env_id="space_invaders", num_players=1
        ),  # underlying gym(-like) environment
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},  # mapping of keypresses to actions
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: "In this task you will play the game Space Invaders.\n Your goal is to shoot as many alien invaders as possible.\n \
                However, you must stay on the left half of the game screen."
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Time spent on left side of screen (fraction)": lambda: SpaceInvadersLeftRightCallable(
                {FIRSTPLAYER: {"min": 0, "max": 0.5}}
            ),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {
            "Active playtime": timedelta(minutes=10),
            "Time spent on left side of screen (fraction)": 0.9,
            "Score": 600,
        },
        "task_bonus_target": {
            "Time spent on left side of screen (fraction)": 1.0,
            "Score": 7000,
        },
        "task_bonus_value": lambda agent, x, task_callables_state: 3 * min(x, 1),
    },
    # SI, but stay on right half of screen
    "space_invaders_right": {
        "make_env": lambda: multiagent_make(
            env_id="space_invaders", num_players=1
        ),  # underlying gym(-like) environment
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},  # mapping of keypresses to actions
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: "In this task you will play the game Space Invaders.\n Your goal is to shoot as many alien invaders as possible.\n \
                However, you must stay on the right half of the game screen."
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Time spent on right side of screen (fraction)": lambda: SpaceInvadersLeftRightCallable(
                {FIRSTPLAYER: {"min": 0.5, "max": 1}}
            ),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {
            "Active playtime": timedelta(minutes=10),
            "Time spent on right side of screen (fraction)": 0.8,
            "Score": 600,
        },
        "task_bonus_target": {
            "Time spent on right side of screen (fraction)": 1.0,
            "Score": 7000,
        },
        "task_bonus_value": lambda agent, x, task_callables_state: 3 * min(x, 1),
    },
    # The following are repeats of the previous tasks, but we made the bonus payment scaling slightly different.
    # Now, bonus only starts accumulating if you're doing at least 50% (i.e. better than random) on the task.
    "space_invaders_rowbyrow_stricter": {
        "make_env": lambda: multiagent_make(
            env_id="space_invaders", num_players=1
        ),  # underlying gym(-like) environment
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},  # mapping of keypresses to actions
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        # A mapping from agent ID strings to human-readable explanation of which player you control
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: "In this task you will play the game Space Invaders. Please shoot aliens in order starting with the bottom-most row, \
                then the second row from the bottom, etc. Do not shoot aliens in rows above the lowest row that still has aliens left."
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Correct aliens shot (total)": lambda: SpaceInvadersRowsByRow(AGENTS1P, kind="total"),
            "Correct aliens shot (fraction)": lambda: SpaceInvadersRowsByRow(AGENTS1P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {
            "Active playtime": timedelta(minutes=10),
            "Correct aliens shot (fraction)": 0.8,
            "Correct aliens shot (total)": 50,
        },
        "task_bonus_target": {
            "Correct aliens shot (fraction)": 1.0,
            "Correct aliens shot (total)": 500,
        },
        "task_bonus_value": lambda agent, x, task_callables_state: 3
        * min(task_callables_state["Correct aliens shot (fraction)"][agent] / 500, 1)
        * max(0, 2 * (task_callables_state["Correct aliens shot (fraction)"][agent] - 0.5)),
    },
    "space_invaders_outsidein_stricter": {
        "make_env": lambda: multiagent_make(
            env_id="space_invaders", num_players=1
        ),  # underlying gym(-like) environment
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},  # mapping of keypresses to actions
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        # A mapping from agent ID strings to human-readable explanation of which player you control
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: 'In this task you will play the game Space Invaders. Please shoot aliens in order "outside in" starting with \
                the outer-most columns (columns 1 and 6), then the second two columns from the outside (columns 2 and 5), then finally \
                the innermost two columns (columns 3 and 4). Do not shoot aliens except in this order.'
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Correct aliens shot (total)": lambda: SpaceInvadersOutsideIn(AGENTS1P, kind="total"),
            "Correct aliens shot (fraction)": lambda: SpaceInvadersOutsideIn(AGENTS1P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {
            "Active playtime": timedelta(minutes=10),
            "Correct aliens shot (fraction)": 0.8,
            "Correct aliens shot (total)": 50,
        },
        "task_bonus_target": {
            "Correct aliens shot (fraction)": 1.0,
            "Correct aliens shot (total)": 400,
        },
        "task_bonus_value": lambda agent, x, task_callables_state: 3
        * min(task_callables_state["Correct aliens shot (fraction)"][agent] / 500, 1)
        * max(0, 2 * (task_callables_state["Correct aliens shot (fraction)"][agent] - 0.5)),
    },
    "space_invaders_insideout_stricter": {
        "make_env": lambda: multiagent_make(
            env_id="space_invaders", num_players=1
        ),  # underlying gym(-like) environment
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},  # mapping of keypresses to actions
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        # A mapping from agent ID strings to human-readable explanation of which player you control
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: 'In this task you will play the game Space Invaders. Please shoot aliens in order "inside out" starting with \
                the inner-most columns (columns 3 and 4), then the second two columns from the inside (columns 2 and 5), then finally \
                the outermost two columns (columns 1 and 6). Do not shoot aliens except in this order.'
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Correct aliens shot (total)": lambda: SpaceInvadersInsideOut(AGENTS1P, kind="total"),
            "Correct aliens shot (fraction)": lambda: SpaceInvadersInsideOut(AGENTS1P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {
            "Active playtime": timedelta(minutes=10),
            "Correct aliens shot (fraction)": 0.8,
            "Correct aliens shot (total)": 50,
        },
        "task_bonus_target": {
            "Correct aliens shot (fraction)": 1.0,
            "Correct aliens shot (total)": 400,
        },
        "task_bonus_value": lambda agent, x, task_callables_state: 3
        * min(task_callables_state["Correct aliens shot (fraction)"][agent] / 500, 1)
        * max(0, 2 * (task_callables_state["Correct aliens shot (fraction)"][agent] - 0.5)),
    },
    "space_invaders_left_stricter": {
        "make_env": lambda: multiagent_make(
            env_id="space_invaders", num_players=1
        ),  # underlying gym(-like) environment
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},  # mapping of keypresses to actions
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: "In this task you will play the game Space Invaders.\n Your goal is to shoot as many alien invaders as possible.\n \
                However, you must stay on the left half of the game screen."
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Time spent on left side of screen (fraction)": lambda: SpaceInvadersLeftRightCallable(
                {FIRSTPLAYER: {"min": 0, "max": 0.5}}
            ),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {
            "Active playtime": timedelta(minutes=10),
            "Time spent on left side of screen (fraction)": 0.9,
            "Score": 600,
        },
        "task_bonus_target": {
            "Time spent on left side of screen (fraction)": 1.0,
            "Score": 7000,
        },
        "task_bonus_value": lambda agent, x, task_callables_state: 3
        * min(task_callables_state["Score"][agent] / 7000, 1)
        * max(
            0,
            2 * (task_callables_state["Time spent on left side of screen (fraction)"][agent] - 0.5),
        ),
    },
    "space_invaders_right_stricter": {
        "make_env": lambda: multiagent_make(
            env_id="space_invaders", num_players=1
        ),  # underlying gym(-like) environment
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},  # mapping of keypresses to actions
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: "In this task you will play the game Space Invaders.\n Your goal is to shoot as many alien invaders as possible.\n \
                However, you must stay on the right half of the game screen."
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Time spent on right side of screen (fraction)": lambda: SpaceInvadersLeftRightCallable(
                {FIRSTPLAYER: {"min": 0.5, "max": 1}}
            ),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {
            "Active playtime": timedelta(minutes=10),
            "Time spent on right side of screen (fraction)": 0.8,
            "Score": 600,
        },
        "task_bonus_target": {
            "Time spent on right side of screen (fraction)": 1.0,
            "Score": 7000,
        },
        "task_bonus_value": lambda agent, x, task_callables_state: 3
        * min(task_callables_state["Score"][agent] / 7000, 1)
        * max(
            0,
            2 * (task_callables_state["Time spent on right side of screen (fraction)"][agent] - 0.5),
        ),
    },
    # -------- Space Invaders for Incentives Experiments --------
    # The following are tasks for the incentive experiments.
    # All the same task, but with different requirements for payment.
    # SI, get paid after 5 minutes no matter what you do.
    "space_invaders_insideout_timeonly": {
        "make_env": lambda: multiagent_make(
            env_id="space_invaders", num_players=1
        ),  # underlying gym(-like) environment
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},  # mapping of keypresses to actions
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        # A mapping from agent ID strings to human-readable explanation of which player you control
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: 'In this task you will play the game Space Invaders. Please shoot aliens in order "inside out" \
                starting with the inner-most columns (columns 3 and 4), then the second two columns from the inside (columns 2 and 5), \
                then finally the outermost two columns (columns 1 and 6). Do not shoot aliens except in this order.'
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Correct aliens shot (total)": lambda: SpaceInvadersInsideOut(AGENTS1P, kind="total"),
            "Correct aliens shot (fraction)": lambda: SpaceInvadersInsideOut(AGENTS1P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {"Time played": timedelta(minutes=5)},
        # 'task_bonus_target': {'Correct aliens shot (fraction)': 1.0, 'Correct aliens shot (total)': 400},
        # 'task_bonus_value': lambda agent, x, task_callables_state: 3 * min(x, 1)
    },
    # SI, get paid after 5 minutes of active playtime (need at least an action and a reward every x frames)
    "space_invaders_insideout_activetime": {
        "make_env": lambda: multiagent_make(
            env_id="space_invaders", num_players=1
        ),  # underlying gym(-like) environment
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},  # mapping of keypresses to actions
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        # A mapping from agent ID strings to human-readable explanation of which player you control
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: 'In this task you will play the game Space Invaders. Please shoot aliens in order "inside out" starting \
                with the inner-most columns (columns 3 and 4), then the second two columns from the inside (columns 2 and 5), \
                then finally the outermost two columns (columns 1 and 6). Do not shoot aliens except in this order.'
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Correct aliens shot (total)": lambda: SpaceInvadersInsideOut(AGENTS1P, kind="total"),
            "Correct aliens shot (fraction)": lambda: SpaceInvadersInsideOut(AGENTS1P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {"Active playtime": timedelta(minutes=5)},
        # 'task_bonus_target': {'Correct aliens shot (fraction)': 1.0, 'Correct aliens shot (total)': 400},
        # 'task_bonus_value': lambda agent, x, task_callables_state: 3 * min(x, 1)
    },
    # SI, get paid lump sum subject to minimum requirement.
    "space_invaders_insideout_taskrequirement": {
        "make_env": lambda: multiagent_make(
            env_id="space_invaders", num_players=1
        ),  # underlying gym(-like) environment
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},  # mapping of keypresses to actions
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        # A mapping from agent ID strings to human-readable explanation of which player you control
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: 'In this task you will play the game Space Invaders. Please shoot aliens in order "inside out" starting \
                with the inner-most columns (columns 3 and 4), then the second two columns from the inside (columns 2 and 5), \
                then finally the outermost two columns (columns 1 and 6). Do not shoot aliens except in this order.'
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Correct aliens shot (total)": lambda: SpaceInvadersInsideOut(AGENTS1P, kind="total"),
            "Correct aliens shot (fraction)": lambda: SpaceInvadersInsideOut(AGENTS1P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {
            "Active playtime": timedelta(minutes=5),
            "Correct aliens shot (fraction)": 0.8,
            "Correct aliens shot (total)": 50,
        },
        # 'task_bonus_target': {'Correct aliens shot (fraction)': 1.0, 'Correct aliens shot (total)': 400},
        # 'task_bonus_value': lambda agent, x, task_callables_state: 3 * min(x, 1)
    },
    # SI, get sliding bonus payment only.
    "space_invaders_insideout_bonusonly": {
        "make_env": lambda: multiagent_make(
            env_id="space_invaders", num_players=1
        ),  # underlying gym(-like) environment
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},  # mapping of keypresses to actions
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        # A mapping from agent ID strings to human-readable explanation of which player you control
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: 'In this task you will play the game Space Invaders. Please shoot aliens in order "inside out" starting \
                with the inner-most columns (columns 3 and 4), then the second two columns from the inside (columns 2 and 5), \
                then finally the outermost two columns (columns 1 and 6). Do not shoot aliens except in this order. \
                Your bonus payment will depend on both the nubmer of aliens you shot as well as how many of them you \
                shot in the correct order. You will only get a bonus payment if at least half the aliens you shoot are in the correct order.'
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Correct aliens shot (total)": lambda: SpaceInvadersInsideOut(AGENTS1P, kind="total"),
            "Correct aliens shot (fraction)": lambda: SpaceInvadersInsideOut(AGENTS1P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {"Active playtime": timedelta(minutes=5)},
        "task_bonus_target": {
            "Correct aliens shot (fraction)": 1.0,
            "Correct aliens shot (total)": 200,
        },
        "task_bonus_value": lambda agent, x, task_callables_state: 1.5
        * min(x, 1)
        * max(0, 2 * (task_callables_state["Correct aliens shot (fraction)"][agent] - 0.5)),
    },
    # SI, get sliding bonus payment, but only subject to minimm performance requirement.
    "space_invaders_insideout_allincentives": {
        "make_env": lambda: multiagent_make(
            env_id="space_invaders", num_players=1
        ),  # underlying gym(-like) environment
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},  # mapping of keypresses to actions
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        # A mapping from agent ID strings to human-readable explanation of which player you control
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: 'In this task you will play the game Space Invaders. Please shoot aliens in order "inside out" \
                starting with the inner-most columns (columns 3 and 4), then the second two columns from the inside (columns 2 and 5), \
                then finally the outermost two columns (columns 1 and 6). Do not shoot aliens except in this order. \
                Your bonus payment will depend on both the nubmer of aliens you shot as well as how many of them you shot \
                in the correct order. You will only get a bonus payment if at least half the aliens you shoot are in the correct order.'
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Correct aliens shot (total)": lambda: SpaceInvadersInsideOut(AGENTS1P, kind="total"),
            "Correct aliens shot (fraction)": lambda: SpaceInvadersInsideOut(AGENTS1P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {
            "Active playtime": timedelta(minutes=5),
            "Correct aliens shot (fraction)": 0.8,
            "Correct aliens shot (total)": 50,
        },
        "task_bonus_target": {
            "Correct aliens shot (fraction)": 1.0,
            "Correct aliens shot (total)": 200,
        },
        "task_bonus_value": lambda agent, x, task_callables_state: 1.5
        * min(x, 1)
        * max(0, 2 * (task_callables_state["Correct aliens shot (fraction)"][agent] - 0.5)),
    },
    # --------- Riverraid -----------
    # Riverraid, stay on left side of screen.
    "riverraid_left": {
        "make_env": lambda: multiagent_make(env_id="riverraid", num_players=1),
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_updownleftrightfire"},
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        "initial_message": {
            FIRSTPLAYER: "In this task you will play the game Riverraid. Please stay on the left half of the game screen. \
                You must spend at least 80% of the time on the left side of the screen to complete the task. \
                Your bonus payment will also depend heavily on spending as much time as possible on the left side \
                of the screen, as well as the score you achieve."
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Time spent on left side of screen (fraction)": lambda: RiverraidLeftRightCallable(
                {FIRSTPLAYER: {"min": -1000, "max": 5}}
            ),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {
            "Active playtime": timedelta(minutes=10),
            "Time spent on left side of screen (fraction)": 0.8,
            "Score": 100,
        },
        "task_bonus_target": {
            "Time spent on left side of screen (fraction)": 1.0,
            "Score": 50000,
        },
        "task_bonus_value": lambda agent, x, task_callables_state: 3
        * min(task_callables_state["Score"][agent] / 50000, 1)
        * max(
            0,
            2 * (task_callables_state["Time spent on left side of screen (fraction)"][agent] - 0.5),
        ),
    },
    # RR, stay on right side of screen
    "riverraid_right": {
        "make_env": lambda: multiagent_make(env_id="riverraid", num_players=1),
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_updownleftrightfire"},
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        "initial_message": {
            FIRSTPLAYER: "In this task you will play the game Riverraid. Please stay on the right half of the game screen. \
                You must spend at least 80% of the time on the right side of the screen to complete the task. \
                Your bonus payment will also depend heavily on spending as much time as possible on the right side of \
                the screen, as well as the score you achieve."
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS1P),
            "Time spent on right side of screen (fraction)": lambda: RiverraidLeftRightCallable(
                {FIRSTPLAYER: {"min": -5, "max": 1000}}
            ),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        },
        "task_requirements": {
            "Active playtime": timedelta(minutes=10),
            "Time spent on right side of screen (fraction)": 0.8,
            "Score": 100,
        },
        "task_bonus_target": {
            "Time spent on right side of screen (fraction)": 1.0,
            "Score": 50000,
        },
        "task_bonus_value": lambda agent, x, task_callables_state: 3
        * min(task_callables_state["Score"][agent] / 50000, 1)
        * max(
            0,
            2 * (task_callables_state["Time spent on right side of screen (fraction)"][agent] - 0.5),
        ),
    },
    # =================================================
    #
    # 2-Player Tasks
    #
    # =================================================
    # Entombed, competitive
    "entombed_comp": {
        "make_env": lambda: multiagent_make(env_id="entombed", num_players=2, mode=2),
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_updownleftrightfire"},
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        "human_player_map": {FIRSTPLAYER: "purple", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: "In this task you will play the game Entombed.\n Your goal is to travel as far down the maze as possible. \n \
                If you touch to top of the screen, you lose.\n If the other player loses, you gain a point, and vice versa. \
                You may get a bonus payments for achieving points. Further down the maze you will find useful powerups. Avoid the monsters.",
            SECONDPLAYER: "In this task you will play the game Entombed.\n Your goal is to travel as far down the maze as possible. \n \
                If you touch to top of the screen, you lose.\n If the other player loses, you gain a point, and vice versa. \
                You may get a bonus payments for achieving points. Further down the maze you will find useful powerups. Avoid the monsters.",
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        # Really only care about action timeout here.
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS2P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS2P, timeout=60 * 60 * 60),
        },
        "task_requirements": {"Active playtime": timedelta(minutes=10)},
    },
    # Entombed, cooperative
    "entombed_coop": {
        "make_env": lambda: multiagent_make(env_id="entombed", num_players=2, mode=3),
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_updownleftrightfire"},
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {},
        "human_player_map": {FIRSTPLAYER: "purple", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: "In this task you will play the game Entombed.\n Your goal is to travel as far down the maze as possible. \n \
                If you or the other player touch to top of the screen, you lose.\n You may want to cooperate with the other player. \
                Further down the maze you will find useful powerups. Avoid the monsters. ",
            SECONDPLAYER: "In this task you will play the game Entombed.\n Your goal is to travel as far down the maze as possible. \n \
                If you or the other player touch to top of the screen, you lose.\n You may want to cooperate with the other player. \
                Further down the maze you will find useful powerups. Avoid the monsters.  ",
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS2P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS2P, timeout=60 * 60 * 60),
        },
        "task_requirements": {"Active playtime": timedelta(minutes=10)},
    },
    # SI, competitive
    "space_invaders_2p_plain": {
        "make_env": lambda: multiagent_make(env_id="space_invaders", num_players=2),
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {
            FIRSTPLAYER: "si-comp-0",
            SECONDPLAYER: "si-comp-1",
        },
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: "In this task you will play the game Space Invaders.\n Your goal is to shoot as many alien invaders as possible.\n",
            SECONDPLAYER: "In this task you will play the game Space Invaders.\n Your goal is to shoot as many alien invaders as possible.\n",
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS2P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS2P, timeout=60 * 60 * 60),
        },
        "task_requirements": {"Active playtime": timedelta(minutes=10)},
    },
    # SI, cooperative
    "space_invaders_2p_coop": {
        "make_env": lambda: multiagent_make(env_id="space_invaders", num_players=2, sicoop=True),
        "ui_layout": ["atari", "keycatcher"],
        "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},
        "fps": 60,
        "ai_agent_map_always": {},
        "ai_agent_map_fallback": {
            FIRSTPLAYER: "si-coop-0",
            SECONDPLAYER: "si-coop-1",
        },
        "human_player_map": {FIRSTPLAYER: "green", SECONDPLAYER: "yellow"},
        "initial_message": {
            FIRSTPLAYER: "In this task you will play the game Space Invaders. This game is cooperative - \
                you and the other player both get points if either of you hits an alien. Please IGNORE THE SCORE SHOWN ON THE GAME SCREEN, \
                and try to maximise the score shown in the text box to the right of the game screen. This score is shared between you \
                and the other player. You may want to cooperate with the other player.",
            SECONDPLAYER: "In this task you will play the game Space Invaders. This game is cooperative - \
                you and the other player both get points if either of you hits an alien. Please IGNORE THE SCORE SHOWN ON THE GAME SCREEN, \
                and try to maximise the score shown in the text box to the right of the game screen. This score is shared between you \
                and the other player. You may want to cooperate with the other player.",
        },
        "target_complete_assignments": 0,  # number of complete assignments we want
        "task_callables": {
            "Score": lambda: ScoreCallable(AGENTS2P),
            "Time played": lambda: TimeCallable(),
            "Active playtime": lambda: ActiveTimeCallable(AGENTS2P, timeout=60 * 60 * 60),
        },
        "task_requirements": {"Active playtime": timedelta(minutes=10)},
    },
}

# =================================================
#
# Done with base tasks
#
# =================================================

# Everything below will now just copy and modify entries from the dict above.
# This allows creating multiple slightly different variants of the same base task.
# We might in the future think of a more elegant way of doing that.


# =================================================
#
# 1-player Social Media games
#
# =================================================

iclr_environments["space_invaders_socialmedia"] = dict(
    iclr_environments["space_invaders"],
    task_requirements={},
    task_callables={
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Time played": lambda: TimeCallable(),
        "Aliens shot": lambda: SpaceInvadersAliensHit(AGENTS1P),
        "Accuracy": lambda: SpaceInvadersAccuracy(AGENTS1P),
        "Time spent on left side of screen (fraction)": lambda: SpaceInvadersLeftRightCallable(
            {FIRSTPLAYER: {"min": 0, "max": 0.5}}
        ),
        "Time spent on right side of screen (fraction)": lambda: SpaceInvadersLeftRightCallable(
            {FIRSTPLAYER: {"min": 0.5, "max": 1}}
        ),
    },
    initial_message={
        FIRSTPLAYER: "In this experiment you will play the game Space Invaders. Your goal is to shoot as many of the alien invaders \
            shown on the screen as possible. You control the small cannon at the bottom of the screen. Use your keyboard's arrow keys \
            to move your cannon left and right, and use the spacebar key to fire. The aliens will fire at you too. If you are hit by \
            alien fire three times, the game ends. The game will also end if the alien invaders reach the bottom of the screen. A new \
            game will then start automatically, but you can end the experiment clicking the Finish Experiment button on the top right. \
            You can end the experiment at any time, but we encourage you to play at least a few games."
    },
)

iclr_environments["space_invaders_rowbyrow_socialmedia"] = dict(
    iclr_environments["space_invaders"],
    task_requirements={},
    task_callables={
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Aliens hit in order": lambda: SpaceInvadersRowsByRow(AGENTS1P, kind="total"),
        "Aliens hit in order (fraction)": lambda: SpaceInvadersRowsByRow(AGENTS1P),
        "Time played": lambda: TimeCallable(),
        "Aliens shot": lambda: SpaceInvadersAliensHit(AGENTS1P),
        "Accuracy": lambda: SpaceInvadersAccuracy(AGENTS1P),
        "Time spent on left side of screen (fraction)": lambda: SpaceInvadersLeftRightCallable(
            {FIRSTPLAYER: {"min": 0, "max": 0.5}}
        ),
        "Time spent on right side of screen (fraction)": lambda: SpaceInvadersLeftRightCallable(
            {FIRSTPLAYER: {"min": 0.5, "max": 1}}
        ),
    },
    initial_message={
        FIRSTPLAYER: "In this experiment you will play the game Space Invaders, but with a twist: Try to shoot the aliens row \
            by row from the bottom. We will keep count of how many you got in order, and you can compare yourself against others \
            afterwards. We recommend you play the standard Space Invaders game first to familiarise yourself with the game mechanics. \
            You can end the experiment at any time, but we encourage you to play at least a few games."
    },
)

iclr_environments["space_invaders_insideout_socialmedia"] = dict(
    iclr_environments["space_invaders"],
    task_requirements={},
    task_callables={
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Aliens hit in order": lambda: SpaceInvadersInsideOut(AGENTS1P, kind="total"),
        "Aliens hit in order (fraction)": lambda: SpaceInvadersInsideOut(AGENTS1P),
        "Time played": lambda: TimeCallable(),
        "Aliens shot": lambda: SpaceInvadersAliensHit(AGENTS1P),
        "Accuracy": lambda: SpaceInvadersAccuracy(AGENTS1P),
        "Time spent on left side of screen (fraction)": lambda: SpaceInvadersLeftRightCallable(
            {FIRSTPLAYER: {"min": 0, "max": 0.5}}
        ),
        "Time spent on right side of screen (fraction)": lambda: SpaceInvadersLeftRightCallable(
            {FIRSTPLAYER: {"min": 0.5, "max": 1}}
        ),
    },
    initial_message={
        FIRSTPLAYER: "In this experiment you will play the game Space Invaders, but with a twist: Try to shoot the aliens column by \
            column from the inside out. I.e. shoot all the aliens in the middle two columns (columns 3 and 4) first, then all the aliens \
            in columns 2 and 5, and finally all the aliens in the outside two columns (columns 1 and 6). We will keep count of how many you \
            got in this order order, and you can compare yourself against others afterwards. We recommend you play the standard Space Invaders \
            game first to familiarise yourself with the game mechanics. You can end the experiment at any time, but we encourage you to play \
            at least a few games."
    },
)


iclr_environments["riverraid_socialmedia"] = dict(
    iclr_environments["riverraid"],
    task_requirements={},
    task_callables={
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Time played": lambda: TimeCallable(),
    },
    initial_message={
        FIRSTPLAYER: "In this experiment you will play the game Riverraid. Your goal is to travel up the river as far as you can, but avoiding \
            enemy ships, helicopters and aircraft. You control the aircraft shown at the bottom of the screen using your keyboard: Use the left \
            and right arrow keys to move left and right, the up and down arrow keys to speed up or slow down, and the spacebar to fire. Press any \
            of these keys to start the game. If you collide with an enemy vessel, with a bridge, or with the river bank, you loose a live. You can \
            fire at enemy vessels and at briges to destroy them. You can also avoid collisions with enemy vessels by moving to avoid them, but you \
            cannot avoid bridges - you must shoot to destroy them. If you loose four lives, the game ends. A new game will then start automatically, \
            but you can end the experiment by clicking the Finish Experiment button on the top right of this page. You can end the experiment at any \
            time, but we encourage you to play at least a few games."
    },
)

iclr_environments["riverraid_left_socialmedia"] = dict(
    iclr_environments["riverraid_socialmedia"],
    task_requirements={},
    task_callables={
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Time spent on left side (fraction)": lambda: RiverraidLeftRightCallable(
            {FIRSTPLAYER: {"min": -1000, "max": 5}}
        ),
        "Time played": lambda: TimeCallable(),
    },
    initial_message={
        FIRSTPLAYER: "In this experiment you will play the game Riverraid, but with a twist: How far can you go only on the left side of the river? \
            We will keep count and show you how you compared to others afterwards. We recommend you play the standard Riverraid game first to \
            familiarise yourself with the game mechanics. You can end the experiment at any time, but we encourage you to play at least a few games."
    },
)

iclr_environments["riverraid_right_socialmedia"] = dict(
    iclr_environments["riverraid_socialmedia"],
    task_requirements={},
    task_callables={
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Time spent on right side (fraction)": lambda: RiverraidLeftRightCallable(
            {FIRSTPLAYER: {"min": -5, "max": 1000}}
        ),
        "Time played": lambda: TimeCallable(),
    },
    initial_message={
        FIRSTPLAYER: "In this experiment you will play the game Riverraid, but with a twist: How far can you go only on the right side of the river? \
            We will keep count and show you how you compared to others afterwards. We recommend you play the standard Riverraid game first to \
            familiarise yourself with the game mechanics. You can end the experiment at any time, but we encourage you to play at least a few games."
    },
)

iclr_environments["montezuma_revenge_socialmedia"] = dict(iclr_environments["montezuma_revenge"], task_requirements={})
iclr_environments["qbert_socialmedia"] = dict(iclr_environments["qbert"], task_requirements={})

# =================================================
#
# 2-player Social Media games
#
# =================================================

iclr_environments["spaceinvaders_competitive_socialmedia"] = dict(
    iclr_environments["space_invaders_2p_plain"],
    task_requirements={},
    task_callables=TIME1MINCALL2P,
    ai_agent_map_fallback={},
)
iclr_environments["spaceinvaders_cooperative_socialmedia"] = dict(
    iclr_environments["space_invaders_2p_coop"],
    task_requirements={},
    task_callables=TIME1MINCALL2P,
    ai_agent_map_fallback={},
)

iclr_environments["socialmedia_2p"] = {
    "choose": [
        {
            "value": "spaceinvaders_competitive_socialmedia",
            "title": "Space Invaders (competitive)",
            "description": "Defend earth from alien attackers - with a friend. This is the competitive version - you compete with the other player.",
            "image": SIIMAGE,
        },
        {
            "value": "spaceinvaders_cooperative_socialmedia",
            "title": "Space Invaders (cooperative)",
            "description": "Defend earth from alien attackers - with a friend. This is the cooperative version - you play in a team with the other player.",
            "image": SIIMAGE,
        },
        {
            "value": "entombed_cooperative_socialmedia",
            "title": "Entombed (cooperative)",
            "description": "Run against the clock down an underground maze. This is the cooperative version - you play in a team with the other player.",
            "image": ENTOMBEDIMAGE,
        },
        {
            "value": "entombed_competitive_socialmedia",
            "title": "Entombed (competitive)",
            "description": "Run against the clock down an underground maze. This is the competitive version - you play against the other player.",
            "image": ENTOMBEDIMAGE,
        },
    ]
}

# =================================================
#
# Human-AI Social Media games
#
# =================================================

iclr_environments["space_invaders_ai_competitive_socialmedia"] = dict(
    iclr_environments["space_invaders_2p_plain"],
    task_requirements={},
    task_callables=TIME1MINCALL2P,
    ai_agent_map_fallback={},
    ai_agent_map_always={SECONDPLAYER: "si-comp-1"},
)

iclr_environments["space_invaders_ai_cooperative_socialmedia"] = dict(
    iclr_environments["space_invaders_2p_coop"],
    task_requirements={},
    task_callables=TIME1MINCALL2P,
    ai_agent_map_fallback={},
    ai_agent_map_always={SECONDPLAYER: "si-coop-1"},
)

iclr_environments["socialmedia_1p"] = {
    "choose": [
        {
            "value": "space_invaders_socialmedia",
            "title": "Space Invaders",
            "description": "START HERE! The classic Atari game Space Invaders. Defend earth from alien invaders! We recommend this for your first game.",
            "image": SIIMAGE,
        },
        {
            "value": "space_invaders_ai_competitive_socialmedia",
            "title": "Space Invaders (AI)",
            "description": "The classic Atari game Space Invaders, but with a second, AI-controlled, player.",
            "image": SIIMAGE,
        },
        {
            "value": "space_invaders_ai_cooperative_socialmedia",
            "title": "Space Invaders (coop AI)",
            "description": "The classic Atari game Space Invaders, but with a second, AI-controlled, player. Special cooperative version, both players \
                share the same score.",
            "image": SIIMAGE,
        },
        {
            "value": "riverraid_socialmedia",
            "title": "Riverraid",
            "description": "The classic Atari game Riverraid. Fly up a river, defeat or evade enemies, and keep an eye on your fuel gauge!",
            "image": RRIMAGE,
        },
        {
            "value": "montezuma_revenge_socialmedia",
            "title": "Montezuma's Revenge",
            "description": "The classic Atari game Montezuma's Revenge. Explore the underground labyrinth of Montezuma's temple. Not for the faint of heart!",
            "image": MONTEZUMAIMAGE,
        },
        {
            "value": "qbert_socialmedia",
            "title": "Q*bert",
            "description": "The classic Atari game Q*bert. An action-puzzle game: Visit all the cubes without running into the snake.",
            "image": QBERTIMAGE,
        },
        {
            "value": "space_invaders_insideout_socialmedia",
            "title": "Space Invaders: Challenge",
            "description": "Is plain Space Invaders getting boring? Try our advanced challenge! Can you win the game by shooting the aliens column \
                by column from the inside out? We recommend you play the standard Space Invaders game first to familiarise yourself with the game mechanics.",
            "image": SIIMAGE,
        },
        {
            "value": "riverraid_left_socialmedia",
            "title": "Riverraid: Challenge",
            "description": "Riverraid, but with a twist: How far can you get if you only ever stay on the left side of the river? We recommend you play \
                the standard Riverraid game first to familiarise yourself with the game mechanics.",
            "image": RRIMAGE,
        },
        {
            "value": "riverraid_right_socialmedia",
            "title": "Riverraid: Challenge",
            "description": "Riverraid, but with a twist: How far can you get if you only ever stay on the right side of the river? We recommend you play \
                the standard Riverraid game first to familiarise yourself with the game mechanics.",
            "image": RRIMAGE,
        },
        {
            "value": "spaceinvaders_competitive_socialmedia",
            "title": "Space Invaders 2P (competitive)",
            "description": "Defend earth from alien attackers - with a friend. This is the competitive version - you compete with the other player.",
            "image": SIIMAGE,
        },
        {
            "value": "spaceinvaders_cooperative_socialmedia",
            "title": "Space Invaders 2P (cooperative)",
            "description": "Defend earth from alien attackers - with a friend. This is the cooperative version - you play in a team with the other player.",
            "image": SIIMAGE,
        },
    ]
}


# =================================================
#
# E-Mail campaign tasks
#
# =================================================

# The following tasks were for students recruited by email.
# There was no payment, but completing a task gave an entry in a raffle.

iclr_environments["space_invaders_email"] = dict(
    iclr_environments["space_invaders"],
    task_requirements={"Active playtime": timedelta(minutes=10), "Score": 5000},
    task_callables={
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        "Time played": lambda: TimeCallable(),
        "Aliens shot": lambda: SpaceInvadersAliensHit(AGENTS1P),
        "Accuracy": lambda: SpaceInvadersAccuracy(AGENTS1P),
        "Time spent on left side of screen (fraction)": lambda: SpaceInvadersLeftRightCallable(
            {FIRSTPLAYER: {"min": 0, "max": 0.5}}
        ),
        "Time spent on right side of screen (fraction)": lambda: SpaceInvadersLeftRightCallable(
            {FIRSTPLAYER: {"min": 0.5, "max": 1}}
        ),
    },
    initial_message={
        FIRSTPLAYER: "In this experiment you will play the game Space Invaders. Your goal is to shoot as many of the alien invaders shown on the screen \
            as possible. You control the small cannon at the bottom of the screen. Use your keyboard's arrow keys to move your cannon left and right, \
            and use the spacebar key to fire. The aliens will fire at you too. If you are hit by alien fire three times, the game ends. The game \
            will also end if the alien invaders reach the bottom of the screen. A new game will then start automatically, but you can end the experiment \
            clicking the Finish Experiment button on the top right. You can end the experiment at any time, but we encourage you to play at least a few games."
    },
)

iclr_environments["space_invaders_insideout_email"] = dict(
    iclr_environments["space_invaders"],
    task_requirements={
        "Active playtime": timedelta(minutes=10),
        "Score": 2000,
        "Aliens hit in order (fraction)": 0.8,
    },
    task_callables={
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        "Aliens hit in order": lambda: SpaceInvadersInsideOut(AGENTS1P, kind="total"),
        "Aliens hit in order (fraction)": lambda: SpaceInvadersInsideOut(AGENTS1P),
        "Time played": lambda: TimeCallable(),
        "Aliens shot": lambda: SpaceInvadersAliensHit(AGENTS1P),
        "Accuracy": lambda: SpaceInvadersAccuracy(AGENTS1P),
        "Time spent on left side of screen (fraction)": lambda: SpaceInvadersLeftRightCallable(
            {FIRSTPLAYER: {"min": 0, "max": 0.5}}
        ),
        "Time spent on right side of screen (fraction)": lambda: SpaceInvadersLeftRightCallable(
            {FIRSTPLAYER: {"min": 0.5, "max": 1}}
        ),
    },
    initial_message={
        FIRSTPLAYER: "In this experiment you will play the game Space Invaders, but with a twist: Try to shoot the aliens column by column from the \
            inside out. I.e. shoot all the aliens in the middle two columns (columns 3 and 4) first, then all the aliens in columns 2 and 5, \
            and finally all the aliens in the outside two columns (columns 1 and 6). We will keep count of how many you got in this order order, \
            and you can compare yourself against others afterwards. We recommend you play the standard Space Invaders game first to familiarise \
            yourself with the game mechanics. You can end the experiment at any time, but we encourage you to play at least a few games."
    },
)


iclr_environments["riverraid_email"] = dict(
    iclr_environments["riverraid"],
    task_requirements={"Active playtime": timedelta(minutes=10), "Score": 5000},
    task_callables={
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        "Time played": lambda: TimeCallable(),
    },
    initial_message={
        FIRSTPLAYER: "In this experiment you will play the game Riverraid. Your goal is to travel up the river as far as you can, but avoiding \
            enemy ships, helicopters and aircraft. You control the aircraft shown at the bottom of the screen using your keyboard: Use the left \
            and right arrow keys to move left and right, the up and down arrow keys to speed up or slow down, and the spacebar to fire. \
            Press any of these keys to start the game. If you collide with an enemy vessel, with a bridge, or with the river bank, you loose a \
            live. You can fire at enemy vessels and at briges to destroy them. You can also avoid collisions with enemy vessels by moving to avoid \
            them, but you cannot avoid bridges - you must shoot to destroy them. If you loose four lives, the game ends. A new game will then start \
            automatically, but you can end the experiment by clicking the Finish Experiment button on the top right of this page. You can end the \
            experiment at any time, but we encourage you to play at least a few games."
    },
)

iclr_environments["riverraid_left_email"] = dict(
    iclr_environments["riverraid_socialmedia"],
    task_requirements={
        "Active playtime": timedelta(minutes=10),
        "Score": 3000,
        "Time spent on left side (fraction)": 0.8,
    },
    task_callables={
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        "Time spent on left side (fraction)": lambda: RiverraidLeftRightCallable(
            {FIRSTPLAYER: {"min": -1000, "max": 5}}
        ),
        "Time played": lambda: TimeCallable(),
    },
    initial_message={
        FIRSTPLAYER: "In this experiment you will play the game Riverraid, but with a twist: How far can you go only on the left side of \
            the river? We will keep count and show you how you compared to others afterwards. We recommend you play the standard Riverraid game \
            first to familiarise yourself with the game mechanics. You can end the experiment at any time, but we encourage you to play at least a few games."
    },
)

iclr_environments["riverraid_right_email"] = dict(
    iclr_environments["riverraid_socialmedia"],
    task_requirements={
        "Active playtime": timedelta(minutes=10),
        "Score": 3000,
        "Time spent on right side (fraction)": 0.8,
    },
    task_callables={
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        "Time spent on right side (fraction)": lambda: RiverraidLeftRightCallable(
            {FIRSTPLAYER: {"min": -5, "max": 1000}}
        ),
        "Time played": lambda: TimeCallable(),
    },
    initial_message={
        FIRSTPLAYER: "In this experiment you will play the game Riverraid, but with a twist: How far can you go only on the right side of the river? \
            We will keep count and show you how you compared to others afterwards. We recommend you play the standard Riverraid game first to \
            familiarise yourself with the game mechanics. You can end the experiment at any time, but we encourage you to play at least a few games."
    },
)

iclr_environments["montezuma_revenge_email"] = dict(
    iclr_environments["montezuma_revenge"],
    task_requirements={"Active playtime": timedelta(minutes=10)},
    task_callables={
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        "Time spent on right side (fraction)": lambda: RiverraidLeftRightCallable(
            {FIRSTPLAYER: {"min": -5, "max": 1000}}
        ),
        "Time played": lambda: TimeCallable(),
    },
)


# Human-AI tasks
iclr_environments["space_invaders_ai_competitive_email"] = dict(
    iclr_environments["space_invaders_2p_plain"],
    ai_agent_map_fallback={},
    ai_agent_map_always={SECONDPLAYER: "si-comp-1"},
    task_requirements={"Time played": timedelta(minutes=10), "Score": 5000},
    task_callables=TIME1MINCALL2P,
)
iclr_environments["space_invaders_ai_cooperative_email"] = dict(
    iclr_environments["space_invaders_2p_coop"],
    ai_agent_map_fallback={},
    ai_agent_map_always={SECONDPLAYER: "so-coop-1"},
    task_requirements={"Time played": timedelta(minutes=10), "Score": 5000},
    task_callables=TIME1MINCALL2P,
)

# 2p tasks
iclr_environments["space_invaders_2p_competitive_email"] = dict(
    iclr_environments["space_invaders_2p_plain"],
    ai_agent_map_fallback={},
    ai_agent_map_always={},
    task_requirements={"Time played": timedelta(minutes=10), "Score": 5000},
    task_callables=TIME1MINCALL2P,
)
iclr_environments["space_invaders_2p_cooperative_email"] = dict(
    iclr_environments["space_invaders_2p_coop"],
    ai_agent_map_fallback={},
    ai_agent_map_always={},
    task_requirements={"Time played": timedelta(minutes=10), "Score": 5000},
    task_callables=TIME1MINCALL2P,
)

iclr_environments["email"] = {
    "choose": [
        {
            "value": "space_invaders_email",
            "title": "Space Invaders",
            "description": "The classic Atari game Space Invaders. Defend earth from alien invaders! We recommend this for your first game.",
            "image": SIIMAGE,
        },
        {
            "value": "space_invaders_ai_competitive_email",
            "title": "Space Invaders (AI)",
            "description": "The classic Atari game Space Invaders, but with a second, AI-controlled, player.",
            "image": SIIMAGE,
        },
        {
            "value": "space_invaders_ai_cooperative_email",
            "title": "Space Invaders (coop AI)",
            "description": "The classic Atari game Space Invaders, but with a second, AI-controlled, player. Special cooperative version, both \
                players share the same score.",
            "image": SIIMAGE,
        },
        {
            "value": "riverraid_email",
            "title": "Riverraid",
            "description": "The classic Atari game Riverraid. Fly up a river, defeat or evade enemies, and keep an eye on your fuel gauge!",
            "image": RRIMAGE,
        },
        {
            "value": "montezuma_revenge_email",
            "title": "Montezuma's Revenge",
            "description": "The classic Atari game Montezuma's Revenge. Explore the underground labyrinth of Montezuma's temple. Not for the faint of heart!",
            "image": MONTEZUMAIMAGE,
        },
        {
            "value": "space_invaders_insideout_email",
            "title": "Space Invaders: Challenge",
            "description": "Is plain Space Invaders getting boring? Try our advanced challenge! Can you win the game by shooting the aliens column by \
                column from the inside out? We recommend you play the standard Space Invaders game first to familiarise yourself with the game mechanics.",
            "image": SIIMAGE,
        },
        {
            "value": "riverraid_left_email",
            "title": "Riverraid: Challenge",
            "description": "Riverraid, but with a twist: How far can you get if you only ever stay on the left side of the river? We recommend you play \
                the standard Riverraid game first to familiarise yourself with the game mechanics.",
            "image": RRIMAGE,
        },
        {
            "value": "riverraid_right_email",
            "title": "Riverraid: Challenge",
            "description": "Riverraid, but with a twist: How far can you get if you only ever stay on the right side of the river? We recommend you play \
                the standard Riverraid game first to familiarise yourself with the game mechanics.",
            "image": RRIMAGE,
        },
        {
            "value": "space_invaders_2p_competitive_email",
            "title": "Space Invaders 2-Player",
            "description": "Win 100$! A two-player version of Space Invaders. You need to find a friend to start the game at the same time as you! \
                Separate raffle for 2x100$ gift cards. Multiple entries if you play with multiple people.",
            "image": SIIMAGE,
        },
        {
            "value": "space_invaders_2p_cooperative_email",
            "title": "Space Invaders 2-Player Coop",
            "description": "Win 100$! A two-player version of Space Invaders. You need to find a friend to start the game at the same time as you! \
                Special cooperative version, both players share the same score.  Separate raffle for 2x100$ gift cards. Multiple entries if you play \
                with multiple people.",
            "image": SIIMAGE,
        },
    ]
}

# =================================================
#
# 1p MTurk tasks
#
# =================================================


# Plain tasks for MTurk
iclr_environments["space_invaders_mturk"] = dict(
    iclr_environments["space_invaders"],
    task_callables={
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Active Playtime": lambda: ActiveTimeCallable(AGENTS1P),
        "Time played": lambda: TimeCallable(),
    },
    task_requirements={"Active Playtime": timedelta(minutes=10), "Score": 1000},
    task_bonus_target={"Score": 20000},
    task_bonus_value=lambda agent, x, task_callables_state: 3 * min(x, 1),
    initial_message={
        FIRSTPLAYER: "In this experiment you will play the game Space Invaders. Your goal is to shoot as many of the alien invaders shown on \
            the screen as possible. You control the small cannon at the bottom of the screen. Use your keyboard's arrow keys to move your cannon \
            left and right, and use the spacebar key to fire. The aliens will fire at you too. If you are hit by alien fire three times, the game \
            ends. The game will also end if the alien invaders reach the bottom of the screen. A new game will then start automatically. You must play \
            for at least 10 minutes and show some effort in the form of a minimum score to complete this task. Your bonus payment will depend entirely \
            on your score."
    },
)


iclr_environments["riverraid_mturk"] = {
    "make_env": lambda: multiagent_make(env_id="riverraid", num_players=1),
    "ui_layout": ["atari", "keycatcher"],
    "ui_layout_options": {"keymap": "multiagent_atari_updownleftrightfire"},
    "fps": 60,
    "ai_agent_map_always": {},
    "ai_agent_map_fallback": {},
    "target_complete_assignments": 0,  # number of complete assignments we want
    "task_callables": {
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Time played": lambda: TimeCallable(),
        "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
    },
    "task_requirements": {"Active playtime": timedelta(minutes=10), "Score": 1000},
    "task_bonus_target": {"Score": 100000},
    "task_bonus_value": lambda agent, x, task_callables_state: 3 * min(x, 1),
    "initial_message": {
        FIRSTPLAYER: "In this experiment you will play the game Riverraid. Your goal is to travel up the river as far as you can, \
            but avoiding enemy ships, helicopters and aircraft. You control the aircraft shown at the bottom of the screen using your \
            keyboard: Use the left and right arrow keys to move left and right, the up and down arrow keys to speed up or slow down, \
            and the spacebar to fire. Press any of these keys to start the game. If you collide with an enemy vessel, with a bridge, \
            or with the river bank, you loose a live. You can fire at enemy vessels and at briges to destroy them. You can also avoid \
            collisions with enemy vessels by moving to avoid them, but you cannot avoid bridges - you must shoot to destroy them. If you \
            loose four lives, the game ends. A new game will then start automatically.  You must play for at least 10 minutes and show some \
            effort in the form of a minimum score to complete this task. Your bonus payment will depend entirely on your score."
    },
}


iclr_environments["breakout_mturk"] = {
    "make_env": lambda: multiagent_make(env_id="breakout", num_players=1),
    "ui_layout": ["atari", "keycatcher"],
    "ui_layout_options": {"keymap": "multiagent_atari_leftrightfire"},
    "fps": 60,
    "ai_agent_map_always": {},
    "ai_agent_map_fallback": {},
    "target_complete_assignments": 0,  # number of complete assignments we want
    "task_callables": {
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Time played": lambda: TimeCallable(),
        "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
    },
    "task_requirements": {"Active playtime": timedelta(minutes=10)},
    "task_bonus_target": {"Score": 100},
    "task_bonus_value": lambda agent, x, task_callables_state: 3 * min(x, 1),
    "initial_message": {
        FIRSTPLAYER: "In this experiment you will play the game Breakout. \
            Your goal is to break apart the colored blocks at the top of the screen by bouncing a ball off the pedal at the bottom of the screen. \
            You control the pedal shown at the bottom of the screen using your keyboard: Use the left and right arrow keys to move left and right, and \
            the spacebar to start the game. \
            If you miss the ball, you lose a live.\
            If you loose four lives, the game ends. A new game will then start automatically.  \
            You must play for at least 10 minutes and show some effort to complete this task. Your bonus payment will depend entirely on your score."
    },
}

iclr_environments["beam_rider_mturk"] = {
    "make_env": lambda: multiagent_make(env_id="beam_rider", num_players=1),
    "ui_layout": ["atari", "keycatcher"],
    "ui_layout_options": {"keymap": "multiagent_atari_updownleftrightfire"},
    "fps": 60,
    "ai_agent_map_always": {},
    "ai_agent_map_fallback": {},
    "target_complete_assignments": 0,  # number of complete assignments we want
    "task_callables": {
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Time played": lambda: TimeCallable(),
        "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
    },
    "task_requirements": {"Active playtime": timedelta(minutes=10)},
    "task_bonus_target": {"Score": 10000},
    "task_bonus_value": lambda agent, x, task_callables_state: 3 * min(x, 1),
    "initial_message": {
        FIRSTPLAYER: "In this experiment you will play the game Beamrider. \
            Your goal is to shoot the alien invaders flying around the top of the screen. \
            You control the yellow spaceship shown at the bottom of the screen using your keyboard: Use the left and right arrow keys to move left \
            and right, the spacebar to fire, and the up arrow key to fire a special torpedo. You only have a limited number of special torbedos, \
            and might want to keep them until the alien mothership arrives. \
            If you get hit by enemy fire, you lose a live.\
            If you loose three lives, the game ends. A new game will then start automatically.  \
            You must play for at least 10 minutes and show some effort to complete this task. Your bonus payment will depend entirely on your score."
    },
}


iclr_environments["montezuma_revenge_mturk"] = dict(
    iclr_environments["montezuma_revenge"],
    task_callables={
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Active playtime": lambda: ActiveTimeCallable(AGENTS1P, timeout=10 * 60 * 60),
        "Time played": lambda: TimeCallable(),
    },
    task_requirements={"Active playtime": timedelta(minutes=10), "Score": 100},
    task_bonus_target={"Score": 5000},
    task_bonus_value=lambda agent, x, task_callables_state: 3 * min(x, 1),
)
iclr_environments["qbert_mturk"] = dict(
    iclr_environments["qbert"],
    task_callables={
        "Score": lambda: ScoreCallable(AGENTS1P),
        "Active playtime": lambda: ActiveTimeCallable(AGENTS1P),
        "Time played": lambda: TimeCallable(),
    },
    task_requirements={"Active playtime": timedelta(minutes=10), "Score": 1000},
    task_bonus_target={"Score": 40000},
    task_bonus_value=lambda agent, x, task_callables_state: 3 * min(x, 1),
)


# =================================================
#
# 2p and Human-AI MTurk tasks
#
# =================================================


iclr_environments["space_invaders_2p_competitive_mturk"] = dict(
    iclr_environments["space_invaders_2p_plain"],
    task_callables={
        "Score": lambda: ScoreCallable(AGENTS2P),
        "Active Playtime": lambda: ActiveTimeCallable(AGENTS2P),
        "Time played": lambda: TimeCallable(),
    },
    task_requirements={"Active Playtime": timedelta(minutes=10)},
    task_bonus_target={"Score": 10000},
    task_bonus_value=lambda agent, x, task_callables_state: 3 * min(x, 1),
    ai_agent_map_fallback={
        FIRSTPLAYER: "si-comp-0",
        SECONDPLAYER: "si-comp-1",
    },
    human_timeout=timedelta(minutes=15),
)

iclr_environments["space_invaders_ai_competitive_mturk"] = dict(
    iclr_environments["space_invaders_2p_competitive_mturk"],
    ai_agent_map_always={SECONDPLAYER: "si-comp-1"},
)

iclr_environments["space_invaders_2p_cooperative_mturk"] = dict(
    iclr_environments["space_invaders_2p_coop"],
    task_callables={
        "Score": lambda: ScoreCallable(AGENTS2P),
        "Active Playtime": lambda: ActiveTimeCallable(AGENTS2P),
        "Time played": lambda: TimeCallable(),
    },
    task_requirements={"Active Playtime": timedelta(minutes=10)},
    task_bonus_target={"Score": 20000},
    task_bonus_value=lambda agent, x, task_callables_state: 3 * min(x, 1),
    ai_agent_map_fallback={
        FIRSTPLAYER: "si-coop-0",
        SECONDPLAYER: "si-coop-1",
    },
    human_timeout=timedelta(minutes=15),
)

iclr_environments["space_invaders_ai_cooperative_mturk"] = dict(
    iclr_environments["space_invaders_2p_cooperative_mturk"],
    ai_agent_map_always={SECONDPLAYER: "si-coop-1"},
)

# For 2-player MTurk tasks, we recommend asking participants to show up at a pre-specified time,
# to increase the chances of them finding a second player online at the same time.
# You can set specific start and end times for such tasks.
# "auto" will match people first to an existing game waiting for more players.
iclr_environments["mturk_2p_0925"] = dict(
    auto=["space_invaders_2p_competitive_mturk", "space_invaders_2p_cooperative_mturk"],
    starttime=datetime(2021, 9, 26, 2, 45),
    endtime=datetime(2021, 9, 26, 7, 0),
)

iclr_environments["mturk_2p_0926"] = dict(
    auto=["space_invaders_2p_competitive_mturk", "space_invaders_2p_cooperative_mturk"],
    starttime=datetime(2021, 9, 27, 0, 45),
    endtime=datetime(2021, 9, 27, 5, 0),
)


# We merge the ICLR environments into the global list of tasks.
# Uncomment this line if you want to use the ICLR environments.
# crowdplay_environments.update(iclr_environments)
