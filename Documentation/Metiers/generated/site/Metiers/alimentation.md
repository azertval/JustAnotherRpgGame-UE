# Tanares nourrit ses habitants par échanges

**Le scénario V3 calculé couvre les besoins énergétiques annuels de 13/13 régions chiffrées.** Les 66 contrôles de conservation et de contraintes passent. Le résultat est une proposition de conception du 7 octobre 2026 : terres, rendements, métiers qualifiés, réseaux, revenus et technologies proposées restent P. Le calcul conserve semences, fourrages, pertes, eau, travail, matière transportée, stocks et populations. La fermeture énergétique ne certifie ni nutrition complète, ni propriétés magiques, ni réalisation historique des investissements. La mauvaise récolte provoque des déficits chiffrés après les mêmes stocks de départ ; ils demeurent visibles.

Le dossier complète [Métiers et populations de Tanares](rapport-populations.md) : les métiers de base, spécialisations et matrices sociales y sont définis. Les résultats détaillés se trouvent dans le [bilan alimentaire V3](Donnees/metiers-tanares-alimentation-v3.json) et le [registre magique V3](Donnees/metiers-tanares-magie-v3.json). Les descriptions des cultures et institutions sont attestées **A**, leur traduction en mécanismes est parfois déduite **D**, et leurs quotas ou quantités calculées sont proposés **P**. Un nombre calculé à partir d'hypothèses P reste P.

## Des habitants aux tonnes : les besoins précèdent les capacités

### L'année compte 360 jours et les géants imposent deux scénarios

