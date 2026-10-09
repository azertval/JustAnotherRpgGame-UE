#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""Contrôle des catalogues de textes du jeu (`Source/Elements/Localization/<langue>.lang`, LOT-1020).

Les écrans du nouveau moteur nomment leurs textes par **clé** (`FJadgTexts::Get(TEXT("hud.map"))`)
et le moteur charge chaque catalogue dans une table de chaînes (`UI/JadgTexts.cpp`). Le français est
la langue de référence ; chaque autre langue doit dire la même chose aux mêmes endroits. Ce contrôle
refuse :

- une clé **d'un seul côté** : présente en français et absente d'une autre langue (le jeu y
  afficherait le français), ou l'inverse (un texte que rien n'affiche) ;
- une valeur **vide** ;
- des **trous** différents entre les langues (`%1` à `%9`) : le texte remplirait le mauvais trou,
  ou aucun ;
- un **espace de bord** ajouté ou perdu : il sert presque toujours à coller deux textes à l'écran
  (sauf l'espace français avant « : ; ! ? », que l'anglais n'écrit pas) ;
- une clé **nommée en dur dans le code du jeu** (`TEXT("domaine.nom")` dans un appel de texte) et
  absente du français : l'écran afficherait la clé elle-même ;
- une clé **répétée** dans un même fichier : la seconde valeur écrase la première sans rien dire.

Usage :
  python scripts/checks/check_translations.py          les catalogues du dépôt et le code du jeu
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CATALOGUES = ROOT / 'Source' / 'Elements' / 'Localization'
CODE = ROOT / 'Source' / 'JustAnotherRpgGame'
REFERENCE = 'fr'

PLACEHOLDER_RE = re.compile(r'%[1-9]')
# Typographie française : espace avant « : ; ! ? ». Une valeur qui commence par « : » le porte,
# que l'anglais n'écrit pas — ce n'est pas un espace perdu.
FRENCH_SPACE_BEFORE_PUNCTUATION_RE = re.compile(r'^\s+(?=[:;!?])')
# Une clé écrite en dur dans un appel de texte du jeu.
CODE_KEY_RE = re.compile(r'(?:Key|Get|Format|JadgText|In)\(\s*TEXT\("([a-z_]+(?:\.[a-z0-9_-]+)+)"\)')


def parse(text, name):
    """La table clé → valeur d'un `.lang`, et les clés répétées."""
    table, problems = {}, []
    for number, line in enumerate(text.lstrip('﻿').splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or '=' not in stripped:
            continue
        key, value = (part.strip() for part in stripped.split('=', 1))
        if not key:
            continue
        if key in table:
            problems.append('%s:%d : clé « %s » répétée' % (name, number, key))
        table[key] = value
    return table, problems


def placeholders(text):
    return sorted(set(PLACEHOLDER_RE.findall(text or '')))


def edges(text):
    """Espaces de début et de fin : le texte qu'on colle à un autre en dépend."""
    text = FRENCH_SPACE_BEFORE_PUNCTUATION_RE.sub('', text or '')
    return (text[:len(text) - len(text.lstrip())], text[len(text.rstrip()):])


def problems(catalogues, code_keys=()):
    """Défauts des catalogues @p catalogues (langue → (table, défauts de lecture))."""
    found = []
    if REFERENCE not in catalogues:
        return ['catalogue de référence %s.lang absent' % REFERENCE]
    reference, _ = catalogues[REFERENCE]
    if not reference:
        return ['%s.lang : aucune clé ; le catalogue est vide ou sa lecture est cassée' % REFERENCE]
    for language, (table, read) in sorted(catalogues.items()):
        found.extend(read)
        for key, value in sorted(table.items()):
            if not value:
                found.append('%s.lang : « %s » est vide' % (language, key))
        if language == REFERENCE:
            continue
        for key in sorted(set(reference) - set(table)):
            found.append('%s.lang : « %s » manque (le jeu afficherait le français)' % (language, key))
        for key in sorted(set(table) - set(reference)):
            found.append('%s.lang : « %s » n\'existe pas en français' % (language, key))
        for key in sorted(set(table) & set(reference)):
            if placeholders(table[key]) != placeholders(reference[key]):
                found.append('%s.lang : « %s » : trous %s, %s en français' % (
                    language, key, placeholders(table[key]) or 'aucun', placeholders(reference[key]) or 'aucun'))
            if edges(table[key]) != edges(reference[key]):
                found.append('%s.lang : « %s » : espaces de bord différents du français' % (language, key))
    for key in sorted(set(code_keys) - set(reference)):
        found.append('code du jeu : la clé « %s » n\'est pas dans %s.lang' % (key, REFERENCE))
    return found


def code_keys(root=CODE):
    keys = set()
    for path in root.rglob('*.cpp'):
        keys.update(CODE_KEY_RE.findall(path.read_text(encoding='utf-8')))
    return keys


def load(directory=CATALOGUES):
    catalogues = {}
    for path in sorted(directory.glob('*.lang')):
        catalogues[path.stem] = parse(path.read_text(encoding='utf-8'), path.name)
    return catalogues


def main():
    catalogues = load()
    errors = problems(catalogues, code_keys())
    for message in errors:
        print('ERREUR : ' + message)
    if errors:
        print('\n%d défaut(s) dans les catalogues de textes.' % len(errors))
        return 1
    print('OK : %d catalogue(s), %d clé(s), toutes traduites et cohérentes.'
          % (len(catalogues), len(catalogues[REFERENCE][0])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
