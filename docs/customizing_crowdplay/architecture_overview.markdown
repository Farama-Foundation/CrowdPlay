---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
title: Architecture Overview
nav_order: 1
layout: default
parent: Customizing CrowdPlay
---

## The CrowdPlay Architecture

CrowdPlay uses a highly scalable, highly flexible client-server architecture.

[![CrowdPlay Architecture](../images/crowdplay_architecture.png)](../images/crowdplay_architecture.png)

The two main components of the platform are the _frontend_, written in React and TypeScript, and the _backend_, written in Python. They communicate with each other using a mixture of http endpoints (for user setup and similar operations) and websockets (for streaming observations and keypresses). Unless you plan on major further developments, we envision that you will interact with these in two places:

1. The backend contains all the configuration regarding environments together with associated information including instructions for users, AI agents, requirements for completing an experiment, and others.
2. The frontend contains some UI elements like the consent form shown to a user upon entering the site.

Should you wish to make changes beyond these, the graphic above gives you a high-level overview of the CrowdPlay architecture. An important part to note is that the backend is parallelized and runs each environment in its own process. Some key files in the project include:

* `backend/app` contains all the backend code:
  * `EnvRunner.py` and `EnvsManager.py` contain the code that manages and runs the RL environment and records trajectories. The structure for this is as follows:
    * There is a singleton `EnvsManager` in the main process, which keeps track of all running environments. When a new user enters the system, this class also starts a new environment for them, or assigns them to an existing (multiagent) environment that is still waiting for additional players.
    * For each environment, `EnvsManager` creates an `EnvRunner`, still in the main process, which is the object through which the main process manages and communicates with this environment.
    * This `EnvRunner` in turn starts a new child process `EnvProcess`, which runs the environment without blocking the main process, and communicates with `EnvRunner` through a pipe. Observations from the environment are still sent through a pipe to the main process, which sends them to the client using websockets; and vice versa user actions are received by the main process and sent to the environment process through a pipe.
    * `EnvRunner` additionally creates a second child process which compresses trajectories and inserts them into the database, without blocking the `EnvProcess` process.
  * `api_routes.py` and `socket_events.py` define all (http and websockets, respectively) endpoints for communicating with the frontend.
  * `env_factory.py`, `gym_wrappers.py` and `atari.py` define the RL environment, and some wrappers we use around plain Gym environments.
  * `environments.py` and `environment_callables.py` define all the environments and associated information, as well as real-time statistics to collect for each environment.
* `frontend/src` contains all the frontend code:
  * `Environment` contains the main game screen and code to update content from new websocket packets.
  * `HomePage` and `MTurk` contain basic user setup.
  * `EnvironmentChoicePage` contains the "game library" style UI for choosing among multiple environments.
  * `ScorePage` contains some basic post-experiment feedback (e.g. distribution of scores among all participants).
