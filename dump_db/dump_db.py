"""This dumps all the instances in the DB to zipfiles. Use with caution."""

import bz2
import hashlib
import os
import pickle
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from crowdplay_datasets.dataset import (
    Base,
    EnvironmentKeywordDataModel,
    EnvironmentModel,
    EpisodeKeywordDataModel,
    EpisodeModel,
    UserModel,
    get_engine_and_session,
)
from crowdplay_backend import db_models
from crowdplay_backend.api_routes import api_v1
from crowdplay_backend.config import Config
from crowdplay_backend.db import db
from crowdplay_backend.db_models import value_to_appropriate_type
from crowdplay_backend.logger import setLoggerConfig
from crowdplay_backend.socket_events import EnvNamespace
from crowdplay_backend.socketio import socketio
from crowdplay_backend.static_routes import register as static_routes
from crowdplay_backend.utils import (
    consolidate_steps,
    make_or_get_env_to_dict,
    observation_to_serializable,
    space_to_dict,
)
from flasgger import Swagger
from flask import Flask
from sqlalchemy import Column, ForeignKey, Integer, String, Table, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship, sessionmaker

# CHANGEME
SECRET_HASH_KEY = b"shfiwuyrow8ryhwk3ryihfsneukyewiufhkjf"


task_definitions = {
    "beam_rider_mturk": {"game": "beam_rider", "task": "plain", "source": "mturk"},
    "breakout_mturk": {"game": "breakout", "task": "plain", "source": "mturk"},
    "montezuma_revenge_email": {"game": "montezuma_revenge", "task": "plain", "source": "email"},
    "montezuma_revenge_mturk": {"game": "montezuma_revenge", "task": "plain", "source": "mturk"},
    "montezuma_revenge_socialmedia": {"game": "montezuma_revenge", "task": "plain", "source": "socialmedia"},
    "qbert_mturk": {"game": "qbert", "task": "plain", "source": "mturk"},
    "qbert_socialmedia": {"game": "qbert", "task": "plain", "source": "socialmedia"},
    "riverraid_email": {"game": "riverraid", "task": "plain", "source": "email"},
    "riverraid_left": {"game": "riverraid", "task": "left", "source": "mturk"},
    "riverraid_left_email": {"game": "riverraid", "task": "left", "source": "email"},
    "riverraid_left_socialmedia": {"game": "riverraid", "task": "left", "source": "socialmedia"},
    "riverraid_mturk": {"game": "riverraid", "task": "plain", "source": "mturk"},
    "riverraid_right": {"game": "riverraid", "task": "right", "source": "mturk"},
    "riverraid_right_email": {"game": "riverraid", "task": "right", "source": "email"},
    "riverraid_right_socialmedia": {"game": "riverraid", "task": "right", "source": "socialmedia"},
    "riverraid_socialmedia": {"game": "riverraid", "task": "plain", "source": "socialmedia"},
    "space_invaders_2p_competitive_email": {"game": "space_invaders_2p", "task": "competitive", "source": "email"},
    "space_invaders_2p_competitive_mturk": {"game": "space_invaders_2p", "task": "competitive", "source": "mturk"},
    "space_invaders_2p_cooperative_email": {"game": "space_invaders_2p", "task": "cooperative", "source": "email"},
    "space_invaders_2p_cooperative_mturk": {"game": "space_invaders_2p", "task": "cooperative", "source": "mturk"},
    "space_invaders_ai_competitive_email": {"game": "space_invaders_ai", "task": "competitive", "source": "email"},
    "space_invaders_ai_competitive_mturk": {"game": "space_invaders_ai", "task": "competitive", "source": "mturk"},
    "space_invaders_ai_competitive_socialmedia": {
        "game": "space_invaders_ai",
        "task": "competitive",
        "source": "socialmedia",
    },
    "space_invaders_ai_cooperative_email": {"game": "space_invaders_ai", "task": "cooperative", "source": "email"},
    "space_invaders_ai_cooperative_mturk": {"game": "space_invaders_ai", "task": "cooperative", "source": "mturk"},
    "space_invaders_ai_cooperative_socialmedia": {
        "game": "space_invaders_ai",
        "task": "cooperative",
        "source": "socialmedia",
    },
    "space_invaders_email": {"game": "space_invaders", "task": "plain", "source": "email"},
    "space_invaders_insideout": {"game": "space_invaders", "task": "insideout", "source": "mturk"},
    "space_invaders_insideout_activetime": {
        "game": "space_invaders",
        "task": "insideout_incentives",
        "source": "mturk",
    },
    "space_invaders_insideout_allincentives": {
        "game": "space_invaders",
        "task": "insideout_incentives",
        "source": "mturk",
    },
    "space_invaders_insideout_bonusonly": {"game": "space_invaders", "task": "insideout_incentives", "source": "mturk"},
    "space_invaders_insideout_email": {"game": "space_invaders", "task": "insideout", "source": "email"},
    "space_invaders_insideout_socialmedia": {"game": "space_invaders", "task": "insideout", "source": "socialmedia"},
    "space_invaders_insideout_stricter": {"game": "space_invaders", "task": "insideout", "source": "mturk"},
    "space_invaders_insideout_taskrequirement": {
        "game": "space_invaders",
        "task": "insideout_incentives",
        "source": "mturk",
    },
    "space_invaders_insideout_timeonly": {"game": "space_invaders", "task": "insideout_incentives", "source": "mturk"},
    "space_invaders_left": {"game": "space_invaders", "task": "left", "source": "mturk"},
    "space_invaders_left_stricter": {"game": "space_invaders", "task": "left", "source": "mturk"},
    "space_invaders_mturk": {"game": "space_invaders", "task": "plain", "source": "mturk"},
    "space_invaders_outsidein": {"game": "space_invaders", "task": "outsidein", "source": "mturk"},
    "space_invaders_outsidein_stricter": {"game": "space_invaders", "task": "outsidein", "source": "mturk"},
    "space_invaders_right": {"game": "space_invaders", "task": "right", "source": "mturk"},
    "space_invaders_right_stricter": {"game": "space_invaders", "task": "right", "source": "mturk"},
    "space_invaders_rowbyrow": {"game": "space_invaders", "task": "rowbyrow", "source": "mturk"},
    "space_invaders_rowbyrow_socialmedia": {"game": "space_invaders", "task": "rowbyrow", "source": "socialmedia"},
    "space_invaders_rowbyrow_stricter": {"game": "space_invaders", "task": "rowbyrow", "source": "mturk"},
    "space_invaders_socialmedia": {"game": "space_invaders", "task": "plain", "source": "socialmedia"},
    "spaceinvaders_cooperative_socialmedia": {
        "game": "space_invaders_2p",
        "task": "cooperative",
        "source": "socialmedia",
    },
}


