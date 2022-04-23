import gzip
import multiprocessing
import os
import pickle
import queue
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from crowdplay_backend.ai_policy import (
    MaxAndSkipAndWarpAndScaleAndStackFrameBuffer,
    PretrainedRLLibPolicy,
)
from crowdplay_backend.environments import crowdplay_environments
from crowdplay_backend.EnvRunner import EnvProcess
from crowdplay_datasets.dataset import (
    EnvironmentModel,
    EpisodeModel,
    get_data_dir,
    get_engine_and_session,
)
from gym.core import Env

"""HIGHLY EXPERIMENTAL This script generates AI-only episodes from the CrowdPlay engine, but saving directly to the local database."""


def local_episode_to_db(trajectory, episode_id):
    """Inserts as gzipped pickled trajectory into local filesystem"""

    gzipped_trajectory = gzip.compress(pickle.dumps(trajectory))

    with open(f"{get_data_dir()}/{episode_id}.pickle.gz", "wb") as f:
        f.write(gzipped_trajectory)
        f.close()


def local_step_enqueue_process_fn(
    input_queue,
    input_queue_priority,
    list_of_agents,
    instance_id,
    database_exit_event,
    database_process_is_finished_event,
):
    def process_data(data):
        if data[0] == "step_to_db":
            pass
        elif data[0] == "episode_to_db":
            local_episode_to_db(data[2], data[1])
        elif data[0] == "completion_to_db":
            pass

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
    database_process_is_finished_event.set()


class LocalEnvProcess(EnvProcess):
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
        fps,
        checkpoint,
        agent_id,
    ):
        super().__init__(
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

        policy_id_string = f"{checkpoint}_{agent_id}"
        if policy_id_string not in self.ai_policies:
            framebuffer = MaxAndSkipAndWarpAndScaleAndStackFrameBuffer(self.env.observation_space[agent_id])
            obs_space = framebuffer.get_observation_space()
            del framebuffer
            self.ai_policies[policy_id_string] = PretrainedRLLibPolicy(
                obs_space,
                self.env.action_space[agent_id],
                f"{Path(__file__).parent.parent}/backend/app/checkpoint/{checkpoint}",
                # os.path.dirname(os.path.realpath(__file__)) + "/../app/backend/checkpoint/" + checkpoint,
                checkpoint_agent_id=agent_id,
            )

        _, self._session = get_engine_and_session("crowdplay_atari-v0")
        e = EnvironmentModel(
            environment_id=instance_id,
            task_id=f"synthetic_{task_id}_{checkpoint}_v2",
        )
        self._session.merge(e)
        self._session.commit()

    def setup_sql(self):
        pass

    def step_to_clients(self, step_info):
        pass

    def episode_start_to_db(self, game_id):
        """Inserts episode start into database."""
        ep = EpisodeModel(episode_id=game_id, environment_id=self.instance_id)
        self._session.merge(ep)
        self._session.commit()

    def episode_end_to_db(self, game_id, episode_callables_state):
        pass

    def task_completion_to_db(self, completion_value, bonus_value, agent_id):
        pass

    def mark_envprocess_status_code(self, status_code):
        pass


def run_local_env_process(
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
    checkpoint,
    agent_id,
):
    env_process = LocalEnvProcess(
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
        checkpoint,
        agent_id,
    )
    env_process.run()
    pass


class AIOnlyEnvRunner:
    def __init__(self, instance_id, task_id, checkpoint, agent_id):
        # Basic info, won't change.
        self.instance_id = instance_id
        self.task_id = task_id

        # Observation and action spaces
        self.env = crowdplay_environments[task_id]["make_env"]()
        # TODO either make and delete env, or start background process and wait for env ready state?
        self.observation_space = self.env.observation_space
        self.action_space = self.env.action_space

        # Data structure that maps agent_id to connected human or AI player, or None if agent is available for new connection.
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
            target=local_step_enqueue_process_fn,
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
            target=run_local_env_process,
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
                6000,
                checkpoint,
                agent_id,
            ),
        )
        self.env_process.start()

        self._episode_is_running = False
        self._stop_runner = False

        # Connect AI agents.
        for agent, (checkpoint_file, checkpoint_agent_id) in crowdplay_environments[self.task_id][
            "ai_agent_map_always"
        ].items():
            self.assign_agent(agent, (2, f"{checkpoint_file}_{checkpoint_agent_id}"))

        self.fps = 6000

        self.start_time = datetime.now()

        self.assign_agent(agent_id, (2, f"{checkpoint}_{agent_id}"))

    def assign_agent(self, agent_id, assign_to):
        """Assigns an agent"""
        if agent_id in self.agents:
            self.agents[agent_id] = assign_to
            self.command_parent.send(("assign_agent", {"agent_id": agent_id, "assign_to": assign_to}))
        else:
            raise KeyError

    def run_episode(self):
        self.game_id = uuid4().hex
        self.command_parent.send(("start_episode", {"game_id": self.game_id}))
        while True:
            cmd, data = self.command_parent.recv()
            if cmd == "episode_end":
                break


def gen_episodes(task="space_invaders", checkpoint="si-comp.checkpoint", num_episodes=10):
    print(f"Process starting for task {task} and checkpoint {checkpoint}.")
    runner = AIOnlyEnvRunner(uuid4().hex, task, checkpoint, "game_0>player_0")
    for i in range(num_episodes):
        print(f"Running episode {i}/{num_episodes} for task {task} and checkpoint {checkpoint}.")
        runner.run_episode()
        print(f"Done running episode {i}/{num_episodes} for task {task} and checkpoint {checkpoint}.")
        time.sleep(2)


def gen_episodes_onearg(arg):
    gen_episodes(arg[1], arg[0], 100)


if __name__ == "__main__":
    ckp_tsk = [
        ("si_outsidein.checkpoint", "space_invaders_outsidein"),
        ("si_insideout.checkpoint", "space_invaders_insideout"),
        ("si_rowbyrow.checkpoint", "space_invaders_rowbyrow"),
        ("si_left_original.checkpoint", "space_invaders_left"),
        ("si_left_new1.checkpoint", "space_invaders_left"),
        ("si_left_new2.checkpoint", "space_invaders_left"),
        ("si_right_original.checkpoint", "space_invaders_right"),
        ("si_right_new1.checkpoint", "space_invaders_right"),
        ("si_right_new2.checkpoint", "space_invaders_right"),
    ]
    # pool = multiprocessing.Pool(12)
    # pool.map(gen_episodes_onearg, ckp_tsk)
    processes = []
    for i in range(len(ckp_tsk)):
        print(f"Starting process for task {ckp_tsk[i][1]} and checkpoint {ckp_tsk[i][0]}.")
        processes.append(multiprocessing.Process(target=gen_episodes, args=(ckp_tsk[i][1], ckp_tsk[i][0], 100)))
        processes[-1].start()

    for i in range(len(ckp_tsk)):
        processes[i].join()
        processes[i].close()
