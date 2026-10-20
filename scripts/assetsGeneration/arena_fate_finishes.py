# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Pure geometry helpers for Arena finishes; caller owns export and placement.

gate_rim(kit): east shaft rails on supported ground, repeat with yaw=180 for west.
No Blender, files, engine state, materials or navigation settings change on import.
"""

from __future__ import annotations

import math


def _rail_segment(kit, first, last):
    """Complete base/cap/balusters between shared corner piers, without doubled posts."""
    length = math.dist(first, last)
    direction = ((last[0] - first[0]) / length, (last[1] - first[1]) / length)

    def box(start, stop, z, depth, height, material):
        centre = (start + stop) / 2
        x = first[0] + centre * direction[0]
        y = first[1] + centre * direction[1]
        width = stop - start
        kit.block(
            x,
            y,
            z,
            width if direction[0] else depth,
            depth if direction[0] else width,
            height,
            material,
        )

    usable = length - 0.44
    for i in range(math.ceil(usable / 0.95)):
        start = 0.22 + i * 0.95 + 0.004
        stop = min(length - 0.22, 0.22 + (i + 1) * 0.95) - 0.004
        box(start, stop, 0, 0.30, 0.12, "stone_cream")
    box(0.255, length - 0.255, 1.02, 0.40, 0.13, "marble_white")
    count = max(2, round((length - 0.65) / 0.43))
    for i in range(count):
        distance = 0.325 + (i + 0.5) * (length - 0.65) / count
        x, y = first[0] + distance * direction[0], first[1] + distance * direction[1]
        kit.turned(
            x,
            y,
            0.12,
            [
                (0.10, 0),
                (0.10, 0.08),
                (0.065, 0.16),
                (0.11, 0.32),
                (0.11, 0.43),
                (0.065, 0.58),
                (0.055, 0.71),
                (0.10, 0.83),
                (0.10, 0.90),
            ],
            "marble_white",
            sides=32,
        )
        kit.turned(
            x,
            y,
            0.68,
            [(0.066, 0), (0.070, 0.008), (0.070, 0.032), (0.066, 0.040)],
            "bronze",
            sides=32,
        )


def gate_rim(kit):
    """East shaft X49..62/Y+-2, on deck only; no crossbar at stair access X49.

    Side centre-lines Y+-2.3; back X62.3. Shared 0.5 m corner caps never duplicate.
    Mirror this complete model at origin with yaw180 for the west gate. No pit wall.
    """
    first = [(49.0, -2.3, 0), (49.0, 2.3, 0)]
    last = [(62.3, -2.3, 0), (62.3, 2.3, 0)]
    for p, q in zip(first, last):
        _rail_segment(kit, p, q)
    _rail_segment(kit, last[0], last[1])
    for x, y, _ in first + last:
        kit.block(x, y, 0, 0.42, 0.42, 0.12, "marble_white")
        kit.block(x, y, 0.12, 0.34, 0.34, 0.91, "stone_cream")
        kit.block(x, y, 1.03, 0.42, 0.42, 0.10, "marble_white")
        kit.block(x, y, 1.13, 0.50, 0.50, 0.10, "marble_white")

