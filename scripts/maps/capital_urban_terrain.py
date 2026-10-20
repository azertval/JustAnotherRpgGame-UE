"""Constructible access grading; no river fill, no competing terrain surface."""
import math
import numpy as np
import capital_landscape_layout as layout
import capital_city_layout as city


def smooth(t):
    t = np.clip(t,0,1)
    return t*t*(3-2*t)


def sample(grid, heights, point):
    return float(heights[grid.vertex(point)])


def envelope(values, edges):
    import heapq
    result=list(values);queue=[(z,i) for i,z in enumerate(values) if math.isfinite(z)]
    heapq.heapify(queue)
    while queue:
        z,i=heapq.heappop(queue)
        if z>result[i]+1e-9:continue
        for j,cost in edges[i]:
            if z+cost<result[j]-1e-9:
                result[j]=z+cost;heapq.heappush(queue,(z+cost,j))
    return np.asarray(result)


def shape_city(grid,height,water):
    """Constrain each route by its use, within narrow cut/fill corridors.

    The midpoint of the upper/lower grade envelopes balances cut and fill.
    A lower envelope alone systematically lowered every street towards a quay.
    """
    height=height.copy()
    for key in city.GATES:
        u,v,z,*_=city.LANDMARKS[key]
        distance=np.hypot(grid.u-u,grid.v-v)*layout.METRES_PER_UNIT
        apron=smooth((22-distance)/8)*(water<.5)
        height=height*(1-apron)+z*apron
    nodes=[];chains=[];buckets={};grades=[]
    for road in layout.ROADS:
        chain=[]
        for a,b in zip(road['points'],road['points'][1:]):
            count=math.ceil(math.dist(a,b)*layout.METRES_PER_UNIT/3)
            for t in np.linspace(0,1,count,endpoint=False):
                nodes.append((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t));chain.append(len(nodes)-1);grades.append(road.get('grade',.12))
        nodes.append(tuple(road['points'][-1]));chain.append(len(nodes)-1);chains.append(chain);grades.append(road.get('grade',.12))
    edges=[[] for _ in nodes]
    def link(i,j):
        cost=math.dist(nodes[i],nodes[j])*layout.METRES_PER_UNIT*min(grades[i],grades[j])
        edges[i].append((j,cost));edges[j].append((i,cost))
    for chain in chains:
        for i,j in zip(chain,chain[1:]):link(i,j)
    for i,(u,v) in enumerate(nodes):
        cell=(int(u//4),int(v//4))
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                for j in buckets.get((cell[0]+dx,cell[1]+dy),[]):
                    if math.dist(nodes[i],nodes[j])<4:link(i,j)
        buckets.setdefault(cell,[]).append(i)
    natural=np.array([max(0.,float(height[grid.vertex(p)])) for p in nodes])
    controls=[]
    for key in city.GATES:
        u,v,z,*_=city.LANDMARKS[key];controls.append((u,v,z,18.))
    for name,ends in layout.BRIDGES.items():
        if name!='aqueduct':
            for p in ends:controls.append((*p,city.BRIDGE_LEVELS[name],27.))
    controls.extend([(1083,420,0,5),(1215,812,52,3),(1175,1180,46,3),(655,690,62,3)])
    fixed={}
    for u,v,z,radius in controls:
        for i,p in enumerate(nodes):
            if math.dist(p,(u,v))*layout.METRES_PER_UNIT<radius:fixed[i]=z
    for i,(u,v) in enumerate(nodes):
        if ((u-layout.ARENA[0])/100)**2+((v-layout.ARENA[1])/84)**2<=1:fixed[i]=0
    upper=envelope([fixed.get(i,math.inf) for i in range(len(nodes))],edges)
    lower=-envelope([-fixed[i] if i in fixed else math.inf for i in range(len(nodes))],edges)
    if np.any(lower>upper+1e-6):
        bad=np.flatnonzero(lower>upper+1e-6)
        raise ValueError(f'Incompatible road constraints: {[(nodes[i],lower[i],upper[i]) for i in bad[:8]]}')
    constrained=np.clip(natural,lower,upper)
    z=(envelope(constrained,edges)-envelope(-constrained,edges))*.5
    best=np.full_like(height,np.inf);target=height.copy();widths=np.zeros_like(height)
    for road,chain in zip(layout.ROADS,chains):
        width=road['width']/2+1.5
        for i,j in zip(chain,chain[1:]):
            a,b=nodes[i],nodes[j];pad=(width+7)/layout.METRES_PER_UNIT
            p0=grid.pixel((min(a[0],b[0])-pad,min(a[1],b[1])-pad))
            p1=grid.pixel((max(a[0],b[0])+pad,max(a[1],b[1])+pad))
            x0=max(0,int(p0[0]));y0=max(0,int(p0[1]));x1=min(grid.shape[1],math.ceil(p1[0])+1);y1=min(grid.shape[0],math.ceil(p1[1])+1)
            if x0>=x1 or y0>=y1:continue
            region=np.s_[y0:y1,x0:x1];u=grid.u[region];v=grid.v[region]
            dx,dy=b[0]-a[0],b[1]-a[1];length=dx*dx+dy*dy
            if length<1e-9:continue
            t=np.clip(((u-a[0])*dx+(v-a[1])*dy)/length,0,1)
            distance=np.hypot(u-a[0]-dx*t,v-a[1]-dy*t)*layout.METRES_PER_UNIT
            use=distance<best[region]
            best[region]=np.where(use,distance,best[region])
            target[region]=np.where(use,z[i]+(z[j]-z[i])*t,target[region])
            widths[region]=np.where(use,width,widths[region])
    w=smooth((widths+7-best)/7)*(water<.5)
    result=height*(1-w)+target*w
    # Fix the four interpolated vertices of the datum, not only its nearest
    # vertex. Otherwise a sub-centimetre interpolation error moves the threshold.
    entry=np.hypot(grid.u-layout.ENTRY_UNITS[0],grid.v-layout.ENTRY_UNITS[1])*layout.METRES_PER_UNIT
    result=np.where(entry<4,0,result)
    return result
