import json
import pickle
from datetime import datetime, timedelta

from .db import db
from .utils import rgb_array_to_image_data, updatable_model


@updatable_model
class EnvModel(db.Model):
    __tablename__ = "envs"
    instance_id = db.Column(db.String(32), primary_key=True)
    env_id = db.Column(db.String(30), nullable=False)
    task_id = db.Column(db.String(255), nullable=False)
    hit_id = db.Column(db.String(255), nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    envprocess_status_code = db.Column(db.Integer, nullable=False, default=0)
    dbprocess_status_code = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            "instance_id": self.instance_id,
            "env_id": self.env_id,
            "task_id": self.task_id,
            "hit_id": self.hit_id,
            "created_on": self.created_on,
            "envprocess_status_code": self.envprocess_status_code,
            "dbprocess_status_code": self.dbprocess_status_code,
        }

    def __repr__(self):
        return f'<EnvModel id="{self.env_id}" created="{self.created_on}" />'


@updatable_model
class SessionModel(db.Model):
    __tablename__ = "sessions"
    visit_id = db.Column(db.String(255), nullable=False, primary_key=True)
    assignment_id = db.Column(db.String(255), nullable=False)
    worker_id = db.Column(db.String(255), nullable=False)
    hit_id = db.Column(db.String(255), nullable=False)
    task_id = db.Column(db.String(255), nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    token = db.Column(db.String(32), index=True, unique=True)
    env_instance_id = db.Column(db.String(32), db.ForeignKey("envs.instance_id"))
    agent_key = db.Column(db.String(255), nullable=False)
    completed = db.Column(db.Float, nullable=False, default=0)
    bonus = db.Column(db.Float, nullable=False, default=0)
    user_type = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            "visit_id": self.visit_id,
            "assignment_id": self.assignment_id,
            "worker_id": self.worker_id,
            "hit_id": self.hit_id,
            "task_id": self.task_id,
            "created_on": self.created_on,
            "token": self.token,
            "env_instance_id": self.env_instance_id,
            "agent_key": self.agent_key,
            "completed": self.completed,
            "bonus": self.bonus,
            "user_type": self.user_type,
        }

    def __repr__(self):
        return f"""<SessionModel
                        visit_id="{self.visit_id}"
                        assignment_id="{self.assignment_id}"
                        worker="{self.worker_id}"
                        hit="{self.hit_id}"
                        task="{self.task_id}"
                        env_instance_id="{self.env_instance_id}"
                        agent_key="{self.agent_key}"
                        completed="{self.completed}"
                        bonus="{self.bonus}"
                        user_type="{self.user_type}" />"""


@updatable_model
class UserDataModel(db.Model):
    __tablename__ = "user_data"
    info_id = db.Column(db.Integer, nullable=False, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey("sessions.visit_id"), nullable=False)
    key_string = db.Column(db.String(255), nullable=False)
    value_string = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            "info_id": self.info_id,
            "visit_id": self.visit_id,
            "key": self.key_string,
            "value": self.value_string,
        }

    def __repr__(self):
        return f"""<UserDataModel
                        info_id="{self.info_id}"
                        visit_id="{self.visit_id}"
                        key="{self.key_string}"
                        value="{self.value_string}" />"""


@updatable_model
class GameModel(db.Model):
    __tablename__ = "games"
    id = db.Column(db.String(32), primary_key=True)
    env_instance_id = db.Column(db.String(32), db.ForeignKey("envs.instance_id"))
    hit_id = db.Column(db.String(255), db.ForeignKey("sessions.hit_id"))
    started_on = db.Column(db.DateTime, default=datetime.utcnow)
    ended_on = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "env_instance_id": self.env_instance_id,
            "started_on": self.started_on,
            "ended_on": self.ended_on,
        }

    def __repr__(self):
        return f'<GameModel id="{self.id}" started="{self.started_on}" ended="{self.ended_on}" />'


@updatable_model
class TrajectoryModel(db.Model):
    __tablename__ = "episode_trajectories"
    episode_id = db.Column(db.String(32), primary_key=True)
    trajectory = db.Column(db.LargeBinary, nullable=False)

    def to_dict(self):
        return {"episode_id": self.id, "trajectory": self.trajectory}

    def __repr__(self):
        return f'<TrajectoryModel episode_id="{self.episode_id}" />'


