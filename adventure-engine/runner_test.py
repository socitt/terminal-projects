"""End-to-end tests for runner.py: run the real interactive loop as a
subprocess with piped input, same style as every board game's
main_test.py, against a tiny fixture story (not real prose) rather than
either real story pack. This covers the I/O wiring itself (rendering,
numbered-choice prompts, save-and-quit, resume-or-decline) -- the
branching/state logic it calls is already covered by engine_test.py.
"""

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import engine

ENGINE_DIR = Path(__file__).resolve().parent

FIXTURE_SCRIPT = textwrap.dedent(f"""
    import sys
    sys.path.insert(0, {str(ENGINE_DIR)!r})
    import types
    import runner

    story = types.SimpleNamespace(
        START="start",
        SCENES={{
            "start": {{
                "text": "Start.",
                "choices": [{{"label": "Go on", "target": "middle"}}],
            }},
            "middle": {{
                "text": "Middle.",
                "choices": [{{"label": "Finish", "target": "end"}}],
            }},
            "end": {{"text": "End.", "choices": []}},
        }},
    )

    runner.run(story, sys.argv[1])
    """)


def _run(fixture_path, save_path, input_text, timeout=10):
    return subprocess.run(
        [sys.executable, str(fixture_path), str(save_path)],
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class RunnerEndToEndTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp_path = Path(self.tmp.name)
        self.fixture_path = tmp_path / "fixture_main.py"
        self.fixture_path.write_text(FIXTURE_SCRIPT)
        self.save_path = tmp_path / "save.json"

    def test_full_playthrough_reaches_ending(self):
        result = _run(self.fixture_path, self.save_path, "1\n1\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("THE END", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertFalse(self.save_path.exists())

    def test_save_and_quit_creates_save_file(self):
        # From "start", choice 1 moves to "middle"; "s" saves there.
        result = _run(self.fixture_path, self.save_path, "1\ns\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Saved.", result.stdout)
        self.assertTrue(self.save_path.exists())
        saved = engine.load_state(self.save_path)
        self.assertEqual(saved["scene"], "middle")

    def test_resume_continues_saved_game(self):
        _run(self.fixture_path, self.save_path, "1\ns\n")
        self.assertTrue(self.save_path.exists())

        result = _run(self.fixture_path, self.save_path, "y\n1\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Saved game found", result.stdout)
        self.assertIn("THE END", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertFalse(self.save_path.exists())

    def test_declining_resume_starts_a_fresh_game(self):
        # Seed a save mid-story, then decline resuming it.
        engine.save_state({"scene": "middle", "inventory": [], "flags": {},
                            "visited": ["start", "middle"]}, self.save_path)

        result = _run(self.fixture_path, self.save_path, "n\n1\n1\n")
        self.assertEqual(result.returncode, 0)
        # "Start." only renders if play genuinely began at story.START --
        # a forced/ignored-answer resume would jump straight to "middle"
        # and never print it.
        self.assertIn("Start.", result.stdout)
        self.assertIn("THE END", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
