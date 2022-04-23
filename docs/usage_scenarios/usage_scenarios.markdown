---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
title: Usage Scenarios
nav_order: 3
layout: default
# has_children: true
---

## CrowdPlay Usage Scenarios

CrowdPlay has been designed with Offline RL and Imitation Learning in mind, but because of it's flexible architecture can be used for many scenarios.

### Offline Learning

CrowdPlay can tap into any standard RL environment and enable these for offline learning, including offline RL and Imitation Learning. Furthermore, by interfacing with standard RL environments, CrowdPlay avoids duplication of effort: the same code can be used for both online and offline RL. Saved trajectories are automatically in the correct format for downstream learning pipelines, and state transitions are guaranteed to be identical to the original environment (since the same simulator is used in online RL, offline RL and crowdsourced trajectories). CrowdPlay can enable any existing current work in online RL to be used in offline RL with minimal effort.

### Multimodal Imitation Learning and Inverse RL

Beyond learning peak performance, CrowdPlay can be used in behavioural learning, such as multimodal Imitation Learning and Inverse Reinforcement Learning. The CrowdPlay platform provides real-time incentiviziation features aimed at eliciting specific and well-defined behavior from particpants, which can serve as test cases for behavioural learning algorithms. For instance, in the CrowdPlay Atari dataset we provide trajectories where participants were asked to keep their game avatar only on the left-hand side of the screen, or only on the right-hand side of the screen.

### Multi-Agent Learning

CrowdPlay supports multi-agent environments, both with multiple human players as well as mixed human-AI environments. For human players, participants can be physically separate, and they can be matched to open environments automatically. AI agents can take over control if a human participant disconnects if needed. CrowdPlay can work with standard RL training pipelines for AI agents, which interact with the same environment in CrowdPlay as they see during traning. The CrowdPlay Atari dataset provides multiagent data in Space Invaders, including data from a custom cooperative version of the game.

### Human-AI Interaction

Because CrowdPlay supports mixed human-AI multi-agent environments, it lends itself to human-AI intereaction research. It can tap into existing, standard training pipelines, allowing for easy access to AI training technology and rapid iteration. By making AI training and deployment plug-and-play, CrowdPlay allows researchers to focus on experiment design rather than on the technical details.

### ... and many others

CrowdPlay is built to be flexible and extensible, and we are always looking for ways to improve it. If you have an idea for a new feature or an application scenario we haven't thought of yet, please let us know!
