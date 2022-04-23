---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
title: CrowdPlay Features
nav_order: 2
layout: default
# has_children: true
---

## CrowdPlay Features

CrowdPlay has been designed with a number of features to allow easy, rapid collection of large-scale datasets tied into existing RL and offline learning pipelines.

### Interfacing with off-the-shelf RL environments

CrowdPlay interfaces with any standard OpenAI Gym and Gym-like environments. Any RL environment that provides a `step()` and a `reset()` function can in principle be streamed through CrowdPlay. This enables the entire ecosystem of existing RL simulators for crowdsourcing large-scale human demonstration datasets.

### Scalable Architecture

[![CrowdPlay Architecture](../images/crowdplay_architecture.png){: .float-right .pl-4 style="width:250px"}](../images/crowdplay_architecture.png)
CrowdPlay provides a highly extensible, high performance client-server architecture for streaming RL environments to remote web browser clients. The backend is highly scalable, and supports within-instance and across-instances load balancing.

### Multi-Agent Environments

CrowdPlay supports multi-agent environments, where each agent is controlled by a separate web browser client. Participants interacting in the same environment can be located anywhere in the world. Upon entering the CrowdPlay app, users can be assigned to environments waiting for participants automatically.

### Mixed human-AI Environments

In multiagent environments, agents can also be controlled by a mix of human and AI agents. AI agents can be trained using standard RL pipelines such as RLLib. CrowdPlay automatically handles image preprocessing for AI agents, for instance "Deepmind"-style preprocessing for Atari 2600 games.

### Rich User Interface

[![CrowdPlay UI Screenshot](../images/screenshot.png){: .float-left .pr-4 style="width:150px"}](../images/screenshot.png)
CrowdPlay comes with a rich, modern user interface. It can show detailed instructions as well as real-time feedback to participants. For paid participants, progress and estimated payments can also be displayed in real time.
{: .d-inline-block .pt-4 }

[![CrowdPlay Game Library Screenshot](../images/screenshot_library.png){: .float-left .pr-4 style="width:150px"}](../images/screenshot_library.png)
A "game library" style interface can allow participants to choose among available environments.
{: .d-inline-block }

[![CrowdPlay Game Library Screenshot](../images/screenshot_results.png){: .float-left .pr-4 style="width:150px"}](../images/screenshot_results.png)
Post-experiments, participants can view their performance relative to other participants.
{: .d-inline-block }
