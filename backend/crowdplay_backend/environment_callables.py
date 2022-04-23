from datetime import timedelta

import numpy as np


class ConstantCallable:
    def __init__(self, constants):
        self.constants = constants

    def __call__(self, step_info):
        return self.constants


class TimeCallable:
    def __init__(self):
        # self.time_goals = time_goals
        self.time_cur = 0

    def __call__(self, step_info):
        self.time_cur += 1
        return {agent: timedelta(seconds=self.time_cur // 60) for agent in step_info["prev_obs"]}


class ActiveTimeCallable:
    """Incentives active play time (at least some reward or action every timout frames)."""

    def __init__(self, agents, timeout=60 * 60, action_timeout=20 * 60):
        self.last_reward_time = {agent: 0 for agent in agents}
        self.last_action_time = {agent: 0 for agent in agents}
        self.agent_active_time = {agent: 0 for agent in agents}
        self.time_cur = 0
        self.timeout = timeout
        self.action_timeout = action_timeout

    def __call__(self, step_info):
        self.time_cur += 1
        for agent in self.agent_active_time:
            if step_info["reward"][agent] != 0:
                self.last_reward_time[agent] = self.time_cur
            if (
                isinstance(step_info["action"][agent], dict)
                and "game" in step_info["action"][agent]
                and step_info["action"][agent]["game"] != 0
            ) or (isinstance(step_info["action"][agent], int) and step_info["action"][agent] > 0):
                self.last_action_time[agent] = self.time_cur
            if self.last_reward_time[agent] + self.timeout >= self.time_cur and (
                self.action_timeout is None or self.last_action_time[agent] + self.action_timeout >= self.time_cur
            ):
                self.agent_active_time[agent] += 1
        return {agent: timedelta(seconds=self.agent_active_time[agent] // 60) for agent in self.agent_active_time}


class ScoreCallable:
    def __init__(self, agents):
        self.reward_cur = {agent: 0 for agent in agents}

    def __call__(self, step_info):
        for agent in step_info["reward"]:
            if agent in self.reward_cur:
                self.reward_cur[agent] += step_info["reward"][agent]
        return {agent: self.reward_cur[agent] for agent in self.reward_cur}
        # {agent: f'Reward: {self.reward_cur[agent]} / {self.reward_goals[agent]}' for agent in self.reward_goals})


class SpaceInvadersLeftRightCallable:
    def __init__(self, position_goals):
        self.position_goals = position_goals
        self.position_cur = {agent: 0 for agent in position_goals}
        self.time = 0

    def __call__(self, step_info):
        self.time += 1
        for agent in step_info["reward"]:
            if agent.endswith("0"):
                pos = (step_info["info"][agent]["RAM"][0x1C] - 0x23) / (0x75 - 0x23)
            else:
                pos = (step_info["info"][agent]["RAM"][0x1D] - 0x23) / (0x75 - 0x23)
            if self.position_goals[agent]["min"] <= pos and pos <= self.position_goals[agent]["max"]:
                self.position_cur[agent] += 1
        return {agent: (self.position_cur[agent] / self.time) for agent in self.position_goals}


# class MinCallable:
#     def __init__(self, callables, list_of_agents):
#         self.callables = callables
#         self.list_of_agents = list_of_agents

#     def __call__(self, step_info):
#         results = []
#         strings = []
#         for callable in self.callables:
#             result, string = callable(step_info)
#             results.append(result)
#             strings.append(string)
#         return ({agent: min([r[agent] for r in results]) for agent in self.list_of_agents},
#                 {agent: ', '.join([s[agent] for s in strings]) for agent in self.list_of_agents})


# class UpToCallable:
#     def __init__(self, maximums, callable):
#         self.maximums = maximums
#         self.callable = callable

#     def __call__(self, step_info):
#         result, string = self.callable(step_info)
#         return ({agent: min(result[agent], self.maximums[agent]) for agent in self.maximums}, string)


def space_invaders_ram_to_aliens(ram):
    """Takes ALE RAM and returns 6x6 nested tuple of aliens present on screen."""
    return tuple(tuple((ram[0x12 + i] & (1 << j)) != 0 for j in range(6)) for i in range(6))
    # for i in range(6):
    #     row = ram[0x12+i]
    #     for j in range(6):
    #         alien = (row & (1<<j) != 0)


# class SpaceInvadersShowAlienMatrix:
#     def __init__(self):
#         pass

#     def __call__(self, step_info):
#         result = {agent: 1 for agent in step_info['reward']}
#         def aliens(agent): return space_invaders_ram_to_aliens(step_info["info"][agent]["RAM"])
#         string = {agent: f'Aliens: {aliens(agent)}' for agent in step_info['info']}
#         return (result, string)


class SpaceInvadersRows135:
    """Incentivises only shooting rows 1,3,5"""

    def __init__(self, agents):
        self.prev_aliens = {agent: tuple(tuple(1 for j in range(6)) for i in range(6)) for agent in agents}
        self.good_aliens = {agent: 0 for agent in agents}
        self.bad_aliens = {agent: 0 for agent in agents}
        pass

    def __call__(self, step_info):
        results = {}
        for agent in step_info["info"]:
            new_aliens = space_invaders_ram_to_aliens(step_info["info"][agent]["RAM"])
            changed_aliens = tuple(
                tuple(self.prev_aliens[agent][i][j] == 1 and new_aliens[i][j] == 0 for j in range(6)) for i in range(6)
            )
            self.prev_aliens[agent] = new_aliens
            for j in (0, 2, 4):
                for i in range(6):
                    if changed_aliens[i][j] == 1:
                        self.good_aliens[agent] += 1
            for j in (1, 3, 5):
                for i in range(6):
                    if changed_aliens[i][j] == 1:
                        self.bad_aliens[agent] += 1
            if self.good_aliens[agent] + self.bad_aliens[agent] > 0:
                alien_ratio = self.good_aliens[agent] / (self.good_aliens[agent] + self.bad_aliens[agent])
            else:
                alien_ratio = 0
            results[agent] = alien_ratio
        return results


class SpaceInvadersAliensHit:
    """Counts number of aliens shot"""

    def __init__(self, agents):
        self.prev_aliens = {agent: tuple(tuple(1 for j in range(6)) for i in range(6)) for agent in agents}
        self.good_aliens = {agent: 0 for agent in agents}
        pass

    def __call__(self, step_info):
        for agent in step_info["info"]:
            new_aliens = space_invaders_ram_to_aliens(step_info["info"][agent]["RAM"])
            changed_aliens = tuple(
                tuple(self.prev_aliens[agent][i][j] == 1 and new_aliens[i][j] == 0 for j in range(6)) for i in range(6)
            )
            self.prev_aliens[agent] = new_aliens
            for j in range(6):
                for i in range(6):
                    if changed_aliens[i][j] == 1:
                        self.good_aliens[agent] += 1
        return self.good_aliens


class SpaceInvadersAccuracy:
    """Calcuates shot accuracy in Space Invaders
    TODO this doesn't factor in the bonus for other agent death in multiplayer
    TODO won't work if rewards are modified, we need clipped game reward
    TODO works only for a single game"""

    def __init__(self, agents):
        self.agents = agents
        self.clipped_reward = {agent: 0 for agent in agents}
        self.shots_fired = {agent: 0 for agent in agents}
        pass

    def __call__(self, step_info):
        for agent in self.agents:
            self.clipped_reward[agent] += np.sign(step_info["reward"][agent])

        # Check if a shot has been fired
        shot_did_fire = {p: False for p in self.agents}

        ale_ram = step_info["info"][self.agents[0]]["RAM"]

        # There are two slots available for shots in flight; either can belong to either player.
        # We will check each, and then check which player it belongs to.
        # Get RAM contents of shot 0 and 1 slots y-coordinate.
        shot0 = ale_ram[0x55]
        shot1 = ale_ram[0x56]

        # New shot starts at y-coordinate 0x55, and no-shot is encoded as 0xf6 (always?).
        # It looks like it is enough to check if a shot is at y-coord 0x55.
        # We check that, then check which player it belongs to, then increase that player's shot counter.
        if shot0 == 0x55:
            if ale_ram[0x18] & 0x4:
                shot_did_fire[self.agents[1]] = True
            else:
                shot_did_fire[self.agents[0]] = True
        if shot1 == 0x55:
            if ale_ram[0x18] & 0x8:
                shot_did_fire[self.agents[1]] = True
            else:
                shot_did_fire[self.agents[0]] = True

        # If a shot has been fired, increment total shot count
        for player in self.agents:
            if shot_did_fire[player]:
                self.shots_fired[player] += 1

        return {
            agent: (self.clipped_reward[agent] / self.shots_fired[agent]) if self.shots_fired[agent] > 0 else 0
            for agent in self.agents
        }


class SpaceInvadersRowsByRow:
    """Incentivises shooting aliens by row"""

    def __init__(self, agents, kind="fraction"):
        self.prev_aliens = {agent: tuple(tuple(1 for j in range(6)) for i in range(6)) for agent in agents}
        self.good_aliens = {agent: 0 for agent in agents}
        self.bad_aliens = {agent: 0 for agent in agents}
        self.kind = kind
        pass

    def __call__(self, step_info):
        results = {}
        for agent in step_info["info"]:
            # Check which aliens have been shot just now
            new_aliens = space_invaders_ram_to_aliens(step_info["info"][agent]["RAM"])
            changed_aliens = tuple(
                tuple(self.prev_aliens[agent][i][j] == 1 and new_aliens[i][j] == 0 for j in range(6)) for i in range(6)
            )
            self.prev_aliens[agent] = new_aliens
            # Check which rows are cleared
            rows_cleared = [True for i in range(-1, 6)]
            for i in range(6):
                for j in range(6):
                    if new_aliens[i][j] == 1:
                        rows_cleared[i] = False
                if not rows_cleared[i]:
                    for k in range(i, 6):
                        rows_cleared[k] = False
                    break
            # Check if the correct aliens have been shot.
            for i in range(6):
                for j in range(6):
                    if changed_aliens[i][j] == 1:
                        if rows_cleared[i - 1]:
                            self.good_aliens[agent] += 1
                        else:
                            self.bad_aliens[agent] += 1
            if self.good_aliens[agent] + self.bad_aliens[agent] > 0:
                alien_ratio = self.good_aliens[agent] / (self.good_aliens[agent] + self.bad_aliens[agent])
            else:
                alien_ratio = 0
            results[agent] = alien_ratio
        if self.kind == "fraction":
            return results
        else:
            return self.good_aliens


class SpaceInvadersOutsideIn:
    """Incentivises shooting aliens by column outside in"""

    def __init__(self, agents, kind="fraction"):
        self.prev_aliens = {agent: tuple(tuple(1 for j in range(6)) for i in range(6)) for agent in agents}
        self.good_aliens = {agent: 0 for agent in agents}
        self.bad_aliens = {agent: 0 for agent in agents}
        self.kind = kind
        pass

    def __call__(self, step_info):
        results = {}
        for agent in step_info["info"]:
            # Check which aliens have been shot just now
            new_aliens = space_invaders_ram_to_aliens(step_info["info"][agent]["RAM"])
            changed_aliens = tuple(
                tuple(self.prev_aliens[agent][i][j] == 1 and new_aliens[i][j] == 0 for j in range(6)) for i in range(6)
            )
            self.prev_aliens[agent] = new_aliens
            # Check which columns are cleared
            cols_cleared = [True for i in range(-1, 7)]
            for i in range(6):
                for j in range(6):
                    if new_aliens[i][j] == 1:
                        cols_cleared[j] = False
                # Propagate cols cleared. But maybe easier to check below.
                # if cols_cleared[j] == False:
                #     for k in range(j, 6):
                #         cols_cleared[k] = False
                #     break
            # Check if the correct aliens have been shot.
            for i in range(6):
                for j in range(3):
                    if changed_aliens[i][j] == 1:
                        if all(list((cols_cleared[k] for k in range(j)))):
                            self.good_aliens[agent] += 1
                        else:
                            self.bad_aliens[agent] += 1
                for j in range(3, 6):
                    if changed_aliens[i][j] == 1:
                        if all(list((cols_cleared[k] for k in range(j + 1, 7)))):
                            self.good_aliens[agent] += 1
                        else:
                            self.bad_aliens[agent] += 1
            if self.good_aliens[agent] + self.bad_aliens[agent] > 0:
                alien_ratio = self.good_aliens[agent] / (self.good_aliens[agent] + self.bad_aliens[agent])
            else:
                alien_ratio = 0
            results[agent] = alien_ratio
        if self.kind == "fraction":
            return results
        else:
            return self.good_aliens


class SpaceInvadersInsideOut:
    """Incentivises shooting aliens by column inside out"""

    def __init__(self, agents, kind="fraction"):
        self.prev_aliens = {agent: tuple(tuple(1 for j in range(6)) for i in range(6)) for agent in agents}
        self.good_aliens = {agent: 0 for agent in agents}
        self.bad_aliens = {agent: 0 for agent in agents}
        self.kind = kind
        pass

    def __call__(self, step_info):
        results = {}
        for agent in step_info["info"]:
            # Check which aliens have been shot just now
            new_aliens = space_invaders_ram_to_aliens(step_info["info"][agent]["RAM"])
            changed_aliens = tuple(
                tuple(self.prev_aliens[agent][i][j] == 1 and new_aliens[i][j] == 0 for j in range(6)) for i in range(6)
            )
            self.prev_aliens[agent] = new_aliens
            # Check which columns are cleared
            cols_cleared = [True for i in range(-1, 7)]
            for i in range(6):
                for j in range(6):
                    if new_aliens[i][j] == 1:
                        cols_cleared[j] = False
                # Propagate cols cleared. But maybe easier to check below.
                # if cols_cleared[j] == False:
                #     for k in range(j, 6):
                #         cols_cleared[k] = False
                #     break
            # Check if the correct aliens have been shot.
            for i in range(6):
                # Innermost two rows
                for j in range(2, 4):
                    if changed_aliens[i][j] == 1:
                        self.good_aliens[agent] += 1
                for j in range(2):
                    if changed_aliens[i][j] == 1:
                        if all(list((cols_cleared[k] for k in range(j + 1, 3)))):
                            self.good_aliens[agent] += 1
                        else:
                            self.bad_aliens[agent] += 1
                for j in range(4, 6):
                    if changed_aliens[i][j] == 1:
                        if all(list((cols_cleared[k] for k in range(3, j)))):
                            self.good_aliens[agent] += 1
                        else:
                            self.bad_aliens[agent] += 1
            if self.good_aliens[agent] + self.bad_aliens[agent] > 0:
                alien_ratio = self.good_aliens[agent] / (self.good_aliens[agent] + self.bad_aliens[agent])
            else:
                alien_ratio = 0
            results[agent] = alien_ratio
        if self.kind == "fraction":
            return results
        else:
            return self.good_aliens


class RiverraidLeftRightCallable:
    def __init__(self, position_goals):
        self.position_goals = position_goals
        self.position_cur = {agent: 0 for agent in position_goals}
        self.time = 0

    def __call__(self, step_info):
        self.time += 1
        for agent in step_info["reward"]:
            if agent.endswith("0"):
                pos = step_info["info"][agent]["RAM"][0x33] - 0x4C
            if self.position_goals[agent]["min"] <= pos and pos <= self.position_goals[agent]["max"]:
                self.position_cur[agent] += 1
        return {agent: (self.position_cur[agent] / self.time) for agent in self.position_goals}
