import pickle
import random
from datetime import datetime, timedelta
from io import BytesIO
from urllib.parse import urlparse
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
from flask import Blueprint, current_app, jsonify, request, send_file

from .db import db
from .db_models import (
    SessionModel,
    UserDataModel,
    get_all_task_callable_by_task_id,
    get_completed_assignments_by_task_id,
    get_completed_assignments_by_task_id_and_worker_id,
    get_env_by_game_id,
    get_envs,
    get_envs_for_worker,
    get_episode_callables_by_task_id,
    get_episode_callables_by_visit_id,
    get_games_by_instance_id,
    get_hits,
    get_step_by_prim_keys,
    get_steps_by_game_id,
    get_task_callable_by_visit_id,
    get_total_reward_by_visit_id,
    get_total_rewards_by_task_id,
)
from .environments import crowdplay_environments
from .EnvsManager import EnvsManager
from .exceptions import (
    EnvironmentMalformed,
    EnvironmentNotFound,
    ErrorArguments,
    InstanceNotFound,
    NoMoreAgents,
    TokenForbidden,
)
from .logger import getLogger
from .session_setup import SessionSetup
from .socketio import socketio
from .utils import (
    consolidate_steps,
    make_or_get_env_to_dict,
    observation_to_serializable,
    space_to_dict,
)

logger = getLogger("api_routes")
api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")


# TODO is this not used anymore at all?
@api_v1.route("/make/<env_id>", methods=["POST"])
def make(env_id):
    """Instantiates an environment given its id.
    ---
    tags:
      - Gym API
    parameters:
      - name: env_id
        in: path
        type: string
        default: SpaceInvaders-v0
    definitions:
      Error:
        type: object
        properties:
          error:
            type: string
      Space:
        type: object
        properties:
          name:
            type: string
            enum: ['Discrete', 'Box', 'MultiBinary', 'MultiDiscrete', 'Dict']
          dtype:
            type: string
            enum: ['uint8', 'int32', 'float32', 'float64']
          shape:
            type: array
            items:
              type: number
      GymEnv:
        type: object
        properties:
          instance_id:
            type: string
          action_space:
            $ref: '#/definitions/Space'
          observation_space:
            $ref: '#/definitions/Space'

    responses:
      200:
        description: Environment successfully instantiated
        schema:
          $ref: '#/definitions/GymEnv'
      400:
        description: Wrong environment id
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Environment not found
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Unknown error
        schema:
          $ref: '#/definitions/Error'
    """
    envs_manager = EnvsManager.getInstance()

    try:
        env_dict = make_or_get_env_to_dict(envs_manager, env_id)

        return jsonify(env_dict)
    except EnvironmentMalformed:
        return jsonify(error="EnvironmentMalformed"), 400
    except EnvironmentNotFound:
        return jsonify(error="EnvironmentNotFound"), 404
    except Exception as error:
        logger.error("Error:", error)
        return jsonify(error=str(error)), 500


@api_v1.route("/close/<instance_id>", methods=["POST"])
def close(instance_id):
    """Closes an environment previously instantiated.
    ---
    tags:
      - Gym API
    parameters:
      - name: instance_id
        in: path
        type: string
    responses:
      200:
        description: Environment successfully closed
        schema:
          type: boolean
      404:
        description: Instance not found
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Unknown error
        schema:
          $ref: '#/definitions/Error'
    """
    envs_manager = EnvsManager.getInstance()

    try:
        is_closed = envs_manager.close_env(instance_id)
        return jsonify(ok=is_closed)
    except InstanceNotFound:
        return jsonify(error="InstanceNotFound"), 404
    except Exception as error:
        logger.error("Error:", error)
        return jsonify(error=str(error)), 500


@api_v1.route("/action-space/<instance_id>")
def action_space(instance_id):
    """Returns the action space of an environment previously instantiated.
    ---
    tags:
      - Gym API
    parameters:
      - name: instance_id
        in: path
        type: string
      - name: in_depth
        in: query
        type: string
        default: False
    responses:
      200:
        description: Action space
        schema:
          $ref: '#/definitions/Space'
      404:
        description: Instance not found
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Unknown error
        schema:
          $ref: '#/definitions/Error'
    """
    envs_manager = EnvsManager.getInstance()
    in_depth = request.args.get("in_depth", False)

    # TODO: multiagent? (agents keys)

    try:
        space = envs_manager.action_space_for(instance_id)
        space_dict = space_to_dict(space, in_depth)
        return jsonify(space_dict)
    except InstanceNotFound:
        return jsonify(error="InstanceNotFound"), 404
    except Exception as error:
        logger.error("Error:", error)
        return jsonify(error=str(error)), 500