@updatable_model
class StepModel(db.Model):
    __tablename__ = "steps"
    game_id = db.Column(db.String(32), db.ForeignKey("games.id"), primary_key=True)
    step_iter = db.Column(db.Integer, primary_key=True)
    agent_key = db.Column(db.String(32), primary_key=True)

    # stored as json
    prev_obs_extra = db.Column(db.Text, nullable=False)

    # stored as pickled np.array
    # MySQL => MEDIUMBLOB
    prev_obs_image = db.Column(db.LargeBinary(length=100960), nullable=False)

    # stored as json
    action = db.Column(db.String(255), nullable=False)  # '[999, 999]'

    action_timestep_index = db.Column(db.Integer)  # '[999, 999]'

    reward = db.Column(db.Float, nullable=False)
    done = db.Column(db.Boolean, nullable=False)

    # stored as json
    info = db.Column(db.Text)

    user_type = db.Column(db.Integer)

    def to_dict(self, with_image=True, image_to_base64=True):
        to_return = {
            "game_id": self.game_id,
            "step_iter": self.step_iter,
            "agent_key": self.agent_key,
            "prev_obs_extra": json.loads(self.prev_obs_extra),
            "action": json.loads(self.action),
            "action_timestep_index": self.action_timestep_index,
            "reward": self.reward,
            "done": self.done,
            "info": pickle.loads(self.info),
            "user_type": self.user_type,
        }

        if with_image:
            rgb_array = pickle.loads(self.prev_obs_image)  # to numpy array
            if image_to_base64:
                image_data = rgb_array_to_image_data(rgb_array)  # to base64
            else:
                image_data = rgb_array
            to_return["prev_obs_image"] = image_data

        return to_return

    def __repr__(self):
        return f"""<StepModel
                        game="{self.game_id}"
                        agent="{self.agent_key}"
                        action="{self.action}"
                        action_timestep_index="{self.action_timestep_index}"
                        reward="{self.reward}"
                        step="{self.step_iter}"
                        done="{self.done}"
                        info="{self.info}"
                        user_type="{self.user_type}" />"""


# Callables models


@updatable_model
class TaskCallableModel(db.Model):
    __tablename__ = "task_callable_per_env"
    env_instance_id = db.Column(db.String(32), primary_key=True)
    agent_key = db.Column(db.String(255), primary_key=True)
    callable_key = db.Column(db.String(255), primary_key=True)
    value_achieved = db.Column(db.String(255))
    value_required = db.Column(db.String(255))

    def to_dict(self):
        return {
            "env_instance_id": self.env_instance_id,
            "agent_key": self.agent_key,
            "callable_key": self.callable_key,
            "value_achieved": self.value_achieved,
            "value_required": self.value_required,
        }

    def __repr__(self):
        return f'<TaskCallableModel env_instance_id="{self.env_instance_id}" agent_key="{self.agent_key}" \
            callable_key="{self.callable_key}"  value_achieved="{self.value_achieved}"  \
            value_required="{self.value_required}" />'


@updatable_model
class EpisodeCallableModel(db.Model):
    __tablename__ = "episode_callable"
    env_instance_id = db.Column(db.String(32), primary_key=True)
    episode_id = db.Column(db.String(32), primary_key=True)
    agent_key = db.Column(db.String(255), primary_key=True)
    callable_key = db.Column(db.String(255), primary_key=True)
    value_achieved = db.Column(db.String(255))
    value_required = db.Column(db.String(255))

    def to_dict(self):
        return {
            "env_instance_id": self.env_instance_id,
            "episode_id": self.episode_id,
            "agent_key": self.agent_key,
            "callable_key": self.callable_key,
            "value_achieved": self.value_achieved,
            "value_required": self.value_required,
        }

    def __repr__(self):
        return f'<TaskCallableModel env_instance_id="{self.env_instance_id}" episode_id="{self.episode_id}" \
            agent_key="{self.agent_key}" callable_key="{self.callable_key}"  value_achieved="{self.value_achieved}" \
            value_required="{self.value_required}" />'


# Helpers functions to query those tables ###


