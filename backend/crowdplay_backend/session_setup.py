from datetime import datetime
from uuid import uuid4

from flask import current_app

from .db import db
from .db_models import (
    SessionModel,
    get_games_by_assignment_id,
    get_total_reward_by_assignment_id,
)
from .exceptions import ErrorArguments, InstanceNotFound, TokenForbidden
from .logger import getLogger

logger = getLogger("SessionSetup")


class SessionSetup:
    def __init__(self, info, create=True):
        self.info = info

        # if 'assignmentId' not in info:
        #     logger.error('No assignmentId provided')
        #     raise ErrorArguments('assignmentId')

        if create:
            logger.info(f"No model found. Inserting: {info}")

            assignment_id = info["assignmentId"]
            worker_id = info["workerId"]
            hit_id = info["hitId"]
            task_id = info["taskId"]
            env_instance_id = info["env_instance_id"]
            agent_key = info["agent_key"]
            user_type = info["userType"]
            visit_id = uuid4().hex

            session_model = SessionModel(
                visit_id=visit_id,
                assignment_id=assignment_id,
                worker_id=worker_id,
                hit_id=hit_id,
                task_id=task_id,
                token=uuid4().hex,
                env_instance_id=env_instance_id,
                agent_key=agent_key,
                user_type=user_type,
            )

            db.session.add(session_model)
            db.session.commit()
            self.visit_id = session_model.visit_id
        else:
            self.visit_id = info["visit_id"]

    @staticmethod
    def get_model(visit_id):
        return SessionModel.query.get(visit_id)

    def get_details(self, with_token=False):
        session_model = self.get_model(self.visit_id)

        if session_model is None:
            raise InstanceNotFound

        details = session_model.to_dict()

        # Calculate time since creation
        created_on = details["created_on"]
        now = datetime.utcnow()
        timedelta = now - created_on

        details["time_since"] = timedelta.total_seconds()
        details["time_min"] = current_app.config["TIME_PLAYING"]

        if with_token:
            # Token is required. Should we give it away?
            if not session_model.completed >= 1:
                raise TokenForbidden("Task not completed.")
        else:
            del details["token"]

        return details
