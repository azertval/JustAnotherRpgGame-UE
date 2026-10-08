#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""Refuse un livre source, ou le texte extrait d'un livre, parmi les fichiers suivis (EX-CNT-023).

Le dépôt est public. Le corpus (`Documentation/SourceBook/`) et le texte intermédiaire que
l'extraction en tire ne se versionnent pas : seules les données finales le sont. Le `.gitignore`
écarte les emplacements connus ; ce contrôle rattrape ce qui passerait à côté — un `git add -f`,
une copie rangée ailleurs, une nouvelle extraction. Il tourne avant le commit (hook pre-commit) et
en CI (tout le dépôt), et c'est le seul contrôle dont l'échec ne se rattrape pas : un texte poussé
sur un dépôt public y reste, même retiré au commit suivant.

Le runner n'a pas le corpus : rien ici ne compare à un livre. Trois règles, sur le chemin puis sur
la forme :

1. **L'emplacement.** Rien sous `Documentation/SourceBook/`, aucun dossier `Corpus/` sous
   `Documentation/`, pas de `lecture-corpus.html` (le lecteur plein texte, qui embarque les livres).
2. **Le format.** Aucun livre numérique (`.pdf`, `.epub`, `.mobi`, `.djvu`, `.cbz`, `.cbr`).
3. **La forme d'une extraction.** Un JSON qui est une liste de pages — des dizaines de longues
   chaînes, à la racine ou sous une clé `pages` — est un livre mis en texte, quel que soit son nom.
   Un HTML ou un script qui embarque une telle liste aussi.

Le manifeste du corpus (`scripts/sourcebook/corpus.toml`) et les registres d'empreintes restent
suivis : ils décrivent les livres, ils ne les portent pas.

Usage :
  python scripts/checks/check_no_sourcebook.py FICHIER...   (fichiers passés par pre-commit)
  python scripts/checks/check_no_sourcebook.py --all        (tous les fichiers suivis)
  python scripts/checks/check_no_sourcebook.py --auto-test
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

BOOK_EXTENSIONS = ('.pdf', '.epub', '.mobi', '.djvu', '.cbz', '.cbr')
FORBIDDEN_PREFIX = 'Documentation/SourceBook/'
FORBIDDEN_NAMES = ('lecture-corpus.html',)
# Une extraction : au moins tant de pages, pour tant de caractères. Le plus petit livre du corpus
# (22 pages) donne 60 000 caractères ; le plus gros fichier de données du jeu qui soit une liste de
# chaînes n'en approche pas.
MIN_PAGES = 15
MIN_CHARS = 40_000
EMBEDDED_PAGES_RE = re.compile(r'"pages"\s*:\s*\[')
EMBEDDED_MIN_BYTES = 200_000


def is_page_dump(value):
    """Vrai si @p value est une liste de pages : beaucoup de chaînes, longues."""
    if not isinstance(value, list) or len(value) < MIN_PAGES:
        return False
    if not all(isinstance(page, str) for page in value):
        return False
    return sum(len(page) for page in value) >= MIN_CHARS


def holds_page_dump(value, depth=0):
    """Vrai si @p value est une liste de pages, ou en range une sous une clé `pages`."""
    if is_page_dump(value):
        return True
    if depth >= 3 or not isinstance(value, dict):
        return False
    return any((key == 'pages' and is_page_dump(child)) or holds_page_dump(child, depth + 1)
               for key, child in value.items())


def problem(path):
    """Le motif du refus de @p path, ou None s'il est admis."""
    normalised = path.replace(os.sep, '/')
    lower = normalised.lower()
    parts = normalised.split('/')
    if normalised.startswith(FORBIDDEN_PREFIX):
        return 'sous %s, le corpus source' % FORBIDDEN_PREFIX
    if lower.endswith(BOOK_EXTENSIONS):
        return 'livre numérique (%s)' % os.path.splitext(lower)[1]
    if parts[0] == 'Documentation' and 'Corpus' in parts[:-1]:
        return 'dossier Corpus/ : le texte extrait des livres'
    if parts[-1] in FORBIDDEN_NAMES:
        return 'lecteur plein texte, qui embarque les livres'
    if not os.path.isfile(path):
        return None  # supprimé dans l'index
    if lower.endswith('.json'):
        try:
            with open(path, encoding='utf-8-sig') as handle:
                value = json.load(handle)
        except (ValueError, OSError):
            return None  # un JSON invalide est l'affaire de check_json_files.py
        if holds_page_dump(value):
            return 'liste de pages de texte : la forme d\'une extraction de livre'
    elif lower.endswith(('.html', '.htm', '.js')) and os.path.getsize(path) >= EMBEDDED_MIN_BYTES:
        with open(path, encoding='utf-8', errors='ignore') as handle:
            if EMBEDDED_PAGES_RE.search(handle.read()):
                return 'embarque une liste `pages` : la forme d\'une extraction de livre'
    return None


def auto_test():
    """Éprouve chaque règle sur des fichiers écrits en temporaire : un contrôle qui n'a jamais rien
    refusé ne prouve pas qu'il en est capable."""
    page = 'Le texte d\'une page. ' * 200
    assert is_page_dump([page] * MIN_PAGES)
    assert not is_page_dump([page] * (MIN_PAGES - 1))
    assert not is_page_dump(['court'] * 500)
    assert not is_page_dump([{'texte': page}] * 50)
    assert holds_page_dump({'SB': {'title': 'Un livre', 'pages': [page] * 30}})
    assert not holds_page_dump({'pages': 179, 'livre': 'Un livre'})
    assert problem('Documentation/SourceBook/VTT/carte.jpg')
    assert problem('Planning/annexes/Regles.PDF')
    assert problem('Documentation/Metiers/Sources/Corpus/sb.json')
    assert problem('Documentation/Metiers/Sources/lecture-corpus.html')
    assert problem('scripts/sourcebook/corpus.toml') is None
    assert problem('Documentation/Metiers/Sources/registre-corpus.json') is None
    with tempfile.TemporaryDirectory() as root:
        def write(name, text):
            path = os.path.join(root, name)
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write(text)
            return path
        assert problem(write('cache.json', json.dumps([page] * 30)))
        assert problem(write('lecteur.html', '<script>{"SB":{"pages": ["%s"]}}</script>'
                             % (page * 60)))
        assert problem(write('catalogue.json', json.dumps({'entries': [{'id': 'a'}] * 400}))) is None
        assert problem(write('page.html', '<p>%s</p>' % (page * 60))) is None
        assert problem(write('tronque.json', '[')) is None
    print('OK : auto-test du garde-fou des livres sources.')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('files', nargs='*')
    parser.add_argument('--all', action='store_true', help='tous les fichiers suivis par git')
    parser.add_argument('--auto-test', action='store_true')
    arguments = parser.parse_args()

    auto_test()
    if arguments.auto_test:
        return 0

    if arguments.all:
        os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        listing = subprocess.run(['git', 'ls-files', '-z'], capture_output=True, check=True)
        paths = [p for p in listing.stdout.decode('utf-8').split('\0') if p]
    else:
        paths = arguments.files

    found = [(path, reason) for path in paths for reason in [problem(path)] if reason]
    for path, reason in found:
        print('ERREUR : %s : %s.' % (path, reason))
    if found:
        print('Un livre source ou son texte ne se versionne pas (EX-CNT-023) : le retirer de '
              'l\'index (`git rm --cached`) et l\'écarter par .gitignore.')
        return 1
    print('OK : %d fichier(s), aucun livre source ni texte extrait.' % len(paths))
    return 0


if __name__ == '__main__':
    sys.exit(main())