@api_v1.route("/observation-space/<instance_id>")
def observation_space(instance_id):
    """Returns the observation space of an environment previously instantiated
    ---
    tags:
      - Gym API
    parameters:
      - name: instance_id
        in: path
        type: string
      - name: in_depth
        in: query
        type: string
        default: False
    responses:
      200:
        description: Observation space
        schema:
          $ref: '#/definitions/Space'
      404:
        description: Instance not found
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Unknown error
        schema:
          $ref: '#/definitions/Error'
    """
    envs_manager = EnvsManager.getInstance()
    in_depth = request.args.get("in_depth", False)

    # TODO: multiagent? (agents keys)

    try:
        space = envs_manager.observation_space_for(instance_id)
        space_dict = space_to_dict(space, in_depth)
        return jsonify(space_dict)
    except InstanceNotFound:
        return jsonify(error="InstanceNotFound"), 404
    except Exception as error:
        logger.error("Error:", error)
        return jsonify(error=str(error)), 500


# TODO I think this is never called? Remove?
@api_v1.route("/stop/<instance_id>", methods=["POST"])
def stop(instance_id):
    """Stops a running environment.
    ---
    tags:
      - App API
    parameters:
      - name: instance_id
        in: path
        type: string
    responses:
      200:
        description: Environment successfully stopped
        schema:
          $ref: '#/definitions/Ok'
      404:
        description: Instance not found
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Unknown error
        schema:
          $ref: '#/definitions/Error'
    """
    envs_manager = EnvsManager.getInstance()

    try:
        env_runner = envs_manager.get_runner(instance_id)
        game_id = env_runner.stop_episode()

        return jsonify(ok=True, game_id=game_id)
    except InstanceNotFound:
        return jsonify(error="InstanceNotFound"), 404
    except Exception as error:
        logger.error("Error:", error)
        return jsonify(error=str(error)), 500


# @api_v1.route("/list-envs")
def list_envs():
    """Lists instantiated envs.
    ---
    tags:
      - App API
    parameters:
      - name: with_games
        in: query
        description: Whether or not to include the list of games for each instance
    definitions:
      Game:
        type: object
        properties:
          id:
            type: string
          started_on:
            type: string
          ended_on:
            type: string
      Env:
        type: object
        properties:
          instance_id:
            type: string
          env_id:
            type: string
          created_on:
            type: string
          games:
            type: array
            default: []
            items:
              $ref: '#/definitions/Game'
    responses:
      200:
        description: List of instantiated environments
        schema:
          type: array
          items:
            $ref: '#/definitions/Env'
      500:
        description: Unknown error
        schema:
          $ref: '#/definitions/Error'

    """
    with_games = request.args.get("with_games")

    try:
        serializable_envs = get_envs()

        if with_games:
            # TODO: better way to do this?
            for env in serializable_envs:
                env["games"] = get_games_by_instance_id(env["instance_id"])

        return jsonify(serializable_envs)
    except Exception as error:
        logger.error("Error:", error)
        return jsonify(error=str(error)), 500


def only_with_games_filter(env, token=None):
    games = get_games_by_instance_id(env["instance_id"], token=token)

    if len(games) > 0:
        env["games"] = games
        return True

    return False


