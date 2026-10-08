# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Inventory and contact sheets for visual atlas review; never edits assets."""

from pathlib import Path
import argparse
import csv
import difflib
import hashlib
import json
import re
import subprocess
import unicodedata
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build/atlas-homogeneity-20261006"
REVIEW = ROOT / "Tools/WorldAtlasReview20261006"


def words(value):
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.findall(r"[a-z0-9]+", ascii_text)


def label_candidates():
    """OCR is review evidence only; never changes geographic data automatically."""
    tess = Path("C:/Program Files/PDF24/tesseract/tesseract.exe")
    source = ROOT / "Tools/WorldAtlas20261005"
    specs = json.loads((source / "generation-specs.json").read_text(encoding="utf-8-sig"))
    regions = [s for s in specs if s["kind"] == "region"]
    groups = {}
    for region in regions:
        rid = region["id"]
        path = REVIEW / "images" / f"{rid}.png"
        if not path.exists():
            continue
        output = OUT / "ocr" / rid
        output.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(path) as im:
            width, height = im.size
            diagnostic = output.with_suffix(".png")
            im.resize((width * 2, height * 2)).save(diagnostic)
        subprocess.run(
            [
                str(tess),
                str(diagnostic),
                str(output),
                "--tessdata-dir",
                str(source),
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
        diagnostic.unlink()
        lines = {}
        with output.with_suffix(".tsv").open(encoding="utf-8") as stream:
            for row in csv.DictReader(stream, delimiter="\t", quoting=csv.QUOTE_NONE):
                if row["level"] != "5" or float(row["conf"]) < 35 or not row["text"].strip():
                    continue
                key = tuple(row[k] for k in ("block_num", "par_num", "line_num"))
                lines.setdefault(key, []).append(row)
        labels = []
        for rows in lines.values():
            text = " ".join(r["text"] for r in rows)
            x = min(int(r["left"]) for r in rows)
            y = min(int(r["top"]) for r in rows)
            right = max(int(r["left"]) + int(r["width"]) for r in rows)
            bottom = max(int(r["top"]) + int(r["height"]) for r in rows)
            labels.append(
                dict(
                    text=text,
                    tokens=words(text),
                    at=[(x + right) / (4 * width), (y + bottom) / (4 * height)],
                )
            )
        groups[rid] = labels
        print("OCR : " + rid, flush=True)
    # Phrase and unique non-generic words both remain candidates for visual review.
    stop = set(
        "the of city forest lake mountain mountains island islands coast range valley fields ruins temple sea archipelago village great north south west east eastern western central old port capital".split()
    )
    candidates = []
    for s in specs:
        if s["kind"] != "geographic" or not s.get("artwork"):
            continue
        significant = [w for w in words(s["name"]) if w not in stop and len(w) > 3]
        expected = words(s["name"])
        found = []
        for rid, labels in groups.items():
            for label in labels:
                phrase = difflib.SequenceMatcher(
                    None, " ".join(expected), " ".join(label["tokens"])
                ).ratio()
                score = max(
                    [phrase]
                    + [
                        difflib.SequenceMatcher(None, w, t).ratio()
                        for w in significant
                        for t in label["tokens"]
                    ]
                )
                if score >= 0.90:
                    found.append(
                        dict(
                            artwork=rid,
                            text=label["text"],
                            at=label["at"],
                            score=round(score, 4),
                            preferred=rid in (s["artwork"], s["parent"]),
                        )
                    )
        found.sort(key=lambda c: (c["preferred"], c["score"]), reverse=True)
        candidates.append(
            dict(
                id=s["id"],
                name=s["name"],
                parent=s["parent"],
                previousArtwork=s["artwork"],
                previousFrame=s["frame"],
                candidates=found[:5],
            )
        )
    (OUT / "label-candidates.json").write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"{len(candidates)} lieux a recaler visuellement ; aucune donnee de jeu modifiee.")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(
        (ROOT / "Source/Elements/Assets/Maps/manifest.json").read_text(encoding="utf-8-sig")
    )
    catalog = json.loads(
        (ROOT / "Source/Elements/Maps/world-maps.json").read_text(encoding="utf-8-sig")
    )
    names = {}
    for pid, plate in sorted(
        catalog["plates"].items(), key=lambda item: bool(item[1].get("frame"))
    ):
        names.setdefault(plate["image"].removeprefix("Maps/"), []).append((pid, plate["name"]))
    records = []
    hashes = {}
    for entry in manifest["maps"]:
        if entry["level"] == "emblem":
            continue
        path = ROOT / "Source/Elements/Assets/Maps" / entry["file"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes.setdefault(digest, []).append(entry["file"])
        with Image.open(path) as im:
            size = list(im.size)
        records.append(
            dict(
                file=entry["file"],
                path=str(path),
                names=names.get(entry["file"], []),
                sha256=digest,
                size=size,
            )
        )
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
    for group in ("world", "capital"):
        items = [r for r in records if (r["file"].startswith("capital/")) == (group == "capital")]
        for page in range(0, len(items), 12):
            canvas = Image.new("RGB", (1600, 1080), "#171d22")
            draw = ImageDraw.Draw(canvas)
            for i, record in enumerate(items[page : page + 12]):
                x, y = i % 4 * 400, i // 4 * 360
                with Image.open(record["path"]) as im:
                    thumb = im.convert("RGB")
                    thumb.thumbnail((390, 304))
                    canvas.paste(
                        thumb, (x + (400 - thumb.width) // 2, y + (304 - thumb.height) // 2)
                    )
                label = record["names"][0][1] if record["names"] else record["file"]
                draw.text(
                    (x + 5, y + 309), f"{page + i + 1}: {label[:36]}", font=font, fill="white"
                )
                draw.text((x + 5, y + 334), record["file"][-44:], font=font, fill="#b3c3cc")
            canvas.save(OUT / f"{group}-{page // 12:02}.jpg", quality=94)
    raw = ROOT / "Tools/WorldAtlas20261005/generated-images"
    raw_inventory = []
    for path in sorted(raw.glob("*.png")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        raw_inventory.append(
            dict(file=path.name, bytes=path.stat().st_size, delivered=hashes.get(digest, []))
        )
    (OUT / "inventory.json").write_text(
        json.dumps(
            dict(plates=len(catalog["plates"]), images=records, raw=raw_inventory),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            dict(
                plates=len(catalog["plates"]),
                illustrations=len(records),
                raw=len(raw_inventory),
                empty=[r["file"] for r in raw_inventory if not r["bytes"]],
                sheets=[p.name for p in OUT.glob("*.jpg")],
            ),
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--labels", action="store_true", help="candidats OCR pour revue, sans ecrire au catalogue"
    )
    args = parser.parse_args()
    if args.labels:
        label_candidates()
    else:
        main()