def get_envs():
    envs = EnvModel.query.order_by(EnvModel.created_on.desc()).all()
    return list(map(lambda env: env.to_dict(), envs))


def get_envs_for_worker(worker_id):
    envs = (
        EnvModel.query.join(SessionModel)
        .filter(SessionModel.worker_id == worker_id)
        .order_by(EnvModel.created_on.desc())
        .all()
    )
    return list(map(lambda env: env.to_dict(), envs))


def get_hits():
    envs = SessionModel.query.order_by(SessionModel.hit_id).all()
    return list(map(lambda env: env.to_dict(), envs))


def get_env_by_game_id(game_id):
    env = EnvModel.query.join(GameModel).filter(GameModel.id == game_id).one()
    return env.to_dict()


def get_games_by_instance_id(instance_id, token=None):
    games = GameModel.query.filter(GameModel.env_instance_id == instance_id)

    if token is not None:
        games = games.filter(GameModel.hit_id == SessionModel.hit_id).filter(SessionModel.token == token)

    games = games.order_by(GameModel.started_on.desc()).all()

    return list(map(lambda game: game.to_dict(), games))


def get_games_by_assignment_id(assignment_id):
    games = (
        GameModel.query.filter(SessionModel.assignment_id == assignment_id)
        .filter(GameModel.hit_id == SessionModel.hit_id)
        .all()
    )
    return list(map(lambda game: game.to_dict(), games))


def get_steps_by_game_id(game_id, with_image=True, image_to_base64=True):
    steps = StepModel.query.filter(StepModel.game_id == game_id).order_by(StepModel.step_iter).all()
    return list(map(lambda step: step.to_dict(with_image, image_to_base64), steps))


def get_step_by_prim_keys(game_id, step_iter, agent_key, with_image=True):
    step = (
        StepModel.query.filter(StepModel.game_id == game_id)
        .filter(StepModel.step_iter == step_iter)
        .filter(StepModel.agent_key == agent_key)
        .one()
    )
    return step.to_dict(with_image)


def get_total_reward_by_assignment_id(assignment_id):
    """Returns the total reward across all games played by the given assignment_id."""
    total_reward = (
        db.session.query(db.func.sum(StepModel.reward))
        .filter(SessionModel.assignment_id == assignment_id)
        .filter(GameModel.env_instance_id == SessionModel.env_instance_id)
        .filter(StepModel.game_id == GameModel.id)
        .filter(StepModel.agent_key == SessionModel.agent_key)
        .scalar()
    )
    return total_reward or 0


def get_total_reward_by_visit_id(visit_id):
    """Returns the total reward across all games played by the given visit_id."""
    total_reward = (
        db.session.query(db.func.sum(StepModel.reward))
        .filter(SessionModel.visit_id == visit_id)
        .filter(GameModel.env_instance_id == SessionModel.env_instance_id)
        .filter(StepModel.game_id == GameModel.id)
        .filter(StepModel.agent_key == SessionModel.agent_key)
        .scalar()
    )
    return total_reward or 0


def value_to_appropriate_type(value):
    """Converts values stored in DB as strings back into appropriate types."""
    if value is None:
        return None
    if ":" in value:
        try:
            t = datetime.strptime(value, "%H:%M:%S")
            t = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
            # t = np.timedelta64(t)
            return t
        except Exception:
            return value
    elif "." in value:
        try:
            return float(value)
        except Exception:
            return value
    else:
        try:
            return int(value)
        except Exception:
            return value


def get_task_callable_by_visit_id(visit_id, callable):
    """Returns the total task callable across all games played by the given visit_id."""
    value_achieved = (
        db.session.query(TaskCallableModel.value_achieved)
        .filter(SessionModel.visit_id == visit_id)
        .filter(TaskCallableModel.env_instance_id == SessionModel.env_instance_id)
        .filter(TaskCallableModel.callable_key == callable)
        .filter(TaskCallableModel.agent_key == SessionModel.agent_key)
        .scalar()
    )
    value_achieved = value_to_appropriate_type(value_achieved)
    return value_achieved