def get_task_id_from_auto(auto_task_id, session_input):
    envs_manager = EnvsManager.getInstance()
    task_list = crowdplay_environments[auto_task_id]["auto"]
    # Check if there is an existing env with open player slots available for any of the tasks.
    for task in task_list:
        for instance_id in (
            instance_id
            for instance_id in envs_manager.env_runners
            if envs_manager.env_runners[instance_id].task_id == task
        ):
            if len(envs_manager._agents_to_assign(instance_id)) > 0:
                return task

    # If the taskId is set to Auto, we assign the first task that doesn't have enough complete assignments yet,
    # and that the user hasn't done before.
    for task in task_list:
        if get_completed_assignments_by_task_id(task) < crowdplay_environments[task]["target_complete_assignments"]:
            if get_completed_assignments_by_task_id_and_worker_id(task, session_input["workerId"]) < 1:
                return task

    # Otherwise assign task with fewest completed tasks so far, tiebreaking randomly.
    completed_so_far = {}
    for task in task_list:
        completed_so_far[task] = int(get_completed_assignments_by_task_id(task))
    m = min(completed_so_far, key=completed_so_far.get)
    min_tasks = [task for task in completed_so_far if completed_so_far[task] == completed_so_far[m]]
    return random.choice(min_tasks)


# TODO: Rename / remake this something like user_connect?
# TODO this can now *only* be used to create a new entry, not to query details of an existing entry.
@api_v1.route("/hello", methods=["POST"])
def session_setup():
    """Stores session info and creates or assigns environment.
    ---
    tags:
      - App API
    definitions:
      SessionInput:
        type: object
        properties:
          assignmentId:
            type: string
            required: true
          environmentId:
            type: string
          workerId:
            type: string
          hitId:
            type: string
          taskId:
            type: string
      SessionDetails:
        type: object
        properties:
          assignment_id:
            type: string
          worker_id:
            type: string
          hit_id:
            type: string
          created_on:
            type: string
          time_since:
            type: number
          time_min:
            type: number
    parameters:
      - name: session_input
        in: body
        schema:
          $ref: '#/definitions/SessionInput'
    responses:
      200:
        description: Session details
        schema:
          $ref: '#/definitions/SessionDetails'
      400:
        description: Wrong arguments
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Instance not found
        schema:
          $ref: '#/definitions/Error'
      409:
        description: Conflict with the current state. No more agents.
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Unknown error
        schema:
          $ref: '#/definitions/Error'
    """
    logger.info("Starting SessionSetup endpoint.")
    session_input = request.get_json()

    try:
        # Set taskId to default if not set or not set properly
        if (
            "taskId" not in session_input
            or session_input["taskId"] is None
            or session_input["taskId"] not in crowdplay_environments
        ):
            session_input["taskId"] = "default"

        if (
            "starttime" in crowdplay_environments[session_input["taskId"]]
            and datetime.now() < crowdplay_environments[session_input["taskId"]]["starttime"]
        ):
            print("Task not available yet.")
            return jsonify(
                {"initial_message": "This task is not available yet. Please come back at the time specified."}
            )

        if (
            "endtime" in crowdplay_environments[session_input["taskId"]]
            and datetime.now() > crowdplay_environments[session_input["taskId"]]["endtime"]
        ):
            print("Task not available anymore.")
            return jsonify({"initial_message": "This task is not available anymore."})

        envs_manager = EnvsManager.getInstance()

        if (
            "taskId" in session_input
            and session_input["taskId"] in crowdplay_environments
            and "auto" in crowdplay_environments[session_input["taskId"]]
        ):
            session_input["taskId"] = get_task_id_from_auto(session_input["taskId"], session_input)

        # Redirect to a given URL instead of starting an env here.
        # Currently only used to redirect to multiplayer instance.
        if "redirect" in crowdplay_environments[session_input["taskId"]]:
            return {"redirect": crowdplay_environments[session_input["taskId"]]["redirect"](session_input)}

        # Creat or assign an environment
        # if session_input["environmentId"] is not None:

        # TODO Don't let same worker connect to both players in same game!
        env_dict = make_or_get_env_to_dict(
            envs_manager,
            session_input["environmentId"],
            session_input["hitId"],
            session_input["taskId"],
            session_input["workerId"],
            session_input["assignmentId"],
        )

        session_input["env_instance_id"] = env_dict["instance_id"]
        session_input["agent_key"] = env_dict["agent_key"]
        # TODO clean this up. We now always create a new session row. Do we still need to fetch details via SesionSetup class?
        # Do we need SessionSetup class at all?
        session_setup = SessionSetup(session_input)
        details = session_setup.get_details()

        # Let's add the environment to the details
        details["env"] = env_dict
        if "initial_message" in crowdplay_environments[details["task_id"]]:
            details["initial_message"] = crowdplay_environments[details["task_id"]]["initial_message"][
                session_input["agent_key"]
            ]
        else:
            details["initial_message"] = None

        if "ui_layout" in crowdplay_environments[details["task_id"]]:
            details["ui_layout"] = crowdplay_environments[details["task_id"]]["ui_layout"]
        else:
            details["ui_layout"] = "default"
        if "ui_layout_options" in crowdplay_environments[details["task_id"]]:
            details["ui_layout_options"] = crowdplay_environments[details["task_id"]]["ui_layout_options"]
        else:
            details["ui_layout_options"] = {}

        # Keep a record of the user agent.
        user_agent = request.headers.get("User-Agent")
        user_data_model = UserDataModel(visit_id=details["visit_id"], key_string="User-Agent", value_string=user_agent)
        db.session.add(user_data_model)
        db.session.commit()

        # Keep record of user URL and referrer
        if "original_url" in session_input:
            user_data_model = UserDataModel(
                visit_id=details["visit_id"], key_string="url", value_string=session_input["original_url"]
            )
            db.session.add(user_data_model)
            db.session.commit()

        if "referrer" in session_input:
            user_data_model = UserDataModel(
                visit_id=details["visit_id"], key_string="referrer", value_string=session_input["referrer"]
            )
            db.session.add(user_data_model)
            db.session.commit()

        logger.info("Returning from SessionSetup endpoint.")
        return jsonify(details)
    except ErrorArguments as error:
        logger.info("Returning from SessionSetup endpoint with error.")
        return jsonify(error=str(error)), 400
    except InstanceNotFound:
        logger.info("Returning from SessionSetup endpoint with error.")
        return jsonify(error="InstanceNotFound"), 404
    except NoMoreAgents:
        logger.info("Returning from SessionSetup endpoint with error.")
        return jsonify(error="NoMoreAgents"), 409
    except Exception as error:
        logger.info("Returning from SessionSetup endpoint with error.")
        logger.error("Error:", error)
        return jsonify(error=str(error)), 500


