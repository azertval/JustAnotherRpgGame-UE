# Données et reproduction

Les données gelées, les explications et les scripts sont conservés avec le dossier. La reproduction ne dépend pas de l’ancien dépôt D: ni d’un PDF installé ailleurs : les entrées numériques et les extractions textuelles utiles sont transmises. Les originaux des livres restent leurs références éditoriales, avec pagination imprimée conservée.

## Données publiées

| Fichier | Contenu |
|---|---|
| [Modèle intégral](Donnees/metiers-tanares-modele.json) | Catalogue, populations, marges, coefficients, sources et bilan intégré |
| [Alimentation](Donnees/metiers-tanares-alimentation-v3.json) | Terres, produits, travail, eau, transport, stocks, budgets et stress |
| [Magie](Donnees/metiers-tanares-magie-v3.json) | Cohortes, classes/niveaux proposés, support et serviteurs |
| [Compétences](Donnees/competences-proposees.json) | Fonctions, savoir-faire, apprentissage et portée des fiches |
| [Corpus et empreintes](Sources/registre-corpus.json) | Origine et transformation des extractions textuelles |

## Rejouer les calculs dans le dossier de reproduction

Le [lanceur V3 portable](Reproduction/Etude/Tools/Worldbuilding/Tanares/Metiers/build_v3.ps1) crée ses résultats dans `Reproduction/Etude/reports` ; les données gelées de `Donnees` restent distinctes. Il reçoit les chemins de Python et Node si ces exécutables ne sont pas dans le chemin système.

```powershell
./Reproduction/Etude/Tools/Worldbuilding/Tanares/Metiers/build_v3.ps1 -Python python -Node node
```

Le lanceur utilise un répertoire temporaire local, fixe le hash seed et calcule depuis une référence V2 fraîche. Les scripts ne réaffectent jamais une V3 déjà modifiée en guise de référence, afin de conserver les deltas. Les vérifications JavaScript sont incluses. Les scripts de l’étude ne touchent ni moteur ni Core.

## Régénérer les pages et figures

```powershell
python -B -X utf8 Reproduction/generer_documentation.py
```

Les fonctions et skills viennent du JSON proposé, les chiffres du modèle gelé. Les SVG sont du texte produit par le générateur, sans recopie des images des livres. L’arbre, les 333 fiches, les 118 pages de population et CSV, les régions et les graphiques sont recréés à partir de ces entrées. Les guides d’explication et les analyses archivées sont conservés avec les sources.

## Lire le site de documentation

Le moteur Markdown du projet rend cette rubrique au même titre que les autres parties. La version HTML est une sortie générée, les pages Markdown sont les sources éditables. Les fichiers JSON, CSV, corpus et explorateur sont joints au rendu afin que les liens restent locaux. Le manifeste de livraison permet de vérifier la copie ; il ne constitue pas une validation de conception par l’auteur.

Les chemins originels des PDF dans les données brutes sont des métadonnées de provenance. La lecture se fait par le corpus et les renvois locaux ; aucun calcul ne lit ces chemins.

La recherche générale du site demande un serveur local :

```powershell
python -m http.server 8000 --directory generated/site
```

Puis ouvrir `http://localhost:8000/Metiers/`. La navigation et l’explorateur fonctionnent aussi sans serveur.

Pour reconstruire le rendu et joindre les annexes locales :

```powershell
python -B Reproduction/rendre_site.py
```
