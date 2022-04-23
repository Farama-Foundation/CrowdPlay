import bz2
import copy
import json
import multiprocessing
import os
import pickle
import queue
import threading
import time
from base64 import b64encode
from datetime import datetime
from uuid import uuid4

import cv2
import numpy as np
from flask import current_app
from gym import Space, spaces
from mysql import connector

from .ai_policy import (
    MaxAndSkipAndWarpAndScaleAndStackFrameBuffer,
    registered_ai_framebuffers,
    registered_ai_policies,
)
from .config import Config
from .db import db
from .db_models import EnvModel, GameModel, SessionModel
from .environment_callables import ConstantCallable, ScoreCallable, TimeCallable
from .environments import (
    CROWDPLAY_REALTIME_REALTIME,
    CROWDPLAY_REALTIME_TURNBASED_HOLDDOWNKEYS,
    CROWDPLAY_REALTIME_TURNBASED_WAITFORNEWKEY,
    crowdplay_environments,
)
from .exceptions import AiPolicyError
from .logger import getLogger
from .socketio import socketio
from .utils import noop, observation_to_serializable

logger = getLogger(__name__)


#########
# Utils #
#########

# TODO: we're repeating all this logic


class SpaceType:
    DISCRETE = "Discrete"
    BOX = "Box"
    MULTI_BINARY = "MultiBinary"
    MULTI_DISCRETE = "MultiDiscrete"
    DICT = "Dict"
    ORDERED_DICT = "OrderedDict"


def get_noop_for_space(space):
    if isinstance(space, spaces.Box):
        return np.zeros(space.shape)
    if isinstance(space, spaces.Discrete):
        return 0
    if isinstance(space, spaces.Dict):
        return {key: get_noop_for_space(space.spaces[key]) for key in space}
    if isinstance(space, spaces.MultiDiscrete):
        return np.zeros(space.shape)
    if isinstance(space, spaces.MultiBinary):
        return np.zeros(space.n)
    if isinstance(space, spaces.Tuple):
        return [get_noop_for_space(s) for s in space.spaces]
    return 0


def rgb_array_to_bytes(rgb_array, ext=".jpg"):
    _, buffer = cv2.imencode(ext, rgb_array[:, :, [2, 1, 0]])
    return buffer.tobytes()


def rgb_array_to_image_data(rgb_array, encoding="utf-8"):
    b_frame = rgb_array_to_bytes(rgb_array)
    b64_frame = b64encode(b_frame).decode(encoding)
    return "data:image/jpeg;base64," + b64_frame


def episode_to_db(trajectory, episode_id, conn):
    """Inserts as bzipped pickled trajectory into the DB."""

    insert_episode_query = """
    INSERT INTO episode_trajectories (
        episode_id,
        trajectory
    )
    VALUES ( %s, %s )
    """

    bzipped_trajectory = bz2.compress(pickle.dumps(trajectory))

    with conn.cursor() as cursor:
        cursor.execute(insert_episode_query, (episode_id, bzipped_trajectory))
        conn.commit()
        cursor.close()


def mark_db_process_status_code(instance_id, status_code, conn):
    logger.info(f"DB process {instance_id} updating status code to {status_code}.")
    updatequery = """
    UPDATE crowdplaydb.envs SET crowdplaydb.envs.dbprocess_status_code = %s WHERE crowdplaydb.envs.instance_id=%s;
    """
    data = (status_code, instance_id)
    with conn.cursor() as cursor:
        cursor.execute(updatequery, data)
        conn.commit()
        cursor.close()
    logger.info(f"DB process {instance_id} updated status code to {status_code}.")


def task_completion_to_db(instance_id, completion_value, bonus_value, agent_id, conn):
    """Update task completion into database."""
    insert_episode_query = """
        UPDATE sessions SET completed=%s, bonus=%s
        WHERE env_instance_id=%s AND agent_key=%s
        """
    data = (completion_value, bonus_value, instance_id, agent_id)
    with conn.cursor() as cursor:
        cursor.execute(insert_episode_query, data)
        conn.commit()
        cursor.close()


def step_enqueue_process_fn(
    input_queue,
    input_queue_priority,
    list_of_agents,
    instance_id,
    database_exit_event,
    database_process_is_finished_event,
):
    def process_data(data):
        if data[0] == "episode_to_db":
            logger.info(f"Enqueueing episode data for game id {data[1]}")
            episode_to_db(data[2], data[1], conn)
            logger.info(f"Done enqueueing episode data for game id {data[1]}")
        elif data[0] == "completion_to_db":
            logger.info(f"Enqueueing completion data for instance id {data[1]} agent id {data[4]}")
            task_completion_to_db(data[1], data[2], data[3], data[4], conn)
            logger.info(f"Done enqueueing completion data for instance id {data[1]} agent id {data[4]}")

    logger.info(f"DB process {instance_id} started.")
    #################
    # DB connection #
    #################

    MYSQL_USER = os.environ.get("MYSQL_USER")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
    MYSQL_HOST = os.environ.get("MYSQL_HOST")
    MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE")

    # TODO: Shouldn't we try-catch?
    conn = connector.connect(user=MYSQL_USER, password=MYSQL_PASSWORD, host=MYSQL_HOST, database=MYSQL_DATABASE)

    i = 0

    while not (database_exit_event.is_set() and input_queue.empty() and input_queue_priority.empty() and i > 10):
        try:
            if not input_queue_priority.empty():
                data = input_queue_priority.get()
                process_data(data)
            if input_queue_priority.empty() and not input_queue.empty():
                data = input_queue.get()
                process_data(data)
        except ValueError:
            print("Excepted ValueError on input_queue.get()")
            # return 0
        except OSError:
            print("Excepted OSError on input_queue.get()")
            # return 0
        except queue.Empty:
            print("Excepted queue.Empty on input_queue.get()")
        if database_exit_event.is_set():
            i += 1
        time.sleep(0.1)

    logger.info(f"DB process {instance_id} exiting.")
    mark_db_process_status_code(instance_id, 1, conn)
    database_process_is_finished_event.set()


