# Revue agronomique indépendante V3 — première passe

7 octobre 2026. Lecture seule de `.cache/metiers-audit/food_v3.py` et `reports/metiers-tanares-parametres-v3-provisoires.json`. La simulation de production et de stocks n'est pas encore présente dans la version examinée : les points ci-dessous sont des risques à prévenir, **pas des erreurs d'exécution déjà démontrées**. Aucune modification des fichiers du rédacteur.

## Points à verrouiller avant le bilan

1. **Une seule perte de stockage.** Les paramètres des cultures intègrent `storage_loss` de 8 %, 10 %, 15 % ou 25 % dans les rendements nets. Le nouveau `monthly_spoilage_dry=0.004` donne environ 4,7 % sur un stock gardé douze mois. Si la simulation applique ce coefficient au produit déjà net, elle ajoute une deuxième perte de même nature. Choisir production brute après semences, puis pertes mensuelles des vrais stocks, ou production nette annuelle puis absence de deuxième perte annuelle équivalente. Une détérioration distincte peut exister, mais doit porter un autre nom et être justifiée.

2. **Un seul prélèvement pour les aliments animaux.** `human_allocation=0.90` retire déjà 10 % du flux des cultures. `grain_feed_fraction_after_processing=0.10` ne doit pas retirer une deuxième fois 10 % au grain humain. Reconstituer un registre en tonnes : récolte, semences, résidus, nourriture humaine, grain pour animaux, stockage, transport. La viande issue de cette ration apparaît ensuite avec le rendement énergétique proposé de 7 % ; elle ne s'ajoute pas à des calories humaines du même grain. Retirer en priorité la ration des animaux de trait à la ration disponible, puis seulement le reliquat pour engraissement.

3. **Préparation et déchets de service.** Les cultures comprennent déjà `preparation_loss=0.02`. Les taux par milieu social de 2 %, 3 % et 8 % peuvent remplacer cette hypothèse moyenne ou décrire explicitement des déchets de repas supplémentaires. Il faut rendre ce choix visible. La perte de cuisson ne consiste pas à appliquer la densité du grain sec au poids du riz cuit.

4. **Traction agricole distincte de traction de transport.** Le rendement de travail de 65 jours-personnes/ha pour les céréales suppose un attelage. Les paramètres visibles donnent quatre animaux par chariot et leur ration, mais aucun quota d'attelages de labour ni leurs journées disponibles. Le bilan ne peut déclarer la capacité de labour assurée par la seule disponibilité de producteurs. Ajouter un plafond proposé de paires de labour / hectares / fenêtre de semis, avec foin, pâtures, grain et eau, ou déclarer cette dépendance non fermée. Le fourrage d'hiver des troupeaux et des attelages doit rester disponible après tout export humain ; les 0,15 t de grain/an par animal ne constituent pas tout son régime.

5. **ETP et pic mensuel cohérents.** `0.65 × 240 = 156` jours par producteur recensé est bien une capacité annuelle proposée. Pour le pic, préciser si les 20 jours/mois portent sur un ETP ou un producteur recensé : appliquer le facteur 0,65 une fois, pas deux. Ajouter les aides de moisson en jours effectivement retirés à leur autre activité, non en nouveaux habitants. La distribution mensuelle actuellement copiée est celle des céréales ; elle ne doit pas être appliquée identiquement au riz, aux racines, aux vergers et à tous les climats sans convention P annoncée.

6. **Terrain de rotation versus terrain cultivé.** `LAND.rotation` doit être un terrain physique et `MIX` des fractions de ce terrain. Pour chaque culture : hectares récoltés = terrain attribué × `cropped_fraction`. Les légumineuses, racines et céréales ont ici 2/3, le riz et les vergers 1. Appliquer la jachère une fois. Les pâtures sont séparées ; si une jachère nourrit des animaux, ne pas compter un deuxième hectare physique ni un deuxième fourrage identique.

7. **Quota marin explicite.** `marine_stock_t` est ambigu : si c'est une biomasse présente, elle n'est pas intégralement capturable chaque année ; si c'est une capture annuelle soutenable proposée, renommer / documenter ce sens. Les limites de travail maritime de 3 t/ETP/an et le quota écologique doivent être appliqués tous deux. La pêche douce, proposée à 40 kg/ha/an, porte sur surface productive accessible, pas une aire de région ou la mer entière. La chair à 55 %, la perte de conservation de 15 % et la densité de 1,5 M kcal/t portent sur trois étapes distinctes ; éviter de réappliquer leur produit.

8. **Stocks saisonniers, semences et réserve d'urgence.** Le tableau `STAPLE_HARVEST` totalise correctement 1, mais il propose une récolte unique concentrée sur les mois 7–8. Une réserve d'urgence de 90 jours n'est pas le stock nécessaire pour vivre jusqu'à la prochaine récolte : le grenier après récolte doit fournir alimentation jusqu'à celle-ci + semences + plancher d'urgence. La constitution initiale de 90 jours est une dépense de départ, pas 25 % de demande ajoutée tous les ans. La simulation doit conserver des stocks par produit, les unités et leurs pertes, pas déplacer instantanément des calories génériques entre produits.

9. **Population et demande de travail.** La pyramide physiologique proposée donne exactement 2 400 kcal/j de référence. Les besoins des adultes lourds y comprennent déjà un travail habituel. Les supplémentations de 150/50 kcal par jour travaillé doivent être déclarées comme effort supplémentaire / prime conservatrice, ou remplacer une partie du besoin de classe, pour ne pas expliquer deux fois la même activité. Le scénario géants ×8 en énergie et le scénario DMG ×16 en masse doivent rester deux variantes nommées ; aucune conversion implicite de kg en kcal.

10. **Changement des métiers V3 visible.** `FOOD_MIX` redistribue les individus entre métiers principaux, notamment de la pêche vers les cultures. Ce peut être un choix de conception V3, mais cela change les pourcentages et les profils urbains/ruraux. Il faut tracer la justification P de ce changement et conserver les sources locales, spécialités et exclusions. Il ne s'agit pas de simples tâches secondaires gratuites ni d'un mécanisme d'optimisation ajusté jusqu'à fermer le bilan. Les îles, Pearl Town et les sites institutionnels ne doivent pas recevoir tous le même mélange régional.

## Points satisfaisants à ce stade

- Année fixée à 360 jours ; plages de rendements et besoins conservées comme propositions.
- Surface, ETP, irrigation, captures et agents ont des paramètres séparés, définis avant résultat.
- Les quantités de golems et morts-vivants n'augmentent pas les habitants ; contrôle et entretien sont prévus, leur capacité devra être plafonnée par les emplois réellement disponibles et les matières.
- Le gibier reçoit biomasse, taux de prélèvement, fraction comestible, perte et plafond de travail distincts.
- La création magique périssable, la croissance des plantes et les réserves ont des paramètres explicites ; aucun portail pénombral automatique dans la référence.
- Les tarifs et taxes sont annoncés comme paramètres P ; les taxes en nature doivent transférer le stock, non retirer ses calories du continent.

## Statut de la revue

Pas de verdict de fermeture avant les fonctions de production, flux et stocks, ni avant le bilan final. Les tests nécessaires sont conservation de la masse par produit, traitement unique des pertes et aliments animaux, contraintes annuelles et saisonnières, besoins individuels, réserves physiques, et budgets des contrôleurs, attelages et bateaux. Les avertissements ont été transmis au rédacteur et au coordinateur.
