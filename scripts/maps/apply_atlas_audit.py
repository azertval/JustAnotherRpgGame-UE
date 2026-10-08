# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Replay the author's 7 October atlas corrections without altering playable scenes.

Illustrations are received from imagegen, never painted or patched by this script.
Plans are drawn from graphic construction data at their native delivery size.
"""

from __future__ import annotations

import argparse
import copy
import csv
import difflib
import hashlib
import html
import importlib.util
import json
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "Tools/WorldAtlasAudit20261007"
CAPITAL = ROOT / "Tools/Assets3D/Regions/central-empire/capital/AtlasCoherent20261005"
ASSETS = ROOT / "Source/Elements/Assets/Maps"
CATALOG = ROOT / "Source/Elements/Maps/world-maps.json"
SIZE = (1536, 1024)
DATE = "2026-10-07"
PAPER = "#efe6d2"
INK = "#443728"
URBAN_MASTER = (
    ROOT / "Tools/WorldAtlas20261005/generated-images/exec-3f2751ae-d49b-4e2c-ad21-07f0bb8d8ee2.png"
)
TERRAIN_MASTER = (
    ROOT / "Tools/WorldAtlas20261005/generated-images/exec-ea864bc9-a14c-4f2b-bae3-e56209bdae6d.png"
)
WALL = [
    (29, 27),
    (43, 27),
    (48, 14),
    (56, 12),
    (64, 20),
    (73, 27),
    (75, 38),
    (86, 44),
    (94, 59),
    (94, 91),
    (72, 95),
    (47, 95),
    (27, 94),
    (28, 68),
    (24, 56),
    (24, 35),
    (29, 27),
]
GATES = [
    ("Water Gate", 44, 27),
    ("Arena Gate", 65, 18),
    ("Market Gate", 87, 45),
    ("Wildlife Gate", 80, 94),
    ("Bauron Gate", 31, 94),
    ("Tamera Gate", 27.6, 83),
]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def font(size):
    return ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", size)


def display_text(text):
    return re.sub(
        r" +",
        " ",
        re.sub(r"\b(?:proposées|proposée|proposés|proposé|proposed)\b", "", text, flags=re.I),
    ).strip()


def normalized(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return " ".join(re.findall(r"[a-z0-9]+", text))


def baseline(target):
    """Freeze review inputs so installation cannot change a queued edit's reference."""
    destination = WORK / "baseline" / target
    if not destination.exists():
        reviewed = (
            ROOT / "Tools/WorldAtlasReview20261006" / target
            if target.startswith("capital/")
            else ROOT / "Tools/WorldAtlasReview20261006/images" / Path(target).name
        )
        original = reviewed if reviewed.is_file() else ASSETS / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, destination)
    return str(destination)


def frame(point, width=0.32, height=None):
    height = width if height is None else height
    return [
        round(max(0, min(1 - width, point[0] - width / 2)), 6),
        round(max(0, min(1 - height, point[1] - height / 2)), 6),
        width,
        height,
    ]