@api_v1.route("/session/<visit_id>/token")
def session_token(visit_id):
    """Gets back the token assigned to the given assignment.
    ---
    tags:
      - App API
    parameters:
      - name: visit_id
        in: path
        type: string
    responses:
      200:
        description: Sesion token
        type: string
      403:
        description: Server refuses to give away the token
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Session entry not found
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Unknown error
        schema:
          $ref: '#/definitions/Error'
    """
    session_details = SessionSetup({"visit_id": visit_id}, create=False)

    try:
        details = session_details.get_details(with_token=True)
        return jsonify(token=details["token"])
    except TokenForbidden as error:
        return jsonify(error=str(error)), 403
    except InstanceNotFound:
        return jsonify(error="SessionNotFound"), 404
    except Exception as error:
        logger.error("Error:", error)
        return jsonify(error=str(error)), 500


# TODO make this more generic?
# TODO errors?
@api_v1.route("/collect-user-data", methods=["POST"])
def collect_user_data():
    """Collects user data, e.g. email address. For now only specifically email address.
    ---
    tags:
      - App API
    definitions:
      Input:
        type: object
        properties:
          visitId:
            type: string
            required: true
          key:
            type: string
            required: true
          value:
            type: string
            required: true
    parameters:
      - name: input
        in: body
        schema:
          $ref: '#/definitions/Input'
    responses:
      200:
        description: OK
        type: string
      500:
        description: Unknown error
        schema:
          $ref: '#/definitions/Error'
    """
    input = request.get_json()

    try:
        if "visit_id" in input:
            visit_id = input["visit_id"]
        else:
            visit_id = 0
        key = input["key"]
        value = input["value"]
        logger.info(f"logging key {key} value {value}")

        user_data_model = UserDataModel(visit_id=visit_id, key_string=key, value_string=value)

        db.session.add(user_data_model)
        db.session.commit()
        # TODO what to return?
        return jsonify(ok=True)
    except Exception as error:
        logger.error("Error:", error)
        return jsonify(error=str(error)), 500


