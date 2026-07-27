"""End-to-end tests for the dungeon story: run the real main.py as a
subprocess with piped input, same style as every board game's
main_test.py. Each scenario was hand-verified live against the real
script first (same discipline as go's snapback/ko fixtures and chess's
castling/en passant checks), before being encoded here.
"""

import subprocess
import sys
import unittest
from pathlib import Path

MAIN = Path(__file__).resolve().parent / "main.py"
SAVE = Path(__file__).resolve().parent / "save.json"


def _run(input_text, timeout=10):
    return subprocess.run(
        [sys.executable, str(MAIN)],
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class DungeonEndToEndTest(unittest.TestCase):
    def tearDown(self):
        SAVE.unlink(missing_ok=True)

    def test_full_escape_with_treasure(self):
        # cell -> search -> torch_room -> pry stone -> found_key_room ->
        # door -> corridor -> study guard (loop) -> down -> vault_entrance
        # -> slip past -> vault -> grab treasure -> ending.
        result = _run("1\n1\n1\n1\n2\n1\n1\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("a sack of gold", result.stdout)
        self.assertIn("THE END", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertFalse(SAVE.exists())

    def test_escape_plain_without_treasure(self):
        # cell -> search -> torch_room -> pry stone -> found_key_room ->
        # door -> corridor -> straight up to the exit.
        result = _run("1\n1\n1\n3\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Free.", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_shouting_leads_to_bad_ending(self):
        result = _run("2\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("YOU", result.stdout)
        self.assertIn("AGAIN", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_vault_sneak_hidden_until_guard_studied(self):
        # Reach vault_entrance without ever studying the guard: "Slip
        # past" must be gated out entirely, leaving only "Turn back" (a
        # loop to corridor), then head up to a clean ending.
        result = _run("1\n1\n1\n2\n1\n3\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("VAULT", result.stdout)
        self.assertNotIn("Slip past the sleeping guard", result.stdout)
        self.assertIn("Free.", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_save_and_resume_across_two_runs(self):
        first = _run("1\ns\n")
        self.assertEqual(first.returncode, 0)
        self.assertTrue(SAVE.exists())

        second = _run("y\n1\n1\n3\n")
        self.assertEqual(second.returncode, 0)
        self.assertIn("Saved game found", second.stdout)
        self.assertIn("Free.", second.stdout)
        self.assertNotIn("Traceback", second.stdout + second.stderr)
        self.assertFalse(SAVE.exists())


if __name__ == "__main__":
    unittest.main()
