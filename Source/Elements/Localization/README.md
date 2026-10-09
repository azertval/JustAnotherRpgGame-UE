# Elements/Localization/

Catalogues de traduction de l'interface, un **fichier par langue** (`<langue>.lang`).

- Format texte simple : une paire `clé = valeur` par ligne, encodage **UTF-8**.
- Lignes vides et lignes commençant par `#` (commentaires) ignorées ; seul le premier `=`
  sépare la clé de la valeur.
- Les **clés** sont stables et référencées par le code (aucun libellé d'interface en dur) ;
  ajouter une langue = ajouter un fichier `<langue>.lang`, sans modifier le code.
- Lus par Core (`core::parseTextCatalog`) et chargés par le moteur en tables de chaînes
  (`FJadgTexts`, `UI/JadgTexts.h`, LOT-1020) ; un trou s'écrit `%1` à `%9`.
- `check_translations.py` vérifie que chaque langue a les clés et les trous du français.

Les cartes ne portent pas de texte : leur nom est la clé `map.<identifiant>.name`, celui de leurs
îlots `city_block.<nom>`, et l'éditeur exige chaque clé dans chaque catalogue (`EX-EDIT-081`).
Créer une carte dans l'éditeur ajoute sa clé ici, avec le nom tapé pour texte.

Réf. specs : `EX-REN-033` (catalogue de traduction), `EX-REN-032` (texte).
