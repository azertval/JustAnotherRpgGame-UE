# Contrôles et limites du scénario

Les contrôles vérifient conservation et contraintes du modèle. Ils ne transforment pas ses paramètres en faits historiques. La publication V3 passe **42 contrôles démographiques** et **66 contrôles alimentaires** ; l’explorateur est exécuté sur les 118 profils et leurs exports.

## Contrôles alimentaires

| Contrôle | Résultat |
|---|---|
| Catalogue et profils conservés | réussi |
| 13 populations source conservées | réussi |
| Calendrier tanaréen : 360 jours et M1 début été | réussi |
| Toutes les lignes sociales restent conservées par métier | réussi |
| Deux dénominateurs totalisent 100 % | réussi |
| Noblesse inconnue jamais convertie en zéro | réussi |
| V3 conserve tous les statuts sociaux lors des réaffectations | réussi |
| Bases = somme des feuilles | réussi |
| Garnisons source sous convention résidentielle inchangées | réussi |
| G’bagede conserve uniquement enseignants et chercheurs de golems | réussi |
| Terres en rotation et irrigation plafonnées indépendamment | réussi |
| Travail annuel et pics bornés, quotité 0,65 une fois | réussi |
| Stock semences séparé et non consommé | réussi |
| Nourriture magique non stockée et cohortes disjointes | réussi |
| 13 bilans annuels conservés, déficits affichés | réussi |
| Flux respectent capacités et pertes | réussi |
| Transits conservent tonnes et arrivées | réussi |
| Stocks mensuels ordinaires non négatifs | réussi |
| Bilans des 12 mois exacts | réussi |
| 13 budgets hydrologiques saisonniers non négatifs | réussi |
| Paniers physiques conservent énergie et publient leur déficit | réussi |
| Masse alimentaire géants supérieure au seuil 8 kg/j | réussi |
| Sindile : aucune viande/poisson/gibier servi | réussi |
| 13 budgets publics proposés non déficitaires | réussi |
| Quota ferroviaire net bauronite respecté | réussi |
| Tous 118 profils ont un bilan ou une référence relative | réussi |
| Matrices emplois–espèces : chaque ligne rejoint le métier actif | réussi |
| Matrices sociales : marges résidentes et statut par strate conservés | réussi |
| Produits naturels : chaque calorie classée une fois | réussi |
| Huile et tourteaux : énergie et masse de pressage conservées | réussi |
| Masses consommées emploient les densités des produits réels | réussi |
| Cargaisons huile/grain : masse et énergie sans tonnes équivalent déguisées | réussi |
| Équipages et conducteurs partagés plafonnés au pool de métiers | réussi |
| Techniciens ferroviaires qualifiés bornés et retirés des aides | réussi |
| Agents agricoles identiques aux affectations exclusives du registre | réussi |
| Taii : entretien minimum source 8 h par mois borne le stock | réussi |
| Hydrologie : recharge annuelle indépendante des besoins et du plafond | réussi |
| Coût du pompage débité au prix source de bauronite | réussi |
| Scénarios de stress réutilisent les mêmes stocks initiaux ordinaires | réussi |
| Stress route : liaison utilisée fermée réellement durant 90 jours | réussi |
| Conservation interne empire | réussi |
| Demande territoriale = somme des habitants empire | réussi |
| Conservation interne freelands | réussi |
| Demande territoriale = somme des habitants freelands | réussi |
| Conservation interne bennet | réussi |
| Demande territoriale = somme des habitants bennet | réussi |
| Conservation interne kolbjorn | réussi |
| Demande territoriale = somme des habitants kolbjorn | réussi |
| Conservation interne magocracy | réussi |
| Demande territoriale = somme des habitants magocracy | réussi |
| Conservation interne seashores | réussi |
| Demande territoriale = somme des habitants seashores | réussi |
| Conservation interne sindile | réussi |
| Demande territoriale = somme des habitants sindile | réussi |
| Conservation interne stravian | réussi |
| Demande territoriale = somme des habitants stravian | réussi |
| Conservation interne storm | réussi |
| Demande territoriale = somme des habitants storm | réussi |
| Conservation interne taiimaku | réussi |
| Demande territoriale = somme des habitants taiimaku | réussi |
| Conservation interne kepesh | réussi |
| Demande territoriale = somme des habitants kepesh | réussi |
| Conservation interne tsvetan | réussi |
| Demande territoriale = somme des habitants tsvetan | réussi |
| Conservation interne yama | réussi |
| Demande territoriale = somme des habitants yama | réussi |

## Ce que la fermeture prouve

Les besoins énergétiques annuels des 13 régions chiffrées sont couverts dans le scénario central avec plafonds proposés, coûts, cohorts qualifiées, fret, eau et stocks. Les marges sociales/espèces, garnisons et totaux sont conservés. Les crises reprennent les mêmes stocks initiaux et peuvent produire une insuffisance. Les tests d’interface couvrent fonctionnement, filtres, justifications, CSV et valeurs relatives ; le rendu visuel de l’ancien explorateur n’avait pas été certifié.

## Ce que les livres et les calculs ne fixent pas

Les pourcentages de métiers et de noblesse, les tailles locales hors deux capitales, le travail disponible, les terrains exploitables, les rendements régionaux et les qualifiés magiques sont P. La magie des micro-noyaux et du contrôle kemet est une technologie proposée. Les salaires, taxes et budgets sont un scénario, pas un marché simulé dans son intégralité. Les micronutriments et besoins individuels ne sont pas validés ; Storm, Taii et Yama restent autour de 13–14 % d’énergie en lipides dans ce panier. Les fréquences inconnues de noblesse ne sont jamais zéro.

La mauvaise récolte −30 % produit, après stocks initiaux, 40,127 milliards kcal de manque aux Seashores et 279,277 à Taii. Un stress absorbé durant l’année peut épuiser une réserve ; des crises répétées nécessiteraient un scénario multiannuel.

[Registre des contrôles et fonctions testées](Donnees/metiers-tanares-verification.json) · [Reproduction et traçabilité](reproduction.md)

Les contrôles de livraison, des 333 fiches, des 118 CSV et des 87 SVG figurent dans le [registre de documentation](controle-documentation.json).