@api_v1.route("/get_scores/<visit_id>")
def get_scores(visit_id):
    # Sleep for a moment to allow scores to make it to the DB after game end.
    socketio.sleep(0.5)
    user_details = SessionModel.query.get(visit_id)
    task_id = user_details.task_id

    if "task_callables" not in crowdplay_environments[task_id]:
        rewards_this_task = get_total_rewards_by_task_id(task_id)
        reward_this_visit = get_total_reward_by_visit_id(visit_id)
        return jsonify(
            [
                get_stats_from_raw_data("Total Score", reward_this_visit, rewards_this_task),
            ]
        )

    results = []
    callables = crowdplay_environments[task_id]["task_callables"]
    for callable in callables:
        total_performance_this_visit = get_task_callable_by_visit_id(visit_id, callable)
        if total_performance_this_visit is None:
            return (
                jsonify(
                    error="No scores found for this ID. Did you forget to start the game? \
                      If you just finished the game, please check back in a moment."
                ),
                404,
            )
        total_performance_this_task = get_all_task_callable_by_task_id(task_id, callable)
        episodes_this_visit = get_episode_callables_by_visit_id(visit_id, callable)
        highest_episode = max(episodes_this_visit)
        episodes_this_task = get_episode_callables_by_task_id(task_id, callable)
        results.append(
            get_stats_from_raw_data(f"{callable} (total)", total_performance_this_visit, total_performance_this_task)
        )
        results.append(get_stats_from_raw_data(f"{callable} (best single game)", highest_episode, episodes_this_task))

    return jsonify(results)


def get_stats_from_raw_data(metric, this_score, all_scores):
    if isinstance(this_score, float):
        this_score_string = f"{this_score:.2f}"
    else:
        this_score_string = str(this_score)
    # Seems to be necessary in case current score hasn't made it into the DB yet.
    # TODO check if this is really the right thing to do.
    # Not a huge problem if not though.
    if this_score not in all_scores:
        all_scores.append(this_score)
    if isinstance(this_score, timedelta):
        this_score = this_score / timedelta(minutes=1)
        all_scores = list(
            map(lambda s: s / timedelta(minutes=1), [score for score in all_scores if isinstance(score, timedelta)])
        )
    all_scores.sort()
    low = all_scores[0]
    high = all_scores[-1]
    n_bins = 10
    # We do one more bin that specified, because we do a half-sized bin on each end
    bin_size = (high - low) / (n_bins)
    if bin_size == 0:
        bin_size = 1
    binned_data = np.histogram(all_scores, bins=n_bins + 1, range=(low - (bin_size / 2), high + (bin_size / 2)))
    # We put the data into an x-y list, and also add a few additional data points
    # below and above the actual data for nicer rendering.
    additional_data_points = n_bins // 5
    binned_data_processed = (
        [{"x": float(low + i * bin_size), "y": 0.0} for i in range(-additional_data_points, 0)]
        + [{"x": float(low + i * bin_size), "y": float(binned_data[0][i])} for i in range(len(binned_data[0]))]
        + [{"x": float(high + i * bin_size), "y": 0.0} for i in range(1, additional_data_points + 1)]
    )
    rank_lower = len(all_scores) - all_scores.index(this_score)
    all_scores.reverse()
    rank = all_scores.index(this_score) + 1

    total_scores = len(all_scores)
    percentile = 100 if total_scores == 1 else int(100 * (1 - rank_lower / total_scores))
    return {
        "metric": metric,
        "your_score": this_score_string,
        "your_score_raw": this_score,
        "your_rank": rank,
        "out_of": total_scores,
        "percentile": percentile,
        "histogram": binned_data_processed,
    }


@api_v1.route("/get_task_choices", methods=["POST"])
def get_task_choices():
    logger.info("Starting task choice endpoint.")
    session_input = request.get_json()
    if (
        "taskId" not in session_input
        or session_input["taskId"] is None
        or session_input["taskId"] not in crowdplay_environments
    ):
        session_input["taskId"] = "default"
    task_id = session_input["taskId"]
    if "choose" in crowdplay_environments[task_id]:
        logger.info("Returning from task choice endpoint with True.")
        return jsonify({"user_choice_available": True, "choices": crowdplay_environments[task_id]["choose"]})
    else:
        logger.info("Returning from task choice endpoint with False.")
        return jsonify({"user_choice_available": False, "choice": task_id})