class EnvProcess:
    def __init__(
        self,
        instance_id,
        task_id,
        command_child,
        action_recv,
        step_info_send,
        env_process_exit_event,
        env_process_episode_running_event,
        env_process_stop_episode_event,
        env_process_is_finished_event,
        database_queue,
        database_queue_priority,
        fps=60,
    ):
        self.instance_id = instance_id
        self.task_id = task_id
        self.command_child = command_child
        self.action_recv = action_recv
        self.step_info_send = step_info_send
        self.env_process_exit_event = env_process_exit_event
        self.env_process_episode_running_event = env_process_episode_running_event
        self.env_process_stop_episode_event = env_process_stop_episode_event
        self.env_process_is_finished_event = env_process_is_finished_event

        self.env = crowdplay_environments[task_id]["make_env"]()
        self.observation_space = self.env.observation_space
        self.action_space = self.env.action_space
        self.agents = {agent: (None, None) for agent in self.env.list_of_agents}

        self.task_callables = {}
        self.task_callables_state = {}
        if "task_callables" in crowdplay_environments[task_id]:
            if "Score" not in crowdplay_environments[task_id]["task_callables"]:
                self.task_callables["Score"] = ScoreCallable(self.agents)
                self.task_callables_state["Score"] = {agent: 0 for agent in self.agents}
            for callable in crowdplay_environments[task_id]["task_callables"]:
                self.task_callables[callable] = crowdplay_environments[task_id]["task_callables"][callable]()
                self.task_callables_state[callable] = {agent: 0 for agent in self.agents}
        if "task_requirements" not in crowdplay_environments[task_id]:
            crowdplay_environments[task_id]["task_requirements"] = {}

        self.task_done = {agent: 0 for agent in self.agents}
        self.task_done_notified = {agent: False for agent in self.agents}
        self.task_bonus = {agent: 0 for agent in self.agents}

        self.scores = {agent: 0 for agent in self.agents}

        self.fps = fps
        if "realtime" in crowdplay_environments[task_id]:
            self.realtime = crowdplay_environments[task_id]["realtime"]
        else:
            self.realtime = CROWDPLAY_REALTIME_REALTIME

        # Keep list of recent steps
        # self.step_infos_for_db = []
        self.trajectory = []

        # Start DB queue process
        # TODO Does a thread make more sense here?
        self.database_queue = database_queue
        self.database_queue_priority = database_queue_priority
        # Notice: We use the same exit event for EnvProcess and database process termination.
        self.database_exit_event = self.env_process_exit_event

        # Set up AI policies if not existing already
        self.ai_policies = {}
        for agent_id in crowdplay_environments[self.task_id]["ai_agent_map_always"]:
            if agent_id in self.env.list_of_agents:
                ai_policy_id = crowdplay_environments[self.task_id]["ai_agent_map_always"][agent_id]
                # policy_id_string = f"{checkpoint_file}_{checkpoint_agent_id}"
                try:
                    if agent_id not in self.ai_policies:
                        self.ai_policies[agent_id] = registered_ai_policies[ai_policy_id]()
                except Exception:
                    logger.error(f"Error: cannot create or find AI policy {ai_policy_id}")
                    raise AiPolicyError()
            else:
                logger.warn(f"Agent ID {agent_id} in AI policy map, but not in environmnent list of agents.")

        # Create policies for fallback agents too to avoid performance issue mid-game
        for agent_id in crowdplay_environments[self.task_id]["ai_agent_map_fallback"]:
            if agent_id in self.env.list_of_agents:
                ai_policy_id = crowdplay_environments[self.task_id]["ai_agent_map_fallback"][agent_id]
                # policy_id_string = f"{checkpoint_file}_{checkpoint_agent_id}"
                try:
                    if agent_id not in self.ai_policies:
                        self.ai_policies[agent_id] = registered_ai_policies[ai_policy_id]()
                except Exception:
                    logger.error(f"Error: cannot create or find AI policy {ai_policy_id}")
                    raise AiPolicyError()
            else:
                logger.warn(f"Agent ID {agent_id} in AI policy map, but not in environmnent list of agents.")
        self.setup_sql()

    def setup_sql(self):
        MYSQL_USER = os.environ.get("MYSQL_USER")
        MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
        MYSQL_HOST = os.environ.get("MYSQL_HOST")
        MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE")
        self.conn = connector.connect(
            user=MYSQL_USER, password=MYSQL_PASSWORD, host=MYSQL_HOST, database=MYSQL_DATABASE
        )

        pass

    def process_command(self):
        if self.command_child.poll():
            cmd, data = self.command_child.recv()
            if cmd == "start_episode":
                game_id = data["game_id"]
                if not self.env_process_episode_running_event.is_set():
                    # TODO store in class?
                    self.game_id = game_id
                    self.episode_thread = threading.Thread(target=self.run_episode, args=(game_id,))
                    self.episode_thread.start()
                    # self.run_episode(game_id)
                else:
                    # TODO this shouldn't happen. Use multiprocessing event for EnvRunner._is_episode_running?
                    logger.error(f"Told to start episode {game_id}, but episode already running.")
            # TODO don't seem to need these anymore thanks to Events?
            # elif cmd == 'stop_episode':
            #     self._stop_episode.set()
            #     # TODO should we wait here?
            #     # self.episode_thread.join()
            # elif cmd == 'stop_runner':
            #     self._stop_runner.set()
            #     self.close_process()
            #     return 0
            elif cmd == "assign_agent":
                self.assign_agent(data["agent_id"], data["assign_to"])
            elif cmd == "set_fps":
                self.fps = data

    def process_command_loop(self):
        while not self.env_process_exit_event.is_set():
            self.process_command()
            time.sleep(0.01)
        logger.info(f"EnvProcess {self.instance_id} command loop exiting.")
        self.close_process()

    def run(self):
        logger.info(f"EnvProcess {self.instance_id} starting.")
        self.process_command_loop()

    def run_episode(self, game_id):
        self.env_process_episode_running_event.set()
        self.env_process_is_finished_event.clear()
        logger.info(f"Episode with id {game_id} in EnvProcess {self.instance_id} started.")
        self.episode_start_to_db(game_id)

        # Set up basics
        episode_end = False
        step_iter = 0
        next_frame_time = time.time() + 1 / self.fps

        # Reset environment.
        # We essentially discard the reset step,
        #  and perform one noop step before sending data to client and DB.
        prev_obs = self.env.reset()

        # Reset AI framebuffers
        ai_framebuffers = {}

        # Reset actions
        action = {
            agent_key: (
                crowdplay_environments[self.task_id]["noop_action"]
                if "noop_action" in crowdplay_environments[self.task_id]
                else self.env.get_noop_action(agent_key)
                if hasattr(self.env, "get_noop_action")
                else get_noop_for_space(self.env.action_space[agent_key])
                if hasattr(self.env, "action_space") and isinstance(self.env.action_space, dict)
                else get_noop_for_space(self.env.action_space)
                if hasattr(self.env, "action_space") and isinstance(self.env.action_space, spaces.Space)
                else 0
            )
            for agent_key in self.env.list_of_agents
        }
        action_step_iter = {agent_key: -1 for agent_key in self.env.list_of_agents}
        # We keep another dict that tells us if each agent has completely lifted all keypresses since their last action.
        # In turn-based environments this tells us if the agent is ready for their next action / turn.
        action_reset = {agent_key: False for agent_key in self.env.list_of_agents}

        # Track callables for this episode only.
        episode_callables = {}
        episode_callables_state = {}
        if "task_callables" in crowdplay_environments[self.task_id]:
            for callable in crowdplay_environments[self.task_id]["task_callables"]:
                episode_callables[callable] = crowdplay_environments[self.task_id]["task_callables"][callable]()
                episode_callables_state[callable] = 0

        self.command_child.send(("episode_starting", {"game_id": game_id}))

        # Send data to client and append for DB
        if hasattr(self.env, "crowdplay_render"):
            client_obs = self.env.crowdplay_render()
        else:
            client_obs = prev_obs
        self.step_to_clients(
            {
                "obs": client_obs,
                "reward": {agent: 0.0 for agent in self.agents},
                "done": {agent: False for agent in self.agents},
                "info": {agent: {} for agent in self.agents},
                "step_iter": 0,
                "task_info": {agent: [] for agent in self.agents},
                "task_complete": {agent: 0.0 for agent in self.agents},
                "scores": {agent: 0 for agent in self.agents},
                "task_bonus": {agent: 0 for agent in self.agents},
            }
        )

        # Episode loop
        while (
            episode_end is False
            and not self.env_process_exit_event.is_set()
            and not self.env_process_stop_episode_event.is_set()
        ):
            # self.process_command()
            # Get current action and timestep. Poll until pipe is empty.
            while self.action_recv.poll():
                agent, agent_action, agent_action_step_iter = self.action_recv.recv()
                if self.realtime == CROWDPLAY_REALTIME_REALTIME:
                    # We're in a realtime env.
                    action[agent] = agent_action
                    action_step_iter[agent] = agent_action_step_iter
                elif self.realtime == CROWDPLAY_REALTIME_TURNBASED_WAITFORNEWKEY:
                    # TODO THIS IS NOW TEMPORARILY BROKEN.
                    # We're in a turn-based env. Register new keypresses only if the user lifted all keys in between.
                    if agent_action == -1:
                        action_reset[agent] = True
                    elif action_reset[agent] and agent_action_step_iter >= step_iter:
                        # We register new keypresses only if the user released all keys in between,
                        # and only if they are for the current iteration.
                        # There should never be keypresses from future iterations here!
                        assert agent_action_step_iter == step_iter
                        action[agent] = agent_action
                        action_step_iter[agent] = agent_action_step_iter
                        action_reset[agent] = False
                else:
                    # Turn-based, but advance state if keys are held down:
                    # This will run at a maximum of self.fps FPS, but in practice
                    # usually slower even if keys are held down.
                    if agent_action_step_iter >= step_iter:
                        assert agent_action_step_iter == step_iter
                        action[agent] = agent_action
                        action_step_iter[agent] = agent_action_step_iter

            if not self.realtime == CROWDPLAY_REALTIME_REALTIME:
                # Check that we have received new actions from all human agents
                if not all(
                    [
                        action_step_iter[agent] == step_iter
                        for agent in [a for a in self.agents if self.agents[a][0] == 1]
                    ]
                ):
                    continue

            # Get AI agent actions
            for agent_id in self.agents:
                if self.agents[agent_id][0] == 2:
                    # Create framebuffer if necessary.
                    # This happens at episode start and on human user disconnect.
                    if agent_id not in ai_framebuffers:
                        ai_policy_id = (
                            crowdplay_environments[self.task_id]["ai_agent_map_always"][agent_id]
                            if agent_id in crowdplay_environments[self.task_id]["ai_agent_map_always"]
                            else crowdplay_environments[self.task_id]["ai_agent_map_fallback"][agent_id]
                        )
                        ai_framebuffers[agent_id] = registered_ai_framebuffers[ai_policy_id]()
                    # Get AI action
                    ac = self.ai_policies[agent_id].compute_action(ai_framebuffers[agent_id].get_obs())
                    # Convert AI action to int insteand of numpy.int64 to be able to save to DB
                    # TODO we need a way to serialise numpy types!!!
                    action[agent_id] = {key: int(ac[key]) for key in ac}
                    action_step_iter[agent_id] = step_iter

            # Actual env step
            try:
                obs, reward, done, info = self.env.step(action)
                # If the env has a render() function, we use this to get the observation to send to the client.
                # This is useful for instance if we want to process the image or format the text output for humans.
                # In that case, we still want to store the unprocessed observation in the DB however.
                if hasattr(self.env, "crowdplay_render"):
                    client_obs = self.env.crowdplay_render()
                else:
                    client_obs = obs
                step_iter += 1

                for agent_id in self.agents:
                    if self.agents[agent_id][0] == 2 and agent_id in ai_framebuffers:
                        ai_framebuffers[agent_id].add_obs(obs[agent_id])

            except IndexError:
                # Wrong action. Do nothing
                # TODO: need to handle this case
                pass
            except KeyError:
                # Can happen with ai_framebuffers?
                # Maybe because an agent gets disconnected between l467 and l491?
                # TODO: Investigate.
                # TODO: Should we have a huge try-except block around the entire loop iteration?
                pass
            else:
                # Check for shutdown before sending data to clients.
                # Seems to help avoid pipe blocking.
                # Maybe not needed anymore.
                if self.env_process_stop_episode_event.is_set() or self.env_process_exit_event.is_set():
                    episode_end = "stopped"
                    break

                for callable in self.task_callables:
                    self.task_callables_state[callable] = self.task_callables[callable](
                        {
                            "prev_obs": prev_obs,
                            "action": action,
                            "action_step_iter": action_step_iter,
                            "obs": obs,
                            "reward": reward,
                            "done": done,
                            "info": info,
                            "step_iter": step_iter,
                        }
                    )
                for callable in episode_callables:
                    episode_callables_state[callable] = episode_callables[callable](
                        {
                            "prev_obs": prev_obs,
                            "action": action,
                            "action_step_iter": action_step_iter,
                            "obs": obs,
                            "reward": reward,
                            "done": done,
                            "info": info,
                            "step_iter": step_iter,
                        }
                    )

                client_task_info = {agent: [] for agent in self.agents}
                for agent in self.agents:
                    self.task_done[agent] = min(
                        [
                            self.task_callables_state[callable][agent]
                            / crowdplay_environments[self.task_id]["task_requirements"][callable]
                            for callable in crowdplay_environments[self.task_id]["task_requirements"]
                        ]
                        + [
                            1,
                        ]
                    )
                    if (
                        "task_requirements" in crowdplay_environments[self.task_id]
                        and len(crowdplay_environments[self.task_id]["task_requirements"]) != 0
                    ):
                        client_task_info[agent].append(
                            {
                                "name": "Overall task completion",
                                "state": f"{int(100*self.task_done[agent])}%",
                                "required": "100%",
                            }
                        )
                    for callable in self.task_callables_state:
                        client_task_info[agent].append(
                            {
                                "name": callable,
                                "state": str(self.task_callables_state[callable][agent])
                                if not isinstance(self.task_callables_state[callable][agent], float)
                                else str(int(100 * self.task_callables_state[callable][agent]) / 100),
                            }
                        )
                        if callable in crowdplay_environments[self.task_id]["task_requirements"]:
                            client_task_info[agent][-1]["required"] = str(
                                crowdplay_environments[self.task_id]["task_requirements"][callable]
                            )
                    if (
                        "task_bonus_target" in crowdplay_environments[self.task_id]
                        and "task_bonus_value" in crowdplay_environments[self.task_id]
                    ):
                        self.task_bonus[agent] = crowdplay_environments[self.task_id]["task_bonus_value"](
                            agent,
                            min(
                                [
                                    self.task_callables_state[callable][agent]
                                    / crowdplay_environments[self.task_id]["task_bonus_target"][callable]
                                    for callable in crowdplay_environments[self.task_id]["task_bonus_target"]
                                ]
                            ),
                            self.task_callables_state,
                        )
                    else:
                        self.task_bonus[agent] = 0

                for agent in self.agents:
                    self.scores[agent] += int(reward[agent])
                    # client_obs[agent]['Score'] = self.scores[agent]
                    # client_obs[agent]['Task Completed'] = f"{int(100*self.task_done[agent])}%"
                    # TODO reimplement bonus estimate
                    # client_obs[agent]['Estimated Bonus Payment'] = f'{self.task_bonus[agent]:.2f} $'
                    if self.task_done[agent] >= 1 and not self.task_done_notified[agent] and self.agents[agent][0] == 1:
                        self.database_queue_priority.put(
                            ("completion_to_db", self.instance_id, self.task_done[agent], self.task_bonus[agent], agent)
                        )
                        self.task_done_notified[agent] = True

                user_types = {agent: self.agents[agent][0] for agent in self.agents}

                # Send data to client and append for DB
                self.step_to_clients(
                    {
                        "obs": client_obs,
                        "reward": reward,
                        "done": done,
                        "info": info,
                        "step_iter": step_iter,
                        "task_info": client_task_info,
                        "task_complete": self.task_done,
                        "scores": self.scores,
                        "task_bonus": self.task_bonus,
                    }
                )
                # self.step_infos_for_db.append({
                #     "prev_obs": prev_obs,
                #     "action": action,
                #     "action_step_iter": action_step_iter,
                #     "obs": obs,
                #     "reward": reward,
                #     "done": done,
                #     "info": info,
                #     "step_iter": step_iter,
                #     "user_type": user_types
                # })
                self.trajectory.append(
                    copy.deepcopy(
                        {
                            "prev_obs": prev_obs,
                            "action": action,
                            "action_step_iter": action_step_iter,
                            # "obs": obs,
                            "reward": reward,
                            "done": done,
                            "info": info,
                            "step_iter": step_iter,
                            "user_type": user_types,
                            "task_callables": self.task_callables_state,
                            "episode_callables": episode_callables_state,
                        }
                    )
                )

                # Store previous obs
                prev_obs = obs

            if all(done.values()):
                # TODO: multiagent. Done for all the agents?
                episode_end = "done"
                break

            # Sleep until end of regular 1/fps intervals.
            time.sleep(max(0.00001, next_frame_time - time.time()))
            next_frame_time += 1 / self.fps

        # Now at end of episode.
        self.episode_end_to_db(game_id, episode_callables_state)
        if episode_end is False and (
            self.env_process_exit_event.is_set() or self.env_process_stop_episode_event.is_set()
        ):
            episode_end = "stopped"
        logger.info(f"Episode with id {game_id} in EnvProcess {self.instance_id} ended. Reason: {episode_end}")

        for agent in self.agents:
            if self.agents[agent][0] == 1:
                self.database_queue_priority.put(
                    ("completion_to_db", self.instance_id, self.task_done[agent], self.task_bonus[agent], agent)
                )
            # self.task_completion_to_db(self.task_done[agent], self.task_bonus[agent], agent)

        # TODO: multiagent? might not be the end for some agents
        self.command_child.send(("episode_end", {"reason": episode_end, "game_id": game_id}))
        # for agent_key in self.agents:
        #     room = f'{self.instance_id}_{agent_key}'
        #     self.notify_client(episode_end, room)

        # We put the enqueue operation into a separate thread / process
        # so that it doesn't block the main thread.
        self.database_queue.put(("episode_to_db", game_id, self.trajectory.copy()))

        # Empty step infos so we can start the next episode.
        # self.step_infos_for_db = []
        self.trajectory = []

        self.env_process_episode_running_event.clear()

        logger.info(f"Episode thread with id {game_id} in EnvProcess {self.instance_id} exiting.")

    # def run_episode(self):
    #     while True:
    #         pass
    #         time.sleep(0.01)
    #     pass

    def step_to_clients(self, step_info):
        """Sends step data to main process to be sent to clients."""
        step_iter = step_info["step_iter"]
        obs_extra_all_agents = observation_to_serializable(step_info["obs"], image_to="base64")

        data_to_send_all_agents = []

        for agent_key in self.env.list_of_agents:
            # We send the frame separetly

            # obs_image = obs_extra_all_agents[agent_key]["image"]
            obs = obs_extra_all_agents[agent_key]
            # del obs_extra["image"]

            reward = float(step_info["reward"][agent_key])
            done = step_info["done"][agent_key]

            task_info = step_info["task_info"][agent_key]
            score = step_info["scores"][agent_key]

            # if "human_player_map" in crowdplay_environments[self.task_id]:
            #     obs_extra["Your Player"] = f"{crowdplay_environments[self.task_id]['human_player_map'][agent_key]}"

            data_to_send = {
                # "obs_image": obs_image,
                # "obs_extra": obs_extra,
                "obs": obs,
                "reward": reward,
                "done": done,
                "step_iter": step_iter,
                "task_info": task_info,
                "task_complete": f"{step_info['task_complete'][agent_key]:.2f}",
                "score": score,
                "task_bonus": f"{step_info['task_bonus'][agent_key]:.2f}",
            }

            room = f"{self.instance_id}_{agent_key}"

            data_to_send_all_agents.append((room, data_to_send))

        self.step_info_send.send(data_to_send_all_agents)

    def episode_start_to_db(self, game_id):
        """Inserts episode start into database."""
        insert_episode_query = """
            INSERT INTO games (
                id,
                env_instance_id,
                started_on
            )
            VALUES ( %s, %s, %s )
            """
        data = (game_id, self.instance_id, datetime.utcnow())
        with self.conn.cursor() as cursor:
            cursor.execute(insert_episode_query, data)
            self.conn.commit()
            cursor.close()

    def episode_end_to_db(self, game_id, episode_callables_state):
        """Inserts episode end into database."""
        update_episode_query = """
            UPDATE games SET ended_on = %s WHERE id = %s
            """
        data = (datetime.utcnow(), game_id)
        with self.conn.cursor() as cursor:
            cursor.execute(update_episode_query, data)
            self.conn.commit()
            cursor.close()
        with self.conn.cursor() as cursor:
            for callable in self.task_callables_state:
                for agent in self.task_callables_state[callable]:
                    # Track overall task progress.
                    update_env_task_completion_query = """
                        REPLACE INTO task_callable_per_env (env_instance_id, agent_key, callable_key, value_achieved,
                        value_required) VALUES ( %s, %s, %s, %s, %s )
                        """  # noqa: E501
                    data = (
                        self.instance_id,
                        agent,
                        callable,
                        str(self.task_callables_state[callable][agent]),
                        str(crowdplay_environments[self.task_id]["task_requirements"][callable])
                        if (
                            "task_requirements" in crowdplay_environments[self.task_id]
                            and callable in crowdplay_environments[self.task_id]["task_requirements"]
                        )
                        else "",
                    )
                    cursor.execute(update_env_task_completion_query, data)
                    self.conn.commit()
                    # Track task progress at end of this episode for debugging / logging purposes.
                    update_env_task_completion_query_episode = """
                        REPLACE INTO task_callable_per_game (env_instance_id, episode_id, agent_key, callable_key,
                        value_achieved, value_required) VALUES ( %s, %s, %s, %s, %s, %s )
                        """
                    data = (
                        self.instance_id,
                        game_id,
                        agent,
                        callable,
                        str(self.task_callables_state[callable][agent]),
                        str(crowdplay_environments[self.task_id]["task_requirements"][callable])
                        if (
                            "task_requirements" in crowdplay_environments[self.task_id]
                            and callable in crowdplay_environments[self.task_id]["task_requirements"]
                        )
                        else "",
                    )
                    cursor.execute(update_env_task_completion_query_episode, data)
                    self.conn.commit()
            for callable in episode_callables_state:
                for agent in episode_callables_state[callable]:
                    # Track task progress for just this episode
                    episode_callable_query = """
                        REPLACE INTO episode_callable (env_instance_id, episode_id, agent_key, callable_key,
                        value_achieved, value_required) VALUES ( %s, %s, %s, %s, %s, %s )
                        """
                    data = (
                        self.instance_id,
                        game_id,
                        agent,
                        callable,
                        str(episode_callables_state[callable][agent]),
                        str(crowdplay_environments[self.task_id]["task_requirements"][callable])
                        if (
                            "task_requirements" in crowdplay_environments[self.task_id]
                            and callable in crowdplay_environments[self.task_id]["task_requirements"]
                        )
                        else "",
                    )
                    cursor.execute(episode_callable_query, data)
                    self.conn.commit()
            cursor.close()

    def task_completion_to_db(self, completion_value, bonus_value, agent_id):
        """Update task completion into database."""
        insert_episode_query = """
            UPDATE sessions SET completed=%s, bonus=%s
            WHERE env_instance_id=%s AND agent_key=%s
            """
        data = (completion_value, bonus_value, self.instance_id, agent_id)
        with self.conn.cursor() as cursor:
            cursor.execute(insert_episode_query, data)
            self.conn.commit()
            cursor.close()

    def assign_agent(self, agent_id, assign_to):
        """Assigns an agent"""
        if agent_id in self.agents:
            if self.agents[agent_id][0] == 1:
                self.database_queue_priority.put(
                    (
                        "completion_to_db",
                        self.instance_id,
                        self.task_done[agent_id],
                        self.task_bonus[agent_id],
                        agent_id,
                    )
                )
            self.agents[agent_id] = assign_to
        else:
            logger.error(f"Error: agent key {agent_id} doesn't exist in instance {self.instance_id}")
            raise KeyError

    def close_process(self):
        # TODO
        logger.info(f"EnvProcess {self.instance_id} closing.")
        self.env_process_exit_event.set()
        if hasattr(self, "episode_thread"):
            logger.info(f"EnvProcess {self.instance_id} waiting for episode thread to finish.")
            self.episode_thread.join()
        self.database_exit_event.set()
        self.database_queue.close()
        self.database_queue_priority.close()
        self.env_process_stop_episode_event.set()
        self.mark_envprocess_status_code(1)
        self.env_process_is_finished_event.set()
        logger.info(f"EnvProcess {self.instance_id} closed.")

    def mark_envprocess_status_code(self, status_code):
        logger.info(f"EnvProcess {self.instance_id} updating status code to {status_code}.")
        updatequery = """
        UPDATE crowdplaydb.envs SET crowdplaydb.envs.envprocess_status_code = %s WHERE crowdplaydb.envs.instance_id=%s;
        """
        data = (status_code, self.instance_id)
        with self.conn.cursor() as cursor:
            cursor.execute(updatequery, data)
            self.conn.commit()
            cursor.close()
        logger.info(f"EnvProcess {self.instance_id} updated status code to {status_code}.")


