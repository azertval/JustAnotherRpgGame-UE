# Rendements, besoins et bilan alimentaire : entrées de V3

**Tous les paramètres de Tanares ci-dessous sont des propositions P**, distincts des effectifs régionaux/cultures attestés A. Date : 7 octobre 2026. Année = **360 jours** (SB255), pas365. Le JSON joint contient toutes valeurs avantarrondi et l’empreinte du modèle utilisé. Les résultats servent à tester/fixer surfaces, travail et transports ; aucune fermeture annuelle ou saisonnière ne peut être proclamée sans choisir les surfaces/cartes, capacités magiques et flux.

## Besoins : démographie, travail, espèces

La référence proposée est 2 400 kcal/j par équivalent humain tousâges, plage2 100–2 800; adulte travail manuel3 000–3 900, modéré2 400–3 000, léger1 900–2 400, enfants selon âge/croissance700–2 000 et adolescents1 800–3 000. Ces plages s’appuient sur les méthodes FAO, pas sur des mesures des espèces fantasy. Une pyramide P illustrative donnant exactement2 400 est30%adultes lourds3 400,20%adultes modérés2 600,10%adultes légers2 200,10%adolescents2 200,20%enfants1 300,10%âgés1 600. Les âges doivent être physiologiques à chaque espèce. Les enfants productifs/apprentis ne sont pas comptés adultes complets. Les taux d’activité V2 seuls ne donnent pas âge/masse/besoin.

