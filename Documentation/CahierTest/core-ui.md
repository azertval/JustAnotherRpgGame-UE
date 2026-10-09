# Core · Ui

Tests unitaires — **7 cas** (5 bloquants, 2 majeurs). [Retour à la synthèse](README.md).

## Ce que cette page couvre

| Fichier de test | Cas | Bloquant | Critique | Majeur | Mineur |
|---|---|---|---|---|---|
| [`test_map_interactions.cpp`](#test-map-interactionscpp) | 2 | 1 | - | 1 | - |
| [`test_text_catalog.cpp`](#test-text-catalogcpp) | 3 | 3 | - | - | - |
| [`test_ui_style.cpp`](#test-ui-stylecpp) | 2 | 1 | - | 1 | - |

## test_map_interactions.cpp

### MapInteractionsTest.LesLieuxSeLisentDuMondeAuxBatiments

*Bloquant · Unitaire · Interface · Carte* — `Source/Test/Unit/Core/Ui/test_map_interactions.cpp:18`

Les lieux de la carte se lisent du monde aux bâtiments.

**Étapes**

1. Lire Source/Elements/Maps/map-interactions.json.
2. Descendre du monde à l'Empire central, à la Capitale, à Arenarea.

**Résultat attendu**

- Vérifie que `read.errors.empty()` est vrai.
- Vérifie que `read.imageOf("world")` vaut `"Maps/world.png"`.
- Vérifie que `empire` est vrai.
- Vérifie que `read.imageOf("central-empire-the-capital-city-arenarea")` vaut `"Maps/capital/images/arenarea.png"`.
- Vérifie que `read.parentOf("arena-of-fate")` vaut `"central-empire-the-capital-city-arenarea"`.
- Vérifie que `read.imageOf("hippodrome").empty() || !read.childrenOf("hippodrome").empty()` est vrai.
- Vérifie que `neighbour` est vrai.

### MapInteractionsTest.UnLieuFautifEstNomme

*Majeur · Unitaire · Interface · Carte* — `Source/Test/Unit/Core/Ui/test_map_interactions.cpp:51`

Un lieu fautif de la carte est nommé, les autres se lisent.

**Étapes**

1. Lire trois entrées : une juste, une sans parent, une à la bannière de trois nombres.

**Résultat attendu**

- Vérifie que `read.errors.size()` vaut `2U`.
- Vérifie que `read.zones.size()` vaut `1U`.
- Vérifie que `read.zones[0].label[2]` vaut `0.3F` (comparaison flottante).

## test_text_catalog.cpp

### TextCatalogTest.UnCatalogueSeLitCleParCle

*Bloquant · Unitaire · Interface · Textes* — `Source/Test/Unit/Core/Ui/test_text_catalog.cpp:20`

Un catalogue de textes se lit clé par clé.

**Étapes**

1. Lire un contenu avec une marque d'ordre des octets, un commentaire, une ligne vide, une valeur qui contient « = », des fins de ligne Windows.

**Résultat attendu**

- Vérifie que `table.size()` vaut `2U`.
- Vérifie que `table.at("menu.quit")` vaut `"Quitter"`.
- Vérifie que `table.at("math.eq")` vaut `"a = b"`.

### TextCatalogTest.LesTrousSeRemplissentEtSeTraduisent

*Bloquant · Unitaire · Interface · Textes* — `Source/Test/Unit/Core/Ui/test_text_catalog.cpp:38`

Les trous d'un texte se remplissent et s'écrivent pour le moteur.

**Étapes**

1. Remplir « %1 · DD %2 » avec deux arguments, puis avec un seul.
2. Traduire un texte à trous et à accolades dans l'écriture du moteur.

**Résultat attendu**

- Vérifie que `core::formatText("%1 · DD %2", {"Persuasion", "12"})` vaut `"Persuasion · DD 12"`.
- Vérifie que `core::formatText("%1 · DD %2", {"Persuasion"})` vaut `"Persuasion · DD %2"`.
- Vérifie que `core::toEngineFormat("%1 · {x}")` vaut `"{0} · `{x`}"`.
- Vérifie que `core::textPlaceholders("%2 puis %1 puis %2")` vaut `(std::vector<int>{1, 2})`.

### TextCatalogTest.LesDeuxCataloguesDuDepotSeRepondent

*Bloquant · Unitaire · Interface · Textes* — `Source/Test/Unit/Core/Ui/test_text_catalog.cpp:55`

Le français et l'anglais ont les mêmes clés et les mêmes trous.

**Étapes**

1. Lire Source/Elements/Localization/fr.lang et en.lang.
2. Comparer leurs clés, puis les trous de chaque valeur.

**Résultat attendu**

- Vérifie que `french.empty()` est faux.
- Vérifie que `english.contains(key)` est vrai.
- Vérifie que `value.empty()` est faux.
- Vérifie que `core::textPlaceholders(value)` vaut `core::textPlaceholders(english.at(key))`.
- Vérifie que `french.contains(key)` est vrai.

## test_ui_style.cpp

### UiStyleTest.LeStyleDuDepotSeLit

*Bloquant · Unitaire · Interface · Style* — `Source/Test/Unit/Core/Ui/test_ui_style.cpp:24`

Le style des écrans du dépôt se lit sans erreur.

**Étapes**

1. Lire Source/Elements/Assets/UI/style.json.

**Résultat attendu**

- Vérifie que `read.ok()` est vrai.
- Vérifie que `style.designWidth` vaut `1920`.
- Vérifie que `style.designHeight` vaut `1080`.
- Vérifie que `style.colours.at("panelEdge")` vaut `*core::parseUiColour("#e4a43c")`.
- Vérifie que `panel.margins.has_value()` est vrai.
- Vérifie que `*panel.margins` vaut `(core::UiMargins{112, 112, 112, 112})`.
- Vérifie que `panel.file()` vaut `"frame/panel-dark.png"`.
- Vérifie que `button.states.size()` vaut `4U`.
- Vérifie que `button.file("hover")` vaut `"button/default/hover.png"`.
- Vérifie que `style.fonts.at("title")` vaut `"Fonts/Cinzel-SemiBold.ttf"`.
- Vérifie que `style.fonts.at("body")` vaut `"Fonts/IMFellEnglish-Regular.ttf"`.
- Vérifie que `std::filesystem::exists(std::filesystem::path(JADG_ASSETS_DIR) / file)` est vrai.
- Vérifie que `style.sizes.at("screenTitle")` vaut `36`.

### UiStyleTest.UneValeurFausseEstNommee

*Majeur · Unitaire · Interface · Style* — `Source/Test/Unit/Core/Ui/test_ui_style.cpp:57`

Une valeur fausse du style est nommée, le reste se lit.

**Étapes**

1. Lire un style à une couleur fausse, une pièce aux marges plus larges qu'elle, une taille négative et une section inconnue, à côté de valeurs justes.

**Résultat attendu**

- Vérifie que `read.errors.size()` vaut `4U`.
- Vérifie que `read.errors[0].find("colours.faux")` diffère de `std::string::npos`.
- Vérifie que `read.style.colours.contains("ink")` est vrai.
- Vérifie que `read.style.pieces.contains("plate/ok")` est vrai.
- Vérifie que `read.style.pieces.contains("plate/faux")` est faux.
- Vérifie que `core::parseUiColour("#12345").has_value()` est faux.
- Vérifie que `core::parseUiColour("#000000a0")->alpha` vaut `160.0F / 255.0F` (comparaison flottante).