def run_env_process(
    instance_id,
    task_id,
    command_child,
    action_recv,
    step_info_send,
    env_process_exit_event,
    env_process_episode_running_event,
    env_process_stop_episode_event,
    env_process_is_finished_event,
    database_queue,
    database_queue_priority,
    fps,
):
    env_process = EnvProcess(
        instance_id,
        task_id,
        command_child,
        action_recv,
        step_info_send,
        env_process_exit_event,
        env_process_episode_running_event,
        env_process_stop_episode_event,
        env_process_is_finished_event,
        database_queue,
        database_queue_priority,
        fps,
    )
    env_process.run()
    pass


class EnvRunner:
    def __init__(self, make_env, instance_id, task_id, fps=60, seed=None):
        # TODO remove make_env, seed
        super().__init__()

        # Basic info, won't change.
        self.instance_id = instance_id
        self.task_id = task_id

        # Observation and action spaces
        self.env = crowdplay_environments[task_id]["make_env"]()
        # TODO either make and delete env, or start background process and wait for env ready state?
        self.observation_space = self.env.observation_space
        self.action_space = self.env.action_space

        # Data structure that maps agent_id to connected human or AI player,
        # or None if agent is available for new connection.
        # (None, None): No agent connected
        # (1, None): Human agent assigned, but pending
        # (1, sid): Human aggent, connected
        # (2, policy_id_string): AI agent with given policy
        self.agents = {agent: (None, None) for agent in self.env.list_of_agents}

        # Pipes for communication
        self.command_parent, self.command_child = multiprocessing.Pipe()
        self.action_recv, self.action_send = multiprocessing.Pipe(duplex=False)
        # TODO would a queue be faster here too?! See below.
        self.step_info_client_recv, self.step_info_client_send = multiprocessing.Pipe(duplex=False)
        # self.agent_command_parent, self.agent_comand_child = multiprocessing.Pipe()

        self.env_process_exit_event = multiprocessing.Event()
        self.env_process_episode_running_event = multiprocessing.Event()
        self.env_process_stop_episode_event = multiprocessing.Event()
        self.env_process_is_finished_event = multiprocessing.Event()

        self.database_process_is_finished_event = multiprocessing.Event()
        # For some reason using a Pipe instead here is really bad for performance.
        # Leads to visible hangs in the game whenever a batch of steps is sent through the Pipe.
        self.database_queue = multiprocessing.Queue()
        self.database_queue_priority = multiprocessing.Queue()
        self.database_process = multiprocessing.Process(
            target=step_enqueue_process_fn,
            args=(
                self.database_queue,
                self.database_queue_priority,
                list(self.agents.keys()),
                self.instance_id,
                self.env_process_exit_event,
                self.database_process_is_finished_event,
            ),
        )
        self.database_process.start()

        self.env_process = multiprocessing.Process(
            target=run_env_process,
            args=(
                instance_id,
                task_id,
                self.command_child,
                self.action_recv,
                self.step_info_client_send,
                self.env_process_exit_event,
                self.env_process_episode_running_event,
                self.env_process_stop_episode_event,
                self.env_process_is_finished_event,
                self.database_queue,
                self.database_queue_priority,
                fps,
            ),
        )
        self.env_process.start()

        self._episode_is_running = False
        self._stop_runner = False

        # Connect AI agents.
        for agent, ai_policy_id in crowdplay_environments[self.task_id]["ai_agent_map_always"].items():
            self.assign_agent(agent, (2, ai_policy_id))

        self.fps = fps
        if "realtime" in crowdplay_environments[task_id]:
            self.realtime = crowdplay_environments[task_id]["realtime"]
        else:
            self.realtime = CROWDPLAY_REALTIME_REALTIME

        self.start_time = datetime.now()

        # start main loop
        socketio.start_background_task(self._command_loop, current_app._get_current_object())

    # def __del__(self):
    #     # TODO this doesn't seem to be working / isn't called. Figure out where to do cleanup.
    #     logger.info(f'EnvRunner {self.instance_id} deleted.')
    #     self._stop_runner = True

    def _command_loop(self, app):
        """Waits for command from EnvProcess and acts on it."""
        while True:
            if self.command_parent.poll():
                cmd, data = self.command_parent.recv()
                if cmd == "episode_end":
                    self.on_episode_end(data["game_id"], data["reason"])
                elif cmd == "episode_starting":
                    self.mark_episode_started(data["game_id"])
            elif self._stop_runner:
                break
            if (
                "human_timeout" in crowdplay_environments[self.task_id]
                and datetime.now() - self.start_time > crowdplay_environments[self.task_id]["human_timeout"]
            ):
                for agent in self.agents:
                    if self.agents[agent][0] == 0 or self.agents[agent][0] is None:
                        logger.warn(
                            f"Instance {self.instance_id} timed out waiting for human players to join. \
                                Assigning agent {agent} to fallback AI policy."
                        )
                        ai_policy_id = crowdplay_environments[self.task_id]["ai_agent_map_fallback"][agent]
                        self.assign_agent(agent, (2, ai_policy_id))
                        # self.assign_agent(agent, (2, crowdplay_environments[self.task_id]['ai_agent_map_fallback'][agent]))
                        self.broadcast(
                            "countdown_start",
                            {
                                "time": 5,
                                "play_sound": True,
                            },
                        )
            socketio.sleep(0.01)

    def _step_to_client_loop(self, app):
        """Waits for step_info from EnvProcess and sends to client."""
        while self._episode_is_running:
            if self.step_info_client_recv.poll():
                # Receive until queue empty, send only latest data.
                # If we're too slow, we prefer to drop frames, rather than send them slow-motion.
                while self.step_info_client_recv.poll():
                    step_info = self.step_info_client_recv.recv()
                self.step_to_client(step_info)
            socketio.sleep(1 / (4 * self.fps))

    def assign_agent(self, agent_id, assign_to):
        """Assigns an agent"""
        if agent_id in self.agents:
            self.agents[agent_id] = assign_to
            self.command_parent.send(("assign_agent", {"agent_id": agent_id, "assign_to": assign_to}))
        else:
            logger.error(f"Error: agent key {agent_id} doesn't exist in instance {self.instance_id}")
            raise KeyError

    def set_action(self, agent, action, step_iter):
        """Sets the current action for a particular agent."""
        self.action_send.send((agent, action, step_iter))

    def set_fps(self, fps):
        """Set FPS."""
        self.command_parent.send(("set_fps", fps))
        self.fps = fps

    def step_to_client(self, step_info):
        """Sends step data to clients. Takes already processed data."""
        for room, data_to_send in step_info:
            self.notify_client("step", room, data=data_to_send)

    def on_episode_end(self, game_id, reason):
        """Sets episode running state to False and notifies clients of episode end."""
        self._episode_is_running = False
        for agent_key in self.agents:
            room = f"{self.instance_id}_{agent_key}"
            self.notify_client(reason, room)

    def start_episode(self):
        """Starts an episode, if there is not already one running"""
        # TODO what if already started?
        if not self._episode_is_running:

            # Generate new game ID
            # TODO put this in a queue instead of straight into state?
            # What if EnvProcess is still finishing up previous episode?
            self.game_id = uuid4().hex

            self.broadcast("starting", self.game_id)

            self.command_parent.send(("start_episode", {"game_id": self.game_id}))
            while not self._episode_is_running:
                socketio.sleep(0.001)
            socketio.start_background_task(self._step_to_client_loop, current_app._get_current_object())

            self.broadcast("started", self.game_id)

        return self.game_id

    def mark_episode_started(self, game_id):
        self._episode_is_running = True

    def stop_episode(self):
        """Stops the current episode, if there is one running."""
        # Stopping episode by setting this flag
        self._episode_is_running = False
        self.command_parent.send(("stop_episode", None))
        # TODO should we wait for episode to finish?

    def stop_runner(self):
        """Stops the EnvRunner object."""
        # TODO Implement properly
        logger.info(f"EnvRunner {self.instance_id} stopping.")
        self.env_process_exit_event.set()
        while self.step_info_client_recv.poll():
            self.step_info_client_recv.recv()
            socketio.sleep(0.01)
        self._stop_runner = True
        # socketio.sleep(1)
        # TODO why does nothing else work?!
        # Not even waiting for an event seems to work. Main process doesn't hang, but EnvProcess persists if we wait.
        for i in range(600):
            if self.env_process_is_finished_event.is_set() and self.database_process_is_finished_event.is_set():
                break
            if i > 10:
                logger.warn(f"Env/DB processes for instance {self.instance_id} still not exited after {i} seconds.")
            socketio.sleep(1)
        self.env_process_is_finished_event.wait(1)
        # Wait up to 10 seconds for DB process to finish
        self.database_process_is_finished_event.wait(1)
        socketio.sleep(0.01)
        if not self.env_process_is_finished_event.is_set():
            logger.warn(f"EnvProcess with ID {self.instance_id} did not exit in time and will be killed.")
            self.set_envprocess_exit_status()
        if not self.database_process_is_finished_event.is_set():
            logger.warn(f"DB process with ID {self.instance_id} did not exit in time and will be killed.")
            self.set_dbprocess_exit_status()
        self.env_process.terminate()
        self.env_process.kill()
        # TODO now not killing DB process, check that this always exits properly!
        # self.database_process.terminate()
        # self.database_process.kill()
        # self.command_parent.send(('stop_runner', None))
        # self.env_process.join()
        # self.env_process.close()
        logger.info(f"EnvRunner {self.instance_id} stopped.")

    def set_envprocess_exit_status(self):
        env_model = EnvModel().query.get(self.instance_id)
        if env_model.envprocess_status_code != 1:
            env_model.envprocess_status_code = 2
            db.session.commit()
        else:
            logger.warn(f"EnvProcess with ID {self.instance_id} did not exit, but exit code is set to 1.")

    def set_dbprocess_exit_status(self):
        env_model = EnvModel().query.get(self.instance_id)
        if env_model.dbprocess_status_code != 1:
            env_model.dbprocess_status_code = 2
            db.session.commit()
        else:
            logger.warn(f"DB process with ID {self.instance_id} did not exit, but exit code is set to 1.")

    @staticmethod
    def notify_client(event, room, data=None):
        """Emits message to specific room."""
        socketio.emit(event, data, room=room, namespace=Config.WS_NS)

    def broadcast(self, event, data=None):
        """Emits message to instance room i.e. all connected clients."""
        socketio.emit(event, data, room=f"{self.instance_id}", namespace=Config.WS_NS)
