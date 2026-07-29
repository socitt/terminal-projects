import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # region-explorer/

import engine
from washington import STATE

_MIN_WIDTH = 28
_MAX_WIDTH = 39


def _widths(grid):
    return {len(row) for row in grid}


class WashingtonDataTest(unittest.TestCase):
    def test_overview_rows_all_equal_width(self):
        self.assertEqual(len(_widths(STATE["art"])), 1)

    def test_six_regions_with_unique_ids(self):
        ids = [r["id"] for r in STATE["regions"]]
        self.assertEqual(len(ids), 6)
        self.assertEqual(len(set(ids)), 6)

    def test_every_region_center_is_within_the_overview_grid(self):
        rows = len(STATE["art"])
        cols = len(STATE["art"][0])
        for region in STATE["regions"]:
            r, c = region["center"]
            self.assertTrue(0 <= r < rows, region["id"])
            self.assertTrue(0 <= c < cols, region["id"])

    def test_every_detail_art_rows_all_equal_width(self):
        for region in STATE["regions"]:
            self.assertEqual(len(_widths(region["detail_art"])), 1, region["id"])

    def test_detail_art_width_within_narrow_terminal_target(self):
        for region in STATE["regions"]:
            width = len(region["detail_art"][0])
            self.assertTrue(_MIN_WIDTH <= width <= _MAX_WIDTH, region["id"])

    def test_overview_width_matches_engine_display_cols_default(self):
        self.assertEqual(len(STATE["art"][0]), engine.DISPLAY_COLS)

    def test_every_region_has_at_least_one_landmark(self):
        for region in STATE["regions"]:
            self.assertGreater(len(region["landmarks"]), 0, region["id"])

    def test_zoom_frames_ends_on_each_regions_own_detail_art(self):
        for region in STATE["regions"]:
            frames = engine.zoom_frames(STATE, region["id"], num_frames=4)
            self.assertEqual(frames[-1], region["detail_art"])


if __name__ == "__main__":
    unittest.main()
