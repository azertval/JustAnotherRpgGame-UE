# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Physical promises specific to the approved Arenarea relief reconstruction."""
import importlib.util
import math
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("arenarea_relief_test",ROOT/"scripts/maps/arenarea_district_layout.py")
layout=importlib.util.module_from_spec(spec)
spec.loader.exec_module(layout)


class ArenareaReliefTests(unittest.TestCase):
    def test_existing_arena_and_bridge_datum_are_preserved(self):
        for point in [(0,16),(0,22),(0,34),(216,-85),(252,-85),(335,-85)]:
            self.assertEqual(layout.ground_height(*point),0)

    def test_rooms_are_flat_at_their_foundation(self):
        for building in layout.BUILDINGS:
            x,y,_=building["position"]
            z=layout.ground_height(x,y)
            for dx in [-building["width"]/2,0,building["width"]/2]:
                for dy in [-building["depth"]/2,0,building["depth"]/2]:
                    self.assertAlmostEqual(layout.ground_height(x+dx,y+dy),z,places=5)

    def test_existing_street_and_crowd_routes_have_no_cliffs(self):
        worst=0
        for route in [layout.ROUTE,layout.VISIT_ROUTE,*layout.CROWD_ROUTES]:
            for a,b in zip(route,route[1:]):
                length=math.dist(a[:2],b[:2])
                if length==0:continue
                midpoint=[(a[k]+b[k])/2 for k in range(2)]
                if any(abs(p[0]-s["x"])<=s["width"]/2 and s["y0"]<=p[1]<=s["y1"]
                       for s in layout.GARDEN_STAIRS for p in [a,b,midpoint]):
                    continue  # Discrete risers have their own physical test.
                for j in range(1,101):
                    p=[a[k]+(b[k]-a[k])*j/100 for k in range(2)]
                    q=[a[k]+(b[k]-a[k])*(j-1)/100 for k in range(2)]
                    worst=max(worst,abs(layout.ground_height(*p)-layout.ground_height(*q))/(length/100))
        self.assertLessEqual(worst,.20)

    def test_relief_reaches_twelve_metres(self):
        self.assertEqual(layout.ground_height(-180,306),12)
        self.assertGreaterEqual(layout.ground_height(-53,246),11)

    def test_whole_rigid_stadium_has_a_level_support(self):
        for y in range(95,276,3):
            for x in range(110,187,3):
                radius=math.hypot(x-148,max(abs(y-185)-52,0))
                if radius<=38:
                    self.assertAlmostEqual(layout.ground_height(x,y),4.5,places=5)

    def test_pub_stairs_regions_match_the_twenty_physical_treads(self):
        stairs=layout.storey_regions()[:20]
        self.assertEqual(len(stairs),20)
        for j,region in enumerate(stairs):
            self.assertAlmostEqual(region["minimum"][2],(j+1)*.2)
            self.assertAlmostEqual(region["maximum"][1]-region["minimum"][1],.5)
        upper=[r for r in layout.storey_regions() if r["storey"]==1]
        self.assertEqual(len(upper),2)
        self.assertTrue(all(r["minimum"][2]==4 for r in upper))

    def test_garden_stairs_are_small_regular_risers_and_exact_endpoints(self):
        for stair in layout.GARDEN_STAIRS:
            rise=(stair["z1"]-stair["z0"])/stair["steps"]
            self.assertGreater(rise,0)
            self.assertLessEqual(rise,.20)
            self.assertAlmostEqual(layout.ground_height(stair["x"],stair["y1"]),stair["z1"])


if __name__=="__main__":
    unittest.main()
