import unittest

import engine

# 6 rows x 8 cols, every cell a distinct char so crop/scale bugs are
# visible (row/col confusion, off-by-one, etc.) rather than hidden by
# repeated characters.
_GRID = [
    "01234567",
    "89ABCDEF",
    "GHIJKLMN",
    "OPQRSTUV",
    "WXYZabcd",
    "efghijkl",
]

_FIXTURE_STATE = {
    "name": "Fixture",
    "art": _GRID,
    "regions": [
        {
            "id": "corner",
            "name": "Corner Region",
            "center": (0, 0),
            "detail_art": ["+--+", "|corner|", "+--+"],
        },
        {
            "id": "middle",
            "name": "Middle Region",
            "center": (2, 4),
            "detail_art": ["middle detail"],
        },
    ],
}


class CropWindowTest(unittest.TestCase):
    def test_centered_window_within_bounds(self):
        window = engine.crop_window(_GRID, (2, 4), 3, 3)
        self.assertEqual(window, ["BCD", "JKL", "RST"])

    def test_clamped_at_top_left_edge(self):
        # Centering a 3x3 window on (0, 0) would need negative
        # top/left; must clamp to the grid's actual top-left corner
        # instead of erroring or padding.
        window = engine.crop_window(_GRID, (0, 0), 3, 3)
        self.assertEqual(window, ["012", "89A", "GHI"])

    def test_clamped_at_bottom_right_edge(self):
        # Centering a 3x3 window on (5, 7) would need the window's
        # bottom-right corner past the grid's edge; must clamp to the
        # grid's actual bottom-right corner instead.
        window = engine.crop_window(_GRID, (5, 7), 3, 3)
        self.assertEqual(window, ["TUV", "bcd", "jkl"])

    def test_window_larger_than_grid_is_clamped_to_grid_size(self):
        window = engine.crop_window(_GRID, (2, 4), 100, 100)
        self.assertEqual(window, _GRID)

    def test_window_size_matches_request_when_it_fits(self):
        window = engine.crop_window(_GRID, (2, 4), 2, 4)
        self.assertEqual(len(window), 2)
        self.assertEqual(len(window[0]), 4)


class ScaleNnTest(unittest.TestCase):
    def test_upscale_repeats_nearest_source_cell(self):
        grid = ["AB", "CD"]
        scaled = engine.scale_nn(grid, 4, 4)
        self.assertEqual(scaled, ["AABB", "AABB", "CCDD", "CCDD"])

    def test_downscale_to_single_cell_picks_top_left(self):
        scaled = engine.scale_nn(_GRID, 1, 1)
        self.assertEqual(scaled, ["0"])

    def test_scale_to_same_size_is_identity(self):
        self.assertEqual(engine.scale_nn(_GRID, 6, 8), _GRID)

    def test_empty_grid_returns_empty(self):
        self.assertEqual(engine.scale_nn([], 4, 4), [])


class RegionByIdTest(unittest.TestCase):
    def test_finds_existing_region(self):
        region = engine.region_by_id(_FIXTURE_STATE, "middle")
        self.assertEqual(region["name"], "Middle Region")

    def test_raises_on_unknown_id(self):
        with self.assertRaises(KeyError):
            engine.region_by_id(_FIXTURE_STATE, "nonexistent")


class ZoomFramesTest(unittest.TestCase):
    def test_frame_count_matches_request(self):
        frames = engine.zoom_frames(_FIXTURE_STATE, "middle", num_frames=4)
        self.assertEqual(len(frames), 4)

    def test_last_frame_is_the_detail_art_unscaled(self):
        frames = engine.zoom_frames(_FIXTURE_STATE, "corner", num_frames=3)
        self.assertEqual(frames[-1], _FIXTURE_STATE["regions"][0]["detail_art"])

    def test_first_frame_is_the_full_grid_scaled_to_display_size(self):
        frames = engine.zoom_frames(
            _FIXTURE_STATE, "middle", num_frames=3, display_rows=6, display_cols=8
        )
        self.assertEqual(frames[0], engine.scale_nn(_GRID, 6, 8))

    def test_cropped_frames_all_match_the_requested_display_size(self):
        frames = engine.zoom_frames(
            _FIXTURE_STATE, "middle", num_frames=5, display_rows=5, display_cols=10
        )
        for frame in frames[:-1]:
            self.assertEqual(len(frame), 5)
            self.assertEqual(len(frame[0]), 10)

    def test_frames_narrow_in_progressively_toward_the_region(self):
        # With num_frames=2 there's exactly one cropped frame before
        # the detail art; it should already be a tighter (1/4-size)
        # crop than the full grid, not just the full grid re-scaled.
        frames = engine.zoom_frames(
            _FIXTURE_STATE, "middle", num_frames=2, display_rows=6, display_cols=8
        )
        full_scaled = engine.scale_nn(_GRID, 6, 8)
        self.assertNotEqual(frames[0], full_scaled)

    def test_single_frame_is_just_the_detail_art(self):
        frames = engine.zoom_frames(_FIXTURE_STATE, "corner", num_frames=1)
        self.assertEqual(frames, [_FIXTURE_STATE["regions"][0]["detail_art"]])

    def test_raises_on_num_frames_below_one(self):
        with self.assertRaises(ValueError):
            engine.zoom_frames(_FIXTURE_STATE, "middle", num_frames=0)

    def test_raises_on_unknown_region(self):
        with self.assertRaises(KeyError):
            engine.zoom_frames(_FIXTURE_STATE, "nonexistent")


if __name__ == "__main__":
    unittest.main()
