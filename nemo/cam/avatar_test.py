import unittest
from types import SimpleNamespace

from nemo.cam import avatar


def _one_move_game(result_after_move, evaluation=0.0):
    return SimpleNamespace(
        moves=lambda s: ["m"] if s == "start" else [],
        play=lambda s, m: "end",
        to_move=lambda s: 0,
        outcome=lambda s: result_after_move if s == "end" else None,
        evaluate=lambda s, p: evaluation,
        HARD_DEPTH=1,
    )


class FaceTest(unittest.TestCase):
    def test_faces_run_from_gloating_to_sulking(self):
        captions = [avatar.face(m)[1] for m in (1.0, 0.3, 0.0, -0.3, -1.0)]
        self.assertEqual(captions, [
            "Nemo is gloating", "Nemo likes this", "Nemo is thinking",
            "Nemo is worried", "Nemo is sulking",
        ])

    def test_boundaries_belong_to_the_happier_face(self):
        self.assertEqual(avatar.face(0.6)[1], "Nemo is gloating")
        self.assertEqual(avatar.face(-0.2)[1], "Nemo is thinking")

    def test_panel_fits_a_narrow_screen(self):
        for m in (1.0, 0.0, -1.0):
            lines = avatar.panel(m)
            self.assertEqual(len(lines), 2)
            self.assertTrue(all(len(line) <= 20 for line in lines))


class MoodTest(unittest.TestCase):
    def test_a_win_in_one_is_full_glee(self):
        self.assertEqual(avatar.mood(_one_move_game(0), "start"), 1.0)

    def test_a_forced_loss_is_full_gloom(self):
        self.assertEqual(avatar.mood(_one_move_game(1), "start"), -1.0)

    def test_heuristic_moods_are_clamped(self):
        self.assertEqual(avatar.mood(_one_move_game(None, 5.0), "start"), 1.0)
        self.assertEqual(avatar.mood(_one_move_game(None, 0.25), "start"), 0.25)

    def test_a_finished_game_is_neutral(self):
        self.assertEqual(avatar.mood(_one_move_game(0), "end"), 0.0)


if __name__ == "__main__":
    unittest.main()