def prepare(request):
    text = Path(request).read_text(encoding="utf-8-sig")
    entries = []
    for section in re.split(r"(?m)^## ", text)[1:]:
        header, _, body = section.partition("\n")
        match = re.match(r"(.+) — (\S+\.png) \[([^,]+), ([^\]]+)\]", header.strip())
        if not match:
            raise ValueError(f"Unrecognized audit heading: {header}")
        name, target, status, severity = match.groups()
        briefs = re.findall(r"(?m)^BRIEF : (.+)$", body)
        data = re.findall(r"(?m)^DONNÉES : (.+)$", body)
        entries.append(
            dict(
                name=name,
                file=target,
                status=status,
                severity=severity,
                briefs=briefs,
                data=data,
                observations=body.strip(),
            )
        )
    write(WORK / "audit.json", dict(date=DATE, source="Author attachment", entries=entries))
    catalog = read(CATALOG)
    canonical = read(ROOT / "scripts/maps/canonical_vtt_places.json")
    jobs = []
    for entry in entries:
        if entry["status"] != "à régénérer" or entry["file"].startswith("capital/plans/"):
            continue
        plates = [
            (k, p)
            for k, p in catalog["plates"].items()
            if p["image"] == "Maps/" + entry["file"] and not p.get("frame")
        ]
        pid, plate = plates[0] if plates else ("", {})
        labels = list(
            dict.fromkeys(p["name"] for p in catalog["plates"].values() if p.get("parent") == pid)
        )
        points = [
            dict(name=p["name"], point=p["referencePoint"])
            for p in canonical
            if p.get("referenceRegion") == pid and p.get("referencePoint")
        ]
        urban = (
            entry["file"].startswith("capital/images/")
            or plate.get("kind") == "city"
            or entry["file"]
            in (
                "world/imperial-benenet-begraense.png",
                "world/republic-of-freelands-the-winterhold-city.png",
                "world/republic-of-freelands-the-port-city-of-goldraft.png",
                "world/storm-islands-cantala-ruins.png",
                "world/taii-maku-city-states-g-bagede-illu.png",
            )
        )
        master = URBAN_MASTER if urban else TERRAIN_MASTER
        prompt = (
            "Use case: precise-object-edit. Original game atlas illustration. "
            "Edit target is image 1; image 2 is the AUTHOR ABSOLUTE STYLE MASTER. "
            "Match image 2 facture, camera, materials, light and plain parchment cartouches. "
            "Exact delivery 1536x1024 landscape. "
            "Preserve validated architecture, relative positions, coastline, rivers and "
            "terrain unless the following author brief explicitly corrects them. "
            "Match its painted miniature materials and camera. All text must remain "
            "legible at 1280px display width. No production notes, schematic insets, "
            "hashes, watermarks, cursor icons, invented names, or human figures.\n"
            "AUTHOR BRIEF:\n" + "\n".join(display_text(b) for b in entry["briefs"]) + "\n"
            "AUDIT OBSERVATIONS:\n" + entry["observations"] + "\n"
        )
        if pid and plate.get("kind") in ("region", "territory"):
            prompt += (
                "Only catalogue labels, exact spelling: " + ", ".join(labels) + ".\n"
                "Geographic context from the catalogue: " + plate.get("description", "") + "\n"
                "Canonical reference positions, normalized graphic coordinates only, "
                "never print these coordinates: " + json.dumps(points, ensure_ascii=False) + "\n"
            )
        prompt += (
            "\nLATEST AUTHOR CORRECTION, takes precedence over old labels and observations: "
            "Remove every occurrence of proposé, proposée, proposés, proposées and proposed "
            "from all titles, headings and legends. Do not introduce ornaments absent from "
            "the style master. Plain restrained parchment label plaques only, no decorative "
            "leaf flourishes, parchment mat, bottom parchment band, or oversized title banner. "
            "Draw the painted neighborhood or terrain to all four image edges. "
            "No extra architecture, monuments, towers, sculptures or floors. "
        )
        if urban:
            prompt += "No ornamental outer border. Preserve the required diptych for building plates, with a thin unobtrusive divider, compact French numbered legend on the painted background, headings Extérieur and Niveau d’accès · intérieur."
        else:
            prompt += (
                "Use only the terrain master thin gold border and compass; title in bottom-left."
            )
        jobs.append(
            dict(
                file=entry["file"],
                id=pid,
                prompt=prompt,
                references=[baseline(entry["file"]), str(master)],
                status="pending",
            )
        )
    previous = (
        {j["file"]: j for j in read(WORK / "generation-jobs.json")}
        if (WORK / "generation-jobs.json").exists()
        else {}
    )
    for job in jobs:
        if job["file"] in previous:
            for key in ("status", "output", "sha256"):
                if key in previous[job["file"]]:
                    job[key] = previous[job["file"]][key]
    # Latest author decision: every single-interior building has two full-frame maps.
    buildings = read(CAPITAL / "atlas.json")["maps"]
    architecture = {
        r["id"]: r for r in read(ROOT / "Source/Elements/Maps/architectures.json")["records"]
    }
    jobs = [j for j in jobs if not j["file"].startswith("capital/images/")]
    for building in buildings:
        pid = building["id"]
        if pid not in architecture:
            continue
        record = architecture[pid]
        shell = dict(parts=record["parts"], holes=record["holes"], features=record["features"])
        common = (
            "Use case: precise-object-edit. Image 1 is the existing building architecture; "
            "image 2 is the AUTHOR ABSOLUTE URBAN STYLE MASTER, style only. "
            "Exact 1536x1024 landscape, ONE SINGLE full-frame map, NEVER a diptych. "
            "Match the master painted miniature facture, high oblique camera, warm clean "
            "light, materials and sober parchment cartouches. Preserve the existing "
            "building silhouette, wings, domes, towers, roof forms, entrances and orientation, "
            "and the SAME dry neighborhood context. NO added water, canal, river, coast, "
            "boats, bridges, structures, monuments, sculpture, towers, rooms or floors. "
            "Painting fills all four edges. No decorative outer border, foliage ornament, "
            "parchment mat, bottom band, inset, ghost roof, wireframe, production annotation, "
            "arrow, compass, human figure or watermark. NO room names, room labels, numbers "
            "or legend. NO proposé/proposée/proposés/proposées/proposed anywhere. "
            "Only a compact plain parchment title top-left. "
            "Architectural envelope: " + record["description"] + "\n"
            "Graphic construction data (unitless, never print): " + json.dumps(shell) + "\n"
        )
        if pid == "illu-die-arena":
            common += "AUTHOR: RED roofs as in Martpart and Capital, modest radial street entrance, no monumental Coliseum facade.\n"
        for view in ("exterior", "interior"):
            target = f"capital/images/{pid}{'-interior' if view == 'interior' else ''}.png"
            label = "Intérieur" if view == "interior" else "Extérieur"
            prompt = common + f"ONLY TEXT, exact: '{building['title']} · {label}'. "
            prompt += (
                "Show only the complete roofless access-level interior, same outer shell and "
                "street entrance as the original, no extra floor or exterior inset. "
                "Use the original right interior panel arrangement, not a new layout."
                if view == "interior"
                else "Show only the complete exterior with all roofs closed. Use the original "
                "left exterior panel. No cutaway, no interior inset or panel."
            )
            jobs.append(
                dict(
                    file=target,
                    id=pid,
                    view=view,
                    prompt=prompt,
                    references=[baseline(f"capital/images/{pid}.png"), str(URBAN_MASTER)],
                    status="pending",
                )
            )
    extras = {
        "central-empire-the-capital-city-neckoffoods": (
            "capital/images/neckoffoods.png",
            "Agricultural suburb outside the city walls beneath Scholarnest and Dweomer ONLY; "
            "remove Uptown and Tamera Gate. Wildlife Gate must sit on the wall. Braves Arena is "
            "a small wooden oval near Farmer’s Market and Old Goat Tavern. Preserve fields and "
            "farms. Only established catalogue labels, no The Crops label.",
        ),
        "magocracy-of-mage-tower-mesoriver": (
            "world/magocracy-of-mage-tower-mesoriver.png",
            "Author requests ground context: show the existing river and forested plain below "
            "the floating islands, matching the regional parent. Keep existing levitating "
            "towers and castles. Label Floating Islands on the already framed northeastern "
            "island group; no extra island groups or names.",
        ),
        "kingdom-of-kolbjorn-kolbjorn-capital": (
            "world/kingdom-of-kolbjorn-kolbjorn-capital.png",
            "Preserve the city exactly, add the existing children parchment labels: Ygfall "
            "Fortress (upper central rock), Shipyards (left shipyards), Imperial District "
            "(lower-right walled quarter).",
        ),
        "theocracy-of-kepesh-pakaitos-the-new-capital": (
            "world/theocracy-of-kepesh-pakaitos-the-new-capital.png",
            "Preserve the city exactly, add the existing children parchment labels: Pyramids "
            "and Temples of Ba-Ka (central pyramids), Outer Rings (outer concentric city rings).",
        ),
        "tsvetan-feargus-the-capital": (
            "world/tsvetan-feargus-the-capital.png",
            "Preserve the city exactly, add the existing children parchment labels: Vharzog’s "
            "Palace (upper right golden domes), City Arena (central-left oval arena).",
        ),
    }
    for pid, (target, brief) in extras.items():
        plate = catalog["plates"][pid]
        prompt = (
            "Use case: precise-object-edit. Single full-frame original game atlas map, "
            "exact 1536x1024 landscape. Image 1 is the edit target; image 2 is the "
            "absolute URBAN STYLE master, style only. Match its painted miniature "
            "facture, camera and sober parchment labels, no border, no decorative "
            "parchment mat or bottom band, no icons, figures, ornaments, schematic "
            "insets, production notes, watermarks or unsupported structures. "
            "Keep all established geography and architecture except the explicit "
            "corrections. No proposed/proposé/proposée/proposés/proposées text. "
            "Exact title: " + plate["name"] + ". " + brief
        )
        jobs.append(
            dict(
                id=pid,
                file=target,
                prompt=prompt,
                references=[baseline(target), str(URBAN_MASTER)],
                status="pending",
            )
        )
    for job in jobs:
        if job["file"] in previous:
            for key in ("status", "output", "sha256"):
                if key in previous[job["file"]]:
                    job[key] = previous[job["file"]][key]
    write(WORK / "generation-jobs.json", jobs)
    print(f"{len(entries)} audit entries; {len(jobs)} illustration jobs prepared.")


