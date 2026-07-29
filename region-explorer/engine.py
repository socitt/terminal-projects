"""Pure zoom logic for region-explorer: crop, scale, and chain into a
zoom-frame sequence. No I/O -- state data comes from a `STATE` dict
(see `data/washington.py` for the shape), rendering is `runner.py`'s
job.
"""

DISPLAY_ROWS = 16
DISPLAY_COLS = 36


def region_by_id(state, region_id):
    for region in state["regions"]:
        if region["id"] == region_id:
            return region
    raise KeyError(region_id)


def crop_window(grid, center, win_rows, win_cols):
    """Return a `win_rows` x `win_cols` window of `grid` centered on
    `center` (row, col), clamped so the window never runs off the
    grid's edges (shifted, not padded).
    """
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    win_rows = min(win_rows, rows)
    win_cols = min(win_cols, cols)

    center_row, center_col = center
    top = center_row - win_rows // 2
    left = center_col - win_cols // 2
    top = max(0, min(top, rows - win_rows))
    left = max(0, min(left, cols - win_cols))

    return [row[left : left + win_cols] for row in grid[top : top + win_rows]]


def scale_nn(grid, target_rows, target_cols):
    """Nearest-neighbor scale `grid` to exactly `target_rows` x
    `target_cols`, in either direction (shrink or enlarge).
    """
    src_rows = len(grid)
    src_cols = len(grid[0]) if src_rows else 0
    if src_rows == 0 or src_cols == 0 or target_rows <= 0 or target_cols <= 0:
        return []

    out = []
    for r in range(target_rows):
        src_r = min(src_rows - 1, (r * src_rows) // target_rows)
        row_src = grid[src_r]
        chars = []
        for c in range(target_cols):
            src_c = min(src_cols - 1, (c * src_cols) // target_cols)
            chars.append(row_src[src_c])
        out.append("".join(chars))
    return out


def _window_sizes(rows, cols, num_steps):
    """Return `num_steps` (rows, cols) window sizes shrinking from the
    full grid size down to a minimum (1/4 size, floor 1) size, evenly
    spaced.
    """
    min_rows = max(1, rows // 4)
    min_cols = max(1, cols // 4)
    sizes = []
    for i in range(num_steps):
        t = i / (num_steps - 1) if num_steps > 1 else 1.0
        win_rows = round(rows - t * (rows - min_rows))
        win_cols = round(cols - t * (cols - min_cols))
        sizes.append((win_rows, win_cols))
    return sizes


def zoom_frames(
    state,
    region_id,
    num_frames=4,
    display_rows=DISPLAY_ROWS,
    display_cols=DISPLAY_COLS,
):
    """Return a list of `num_frames` char-grids: the first `num_frames
    - 1` are shrinking, edge-clamped crops of `state["art"]` centered
    on the region, each nearest-neighbor scaled to a consistent
    `display_rows` x `display_cols` size, and the last is the region's
    hand-authored `detail_art` (returned as-is, not scaled).
    """
    if num_frames < 1:
        raise ValueError("num_frames must be >= 1")

    region = region_by_id(state, region_id)
    grid = state["art"]
    rows = len(grid)
    cols = len(grid[0]) if rows else 0

    cropped_steps = num_frames - 1
    frames = []
    for win_rows, win_cols in _window_sizes(rows, cols, cropped_steps):
        window = crop_window(grid, region["center"], win_rows, win_cols)
        frames.append(scale_nn(window, display_rows, display_cols))

    frames.append(region["detail_art"])
    return frames