if __name__ == "__main__":

    app = Flask(__name__, template_folder="web", static_folder="web", static_url_path="")

    # App configuration
    config_class = os.environ.get("APP_SETTINGS") or "crowdplay_backend.config.Config"
    app.config.from_object(config_class)

    # Database
    db.init_app(app)

    # Create local directory if not existing.
    if not os.path.isdir(f"{Path(__file__).resolve().parent.parent}/dataset/data/"):
        os.makedirs(f"{Path(__file__).resolve().parent.parent}/dataset/data/")

    # local SQLite
    local_engine, local_session = get_engine_and_session("crowdplay_atari-v0", create=True)
    # Base.metadata.create_all(local_engine)

    with app.app_context():
        print("start")
        # Get all the environments
        environment_instances = db_models.EnvModel.query.all()
        for env_instance in environment_instances:
            print(f"Processing env instance: {env_instance.instance_id}")
            users = db_models.SessionModel.query.filter(
                db_models.SessionModel.env_instance_id == env_instance.instance_id
            ).all()
            users_are_test = False
            for user in users:
                if user.user_type == "test":
                    users_are_test = True
            if env_instance.task_id in task_definitions.keys() and not users_are_test:
                # Get all the episodes in each environment.
                # If at least one episode has a trajectory saved in the DB, the env is relevant.
                episodes = db_models.GameModel.query.filter(
                    db_models.GameModel.env_instance_id == env_instance.instance_id
                ).all()
                has_trajectories = False
                for episode in episodes:
                    # Check if episode has a trajectory saved. If yes, save it locally, if it's not here yet.
                    if (
                        db.session.query(db_models.TrajectoryModel.episode_id).filter_by(episode_id=episode.id).first()
                        is not None
                    ):
                        has_trajectories = True
                        if not os.path.isfile(
                            f"{Path(__file__).resolve().parent.parent}/dataset/data/{episode.id}.pickle.bz2"
                        ):
                            print(f"Downloading episode {episode.id}")
                            trajectory = db_models.TrajectoryModel.query.get(episode.id)
                            with open(
                                f"{Path(__file__).resolve().parent.parent}/dataset/data/{episode.id}.pickle.bz2", "wb"
                            ) as f:
                                f.write(trajectory.trajectory)
                                f.close()
                        else:
                            print(f"Already downloaded episode {episode.id}")
                        local_episode = EpisodeModel(episode_id=episode.id, environment_id=env_instance.instance_id)
                        local_session.merge(local_episode)
                        # local_session.commit()

                        # Save all episode callables
                        keyword_datas = db_models.EpisodeCallableModel.query.filter(
                            db_models.EpisodeCallableModel.episode_id == episode.id
                        ).all()
                        for keyword_data in keyword_datas:
                            kw_model = EpisodeKeywordDataModel(
                                episode_id=episode.id,
                                agent_id=keyword_data.agent_key,
                                key=keyword_data.callable_key,
                                value=value_to_appropriate_type(keyword_data.value_achieved),
                                # value_required=value_to_appropriate_type(
                                #     keyword_data.value_required)
                            )
                            local_session.merge(kw_model)
                            # local_session.commit()
                        # Save created on kwdata.
                        kw_model = EpisodeKeywordDataModel(
                            episode_id=episode.id,
                            agent_id="all",
                            key="created_on",
                            value=episode.started_on,
                            # value_required=''
                        )
                        local_session.merge(kw_model)
                        # local_session.commit()

                    else:
                        print(f"Episode {episode.id} has no trajectory data.")
                if has_trajectories:
                    # Save environment info
                    environment_db = EnvironmentModel(
                        environment_id=env_instance.instance_id, task_id=env_instance.task_id
                    )
                    local_session.merge(environment_db)
                    # local_session.commit()
                    users = db_models.SessionModel.query.filter(
                        db_models.SessionModel.env_instance_id == env_instance.instance_id
                    ).all()

                    # Save users
                    for user in users:
                        user_id = hashlib.blake2b(
                            user.worker_id.encode(), key=SECRET_HASH_KEY, digest_size=20
                        ).hexdigest()
                        user_db = UserModel(
                            user_id=user.visit_id,
                            permanent_user_id=user_id,
                            # user_type=user.user_type,
                            task_id=user.task_id,
                            environment_id=user.env_instance_id,
                            agent_id=user.agent_key,
                        )
                        local_session.merge(user_db)
                        # local_session.commit()
                        # user_agent = db_models.UserDataModel.query.filter(db_models.UserDataModel.visit_id == user.visit_id)\
                        #     .filter(db_models.UserDataModel.key_string == 'User-Agent').one()
                        # if user_agent is not None:
                        #     kw_model = EnvironmentKeywordDataModel(
                        #         environment_id=env_instance.instance_id,
                        #         agent_id=user.agent_key,
                        #         key='User-Agent',
                        #         value=user_agent.value_string,
                        #         value_required=''
                        #     )
                        #     local_session.merge(kw_model)
                        #     local_session.commit()
                        # kw_model = EnvironmentKeywordDataModel(
                        #     environment_id=env_instance.instance_id,
                        #     agent_id=user.agent_key,
                        #     key='completed',
                        #     value=user.completed,
                        #     value_required=''
                        # )
                        # local_session.merge(kw_model)
                        # local_session.commit()
                        # kw_model = EnvironmentKeywordDataModel(
                        #     environment_id=env_instance.instance_id,
                        #     agent_id=user.agent_key,
                        #     key='bonus',
                        #     value=user.bonus,
                        #     value_required=''
                        # )
                        # local_session.merge(kw_model)
                        # local_session.commit()
                    kw_model = EnvironmentKeywordDataModel(
                        environment_id=env_instance.instance_id,
                        agent_id="all",
                        key="created_on",
                        value=env_instance.created_on,
                        # value_required=''
                    )
                    local_session.merge(kw_model)
                    # local_session.commit()
                    keyword_datas = db_models.TaskCallableModel.query.filter(
                        db_models.TaskCallableModel.env_instance_id == env_instance.instance_id
                    ).all()
                    for keyword_data in keyword_datas:
                        kw_model = EnvironmentKeywordDataModel(
                            environment_id=env_instance.instance_id,
                            agent_id=keyword_data.agent_key,
                            key=keyword_data.callable_key,
                            value=value_to_appropriate_type(keyword_data.value_achieved),
                            # value_required=value_to_appropriate_type(
                            #     keyword_data.value_required)
                        )
                        local_session.merge(kw_model)
                        # local_session.commit()
                    for k in task_definitions[env_instance.task_id].keys():
                        kw_model = EnvironmentKeywordDataModel(
                            environment_id=env_instance.instance_id,
                            agent_id="all",
                            key=k,
                            value=task_definitions[env_instance.task_id][k],
                            # value_required=None
                        )
                        local_session.merge(kw_model)
                        # local_session.commit()
                    local_session.commit()
                else:
                    print(f"Env {env_instance.instance_id} has no trajectories.")
            else:
                print(f"Skipping env {env_instance.instance_id} due to task {env_instance.task_id}")
