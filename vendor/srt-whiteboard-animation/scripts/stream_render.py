#!/usr/bin/env python3
"""
Stream-stroke animation — single-image rendering entry point

Render a color image as a whiteboard animation with continuous pen movement and ink deposition.
Rendering has three stages:
  ink: the pen traces the ink stream and reveals black line art.
  color: the pen follows the same path again to reveal original colors.
  gaze: hold the complete source image after drawing.

Unlike cell-by-cell jumps, drawing order is represented as a pen-motion polyline.
Interpolate adjacent positions and deposit ink continuously as the brush slides along the path.
"""
from __future__ import annotations

import argparse
import datetime
import math
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np

# ──────────────────────────────────────────────────────────────
# Resource discovery
# ──────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
_ASSETS_DIR = _SCRIPT_DIR.parent / "assets"
DEFAULT_HAND_PNG = _ASSETS_DIR / "drawing-hand.png"


def _imread_any(path: str | Path, flags: int = cv2.IMREAD_COLOR) -> np.ndarray | None:
    """
    Read an image, including Windows paths with spaces or non-ASCII characters.
    Read bytes with np.fromfile and decode with cv2.imdecode,
    bypassing cv2.imread compatibility issues with non-ASCII paths.
    """
    raw = np.fromfile(str(path), dtype=np.uint8)
    if raw.size == 0:
        return None
    return cv2.imdecode(raw, flags)


# ──────────────────────────────────────────────────────────────
# Centralized rendering parameters
# ──────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Config:
    fps: int = 60                  # Higher frame rate makes pen motion closer to continuous writing
    grid_edge: int = 10            # Smaller grid reduces blockiness in ink reveals
    sample_step: int = 2           # Pen trajectory sampling interval in pixels
    cap_long_edge: int = 1080      # Maximum input image long edge
    brush_radius: int = 40         # Circular brush radius for coloring
    ink_weight: int = 2            # Ink-stage weight: allow more time to observe strokes
    color_weight: int = 1          # Color-stage weight
    gaze_seconds: float = 3.0      # Baseline finished-image hold duration in seconds
    ink_threshold: int = 10        # Pixels below this grayscale value count as ink
    ink_reveal_radius: int = 4     # Radius within which a pen segment reveals line art
    target_hand_height: int = 493  # Scaled hand asset target height (tuned for 1080p)
    # Normalized pen-tip coordinates in the asset (0..1) define the ink-contact pixel.
    # The bundled drawing-hand.png is cropped with the tip at its top-left, so its anchor is (0, 0).
    # This describes the actual ink-contact point, not the hand image bounding box.
    tip_anchor_x: float = 0.0
    tip_anchor_y: float = 0.0
    canvas_hex: str = "#F6F1E3"    # Canvas background color
    match_bg: bool = True          # Match source background to canvas so ink and coloring backgrounds agree
    match_bg_threshold: int = 28   # Pixels within this summed BGR-channel difference count as background
    steps_per_frame: int = 4       # Baseline pen positions advanced per frame
    # Contour-wipe coloring parameters
    color_fill: str = "contour-wipe"  # Coloring: "contour-wipe" contour-aware top-down scan (default); "brush" follows strokes
    wipe_decay: float = 0.86       # Downward row-to-row resistance decay (half-life about 4.6px)
    wipe_delay_ratio: float = 0.04  # Frontier delay at contours as a fraction of h, clamped to [12,52]
    wipe_blocks: int = 18          # Number of side-to-side pen sweeps
    # Adaptive ink-stage pauses (simulate breathing and pen changes)
    # pause_mode: "heavy" pronounced pauses (default); "auto" density-based; "off" disabled; "light" brief
    pause_mode: str = "heavy"
    pause_ratio_heavy: float = 0.03   # Low-density slow pacing: about 3% of frames are pauses
    pause_ratio_light: float = 0.008  # Medium-density pause fraction: about 0.8%
    # Density thresholds use frames_per_cell to measure available time relative to content.
    # >= heavy_fpc: ample time, heavy pauses; >= light_fpc: moderate, light pauses;
    # < light_fpc: dense content, tight timing, no pauses.
    pause_heavy_fpc: float = 0.7
    pause_light_fpc: float = 0.4
    # Ink path modes
    # ink_path_mode: "grid" interpolated cell centers (default); "skeleton" pixel-level skeleton tracing
    ink_path_mode: str = "grid"
    skeleton_min_points: int = 8        # Minimum points per skeleton stroke (fragment filter)
    skeleton_resample_spacing: float = 2.5  # Skeleton resampling interval in pixels


# ──────────────────────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────────────────────
def _hex_to_bgr(hex_color: str) -> np.ndarray:
    digits = hex_color.lstrip("#")
    if len(digits) != 6:
        raise ValueError(f"Invalid color value: {hex_color}")
    r = int(digits[0:2], 16)
    g = int(digits[2:4], 16)
    b = int(digits[4:6], 16)
    return np.array([b, g, r], dtype=np.uint8)


def _bounding_box(mask: np.ndarray) -> tuple[tuple[int, int], tuple[int, int]]:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return (0, 0), (0, 0)
    return (int(xs.min()), int(ys.min())), (int(xs.max()), int(ys.max()))


# ──────────────────────────────────────────────────────────────
# Ink grid partitioning
# ──────────────────────────────────────────────────────────────
def _to_grid_blocks(image: np.ndarray, edge: int) -> np.ndarray:
    """Split an HxW (x C) image into a tiled view of (rows, columns, edge, edge[, C])."""
    image = np.ascontiguousarray(image)
    h, w = image.shape[:2]
    if h % edge or w % edge:
        raise ValueError(f"Image dimensions {w}x{h} must be multiples of {edge}")
    rows, cols = h // edge, w // edge
    if image.ndim == 2:
        return image.reshape(rows, edge, cols, edge).transpose(0, 2, 1, 3)
    return image.reshape(rows, edge, cols, edge, image.shape[2]).transpose(0, 2, 1, 3, 4)


def _active_mask(threshold_map: np.ndarray, edge: int, threshold: int) -> np.ndarray:
    """Return cells containing ink, where any pixel in a cell is below the grayscale threshold."""
    blocks = _to_grid_blocks(threshold_map, edge)
    return np.any(blocks < threshold, axis=(2, 3))


# ──────────────────────────────────────────────────────────────
# Ink-stream clustering and density-guided traversal
# ──────────────────────────────────────────────────────────────
def _label_components(active: np.ndarray) -> tuple[np.ndarray, int]:
    """Label 8-connected ink-cell components; return (label map, component count)."""
    n, labels = cv2.connectedComponents(active.astype(np.uint8), connectivity=8)
    return labels, n - 1  # Exclude background label 0


def _component_cells(labels: np.ndarray, label: int) -> list[tuple[int, int]]:
    coords = np.argwhere(labels == label)
    return [(int(r), int(c)) for r, c in coords]


def _merge_small_components(
    components: list[list[tuple[int, int]]],
    merge_threshold: int,
) -> list[list[tuple[int, int]]]:
    """
    Merge small connected components (cell count <= merge_threshold) into the nearest large component.
    This prevents tiny one- or two-cell fragments from interrupting large text regions.
    If no large component exists, retain the originals without discarding ink.
    """
    if not components:
        return components
    big = [c for c in components if len(c) > merge_threshold]
    small = [c for c in components if len(c) <= merge_threshold]
    if not small or not big:
        return components

    # Precompute the centroid of each large region
    centroids = []
    for cells in big:
        rs = [c[0] for c in cells]
        cs = [c[1] for c in cells]
        centroids.append((sum(rs) / len(rs), sum(cs) / len(cs)))

    # Merge each small fragment into its nearest large region
    merged = [list(cells) for cells in big]  # Make appendable copies
    for cells in small:
        rs = [c[0] for c in cells]
        cs = [c[1] for c in cells]
        cr = sum(rs) / len(rs)
        cc = sum(cs) / len(cs)
        best = min(
            range(len(big)),
            key=lambda i: (centroids[i][0] - cr) ** 2 + (centroids[i][1] - cc) ** 2,
        )
        merged[best].extend(cells)
    return merged


