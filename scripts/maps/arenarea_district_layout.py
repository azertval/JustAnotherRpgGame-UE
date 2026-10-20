#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Arenarea complete exterior contract, metres X east / Y south / Z up.

The 189 by 156 metre Arena remains the existing monument. Streets connect real
city blocks around it; positions change, quest identity and transitions do not.
No Unreal imports: the asset builder and engine importer share this document.
"""

AREA = [-220.0, -162.0, 350.0, 306.0]
TRACK_SURFACE_OFFSET = .04  # Sand must not share a plane with the terrain.

# Author-approved 11 October: the city climbs twelve metres from the Arena
# threshold to its southern terraces. Pads describe real horizontal rooms and
# civic gardens; smooth approaches keep the principal streets cart-passable.
TERRAIN_PADS = [
    {"id":"arena-parvis", "bounds":[-40,12,40,47], "z":0., "blend":12.},
    {"id":"dusk-of-justice", "bounds":[-22,59,22,94], "z":1.0, "blend":25.},
    {"id":"cloaked-brewer", "bounds":[171,27,208,62], "z":0.0, "blend":33.},
    {"id":"natural-pool", "bounds":[-164,42,-90,104], "z":1.0, "blend":24.},
    {"id":"golden-chalice", "bounds":[-82,160,-24,205], "z":7.4, "blend":32.},
    {"id":"inlets-bazaar", "bounds":[-183,140,-132,207], "z":5.4, "blend":27.},
    {"id":"hippodrome", "bounds":[95,91,202,279], "z":4.5, "blend":40.},
    {"id":"mapleleaf-plaza", "bounds":[67,260,105,287], "z":8.0, "blend":32.},
]


def smoothstep(value):
    value=max(0.,min(1.,value))
    return value*value*(3.-2.*value)


def _base_ground_height(x,y):
    """Metres, deterministic city datum shared with meshes, routes and actors.

    The original bridge and Arena entrances stay exactly at zero. Horizontal
    civic platforms blend into long approach slopes, never floating steps.
    """
    import math
    if x>=234 and y<100:
        return 0.0
    height=12.0*smoothstep((y-26.)/280.)
    for pad in TERRAIN_PADS:
        x0,y0,x1,y1=pad["bounds"]
        distance=max(x0-x,0.,x-x1,y0-y,0.,y-y1)
        weight=max(0.,1.-distance/pad["blend"])
        height=height*(1.-weight)+pad["z"]*weight
    for pad in (TERRAIN_PADS[0],TERRAIN_PADS[2]):
        x0,y0,x1,y1=pad["bounds"]
        distance=max(x0-x,0.,x-x1,y0-y,0.,y-y1)
        weight=max(0.,1.-distance/pad["blend"])
        height=height*(1.-weight)+pad["z"]*weight
    stadium_radius=math.hypot(x-148.,max(abs(y-185.)-52.,0.))
    stadium_weight=max(0.,1.-max(stadium_radius-40.,0.)/26.)
    height=height*(1.-stadium_weight)+4.5*stadium_weight
    radius=math.sqrt((x/105.)**2+((y+65.)/88.)**2)
    height*=smoothstep((radius-1.)/.28)
    # The unmodified Arching Bridge needs an entirely level approach.
    bridge_distance=max(abs(y+85.)-12.,0.,215.-x)
    height*=smoothstep(bridge_distance/30.)
    return round(height,7)


GARDEN_TERRACES = [
    {"id":"casino-lower-garden", "bounds":[-86,220,-20,232], "z":9.4},
    {"id":"casino-upper-garden", "bounds":[-86,240,-20,252], "z":11.2},
]
GARDEN_STAIRS = [
    {"id":"casino-garden-first-stair", "x":-53.,"width":5.,"y0":212.,"y1":220.,
     "z0":_base_ground_height(-53,212),"z1":9.4,"steps":12},
    {"id":"casino-garden-second-stair", "x":-53.,"width":5.,"y0":232.,"y1":240.,
     "z0":9.4,"z1":11.2,"steps":12},
]


def ground_height(x,y):
    """Absolute surface, including the two deliberately stepped garden routes."""
    import math
    for stair in GARDEN_STAIRS:
        if abs(x-stair["x"])<=stair["width"]/2 and stair["y0"]<y<stair["y1"]:
            step=math.ceil((y-stair["y0"])/(stair["y1"]-stair["y0"])*stair["steps"])
            return stair["z0"]+(stair["z1"]-stair["z0"])*step/stair["steps"]
    for terrace in GARDEN_TERRACES:
        x0,y0,x1,y1=terrace["bounds"]
        if x0<=x<=x1 and y0<=y<=y1:
            return terrace["z"]
    return _base_ground_height(x,y)


def foundation_height(x,y):
    """Underlying ground is hidden beneath constructed terraces and stairs."""
    for stair in GARDEN_STAIRS:
        if abs(x-stair["x"])<=stair["width"]/2 and stair["y0"]<=y<=stair["y1"]:
            return min(_base_ground_height(x,y),stair["z0"])-.4
    for terrace in GARDEN_TERRACES:
        x0,y0,x1,y1=terrace["bounds"]
        if x0<=x<=x1 and y0<=y<=y1:
            return min(_base_ground_height(x,y),terrace["z"])-.5
    return ground_height(x,y)


def ground_position(position):
    import math
    x,y,z=position
    track=math.hypot(x-148.,max(abs(y-185.)-52.,0.))<37.5
    return [x,y,round(z+ground_height(x,y)+(TRACK_SURFACE_OFFSET if track else 0),5)]


def storey_regions():
    """Exact physical tread heights precede the broad level-floor regions."""
    pub_z=ground_height(190,44)
    regions=[{"storey":0,"minimum":[181,51-(j+1)*.5,pub_z+(j+1)*.2],
              "maximum":[185,51-j*.5,pub_z+(j+1)*.2+.01]} for j in range(20)]
    for stair in GARDEN_STAIRS:
        tread=(stair["y1"]-stair["y0"])/stair["steps"]
        rise=(stair["z1"]-stair["z0"])/stair["steps"]
        regions.extend({"storey":0,
            "minimum":[stair["x"]-stair["width"]/2,stair["y0"]+j*tread,stair["z0"]+(j+1)*rise],
            "maximum":[stair["x"]+stair["width"]/2,stair["y0"]+(j+1)*tread,stair["z0"]+(j+1)*rise+.01]}
            for j in range(stair["steps"]))
    regions.extend([
        {"storey":1,"minimum":[177.4,32.4,pub_z+4],"maximum":[187,41,pub_z+8]},
        {"storey":1,"minimum":[187,32.4,pub_z+4],"maximum":[202.6,55.6,pub_z+8]},
        {"storey":0,"minimum":[234,-92.7,.04],"maximum":[342,-77.3,.05]},
    ])
    return regions
ARENA = [0.0, -65.0, 0.0]
LANDMARKS = [
    {"id": "arena-of-fate", "name": "Arena of Fate", "position": ARENA, "kind": "monument"},
    {"id": "dusk-of-justice", "name": "Dusk of Justice Betting House", "position": [0, 76, 0], "kind": "interior"},
    {"id": "natural-pool", "name": "Natural Pool", "position": [-127, 73, 0], "kind": "garden"},
    {"id": "golden-chalice", "name": "Golden Chalice Casino", "position": [-53, 182, 0], "kind": "interior"},
    {"id": "hippodrome", "name": "Hippodrome", "position": [148, 185, 0], "kind": "sports"},
    {"id": "inlets-bazaar", "name": "Inlet's Bazaar Block", "position": [-158, 177, 0], "kind": "market"},
    {"id": "cloaked-brewer", "name": "Cloaked Brewer Pub", "position": [190, 44, 0], "kind": "interior"},
    {"id": "arena-gate", "name": "Arena Gate / Arching Bridge", "position": [216, -85, 0], "kind": "gate"},
    {"id": "mapleleaf-plaza", "name": "Mapleleaf Plaza", "position": [88, 272, 0], "kind": "square"},
    {"id": "water-gate", "name": "Water Gate / Docks District", "position": [-203, 112, 0], "kind": "gate"},
    {"id": "arching-bridge", "name": "Arching Bridge / Rubicund River", "position": [288, -85, 0], "kind": "bridge"},
    {"id": "oldtown-riverbank", "name": "Oldtown Riverbank", "position": [344, -85, 0], "kind": "background"},
    {"id": "docks-district", "name": "Docks District", "position": [-256, 124, 0], "kind": "background"},
    {"id": "palacedomain-boundary", "name": "Palacedomain Boundary", "position": [-182, 317, 0], "kind": "background"},
    {"id": "downtown-boundary", "name": "Downtown Boundary", "position": [20, 317, 0], "kind": "background"},
]

# Front doors are unobstructed, four metres wide at the narrowest public route.
NAVIGATION_TARGETS = [
    {"id": "parvis", "position": [0, 34, 0]},
    {"id": "arena-threshold", "position": [0, 16, 0]},
    {"id": "dusk-hall", "position": [0, 76, 0]},
    {"id": "pool-promenade", "position": [-127, 103, 0]},
    {"id": "casino-gaming-hall", "position": [-53, 182, 0]},
    {"id": "casino-reading-room", "position": [-63, 169, 0]},
    {"id": "hippodrome-track", "position": [148, 255, 0]},
    {"id": "hippodrome-stand", "position": [108, 187, 0]},
    {"id": "bazaar-court", "position": [-158, 177, 0]},
    {"id": "pub-taproom", "position": [190, 44, 0]},
    {"id": "pub-upper-room", "position": [194, 45, 4]},
    {"id": "arena-gate", "position": [216, -85, 0]},
    {"id": "water-gate", "position": [-203, 112, 0]},
    {"id": "plaza", "position": [88, 280, 0]},
    {"id": "quay", "position": [-197, -50, 0]},
    {"id": "bridge-western-approach", "position": [234, -85, .04]},
    {"id": "bridge-midspan", "position": [288, -85, .04]},
    {"id": "bridge-oldtown-threshold", "position": [335, -85, .04]},
]

ENTITY_POSITIONS = {
    "e1": [224, 292, 0], "e2": [226, 298, 0],
    "e3": [0, 22, 0], "e4": [0, 17, 0],
    "e5": [-3, 35, 0], "e6": [-1, 35, 0], "e7": [-10, 30, 0],
    "e8": [216, -85, 0], "e9": [-203, 112, 0],
    "e10": [190, 57, 0], "e11": [148, 257, 0],
}
START = ENTITY_POSITIONS["e1"]
# Core quest route: one leg across the neighbourhood, no repeated sightseeing.
ROUTE = [[224,292,0], [222,269,0], [211,263,0], [211,155,0],
         [224,94,0], [220,72,0], [176,72,0], [137,54,0],
         [94,45,0], [38,39,0], [0,34,0], [0,22,0]]
# Physical acceptance walk for the composed neighbourhood. The Arena portal at
# (0,17) and the reserved gates are deliberately avoided during this tour.
VISIT_ROUTE = [
    [224,292,0],[211,290,0],[130,290,0],[104,283,0],[88,280,0],
    [130,264,0],[148,251,0],[175,230,0],[185,188,0],[175,151,0],
    [185,188,0],[175,235,0],[195,255,0],[211,263,0],[211,155,0],
    [224,94,0],[220,72,0],[190,66,0],[190,57,0],[190,44,0],
    [183,51.5,0],
    *[[183,51-(j+.5)*.5,(j+1)*.2] for j in range(20)],
    [183,39.5,4],[190,39.5,4],[194,45,4],
    [190,39.5,4],[183,39.5,4],
    *[[183,51-(j+.5)*.5,(j+1)*.2] for j in reversed(range(20))],
    [183,51.5,0],[190,57,0],[190,66,0],[220,72,0],[224,-60,0],
    [234,-85,.04],[252,-85,.04],[288,-85,.04],[324,-85,.04],[335,-85,.04],
    [324,-85,.04],[288,-85,.04],[252,-85,.04],[234,-85,.04],[224,-60,0],
    [220,72,0],[176,72,0],[137,54,0],
    [94,45,0],[38,39,0],[0,34,0],[0,56,0],[0,91,0],[0,76,0],
    [0,67,0],[0,76,0],[0,91,0],[0,111,0],[-85,111,0],
    [-97,108,0],[-127,103,0],[-168,95,0],[-158,74,0],
    [-172,103,0],[-196,91,0],[-203,73,0],[-203,-50,0],
    [-203,73,0],[-196,91,0],[-181,125,0],[-181,159.5,0],
    [-158,159.5,0],[-158,177,0],[-158,205,0],[-113,212,0],
    [-53,212,0],[-53,204,0],[-53,194,0],[-53,182,0],[-53,173,0],
    [-63,169,0],[-53,173,0],[-53,182,0],[-53,204,0],[-27,212,0],
    [66,212,0],[66,266,0],[88,280,0],[104,283,0],[130,290,0],[211,290,0],[224,292,0],
]
CROWD_ROUTES = [
    [[-181,148,0],[-181,208,0],[-139,208,0],[-139,148,0]],
    [[-99,154,0],[-99,208,0],[-28,208,0],[-28,154,0]],
    [[166,73,0],[216,73,0],[216,105,0],[166,105,0]],
    [[66,266,0],[88,280,0],[104,283,0],[66,286,0]],
]
SHOTS = [
    {"name": "ensemble", "target": [0,70,10], "yaw": 0, "pitch": 55, "distance": 430},
    *[{"name": p["id"], "target": [p["position"][0], p["position"][1], 1.8],
       "yaw": 0, "pitch": 40, "distance": 23 if p["kind"] == "interior" else 38}
      for p in LANDMARKS if p["kind"] not in {"background", "bridge"}],
    {"name": "parvis", "target": [0,35,1.8], "yaw": 0, "pitch": 40, "distance": 22},
    {"name": "quais", "target": [-214,-24,-.5], "yaw": -90, "pitch": 38, "distance": 28},
    {"name": "casino-entree", "target": [-53,199,3.2], "yaw": 0, "pitch": 27, "distance": 48},
    {"name": "maison-paris-entree", "target": [0,89,3.2], "yaw": 0, "pitch": 28, "distance": 39},
    {"name": "pub-entree", "target": [190,57,3.0], "yaw": 0, "pitch": 28, "distance": 32},
    {"name": "pub-etage", "target": [194,45,5.8], "yaw": 0, "pitch": 40, "distance": 16},
    {"name": "arching-bridge", "target": [288,-85,-.8], "yaw": 20, "pitch": 28, "distance": 116},
    {"name": "oldtown-rive", "target": [341,-85,3], "yaw": 90, "pitch": 32, "distance": 56},
    {"name": "docks-district", "target": [-252,120,0], "yaw": 90, "pitch": 38, "distance": 66},
    {"name": "palacedomain-raccord", "target": [-182,326,4], "yaw": 180, "pitch": 30, "distance": 62},
    {"name": "downtown-raccord", "target": [20,326,4], "yaw": 180, "pitch": 30, "distance": 62},
]
SHOTS[1] = {"name": "arena-of-fate", "target": [0,4,15], "yaw": 0, "pitch": 32, "distance": 90}

# Plots are written independently of the camera/quest; reserved landscape fields
# receive deliberate planting, paving and garden furniture in the generator.
BUILDINGS = [
    {"id": "dusk-of-justice", "position": [0,76,0], "width": 34, "depth": 24,
     "height": 7, "use": "betting", "upstairs": False},
    {"id": "golden-chalice", "position": [-53,182,0], "width": 44, "depth": 32,
     "height": 9, "use": "casino", "upstairs": False},
    {"id": "cloaked-brewer", "position": [190,44,0], "width": 26, "depth": 24,
     "height": 8, "use": "pub", "upstairs": True},
]

# Every consumer receives absolute altitudes. Room geometry remains local to its
# plot, while upper-floor waypoints retain their four-metre local elevation.
NAVIGATION_TARGETS.extend([
    {"id":"casino-lower-garden","position":[-53,225,0]},
    {"id":"casino-upper-garden","position":[-53,246,0]},
])
_garden_path=[]
for _stair in GARDEN_STAIRS:
    _garden_path.extend([_stair["x"],_stair["y0"]+(j+.5)*(_stair["y1"]-_stair["y0"])/_stair["steps"],0]
                        for j in range(_stair["steps"]))
    _garden_path.append([_stair["x"],_stair["y1"]+4,0])
_garden_path.append([-53,246,0])
_branch=VISIT_ROUTE.index([-53,212,0])+1
VISIT_ROUTE[_branch:_branch]=_garden_path+list(reversed(_garden_path[:-1]))+[[-53,212,0]]
for _entry in LANDMARKS + NAVIGATION_TARGETS:
    if _entry["id"] != "arena-of-fate":
        _entry["position"] = ground_position(_entry["position"])
ENTITY_POSITIONS = {key:ground_position(value) for key,value in ENTITY_POSITIONS.items()}
START = ENTITY_POSITIONS["e1"]
ROUTE = [ground_position(point) for point in ROUTE]
VISIT_ROUTE = [ground_position(point) for point in VISIT_ROUTE]
CROWD_ROUTES = [[ground_position(point) for point in route] for route in CROWD_ROUTES]
for _shot in SHOTS:
    _shot["target"] = ground_position(_shot["target"])
SHOTS.extend([
    {"name":"relief-casino-terraces", "target":ground_position([-89,213,4]),
     "yaw":45,"pitch":26,"distance":82},
    {"name":"relief-boulevard", "target":ground_position([66,135,3]),
     "yaw":180,"pitch":25,"distance":90},
    {"name":"hippodrome-longitudinal", "target":ground_position([148,180,3]),
     "yaw":0,"pitch":35,"distance":175},
])
