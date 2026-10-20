"""Les planches du « Guide de Creation » de la capitale, lues dans le PDF tel qu'il est livre.

Le guide (`Documentation/SourceBook/references-capitale/output/Guide de Creation.pdf`) porte une
image par page, au meme cadrage : 01 la carte entiere (5000 x 3532), 02 le landscape valide, 03 le
relief annote, 04 le reseau routier, 05 l'eau annotee, 06 la carte topographique (1492 x 1054).
Les images sont des flux JPEG (DCTDecode, enveloppes d'ASCII85) : on les extrait sans dependance hors Pillow, dans l'ordre
des pages, et on les ramene au cadrage commun des planches 02 a 06.
"""
from pathlib import Path
import base64
import io
import re

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / 'Documentation/SourceBook/references-capitale/output/Guide de Creation.pdf'
PLATE = (1492, 1054)  # cadrage commun des planches


def _object(data, number):
    m = re.search(rb'(?:^|[\r\n])%d 0 obj\s*<<' % number, data)
    if not m:
        raise RuntimeError(f'Objet {number} absent du guide')
    return m.end()


def _pages(data):
    """Les numeros d'objet des images, une par page, dans l'ordre des pages."""
    root = re.search(rb'/Type\s*/Pages\b', data)
    start = data.rfind(b'obj', 0, root.start())
    kids = re.search(rb'/Kids\s*\[([^\]]*)\]', data[start:root.start() + 400])
    pages = [int(k) for k in re.findall(rb'(\d+)\s+0\s+R', kids.group(1))]
    images = []
    for page in pages:
        at = _object(data, page)
        body = data[at:data.index(b'endobj', at)]
        xobject = re.search(rb'/XObject\s*<<[^>]*?(\d+)\s+0\s+R', body)
        images.append(int(xobject.group(1)))
    return images


def _jpeg(data, number):
    at = _object(data, number)
    head_end = data.index(b'stream', at)
    head = data[at:head_end]
    if b'/DCTDecode' not in head:
        raise RuntimeError(f'Image {number} : flux non JPEG')
    length = int(re.search(rb'/Length\s+(\d+)', head).group(1))
    body = head_end + len(b'stream')
    body += 2 if data[body:body + 2] == b'\r\n' else 1
    raw = data[body:body + length]
    if b'/ASCII85Decode' in head:  # le JPEG est enveloppe d'ASCII85, termine par ~>
        raw = raw.strip()
        raw = base64.a85decode(raw[:raw.rindex(b'~>')], adobe=False, ignorechars=b' \t\r\n\x0b\x0c')
    return Image.open(io.BytesIO(raw)).convert('RGB')


def plates():
    """Les six planches, numerotees comme le guide (1 a 6), au cadrage commun."""
    data = GUIDE.read_bytes()
    out = {}
    for page, number in enumerate(_pages(data), start=1):
        img = _jpeg(data, number)
        out[page] = img if img.size == PLATE else img.resize(PLATE, Image.LANCZOS)
    if len(out) != 6:
        raise RuntimeError(f'Le guide devrait avoir six planches, il en a {len(out)}')
    return out


def full_map():
    """La planche 01 a sa resolution d'origine (5000 x 3532), pour lire les remparts."""
    data = GUIDE.read_bytes()
    return _jpeg(data, _pages(data)[0])
