from crowdplay_datasets.dataset import (
    EnvironmentKeywordDataModel,
    EnvironmentModel,
    EpisodeKeywordDataModel,
    EpisodeModel,
    UserModel,
    get_engine_and_session,
    get_trajectory_by_id,
)

if __name__ == "__main__":

    # Advanced filtering
    _, session = get_engine_and_session("crowdplay_atari-v0")
    # Filter by episodes with score > 100
    episodes = (
        session.query(EpisodeModel)
        .filter(EpisodeKeywordDataModel.key == "Score")
        .filter(EpisodeKeywordDataModel.value > 100)
        .filter(EpisodeKeywordDataModel.episode_id == EpisodeModel.episode_id)
        .filter(EnvironmentModel.environment_id == EpisodeModel.environment_id)
        .filter(EnvironmentModel.task_id == "space_invaders_insideout")
        .all()
    )
    # print(episodes)
    # trajectory = get_trajectory_by_id(episodes[0].episode_id)
    # print(trajectory)
    episode = episodes[0]
    print(episode)
    print(episode.keyword_data)
    print(episode.environment.keyword_data)
    trajectory = episode.get_raw_trajectory()
    print(trajectory)