Le calendrier tanaréen comporte **douze mois de trente jours**, avec le premier mois au début de l'été. Le modèle n'utilise donc pas une année terrestre de 365 jours. La référence énergétique proposée est **2 400 kcal par jour et par équivalent humain**, tous âges confondus, avec une sensibilité de 2 100 à 2 800 kcal. Le besoin annuel de référence vaut ainsi **864 000 kcal par équivalent humain**. La méthode relie le métabolisme, la masse, l'âge et l'activité ; elle ne déduit pas un besoin physiologique du seul statut « actif ». ([Sourcebook, p. 255](Sources/sb.md), [FAO, besoins énergétiques des adultes](https://www.fao.org/4/y5686e/y5686e07.htm), [FAO, enfants et adolescents](https://www.fao.org/4/y5686e/y5686e06.htm)).

La pyramide physiologique centrale est une convention P : 30 % d'adultes aux activités lourdes à 3 400 kcal/jour, 20 % aux activités modérées à 2 600, 10 % aux activités légères à 2 200, 10 % d'adolescents à 2 200, 20 % d'enfants à 1 300 et 10 % de personnes âgées à 1 600. Elle donne exactement la moyenne de 2 400 kcal. Les âges sont physiologiques : les durées de croissance des espèces ne sont pas remplacées par un seuil humain universel. Le calcul effectif ajoute ses suppléments de travail et les pertes de service ; il conserve donc séparément besoin de référence et demande finale à livrer.

Les coefficients énergétiques P sont de 0,70 pour les gnomes et les halfelins, 1,15 pour les orcs, 1 pour les espèces sans calibration particulière, et **8 pour les géants dans le scénario central**. La règle de nourriture du Guide du Maître donne cependant **8 kg de nourriture et 56 litres d'eau par jour pour une créature Très Grande**, contre 0,5 kg et 3,5 litres pour une créature Moyenne. Elle impose une comparaison par masse de ration ; elle n'établit pas directement le nombre de calories d'une espèce. Le dossier conserve donc une variante énergétique ×16 et vérifie séparément la masse et la composition de la ration géante. Le facteur central ×8 est un pont de conception, motivé par des ordres de grandeur allométriques, dont l'exposant est lui-même discuté ; ce n'est pas une loi biologique de Tanares. ([Guide du Maître, p. 111](Sources/gm.md), [White et Seymour, étude originale sur l'allométrie des mammifères](https://pubmed.ncbi.nlm.nih.gov/12637681/)).

### Un hectare semé n'est pas un hectare de rotation

Le tableau suivant fixe les rendements centraux de référence avant la simulation. Les céréales sont des grains secs, le riz est d'abord du **paddy**, et les racines et fruits sont pesés frais. Les pertes de poids par retrait d'eau ne sont pas assimilées à une destruction de calories. La cuisson, la mouture et la fabrication du fromage ne créent pas de nourriture à partir de calories déjà comptées. Les comptes agricoles historiques permettent de choisir des ordres de grandeur préindustriels, mais ils ne mesurent pas les champs de Tanares. ([Base originale de rendements médiévaux](https://www.bahs.org.uk/crop-yields-database/the-data/), [FAO, composition des céréales et tubercules](https://www.fao.org/4/t0567e/T0567E0d.htm)).

| Culture | Récolte centrale, t/ha cultivé/an | Plage proposée | Semences, t/ha cultivé | Fraction annuelle cultivée du terrain | Travail, jours-personnes/ha cultivé/an |
|---|---:|---:|---:|---:|---:|
| Céréales sèches | 0,80 | 0,50–1,20 | 0,16 | 2/3 | 65 |
| Riz paddy | 1,50 | 1,00–2,30 | 0,06 | 1 | 140 |
| Racines et tubercules | 6,00 | 3,00–10,00 | 0,80 | 2/3 | 95 |
| Légumineuses sèches | 0,55 | 0,30–0,85 | 0,08 | 2/3 | 70 |
| Verger entretenu | 6,00 | 2,00–10,00 | Stock de plantation distinct | 1 | 110 |

La jachère occupe un tiers des blocs concernés : un terrain de 150 hectares portant une culture à fraction 2/3 donne 100 hectares récoltés dans l'année. Les vergers sont permanents et le riz prévoit une récolte annuelle, sans hybride industriel ni deuxième récolte automatique. Les valeurs centrales du travail restent P. À titre de borne physique, la FAO donne un exemple de petite riziculture demandant 150 à 200 jours-personnes par hectare selon l'équipement ; les 80 à 160 heures de récolte à la faucille ne couvrent que cette opération. ([FAO, évaluation des systèmes d'exploitation](https://www.fao.org/4/T0715E/t0715e06.htm), [FAO, récolte manuelle du riz](https://www.fao.org/4/t0522e/t0522e05.htm)).

Les facteurs climatiques proposés sont appliqués à la récolte brute avant retrait des semences : Empire 1,10 ; Freelands 1 ; Ben'net 0,60 ; Kolbjörn 0,75 ; Mage Tower 1 ; Seashores 1 ; Sindile 0,85 ; Stravian 1,05 ; Storm Islands 0,50 ; Taii'Maku 0,45 ; Kepesh 0,60 ; Tsvetan 0,65 ; Yama 1. Les valeurs de Kepesh supposent des périmètres cultivables disposant d'eau : elles ne s'appliquent pas indistinctement au sable. Le sol, la main-d'œuvre et l'eau sont trois plafonds indépendants. Les hectares proposés ne sont pas présentés comme un relevé cadastral obtenu par la seule carte.

Le calcul protège les semences avant tout export. Il sépare ensuite les fractions comestibles, les aliments destinés aux animaux, les pertes physiques et les stocks. Les densités énergétiques P sont de 3,50 millions de kcal par tonne de céréales comestibles, 3,60 pour le riz, 3,40 pour les légumineuses, 0,80 pour les racines et 0,55 pour les fruits. Les rendements nets sont recalculés avec les opérations effectives du bilan ; un ancien rendement net intégrant des pertes de stockage ne doit pas subir une seconde déduction identique dans les stocks mensuels. La FAO montre que les pertes varient par étape et par contexte : un taux global n'est pas une constante universelle. ([FAO, pertes après récolte](https://www.fao.org/4/t0522e/t0522e04.htm)).

### Le travail impose un plafond annuel et un plafond de saison

Un **équivalent temps plein, ETP, vaut 240 journées de travail par an**. Un producteur recensé représente en moyenne 0,65 ETP, soit **156 journées**. Cette convention rend visibles les apprentis, les aides familiales et le temps partiel. Les jours de travail mensuels du scénario effectif sont répartis selon le calendrier agricole tanaréen ; les mois de pointe autorisent jusqu'à **26 journées par producteur concerné**, sans augmenter ses 156 journées annuelles. Il faut satisfaire à la fois le total annuel et chaque mois. Une capacité suffisante en hiver ne compense pas une récolte impossible au mois de pointe.

La référence effective place les céréales en M2–M3, le riz en M4, les racines en M4–M5 et les fruits en M1–M5. Le modèle mobilise aussi **25 % des autres occupés pendant vingt journées** pour l'aide saisonnière. Ces personnes gardent leur métier principal, mais leurs journées sont explicitement retirées à leur autre activité et leur effort supplémentaire entre dans les besoins. Le paramètre n'ajoute ni habitants ni emploi agricole à temps plein. Les animaux de trait, leurs rations, leurs journées et leurs besoins d'eau sont suivis à part ; compter le grain de leur alimentation parmi la consommation humaine puis parmi leur production animale constituerait un double compte.

L'élevage transforme des fourrages et des sous-produits en lait, viande ou œufs ; le lait accessible aux humains est calculé après les besoins du jeune animal. Le rendement pâtural central proposé est de 150 000 kcal nettes par hectare et par an, ajusté au climat, avec un plafond de travail de 35 hectares par ETP. Le grain consacré à l'engraissement est retiré du stock alimentaire, puis converti avec une efficacité énergétique P de 7 %. Ces conventions privilégient les systèmes familiaux et herbagers, sans appliquer à la chaîne médiévale les rendements de vaches laitières modernes. ([FAO, lait traditionnel et alimentation des jeunes](https://www.fao.org/4/t0251e/T0251E02.htm), [FAO, concurrence entre aliments humains et aliments animaux](https://www.fao.org/4/x5303e/x5303e0e.htm)).

La pêche est plafonnée à la fois par le travail et par la ressource. Les références P sont de 3 tonnes de poisson entier par ETP maritime et par an, et 1,5 tonne en eau douce. Le poisson entier fournit une fraction comestible centrale de 55 %, à 1,5 million de kcal par tonne de chair, avec 15 % de pertes de conservation. Le plafond d'eau douce de 40 kg par hectare productif et par an ne s'applique pas à toute la mer. Les quotas marins sont des captures annuelles proposées. Le gibier dispose de sa propre biomasse, d'un prélèvement maximal et d'un plafond de travail ; les cueilleurs ne bénéficient pas du rendement d'un verger entretenu sur toute la forêt. ([FAO, rendements des milieux aquatiques](https://www.fao.org/4/y2785e/y2785e02.htm), [FAO, composition et fraction comestible des poissons](https://www.fao.org/4/T0219E/T0219E02.htm)).

## Les régions produisent selon leurs terres et leurs institutions

La première sortie annuelle du scénario d'investissement donne les surfaces cultivées et les couvertures ci-dessous. **Couverture** signifie ressources alimentaires livrables après les opérations retenues, rapportées à la demande finale calculée. Une valeur de 1,000 ne démontre ni une marge face aux crises, ni une alimentation suffisante dans chaque ville à chaque mois. Les chiffres de population sont approximatifs dans les livres ; les hectares et les couvertures sont des résultats P du modèle.

| Région | Habitants | Hectares cultivés/an | ETP producteurs vivants | Couverture annuelle | Réserve d’urgence |
|---|---|---|---|---|---|
| Central Empire | 2 300 000 | 1 232 877 | 408 098 | 1,299 | 90 jours |
| Republic of Freelands | 1 700 000 | 760 549 | 226 272 | 1,000 | 90 jours |
| Imperial Ben’net | 445 000 | 106 667 | 60 775 | 1,000 | 180 jours |
| Kingdom of Kolbjörn | 720 000 | 390 174 | 117 852 | 1,000 | 180 jours |
| Magocracy of Mage Tower | 867 000 | 482 759 | 152 899 | 1,365 | 90 jours |
| Seashores | 617 000 | 78 571 | 52 411 | 1,000 | 90 jours |
| Sindile Forest | 432 000 | 179 592 | 84 911 | 1,079 | 90 jours |
| Stravian Domains | 960 000 | 664 617 | 209 697 | 1,362 | 90 jours |
| Storm Islands | 386 000 | 418 821 | 10 114 | 1,093 | 180 jours |
| Taii’Maku City States | 698 000 | 168 718 | 19 278 | 1,000 | 90 jours |
| Theocracy of Kepesh | 695 000 | 344 828 | 117 637 | 1,001 | 90 jours |
| Tsvetan | 468 000 | 284 746 | 90 145 | 1,009 | 90 jours |
| Yama | 793 000 | 298 574 | 189 857 | 1,184 | 90 jours |

Ces résultats sont tirés du [bilan annuel V3](Donnees/metiers-tanares-alimentation-v3.json). Les ETP de ce tableau sont les affectations des producteurs vivants aux cultures : les aides saisonnières et les capacités des agents non vivants sont enregistrées séparément. Les hectares de rotation, plus étendus que les hectares cultivés lorsque des terres sont en jachère, restent des plafonds P séparés.

| Région | Demande finale | Imports livrés | Exports chargés | Stock de travail initial | Réserve d’urgence initiale |
|---|---|---|---|---|---|
| Central Empire | 2 045,82 | 3,15 | 262,55 | 150,53 | 511,45 |
| Republic of Freelands | 1 514,52 | 196,38 | 487,42 | 115,95 | 378,63 |
| Imperial Ben’net | 402,34 | 41,73 | 0,00 | 22,69 | 201,17 |
| Kingdom of Kolbjörn | 1 105,64 | 311,37 | 0,00 | 45,62 | 552,82 |
| Magocracy of Mage Tower | 782,74 | 0,00 | 0,00 | 47,63 | 195,69 |
| Seashores | 537,16 | 123,39 | 0,00 | 9,26 | 134,29 |
| Sindile Forest | 386,09 | 0,00 | 0,00 | 9,32 | 96,52 |
| Stravian Domains | 820,16 | 0,00 | 655,99 | 105,88 | 205,04 |
| Storm Islands | 349,28 | 0,00 | 0,00 | 26,74 | 174,64 |
| Taii’Maku City States | 625,55 | 459,12 | 0,00 | 7,17 | 156,39 |
| Theocracy of Kepesh | 628,43 | 604,63 | 483,28 | 23,78 | 157,11 |
| Tsvetan | 478,81 | 0,00 | 0,00 | 29,37 | 119,70 |
| Yama | 716,12 | 0,00 | 3,50 | 88,38 | 179,03 |

**Toutes les valeurs du second tableau sont en milliards de kcal ; les demandes et flux portent sur une année de 360 jours.** Les deux dernières colonnes sont des stocks au démarrage, et non des productions annuelles. Imports et exports ne sont pas égaux après sommation : les pertes du transport sont retirées entre le chargement et la livraison. Kepesh apparaît à la fois importateur et exportateur parce que ses dépôts constituent un relais vers les cités taii'maku ; l'alimentation achetée n'est pas comptée comme récolte locale. ([Registre des flux et stocks V3](Donnees/metiers-tanares-alimentation-v3.json)).

Le rôle des régions reste conforme aux filières décrites dans les livres. L'Empire dispose de terres agricoles et d'élevages ; Stravian combine mines et production des fermes et vergers halfelins, tout en important une partie du bétail et du cuir. Yama produit du riz, tandis que le thé et la soie restent exclus des calories. Ben'net repose sur les tubercules, l'élevage et la pêche ; les communautés cirrus ont des circuits locaux qui ne sont pas assimilés à un commerce continental uniforme. Seashores fournit une forte filière maritime, sans devenir un réservoir illimité de poissons. ([Sourcebook, p. 90–91](Sources/sb.md), [p. 120–121](Sources/sb.md), [p. 146–147](Sources/sb.md), [p. 160–161](Sources/sb.md), [p. 198–199](Sources/sb.md)).

Le scénario V3 redistribue les **métiers principaux à l'intérieur du groupe des producteurs vivriers**, tout en conservant le nombre total des personnes, les habitants, les espèces et les strates sociales. Ce changement est une révision P des affectations professionnelles. Il ne suppose pas que les pêcheurs pratiquent gratuitement une deuxième activité céréalière ni qu'un collège entier se transforme en exploitation agricole. Les activités particulières des villes sous-marines, des sanctuaires et des établissements d'étude gardent leurs contraintes locales.

Les populations d'Undertanares et de Darkall ne sont pas publiées. Leur alimentation est donc décrite par **tranches de 1 000 équivalents humains**, représentant une référence de 864 millions de kcal par année tanaréenne, puis adaptée aux espèces et aux consommateurs réellement retenus. L'Undertanares doit recevoir une source de matière organique, un substrat, du travail et des échanges : une récolte de champignons ne crée pas de calories indéfinies sans intrants. Les apports de Darkall ne sont pas un flux extérieur gratuit ajouté au déficit des treize régions. Mystical conserve ses habitants morts-vivants et ses éventuels visiteurs vivants dans des registres distincts ; le dossier n'y invente ni champs paysans ni population nulle. ([Sourcebook, p. 206–211](Sources/sb.md)).

La magie intervient par **cohortes entières de praticiens**, avec métiers d'origine, formations, sorts admissibles, emplacements disponibles, journées de service et contraintes de distribution. Une personne capable de fabriquer un objet n'est pas automatiquement un druide, un prêtre de haut niveau ou un transporteur de tonnes par portail. La création de nourriture périssable sert les consommateurs proches et son expiration empêche de la traiter comme un stock exportable. La croissance des plantes ajoute un rendement seulement sur les surfaces effectivement couvertes, avec une union contrôlée des périmètres : plusieurs services sur une même parcelle ne multiplient pas indéfiniment la récolte. Le miel, les vergers féeriques et les soins des arbres de Sindile ne sont pas des permissions générales d'annuler toute contrainte agricole.

| Mécanisme attesté | Capacité de la règle | Convention de service V3 |
|---|---|---|
| Baies nourricières, sort de niveau 1 | Jusqu'à dix baies ; une baie nourrit une créature pour une journée, sans plafond de taille indiqué ; effet perdu après 24 h | Créatures-jours affectées à des bénéficiaires, eau séparée ; aucune baie périssable dans la réserve annuelle |
| Création de nourriture et d'eau, sort de niveau 3 | 22,5 kg de nourriture et 120 litres d'eau ; quinze humanoïdes ou cinq montures pour 24 h ; nourriture périssable | Quinze bénéficiaires admissibles au maximum, sans transformer 22,5 kg en quarante-cinq rations ; géants de type géant exclus de l'assimilation automatique aux humanoïdes |
| Croissance végétale, enrichissement de huit heures | Périmètre de rayon 800 m dans la traduction retenue, soit environ 201 ha ; production augmentée selon le sort | Vingt journées de service proposées ; fraction utile et nouvelle surface proposées de 0,375 du disque ; union contrôlée plafonnée à 25 % des cultures retenues |

Les mécanismes viennent des [MJ, p. 217 et 230–231](Sources/mj.md). Les fractions utiles, quotas, journées et bénéficiaires sont P. Le service alimentaire retient 240 journées par praticien, avec **rotation des participants sur les 360 jours** : le tiers de l'année restant n'est pas oublié ni financé par un deuxième emploi gratuit. Le registre garde les effectifs entiers et le nombre de personnes simultanément en service. Une fiche générique d'acolyte ou de druide ne prouve pas que ces sorts sont préparés ni que les emplacements de niveau 3 existent ; qualification et préparation sont donc vérifiées avant attribution du quota. ([Manuel des Monstres, p. 342 et 345](Sources/mm.md), [registre magique V3](Donnees/metiers-tanares-magie-v3.json)).

Les agents non vivants sont un stock de travail séparé des résidents et borné par les cohortes de contrôle et d’entretien. Le parc taii soutenu est de 81 825 unités ; ses noyaux P représentent 0,040912 tonne initiale et leurs remplacements 0,008182 tonne/an. La masse des micro-noyaux est une technique proposée, tandis que l’obligation d’entretien SB346 est appliquée. L’entretien ne dispense pas de l’approvisionnement en minerai ni de son prix source600–800 gp/livre ; le central arrondi est P1,54 milliongp/t. Les 180000unités souhaitées ne sont pas toutes comptées productives.

## Les corridors et les greniers ferment la chaîne matérielle

### Les grandes villes consomment au-delà de leurs limites

La Capitale impériale de **680 000 habitants** et Fisherman's Wharf de **570 000 habitants** ne sont pas des fermes autosuffisantes. Le dossier distingue la consommation résidente, les emplois réellement situés dans le noyau, les producteurs de son arrière-pays, les ports ou terminaux et les stocks urbains. Les débits physiques doivent couvrir chaque arrivage, pas seulement dessiner une route reliant deux villes. Les effectifs de garnison sont intégrés selon une convention résidentielle explicite, sans ajouter une seconde fois leurs habitants. ([Sourcebook, p. 98–99](Sources/sb.md), [p. 111–113](Sources/sb.md)).

Le calcul attribue à la Capitale 603,07 milliards de kcal de demande annuelle et à Fisherman’s Wharf 507,10. Leurs entrées d’arrière-pays sont respectivement 480,88 et 153,34 milliards de kcal ; leurs imports régionaux attribués 2,85 et 144,39. Les flux internes sont conservés une seule fois dans la région. Les couvertures calculées sont 1,056 et 1,000. La capacité locale détaillée des rues et terminaux n’est pas certifiée par cette allocation P.

L'échelle de la carte mondiale est relevée à **0,5294105 km par pixel**, avec une incertitude de lecture d'environ 1 %. Les trajets sont des corridors explicités : un segment entre deux centres ne devient pas une route canonique. Le tracé, les détours, le mode et une marge d'incertitude sont conservés. Une nouvelle voie est P même lorsque les villes qu'elle relie et la possibilité du véhicule sont attestées. Les convois sont dimensionnés par charge utile, voyages annuels, durée aller-retour, entretien et capacité du terminal. ([Relevé cartographique et corridors](Archives/alimentation-cartes_echanges.json)).

| Infrastructure du scénario d'investissement | Longueur ou implantation | Parc proposé | Portée documentaire |
|---|---|---:|---|
| Train Stravian–Kepesh | 1 500 miles | 300 rames | Corridors et parc P |
| Train Empire–Fisherman's Wharf | 1 900 miles | 160 rames | Corridors et parc P |
| Train Empire–Ben'net | 923 miles | 28 rames | Corridors et parc P |
| Cargos Fisherman's Wharf–Kolbjörn | Couloir maritime retenu | 160 cargos | Quota de flotte P |
| Cargos Goldraft–Bluhaven | Couloir maritime retenu | 90 cargos | Quota de flotte P |

Le scénario emploie des rames de vingt wagons pour **80 tonnes utiles par rame**, en distinguant la base documentaire du véhicule des charges, parcs et performances P de la nouvelle infrastructure. Le coût annuel de l'exploitation reste distinct de la construction de la flotte, des voies, des greniers et des terminaux. La référence proposée d'énergie est de 1 000 kWh par gramme de bauronite, et le train consomme 0,05 g par kilomètre et par rame. Ces coefficients ferment un budget de scénario ; ils ne décrivent pas une caractéristique mesurée du minerai magique.

Dans le registre de fret actualisé, les masses suivantes sont les cargaisons physiques après pertes, et non des tonnes équivalent grain : E2 Yama–Empire : route au nord de Mystical : 900 t/an; E3 Capital–Northcross–Hajal–Begraense : ligne construite P : 11 922 t/an; E5 Fisherman’s Wharf–Northharbor : 88 962 t/an; E6 Goldraft–débarcadère de Bluhaven puis 50 mi terrestres : 35 255 t/an; E7 Mirare–Cragplateaus/Ruricans–Pakaitos : ligne alimentaire construite P : 167 239 t/an; E8 Fermes du nord–Pakaitos : 319 t/an; E9 Pakaitos–dépôts des illus autorisés : 127 227 t/an; E12 Capital–Deverell/Mirare–Cragplateaus–Fisherman’s Wharf : ligne construite P : 56 110 t/an. Le mélange E7/E9 consacre 5 % de son énergie à l’huile ; ses masses grain/huile et densités sont conservées dans le JSON. Les quotas de capacité, équipages partagés et techniciens formés sont contrôlés ; les corridors, parcs et formation demeurent P.

### Une réserve de 90 jours ne remplace pas le stock de saison

Le bilan suit des produits physiques, avec leurs masses et densités énergétiques. Une exportation est retirée au chargement et son importation est ajoutée après les pertes et le temps de parcours. Le transit contient les cargaisons, y compris celles chargées l'année précédente ; elles ne sont pas disponibles chez l'expéditeur et chez le destinataire en même temps. Le cycle mensuel hérite de ce pipeline et de ses stocks, au lieu de faire arriver instantanément toutes les importations de l'année.

L'identité de conservation est : **stock final = stock initial + récoltes + imports livrés + création utilisable − consommation − alimentation animale − semences utilisées − exports chargés − pertes − autres usages**. Chaque étape apparaît une fois. Une taxe en grain déplace le contrôle d'un stock ; elle ne retire pas ses calories du continent. Les matières du grain décortiqué, les résidus, le fourrage et les semences restent suivis dans leur propre registre.

La réserve d'urgence centrale vaut **90 jours de besoins**, avec un stock de travail distinct qui couvre le calendrier courant. Immédiatement après une récolte unique, le système doit financer la consommation jusqu'à la récolte suivante, les semences et le plancher d'urgence. Constituer la réserve initiale représente un investissement ; la stationnarité n'ajoute pas ensuite 25 % de consommation chaque année. Les pertes, les distributions et les reprises après crise demandent seulement leur recomplètement réel. Le scénario ne peut annoncer un stock protégé sans nommer sa capacité, ses gardiens, ses magasiniers, son entretien et le droit d'accès des consommateurs.

## L'accès social et la résilience restent vérifiables

Les **nobles reconnus**, les milieux privilégiés, le peuple et les populations précaires sont des catégories distinctes. Le peuple comprend des maîtres et des marchands riches ; un puissant mage, un capitaine ou un prêtre n'est pas automatiquement noble. Dans les régions où la noblesse formelle n'est pas établie, les proportions de nobles et de non nobles restent non renseignées, tandis que les milieux professionnels et économiques peuvent recevoir des parts P. Les enfants, les personnes sans activité et les familles restent dans la population de leur strate.

Les besoins alimentaires sont distribués entre ces groupes selon le corps et l'activité. Les pertes de service P sont différentes, de 8 % pour les milieux nobles ou privilégiés, 3 % pour les milieux ordinaires et 2 % pour les milieux précaires ; ces écarts ne réduisent pas le besoin physiologique des pauvres. Le scénario garantit un droit minimal à la ration nécessaire, puis affecte les budgets de commande, les surplus et le contrôle des stocks. Les règles alimentaires propres à une région, notamment le végétarisme majoritaire de Sindile et les fonctions rituelles des banquets halfelins, modifient les produits et les institutions concernés. ([Sourcebook, p. 152–155](Sources/sb.md), [Player's Guide, p. 20–21](Sources/pg.md)).

**Eau et panier matériel — calculés sous paramètres P.** Les treize budgets hydrologiques saisonniers non négatifs incluent boisson, troupeaux, attelage et irrigation. Bassins, pluie capturable, stockage et efficacité du pompage sont P ; leur énergie et leur prix de bauronite sont débités. Le panier géant atteint 11,864 kg/j, au-dessus du minimum de 8 kg/j des règles (DMG111). L’application Huge à toute la marge géante reste P, enfants et sous-types non recensés. Les traits cirrus et soulborn ne donnent aucune dispense alimentaire démontrée ; les hôtes soulborn inconnus restent une convention de corps P. Une eau comptée ne prouve pas sa potabilité ni la capacité sanitaire de livraison.

**Financement — budget de scénario calculé.** Les treize soldes publics proposés restent positifs après équipages, techniciens, réseau, agents, subvention des rations importées et énergie du pompage. Impôt P15 %, Storm20 %, amortissement P40 ans ; le prélèvement en nature est un transfert de la même assiette, sans seconde disparition de calories. Les stocks et parcs hérités supposent un investissement préalable : ce budget annuel ne certifie ni la levée du capital initial, ni l’accessibilité individuelle de toutes les denrées, ni un marché complet.

**Stress — résultats calculés avec stocks initiaux ordinaires conservés.** La route effectivement utilisée E7 Stravian–Kepesh est fermée M4–M6 pendant 90 jours : départs nuls pendant ces mois, retards et baisse de capacité conservés. Les scénarios récoltes−30 %, magie÷2 et géants×16 ne créent aucune réserve supplémentaire. Un déficit annuel et un manque après réserve sont deux résultats distincts ; le tableau ci-dessous donne les crises observées.

## Le choix d'univers porte sur un réseau réel

Adopter ce scénario revient à donner à Tanares un programme alimentaire concret : des périmètres cultivés bornés, des cohortes magiques avec qualifications et coûts, des agents entretenus, des flottes et rames dimensionnées, des terminaux et des greniers avec des droits de distribution. Les métiers manuels, domestiques, agricoles et logistiques deviennent les acteurs du réseau, et les élites en contrôlent des parties identifiées. Ces engagements sont des choix d'univers proposés et révisables ; ils ne sont plus remplacés par une mention générale de magie ou par une importation sans producteur.

Le scénario central couvre ses besoins énergétiques sous ses investissements P ; les contraintes calculées et les limites restantes sont publiées séparément. Aucune correction de rendement ne sert à fermer un déficit.


## Audit final et vulnérabilités chiffrées

Le parc taii proposé de 180 000 unités n’est pas automatiquement exploitable. SB346 impose à un taii’makian construct au moins huit heures mensuelles d’entretien par un ingénieur qualifié avec outils, soit 9 000 ETP pour ce parc à 240×8 h/an. La cohorte de spécialistes est une qualification proposée, retirée de leurs tâches principales ; elle ne transforme pas tous les chercheurs en ingénieurs canoniques. Avec 4 091,263 ETP admissibles, le parc utilisable est borné à **81 825 unités**, les unités restantes ne produisent rien. Les cultures taii représentent 168 718 ha/an et le réseau livre 459,12 milliards de kcal/an. Aucun petit modèle exempté d’entretien n’a été introduit pour fermer le calcul. Les stocks de noyaux et flux annuels sont recalculés sur le parc soutenu.

Les huiles et noix remplacent une part des parcelles existantes : semences, pertes, rotation, eau et travail sont retranchés. Huile et tourteau se partagent l’énergie et la masse sorties de presse. Les masses des tourteaux emploient une densité spécifique au mélange régional ; leur composition protéique et lipidique demeure un indicateur P générique.

| Région | Protéines g/j/équivalent M (P) | Lipides % énergie physique (P) | Solde public gp/an (P) |
|---|---:|---:|---:|
| Central Empire | 88,32 | 17,22 | 5 333 525 |
| Republic of Freelands | 102,78 | 15,54 | 4 231 493 |
| Imperial Ben’net | 145,18 | 31,72 | 1 002 743 |
| Kingdom of Kolbjörn | 106,80 | 16,59 | 1 884 042 |
| Magocracy of Mage Tower | 89,95 | 15,59 | 2 881 509 |
| Seashores | 167,29 | 25,23 | 1 563 919 |
| Sindile Forest | 62,87 | 15,26 | 1 353 397 |
| Stravian Domains | 84,46 | 16,53 | 1 342 887 |
| Storm Islands | 83,91 | 13,32 | 2 096 938 |
| Taii’Maku City States | 70,54 | 13,61 | 1 217 175 |
| Theocracy of Kepesh | 113,99 | 21,13 | 864 919 |
| Tsvetan | 102,22 | 16,62 | 1 389 262 |
| Yama | 80,29 | 13,87 | 1 513 843 |

Storm, Taii et Yama restent pauvres en lipides, autour de 13–14 % de l’énergie matérielle. Les protéines/lipides sont des indicateurs de composition P ; ni micronutriments, acides gras essentiels, vitamines, sel, qualité sanitaire, ni besoins propres à chaque âge et espèce ne sont certifiés. La nourriture magique n’a pas reçu une composition nutritionnelle humaine inventée. Le droit proposé à 100 % de rations constitue une politique de scénario, pas une garantie canonique d’accès.

| Stress | Régions avec manque après stock initial | Déficit après stock initial (milliards kcal) |
|---|---|---:|
| bad_harvest | Seashores ; Taii’Maku City States | 319,40 |
| magic_halved | Aucune dans cette variante chiffrée | 0,00 |
| route_closed_90_days | Aucune dans cette variante chiffrée | 0,00 |
| giants_energy_16 | Aucune dans cette variante chiffrée | 0,00 |

Les résultats positifs d’un stress isolé ne certifient pas les chocs combinés, une crise prolongée ou la reconstitution des réserves. Réserves et stocks de roulement sont les mêmes que dans l’ordinaire ; le déficit après stock est le minimum mensuel négatif réellement calculé.

Reproduction unique : `Tools/Worldbuilding/Tanares/Metiers/build_v3.ps1 -Python <exécutable Python> -Node <exécutable Node>`. Ce lanceur fixe TEMP/TMP sur le sous-dossier Temp et la graine de parcours Python, utilise UTF-8 et `-B`, construit la référence V2, révise et contrôle V3 puis teste les panneaux/CSV Node VM. Le solver séparé reprend `metiers-tanares-v2-reference.json`, jamais un modèle V3 déjà réaffecté. Les 66 contrôles chiffrés figurent dans le registre. **Rendu visuel non certifié.** Les fichiers de contenu et scripts sont transportables vers la passation UE5, sans dépendance au moteur ou à Source/Core.