def get_episode_callables_by_visit_id(visit_id, callable):
    """Returns the callables for each games played by the given visit_id."""
    values = (
        db.session.query(EpisodeCallableModel.value_achieved)
        .filter(SessionModel.visit_id == visit_id)
        .filter(EpisodeCallableModel.env_instance_id == SessionModel.env_instance_id)
        .filter(EpisodeCallableModel.callable_key == callable)
        .filter(EpisodeCallableModel.agent_key == SessionModel.agent_key)
        .all()
    )
    values = list(map(lambda t: value_to_appropriate_type(t[0]), values))
    return values or [
        0,
    ]


def get_episode_callables_by_task_id(task_id, callable):
    """Returns the callables for each games played by the given visit_id."""
    values = (
        db.session.query(EpisodeCallableModel.value_achieved)
        .filter(SessionModel.task_id == task_id)
        .filter(EpisodeCallableModel.env_instance_id == SessionModel.env_instance_id)
        .filter(EpisodeCallableModel.callable_key == callable)
        .filter(EpisodeCallableModel.agent_key == SessionModel.agent_key)
        .all()
    )
    values = list(map(lambda t: value_to_appropriate_type(t[0]), values))
    return values or [
        0,
    ]


def get_all_task_callable_by_task_id(task_id, callable):
    """Returns the total task callable across all games played by the given visit_id."""
    values_achieved = (
        db.session.query(TaskCallableModel.value_achieved)
        .filter(SessionModel.task_id == task_id)
        .filter(TaskCallableModel.env_instance_id == SessionModel.env_instance_id)
        .filter(TaskCallableModel.callable_key == callable)
        .filter(TaskCallableModel.agent_key == SessionModel.agent_key)
        .all()
    )
    raw_values = list(map(lambda value_achieved: value_achieved[0], values_achieved)) or [
        0,
    ]
    return list(map(value_to_appropriate_type, raw_values))


def get_total_rewards_by_task_id(task_id):
    """Returns the total reward across all games played by the given visit_id."""
    total_rewards = (
        db.session.query(db.func.sum(StepModel.reward))
        .filter(SessionModel.task_id == task_id)
        .filter(GameModel.env_instance_id == SessionModel.env_instance_id)
        .filter(StepModel.game_id == GameModel.id)
        .filter(StepModel.agent_key == SessionModel.agent_key)
        .group_by(SessionModel.visit_id)
        .all()
    )
    return list(map(lambda reward: reward[0], total_rewards)) or [
        0,
    ]


def get_total_steps_by_assignment_id(assignment_id):
    """Returns the total number of steps (i.e. playtime) across all games played by the given assignment_id."""
    total_steps = (
        db.session.query(db.func.count())
        .filter(SessionModel.assignment_id == assignment_id)
        .filter(GameModel.env_instance_id == SessionModel.env_instance_id)
        .filter(StepModel.game_id == GameModel.id)
        .filter(StepModel.agent_key == SessionModel.agent_key)
        .scalar()
    )
    return total_steps or 0


def get_completed_assignments_by_hit_id(hit_id, min_reward, min_steps):
    """Returns how many complete assignments we have for a given HIT."""
    # TODO make this one fancy SQL query?
    assignments = SessionModel.query.filter(SessionModel.hit_id == hit_id).all()
    completed_assignments = len(
        [
            assignment
            for assignment in assignments
            if (
                get_total_reward_by_assignment_id(assignment.assignment_id) >= min_reward
                and get_total_steps_by_assignment_id(assignment.assignment_id) >= min_steps
            )
        ]
    )
    return completed_assignments


def get_completed_assignments_by_task_id(task_id):
    """Returns how many complete assignments we have for a given task."""
    # TODO make this one fancy SQL query?
    assignments = SessionModel.query.filter(SessionModel.task_id == task_id).all()
    completed_assignments = sum(assignment.completed for assignment in assignments)
    return completed_assignments


def get_completed_assignments_by_task_id_and_worker_id(task_id, worker_id):
    """Returns how many complete assignments we have for a given task and worker."""
    # TODO make this one fancy SQL query?
    assignments = (
        SessionModel.query.filter(SessionModel.task_id == task_id).filter(SessionModel.worker_id == worker_id).all()
    )
    completed_assignments = sum(assignment.completed for assignment in assignments)
    return completed_assignments
