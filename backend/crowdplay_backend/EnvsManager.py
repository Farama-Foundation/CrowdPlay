import os
from datetime import datetime
from re import I
from uuid import uuid4

import gym

from .ai_policy import (
    MaxAndSkipAndWarpAndScaleAndStackFrameBuffer,
    PretrainedRLLibA2CPolicyCustomModel,
)
from .config import Config
from .db import db
from .db_models import EnvModel, GameModel
from .environments import crowdplay_environments
from .EnvRunner import EnvRunner
from .exceptions import (
    AgentAlreadyInGame,
    AgentKeyExists,
    AiPolicyError,
    EnvironmentMalformed,
    EnvironmentNotFound,
    InstanceNotFound,
    NoMoreAgents,
    SingletonClass,
)
from .logger import getLogger

logger = getLogger("EnvsManager")


class EnvsManager:
    """Singleton class"""

    __instance = None

    @staticmethod
    def getInstance():
        if EnvsManager.__instance is None:
            EnvsManager.__instance = EnvsManager()
        return EnvsManager.__instance

    env_runners = {}

    def __init__(self):
        if EnvsManager.__instance is not None:
            raise SingletonClass()
        else:
            EnvsManager.__instance = self

    def env_to_db(self, instance_id, env_id, task_id, hit_id=Config.NO_HIT):
        env_model = EnvModel(instance_id=instance_id, env_id=env_id, task_id=task_id, hit_id=hit_id)

        db.session.add(env_model)
        db.session.commit()

        logger.info(f"EnvModel stored: {env_model}")

    def _agents_to_assign(self, instance_id):
        return [
            agent
            for agent in self.env_runners[instance_id].agents
            if self.env_runners[instance_id].agents[agent][0] is None
        ]

    def assign_agent(self, instance_id, agent, assign_to):
        self.get_runner(instance_id).assign_agent(agent, assign_to)

    def get_instance_ids_for_sid(self, sid):
        instances = []
        for instance_id in self.env_runners:
            # if (1, sid) in self.env_runners[instance_id].agents.values():
            for agent in self.env_runners[instance_id].agents.values():
                if len(agent) >= 2 and agent[1] == sid:
                    instances.append(instance_id)
        return instances

    def get_agent_for_sid(self, instance_id, sid):
        if instance_id in self.env_runners:
            # TODO could there ever be two agents with the same sid?
            agent_keys = list(
                (
                    agent
                    for agent in self.env_runners[instance_id].agents
                    if self.env_runners[instance_id].agents[agent][1] == sid
                )
            )
            return agent_keys[0]

    def num_total_agents_in_instance(self, instance_id):
        runner = self.get_runner(instance_id)
        return len(runner.agents)

    def num_connected_agents_in_instance(self, instance_id):
        runner = self.get_runner(instance_id)
        return len(
            list(
                (
                    agent
                    for agent in runner.agents
                    if (runner.agents[agent][0] is not None and runner.agents[agent][0] != 0)
                )
            )
        )

    def num_human_agents_in_instance(self, instance_id):
        runner = self.get_runner(instance_id)
        return len(list((agent for agent in runner.agents if runner.agents[agent][0] == 1)))

    def num_ai_agents_in_instance(self, instance_id):
        runner = self.get_runner(instance_id)
        return len(list((agent for agent in runner.agents if runner.agents[agent][0] == 2)))

    def make_or_get_env(self, env_id, task_id="default", hit_id=Config.NO_HIT, worker_id=None, assignment_id=None):
        """Find environment for a given env_id and hit_id. If an existing environment has an available
        slot for a new agent to join, returns that environment and agent ID. If not, creates a new
        environment.
        """

        # Reconnect agent to their existing session.
        if assignment_id is not None:
            # Find agent's instance, if any:
            agents_to_disconnect = []
            for instance_id in (
                instance_id for instance_id in self.env_runners if self.env_runners[instance_id].task_id == task_id
            ):
                for agent_id in self.env_runners[instance_id].agents:
                    if (
                        self.env_runners[instance_id].agents[agent_id][0] == 1
                        and len(self.env_runners[instance_id].agents[agent_id]) >= 3
                        and str(self.env_runners[instance_id].agents[agent_id][2]) == str(assignment_id)
                    ):
                        agents_to_disconnect.append((instance_id, agent_id))
                        # Previous logic for connecting user to existing session:
                        # if self.env_runners[instance_id]._stop_runner == False
                        #   and not self.env_runners[instance_id].env_process_exit_event.is_set():
                        #     return instance_id, agent_id
            # First notify all clients, then disconnect agents.
            for instance_id, agent_id in agents_to_disconnect:
                room = f"{instance_id}_{agent_id}"
                self.get_runner(instance_id).notify_client(
                    "force_disconnected",
                    room,
                    data={
                        "reason": "You have been disconnected. \
                            Please do not open multiple browser windows or tabs with this app at the same time."
                    },
                )
            for instance_id, agent_id in agents_to_disconnect:
                if instance_id in self.env_runners:
                    self.disconnect_human_agent(agent_id, instance_id, None)

        # TODO implement more general logic for assigning players to envs.
        # Use task_id to find available envs.
        # Check if any envs for this task have available agent slots.
        # If yes, connect agent to first free agent slot.
        for instance_id in (
            instance_id for instance_id in self.env_runners if self.env_runners[instance_id].task_id == task_id
        ):
            if len(self._agents_to_assign(instance_id)) > 0:
                logger.info(f"Returning instance {instance_id} for hit {hit_id}")
                # Get next available agent
                agent_key = self._agents_to_assign(instance_id)[0]
                # Set this agent to human, assigned but not connected yet
                self.assign_agent(instance_id, agent_key, (1, None, assignment_id))
                # Return instance_id and agent key
                return instance_id, agent_key

        # If no, create new env for this hit.
        instance_id = uuid4().hex

        self.make_runner(instance_id, task_id, hit_id=hit_id)

        logger.info(f"Instance {instance_id} on hold with id {hit_id}")

        # Set up AI policies if not existing already
        for agent_id in crowdplay_environments[task_id]["ai_agent_map_always"]:
            if agent_id not in self._agents_to_assign(instance_id):
                logger.warn(f"Agent ID {agent_id} in AI policy map, but not in environmnent list of agents.")

        self.env_to_db(instance_id, env_id, task_id, hit_id)

        logger.info(f"Environment {env_id} created with id {instance_id}")

        # Get next available agent
        agent_key = self._agents_to_assign(instance_id)[0]
        # Set this agent to human, assigned but not connected yet
        self.assign_agent(instance_id, agent_key, (1, None, assignment_id))
        # Return instance_id and agent key
        return instance_id, agent_key

    def get_task_id(self, instance_id):
        try:
            return self.env_runners[instance_id].task_id
        except KeyError:
            logger.error(f"Error: instance {instance_id} not found")
            raise InstanceNotFound(instance_id)

    def disconnect_human_agent(self, agent_key, instance_id, sid_id):
        # TODO We don't really need both agent_key and sid_id here, one or the other would be enough.
        # Not currently actually using sid_id!
        try:
            # agent_key = self.get_agent_for_sid(instance_id, sid_id)
            # Make sure it doesn't exist
            if agent_key in self._agents_to_assign(instance_id):
                logger.error(f"Error: agent key {agent_key} already in pool")
                raise AgentKeyExists(agent_key)
            else:
                # Close env if no more human agents.
                if self.num_human_agents_in_instance(instance_id) <= 1:
                    self.close_env(instance_id)
                    return None
                # Otherwise disconnect human and replace by AI if AI fallback specified

                if agent_key in crowdplay_environments[self.get_task_id(instance_id)]["ai_agent_map_fallback"]:
                    ai_policy_id = crowdplay_environments[self.get_task_id(instance_id)]["ai_agent_map_fallback"][
                        agent_key
                    ]
                    self.assign_agent(instance_id, agent_key, (2, ai_policy_id))
                    # self.hits[hit_id][instance_id]['sid_in_game'][f'ai_{policy_id_string}'] = agent_key
                    # del self.hits[hit_id][instance_id]['sid_in_game'][sid_id]
                    # Add AI agent to EnvRunner AI policy map.
                    # runner = self.get_runner(instance_id)
                    # runner.ai_agent_map[agent_key] = policy_id_string
                    logger.info(
                        f"Human agent {sid_id} disconnected from agent {agent_key} in env {instance_id},\
                        replaced by AI policy {ai_policy_id}"
                    )
                else:
                    self.assign_agent(instance_id, agent_key, (0, None))
                    logger.info(
                        f"Human agent {sid_id} disconnected from agent {agent_key} in env {instance_id},\
                        no replacement AI."
                    )
                num_agents_in_game = self.num_connected_agents_in_instance(instance_id)
                is_ready = num_agents_in_game == len(self.get_runner(instance_id).agents)

                logger.info(f"Player left. Still in game: {num_agents_in_game}")
                if not is_ready:
                    for other_agent in self.get_runner(instance_id).agents:
                        if other_agent != agent_key and self.get_runner(instance_id).agents[other_agent][0] == 1:
                            self.get_runner(instance_id).notify_client(
                                "force_disconnected",
                                data={
                                    "reason": """Unfortunately, your game has ended because one of the other players
                                     has disconnected. We try to have an AI on standby for this situation,
                                     but do not have one for this particular game yet. However, please feel
                                     free to click "Finish Experiment", and start a new one if you'd like."""
                                },
                                room=f"{instance_id}_{other_agent}",
                            )
                    self.stop_runner(instance_id)

        except KeyError:
            logger.error(f"Error: instance {instance_id} not found")
            raise InstanceNotFound(instance_id)

    def get_runner(self, instance_id):
        try:
            return self.env_runners[instance_id]
        except KeyError:
            logger.error(f"Error: instance {instance_id} not found")
            raise InstanceNotFound(instance_id)

    def make_runner(
        self,
        instance_id,
        task_id,
        hit_id=Config.NO_HIT,
        seed=None,
    ):
        fps = crowdplay_environments[task_id]["fps"] if "fps" in crowdplay_environments[task_id] else 60
        env_runner = EnvRunner(
            crowdplay_environments[task_id]["make_env"], instance_id, task_id=task_id, fps=fps, seed=seed
        )

        self.env_runners[instance_id] = env_runner

        # logger.info(f'Runner for {env.spec.id} with id {instance_id} created')

        return env_runner

    def stop_runner(self, instance_id):
        try:
            # Stop only if there is a runner
            env_runner = self.get_runner(instance_id)
            del self.env_runners[instance_id]

            logger.info(f"Stopping env {id(env_runner.env)} with id {instance_id}...")

            env_runner.stop_episode()
            env_runner.stop_runner()
            # del self.env_runners[instance_id]
        except Exception:
            pass

    # TODO rename

    def close_env(self, instance_id):
        self.stop_runner(instance_id)

        logger.info(f"Environment with instance id {instance_id} closed")

        return instance_id not in self.env_runners

    def action_space_for(self, instance_id):
        return self.get_runner(instance_id).action_space

    def observation_space_for(self, instance_id):
        return self.get_runner(instance_id).observation_space

    def __del__(self):
        for runner in self.env_runners:
            self.close_runner(self.env_runners[runner])
            del self.env_runners[runner]

        EnvsManager.__instance = None
