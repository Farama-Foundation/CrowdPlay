CREATE DATABASE IF NOT EXISTS crowdplaydb;

USE crowdplaydb;

-- Lists all the environmnets (EnvRunner objects) created.
-- instance_id: UUID of the EnvRunner.
-- env_id: ID of the environment, e.g. SpaceInvaders-v0. Not really used anywhere anymore.
-- task_id: The task ID of the env, e.g. space_invaders, as defined in crowdplay_environments.py. Has replaced env_id, but does much more.
-- hit_id: The HIT ID if we're coming from Amazon.
-- created_on: Date/Time when env was created.
-- envprocess_status_code: 0 if running, 1 if exited properly, 2 if killed
-- dbprocess_status_code: 0 if running, 1 if exited properly, 2 if killed
CREATE TABLE IF NOT EXISTS envs (
	instance_id VARCHAR(32) NOT NULL, 
	env_id VARCHAR(30) NOT NULL, 
	task_id VARCHAR(255) NOT NULL, 
	hit_id VARCHAR(255) NOT NULL, 
	created_on DATETIME, 
	envprocess_status_code TINYINT NOT NULL DEFAULT 0,
	dbprocess_status_code TINYINT NOT NULL DEFAULT 0,
	PRIMARY KEY (instance_id)
);

-- Tracks task callables per env
CREATE TABLE IF NOT EXISTS task_callable_per_env (
	env_instance_id VARCHAR(32) NOT NULL,
	agent_key VARCHAR(255) NOT NULL, 
	callable_key VARCHAR(255) NOT NULL, 
	value_achieved VARCHAR(255) NOT NULL,
	value_required VARCHAR(255) NOT NULL,
	PRIMARY KEY (env_instance_id, agent_key, callable_key),
	FOREIGN KEY(env_instance_id) REFERENCES envs (instance_id)
);

-- Tracks task callables per env
-- This tracks to overall cumulative(!) progress toward the task callable. Useful for debugging purposes mostly.
-- There is a separate table that tracks metrics for each episode.
CREATE TABLE IF NOT EXISTS task_callable_per_game (
	env_instance_id VARCHAR(32) NOT NULL,
	episode_id VARCHAR(32) NOT NULL,
	agent_key VARCHAR(255) NOT NULL, 
	callable_key VARCHAR(255) NOT NULL, 
	value_achieved VARCHAR(255) NOT NULL,
	value_required VARCHAR(255) NOT NULL,
	PRIMARY KEY (env_instance_id, episode_id, agent_key, callable_key),
	FOREIGN KEY(env_instance_id) REFERENCES envs (instance_id)
);

-- Tracks callables per episode
-- This tracks stats for each episode only, non-cumulative.
CREATE TABLE IF NOT EXISTS episode_callable (
	env_instance_id VARCHAR(32) NOT NULL,
	episode_id VARCHAR(32) NOT NULL,
	agent_key VARCHAR(255) NOT NULL, 
	callable_key VARCHAR(255) NOT NULL, 
	value_achieved VARCHAR(255) NOT NULL,
	value_required VARCHAR(255) NOT NULL,
	PRIMARY KEY (env_instance_id, episode_id, agent_key, callable_key),
	FOREIGN KEY(env_instance_id) REFERENCES envs (instance_id)
);


-- Table that lists all user visits to the page.
-- Originally used to track MTurk details, but does more now.
-- TODO rename this.
-- visit_id: Unique ID of this visit (new ID if user refreshes page!)
-- assignment_id: MTurk assignment ID, randomly generated for other user types.
-- worker_id: MTurk worker ID, or random ID for other user types..
-- hit_id: MTurk HIT ID.
-- created_on: obvious
-- token: A token we give to MTurkers that they can enter on the MTurk website to show they completed the task.
-- env_instance_id: Instance ID of the environment (EnvRunner object).
-- agent_key: Agent ID that this user was controlling in that game, relevant for multiplayer games.
-- completed: Did they complete the task (>=1) or not (<1). Float, so we can see partial completion.
-- bonus: Bonus payment this user gets (relevant for MTurkers)
-- user_type: What kind of user is this (MTurk, Email, Lab in the Wild, Social Media, etc.)
CREATE TABLE IF NOT EXISTS sessions (
	visit_id VARCHAR(255) NOT NULL,
	assignment_id VARCHAR(255) NOT NULL, 
	worker_id VARCHAR(255) NOT NULL, 
	hit_id VARCHAR(255) NOT NULL, 
	task_id VARCHAR(255) NOT NULL, 
	created_on DATETIME, 
	token VARCHAR(32), 
	env_instance_id VARCHAR(32) NOT NULL, 
	agent_key VARCHAR(255) NOT NULL, 
	completed FLOAT NOT NULL default 0, 
	bonus FLOAT NOT NULL default 0, 
	user_type VARCHAR(255) NOT NULL,
	PRIMARY KEY (visit_id),
	UNIQUE KEY unique_token (token),
	FOREIGN KEY(env_instance_id) REFERENCES envs (instance_id)
);

-- Tracks additional user data as key-value pairs.
-- Currently only used for user email for a raffle.
-- But could track other data.
CREATE TABLE IF NOT EXISTS user_data (
	info_id INT NOT NULL AUTO_INCREMENT,
	visit_id VARCHAR(32) NOT NULL,
	key_string VARCHAR(255) NOT NULL, 
	value_string TEXT NOT NULL,
	PRIMARY KEY (info_id),
	FOREIGN KEY(visit_id) REFERENCES sessions (visit_id)
);

-- Tracks each game (i.e. episode) played.
-- TODO should rename this "episodes"
-- id: id of the game / episode
-- env_instance_id: ID of the environment (EnvRunner object)
-- hit_id: HIT ID. Probably not needed in this many places (TODO!)
-- started_on, ended_on: start and end time of this episode
CREATE TABLE IF NOT EXISTS games (
	id VARCHAR(32) NOT NULL, 
	env_instance_id VARCHAR(32), 
	hit_id VARCHAR(255), 
	started_on DATETIME, 
	ended_on DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(env_instance_id) REFERENCES envs (instance_id)
);

-- Stores trajectories.
-- TODO this will replace the steps table
-- episode_id: id of the game / episode
-- trajectory: Pickled and bzipped trajectory
CREATE TABLE IF NOT EXISTS episode_trajectories (
	episode_id VARCHAR(32) NOT NULL, 
	trajectory LONGBLOB NOT NULL,
	PRIMARY KEY (episode_id), 
	FOREIGN KEY(episode_id) REFERENCES games (id)
);

-- Grant user privileges.
GRANT ALL PRIVILEGES ON crowdplaydb.* TO 'crowdplayuser'@'%';
FLUSH PRIVILEGES;
