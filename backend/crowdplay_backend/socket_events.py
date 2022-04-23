from flask import jsonify, request
from flask_socketio import Namespace, join_room

from .config import Config
from .environments import crowdplay_environments
from .EnvsManager import EnvsManager
from .exceptions import InstanceNotFound, WrongAction
from .logger import getLogger
from .socketio import socketio

logger = getLogger("socket_events")


class EnvNamespace(Namespace):
    def on_connect(self):
        logger.info(f"Client with sid {request.sid} connected")

    def on_disconnect(self):
        logger.info(f"Client with sid {request.sid} disconnected")

        # The idea is to stop the running environment if
        # there are no more players in the game

        envs_manager = EnvsManager.getInstance()

        # Disconnect user from all instances they are connected to.
        # TODO can this ever be more than one instance?
        # All further logic now handled in EnvsManager.
        for instance_id in envs_manager.get_instance_ids_for_sid(request.sid):
            agent_key = envs_manager.get_agent_for_sid(instance_id, request.sid)
            envs_manager.disconnect_human_agent(agent_key, instance_id, request.sid)

            # # env = envs_manager.hits[hit_id][instance_id]

            # instance_room = f'{instance_id}'
            # # check if the user is the only non-AI (!) player left
            # if envs_manager.num_human_agents_in_instance(instance_id) <= 1:
            #     # if len(list(filter(lambda x: not x.startswith('ai_'), env['sid_in_game'].keys()))) == 1:
            #     # and if so, close the environment (will first stop it)
            #     envs_manager.close_env(instance_id)
            # else:
            #     # otherwise just remove it from the list...

            #     # store how many agents there are currently:
            #     num_agents_in_game_before = envs_manager.num_agents_in_instance(instance_id)

            #     # ... but first we need to return the `agent_key` used
            #     # back to the pool of agent keys that will be assigned to
            #     # new joiners
            #     agent_key = envs_manager.get_agent_for_sid(instance_id, request.sid)
            #     envs_manager.disconnect_human_agent(agent_key, instance_id, request.sid)
            #     # envs_manager.add_agent_key(agent_key, instance_id)

            #     # ... and finally remove this session id from the hit
            #     # del env['sid_in_game'][request.sid]

            #     num_agents_in_game = envs_manager.num_agents_in_instance(instance_id)
            #     is_ready = num_agents_in_game == len(envs_manager.get_runner(instance_id).agents)

            #     logger.info(f'Player left. Still in game: {num_agents_in_game}')

            #     # and notify all players if number of agents has changed
            #     if num_agents_in_game_before != num_agents_in_game:
            #         self.emit('change_agents', {
            #             'num_agents_in_game': num_agents_in_game,
            #             'is_ready': is_ready,
            #         }, room=instance_room)

    def on_error_handler(self, err):
        logger.error("Socket error:", err)

    def on_setup_user(self, instance_id, agent_key, assignment_id=None):
        # TODO move some/all of this to EnvsManager similar to user disconnect?
        # 1. This user will be assigned to this specific room
        player_room = f"{instance_id}_{agent_key}"
        join_room(room=player_room)
        instance_room = f"{instance_id}"
        join_room(room=instance_room)
        logger.info(f"Client with sid {request.sid} has joined room {player_room}")

        # 2. Register the player. Add it to `sid_in_game`
        envs_manager = EnvsManager.getInstance()

        # TODO As a workaround, for now we get the assignment_id from the env runner agent list.
        # Should we get it from the client instead?
        # TODO if not from the client, then remove it from the API endpoint.
        if assignment_id is None and len(envs_manager.env_runners[instance_id].agents[agent_key]) >= 3:
            assignment_id = envs_manager.env_runners[instance_id].agents[agent_key][2]
        envs_manager.assign_agent(instance_id, agent_key, (1, request.sid, assignment_id, "not_ready"))

    def on_action(self, instance_id, agent_key, step_iter, action):
        """Sends an action to the environment.
        parameters:
            - instance_id: the instance_id to send the action to.
            - agent_key: the agent_key the action belongs to.
            - step_iter: the step_iter the frontend was at when the action was sent.
            - action: the action to send, should already be in the format the env.step() expects."""
        envs_manager = EnvsManager.getInstance()
        player_room = f"{instance_id}_{agent_key}"

        try:
            env_runner = envs_manager.get_runner(instance_id)
            env_runner.set_action(agent_key, action, step_iter)
        except WrongAction:
            self.emit("error", jsonify(error="WrongAction", action=action), room=player_room)
        except InstanceNotFound:
            self.emit("error", jsonify(error="InstanceNotFound"), room=player_room)
        except Exception as error:
            logger.error("Error:", error)
            self.emit("error", jsonify(error=str(error)), room=player_room)

    def on_fps(self, instance_id, fps):
        envs_manager = EnvsManager.getInstance()
        instance_room = f"{instance_id}"

        try:
            env_runner = envs_manager.get_runner(instance_id)
            env_runner.set_fps(fps)
        except InstanceNotFound:
            self.emit("error", jsonify(error="InstanceNotFound"), room=instance_room)
        except Exception as error:
            logger.error("Error:", error)
            self.emit("error", jsonify(error=str(error)), room=instance_room)

    def on_start(self, instance_id):
        """Starts an episode, stepping in a loop.
        parameters:
            - instance_id: the instance_id to start.
        """
        envs_manager = EnvsManager.getInstance()

        try:
            env_runner = envs_manager.get_runner(instance_id)
            env_runner.start_episode()
        except Exception as error:
            logger.error("Error:", error)

    # TODO on_user_unready?
    def on_user_ready(self, instance_id, agent_key):
        """Marks a user as ready, and if all users are ready starts the countdown for the game."""
        envs_manager = EnvsManager.getInstance()
        try:
            env_runner = envs_manager.get_runner(instance_id)
            user_entry = env_runner.agents[agent_key]
            assert user_entry[0] == 1
            # Check if instance was ready before.
            instance_ready_before = True
            for agent in env_runner.agents:
                if not (
                    env_runner.agents[agent][0] == 2
                    or (
                        env_runner.agents[agent][0] == 1
                        and len(env_runner.agents[agent]) >= 4
                        and env_runner.agents[agent][3] == "ready"
                    )
                ):
                    instance_ready_before = False
            if instance_ready_before:
                logger.warn(f"User marked themselves as ready, but instance {instance_id} was already ready.")
            # Mark user as ready
            envs_manager.assign_agent(instance_id, agent_key, (user_entry[0], user_entry[1], user_entry[2], "ready"))
            # Check if instance is ready now
            instance_ready = True
            for agent in env_runner.agents:
                if not (
                    env_runner.agents[agent][0] == 2
                    or (
                        env_runner.agents[agent][0] == 1
                        and len(env_runner.agents[agent]) >= 4
                        and env_runner.agents[agent][3] == "ready"
                    )
                ):
                    instance_ready = False
            if instance_ready:
                # Notify users of ready.
                other_users = False
                for other_agent in envs_manager.get_runner(instance_id).agents:
                    if other_agent != agent_key and envs_manager.get_runner(instance_id).agents[other_agent][0] == 1:
                        other_users = True
                        self.emit(
                            "countdown_start",
                            {
                                "time": 5,
                                "play_sound": True,
                            },
                            room=f"{instance_id}_{other_agent}",
                        )
                countdown_time = 5 if other_users else 0
                self.emit(
                    "countdown_start",
                    {
                        "time": countdown_time,
                        "play_sound": False,
                    },
                    room=f"{instance_id}_{agent_key}",
                )

        except Exception as error:
            logger.error("Error:", error)
            self.emit("error", jsonify(error=str(error)), room=f"{instance_id}")
