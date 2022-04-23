import unittest

from crowdplay_backend.utils import consolidate_steps


class TestUtils(unittest.TestCase):
    def test_consolidate_steps(self):
        # Let's use 3 agents 3 steps
        steps = [
            {"game_id": "game1", "step_iter": 1, "agent_key": "agent_A", "reward": 0},
            {"game_id": "game1", "step_iter": 1, "agent_key": "agent_B", "reward": 0},
            {"game_id": "game1", "step_iter": 1, "agent_key": "agent_C", "reward": 0},
            {"game_id": "game1", "step_iter": 2, "agent_key": "agent_A", "reward": 0},
            {"game_id": "game1", "step_iter": 2, "agent_key": "agent_B", "reward": 1},
            {"game_id": "game1", "step_iter": 2, "agent_key": "agent_C", "reward": 1},
            {"game_id": "game1", "step_iter": 3, "agent_key": "agent_A", "reward": 2},
            {"game_id": "game1", "step_iter": 3, "agent_key": "agent_B", "reward": 1},
            {"game_id": "game1", "step_iter": 3, "agent_key": "agent_C", "reward": 5},
        ]

        consolidated_steps = consolidate_steps(steps)

        self.assertEqual(len(consolidated_steps), 3)

        self.assertListEqual(list(consolidated_steps[0].keys()), ["step_iter", "agents"])
        self.assertListEqual(list(consolidated_steps[1].keys()), ["step_iter", "agents"])
        self.assertListEqual(list(consolidated_steps[2].keys()), ["step_iter", "agents"])

        self.assertEqual(consolidated_steps[0]["step_iter"], 1)
        self.assertEqual(consolidated_steps[1]["step_iter"], 2)
        self.assertEqual(consolidated_steps[2]["step_iter"], 3)

        self.assertListEqual(list(consolidated_steps[0]["agents"].keys()), ["agent_A", "agent_B", "agent_C"])
        self.assertListEqual(list(consolidated_steps[1]["agents"].keys()), ["agent_A", "agent_B", "agent_C"])
        self.assertListEqual(list(consolidated_steps[2]["agents"].keys()), ["agent_A", "agent_B", "agent_C"])

        self.assertDictEqual(consolidated_steps[0]["agents"]["agent_A"], {"reward": 0})
        self.assertDictEqual(consolidated_steps[1]["agents"]["agent_B"], {"reward": 1})
        self.assertDictEqual(consolidated_steps[2]["agents"]["agent_C"], {"reward": 5})
