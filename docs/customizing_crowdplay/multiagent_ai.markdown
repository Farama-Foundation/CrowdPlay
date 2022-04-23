---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
title: Multiagent Environments & AI Agents
nav_order: 5
layout: default
parent: Customizing CrowdPlay
---

## Multi-Agent Environments and AI Agents

CrowdPlay supports multi-agent environments, both with all-human agents as well as with a mix of human and AI agents. Configuration is simple, and AI agents can tap into existing RL training pipelines.

### Multi-Agent Environments

Multi-agent environments do not need to be explicitly configured: If an environment's `self.list_of_agents` contains more than one entry, CrowdPlay automatically treats it accordingly. There are, however, several useful configuration options specific to multi-agent environments.

* Some configuration options like `initial_message` are agent-specific, and take the form `{agent_key: config_value}` (even in single-agent environments).
* There are two types of AI agent configurations, each of which map agents to registered AI policies (more on the latter below).
  * `ai_agent_map_always` provides a mapping of agents to AI policies which will _always_ be in control of the corresponding agent. For instance, this allows you to create an environment where a human participant interacts with a pre-trained AI agent.
  * `ai_agent_map_fallback` defines AI policies that can take over control of an agent if a human participant disconnects from an environment. This is useful in environments that have more than one human agent. With AI agent fallback, the remaining human participants can keep playing even if one agent disconnects.
  * Selecting policies for each agent / environment works via a registration system, and policies are configured via the name string they are registered under. For instance:

``` python
    "ai_agent_map_fallback" : {
        "agent_0": "my_policy_agent_0",
        "agent_1": "my_policy_agent_1",
    }
```

* `human_timeout`: A secondary use of fallback AI agents is to limit wait times of human participants in multi-agent environments. If `human_timeout` is set for an environment, then CrowdPlay will automatically start th environment after the specified time has passed, even if not all human agent slots have been filled, using fallback AI agents to control the still-missing agents.

### Agent Assignment

When a new participant enters the app, CrowdPlay first looks to see if there are any already-instantiated matching environments that are still waiting for additional agents. If this is the case, the new participant is automatically connected to such an environment. Only if no matching environment with open agent slots is found, Crowdplay creates a new environment.

One caveat is that this can only happen for environments running on the same physical instance. In load-balanced deployment such as via Elastic Beanstalk we therefor recommend fewer (but larger) instances, and potentially running a separate deployment for multi-agent environments. If you want a unified "game library" environment chooser for both single- and multi-agent environments, you can use the `redirect` environment configuration option to send users to the multi-agent deployment URL.

### AI Policy Configuration

CrowdPlay supports AI agents trained with standard RL pipelines. We provide example code for RLLib policies. Integrating policies from other frameworks would essentially only require providing a `compute_action()` method. CrowdPlay expects that the policy's constructor does not require an arguments. A useful design pattern is therefore to define a generic class for the type of policy you want to load (e.g. an RLLib DQN policy), and a derived class for each specific pre-trained agent. You would then register the derived classes.

``` python
import crowdplay_backend.ai_policy.register_ai_policy

class MyPolicy(Policy):
    def __init__(self, observation_space, action_space, config):
        ...
    def compute_action(self, observation):
        ...

@register_policy("my_policy_agent_0")
class MyPolicyAgent0(MyPolicy):
    def __init__(self):
        super().__init__(specific_observation_space, specific_action_space, specific_config)
```

### AI Observation Preprocessing

CrowdPlay supports preprocessing observations for AI agents, and includes a preprocessing pipeline for Atari agents, including standard "max-and-skip" and "framestacking". In order to enable this, register the `AtariFB` preprocessor for your AI policy:

``` python
...
@register_ai_framebuffer(...)
@register_ai_framebuffer("my_policy_agent_0")
class AtariFB(...):
    ...
```

This will preprocess Atari observations in the same manner as standard "Deepmind" wrappers do. However, unlike in standard "Deepmind"-style Atari training pipelines, the policy will be queried for an action at every frame, rather than at every fourth frame. If you rely on repeating each action four times, you should implement this in your custom policy class.