# Author-supplied graphic windows. They locate children on the unchanged parent image;
# frame of a child is otherwise its own image's crop and MUST NOT be repurposed.
CAPITAL_WINDOWS = {
    "arena-of-fate": [0.35, 0.11, 0.21, 0.26],
    "hippodrome": [0.60, 0.43, 0.27, 0.40],
    "golden-chalice": [0.34, 0.56, 0.22, 0.19],
    "dusk-of-justice": [0.40, 0.36, 0.12, 0.12],
    "the-vault": [0.44, 0.15, 0.14, 0.18],
    "cathedral-eight": [0.62, 0.32, 0.20, 0.32],
    "municipal-palace": [0.43, 0.31, 0.15, 0.20],
    "sara-hospital": [0.23, 0.49, 0.17, 0.16],
    "torygg-tower": [0.13, 0.08, 0.17, 0.38],
    "wizards-headquarters": [0.67, 0.35, 0.19, 0.29],
    "omathyr-manor": [0.49, 0.21, 0.15, 0.20],
    "illu-die-arena": [0.52, 0.50, 0.20, 0.25],
    "municipal-market": [0.44, 0.27, 0.18, 0.20],
    "cemetery-moon-tower": [0.34, 0.06, 0.39, 0.20],
    "imperial-palace": [0.40, 0.08, 0.25, 0.24],
    "ironhand-headquarters": [0.54, 0.54, 0.23, 0.17],
    "wicar-war-school": [0.52, 0.66, 0.22, 0.18],
    "tamera-temple": [0.40, 0.55, 0.12, 0.20],
    "capital-portals": [0.25, 0.55, 0.12, 0.14],
    "imperial-university": [0.21, 0.42, 0.26, 0.27],
    "imperial-museum": [0.21, 0.15, 0.19, 0.18],
    "baleroth-library": [0.62, 0.38, 0.11, 0.17],
}


def apply_data():
    document = read(CATALOG)
    plates = document["plates"]
    changes = []
    for pid, window in CAPITAL_WINDOWS.items():
        if pid in plates:
            plates[pid]["parentFrame"] = window
            plates[pid]["parentFrameBasis"] = (
                "Author visual audit, 7 October 2026; window on parent illustration."
            )
            changes.append(pid)
    plates["catacombs"]["at"] = [0.59, 0.10]
    # A level change is explicit navigation; the sand is not a staircase.
    plates["arena-of-fate"]["links"] = list(
        dict.fromkeys(plates["arena-of-fate"].get("links", []) + ["undercroft"])
    )
    plates["mystical"]["at"] = [0.78, 0.64]
    plates["stravian-domains-dorsian-forge"]["at"] = [0.85, 0.15]
    for pid in ("darkall", "undertanares"):
        plates["world"]["links"] = list(dict.fromkeys(plates["world"].get("links", []) + [pid]))
    # Darkall and Undertanares have no attested point on the world illustration.
    # Keep stable identifiers: the Dorsian historical prefix is not a parent relation.
    for _pid, plate in plates.items():
        if plate["name"] in ("Shredded Coast", "The Ice Coast") and plate.get("parent") == "world":
            plate.pop("frame", None)
            plate["frameBasis"] = "World context only; coastline extent not established."
    for name, point in [
        ("Bluhaven, the Capital", [0.43, 0.56]),
        ("Mustardseed", [0.58, 0.58]),
        ("Pearl Town", [0.25, 0.57]),
        ("The Whirlpool", [0.58, 0.70]),
        ("Uncle Joe’s Tavern", [0.21, 0.65]),
    ]:
        for pid, p in plates.items():
            if p["parent"] == "seashores" and p["name"].replace("'", "’") == name.replace("'", "’"):
                p["at"] = point
                changes.append(pid)
    for name, point in [
        ("Begraense", [0.37, 0.62]),
        ("Crystal Mountains", [0.65, 0.21]),
        ("Mistvale", [0.87, 0.45]),
    ]:
        for pid, p in plates.items():
            if p["parent"] == "imperial-benenet" and p["name"] == name:
                p["at"] = point
                changes.append(pid)
    for _pid, p in plates.items():
        if p["name"] == "Irongauntlet" and p["parent"] == "kingdom-of-kolbjorn":
            p["at"] = [0.36, 0.75]
    dark_windows = {
        "darkall-north": [0.10, 0, 0.80, 0.27],
        "darkall-central": [0.10, 0.27, 0.80, 0.29],
        "darkall-demonic-lands": [0.05, 0.56, 0.90, 0.44],
    }
    for pid, window in dark_windows.items():
        if pid in plates:
            plates[pid]["frame"] = window
            plates[pid]["frameBasis"] = (
                "Author audit bands with adjacent, non-overlapping boundaries."
            )
            changes.append(pid)
    for plate in plates.values():
        plate["name"] = display_text(plate["name"])
        plate["description"] = display_text(plate.get("description", ""))
        plate["description"] = plate["description"].replace(
            " Le panneau intérieur est une proposition à valider.", ""
        )
        for layer in plate.get("layers", []):
            layer["name"] = display_text(layer["name"])
        short_labels = {
            "Wallside District": "Wallside",
            "Seabreeze District": "Seabreeze",
            "The Cerulean Plaza": "Cerulean Plaza",
            "The Arena of Future": "Arena of Future",
            "Celestianist Cathedral of Sun and Moon": "Cathedral of Sun and Moon",
        }
        if (
            plate.get("parent") == "republic-of-freelands-fisherman-s-wharf"
            and plate["name"] in short_labels
        ):
            plate["aliases"] = list(
                dict.fromkeys(plate.get("aliases", []) + [short_labels[plate["name"]]])
            )
    if "vtt-winter-hold" in plates:
        plates["vtt-winter-hold"]["aliases"] = list(
            dict.fromkeys(plates["vtt-winter-hold"].get("aliases", []) + ["Winter Hold City"])
        )
        plates["vtt-winter-hold"]["name"] = "The Winterhold City"
    write(CATALOG, document)
    registry_path = ROOT / "Source/Elements/Maps/architectures.json"
    if registry_path.exists():
        registry = read(registry_path)
        for record in registry["records"]:
            for room in record.get("rooms", []):
                room["label"] = display_text(room["label"])
            for key in ("source", "description", "floors"):
                if isinstance(record.get(key), str):
                    record[key] = display_text(record[key])
        write(registry_path, registry)
    write(
        WORK / "data-changes.json",
        dict(date=DATE, updated=changes, awaitingIllustrationRegistration=True),
    )
    print(f"{len(changes)} graphic windows and child positions updated.")