Source : [FAO adultes](https://www.fao.org/4/y5686e/y5686e07.htm), [FAO enfants](https://www.fao.org/4/y5686e/y5686e06.htm).

Espèces P : humains et toutes espèces non étalonnées1 ; gnomes/halfelins0,70 ; orcs1,15 ; géants8 central, tests4/16. **DMG111 donne nourriture Huge8kg contre Medium0,5kg =×16 en masse, pas une mesure énergétique.** En motivation, ratio théorique masse16 à exposant2/3–3/4 donne6,35–8 ; étude originale [White/Seymour](https://pubmed.ncbi.nlm.nih.gov/12637681/) souligne précisément que l’exposant est disputé. Ce n’est ni preuve biologique des géants ni respect littéral DMG de leur masseration. Tester séparément demandecalories×8 et régime DMGmasse×16 avec composition/énergie des rations. Goodberry s’il nourrit un géant selon sort ne devient pas fraction globale offerte sans caster/slots/logistique. Nobles/élites ont besoin métabolique selon corps/travail, pas calories×5 par titre ; luxe change la composition, les pertes et les flux.

Besoin régional E_r =360×Σ_{âge,travail,espèce}(N×kcal_j×facteur_espèce). Central : E_r =N×864 000×facteur_pondéré. Les extincteurs de famine ne remplacent pas une pyramide d’âge ; sous-nutrition ne doit pas être transformée en besoins physiologiques plus faibles.

## Rendements et conversions fixés avant la fermeture

Définition : tonne récoltée à humidité spécifiée, pas récolte sur pied ; semences en tonnesdu même produit. Les céréales sont sèches, le riz est **paddy** puis décortiqué, racines/fruits humides. Pas de multiplication du poidsdu riz cuit par kcal/t du grainsec. Moudre/sécher/fairefromage ne crée pas calories ; dissocier retrait d’eau, résidus comestibles et vraies pertes.

| Filière | Rendement récolté P t/ha/an (plage) | Semences t/ha | Fraction annuelle cultivée du terrain | Net kcal/ha cultivé | J-personnes/ha/an |
|---|---:|---:|---:|---:|---:|
| cereal | 0.8 (0.5–1.2) | 0.16 | 0.667 | 1 726 744 | 65 (40–100) |
| rice | 1.5 (1.0–2.3) | 0.06 | 1.000 | 2 818 358 | 140 (100–200) |
| roots | 6.0 (3.0–10.0) | 0.8 | 0.667 | 2 806 877 | 95 (60–150) |
| legumes | 0.55 (0.3–0.85) | 0.08 | 0.667 | 1 243 123 | 70 (40–110) |
| orchard | 6.0 (2.0–10.0) | 0.0 | 1.000 | 1 964 655 | 110 (70–180) |

Paramètres supplémentaires P : céréales postrécolte/stockage8%, fractioncomestible/mouture95%, allocation aux humains90% (reste10% alimentationanimale ou autresusages identifiés), préparation2%; kcal/t3,50M. Paddy pertes8%, extractionriz67%, humain90%, préparation2%,3,60M kcal/t rizcomestible. Racines pertes15%, épluchage90%, humain90%, préparation2%,0,80M; légumineuses pertes10%, extraction98%, humain90%, préparation2%,3,40M. Fruits pertes25%, extraction90%, humain90%, préparation2%,0,55M. Pertes de transport interrégional séparées, **non incluses** dans rendements ci-dessus. La10%allocation n’est ni perte ni réserve annuelle ; elle doit aller dansun registre d’usage. Semences réservées avant toutcommerce, avecstock séparé et mortalité/germination explicites.

Sources : [dataset historique manorial](https://www.bahs.org.uk/crop-yields-database/the-data/), [chronologies](https://www.bahs.org.uk/crop-yields-database/chronologies/), [FAO limites riz pré1950](https://www.fao.org/agriculture/crops/thematic-sitemap/theme/spi/scpi-home/managing-ecosystems/sustainable-rice-systems/rice-how/en/), [FAO densités et humidité](https://www.fao.org/4/t0567e/T0567E0d.htm), [FAO pertes](https://www.fao.org/4/t0522e/t0522e04.htm). Ces documents motivent les ordres de grandeur ;0,8t blé,0,55t légumes secs,6t racines/fruits et leurs plages sont **calibrages proposés**, pas moyennes historiques universelles.

La jachère1/3 implique2/3 du terrainsemé annuel ; le riz prévoit **une seule récolte** annuelle, pas cultures moderneshaut rendement multiples. Le verger estpermanent. Des légumineuses peuvent remplacer certaines jachères si rotation explicitement recalculée, sans compter la même parcelle dans deux blocs. Aucunprélèvementimpôt/dîme n’est perte biologique : transfertàautres consommateurs ou au grenier, non soustractiondu totalcontinental.

## Contraintes de travail : recensement ≠ ETP

Budget P :1ETP=240jours×8h/an (plage200–260jours) ; actif producteur recencé=0,65ETP moyen (0,45–0,85), à remplacerpar travail tempscomplet/apprentis/tempspartiel réellement généré. Céréales avec attelage65j/ha récolté donc3,69ha/ETP/an;0,65ETP/personne donne2,4ha/personne **seulement sur contrainte annuelle**. Riz140j/ha donne1,71ha/ETP, racines95 donne2,53, legumes70 donne3,43, vergers110 donne2,18. Paramètres riz liés [exemple FAO150–200jours/ha](https://www.fao.org/4/T0715E/t0715e06.htm); [seule récolte manuelle80–160h/ha](https://www.fao.org/4/t0522e/t0522e05.htm) ne couvre pas culture/irrigation/transport. Céréales, racines, legumes et vergers sont P faute équivalent universel; ne pas caler cescoefficients après résultat.

Double contrainte : travail Σha_c×jours_c ≤ETP×240 ET, pour chaque mois, Σha_c×jours_c×part_m ≤ travailleurs_m×jours_disponibles_m. Répartition céréalesP sur12mois :2,4,14,12,12,8,15,20,9,3,1,0%; disponibilité20jours/mois. Au pic20%,65j/ha impose13j/ha dans mois : un travailleurfulltime couvre1,54ha au pic, contre3,69 annuel. Pour compter l’aide de familles/voisins/artisans en moisson, créer journées et kcal supplémentaires réellement prises à leurs autresactivités. Attelages/plough et fourrage/eau sont deuxième capanimal, zéro si pas disponibles. Les pourcentagesV2 ne décrivent aucun de cesjours. Les contraintes saisonnières ne sont donc pas validées dans table ci-dessous.

Golems, morts-vivants et élémentaires ajoutent des journéesproductives mesurables :nombre×heures/j×disponibilité×efficacité. Leur coût contrôleurs/maintenance/composants/énergie estattaché aux emplois appropriés, leurs récoltes utilisent mêmes terres/semences/pertes sauf mécanismemagiqueexplicit. Les golems ne transforment pas tout désert en champ; les morts-vivants ne produisent pas nourriture àconsommer eux-mêmes s’ils n’enont pasbesoin. Lesvivants de Storm/Taii requièrent des calories même si lestravailleurs sont artificiels.

## Élevage, pêche et chasse bornés

Registre végétal : récolte =semence +nourriture humaine +fourragegrain +usages autres +pertes +stockvariation +exports. **La même tonne de grain ne nourrit pas humains puis animaux.** Les fourrages grass/straw/sousproduits ne sont pas tous calorieshumaines et leur valorisation animale doit être séparée. Le lait livré auxhumains estaprès allaitementduveau; lactation et maintien reproducteurs imposent pâtures/foin/eau. Un troupeau n’est pas entièrement abattu chaqueannée. Le rendement P pâtural netretenu est0,15M kcal/ha/an (plage0,05–0,35M), horscalories déjàdugrain, climatmultiplicatif même coefficient que cultures par prudence. Cette valeur vise un troupeaufamilial herbivore faibleproductivité, doit céder à feuille troupeau espèce/parité/production/abattage; fourrages hiver et animauxde trait supplémentaires noncouverts. [FAO lait traditionnel aprèsveau](https://www.fao.org/4/t0251e/T0251E02.htm), [FAO distinction feeds/food](https://www.fao.org/4/x5303e/x5303e0e.htm).

Option grain-engraissement : P 8kg grain/kg viandecomestible (plage5–15) ET viande2M kcal/t →rendementénergétique≈7,1% dugrain3,5M kcal/t. Cette branche exige débitgrainadditionnel; porcs/volaille peuvent mieux convertir, mais aucun ratio industriel moderne choisi par défaut. Lespâtures de table sont supplémentaires auxrotations; si jachères ou chaumes pâturés, déduire ceshectares àpartir du fourrageréel, pas compter deux productionspâturales.

Poisson entier P : fractionchair0,55 (0,40–0,70),1,5M kcal/tchair(0,8–2,2M), pertesconservation15%(5–30%) →0,70125M kcal/tpoissonentier. Capturede travailP maritime3t/ETP/an, douce1,5t/ETP/an (sensibilité0,5–5t), avantcapécologique. Rendement eau douce P40kg/ha/an (10–100;5–20petitscours); cesbornes sontmotivées par [FAO captures/stock milieux](https://www.fao.org/4/y2785e/y2785e02.htm), non garantitexploitationdurable régionale. Captures limitées à min(captravail, productionstockautorisé, bateaujours/météo, transformationtransport). La mer doit recevoir étudestockproductif propre : ne pasmultiplier40kg par tout océan, ni assimiler perles àfishfood. [FAO chair/composition](https://www.fao.org/4/T0219E/T0219E02.htm).

Gibier P : prélèvementannuel≤10%biomasseciblée (plage5–15%) et viandecomestible50%(30–65%); utiliserproposédensité1–5kgbiomasse/haouespèces locales =faible rendement, pas viandeinfinie parchasseur. P0,5t animalentier/ETP chasseur/an maximum de travail de premieressai;3M kcal/t chair dense possible, résidupertes explicite. La chasse doit rester complément, notamment Tsvetan/Kolbjörn; sans habitat quantifié elle neferme pas deficitde10% de l’énergie. De même cueillir fruitsdans forêt non gérée n’égalepas verger6t/ha : centralP0,1–0,5t/ha selonmilieu, pas rendementforestiercanonique.

## Surfaces et travail nécessaires par région

Table conditionnelle à **régime P**, toutes denrées produites quelque part sansmagic. Les hectares restent **équivalents au lieu de production** : importerdéplace surfaceàexportateur, ne l’abolit pas. Ce n’est pas minimumgéométrique local si100%imports possibles. Pas de10%surplus, ni installationréserveannéeinitiale dans table ; champs incluentjachères, pâtures sont distinctes. Lesplafonds poissons/gibier et lespics main-d’œuvre restent à tester. Coefficient climatique P appliquéavantdéductionsemence : Empire1,10; Freelands1; Ben’net0,60; Kolbjörn0,75; MageTower1; Seashores1; Sindile0,85; Stravian1,05; Storm0,50; Taii0,45; Kepesh0,60 sousirrigation; Tsvetan0,65; Yama1.

| Région | Hab. source≈ | Eq.humains P | Besoin milliards kcal/an | Rotation cultures ha | Pâtures ha P | ETP cultures requis | ETP cultures V2×0,65 | Réserve90j t eq.grain |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Central Empire | 2 300 000 | 2 265 500 | 1957.4 | 1 317 267 | 949 039 | 256 211 | 378 619 | 151 971 |
| Republic of Freelands | 1 700 000 | 1 679 600 | 1451.2 | 988 040 | 967 450 | 193 719 | 129 655 | 112 669 |
| Imperial Ben’net | 445 000 | 445 000 | 384.5 | 306 001 | 1 281 600 | 63 805 | 6 938 | 29 851 |
| Kingdom of Kolbjörn | 720 000 | 1 224 000 | 1057.5 | 743 825 | 1 880 064 | 145 483 | 12 154 | 82 107 |
| Magocracy of Mage Tower | 867 000 | 867 000 | 749.1 | 539 917 | 249 696 | 107 372 | 105 618 | 58 159 |
| Seashores | 617 000 | 594 788 | 513.9 | 309 998 | 171 299 | 65 180 | 724 | 39 899 |
| Sindile Forest | 432 000 | 428 112 | 369.9 | 286 505 | 58 022 | 76 296 | 72 512 | 28 718 |
| Stravian Domains | 960 000 | 908 160 | 784.7 | 572 704 | 249 095 | 115 347 | 193 646 | 60 920 |
| Storm Islands | 386 000 | 386 000 | 333.5 | 578 720 | 222 336 | 113 941 | 3 171 | 25 893 |
| Taii’Maku City States | 698 000 | 698 000 | 603.1 | 1 332 349 | 893 440 | 260 223 | 19 943 | 46 822 |
| Theocracy of Kepesh | 695 000 | 695 000 | 600.5 | 842 910 | 667 200 | 170 717 | 27 973 | 46 621 |
| Tsvetan | 468 000 | 529 776 | 457.7 | 455 766 | 938 926 | 93 697 | 50 772 | 35 538 |
| Yama | 793 000 | 793 000 | 685.2 | 298 996 | 274 061 | 119 908 | 205 232 | 53 195 |

Ce contrôle de travail compare producteurs de culturesagriculture/céréales/riz/maraîchage/vergers/tubercules au besoin calculé ; cueilleurs/pêcheurs/éleveurs ne sont pas convertis gratuitement en laboureurs. Une couvertureannuelle<1demande ETPsupplémentaires ouproductionimportée/golementretiens/sort documenté. Unecouverture>1n’est pas preuve d’autosuffisance : ressources/eau, picscalendrier, stockage, troupeaux/bateaux et demandesvariantes restentcontraignants.

Régimes énergétiques P, pourcents cereal/rice/roots/legumes/fruits/livestock/fish/game :
- **Central Empire** : [70, 0, 8, 7, 4, 8, 2, 1]. Céréales et élevage attestés; terresfertiles. Surplus et export à mesurer, rôle grenier impérial pas rendement canonique. — SB90,91.
- **Republic of Freelands** : [60, 0, 8, 8, 4, 10, 6, 4]. Disponibilités de sols variables/nouvelles communautés; importations et miseenculture prioritaires; Winterhold morts-vivants ajoutent travail, pas terres/kcal. — SB104,105.
- **Imperial Ben’net** : [25, 0, 25, 5, 0, 30, 10, 5]. Tubercules/élevage/pêche attestés, communautés cirrus autosuffisantes localement. Part céréales candidate25% doit souvent être importée; isolément certains villages peuvent remplacer céréales par tubercules. — SB120,121.
- **Kingdom of Kolbjörn** : [40, 0, 15, 5, 0, 20, 15, 5]. Froid saisonnier, pêche profonde possible et géants10% créent forte demande; pâture/hiver et transport fourrages contraignants. — SB128,129.
- **Magocracy of Mage Tower** : [60, 0, 10, 10, 5, 5, 9, 1]. Pêche eau douce et agriculture de vallées, beaucoup denonmage travailleurs. Magie réseau ne prouve pas agriculture améliorée; importer vivrier en tours/campus. — SB138,139.
- **Seashores** : [45, 0, 15, 8, 7, 5, 19, 1]. Pêche et conservation centrales, îles agricoles seulement oùsol; grain importé plausible; forte part pêcheurs ne signifie pas caloriesinfinies. — SB146,147.
- **Sindile Forest** : [20, 0, 25, 15, 30, 2, 4, 4]. Végétarisme majoritaire, miel/bois et rarités; sols dansombre ne deviennent pas champs céréaliers. Terres ci-dessous équivalent champs/jardins entretenus, ni toute forêt ni magiegratuite. — SB152,153.
- **Stravian Domains** : [65, 0, 10, 10, 7, 5, 2, 1]. Halfelins vergers et fermes granary explicit; déficit animaux/cuir. Estimer surface fey améliorée et travailleurs avant multiplier rendement. — SB160,161.
- **Storm Islands** : [55, 0, 25, 5, 0, 5, 8, 2]. Céréales/tubercules/pêche avancée, quasiauautosuffisance explicit, rares producteurs vivants car undead réalisent travail. Leurs ETPdoivent être chiffrés avant valider. — SB168,169,170.
- **Taii’Maku City States** : [60, 0, 10, 10, 5, 10, 4, 1]. Illus mouvantes et golems; agriculture hors wagon ou imports/foodmagic requis. P coefficientaride. Ne pas créer champs sous mobilecity dans chaque désert. — SB174,175,178.
- **Theocracy of Kepesh** : [60, 0, 5, 10, 10, 10, 4, 1]. Bétail/déserts/vallées irriguées: coefficientcentral suppose oasis/irrigation localisées; sol sec non irrigué n’a pas cesrendements. — SB182,183.
- **Tsvetan** : [40, 0, 15, 10, 5, 20, 3, 7]. Sec/roche/élevage/chasse; plafonner gibier. Faible céréaleslocales peut exiger import; rogner7% game diet si milieu insuffisant. — SB190,191.
- **Yama** : [10, 60, 5, 7, 5, 6, 6, 1]. Riz humidité/plaines très cohérents, soie et thé horscalories. Rendement paddy manuel1.5t/ha pas hybrides modernes. — SB198,199.

Sensibilité Kolbjörn géants10% :
- Facteurénergie géant **×4 P** : 936 000 équiv.humains; 808.7 milliardskcal/an; 568 807ha rotation et 1 437 696ha pâture àrégimeidentique. ×16est varianteénergieproportionnellemassedejeu, pas loiFAO.
- Facteurénergie géant **×8 P** : 1 224 000 équiv.humains; 1057.5 milliardskcal/an; 743 825ha rotation et 1 880 064ha pâture àrégimeidentique. ×16est varianteénergieproportionnellemassedejeu, pas loiFAO.
- Facteurénergie géant **×16 P** : 1 800 000 équiv.humains; 1555.2 milliardskcal/an; 1 093 860ha rotation et 2 764 800ha pâture àrégimeidentique. ×16est varianteénergieproportionnellemassedejeu, pas loiFAO.

Undertanares/Darkall populationsinconnues : exprimer par10 000équiv.humains =8,64milliardskcal/an; utiliser régimedechaque communauté et surfaces éclairées/forage/imports. Mystical habitantsundead : pas0personne, mais besoin nourrituredecréaturesàdéfinir parnature etnon assimiler au besoinhumain. Livantsvisiteurs1000P demandent0,864milliard/an pourrésidenceannéeentière; rien si aucun Nchoisi. Aucun totalcontinental universel prouvé àpartir des13régions chiffrées seulement.

## Annuel, saisons, pertes de convoyage et réserves

Pour chaque produitphysique j et régionr, travailler tonnes et énergie séparées :

`Stock_fin = Stock_debut + récoltes_net + imports_livrés + création_magique_effective - consommation - feed - semences_utilisées - exports_chargés - pertes_stockage - autres_usages`

`imports_livrés = exports_chargés_origine × (1-perte_trajet)` ; une perte de trajet est comptée une fois, àla réception. Les deux régions doivent pointer le mêmeflux et produit. Si productionnet ci-dessus a déjà8%perte annuellestock, ne redéduire pas8% dans stockmensuel : choisir simulationmensuelle exacte OU approximationannuelle, jamaisles deux.

GrainsP localtransport2%(0,5–4), caravaneroute8%(3–15), maritime5%(2–12); racines/fruits frais15%(8–30), poissonsfrais25%(10–50) si trajetlongnonprotégé. Produits séchés/salés ramener périssabilité au niveaugrain mais rendement matièreavanttransport reste fractionchair+séchageexplicit. Pertes attaques/pillage : fractionstochastique séparée; récupéréeparpiratesne disparaîtpasducontinental si redistribuée, mais disparaît du destinataire. Conversion conservation doit tracer résidus/combustible/sel/travail et stock produittransformé.

Annuel centralfermé en régime stationnaire : Σr(kcalproductioneffective+magieeffective-kcalconsommation-kcallost)=0 si monde total etstocksconstants; chaque région peut exporter/importer. Imports Darkall ne peuvent être sourceillimitée parce que populationestnull : autoriser fluxexogèneP plafonné oufermermodèle producteur Darkall. Fermer seulementaux frontières13régions doit déclarer apports exogènes.

Sécurité P90jours pleinbesoinhumain,180jours froid/siègesinsulaires,30–60comptoir approvisionnéhebdo. Réserve=besoinjournaliers×jours/protectionpertes, stockphysique produitsecéquivalent. 90jours ajoutent25%demandecentrale pourconstitutioninitiale (180=50%); enstationnaire neconsommer pasetneproduire pas25% chaqueannée : seulrecomplètementpertes/déstockage. Réserve définitstockplancher d’urgence, **ne couvre pas enelle-même le pont saisonnier** : après récolteunique il fautconsommationjusqu’àrécoltesuivante +réserved’urgence +semences. Les réservoirs/glaciers de nourriture n’apparaissentpas sans grenier/personnel.

Simulation12mois×30joursP : récoltegrain70%mois8+30%mois9 (Nord pluscourte/plus tard àproposer), racines60%mois9+40%mois10, vergersétalés6–10, rizmois9une récolte, pêchecontinuelledisponibilitésmétéoetfrai; adaptéaucalendriersaisonsTanaresparcarte. Travail lourd augmentebesoinP15% surdeuxmoisdemisson et doit baisser/adapter ailleurs si2 400estmoyenneannuelle. Le testminstock mensuel≥0 ET stockurgenceplancher estplusimportant qu’une égalitéannuelle qui échoue ensoudure.

Mauvaiserécolte test P−30%surgrainetlegumes,−20%racines, transport−30%pendant2mois, besoin+10% en froid/effort. Avec un objectif90joursréserves et marge10%, un déficit annuelgrain30% peut épuiserreserveavantpremierprintemps: calculerstockavec calendrier, interdictionvendresemences, prioritérationdebase. Mesurestaxes/réquisitions récupèrentstock/exchanges, pas rendements nouveaux.

## Relier le modèle aux métiers et classes sociales

Nommergrenierspublics/communautaires, stocksprivés, propriétaires, tributetdîme, droitsemencesetcompensation. Un exploitantpeutpayeren grain sanspertecontinental; le grenier peut avoir problème d’accès/richessedistribution même bilanphysiquepositif. Elitesnoblessefondentqui contrôle, pasqui mangephysiquement. BudgetannuelP parsite stockage : capacité t, magaziniers/gardiens/carriers/maintenance, tonne-joursoccupation, fumigationsséchagemanuelle/tri, misesàdisposition, rémunération/réquisitions etindemnisationtransporteurs. Aucunprixinventé ici; raccorder futursprixgrain/tauxsalaires auxmétiers déjàmodélisés.

Pour le simulategénéral, budgetsphysiques précèdent flux : solsfertiles+irrigation+travailattelageproduisentmaximum; on ne choisit pas hectares/ouvrier pour annuler déficit. Lesparamètrescentre etbornesJSON permettent scénarioresilient/mauvais. Les valeursstresstests ne forment pas dossier nutritionnel complet : contrôler aussi proteinP45g/eq.humain/j(35–60), lipidesP20–30%kcal, diversitéetmicronutriments, eaupotable etchauffage; un bilan kcal seul ne justifie pasvivre uniquement poissonoufruit.

## Limites documentaires

Sourcesprimaires modernes FAO serventdebornes physiques et méthodes, pas preuve agricultureEurope1300universelle. Lescomptesmanoriaux concernentdomainesprincipalementanglais, paschaqueterritoireTanares; climaticmultipliers/diets/pastures/labouraveragePàmesurerouvalider. AucunepopulationmunicipaleV3n est devenuecanonique. LesdatesourcecalendarSB255 etDMG111fourniestégantes doivent resterrecoupéesparagentmagie. Tous motscollés dans JSON descriptive notes sontconvention script, aucunidentifiantsource changé.
