#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""Vérifie qu'un outil épinglé à deux endroits l'est à la même version.

Deux écritures d'un même fait finissent par diverger sans que rien ne le signale. Ici :

- **clang-format** : `LLVM_VERSION` de ci.yml (job `format`) et le tag du dépôt
  `mirrors-clang-format` dans .pre-commit-config.yaml. Deux versions majeures ne formatent pas
  pareil : le hook reformaterait un fichier que la CI refuse, ou l'inverse.

- **Unreal Engine** (LOT-1014) : `UNREAL_ENGINE_VERSION` de ci.yml et l'`IncludeOrderVersion` des
  deux cibles du projet (`Source/*.Target.cs`). Le `.uproject` n'aide pas : il associe un moteur
  construit des sources par un identifiant de poste, pas par un numéro. C'est `scripts/build.ps1
  -Unreal` qui compare l'épingle au moteur installé (`Engine/Build/Build.version`) ; ce contrôle-ci
  tient les écritures du dépôt d'accord entre elles, sans moteur.

Usage :
  python scripts/ci/check_tool_pins.py
"""
import os
import re
import sys

CI = os.path.join('.github', 'workflows', 'ci.yml')
PRE_COMMIT = '.pre-commit-config.yaml'
GAME_TARGET = os.path.join('Source', 'JustAnotherRpgGame.Target.cs')
EDITOR_TARGET = os.path.join('Source', 'JustAnotherRpgGameEditor.Target.cs')


def env_value(name):
    """Le motif qui lit la valeur de `NAME:` dans le bloc `env:` d'un workflow."""
    return re.compile(r'^\s*%s:\s*[\'"]?([^\'"\s#]+)[\'"]?\s*(?:#.*)?$' % re.escape(name),
                      re.MULTILINE)


# Le SHA épinglé est suivi du tag en commentaire : `rev: <sha>  # frozen: v20.1.8`.
CLANG_FORMAT_RE = re.compile(
    r'repo:\s*https://github\.com/pre-commit/mirrors-clang-format\s*\n'
    r'\s*rev:\s*\S+\s*#\s*frozen:\s*v([0-9][^\s]*)')

# `IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;` : la version s'y écrit `5_8`.
INCLUDE_ORDER_RE = re.compile(r'EngineIncludeOrderVersion\.Unreal(\d+_\d+)\s*;')
INCLUDE_ORDER = 'IncludeOrderVersion (EngineIncludeOrderVersion.UnrealX_Y)'

PAIRS = [
    ('clang-format', (CI, env_value('LLVM_VERSION'), 'LLVM_VERSION'),
     (PRE_COMMIT, CLANG_FORMAT_RE, 'rev de mirrors-clang-format (# frozen: vX)')),
    ('Unreal Engine', (CI, env_value('UNREAL_ENGINE_VERSION'), 'UNREAL_ENGINE_VERSION'),
     (GAME_TARGET, INCLUDE_ORDER_RE, INCLUDE_ORDER)),
    ('Unreal Engine', (CI, env_value('UNREAL_ENGINE_VERSION'), 'UNREAL_ENGINE_VERSION'),
     (EDITOR_TARGET, INCLUDE_ORDER_RE, INCLUDE_ORDER)),
]


def read_single(path, pattern, label):
    """L'unique capture de `pattern` dans `path`, ou None après avoir dit pourquoi."""
    try:
        with open(path, encoding='utf-8') as handle:
            matches = pattern.findall(handle.read())
    except OSError as error:
        print('ERREUR : %s illisible (%s).' % (path, error))
        return None
    if len(matches) != 1:
        print('ERREUR : %s attendu exactement une fois dans %s (trouvé %d).'
              % (label, path, len(matches)))
        return None
    # Une cible écrit `5_8` là où le reste du dépôt écrit `5.8`.
    return matches[0].replace('_', '.')


def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    ok = True
    for tool, (path_a, pattern_a, label_a), (path_b, pattern_b, label_b) in PAIRS:
        version_a = read_single(path_a, pattern_a, label_a)
        version_b = read_single(path_b, pattern_b, label_b)
        if version_a is None or version_b is None:
            ok = False
            continue
        if version_a != version_b:
            print('ERREUR : %s épinglé à deux versions.' % tool)
            print('  %s : %s = %s' % (path_a, label_a, version_a))
            print('  %s : %s = %s' % (path_b, label_b, version_b))
            ok = False
        else:
            print('OK : %s %s dans %s et %s.' % (tool, version_a, path_a, path_b))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