def ocr_candidates():
    """Read labels on each *own parent*, never borrow a point from a neighboring region."""
    tess = Path("C:/Program Files/PDF24/tesseract/tesseract.exe")
    catalog = read(CATALOG)["plates"]
    images = {
        p["image"].removeprefix("Maps/"): pid
        for pid, p in catalog.items()
        if not p.get("frame") and p["image"].startswith("Maps/world/")
    }
    output = []
    for relative, pid in images.items():
        source = WORK / relative
        if not source.is_file():
            continue
        dest = WORK / "ocr" / source.stem
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                str(tess),
                str(source),
                str(dest),
                "--tessdata-dir",
                str(ROOT / "Tools/WorldAtlas20261005"),
                "-l",
                "eng",
                "--psm",
                "11",
                "-c",
                "tessedit_create_tsv=1",
            ],
            check=True,
            capture_output=True,
        )
        groups = {}
        tokens = []
        with dest.with_suffix(".tsv").open(encoding="utf-8") as stream:
            for row in csv.DictReader(stream, delimiter="\t", quoting=csv.QUOTE_NONE):
                if row["level"] != "5" or float(row["conf"]) < 25 or not row["text"].strip():
                    continue
                key = (row["block_num"], row["par_num"])
                groups.setdefault(key, []).append(row)
                tokens.append(row)
        labels = []
        for rows in groups.values():
            left = min(int(r["left"]) for r in rows)
            top = min(int(r["top"]) for r in rows)
            right = max(int(r["left"]) + int(r["width"]) for r in rows)
            bottom = max(int(r["top"]) + int(r["height"]) for r in rows)
            labels.append(
                dict(
                    text=" ".join(r["text"] for r in rows),
                    at=[
                        round((left + right) / (2 * SIZE[0]), 6),
                        round((top + bottom) / (2 * SIZE[1]), 6),
                    ],
                )
            )
        for child_id, child in catalog.items():
            if child["parent"] != pid:
                continue
            matches = []
            for label in labels:
                score = difflib.SequenceMatcher(
                    None, normalized(child["name"]), normalized(label["text"])
                ).ratio()
                if score >= 0.84:
                    matches.append(dict(**label, score=round(score, 4)))
            # Sparse-text OCR can split a multi-line plaque into independent blocks.
            # Distinctive words produce review candidates only, never an automatic change.
            common = set(
                "the of city forest lake town mountains mountain island islands coast range valley fields ruins fortress temple site sea archipelago village great north south west east eastern western central old true bridge passing hall port capital depths outskirts river".split()
            )
            significant = [
                w for w in normalized(child["name"]).split() if w not in common and len(w) > 3
            ]
            if not matches and significant:
                for token in tokens:
                    value = normalized(token["text"])
                    score = max(
                        difflib.SequenceMatcher(None, w, value).ratio() for w in significant
                    )
                    if score >= 0.9:
                        at = [
                            round((int(token["left"]) + int(token["width"]) / 2) / SIZE[0], 6),
                            round((int(token["top"]) + int(token["height"]) / 2) / SIZE[1], 6),
                        ]
                        matches.append(
                            dict(
                                text=token["text"],
                                at=at,
                                score=round(score, 4),
                                method="distinctive-word",
                            )
                        )
            matches.sort(key=lambda m: m["score"], reverse=True)
            output.append(dict(id=child_id, parent=pid, name=child["name"], candidates=matches[:3]))
        print(f"{pid}: {len(labels)} label blocks read.", flush=True)
    write(WORK / "registration-candidates.json", output)
    print(
        f"{len(output)} children checked; {sum(bool(r['candidates']) for r in output)} label matches for visual review."
    )


def register():
    """Install visually checked registration records; no automatic fuzzy match approval."""
    document = read(CATALOG)
    for row in read(WORK / "approved-registration.json"):
        child = document["plates"][row["id"]]
        if child["parent"] != row["parent"]:
            raise ValueError("Registration belongs to a different parent")
        parent = document["plates"][row["parent"]]
        source = WORK / parent["image"].removeprefix("Maps/")
        if not source.is_file():
            source = ASSETS / parent["image"].removeprefix("Maps/")
        if (
            row.get("sourceSha256")
            and hashlib.sha256(source.read_bytes()).hexdigest() != row["sourceSha256"]
        ):
            raise ValueError("Illustration changed after visual registration")
        if child["image"] == parent["image"] or child["kind"] == "geographic":
            child["image"] = parent["image"]
            child["layers"] = [dict(id="illustration", name="Carte", image=parent["image"])]
            child["frame"] = row["frame"] if "frame" in row else frame(row["at"])
        elif "parentFrame" in row:
            child["parentFrame"] = row["parentFrame"]
        else:
            child["at"] = row["at"]
        child["frameBasis"] = (
            "Label visually checked on its own parent illustration, 7 October 2026."
        )
    write(CATALOG, document)
    report_path = WORK / "data-changes.json"
    if report_path.exists():
        report = read(report_path)
        report.update(
            awaitingIllustrationRegistration=False,
            registeredViews=len(read(WORK / "approved-registration.json")),
        )
        write(report_path, report)


