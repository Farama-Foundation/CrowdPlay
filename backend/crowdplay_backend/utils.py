import pickle
from base64 import b64encode

import cv2
from numpy import ndarray

from .config import Config


def noop(*args, **kwargs):
    pass


class SpaceType:
    DISCRETE = "Discrete"
    BOX = "Box"
    MULTI_BINARY = "MultiBinary"
    MULTI_DISCRETE = "MultiDiscrete"
    DICT = "Dict"
    ORDERED_DICT = "OrderedDict"


def space_to_dict(space, in_depth=False):

    if type(space) == dict:
        # We might have a dictionary with the following shape: { 'agent_x': Space },
        # in that case we turn it into a serializable dictionary:
        return {agent_n: space_to_dict(agent_space, in_depth) for agent_n, agent_space in space.items()}

    name = space.__class__.__name__
    space_dict = {"name": name}
    space_dict["dtype"] = str(space.dtype) if space.dtype is not None else None

    if name in SpaceType.DISCRETE:
        space_dict["n"] = space.n

    elif name == SpaceType.BOX:
        space_dict["shape"] = space.shape

        if in_depth:
            # I noticed that numpy.float32 isn't JSON serializable but numpy.float64 is.
            space_dict["low"] = space.low.astype("float64").tolist()
            space_dict["high"] = space.high.astype("float64").tolist()

    elif name == SpaceType.MULTI_BINARY:
        space_dict["n"] = space.n
        # TODO: does it make sense to return this?
        space_dict["shape"] = space.shape

    elif name == SpaceType.MULTI_DISCRETE:
        space_dict["nvec"] = space.nvec.tolist()
        space_dict["shape"] = space.nvec.shape

    elif name == SpaceType.DICT:
        space_dict["space"] = {key: space_to_dict(sub_space) for key, sub_space in space.spaces.items()}

    return space_dict


def rgb_array_to_bytes(rgb_array, ext=".jpg"):
    _, buffer = cv2.imencode(ext, rgb_array[:, :, [2, 1, 0]])
    return buffer.tobytes()


def rgb_array_to_image_data(rgb_array, encoding="utf-8"):
    b_frame = rgb_array_to_bytes(rgb_array)
    b64_frame = b64encode(b_frame).decode(encoding)
    return "data:image/jpeg;base64," + b64_frame


def updatable_model(ClassModel):
    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    setattr(ClassModel, "update", update)
    return ClassModel


def observation_to_serializable(obs, image_to="base64"):

    # TODO: might not be the best way to check this
    if type(obs) == dict:
        # Multiagent dictionary: { agent_key: Space },
        # in that case we turn it into a serializable dictionary:
        return {agent_key: observation_to_serializable(agent_obs, image_to) for agent_key, agent_obs in obs.items()}

    space_type = obs.__class__.__name__

    if space_type == SpaceType.BOX:
        return obs.tolist()

    # Convert image data to base64 jpg
    # TODO
    if isinstance(obs, ndarray) and len(obs.shape) == 3 and obs.shape[-1] == 3:
        if image_to == "base64":
            return rgb_array_to_image_data(obs)
        elif image_to == "pickle":
            return pickle.dumps(obs)
        else:
            return obs.tolist()

    elif space_type in [SpaceType.DICT, SpaceType.ORDERED_DICT]:
        serializable_obs = {}

        for key, value in obs.items():

            # TODO: this possibly depends on the game, Space Invaders?
            if isinstance(key, str) and key.startswith("image"):
                if image_to == "base64":
                    serializable_obs["image"] = rgb_array_to_image_data(value)
                elif image_to == "pickle":
                    serializable_obs["image"] = pickle.dumps(value)
                else:
                    serializable_obs["image"] = value.tolist()
            else:
                serializable_obs[key] = value

        return serializable_obs

    # Fallback: just return the plain observation
    return obs


# This logic will be used more than once, hence the extraction
# TODO this is used to set up a new player, essentially?
def make_or_get_env_to_dict(envs_manager, env_id, hit_id=None, task_id="default", worker_id=None, assignment_id=None):
    instance_id, agent_key = envs_manager.make_or_get_env(
        env_id, task_id=task_id, hit_id=hit_id, worker_id=worker_id, assignment_id=assignment_id
    )
    # agent_key = envs_manager.get_next_agent_key(instance_id)

    action_space = envs_manager.action_space_for(instance_id)
    observation_space = envs_manager.observation_space_for(instance_id)

    return {
        "id": env_id,
        "instance_id": instance_id,
        "action_space": space_to_dict(action_space[agent_key], in_depth=False),
        "observation_space": space_to_dict(observation_space[agent_key], in_depth=False),
        "agent_key": agent_key,
    }


def consolidate_steps(steps, skip_from_step=["game_id", "step_iter", "agent_key"]):
    """
    This function will help us to transform the list of steps,
    where we have multiple entries for the same step, one per agent,
    into a consolidated entry
    """
    consolidated_steps = []
    for step in steps:
        step_iter = step["step_iter"]
        agent_key = step["agent_key"]
        step_idx = step_iter - 1

        # Skipping unnecessary information in the step
        for to_skip in skip_from_step:
            del step[to_skip]

        if 0 <= step_idx < len(consolidated_steps):  # is it a valid index?
            consolidated_steps[step_idx]["agents"][agent_key] = step
        else:
            consolidated_steps.append(
                {
                    "step_iter": step_iter,
                    "agents": {agent_key: step},
                }
            )

    return consolidated_steps