def _bounds(cells: Sequence[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _split_bridge_connected_component(
    cells: list[tuple[int, int]],
    min_side_cells: int = 20,
) -> list[list[tuple[int, int]]]:
    """Split a very wide component when it is connected only by a thin bridge.

    A baseline, arrow, or stray outline can join separate objects into one
    connected component.  Drawing that component with one nearest-neighbour
    walk makes the pen alternate between those objects.  Valleys in the
    vertical ink projection are reliable weak-bridge signals at grid scale.
    """
    if len(cells) < min_side_cells * 2:
        return [cells]

    min_row, min_col, max_row, max_col = _bounds(cells)
    height = max_row - min_row + 1
    width = max_col - min_col + 1
    if width < 16 or height < 10:
        return [cells]

    counts = {col: 0 for col in range(min_col, max_col + 1)}
    for _, col in cells:
        counts[col] += 1
    valley_limit = max(3, int(np.ceil(height * 0.30)))
    edge_guard = 4
    valleys: list[tuple[int, int]] = []
    start: int | None = None
    for col in range(min_col, max_col + 2):
        low = col <= max_col and counts[col] <= valley_limit
        if low and start is None:
            start = col
        elif not low and start is not None:
            end = col - 1
            if (
                end - start + 1 >= 2
                and start > min_col + edge_guard
                and end < max_col - edge_guard
            ):
                valleys.append((start, end))
            start = None
    if not valleys:
        return [cells]

    # Prefer the broadest empty corridor.  It is much less likely to be an
    # internal detail of a character than a one-column dip.
    start, end = max(valleys, key=lambda band: (band[1] - band[0], -band[0]))
    cut = (start + end) // 2
    left = [cell for cell in cells if cell[1] <= cut]
    right = [cell for cell in cells if cell[1] > cut]
    if len(left) < min_side_cells or len(right) < min_side_cells:
        return [cells]
    return (
        _split_bridge_connected_component(left, min_side_cells)
        + _split_bridge_connected_component(right, min_side_cells)
    )


def _split_bridge_connected_components(
    components: list[list[tuple[int, int]]],
) -> list[list[tuple[int, int]]]:
    return [
        piece
        for cells in components
        for piece in _split_bridge_connected_component(cells)
    ]


def _boxes_touch(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
    margin: int = 2,
) -> bool:
    """Whether two component boxes belong to the same visual region."""
    a_top, a_left, a_bottom, a_right = first
    b_top, b_left, b_bottom, b_right = second
    return not (
        a_right + margin < b_left
        or b_right + margin < a_left
        or a_bottom + margin < b_top
        or b_bottom + margin < a_top
    )


def _group_adjacent_stroke_groups(
    groups: list[tuple[str, list[tuple[int, int]]]],
) -> list[list[tuple[str, list[tuple[int, int]]]]]:
    """Keep overlapping label parts and outline pieces in one draw region."""
    regions: list[list[tuple[str, list[tuple[int, int]]]]] = []
    boxes: list[tuple[int, int, int, int]] = []
    for group in groups:
        group_box = _bounds(group[1])
        touching = [index for index, box in enumerate(boxes) if _boxes_touch(group_box, box)]
        if not touching:
            regions.append([group])
            boxes.append(group_box)
            continue
        target = touching[0]
        regions[target].append(group)
        top, left, bottom, right = boxes[target]
        boxes[target] = (
            min(top, group_box[0]), min(left, group_box[1]),
            max(bottom, group_box[2]), max(right, group_box[3]),
        )
        # Merge any regions newly bridged by the expanded box.
        for index in reversed(touching[1:]):
            regions[target].extend(regions.pop(index))
            other = boxes.pop(index)
            top, left, bottom, right = boxes[target]
            boxes[target] = (
                min(top, other[0]), min(left, other[1]),
                max(bottom, other[2]), max(right, other[3]),
            )
    return regions


def classify_stroke_groups(
    active: np.ndarray,
) -> list[tuple[str, list[tuple[int, int]]]]:
    """Classify connected ink regions as a main subject, text, or local contour."""
    labels, count = _label_components(active)
    components = [
        _component_cells(labels, label)
        for label in range(1, count + 1)
    ]
    components = [cells for cells in components if cells]
    if not components:
        return []

    # A long ground line may connect a mountain, a character, and a crowd.
    # Split that weak connection before any region ordering is decided.
    components = _split_bridge_connected_components(components)

    # Merge small fragments into the nearest large region to avoid interrupting continuous text drawing
    total_cells = sum(len(c) for c in components)
    merge_threshold = max(3, int(total_cells * 0.005))
    components = _merge_small_components(components, merge_threshold)

    subject_index = max(range(len(components)), key=lambda index: len(components[index]))
    groups: list[tuple[str, list[tuple[int, int]], tuple[int, int, int]]] = []
    for index, cells in enumerate(components):
        min_row, min_col, max_row, max_col = _bounds(cells)
        height = max_row - min_row + 1
        width = max_col - min_col + 1
        density = len(cells) / (height * width)
        if index == subject_index:
            kind, rank = "subject", 0
        elif height >= 2 and width / height >= 2.2 and density >= 0.5:
            kind, rank = "text", 1
        else:
            kind, rank = "contour", 2
        groups.append((kind, cells, (rank, min_row, min_col)))

    groups.sort(key=lambda group: group[2])
    return [(kind, cells) for kind, cells, _ in groups]


def _density_seed(cells: Sequence[tuple[int, int]], radius: int = 2) -> tuple[int, int]:
    """Choose the cell with the densest local neighborhood as the starting point."""
    cell_set = set(cells)
    best = cells[0]
    best_score = -1
    for (r, c) in cells:
        score = sum(
            1
            for dr in range(-radius, radius + 1)
            for dc in range(-radius, radius + 1)
            if (r + dr, c + dc) in cell_set
        )
        if score > best_score:
            best_score = score
            best = (r, c)
    return best


def _gradient_walk(cells: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    """
    Greedy density-guided traversal starts from the densest seed cell.
    At each step select the unvisited neighbor with the highest local density and smallest direction change.
    This follows the ink with minimal backtracking to form continuous strokes.
    When no neighbor is reachable, jump to the nearest globally unvisited cell.
    """
    if not cells:
        return []

    cell_set = set(cells)
    seed = _density_seed(cells)
    visited: set[tuple[int, int]] = {seed}
    path: list[tuple[int, int]] = [seed]
    current = seed
    prev_dir = (0, 0)

    while len(visited) < len(cells):
        neighbors = [
            (r, c)
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if (dr or dc)
            and (r := current[0] + dr, c := current[1] + dc) in cell_set
            and (r, c) not in visited
        ]
        if neighbors:
            def cost(cell: tuple[int, int]) -> tuple:
                # Prefer more neighbors (negative value), smaller direction change, then stable positional order
                local = sum(
                    1
                    for dr in (-1, 0, 1)
                    for dc in (-1, 0, 1)
                    if (cell[0] + dr, cell[1] + dc) in cell_set
                    and (cell[0] + dr, cell[1] + dc) not in visited
                )
                step = (cell[0] - current[0], cell[1] - current[1])
                turn = (step[0] - prev_dir[0]) ** 2 + (step[1] - prev_dir[1]) ** 2
                return (-local, turn, cell[0], cell[1])

            nxt = min(neighbors, key=cost)
        else:
            # Pen lift: jump to the nearest unvisited cell
            unvisited = [cell for cell in cells if cell not in visited]
            nxt = min(
                unvisited,
                key=lambda cell: (
                    (cell[0] - current[0]) ** 2 + (cell[1] - current[1]) ** 2,
                    cell[0],
                    cell[1],
                ),
            )

        prev_dir = (nxt[0] - current[0], nxt[1] - current[1])
        path.append(nxt)
        visited.add(nxt)
        current = nxt

    return path


def _nearest_neighbor_order(
    cells: Sequence[tuple[int, int]], seed: tuple[int, int]
) -> list[tuple[int, int]]:
    """Starting at seed, visit the nearest unvisited cell at every step to form continuous strokes."""
    if not cells:
        return []
    remaining = list(cells)
    ordered: list[tuple[int, int]] = []
    current = seed if seed in remaining else remaining[0]
    while remaining:
        ordered.append(current)
        remaining.remove(current)
        if not remaining:
            break
        current = min(
            remaining,
            key=lambda cell: (cell[0] - ordered[-1][0]) ** 2
            + (cell[1] - ordered[-1][1]) ** 2,
        )
    return ordered


def _text_scan_order(
    cells: Sequence[tuple[int, int]], segment_cols: int = 4
) -> list[tuple[int, int]]:
    """
    Text-specific drawing: scan horizontally in segments to simulate writing.
    Divide cells into column segments of segment_cols width and process segments left to right.
    Within each segment, follow ink continuously using nearest neighbors rather than row-by-row scanning.
    This avoids leaving a segment incomplete and returning to its top later.
    """
    if not cells:
        return []
    if segment_cols < 1:
        segment_cols = 1
    left_col = min(col for _, col in cells)
    # Bucket by starting column // segment_cols; draw leftmost buckets first
    buckets: dict[int, list[tuple[int, int]]] = {}
    for cell in cells:
        bucket_key = (cell[1] - left_col) // segment_cols
        buckets.setdefault(bucket_key, []).append(cell)

    ordered: list[tuple[int, int]] = []
    prev_tail: tuple[int, int] | None = None
    for key in sorted(buckets):
        seg_cells = buckets[key]
        # Start each segment near the previous exit to reduce pen jumps
        if prev_tail is not None:
            seed = min(
                seg_cells,
                key=lambda cell: (cell[0] - prev_tail[0]) ** 2
                + (cell[1] - prev_tail[1]) ** 2,
            )
        else:
            seed = min(seg_cells, key=lambda cell: (cell[0], cell[1]))
        seg_order = _nearest_neighbor_order(seg_cells, seed)
        ordered.extend(seg_order)
        prev_tail = seg_order[-1]
    return ordered


def _order_stream_by_kind(
    kind: str, cells: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    """Select traversal by region type: segmented horizontal scan for text, density-guided for subject/contour."""
    if kind == "text":
        return _text_scan_order(cells)
    return _gradient_walk(cells)


def _chain_region_paths(
    groups: list[tuple[str, list[tuple[int, int]]]],
) -> list[tuple[int, int]]:
    """Finish every component in one visual region before leaving it."""
    paths = [_order_stream_by_kind(kind, cells) for kind, cells in groups]
    remaining = [path for path in paths if path]
    ordered: list[tuple[int, int]] = []
    tail: tuple[int, int] | None = None
    while remaining:
        if tail is None:
            pick_index = 0  # groups retain subject/text/contour priority.
        else:
            pick_index = min(
                range(len(remaining)),
                key=lambda index: min(
                    (remaining[index][0][0] - tail[0]) ** 2
                    + (remaining[index][0][1] - tail[1]) ** 2,
                    (remaining[index][-1][0] - tail[0]) ** 2
                    + (remaining[index][-1][1] - tail[1]) ** 2,
                ),
            )
        path = remaining.pop(pick_index)
        if tail is not None and len(path) > 1:
            head_distance = (path[0][0] - tail[0]) ** 2 + (path[0][1] - tail[1]) ** 2
            end_distance = (path[-1][0] - tail[0]) ** 2 + (path[-1][1] - tail[1]) ** 2
            if end_distance < head_distance:
                path.reverse()
        ordered.extend(path)
        tail = path[-1]
    return ordered


def cluster_ink_streams(active: np.ndarray) -> list[list[tuple[int, int]]]:
    """
    Group ink cells semantically into streams: subject, text, then local contours.
    Choose traversal by type: segmented scan for text, density-guided for others.
    Chain streams by nearest exit-to-entry distance and reverse streams if needed to reduce pen jumps.
    Return the ordered, chained stroke streams.
    """
    if not active.any():
        return []
    groups = classify_stroke_groups(active)
    # A stream is now a complete visual region, not merely one connected
    # component.  Thus a label's border, its characters, and its arrow cannot
    # be interrupted by a different object that happens to be closer.
    regions = _group_adjacent_stroke_groups(groups)
    streams = [_chain_region_paths(region) for region in regions]
    streams = [s for s in streams if s]
    if not streams:
        return []

    # Chain streams starting with the subject, then select the stream whose entrance is closest to the current exit.
    # Reverse the whole stream when needed to bring its start closer to the previous exit.
    ordered: list[list[tuple[int, int]]] = []
    remaining = list(streams)
    tail: tuple[int, int] | None = None
    while remaining:
        if tail is None:
            pick_idx = 0  # classify has already placed the subject first
        else:
            def dist_to_tail(stream: list[tuple[int, int]]) -> int:
                head = stream[0]
                return (head[0] - tail[0]) ** 2 + (head[1] - tail[1]) ** 2
            pick_idx = min(range(len(remaining)), key=lambda i: dist_to_tail(remaining[i]))
        pick = remaining.pop(pick_idx)
        # Reverse if the current tail is closer to the candidate end than its start
        if tail is not None and len(pick) > 1:
            head = pick[0]
            end = pick[-1]
            d_end = (end[0] - tail[0]) ** 2 + (end[1] - tail[1]) ** 2
            d_head = (head[0] - tail[0]) ** 2 + (head[1] - tail[1]) ** 2
            if d_end < d_head:
                pick = pick[::-1]
        ordered.append(pick)
        tail = pick[-1]
    return ordered


def flatten_streams(streams: list[list[tuple[int, int]]]) -> list[tuple[int, int]]:
    return [cell for stream in streams for cell in stream]


# ──────────────────────────────────────────────────────────────
# Pen-tip and hand overlays
# ──────────────────────────────────────────────────────────────
def _load_hand(path: Path, target_h: int) -> tuple[np.ndarray, np.ndarray] | None:
    """
    Read the hand asset and scale proportionally to the target height.
    Prefer alpha masking; fall back to near-white background detection if alpha is absent.
    Return (hand BGR, normalized mask [0..1]), or None on failure.
    """
    if not path.exists():
        return None
    raw = _imread_any(path, cv2.IMREAD_UNCHANGED)
    if raw is None:
        return None

    if raw.ndim == 3 and raw.shape[2] == 4:
        hand = raw[:, :, :3]
        mask = raw[:, :, 3]
    else:
        hand = raw
        gray = cv2.cvtColor(hand, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)

    # Crop to the effective region
    (x0, y0), (x1, y1) = _bounding_box(mask)
    if x1 <= x0 or y1 <= y0:
        return None
    hand = hand[y0:y1 + 1, x0:x1 + 1]
    mask = mask[y0:y1 + 1, x0:x1 + 1]

    scale = target_h / hand.shape[0]
    new_w = max(1, int(round(hand.shape[1] * scale)))
    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    hand = cv2.resize(hand, (new_w, target_h), interpolation=interp)
    mask = cv2.resize(mask, (new_w, target_h), interpolation=interp)
    mask = mask.astype(np.float32) / 255.0

    # Set pixels outside the mask to black for subsequent masked blending
    hand[mask <= 0] = 0
    return hand, mask


def _procedural_tip(target_h: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Fallback pen tip: procedurally draw a marker with barrel gradient, soft rounded tip, and shadow.
    No external image is required; rendering still works when the asset is missing.
    """
    w = max(1, int(target_h * 0.34))
    h = target_h
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    # Drop shadow: soften an offset dark strip beneath the pen
    shadow = np.zeros((h, w), dtype=np.uint8)
    cv2.rectangle(shadow, (3, int(h * 0.06)), (w - 2, int(h * 0.62)), 90, thickness=-1)
    shadow = cv2.GaussianBlur(shadow, (15, 15), 0)
    rgba[:, :, 3] = shadow

    # Pen barrel: vertical gradient from light to dark
    for y in range(h):
        t = y / max(1, h - 1)
        shade = int(220 - 130 * t)
        rgba[y, :, 0:3] = (shade, shade, shade + 10)
    cv2.rectangle(rgba, (4, int(h * 0.04)), (w - 4, int(h * 0.58)), (0, 0, 0), thickness=1)

    # Rounded pen tip, warm ink color
    tip_cy = int(h * 0.70)
    cv2.circle(rgba, (w // 2, tip_cy), max(3, w // 4), (70, 90, 230), thickness=-1)

    # Build the alpha mask from the rounded tip and barrel contour
    body_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.rectangle(body_mask, (3, int(h * 0.04)), (w - 3, tip_cy), 255, thickness=-1)
    cv2.circle(body_mask, (w // 2, tip_cy), max(3, w // 4), 255, thickness=-1)
    body_mask = cv2.GaussianBlur(body_mask, (7, 7), 0)

    hand = rgba[:, :, :3]
    mask = np.maximum(rgba[:, :, 3], body_mask).astype(np.float32) / 255.0
    hand[mask <= 0] = 0
    return hand, mask


class TipOverlay:
    """Alpha-blend the pen/hand onto the canvas with its specified tip anchor aligned to the ink point."""

    def __init__(
        self,
        hand: np.ndarray,
        mask: np.ndarray,
        tip_anchor_x: float = 0.0,
        tip_anchor_y: float = 0.0,
    ) -> None:
        self.hand = hand
        self.mask = mask
        self.h, self.w = hand.shape[:2]
        self.mask_inv = 1.0 - mask
        # Pixel coordinates of the asset pen tip (align the ink point here)
        # Map normalized anchors exactly onto the source image's pixel range.
        self.tip_px = int(round((self.w - 1) * np.clip(tip_anchor_x, 0.0, 1.0)))
        self.tip_py = int(round((self.h - 1) * np.clip(tip_anchor_y, 0.0, 1.0)))

    def stamp(self, canvas: np.ndarray, x: int, y: int) -> np.ndarray:
        """Align the asset tip anchor to canvas coordinates (x, y), the ink-contact point."""
        # Asset top-left = ink point minus tip offset
        anchor_x = x - self.tip_px
        anchor_y = y - self.tip_py
        h_canvas, w_canvas = canvas.shape[:2]

        x0 = max(0, anchor_x)
        y0 = max(0, anchor_y)
        x1 = min(w_canvas, anchor_x + self.w)
        y1 = min(h_canvas, anchor_y + self.h)
        if x1 <= x0 or y1 <= y0:
            return canvas

        sx0 = x0 - anchor_x
        sy0 = y0 - anchor_y
        sx1 = sx0 + (x1 - x0)
        sy1 = sy0 + (y1 - y0)

        region = canvas[y0:y1, x0:x1]
        hand_region = self.hand[sy0:sy1, sx0:sx1]
        mask_region = self.mask[sy0:sy1, sx0:sx1]
        inv_region = self.mask_inv[sy0:sy1, sx0:sx1]

        for c in range(3):
            region[:, :, c] = (
                region[:, :, c] * inv_region + hand_region[:, :, c] * mask_region
            )
        canvas[y0:y1, x0:x1] = region
        return canvas


# ──────────────────────────────────────────────────────────────
# Ink brush
# ──────────────────────────────────────────────────────────────
def _feathered_disk(radius: int) -> np.ndarray:
    """Create a circular mask of radius r with Gaussian-feathered edges and values from 0 to 1."""
    y, x = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    dist = np.sqrt(x * x + y * y).astype(np.float32)
    return np.clip(1.0 - (dist - radius * 0.75) / (radius * 0.25), 0.0, 1.0)


# ──────────────────────────────────────────────────────────────
# Contour-wipe coloring utilities
# ──────────────────────────────────────────────────────────────
def _ease_in_out_sine(t: float | np.ndarray) -> float | np.ndarray:
    """Sine easing: slow at both ends, fast in the middle; accepts a scalar or array and preserves shape."""
    return -(np.cos(np.pi * t) - 1.0) / 2.0


def _build_wipe_wave(width: int) -> np.ndarray:
    """
    Precompute a dual-frequency sine boundary so the reveal frontier undulates like water.
    Return a float32 array of shape (W,), approximately in [-1.35, 1.35].
    """
    wave_px1 = max(24.0, width / 20.0)
    wave_px2 = max(8.0, width / 72.0)
    xs = np.arange(width, dtype=np.float32)
    return np.sin(xs / wave_px1) + 0.35 * np.sin(xs / wave_px2 + 1.7)


# ──────────────────────────────────────────────────────────────
# Skeleton-level stroke tracing (adapted from whiteboard-video-engine preprocess.py)
# Zhang-Suen thinning → straightest 8-neighbor edge tracing → ordered pixel strokes
# ──────────────────────────────────────────────────────────────
_SKEL_NEIGHBORS_8 = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0),           (1, 0),
    (-1, 1),  (0, 1),  (1, 1),
]


def _zhang_suen_skeleton(mask: np.ndarray, max_iterations: int = 160) -> np.ndarray:
    """
    Zhang-Suen two-subiteration thinning reduces a binary foreground mask to a one-pixel skeleton.
    Input: two-dimensional bool/uint8 array, True/1 denotes foreground ink.
    Output: boolean skeleton of the same shape.
    """
    img = np.pad(mask.astype(np.uint8), 1, mode="constant")
    for _ in range(max_iterations):
        changed = False
        for step in (0, 1):
            p2, p3, p4 = img[:-2, 1:-1], img[:-2, 2:], img[1:-1, 2:]
            p5, p6, p7 = img[2:, 2:], img[2:, 1:-1], img[2:, :-2]
            p8, p9 = img[1:-1, :-2], img[:-2, :-2]
            center = img[1:-1, 1:-1]
            neighbors = [p2, p3, p4, p5, p6, p7, p8, p9]
            # Count clockwise 0-to-1 transitions
            transitions = sum(
                (neighbors[i] == 0) & (neighbors[(i + 1) % 8] == 1) for i in range(8)
            )
            count = sum(neighbors)
            if step == 0:
                marker = (
                    (center == 1) & (count >= 2) & (count <= 6)
                    & (transitions == 1)
                    & ((p2 * p4 * p6) == 0) & ((p4 * p6 * p8) == 0)
                )
            else:
                marker = (
                    (center == 1) & (count >= 2) & (count <= 6)
                    & (transitions == 1)
                    & ((p2 * p4 * p8) == 0) & ((p2 * p6 * p8) == 0)
                )
            if np.any(marker):
                center[marker] = 0
                changed = True
        if not changed:
            break
    return img[1:-1, 1:-1].astype(bool)


def _skel_neighbors(skel: np.ndarray, point: tuple[int, int]) -> list[tuple[int, int]]:
    """
    Return valid 8-connected neighbors of a skeleton point.
    Skip a diagonal neighbor when an orthogonal bridge already connects it to the current point.
    This avoids triangular fragments at T/cross intersections while preserving genuine diagonal centerlines.
    """
    x, y = point
    h, w = skel.shape
    result: list[tuple[int, int]] = []
    for dx, dy in _SKEL_NEIGHBORS_8:
        nx, ny = x + dx, y + dy
        if not (0 <= nx < w and 0 <= ny < h and skel[ny, nx]):
            continue
        if dx != 0 and dy != 0 and (skel[y, nx] or skel[ny, x]):
            continue  # Orthogonal bridge exists; skip the redundant diagonal
        result.append((nx, ny))
    return result


def _edge_key(a: tuple[int, int], b: tuple[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
    """Normalize undirected edges so (A,B) and (B,A) map to the same key."""
    return (a, b) if a <= b else (b, a)


def _choose_next(
    prev: tuple[int, int],
    cur: tuple[int, int],
    candidates: list[tuple[int, int]],
    visited_edges: set,
) -> tuple[int, int] | None:
    """
    Continue along the straightest unvisited edge at an intersection.
    Maximize cosine similarity between the current and candidate directions.
    """
    fresh = [p for p in candidates if _edge_key(cur, p) not in visited_edges and p != prev]
    if not fresh:
        return None
    vx, vy = cur[0] - prev[0], cur[1] - prev[1]
    vlen = math.hypot(vx, vy)
    return max(
        fresh,
        key=lambda p: (
            (vx * (p[0] - cur[0]) + vy * (p[1] - cur[1]))
            / (vlen * math.hypot(p[0] - cur[0], p[1] - cur[1]) or 1.0)
        ),
    )


def trace_8connected(skel: np.ndarray, min_points: int = 8) -> list[list[tuple[int, int]]]:
    """
    Trace a one-pixel skeleton into ordered strokes.

    - Starting priority: degree-1 endpoints, degree>2 intersections, then others.
    - At intersections follow the straightest unvisited edge rather than splitting each branch into short strokes.
    - Track visited undirected edges; pixels can recur, but edges cannot.
    - Stop at a dead end with no fresh edge; later starts cover remaining branches.
    - Discard fragments shorter than min_points.

    Return list[list[(x,y)]] with ordered pixel coordinates along each stroke.
    """
    ys, xs = np.nonzero(skel)
    points = [(int(x), int(y)) for x, y in zip(xs, ys)]
    if not points:
        return []
    degrees = {p: len(_skel_neighbors(skel, p)) for p in points}
    starts = (
        [p for p in points if degrees[p] == 1]
        + [p for p in points if degrees[p] > 2]
        + points
    )
    visited_edges: set = set()
    strokes: list[list[tuple[int, int]]] = []
    for start in starts:
        for nb in _skel_neighbors(skel, start):
            edge = _edge_key(start, nb)
            if edge in visited_edges:
                continue
            path = [start]
            prev, cur = start, nb
            visited_edges.add(edge)
            while True:
                path.append(cur)
                next_pt = _choose_next(prev, cur, _skel_neighbors(skel, cur), visited_edges)
                if next_pt is None:
                    break
                visited_edges.add(_edge_key(cur, next_pt))
                prev, cur = cur, next_pt
            if len(path) >= min_points:
                strokes.append(path)
    return strokes


# Skeleton post-processing: resampling, smoothing, ordering
def _stroke_cumulative_length(points: list[tuple[float, float]]) -> list[float]:
    """Cumulative arc length at each point: [0, d01, d012, ...]."""
    cum = [0.0]
    for a, b in zip(points, points[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return cum


def _resample_stroke_points(
    points: list[tuple[float, float]], spacing: float
) -> list[tuple[float, float]]:
    """Resample at equal arc-length intervals of spacing to reduce pixel jaggies."""
    if len(points) < 2:
        return list(points)
    cum = _stroke_cumulative_length(points)
    total = cum[-1]
    if total < spacing:
        return [points[0], points[-1]]
    n = max(2, int(round(total / spacing)))
    result: list[tuple[float, float]] = []
    for i in range(n + 1):
        target = total * i / n
        # Binary search for position
        lo, hi = 0, len(cum) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if cum[mid] < target:
                lo = mid + 1
            else:
                hi = mid
        if lo == 0:
            result.append(points[0])
            continue
        seg_start = cum[lo - 1]
        seg_len = cum[lo] - seg_start
        t = (target - seg_start) / seg_len if seg_len > 0 else 0.0
        ax, ay = points[lo - 1]
        bx, by = points[lo]
        result.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    return result


def _chaikin_smooth(
    points: list[tuple[float, float]], iterations: int = 1
) -> list[tuple[float, float]]:
    """Chaikin corner-cutting: replace each segment with points at 0.25/0.75, preserving endpoints."""
    pts = list(points)
    for _ in range(iterations):
        if len(pts) < 3:
            break
        smoothed = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            smoothed.append((a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25))
            smoothed.append((a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75))
        smoothed.append(pts[-1])
        pts = smoothed
    return pts


def _order_skeleton_strokes(strokes: list[list[tuple[float, float]]]) -> list[list[tuple[float, float]]]:
    """
    Order strokes top to bottom, then left to right, preferring longer strokes.
    Simplified order_strokes uses lexicographic bounding-box top-left and negative length.
    """
    def sort_key(s):
        if not s:
            return (0, 0, 0, 0)
        xs = [p[0] for p in s]
        ys = [p[1] for p in s]
        length = _stroke_cumulative_length(s)[-1]
        return (min(ys) // 12, min(xs), min(ys), -length)
    return sorted(strokes, key=sort_key)


# ──────────────────────────────────────────────────────────────
# Duration and stage splitting
# ──────────────────────────────────────────────────────────────
@dataclass
class PhasePlan:
    ink_frames: int
    color_frames: int
    gaze_frames: int
    ratio_label: str


def plan_phases(total_ms: int, cfg: Config) -> PhasePlan:
    """
    Split total duration into ink, color, and finished-image hold.
    Reserve baseline hold seconds, then distribute the remaining time by ink/color weights.
    Assign integer-division remainder to the hold to avoid lost precision.
    """
    weight_sum = cfg.ink_weight + cfg.color_weight
    gaze_ms = int(cfg.gaze_seconds * 1000)
    anim_ms = total_ms - gaze_ms
    remainder = anim_ms % weight_sum
    if remainder:
        anim_ms -= remainder
        gaze_ms += remainder

    ink_frames = round(anim_ms * cfg.ink_weight / weight_sum * cfg.fps / 1000)
    color_frames = round(anim_ms * cfg.color_weight / weight_sum * cfg.fps / 1000)
    gaze_frames = round(gaze_ms * cfg.fps / 1000)
    if ink_frames <= 0 and color_frames <= 0:
        ink_frames = color_frames = 0
    return PhasePlan(ink_frames, color_frames, gaze_frames, f"{cfg.ink_weight}:{cfg.color_weight}")


# ──────────────────────────────────────────────────────────────
# Renderer implementation
# ──────────────────────────────────────────────────────────────
class StreamBoardRenderer:
    """Keep all state for one render on a single instance."""

    def __init__(
        self,
        image_bgr: np.ndarray,
        cfg: Config,
        hand_png: Path | None,
        bare_tip: bool,
    ) -> None:
        self.cfg = cfg
        self.canvas_bgr = _hex_to_bgr(cfg.canvas_hex)

        # Limit long edge to cap and align to an even multiple of grid_edge for encoding
        h0, w0 = image_bgr.shape[:2]
        scale = cfg.cap_long_edge / max(h0, w0)
        w = int(round(w0 * scale))
        h = int(round(h0 * scale))
        align = cfg.grid_edge if cfg.grid_edge % 2 == 0 else cfg.grid_edge * 2
        w = (w // align) * align
        h = (h // align) * align
        self.out_w = max(align, w)
        self.out_h = max(align, h)

        self.color_img = cv2.resize(image_bgr, (self.out_w, self.out_h), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(self.color_img, cv2.COLOR_BGR2GRAY)
        self.thresh_map = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 10
        )
        self.active = _active_mask(self.thresh_map, cfg.grid_edge, cfg.ink_threshold)
        self.grid_blocks = _to_grid_blocks(self.thresh_map, cfg.grid_edge)
        self.ink_pixels = self.thresh_map < cfg.ink_threshold
        self.ink_paint = np.repeat(self.thresh_map[:, :, None], 3, axis=2).astype(np.float32)

        # Match source background to canvas; affects only color_img, not ink_pixels or ink_paint.
        # This keeps coloring and finished-hold backgrounds consistent with the ink stage.
        # Run after ink_pixels is calculated so line-art quality is unaffected.
        if cfg.match_bg:
            self._match_original_background()

        # Grid-space clustering (needed by grid paths and the contour-wipe resistance field)
        self.ink_streams = cluster_ink_streams(self.active)

        # Choose grid cell-center interpolation or skeleton tracing according to ink_path_mode
        if cfg.ink_path_mode == "skeleton":
            self.skeleton_strokes = self._build_skeleton_path()
            if self.skeleton_strokes:
                self.stroke_path = [pt for stroke in self.skeleton_strokes for pt in stroke]
            else:
                # No skeleton strokes: actually fall back to cell-center paths, not an empty path
                self.stroke_path = flatten_streams(self.ink_streams)
        else:
            self.skeleton_strokes = []
            self.stroke_path = flatten_streams(self.ink_streams)

        # Floating-point canvas buffer for accumulating blended brush marks
        self.drawn = np.zeros((self.out_h, self.out_w, 3), dtype=np.float32)
        self.drawn[...] = self.canvas_bgr.astype(np.float32)

        # Pen overlay
        self.tip: TipOverlay | None = None
        if not bare_tip:
            hand_data = _load_hand(hand_png, cfg.target_hand_height) if hand_png else None
            tip_anchor_x = cfg.tip_anchor_x
            tip_anchor_y = cfg.tip_anchor_y
            if hand_data is None:
                hand_data = _procedural_tip(cfg.target_hand_height)
                tip_anchor_x = 0.5
                tip_anchor_y = 0.70
            self.tip = TipOverlay(
                hand_data[0], hand_data[1],
                tip_anchor_x=tip_anchor_x,
                tip_anchor_y=tip_anchor_y,
            )

    # Match source background to canvas (color_img only; preserve ink)
    def _match_original_background(self) -> None:
        """
        Sample the source corners as background reference and replace pixels below the difference threshold with canvas_hex.
        Keep coloring and finished-hold backgrounds consistent with ink to avoid sudden color changes.
        Preserve original colors where content differs significantly from the background.
        """
        img = self.color_img
        h, w = img.shape[:2]
        margin = max(3, min(h, w) // 50)
        samples = [
            img[:margin, :margin], img[:margin, -margin:],
            img[-margin:, :margin], img[-margin:, -margin:],
        ]
        bg_color = np.median(np.concatenate([s.reshape(-1, 3) for s in samples]), axis=0)
        diff = np.abs(img.astype(np.int16) - bg_color.astype(np.int16)).sum(axis=2)
        bg_mask = diff < self.cfg.match_bg_threshold
        img[bg_mask] = self.canvas_bgr

    # Stroke center points in pixel coordinates
    def _cell_center(self, cell: tuple[int, int]) -> tuple[int, int]:
        r, c = cell
        e = self.cfg.grid_edge
        return (c * e + e // 2, r * e + e // 2)  # (x, y)

    # Skeleton stroke paths: Zhang-Suen thinning plus straightest 8-neighbor edge tracing
    def _build_skeleton_path(self) -> list[list[tuple[int, int]]]:
        """
        Generate ordered pixel-level strokes by skeleton tracing instead of interpolated grid centers.
        The pen follows the real skeleton and more closely matches source lines.
        At intersections follow the straightest edge to avoid triangular fragments.
        """
        cfg = self.cfg
        skel = _zhang_suen_skeleton(self.ink_pixels, max_iterations=160)
        raw_strokes = trace_8connected(skel, min_points=cfg.skeleton_min_points)
        if not raw_strokes:
            print("  [warn] No skeleton strokes; falling back to cell-center paths")
            return []

        spacing = cfg.skeleton_resample_spacing
        processed: list[list[tuple[int, int]]] = []
        for stroke in raw_strokes:
            pts = [(float(x), float(y)) for x, y in stroke]
            pts = _resample_stroke_points(pts, spacing)
            pts = _chaikin_smooth(pts, iterations=1)
            pts = _resample_stroke_points(pts, spacing)
            if len(pts) >= 2 and _stroke_cumulative_length(pts)[-1] > 2.0:
                processed.append([(int(round(x)), int(round(y))) for x, y in pts])

        processed = _order_skeleton_strokes(processed)
        total_pts = sum(len(s) for s in processed)
        print(f"  Skeleton tracing: {len(processed)} strokes, {total_pts} samples")
        return processed

    # Lazy contour-wipe resistance field, reused throughout coloring
    def _build_resistance_field(self) -> np.ndarray:
        """
        Build a resistance field from ink: resistance is about 1 at contours and decays exponentially downward by decay.
        High resistance subtracts pixels from the reveal frontier, briefly holding at contours before crossing.

        Resistance is static and independent of coloring progress, so cache it once in self._resistance.
        """
        if getattr(self, "_resistance", None) is not None:
            return self._resistance

        h, w = self.out_h, self.out_w
        cfg = self.cfg

        # 1) Binary ink image (uint8 0/255)
        ink_u8 = (self.ink_pixels.astype(np.uint8)) * 255

        # 2) Dilate with a circular kernel to thicken contours into barriers
        spread = int(np.clip(min(w, h) // 64, 3, 17))
        if spread % 2 == 0:  # Kernel size must be positive and odd
            spread = max(3, spread - 1)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (spread, spread))
        dilated = cv2.dilate(ink_u8, kernel, iterations=1)

        # 3) Gaussian blur converts hard edges to a gradient (positive odd kernel)
        blur_r = max(1, int(round(min(w, h) / 220.0)))
        if blur_r % 2 == 0:
            blur_r += 1
        resistance = cv2.GaussianBlur(dilated, (blur_r, blur_r), 0).astype(np.float32)

        # 4) Normalize to [0,1]
        peak = float(resistance.max())
        if peak > 1e-6:
            resistance /= peak
        else:
            # No ink (white image): resistance is zero, so contour-wipe becomes a straight scan
            resistance = np.zeros((h, w), dtype=np.float32)

        # 5) Causal downward row decay: contours cast an exponentially decaying shadow
        decay = cfg.wipe_decay
        for row in range(1, h):
            resistance[row] = np.maximum(resistance[row], resistance[row - 1] * decay)

        self._resistance = resistance
        return resistance

    # Stamp ink at each point: threshold image for ink stage, original color for coloring
    def _reveal_ink_segment(
        self, start: tuple[int, int], end: tuple[int, int]
    ) -> None:
        """Reveal only the original line-art pixels touched by one pen movement."""
        segment = np.zeros((self.out_h, self.out_w), dtype=np.uint8)
        thickness = max(1, self.cfg.ink_reveal_radius * 2 + 1)
        cv2.line(segment, start, end, 255, thickness=thickness, lineType=cv2.LINE_AA)
        revealed = (segment > 0) & self.ink_pixels
        self.drawn[revealed] = self.ink_paint[revealed]

    def _ink_stamp(self, cell: tuple[int, int]) -> None:
        r, c = cell
        e = self.cfg.grid_edge
        block = self.grid_blocks[r, c]
        ink_region = block < self.cfg.ink_threshold
        # Threshold image is single-channel; replicate to the three-channel canvas
        paint = np.repeat(block[:, :, None], 3, axis=2)
        target = self.drawn[r * e:r * e + e, c * e:c * e + e]
        target[ink_region] = paint[ink_region]

    def _color_stamp(self, px: int, py: int, disk: np.ndarray) -> None:
        radius = self.cfg.brush_radius
        h, w = self.out_h, self.out_w
        y0, y1 = max(0, py - radius), min(h, py + radius + 1)
        x0, x1 = max(0, px - radius), min(w, px + radius + 1)
        if y1 <= y0 or x1 <= x0:
            return
        by0, by1 = y0 - (py - radius), disk.shape[0] - ((py + radius + 1) - y1)
        bx0, bx1 = x0 - (px - radius), disk.shape[1] - ((px + radius + 1) - x1)
        m = disk[by0:by1, bx0:bx1]
        inv = 1.0 - m
        target = self.drawn[y0:y1, x0:x1]
        source = self.color_img[y0:y1, x0:x1].astype(np.float32)
        for ch in range(3):
            target[:, :, ch] = target[:, :, ch] * inv + source[:, :, ch] * m

    # Write current canvas snapshot with pen for the specified frames
    def _snapshot_with_tip(self, px: int, py: int) -> np.ndarray:
        snap = self.drawn.astype(np.uint8)  # astype returns a new array; no extra copy needed
        if self.tip is not None:
            self.tip.stamp(snap, px, py)
        return snap

    def _build_stroke_samples(
        self, path: list[tuple[int, int]]
    ) -> tuple[list[tuple[int, int]], set[int], list[int]]:
        """
        Interpolate the stroke polyline into a continuous sequence of pixel pen positions.
        Sample uniformly every sample_step pixels between neighboring cell centers for smooth motion.

        Return (samples, pen_lifts, sample_cell_index):
          samples: list of pen-tip pixel coordinates.
          pen_lifts: sample indices requiring a pen lift between nonadjacent cells.
          sample_cell_index: index in path of the cell belonging to each sample,
                              used to synchronize ink-reveal progress precisely with pen position.
        """
        samples: list[tuple[int, int]] = []
        pen_lifts: set[int] = set()
        sample_cell_index: list[int] = []
        for idx, cell in enumerate(path):
            cx, cy = self._cell_center(cell)
            if idx == 0:
                samples.append((cx, cy))
                sample_cell_index.append(idx)
                continue
            prev_cell = path[idx - 1]
            prev = self._cell_center(prev_cell)
            cell_distance = math.hypot(cell[0] - prev_cell[0], cell[1] - prev_cell[1])
            if cell_distance > math.sqrt(2):
                pen_lifts.add(len(samples))
                samples.append((cx, cy))
                sample_cell_index.append(idx)
                continue
            steps = max(
                1, int(math.hypot(cx - prev[0], cy - prev[1]) / self.cfg.sample_step)
            )
            for s in range(1, steps + 1):
                samples.append(
                    (int(prev[0] + (cx - prev[0]) * s / steps),
                     int(prev[1] + (cy - prev[1]) * s / steps))
                )
                sample_cell_index.append(idx)
        return samples, pen_lifts, sample_cell_index

    def _frame_progress_indices(self, n_steps: int, target_frames: int) -> list[int]:
        """
        Given n_steps pen positions and target_frames output frames,
        return the position index for each target frame using uniform mapping over the full trajectory.
        target_frames <= n_steps downsamples; larger values repeat samples.
        If target_frames <= 0 (for example total duration consumed by the hold), return no frames.
        """
        if n_steps == 0 or target_frames <= 0:
            return []
        if target_frames == 1:
            return [n_steps - 1]
        return [
            round(f * (n_steps - 1) / (target_frames - 1))
            for f in range(target_frames)
        ]

    def _pause_frame_indices(
        self, target_frames: int, n_cells: int
    ) -> set[int]:
        """
        Adaptive pauses choose a fraction by density and distribute paused frames evenly along the timeline.
        Return indices of frames that must repeat the previous frame's progress.

        The density measure is frames_per_cell = target_frames / n_cells.
        Many more frames than cells means ample time: add pauses to simulate natural pen changes.
        Few frames per cell means dense content and tight timing: omit pauses.

        pause_mode overrides the tier: "off", fixed "light"/"heavy", or automatic "auto".
        """
        mode = self.cfg.pause_mode
        if mode == "off" or target_frames < 8 or n_cells <= 0:
            return set()

        if mode == "light":
            ratio = self.cfg.pause_ratio_light
        elif mode == "heavy":
            ratio = self.cfg.pause_ratio_heavy
        else:  # auto: choose pause tier by frames per cell
            fpc = target_frames / n_cells
            if fpc >= self.cfg.pause_heavy_fpc:
                ratio = self.cfg.pause_ratio_heavy
            elif fpc >= self.cfg.pause_light_fpc:
                ratio = self.cfg.pause_ratio_light
            else:
                return set()  # Dense content: fast pace, no pauses

        # Clamp pause count to at least zero and at most target_frames-2 to avoid first/last-frame pauses
        pause_count = min(
            max(0, int(round(target_frames * ratio))),
            max(0, target_frames - 2),
        )
        if pause_count <= 0:
            return set()

        # Divide target_frames into pause_count+1 equal intervals and pause at interior boundaries
        # Exclude endpoints to preserve uninterrupted beginning and ending
        return {
            max(1, min(target_frames - 2,
                       round((idx + 1) * target_frames / (pause_count + 1))))
            for idx in range(pause_count)
        }

    # Ink stage: trace stroke_path with pen motion synchronized to ink reveal
    def lay_down_ink(self, writer: cv2.VideoWriter, target_frames: int) -> None:
        """Dispatch the ink stage to skeleton tracing or grid-cell paths according to ink_path_mode."""
        if self.cfg.ink_path_mode == "skeleton" and self.skeleton_strokes:
            return self._lay_down_ink_skeleton(writer, target_frames)
        return self._lay_down_ink_grid(writer, target_frames)

    # Grid mode: reveal ink along interpolated cell-center paths (original method)
    def _lay_down_ink_grid(self, writer: cv2.VideoWriter, target_frames: int) -> None:
        path = self.stroke_path
        n = len(path)
        if n == 0:
            print("  No ink; skipping ink stage")
            for _ in range(target_frames):
                writer.write(self._snapshot_with_tip(self.out_w // 2, self.out_h // 2))
            return

        samples, pen_lifts, sample_cell_index = self._build_stroke_samples(path)
        sample_idx_for_frame = self._frame_progress_indices(len(samples), target_frames)

        # Adaptive pauses select frozen frames based on density; pen and ink reveal stop.
        # This simulates natural pen changes and breathing.
        pause_frames = self._pause_frame_indices(target_frames, n)
        if pause_frames:
            print(f"  Adaptive pauses: {len(pause_frames)} frozen frames (mode={self.cfg.pause_mode})")

        written = 0
        cells_revealed = 0  # Fully revealed cell count, incremented in step with pen progress
        last_sample_idx: int | None = None
        for fi, si in enumerate(sample_idx_for_frame):
            # Pause frame: reuse previous pen position and progress; write a snapshot without revealing ink
            if fi in pause_frames and last_sample_idx is not None:
                sx, sy = samples[last_sample_idx]
                writer.write(self._snapshot_with_tip(sx, sy))
                written += 1
                if (fi + 1) % max(1, target_frames // 10) == 0:
                    print(f"  Ink progress: {int((fi + 1) / target_frames * 100)}%")
                continue

            # Reveal along the pen path to preserve flowing strokes
            if last_sample_idx is None:
                self._reveal_ink_segment(samples[si], samples[si])
            else:
                for sample_idx in range(last_sample_idx + 1, si + 1):
                    if sample_idx in pen_lifts:
                        continue
                    self._reveal_ink_segment(
                        samples[sample_idx - 1], samples[sample_idx]
                    )

            # Reveal full cells only through the current pen cell to synchronize drawing and preserve text.
            # sample_cell_index[si] identifies the current frame's pen cell; reveal through that cell.
            target_cell = sample_cell_index[si]
            while cells_revealed <= target_cell and cells_revealed < n:
                self._ink_stamp(path[cells_revealed])
                cells_revealed += 1

            sx, sy = samples[si]
            writer.write(self._snapshot_with_tip(sx, sy))
            written += 1
            last_sample_idx = si
            if (fi + 1) % max(1, target_frames // 10) == 0:
                print(f"  Ink progress: {int((fi + 1) / target_frames * 100)}%")

        # Finalize: reveal all grid ink and fill remaining frames
        while cells_revealed < n:
            self._ink_stamp(path[cells_revealed])
            cells_revealed += 1
        last = samples[-1]
        while written < target_frames:
            writer.write(self._snapshot_with_tip(*last))
            written += 1
        print(f"  Ink complete: {n} cells, {written} frames")

    # Skeleton mode: reveal ink along the actual skeleton pixel path
    def _lay_down_ink_skeleton(self, writer: cv2.VideoWriter, target_frames: int) -> None:
        """
        In skeleton mode, slide along skeleton pixels and reveal source ink using _reveal_ink_segment.
        Do not reveal full blocks (_ink_stamp); skeleton coordinates are already pixel-accurate.
        Mark pen_lifts between strokes and skip interpolation across them.
        """
        strokes = self.skeleton_strokes
        if not strokes:
            return self._lay_down_ink_grid(writer, target_frames)

        # Flatten strokes into sampled positions and mark pen lifts between strokes
        samples: list[tuple[int, int]] = []
        pen_lifts: set[int] = set()
        for si, stroke in enumerate(strokes):
            if si > 0:
                pen_lifts.add(len(samples))  # Pen lift between strokes
            samples.extend(stroke)

        n = len(samples)
        if n == 0:
            print("  No skeleton strokes; skipping ink stage")
            for _ in range(target_frames):
                writer.write(self._snapshot_with_tip(self.out_w // 2, self.out_h // 2))
            return

        sample_idx_for_frame = self._frame_progress_indices(n, target_frames)

        # Adaptive pauses use stroke count instead of cell count for density
        pause_frames = self._pause_frame_indices(target_frames, len(strokes))
        if pause_frames:
            print(f"  Adaptive pauses: {len(pause_frames)} frozen frames (mode={self.cfg.pause_mode})")

        written = 0
        last_sample_idx: int | None = None
        report_step = max(1, target_frames // 10)
        for fi, si in enumerate(sample_idx_for_frame):
            # Pause frame: freeze the pen
            if fi in pause_frames and last_sample_idx is not None:
                sx, sy = samples[last_sample_idx]
                writer.write(self._snapshot_with_tip(sx, sy))
                written += 1
                if (fi + 1) % report_step == 0:
                    print(f"  Ink progress: {int((fi + 1) / target_frames * 100)}%")
                continue

            # Reveal original ink along skeleton segments between previous and current samples
            if last_sample_idx is None:
                self._reveal_ink_segment(samples[si], samples[si])
            else:
                for idx in range(last_sample_idx + 1, si + 1):
                    if idx in pen_lifts:
                        continue
                    self._reveal_ink_segment(samples[idx - 1], samples[idx])

            sx, sy = samples[si]
            writer.write(self._snapshot_with_tip(sx, sy))
            written += 1
            last_sample_idx = si
            if (fi + 1) % report_step == 0:
                print(f"  Ink progress: {int((fi + 1) / target_frames * 100)}%")

        # Finalize by filling remaining frames
        last = samples[-1]
        while written < target_frames:
            writer.write(self._snapshot_with_tip(*last))
            written += 1
        print(f"  Ink complete (skeleton): {n} samples, {written} frames")

    # Coloring-stage entry: dispatch by color_fill
    def wash_color(self, writer: cv2.VideoWriter, target_frames: int) -> None:
        if self.cfg.color_fill == "contour-wipe":
            return self.wash_color_contour(writer, target_frames)
        return self.wash_color_brush(writer, target_frames)

    # Brush: paint original color along strokes using a circular brush
    def wash_color_brush(self, writer: cv2.VideoWriter, target_frames: int) -> None:
        path = self.stroke_path
        n = len(path)
        disk = _feathered_disk(self.cfg.brush_radius)
        if n == 0:
            print("  No ink; skipping coloring stage")
            gaze = self.color_img
            for _ in range(target_frames):
                writer.write(gaze)
            return

        centers = [self._cell_center(cell) for cell in path]
        cell_idx_for_frame = self._frame_progress_indices(n, target_frames)

        written = 0
        last_cell_idx: int | None = None
        for fi, ci in enumerate(cell_idx_for_frame):
            # Color according to frame progress: paint from previous cell to current cell.
            # Include intermediate cells skipped by downsampling to preserve continuous color.
            if last_cell_idx is None:
                self._color_stamp(*centers[ci], disk)
            else:
                for cell_idx in range(last_cell_idx + 1, ci + 1):
                    self._color_stamp(*centers[cell_idx], disk)

            cx, cy = centers[ci]
            writer.write(self._snapshot_with_tip(cx, cy))
            written += 1
            last_cell_idx = ci
            if (fi + 1) % max(1, target_frames // 10) == 0:
                print(f"  Color progress: {int((fi + 1) / target_frames * 100)}%")

        # Finalize remaining color
        last = centers[-1]
        while written < target_frames:
            writer.write(self._snapshot_with_tip(*last))
            written += 1
        print(f"  Color complete: {n} cells, {written} frames")

    # Contour-wipe: contour-aware top-to-bottom coloring
    def wash_color_contour(self, writer: cv2.VideoWriter, target_frames: int) -> None:
        """
        Instead of brushing along strokes, sweep a global color-reveal frontier from top to bottom.
        Contours initially hold the frontier back (resistance about 1 reduces it by delay_px), then it crosses as resistance decays.
        This makes color appear to spread along lines; the pen sweeps horizontally to simulate coloring.
        """
        cfg = self.cfg
        h, w = self.out_h, self.out_w

        if target_frames <= 0:
            print("  No color frames; skipping contour-wipe stage")
            return

        # Precompute resistance field, wave boundary, delay pixels, and row-coordinate grid
        resistance = self._build_resistance_field()
        wave = _build_wipe_wave(w)
        delay_px = int(np.clip(h * cfg.wipe_delay_ratio, 12, 52))
        blocks = max(1, cfg.wipe_blocks)
        ys = np.arange(h, dtype=np.float32)[:, None]   # (H,1), reused each frame

        # Continue from the completed line-art state, as brush mode does after lay_down_ink.
        # color_img is the reveal target
        color_src = self.color_img.astype(np.float32)

        print(f"  contour-wipe: {w}x{h}, delay_px={delay_px}, passes={blocks}")

        written = 0
        # Reveal frontier sweeps from -delay_px to h+delay_px for full coverage
        sweep = h + 2 * delay_px
        report_step = max(1, target_frames // 10)

        for fi in range(target_frames):
            # Global progress with sine easing: 0 to 1
            if target_frames == 1:
                progress = 1.0
            else:
                progress = fi / (target_frames - 1)
            lead = _ease_in_out_sine(progress) * sweep - delay_px

            # Reveal mask: y <= lead + wave[x] - resistance[y,x]*delay_px
            threshold = lead + wave[None, :] - resistance * delay_px  # (H,W)
            reveal = ys <= threshold                        # (H,W) bool

            # Reveal source colors into the drawn buffer
            self.drawn[reveal] = color_src[reveal]

            # Sweep pen horizontally back and forth; reverse odd passes
            lane = (fi / blocks * 2.0) % 1.0               # Normalized progress of one pass, 0..1
            lane = _ease_in_out_sine(lane)
            forward = (int(fi // blocks) % 2 == 0)         # Even passes forward, odd passes backward
            cursor_x = int(lane * w) if forward else int((1.0 - lane) * w)
            cursor_x = max(0, min(w - 1, cursor_x))

            # Cursor y is the lowest revealed row in the current column
            col_revealed = np.where(reveal[:, cursor_x])[0]
            cursor_y = int(col_revealed[-1]) if col_revealed.size > 0 else 0

            writer.write(self._snapshot_with_tip(cursor_x, cursor_y))
            written += 1
            if (fi + 1) % report_step == 0:
                print(f"  Color progress (contour-wipe): {int((fi + 1) / target_frames * 100)}%")

        # Finalize full reveal; final lead is about h+delay_px, theoretically covering all pixels
        full_reveal = np.ones((h, w), dtype=bool)
        self.drawn[full_reveal] = color_src[full_reveal]
        last = self._snapshot_with_tip(w // 2, h - 1)
        while written < target_frames:
            writer.write(last)
            written += 1
        print(f"  contour-wipe complete: {written} frames")

    def render_to(self, raw_path: Path, total_ms: int) -> Path:
        cfg = self.cfg
        plan = plan_phases(total_ms, cfg)
        ink_cells = len(self.stroke_path)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(raw_path), fourcc, cfg.fps, (self.out_w, self.out_h))

        print(f"  Ink streams: {len(self.ink_streams)}, ink cells: {ink_cells}")
        print(
            f"  Duration: {total_ms}ms -> ink {plan.ink_frames}f / "
            f"color {plan.color_frames}f / hold {plan.gaze_frames}f (weights {plan.ratio_label})"
        )

        started = time.time()
        self.lay_down_ink(writer, plan.ink_frames)
        self.wash_color(writer, plan.color_frames)
        # Finished hold: complete source image
        gaze_img = self.color_img
        for _ in range(plan.gaze_frames):
            writer.write(gaze_img)
        writer.release()
        print(f"  Render time: {time.time() - started:.1f}s")
        return raw_path


# ──────────────────────────────────────────────────────────────
# Transcoding: system ffmpeg first, PyAV second, retain mp4v if neither exists
# ──────────────────────────────────────────────────────────────
def transcode_h264(src: Path, dst: Path) -> Path:
    """
    Transcode raw mp4v video to H.264 (yuv420p) for better player compatibility.

    Priority:
      1. System ffmpeg subprocess (best compression efficiency and smallest files, CRF=20).
      2. PyAV (pip-installed without system ffmpeg; less efficient, use CRF=28).
      3. If neither is available, preserve raw mp4v and emit a warning.
    """
    # Route 1: system ffmpeg (recommended, smallest files)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is not None:
        cmd = [
            ffmpeg, "-y", "-loglevel", "error",
            "-i", str(src),
            "-c:v", "libx264",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            str(dst),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            src.unlink(missing_ok=True)
            print(f"  H.264 transcoding complete (ffmpeg): {dst}")
            return dst
        print(f"  [warn] ffmpeg transcoding failed: {res.stderr.strip()}")

    # Route 2: PyAV (pip-installable fallback)
    try:
        return _transcode_with_pyav(src, dst)
    except ImportError:
        pass
    except Exception as e:
        print(f"  [warn] PyAV transcoding failed: {e}")

    # Route 3: neither available; retain mp4v
    print(f"  [warn] Neither ffmpeg nor PyAV found; retaining original mp4v: {src}")
    print("         Install either for H.264: pip install av, or install system ffmpeg")
    return src


def _transcode_with_pyav(src: Path, dst: Path) -> Path:
    """
    Transcode to H.264 in Python using PyAV; raise ImportError if PyAV is missing.
    Bundled PyAV libx264 can produce larger files than system ffmpeg at equal CRF.
    Use CRF=28 to balance size and quality.
    """
    import av
    input_container = av.open(str(src), mode="r")
    in_stream = input_container.streams.video[0]
    width = in_stream.codec_context.width
    height = in_stream.codec_context.height
    fps = in_stream.average_rate

    output_container = av.open(str(dst), mode="w")
    out_stream = output_container.add_stream("h264", rate=fps)
    out_stream.width = width
    out_stream.height = height
    out_stream.pix_fmt = "yuv420p"
    out_stream.options = {"crf": "28", "preset": "medium"}

    for frame in input_container.decode(video=0):
        packet = out_stream.encode(frame)
        if packet:
            output_container.mux(packet)
    # flush
    packet = out_stream.encode(None)
    if packet:
        output_container.mux(packet)

    output_container.close()
    input_container.close()
    src.unlink(missing_ok=True)
    print(f"  H.264 transcoding complete (PyAV): {dst}")
    return dst


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────
def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Render an image as a stream-stroke whiteboard animation video"
    )
    p.add_argument("image", help="Input image path (PNG/JPG/JPEG/BMP/TIFF)")
    p.add_argument("--out-dir", default="./out", help="Output directory (default: ./out)")
    p.add_argument("--total-ms", type=int, default=10000, help="Total video duration in milliseconds (default: 10000)")
    p.add_argument("--bare-tip", action="store_true", help="Do not overlay a pen tip or hand")
    p.add_argument(
        "--pen-image", default=str(DEFAULT_HAND_PNG),
        help="Custom pen/hand asset path (default: bundled drawing-hand.png)",
    )
    p.add_argument("--fps", type=int, default=None, help="Override default frame rate")
    p.add_argument("--grid-edge", type=int, default=None, help="Override default grid-cell edge length")
    p.add_argument("--brush-radius", type=int, default=None, help="Override default brush radius")
    p.add_argument(
        "--color-fill", default="contour-wipe", choices=["brush", "contour-wipe"],
        help="Coloring style: contour-wipe (contour-aware top-down scan, default); brush follows strokes",
    )
    p.add_argument(
        "--wipe-decay", type=float, default=None,
        help="contour-wipe: downward resistance decay per row (default 0.86; lower crosses contours faster)",
    )
    p.add_argument(
        "--wipe-delay-ratio", type=float, default=None,
        help="contour-wipe: frontier delay ratio times height (default 0.04; larger holds at contours longer)",
    )
    p.add_argument(
        "--wipe-blocks", type=int, default=None,
        help="contour-wipe: number of horizontal pen sweeps (default 18)",
    )
    p.add_argument(
        "--pause", default="heavy", choices=["auto", "off", "light", "heavy"],
        help="Ink-stage pause rhythm: heavy (default); auto by density; off; light",
    )
    p.add_argument(
        "--ink-path", default="grid", choices=["grid", "skeleton"],
        help="Ink path: grid (interpolated cell centers, default); skeleton (pixel-level tracing, closer to lines)",
    )
    return p.parse_args(argv)


def _build_cfg(args: argparse.Namespace) -> Config:
    kw: dict = {}
    if args.fps is not None:
        kw["fps"] = args.fps
    if args.grid_edge is not None:
        kw["grid_edge"] = args.grid_edge
    if args.brush_radius is not None:
        kw["brush_radius"] = args.brush_radius
    if args.color_fill is not None:
        kw["color_fill"] = args.color_fill
    if args.wipe_decay is not None:
        kw["wipe_decay"] = args.wipe_decay
    if args.wipe_delay_ratio is not None:
        kw["wipe_delay_ratio"] = args.wipe_delay_ratio
    if args.wipe_blocks is not None:
        kw["wipe_blocks"] = args.wipe_blocks
    if args.pause is not None:
        kw["pause_mode"] = args.pause
    if args.ink_path is not None:
        kw["ink_path_mode"] = args.ink_path
    return Config(**kw)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    cfg = _build_cfg(args)

    print("=" * 56)
    print("Stream-stroke animation renderer")
    print("=" * 56)

    image_bgr = _imread_any(args.image)
    if image_bgr is None:
        print(f"[err] Cannot read image: {args.image}")
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_path = out_dir / f"stream_{ts}.mp4"
    h264_path = out_dir / f"stream_{ts}_h264.mp4"

    pen_png = Path(args.pen_image) if args.pen_image else None
    renderer = StreamBoardRenderer(image_bgr, cfg, pen_png, args.bare_tip)
    print(f"  Input: {args.image}")
    print(f"  Output dimensions: {renderer.out_w}x{renderer.out_h}, frame rate: {cfg.fps}")

    renderer.render_to(raw_path, args.total_ms)
    final = transcode_h264(raw_path, h264_path)

    size_mb = final.stat().st_size / (1024 * 1024)
    print(f"\nFinal video: {final}")
    print(f"  File size: {size_mb:.2f} MB")
    print("=" * 56)
    print("Complete")
    # Print final path on last line for callers
    print(f"OUTPUT={final}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