def load_architecture():
    spec = importlib.util.spec_from_file_location(
        "audit_capital_architecture", CAPITAL / "architecture.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def corrected_models(architecture, maps):
    models = architecture.MODELS
    models["illu-die-arena"]["features"] = [["roof", "burgundy"]]
    models["illu-die-arena"]["description"] = models["illu-die-arena"]["description"].replace(
        "bleu-violet", "rouges"
    )
    market = models["municipal-market"]
    market["parts"] = [["rect", 14, 33, 72, 30]]
    market["roomSeeds"] = [(19, 48), (45, 48), (54, 39), (76, 55)]
    cemetery = models["cemetery-moon-tower"]
    cemetery["roomSeeds"][2:4] = [(34, 36), (34, 24)]
    palace = models["imperial-palace"]
    palace["roomSeeds"] = [(28, 74), (28, 66), (50, 27), (27, 48), (50, 60)]
    tamera = models["tamera-temple"]
    tamera["parts"] += [["ellipse", 20, 62, 18, 18], ["ellipse", 62, 62, 18, 18]]
    # Parvis touches the front threshold instead of becoming a broad lateral rectangle.
    tamera["roomSeeds"][0] = (50, 94)
    portals = models["capital-portals"]
    portals["description"] = portals["description"].replace(
        "Cour centrale circulaire", "Cour centrale carrée"
    )
    for m in maps:
        if m["id"] == "docks":
            m["landmarks"] = [p for p in m.get("landmarks", []) if p["name"] != "Docks District"]
        if m["id"] == "downtown":
            for p in m["landmarks"]:
                if p["name"] == "Heartmountain Jewelry":
                    p["at"] = [54, 57]
                if p["name"] == "Ertugrul Place":
                    p["at"] = [59, 57]
            x, y, w, h = m["frame"]
            m["frame"] = [x, min(y, 34), w, h + y - min(y, 34)]
        if m["id"] == "palacedomain":
            x, y, w, h = m["frame"]
            m["frame"] = [18, y, w + x - 18, h]
            for p in m["landmarks"]:
                if p["name"] == "Grove of Hope":
                    p["at"] = [19, 59]
                if p["name"] == "Governor’s Square" or p["name"] == "Governor's Square":
                    p["at"] = [23, 56]
        if m["id"] == "oldtown":
            # Tower belongs to the combined cemetery footprint; retain its catalogue name.
            m["landmarks"] = [p for p in m["landmarks"] if p["name"] != "Moon Tower"]


def fit_label(draw, pos, label, size=18, anchor="la", box=(28, 132, 1508, 928)):
    ft = font(size)
    bounds = draw.textbbox(pos, label, font=ft, anchor=anchor)
    x, y = pos
    if bounds[0] < box[0]:
        x += box[0] - bounds[0]
    if bounds[2] > box[2]:
        x -= bounds[2] - box[2]
    if bounds[1] < box[1]:
        y += box[1] - bounds[1]
    if bounds[3] > box[3]:
        y -= bounds[3] - box[3]
    draw.text((x, y), label, font=ft, fill=INK, anchor=anchor, stroke_width=2, stroke_fill=PAPER)


def draw_district(m, maps, architecture):
    canvas = Image.new("RGB", SIZE, PAPER)
    terrain = Image.new("RGB", SIZE, PAPER)
    d = ImageDraw.Draw(terrain)
    if m["kind"] == "quartier":
        x, y, w, h = m["frame"]
        vx, vy, vw, vh = x - 1, y - 1, w + 2, h + 2
        points = [p["at"] for p in m.get("landmarks", [])]
        if points:
            right = max(vx + vw, max(p[0] for p in points) + 2)
            bottom = max(vy + vh, max(p[1] for p in points) + 2)
            vx = min(vx, min(p[0] for p in points) - 2)
            vy = min(vy, min(p[1] for p in points) - 2)
            vw, vh = right - vx, bottom - vy
    else:
        vx, vy, vw, vh = 0, 0, 100, 100
    legend_rows = (len(m.get("landmarks", [])) + 1) // 2 if m["kind"] == "quartier" else 0
    plot_bottom = 900 - legend_rows * 25

    def pt(x, y):
        return 40 + (x - vx) * 1456 / vw, 140 + (y - vy) * (plot_bottom - 140) / vh

    d.polygon(
        [
            pt(0, 0),
            pt(54, 0),
            pt(47, 14),
            pt(28, 22),
            pt(22, 34),
            pt(14, 53),
            pt(12, 74),
            pt(8, 100),
            pt(0, 100),
        ],
        fill="#2f7f86",
    )
    d.line(
        [pt(*p) for p in [(46, 11), (58, 15), (71, 23), (80, 31), (91, 36), (100, 38)]],
        fill="#2f7f86",
        width=20,
    )
    d.line([pt(*p) for p in WALL], fill="#817157", width=6)
    d.line(
        [
            pt(*p)
            for p in [
                (28, 34),
                (37, 32),
                (45, 42),
                (47, 56),
                (43, 66),
                (29, 65),
                (25, 54),
                (26, 40),
                (28, 34),
            ]
        ],
        fill="#c9a45c",
        width=4,
    )
    for a, b, c, e in [(65, 18, 70, 13), (87, 45, 91, 34), (95, 37, 97, 33), (8, 79, 15, 77)]:
        d.line([pt(a, b), pt(c, e)], fill="#c9a45c", width=8)
    for _name, x, y in GATES:
        u, v = pt(x, y)
        d.rectangle((u - 6, v - 6, u + 6, v + 6), fill="#8e2335")
    if m["kind"] == "quartier":
        x, y, w, h = m["frame"]
        d.rectangle((*pt(x, y), *pt(x + w, y + h)), outline="#8e2335", width=3)
    canvas.paste(terrain.crop((20, 130, 1516, plot_bottom + 15)), (20, 130))
    d = ImageDraw.Draw(canvas)
    # Long place names are keyed in a side legend rather than colliding with footprints.
    for other in maps:
        if other["kind"] != "quartier":
            continue
        if m["id"] == "capital":
            x, y, w, h = other["frame"]
            fit_label(d, pt(x + w / 2, y + h / 2), other["title"], 18, anchor="mm")
        if other["id"] != m["id"] and m["id"] != "capital":
            pos = pt(*other["center"]) if "center" in other else None
            if pos and 35 < pos[0] < 1500 and 135 < pos[1] < 920:
                fit_label(d, pos, other["title"], 16, anchor="mm")
            continue
        for i, p in enumerate(other.get("landmarks", []), 1):
            u, v = pt(*p["at"])
            if not 20 < u < 1516 or not 130 < v < 930:
                continue
            matching = next(
                (
                    site
                    for site in maps
                    if site.get("parent") == other["id"]
                    and (
                        site["title"] == p["name"]
                        or site["id"] == "cemetery-moon-tower"
                        and p["name"] == "Cemetery of Sacred Remembrance"
                    )
                ),
                None,
            )
            if matching and matching["id"] in architecture.MODELS:
                architecture.stamp(d, matching["id"], u, v, 72 if m["kind"] == "quartier" else 30)
                footprint = True
            elif p["name"] == "Arena of Fate":
                r = 36 if m["kind"] == "quartier" else 14
                d.ellipse(
                    (u - r, v - r * 0.7, u + r, v + r * 0.7), fill="#ab785d", outline=INK, width=2
                )
                footprint = True
            else:
                footprint = False
            if m["id"] == "capital":
                if footprint:
                    fit_label(d, (u + 20, v + 20), p["name"], 17)
                continue
            # Numbers sit outside drawn silhouettes and remain inside the review frame.
            u = max(45, min(1480, u + (50 if footprint else 0)))
            v = max(145, min(910, v + 20 if footprint else v))
            d.ellipse((u - 13, v - 13, u + 13, v + 13), fill="#8e2335", outline=PAPER, width=2)
            d.text((u, v), str(i), font=font(17), fill="white", anchor="mm")
    # Titles are drawn last on a reserved band, with no water or wall beneath them.
    d.text((35, 20), m["title"], font=font(32), fill=INK)
    d.text(
        (35, 70),
        "Implantations relatives · Ouest en haut / Nord à droite · sans échelle métrique",
        font=font(18),
        fill=INK,
    )
    d.rectangle((22, 940, 1514, 1020), fill=PAPER)
    for i, (label, color, shape) in enumerate(
        [
            ("Lieu", "#8e2335", "circle"),
            ("Porte", "#8e2335", "square"),
            ("Enceinte", "#817157", "line"),
            ("Enclos / pont", "#c9a45c", "line"),
        ]
    ):
        x = 35 + i * 285
        if shape == "circle":
            d.ellipse((x, 947, x + 14, 961), fill=color)
        elif shape == "square":
            d.rectangle((x, 947, x + 14, 961), fill=color)
        else:
            d.line((x, 954, x + 24, 954), fill=color, width=5)
        d.text((x + 30, 941), label, font=font(18), fill=INK)
    if m["kind"] == "quartier":
        items = [f"{i} · {p['name']}" for i, p in enumerate(m.get("landmarks", []), 1)]
        # A separate legend panel replaces unused map area, at a minimum 17px text size.
        rows = (len(items) + 1) // 2
        height = rows * 25 + 16
        d.rounded_rectangle(
            (35, 925 - height, 1498, 925), radius=5, fill=PAPER, outline="#b59555", width=2
        )
        for i, item in enumerate(items):
            d.text(
                (50 + (i // rows) * 730, 933 - height + (i % rows) * 25),
                item,
                font=font(17),
                fill=INK,
            )
    path = WORK / "capital/plans" / f"{m['id']}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def draw_building(m, model, architecture):
    # Use identical construction masks for the registry and both exported layers.
    image = Image.new("RGB", SIZE, PAPER)
    d = ImageDraw.Draw(image)
    d.text((35, 20), m["title"] + " · plan intérieur", font=font(26), fill=INK)
    d.text((35, 65), "Niveau d’accès · proportions graphiques sans cotes", font=font(18), fill=INK)

    def pt(x, y):
        return 240 + x * 8, 120 + y * 8

    for x, y in model["walk"]:
        color = "#d5cfb9" if (x, y) not in model["body"] else architecture.STONE
        d.polygon([pt(x, y), pt(x + 1, y), pt(x + 1, y + 1), pt(x, y + 1)], fill=color)
    architecture.outline(d, model["body"], pt, 3)
    out = WORK / "capital/plans"
    out.mkdir(parents=True, exist_ok=True)
    image.save(out / f"{m['id']}-interieur.png")
    image = Image.new("RGB", SIZE, PAPER)
    d = ImageDraw.Draw(image)
    d.text((35, 20), m["title"], font=font(28), fill=INK)
    d.text((35, 65), "Extérieur et coupe · même enveloppe graphique", font=font(18), fill=INK)
    architecture.volume(d, model, 420, 220, s=5.6)

    # Development volume view keeps the same envelope, without room labels.
    def ax(x, y):
        return 1175 + (x - y) * 5.6 * 0.8, 240 + (x + y) * 5.6 * 0.38

    for x, y in model["walk"]:
        d.polygon(
            [ax(x, y), ax(x + 1, y), ax(x + 1, y + 1), ax(x, y + 1)],
            fill=architecture.STONE if (x, y) in model["body"] else "#d5cfb9",
        )
    architecture.outline(d, model["body"], ax, 3)
    image.save(out / f"{m['id']}-architecture.png")


def draw_lower_level(pid):
    """Replay primitives; clip full wall rectangles to the shared oval envelope."""
    spec = importlib.util.spec_from_file_location(
        "audit_arena_levels", ROOT / "scripts/maps/arena_fate_levels.py"
    )
    levels = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(levels)
    construction, _ = getattr(levels, pid)()
    canvas = Image.new("RGB", SIZE, PAPER)
    floor = Image.new("RGB", SIZE, "#d9c7a3")
    d = ImageDraw.Draw(floor)
    sx, sy = 38 * SIZE[0] / 1800, 38 * SIZE[1] / 1260
    ox, oy = 250 * SIZE[0] / 1800, 190 * SIZE[1] / 1260

    def box(x, y, w=1, h=1):
        return ox + x * sx, oy + y * sy, ox + (x + w) * sx, oy + (y + h) * sy

    ellipse = box(2, 1, 30, 22)
    mask = Image.new("L", SIZE, 0)
    ImageDraw.Draw(mask).ellipse(ellipse, fill=255)
    for x, y in construction.walls:
        if levels.inside(x, y):
            d.rectangle(box(x, y), fill="#6c5e52")
    for _, piece, x, y in construction.pieces:
        if any(word in piece for word in ("bench", "rack", "table")):
            d.rounded_rectangle(box(x + 0.15, y + 0.2, 1.45, 0.45), radius=3, fill="#987951")
    canvas.paste(floor, (0, 0), mask)
    d = ImageDraw.Draw(canvas)
    d.ellipse(ellipse, outline="#6c5e52", width=10)
    d.ellipse(ellipse, outline="#b59555", width=3)
    title = {
        "undercroft": "Vestiaires et prison · niveau −1",
        "catacombs": "Catacombes cultistes · niveau −2",
    }[pid]
    d.text((48, 28), title, font=font(30), fill=INK)
    for letter, x, y in [("T", 3, 11.5), ("M", 30, 11.5), ("P", 16.5, 21), ("C", 22.5, 5)]:
        active = pid == "undercroft" or letter == "C"
        u, v = ox + (x + 0.5) * sx, oy + (y + 0.5) * sy
        d.ellipse(
            (u - 11, v - 11, u + 11, v + 11),
            fill="#8e2335" if active else PAPER,
            outline="#8e2335",
            width=2,
        )
        d.text((u, v), letter, font=font(14), anchor="mm", fill=PAPER if active else INK)
    if pid == "undercroft":
        d.rectangle((48, 942, 74, 954), fill="#987951")
        d.text((85, 935), "Bancs, tables et rangements", font=font(18), fill=INK)
    else:
        d.text((48, 935), "Repères creux : projection sans accès", font=font(18), fill=INK)
    d.rectangle((415, 936, 433, 954), fill="#6c5e52")
    d.text((445, 935), "Murs", font=font(18), fill=INK)
    d.text(
        (48, 977),
        "T : triomphe · M : morts · P : parvis · C : descente des catacombes",
        font=font(18),
        fill=INK,
    )
    destination = WORK / "capital/plans" / f"{pid}.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination)


def plans():
    atlas = read(CAPITAL / "atlas.json")
    maps = atlas["maps"]
    architecture = load_architecture()
    corrected_models(architecture, maps)
    registry = read(ROOT / "Source/Elements/Maps/architectures.json")
    records = {r["id"]: r for r in registry["records"]}
    targets = set(architecture.MODELS)
    for m in maps:
        if m["id"] not in architecture.MODELS:
            continue
        model = architecture.prepare(m)
        if m["id"] == "tamera-temple":
            # Bound the approach to a narrow front apron and the courtyard to the shell.
            model["walk"] = {
                p
                for p in model["walk"]
                if p in model["body"]
                or 33 <= p[0] <= 66
                and 33 <= p[1] <= 56
                or 40 <= p[0] <= 60
                and 90 <= p[1] <= 96
            }
            # Public and service routes branch at the threshold and stay disjoint thereafter.
            service = set()
            for i, p in enumerate(model["seeds"]):
                if model["serviceRooms"][i]:
                    service_area = {
                        p for p in model["body"] if p[1] <= 33 or p[0] <= 32 or p[0] >= 67
                    }
                    route = architecture.path(
                        architecture.nearest(model["serviceEntry"], service_area), p, service_area
                    )
                    if not route:
                        raise ValueError("Unreachable Tamera service room")
                    model["routes"][i] = route
                    service.update(route)
            for i, p in enumerate(model["seeds"]):
                if not model["serviceRooms"][i]:
                    route = architecture.path(
                        architecture.nearest(model["entry"], model["walk"]),
                        p,
                        model["walk"] - (service - {p, tuple(model["entry"])}),
                    )
                    if not route:
                        raise ValueError("Public Tamera route crosses service circulation")
                    model["routes"][i] = route
        if m["id"] not in targets:
            continue
        draw_building(m, model, architecture)
        record = records[m["id"]]
        record.update(
            parts=model["parts"],
            holes=model["holes"],
            features=model["features"],
            description=model["description"],
            footprintHash=model["hash"],
            rooms=[
                dict(label=display_text(n), anchor=list(p), exterior=o)
                for n, p, o in zip(m["proposedRooms"], model["seeds"], model["outside"])
            ],
        )
        runs = []
        for y in range(100):
            x = 0
            while x < 100:
                owner = model["owners"].get((x, y))
                if owner is None:
                    x += 1
                    continue
                start = x
                while x < 100 and model["owners"].get((x, y)) == owner:
                    x += 1
                runs.append([owner + 1, y, start, x])
        record["traces"] = dict(
            id=m["id"],
            parts=model["parts"],
            holes=model["holes"],
            roomRuns=runs,
            roomRunConvention="numéro de salle, ligne Y, début X inclus, fin X exclue",
            routes=[
                dict(room=i + 1, service=model["serviceRooms"][i], path=route)
                for i, route in enumerate(model["routes"])
            ],
            footprintHash=model["hash"],
        )
    registry["date"] = DATE
    write(ROOT / "Source/Elements/Maps/architectures.json", registry)
    write(WORK / "capital/atlas.json", atlas)
    for m in maps:
        if m["kind"] in ("quartier", "ensemble"):
            draw_district(m, maps, architecture)
    for pid in ("undercroft", "catacombs"):
        draw_lower_level(pid)
    print("Native 1536x1024 district and corrected building plans exported.")


def receive(target, source):
    source = Path(source)
    with Image.open(source) as im:
        if im.size != SIZE:
            raise ValueError(f"{target}: {im.size}, expected {SIZE}")
    destination = WORK / target
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    jobs = read(WORK / "generation-jobs.json")
    for job in jobs:
        if job["file"] == target:
            job["status"] = "received"
            job["output"] = str(source)
            job["sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
    write(WORK / "generation-jobs.json", jobs)
    job = next((j for j in jobs if j["file"] == target), {})
    actual = WORK / "requests" / (target.replace("/", "--") + ".json")
    if actual.exists():
        job = {**job, **read(actual)}
    write(
        WORK / "records" / (target.replace("/", "--") + ".json"), dict(job=job, source=str(source))
    )
    print(f"Received {target}.")


def install():
    manifest = read(ASSETS / "manifest.json")
    index = {m["file"]: m for m in manifest["maps"]}
    catalog = read(CATALOG)
    new_interiors = []
    for source in (WORK / "capital/images").glob("*-interior.png"):
        pid = source.stem.removesuffix("-interior")
        target = source.relative_to(WORK).as_posix()
        if target not in index:
            entry = copy.deepcopy(index[f"capital/images/{pid}.png"])
            entry["file"] = target
            entry["level"] = "interior"
            manifest["maps"].append(entry)
            index[target] = entry
        plate = catalog["plates"][pid]
        old_images = [layer["image"] for layer in plate["layers"] if layer["id"] == "interior"]
        plate["layers"] = [layer for layer in plate["layers"] if layer["id"] != "interior"]
        for layer in plate["layers"]:
            if layer["id"] == "illustration":
                layer["name"] = "Extérieur"
        plate["layers"].insert(1, dict(id="interior", name="Intérieur", image="Maps/" + target))
        new_interiors.extend(old_images)
    copied = []
    for source in WORK.rglob("*.png"):
        target = source.relative_to(WORK).as_posix()
        if (
            target not in index
            or target.startswith("capital/plans/")
            and target.endswith("-interieur.png")
        ):
            continue
        with Image.open(source) as im:
            if im.size != SIZE:
                raise ValueError(f"Non-native plan: {target}")
        shutil.copy2(source, ASSETS / target)
        data = source.read_bytes()
        index[target].update(
            sha256=hashlib.sha256(data).hexdigest(),
            size=list(SIZE),
            bytes=len(data),
            source=source.relative_to(ROOT).as_posix(),
            date=DATE,
        )
        copied.append(target)
    used = {p["image"] for p in catalog["plates"].values()}
    used.update(layer["image"] for p in catalog["plates"].values() for layer in p.get("layers", []))
    for obsolete in new_interiors:
        if obsolete not in used:
            relative = obsolete.removeprefix("Maps/")
            path = ASSETS / relative
            if path.resolve().is_relative_to(ASSETS.resolve()) and path.is_file():
                path.unlink()
            manifest["maps"] = [entry for entry in manifest["maps"] if entry["file"] != relative]
    write(ASSETS / "manifest.json", manifest)
    # Refresh footprint references from the registry after changing graphic envelopes.
    architecture = read(ROOT / "Source/Elements/Maps/architectures.json")
    for record in architecture["records"]:
        if record["id"] in catalog["plates"]:
            catalog["plates"][record["id"]]["footprint"] = record["footprintHash"]
    write(CATALOG, catalog)
    write(WORK / "delivery.json", dict(date=DATE, installed=copied))
    print(f"{len(copied)} replacement images installed with updated hashes.")


def gallery():
    """Show the final native illustrations, paired buildings and corrected plans."""
    jobs = read(WORK / "generation-jobs.json")
    plates = read(CATALOG)["plates"]
    for job in jobs:
        record = read(WORK / "records" / (job["file"].replace("/", "--") + ".json"))
        final = WORK / job["file"]
        actual = record["job"]
        digest = hashlib.sha256(final.read_bytes()).hexdigest()
        if actual["sha256"] != digest:
            raise ValueError("Receipt no longer matches selected image")
        job.update(actual, status="received")
    write(WORK / "generation-jobs.json", jobs)
    write(
        WORK / "final-selection.json",
        dict(
            date=DATE,
            images=[dict(file=j["file"], source=j["output"], sha256=j["sha256"]) for j in jobs],
        ),
    )

    def picture(file, caption):
        safe = html.escape(file, quote=True)
        return f'<figure><a href="{safe}" target="_blank"><img loading="lazy" src="{safe}" alt="{html.escape(caption)}"></a><figcaption>{html.escape(caption)}</figcaption></figure>'

    groups = []
    paired = set()
    for job in jobs:
        file = job["file"]
        if file in paired:
            continue
        name = plates.get(job["id"], {}).get("name", job["id"])
        interior = file.removesuffix(".png") + "-interior.png"
        if file.startswith("capital/images/") and (WORK / interior).is_file():
            content = picture(file, "Extérieur") + picture(interior, "Intérieur")
            paired.add(interior)
            category = "Bâtiments"
        elif file.endswith("-interior.png"):
            continue
        else:
            content = picture(file, name)
            category = "Régions et villes"
        groups.append(
            f'<section data-category="{category}"><h2>{html.escape(name)}</h2><div class="pictures">{content}</div></section>'
        )
    for path in sorted((WORK / "capital/plans").glob("*.png")):
        if "-interieur" in path.stem or "-architecture" in path.stem:
            continue
        name = next(
            (
                p["name"]
                for p in plates.values()
                if p["image"] == "Maps/capital/images/" + path.name
            ),
            path.stem,
        )
        groups.append(
            f'<section data-category="Plans"><h2>{html.escape(name)} · Plan</h2><div class="pictures">{picture(path.relative_to(WORK).as_posix(), name)}</div></section>'
        )
    page = (
        """<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Atlas révisé · 7 octobre 2026</title>
<style>body{margin:0;background:#181a1a;color:#eee9dc;font:16px system-ui}header{padding:24px 4vw;position:sticky;top:0;background:#202323ee;z-index:1;border-bottom:1px solid #555}h1{margin:0 0 8px;font:28px Georgia}p{margin:8px 0}input,select{font:inherit;padding:8px;margin:4px;background:#303535;color:inherit;border:1px solid #7b807a;border-radius:4px}main{padding:20px 3vw}section{padding:16px 0 28px;border-bottom:1px solid #555}h2{font:24px Georgia}figure{margin:0;min-width:0;flex:1}img{display:block;width:100%;height:auto;aspect-ratio:3/2;object-fit:contain;background:#101212}.pictures{display:flex;gap:16px}figcaption{text-align:center;padding:10px;color:#d8cfb5}[hidden]{display:none}a{color:inherit}@media(max-width:900px){.pictures{display:block}figure{margin-bottom:16px}}</style>
<header><h1>Atlas révisé · 7 octobre 2026</h1><p>70 illustrations · 22 paires extérieur / intérieur · cliquez sur une carte pour l’ouvrir en grand.</p><input id="search" type="search" placeholder="Rechercher un lieu"><select id="category"><option>Toutes les cartes</option><option>Bâtiments</option><option>Régions et villes</option><option>Plans</option></select></header><main>"""
        + "".join(groups)
        + """</main><script>function filter(){const text=document.querySelector('#search').value.toLocaleLowerCase();const category=document.querySelector('#category').value;document.querySelectorAll('section').forEach(s=>s.hidden=!(s.textContent.toLocaleLowerCase().includes(text)&&(category==='Toutes les cartes'||s.dataset.category===category)))}document.querySelector('#search').addEventListener('input',filter);document.querySelector('#category').addEventListener('change',filter);</script></html>"""
    )
    (WORK / "index.html").write_text(page, encoding="utf-8")
    print(f"{len(jobs)} final illustrations verified; gallery written.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=["prepare", "data", "plans", "receive", "install", "ocr", "register", "gallery"],
    )
    parser.add_argument("--request")
    parser.add_argument("--target")
    parser.add_argument("--source")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.request)
    elif args.action == "receive":
        receive(args.target, args.source)
    else:
        {
            "data": apply_data,
            "plans": plans,
            "install": install,
            "ocr": ocr_candidates,
            "register": register,
            "gallery": gallery,
        }[args.action]()


if __name__ == "__main__":
    main()
