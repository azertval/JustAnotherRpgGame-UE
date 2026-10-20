"""Subdivision must preserve closed slab adjacency before normal recalculation."""
import collections
import importlib.util
import math
from pathlib import Path
import unittest


class PavingTopologyTests(unittest.TestCase):
    def test_closed_slab_keeps_shared_edges_and_its_surface(self):
        root=Path(__file__).resolve().parents[2]
        spec=importlib.util.spec_from_file_location('paving_topology',root/'scripts/assetsGeneration/build_arenarea_district.py')
        a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
        points=[(-1,-1,0),(1,-1,0),(1,1,0),(-1,1,0),
                (-1,-1,.2),(1,-1,.2),(1,1,.2),(-1,1,.2)]
        faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        a.g.solid(points,faces,'marble_white',bevel=0,color=(.8,.9,1,1),seed_alpha=.37)
        a.refine_closed_paving(0)
        edges=collections.Counter(tuple(sorted((u,v))) for f in a.g.FACES for u,v in zip(f,f[1:]+f[:1]))
        self.assertTrue(edges)
        self.assertEqual(set(edges.values()),{2})
        area=0.
        for f in a.g.FACES:
            self.assertEqual(len(f),3)
            p,q,r=[a.g.VERTS[i] for i in f]
            u=[q[i]-p[i] for i in range(3)];v=[r[i]-p[i] for i in range(3)]
            cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            area+=math.sqrt(sum(x*x for x in cross))/2
            self.assertTrue(any(all(abs(a.g.VERTS[i][axis]-value)<1e-12 for i in f)
                                for axis,values in enumerate([(-1,1),(-1,1),(0,.2)]) for value in values))
        self.assertAlmostEqual(area,9.6)
        self.assertTrue(all(c==(.8,.9,1,1) for c in a.g.FACE_COLORS))
        self.assertTrue(all(s==.37 for s in a.g.FACE_SEEDS))


if __name__=='__main__':
    unittest.main()
