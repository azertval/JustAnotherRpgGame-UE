# Métiers et populations de Tanares

**Extension alimentaire V3 calculée : 13/13 régions couvrent leurs besoins énergétiques annuels dans ce scénario.** Les plafonds de terres, eau, métiers qualifiés, magie et transport sont proposés. Les 66 contrôles de conservation passent ; ils ne certifient pas la nutrition complète, les techniques proposées ou un marché réellement simulé. Le stock taii utilisable est réduit par les huit heures mensuelles d’entretien des constructs (SB346), sans augmenter le rendement pour compenser. Les bilans saisonniers, coûts, lipides faibles de Storm/Taii/Yama et crises chiffrées figurent dans [Alimentation et échanges de Tanares](alimentation.md). Les revenus, infrastructures, droits aux rations et stocks initiaux demeurent P.

**La liste initiale est enrichie et organisée en 66 métiers de base, 234 spécialisations et 33 feuilles généralistes. Cette version 3 révise les populations professionnelles selon un scénario médiéval fantastique et leurs milieux sociaux.** Elle distingue la noblesse reconnue du peuple lorsque les livres établissent ce statut, et conserve les élites professionnelles, économiques ou institutionnelles dans un axe différent. Les enfants nobles, personnes sans métier, chômeurs, étudiants et retraités demeurent dans les habitants ; seuls les producteurs réels reçoivent une profession principale. Les campagnes ordinaires consacrent ici **62 à 80 % de leurs occupés civils à la production vivrière**, avec variations locales et exceptions surnaturelles explicitement signalées. Les sources fixent les institutions, usages, populations régionales et deux tailles municipales ; **tous les pourcentages professionnels et sociaux, taux d’activité et autres tailles locales sont proposés**, jamais statistiques canoniques. Le statut économique est **médiéval fantastique proposé, paramètres alimentaires proposés et bilan annuel calculé** ; cette version remplace les répartitions de la première.

Les **118 profils** couvrent les 13 régions chiffrées, leurs villes, quartiers et communautés, ainsi que des références relatives pour Undertanares et Darkall. Mystical conserve ses habitants morts-vivants et les expéditions dans un registre distinct, sans population civile vivante fabriquée. [L’explorateur local](explorateur.html) présente chaque métier, ses deux dénominateurs, ses origines sociales et une justification développable, y compris les zéros ; l’export CSV conserve ces explications. [Le modèle intégral](Donnees/metiers-tanares-modele.json) contient les strates, matrices, règles héritées et coefficients. Les calculs sont vérifiés dans [le fichier de contrôle](Donnees/metiers-tanares-verification.json).

## Noblesse reconnue et milieux privilégiés mesurent deux choses différentes

Un noble possède un **titre ou statut reconnu localement**, transmis ou acquis par anoblissement ; ni richesse, caste, grade militaire, clan, métier, classe D&D ou fonction dirigeante ne suffit. Les familles et enfants nobles restent nobles hors activité, tandis que les employés de leur maisonnée restent non nobles sauf titre propre. Un noble modeste ou déchu demeure possible, comme un bourgeois, maître de guilde, mage ou prêtre riche non noble. La règle familiale de scénario reconnaît les enfants d’une maison noble ; les conjoints conservent leur statut propre sauf reconnaissance distincte. Cette convention de transmission est proposée, les livres ne donnent pas un droit familial complet.

L’Empire possède des nobles gouverneurs et seigneurs ; ses officiers proviennent aussi de classes moyennes. Les Freelands conservent des nobles fonciers sans leur ancienne autorité politique. Les maisons de Jarls de Kolbjörn sont reconnues, mais tous les membres d’un clan ne sont pas nobles. Yama distingue lignages nobles, castes et fonctions professionnelles. Le sud impérial de Ben’net est séparé des communautés cirrus et ordres autonomes. [SB p. 90](Sources/sb.md), [SB p. 91](Sources/sb.md), [SB p. 104](Sources/sb.md), [SB p. 123](Sources/sb.md), [SB p. 128](Sources/sb.md), [SB p. 129](Sources/sb.md), [SB p. 198](Sources/sb.md), [SB p. 200](Sources/sb.md).

**Mage Tower, Seashores, Sindile, Stravian, Storm, les Illus, Kepesh, Tsvetan, Undertanares et Darkall n’obtiennent pas une noblesse inventée pour remplir un tableau.** Leurs dignités, conseils, royautés, rangs ou castes sont décrits ; la catégorie complète de noblesse reconnue reste non établie là où le corpus ne permet pas de la définir. Les valeurs nobles/peuple sont alors **non renseignées**, jamais converties en 0 % nobles et 100 % peuple. Pour les régions mêlant institutions définies et indéterminées, le modèle conserve les parts connues et la part de statuts non renseignés ; les filtres conditionnels nobles/peuple sont indisponibles pour cet agrégat complet. Les milieux privilégiés et ordinaires demeurent consultables séparément. [SB p. 138](Sources/sb.md), [SB p. 146](Sources/sb.md), [SB p. 154](Sources/sb.md), [SB p. 160](Sources/sb.md), [SB p. 168](Sources/sb.md), [SB p. 174](Sources/sb.md), [SB p. 182](Sources/sb.md), [SB p. 190](Sources/sb.md), [SB p. 206](Sources/sb.md), [SB p. 208](Sources/sb.md).

Lorsque la noblesse est définie, cinq strates sont proposées : nobles de milieu privilégié, autres nobles, peuple privilégié, peuple ordinaire et peuple précaire. Ailleurs, trois strates décrivent seulement milieu privilégié, ordinaire et précaire. Ces strates incluent tous les habitants ; le terme « milieu privilégié » comprend les dépendants d’une famille disposant de cet accès, sans attribuer un métier aux enfants. Les nobles actifs sont davantage orientés vers gestion réelle, administration, diplomatie, commandement ou savoir ; le peuple privilégié vers ateliers, négoce et expertise. Les milieux précaires rencontrent davantage de barrières de formation et de capital. **La répartition n’est pas indépendante du statut social**, et aucun métier ne confère un titre : les parts sociales et taux d’activité sont fixés avant de distribuer les emplois.

La noblesse représente dans ce scénario **1,55 % des habitants de l’Empire**, 0,72 % des Freelands et 1,89 % de Yama. Ce sont des proportions proposées, pas une norme médiévale attestée. Downtown est ramené à **10 000 habitants**, Palacedomain à **6 000** ; les habitants libérés rejoignent des quartiers populaires, le total de la capitale reste **680 000**. Dans Downtown, les non nobles résidents sont exclusivement membres du clergé admis sur terrain de temple ; leurs emplois principaux peuvent être soins, copie ou instruction, avec affiliation explicite. Les artisans et domestiques ordinaires travaillant dans le quartier sont domiciliés ailleurs. [SB p. 99](Sources/sb.md).

## Des budgets civils replacent les campagnes et ateliers au cœur de l’économie

Le budget vivrier compte **les producteurs caloriques primaires** : cultures alimentaires, vergers nourriciers, animaux alimentaires, pêche, chasse et plantes comestibles. Il exclut les montures, vers à soie, herbes d’infusion, épices, bois/mines, mouture, conservation et cuisine. Les tâches familiales de filage, jardin, cuisson, réparation et milice temporaire restent secondaires ; elles ne créent pas plusieurs personnes ou professions. Un producteur peut changer de tâches avec les saisons sans multiplier les emplois annuels. Les métiers spécialisés coûteux et tertiaires sont raréfiés dans les villages puis concentrés dans leurs pôles de formation, de matière et de clientèle.

| Profil rural ordinaire | Primaire vivrier / occupés civils | Matières non alimentaires | Artisanat/transformation | Commerce/logistique | Services et institutions | Défense civile, experts et arts |
|---|---:|---:|---:|---:|---:|---:|
| Central Empire | 75 % | 4,0 % | 11,0 % | 5,0 % | 4,0 % | 1,0 % |
| Republic of Freelands | 62 % | 12,0 % | 10,0 % | 5,0 % | 5,0 % | 6,0 % |
| Imperial Ben’net | 80 % | 3,0 % | 11,0 % | 3,0 % | 2,5 % | 0,5 % |
| Kingdom of Kolbjörn | 68 % | 8,0 % | 12,0 % | 5,0 % | 4,0 % | 3,0 % |
| Magocracy of Mage Tower | 65 % | 4,0 % | 17,0 % | 7,0 % | 5,0 % | 2,0 % |
| Seashores | 72 % | 3,0 % | 12,0 % | 6,0 % | 4,0 % | 3,0 % |
| Sindile Forest | 75 % | 3,0 % | 12,0 % | 3,0 % | 4,0 % | 3,0 % |
| Stravian Domains | 75 % | 2,0 % | 14,0 % | 5,0 % | 2,0 % | 2,0 % |
| Theocracy of Kepesh | 65 % | 6,0 % | 14,0 % | 7,0 % | 5,0 % | 3,0 % |
| Tsvetan | 68 % | 4,0 % | 14,0 % | 5,0 % | 5,0 % | 4,0 % |
| Yama | 66 % | 10,0 % | 13,0 % | 5,0 % | 4,0 % | 2,0 % |

Ces enveloppes sont les décisions numériques du scénario. Les livres justifient les **priorités**, pas leurs valeurs exactes : céréales de l’Empire, ressources et aventure des Freelands, élevage/tubercules de Ben’net, pêche/chasse/navires de Kolbjörn, forêts végétariennes de Sindile, cultures féeriques stravianes, irrigation/imports de Kepesh et riz/soie de Yama. Les métiers de thé, soie et épices ont leur poids en matières ou spécialités, sans gonfler le nombre de producteurs alimentaires. Les profils résiduels incluent les petites implantations anonymes ; les villes nommées sont moins grandes que dans la première proposition, afin de ne pas créer gratuitement plusieurs métropoles à côté des deux énormes capitales publiées. [SB p. 90](Sources/sb.md), [SB p. 104](Sources/sb.md), [SB p. 120](Sources/sb.md), [SB p. 128](Sources/sb.md), [SB p. 152](Sources/sb.md), [SB p. 160](Sources/sb.md), [SB p. 182](Sources/sb.md), [SB p. 198](Sources/sb.md).

Les exceptions ne reçoivent aucun rendement surnaturel inventé. À G’bagede, seuls enseignants et chercheurs en golems travaillent parmi les vivants ; contemplation et dépendants restent hors activité, capacités des golems séparées. Storm et Winterhold délèguent les tâches manuelles à des morts-vivants ; les Illus et plusieurs réseaux arcaniques emploient constructions ou élémentaires. Mirare dispose d’aides féeriques locales ; Kepesh dépend aussi d’eau magique et d’importations. Ces sources indiquent ce qui doit être quantifié ensuite : elles ne prouvent pas que n’importe quel petit nombre de travailleurs nourrit toute la population. [SB p. 108](Sources/sb.md), [SB p. 161](Sources/sb.md), [SB p. 168](Sources/sb.md), [SB p. 174](Sources/sb.md), [SB p. 178](Sources/sb.md), [SB p. 182](Sources/sb.md), [SB p. 185](Sources/sb.md).

Les **34 000 soldats présents dans Capital City et 4 100 dans Fisherman’s Wharf** sont inclus dans les résidents par convention proposée. Ils sont exclus des budgets des occupés civils, puis réintégrés une seule fois. Les résidences ont été redistribuées dans les quartiers admissibles : aucun soldat non noble ordinaire n’est domicilié dans Downtown, et la petite enclave Palacedomain ne porte plus 5 500 soldats. Les sources attestent la présence, pas cette convention de résidence. [SB p. 98](Sources/sb.md), [SB p. 111](Sources/sb.md).

Dawn of Light est un ensemble ville-campus avec enseignants minoritaires, supports de livres/labos et services de logement ; aucun instructeur d’archerie ou d’arts martiaux sans établissement attesté. Eberek privilégie personnel soignant et aides plutôt que barbiers ou gardiens d’enfants. Les roses magiques restent à Mirror Lake, la psychosurgery à Phantom Fortress, les initiés de réacteurs dans des sites autorisés et sous un plafond de **0,01 % des occupés**. Les inquisiteurs bauroniens sont exclus des ordres cirrus et cultes incompatibles ; aucun rite Ba-Akhu n’est donné aux tribus Brightlight non converties. Ces zéros sont des contraintes du scénario courant, avec preuve et raison, pas interdictions universelles. [SB p. 29](Sources/sb.md), [SB p. 94](Sources/sb.md), [SB p. 141](Sources/sb.md), [SB p. 157](Sources/sb.md), [SB p. 174](Sources/sb.md), [SB p. 186](Sources/sb.md), [SB p. 187](Sources/sb.md).

## Chaque région conserve ses cultures et des pourcentages socialement différenciés

| Région | Activités communes attestées | Activités caractéristiques | Expertise et portée | Références imprimées |
|---|---|---|---|---|
| Central Empire | Agriculture, construction, commerce, artisans, fonctionnaires | Contrôle magique impérial, psychosurgery Ironhand, finance Hajal, pèlerinage Skybell | Artisansquare : artisanat de haut niveau ; Hajal : centre financier ; pas meilleur forgeron universel | [SB p. 90](Sources/sb.md), [SB p. 93](Sources/sb.md), [SB p. 98](Sources/sb.md), [SB p. 212](Sources/sb.md) |
| Republic of Freelands | Pêche, bois, extraction, commerce, mercenariat et aventure | Guildes de missions, chasse de monstres, reliques, illusion solide Aurindunnum, nécromancie Winterhold | Aventure et chasse reconnues ; prestige individuel Avelum/Sara et musée, pas tous les mages | [SB p. 104](Sources/sb.md), [SB p. 107](Sources/sb.md), [SB p. 108](Sources/sb.md), [SB p. 113](Sources/sb.md) |
| Imperial Ben’net | Élevage moutons/yaks, tubercules, laine, cuir, fromage, boissons | Highlandtuber, plantes montagnardes, montures aériennes et communautés cirrus | Meilleurs et plus forts alcools distillés de Tanares, produits traditionnels ; textile connu | [SB p. 120](Sources/sb.md), [SB p. 121](Sources/sb.md), [SB p. 124](Sources/sb.md) |
| Kingdom of Kolbjörn | Pêche, chasse, navigation, navires, cuir, forge, mercenaires | Drakkars avec rites, shamans, Falun armes enchantées et poésie, savoirs des géants | Navires/navigateurs renommés ; Northharbor endurance guerrière ; rang continental forge non donné | [SB p. 128](Sources/sb.md), [SB p. 130](Sources/sb.md), [SB p. 133](Sources/sb.md), [SB p. 134](Sources/sb.md) |
| Magocracy of Mage Tower | Pêche douce, papier, enseignement, recherche, potions, objets et parchemins | Certification, enchères, recyclage arcanique, mémoire, aethermancy, biomancy, police magique | Meilleures écoles arcaniques de Tanares ; Arcane University lieu privilégié, pas tout objet certifié | [SB p. 15](Sources/sb.md), [SB p. 138](Sources/sb.md), [SB p. 139](Sources/sb.md), [SB p. 140](Sources/sb.md), [SB p. 141](Sources/sb.md) |
| Seashores | Pêche, navigation, commerce, navires, services portuaires, marchés clandestins | Perles et reliques sous-marines, arts Mustardseed, courtage maritime, cuisine gnome | Meilleurs constructeurs navals de Tanares ; institutions musicales réputées ; arts gnomes réputés comme peuple | [SB p. 148](Sources/sb.md), [SB p. 149](Sources/sb.md), [PG p. 28](Sources/pg.md), [CC p. 52](Sources/cc.md) |
| Sindile Forest | Culture végétale, herbes, bois, arcs, guides, musiciens, gardiens | Estelindea, Mother Trees, roses Mirror Lake, canopée, arbres funéraires | Remèdes et matériau exceptionnels ; puissance du site Mirror Lake ; aucune suprématie générale des artisans | [SB p. 152](Sources/sb.md), [SB p. 153](Sources/sb.md), [SB p. 154](Sources/sb.md), [SB p. 155](Sources/sb.md), [SB p. 157](Sources/sb.md) |
| Stravian Domains | Mines, forge, pierre, bijoux, commerce, cultures du Sud | Stone Disks, runes de tunnels, Stone Spirits, agriculture féerique, vergers sacrés | Nains réputés métal/pierre/mines ; Stonelair renommée ; Mirare grenier ; forge dorsienne installation ancienne | [SB p. 160](Sources/sb.md), [SB p. 161](Sources/sb.md), [SB p. 162](Sources/sb.md), [SB p. 163](Sources/sb.md), [PG p. 12](Sources/pg.md), [PG p. 13](Sources/pg.md) |
| Storm Islands | Militaires, prêtres Bás, pêche, cultures, mines, navigation | Nécromancie glaciale, pylônes, laboratoire et navires morts-vivants | Flotte morte-vivante remarquable dans l’Océan ; astronomie Cantala historique, pas expertise kemet héritée | [SB p. 168](Sources/sb.md), [SB p. 170](Sources/sb.md), [SB p. 171](Sources/sb.md) |
| Taii’Maku City States | Ingénieurs, enseignants, chercheurs, inventeurs, mathématiciens, artistes | Golems, réacteurs bauronite, lentilles, horloges, outils de précision et communications | Excellence technique/architecturale ; seuls exportateurs de plusieurs dispositifs précis ; secrets limités | [SB p. 174](Sources/sb.md), [SB p. 175](Sources/sb.md), [SB p. 178](Sources/sb.md), [SB p. 180](Sources/sb.md) |
| Theocracy of Kepesh | Cultures irriguées, élevage, mines, bijoux, temples, pêche côtière | Momification, rites Ba-Akhu, communication ethérique, castes et clergé | Montures reconnues pour endurance ; bijoux raffinés ; aucune première place mondiale affirmée | [SB p. 182](Sources/sb.md), [SB p. 184](Sources/sb.md), [SB p. 186](Sources/sb.md) |
| Tsvetan | Chasse, élevage, cultures arides, extraction, cuir, guerre, shamans | Loups géants, poisons animaux, totems, peintures spirituelles et champs funéraires | Hot Bloods parmi les meilleurs guerriers orques ; Stone Fangs chasse/poisons ; portée clanique | [SB p. 190](Sources/sb.md), [SB p. 191](Sources/sb.md), [SB p. 193](Sources/sb.md) |
| Yama | Riz, soie, acier, herbes/thé, administration, commerce fluvial | Thé rituel, sugenjas, Édits, Ki, entraînement martial, institutions diplomatiques | Acier haute qualité ; maîtrise rituelle et monastique ; Rokaru individu, pas tous les forgerons | [SB p. 198](Sources/sb.md), [SB p. 200](Sources/sb.md), [SB p. 201](Sources/sb.md), [SB p. 204](Sources/sb.md), [SB p. 220](Sources/sb.md) |
| Undertanares | Mines, forge, défense ; chasse/culture/services communautaires gloomfolk | Ruches et mémoires, venins, Stone Spirits, duergars et Dorsian Forge | Installation légendaire avec maîtrise actuelle partielle ; aucune domination professionnelle générale | [SB p. 206](Sources/sb.md), [SB p. 207](Sources/sb.md), [PG p. 40](Sources/pg.md) |
| Darkall | Guerre, nécromancie, industrie militaire au Nord ; ressources et subsistance au Centre | Légions et serviteurs morts-vivants, sièges et conflit démoniaque | Aucun métier civil déclaré meilleur de Tanares | [SB p. 208](Sources/sb.md), [SB p. 209](Sources/sb.md), [SB p. 210](Sources/sb.md) |
| Mystical / Wasteland | Expéditions, mercenaires et chasseurs de reliques visiteurs ; populations mortes-vivantes | Arcana, hordes, golems, ruines, limitation du soin des vivants | Savoirs anciens : expertise historique, capacité productive contemporaine inconnue | [SB p. 210](Sources/sb.md), [SB p. 211](Sources/sb.md) |

Le tableau suivant porte sur **tous habitants** pour noblesse, milieu privilégié, activité et producteurs vivriers. La colonne « vivrier civil » porte sur les **occupés civils**, excluant les soldats permanents. Les régimes non chiffrés n’obtiennent pas de population absolue inventée. Les milieux privilégiés chevauchent les nobles : leurs pourcentages ne sont pas à additionner.

| Région | Habitants source | Nobles parmi habitants | Milieu privilégié / habitants | Actifs / habitants | Vivrier / occupés civils | Producteurs vivriers / habitants | Habitants par producteur vivrier |
|---|---:|---|---:|---:|---:|---:|---:|
| Central Empire | 2 300 000 | 1,5 % | 3,5 % | 64,5 % | 58,8 % | 35,5 % | 2,8 |
| Republic of Freelands | 1 700 000 | 0,7 % | 3,7 % | 64,1 % | 44,6 % | 27,2 % | 3,7 |
| Imperial Ben’net | 445 000 | n.r. ; 22,5 % de statuts indéterminés | 1,6 % | 67,2 % | 72,8 % | 46,9 % | 2,1 |
| Kingdom of Kolbjörn | 720 000 | n.r. ; 11,1 % de statuts indéterminés | 1,8 % | 66,7 % | 62,8 % | 40,2 % | 2,5 |
| Magocracy of Mage Tower | 867 000 | non établi | 1,8 % | 66,2 % | 60,1 % | 38,3 % | 2,6 |
| Seashores | 617 000 | non établi | 2,1 % | 66,2 % | 62,3 % | 39,3 % | 2,5 |
| Sindile Forest | 432 000 | non établi | 2,0 % | 67,2 % | 69,2 % | 43,9 % | 2,3 |
| Stravian Domains | 960 000 | non établi | 2,0 % | 66,2 % | 59,7 % | 37,9 % | 2,6 |
| Storm Islands | 386 000 | non établi | 3,0 % | 72,0 % | 25,2 % | 8,6 % | 11,6 |
| Taii’Maku City States | 698 000 | non établi | 2,0 % | 43,6 % | 14,1 % | 5,6 % | 17,9 |
| Theocracy of Kepesh | 695 000 | non établi | 3,7 % | 66,9 % | 63,6 % | 41,0 % | 2,4 |
| Tsvetan | 468 000 | non établi | 3,0 % | 66,9 % | 64,4 % | 40,2 % | 2,5 |
| Yama | 793 000 | 1,9 % | 1,8 % | 66,6 % | 62,4 % | 40,0 % | 2,5 |
| Undertanares | n.r. | non établi | 3,0 % | 64,1 % | 37,9 % | 23,1 % | 4,3 |
| Darkall | n.r. | non établi | 6,0 % | 66,0 % | 41,4 % | 21,5 % | 4,7 |
| Mystical / Wasteland | inconnu | n.r. | n.r. | n/a | n/a | n/a | n/a |

**Habitants par producteur est une charge démographique, pas un rendement.** Elle ignore encore consommation des géants et autres espèces, temps de production secondaire, visiteurs, pertes, surplus, routes, stockage, imports/exports et capacité des travailleurs surnaturels. Une valeur basse ne prouve pas autosuffisance ; une valeur haute signale un besoin de flux ou capacités à résoudre. Les populations régionales et marges d’espèces publiées restent conservées, pour un total connu d’environ **11 081 000 habitants**. Les matrices emploi–espèce et emploi–milieu social sont deux projections marginales ; elles ne prouvent pas une répartition détaillée espèce–classe sociale.

### Central Empire

Contexte : [SB p. 128](Sources/sb.md), [SB p. 212](Sources/sb.md), [SB p. 213](Sources/sb.md), [SB p. 90](Sources/sb.md), [SB p. 91](Sources/sb.md), [SB p. 92](Sources/sb.md), [SB p. 93](Sources/sb.md), [SB p. 94](Sources/sb.md). Les pages soutiennent mécanismes, cultures et institutions ; les parts ci-dessous sont proposées.

| Lieu | Habitants | Nobles / habitants | Privilégiés / habitants | Actifs / habitants | Vivrier / habitants | Sans emploi / actifs |
|---|---:|---|---:|---:|---:|---:|
| Sloghood | 110 000 | 0,3 % | 4,0 % | 60,4 % | 0,9 % | 5,4 % |
| Uptown | 55 000 | 10,0 % | 15,0 % | 57,6 % | 2,6 % | 5,2 % |
| Artisansquare | 60 000 | 0,8 % | 4,0 % | 60,3 % | 1,1 % | 5,4 % |
| Scholarnest | 40 000 | 1,0 % | 4,0 % | 40,0 % | 1,1 % | 3,0 % |
| Dweomer | 15 000 | 8,0 % | 12,0 % | 58,3 % | 0,5 % | 5,3 % |
| Martpart | 67 000 | 0,3 % | 4,0 % | 60,4 % | 2,7 % | 5,4 % |
| Arenarea | 45 000 | 12,0 % | 18,0 % | 57,0 % | 1,0 % | 5,1 % |
| Oldtown | 45 000 | 0,5 % | 4,0 % | 45,0 % | 2,0 % | 5,0 % |
| Neckoffoods | 100 000 | 0,2 % | 1,5 % | 67,5 % | 46,7 % | 3,3 % |
| Bloomburgs | 127 000 | 0,1 % | 4,0 % | 60,0 % | 1,0 % | 8,1 % |
| Downtown | 10 000 | 90,0 % | 82,0 % | 32,5 % | 0,0 % | 1,0 % |
| Palacedomain | 6 000 | 85,0 % | 83,0 % | 33,8 % | 0,0 % | 1,0 % |
| Skybell City | 25 000 | 1,0 % | 4,0 % | 60,3 % | 2,8 % | 5,4 % |
| Hajal City | 35 000 | 3,0 % | 12,0 % | 59,2 % | 1,7 % | 5,2 % |
| Odraz Monastery | 1 200 | 0,4 % | 4,0 % | 60,4 % | 11,3 % | 5,4 % |
| Phantom Fortress | 2 200 | 0,4 % | 4,0 % | 73,9 % | 1,0 % | 2,0 % |
| Great Forest of Bak (communautés) | 18 000 | 0,4 % | 1,5 % | 67,5 % | 48,8 % | 3,3 % |
| Autres villes, villages et campagnes (résiduel) | 1 538 600 | 0,4 % | 1,5 % | 67,5 % | 48,8 % | 3,3 % |
| Capital City | 680 000 | 4,1 % | 7,5 % | 58,0 % | 8,0 % | 5,4 % |

### Republic of Freelands

Contexte : [SB p. 104](Sources/sb.md), [SB p. 105](Sources/sb.md), [SB p. 106](Sources/sb.md), [SB p. 107](Sources/sb.md), [SB p. 108](Sources/sb.md), [SB p. 109](Sources/sb.md), [SB p. 110](Sources/sb.md), [SB p. 111](Sources/sb.md). Les pages soutiennent mécanismes, cultures et institutions ; les parts ci-dessous sont proposées.

| Lieu | Habitants | Nobles / habitants | Privilégiés / habitants | Actifs / habitants | Vivrier / habitants | Sans emploi / actifs |
|---|---:|---|---:|---:|---:|---:|
| Seabreeze District | 90 000 | 0,5 % | 4,0 % | 60,4 % | 9,0 % | 5,4 % |
| The Six Quarters | 45 000 | 8,0 % | 25,0 % | 57,1 % | 0,0 % | 4,9 % |
| Wallside District | 100 000 | 1,0 % | 4,0 % | 60,3 % | 11,3 % | 5,4 % |
| Uptown | 95 000 | 0,5 % | 15,0 % | 59,4 % | 2,8 % | 5,1 % |
| Hope Square | 150 000 | 0,1 % | 4,0 % | 60,0 % | 21,0 % | 7,0 % |
| The Cerulean Plaza | 90 000 | 0,5 % | 4,0 % | 60,4 % | 4,5 % | 5,4 % |
| Aurindunnum | 40 000 | 4,0 % | 4,0 % | 59,7 % | 2,8 % | 5,4 % |
| Aeyefall | 20 000 | 0,6 % | 4,0 % | 60,4 % | 8,4 % | 5,4 % |
| Heroes Rise | 25 000 | 0,5 % | 4,0 % | 60,4 % | 4,5 % | 5,4 % |
| Winterhold | 30 000 | 4,0 % | 4,0 % | 47,5 % | 2,7 % | 3,0 % |
| Goldraft | 30 000 | 0,6 % | 4,0 % | 60,3 % | 6,7 % | 5,7 % |
| Autres villes, villages et campagnes (résiduel) | 985 000 | 0,3 % | 1,5 % | 67,5 % | 40,4 % | 3,3 % |
| Fisherman’s Wharf | 570 000 | 1,1 % | 7,5 % | 59,9 % | 10,1 % | 5,8 % |

### Imperial Ben’net

Contexte : [SB p. 120](Sources/sb.md), [SB p. 121](Sources/sb.md), [SB p. 122](Sources/sb.md), [SB p. 123](Sources/sb.md), [SB p. 124](Sources/sb.md), [SB p. 125](Sources/sb.md), [SB p. 15](Sources/sb.md), [SB p. 82](Sources/sb.md). Les pages soutiennent mécanismes, cultures et institutions ; les parts ci-dessous sont proposées.

| Lieu | Habitants | Nobles / habitants | Privilégiés / habitants | Actifs / habitants | Vivrier / habitants | Sans emploi / actifs |
|---|---:|---|---:|---:|---:|---:|
| Begraense | 18 000 | 2,0 % | 4,0 % | 60,1 % | 5,6 % | 5,4 % |
| Crystal Mountains communities | 95 000 | non établi | 1,5 % | 67,6 % | 39,1 % | 3,3 % |
| Ice Fortress | 1 800 | non établi | 4,0 % | 74,0 % | 1,5 % | 2,0 % |
| Plateaus of the Eternal Ice | 2 200 | non établi | 4,0 % | 60,5 % | 2,6 % | 5,4 % |
| Temple of the Four Winds | 1 000 | non établi | 4,0 % | 60,5 % | 8,5 % | 5,4 % |
| Autres villes, villages et campagnes (résiduel) | 327 000 | 0,2 % | 1,5 % | 67,5 % | 52,1 % | 3,3 % |

### Kingdom of Kolbjörn

Contexte : [SB p. 128](Sources/sb.md), [SB p. 129](Sources/sb.md), [SB p. 130](Sources/sb.md), [SB p. 131](Sources/sb.md), [SB p. 132](Sources/sb.md), [SB p. 133](Sources/sb.md), [SB p. 134](Sources/sb.md), [SB p. 135](Sources/sb.md). Les pages soutiennent mécanismes, cultures et institutions ; les parts ci-dessous sont proposées.

| Lieu | Habitants | Nobles / habitants | Privilégiés / habitants | Actifs / habitants | Vivrier / habitants | Sans emploi / actifs |
|---|---:|---|---:|---:|---:|---:|
| Kolbjörn Capital | 30 000 | 1,5 % | 4,0 % | 60,2 % | 7,9 % | 5,4 % |
| Irongauntlet | 12 000 | 0,3 % | 4,0 % | 60,3 % | 5,4 % | 9,3 % |
| Northharbor | 25 000 | 0,8 % | 4,0 % | 60,3 % | 12,4 % | 5,4 % |
| Falun | 4 000 | non établi | 4,0 % | 60,5 % | 2,4 % | 5,4 % |
| Great Valley (communautés géantes) | 70 000 | non établi | 1,5 % | 67,6 % | 41,7 % | 3,3 % |
| Autres Floating Islands | 6 000 | non établi | 4,0 % | 60,5 % | 5,6 % | 5,4 % |
| Autres villes, villages et campagnes (résiduel) | 573 000 | 0,5 % | 1,5 % | 67,5 % | 44,3 % | 3,3 % |

### Magocracy of Mage Tower

Contexte : [SB p. 138](Sources/sb.md), [SB p. 138–139](Sources/sb.md), [SB p. 139](Sources/sb.md), [SB p. 139–140](Sources/sb.md), [SB p. 140](Sources/sb.md), [SB p. 141](Sources/sb.md), [SB p. 141–142](Sources/sb.md), [SB p. 142](Sources/sb.md). Les pages soutiennent mécanismes, cultures et institutions ; les parts ci-dessous sont proposées.

| Lieu | Habitants | Nobles / habitants | Privilégiés / habitants | Actifs / habitants | Vivrier / habitants | Sans emploi / actifs |
|---|---:|---|---:|---:|---:|---:|
| Mesoriver | 60 000 | non établi | 4,0 % | 60,5 % | 3,9 % | 5,4 % |
| Dawn of Light et campus | 25 000 | non établi | 4,0 % | 40,0 % | 3,1 % | 3,0 % |
| Crystal Tower et environs | 2 000 | non établi | 15,0 % | 59,5 % | 0,0 % | 5,1 % |
| Summer Island (résidents) | 3 000 | non établi | 4,0 % | 60,5 % | 11,3 % | 5,4 % |
| Asylum Eberek | 1 500 | non établi | 4,0 % | 25,7 % | 0,3 % | 1,0 % |
| Autres villes, villages et campagnes (résiduel) | 775 500 | non établi | 1,5 % | 67,6 % | 42,4 % | 3,3 % |

### Seashores

Contexte : [CC p. 52](Sources/cc.md), [PG p. 28–29](Sources/pg.md), [SB p. 146](Sources/sb.md), [SB p. 146–147](Sources/sb.md), [SB p. 146–149](Sources/sb.md), [SB p. 147](Sources/sb.md), [SB p. 148](Sources/sb.md), [SB p. 148–149](Sources/sb.md). Les pages soutiennent mécanismes, cultures et institutions ; les parts ci-dessous sont proposées.

| Lieu | Habitants | Nobles / habitants | Privilégiés / habitants | Actifs / habitants | Vivrier / habitants | Sans emploi / actifs |
|---|---:|---|---:|---:|---:|---:|
| Bluhaven | 40 000 | non établi | 4,0 % | 60,2 % | 9,4 % | 6,5 % |
| Mustardseed | 40 000 | non établi | 6,0 % | 60,3 % | 5,1 % | 5,4 % |
| Pearl Town | 26 000 | non établi | 4,0 % | 60,5 % | 18,0 % | 5,4 % |
| Fishtail City | 15 000 | non établi | 4,0 % | 60,0 % | 10,9 % | 7,8 % |
| Turtledragon Island | 4 000 | non établi | 4,0 % | 74,0 % | 2,0 % | 2,0 % |
| Uncle Joe’s Tavern et île | 1 500 | non établi | 4,0 % | 60,5 % | 1,1 % | 5,4 % |
| Autres villes, villages et campagnes (résiduel) | 490 500 | non établi | 1,5 % | 67,6 % | 46,9 % | 3,3 % |

### Sindile Forest

Contexte : [SB p. 152](Sources/sb.md), [SB p. 152–153](Sources/sb.md), [SB p. 152–155](Sources/sb.md), [SB p. 153](Sources/sb.md), [SB p. 153–155](Sources/sb.md), [SB p. 154](Sources/sb.md), [SB p. 155](Sources/sb.md), [SB p. 157](Sources/sb.md). Les pages soutiennent mécanismes, cultures et institutions ; les parts ci-dessous sont proposées.

| Lieu | Habitants | Nobles / habitants | Privilégiés / habitants | Actifs / habitants | Vivrier / habitants | Sans emploi / actifs |
|---|---:|---|---:|---:|---:|---:|
| Sweetsprings | 35 000 | non établi | 6,0 % | 60,3 % | 11,2 % | 5,4 % |
| Hunter’s Nest | 16 000 | non établi | 4,0 % | 74,0 % | 1,5 % | 2,0 % |
| Villages de Sindile Road | 35 000 | non établi | 1,5 % | 67,6 % | 48,9 % | 3,3 % |
| Mirror Lake / Mountain Gate (résidents) | 1 800 | non établi | 4,0 % | 60,5 % | 4,5 % | 5,4 % |
| Autres villes, villages et campagnes (résiduel) | 344 200 | non établi | 1,5 % | 67,6 % | 48,9 % | 3,3 % |

### Stravian Domains

Contexte : [PG p. 12](Sources/pg.md), [PG p. 12–13](Sources/pg.md), [PG p. 13](Sources/pg.md), [PG p. 21](Sources/pg.md), [SB p. 14](Sources/sb.md), [SB p. 160](Sources/sb.md), [SB p. 160–161](Sources/sb.md), [SB p. 160–163](Sources/sb.md). Les pages soutiennent mécanismes, cultures et institutions ; les parts ci-dessous sont proposées.

| Lieu | Habitants | Nobles / habitants | Privilégiés / habitants | Actifs / habitants | Vivrier / habitants | Sans emploi / actifs |
|---|---:|---|---:|---:|---:|---:|
| Stonelair | 65 000 | non établi | 4,0 % | 60,5 % | 4,5 % | 5,4 % |
| Mirare | 25 000 | non établi | 4,0 % | 60,5 % | 13,5 % | 5,4 % |
| Eclipse Village | 4 000 | non établi | 4,0 % | 60,2 % | 16,6 % | 6,5 % |
| Eb’boria | 4 000 | non établi | 1,5 % | 67,6 % | 48,9 % | 3,3 % |
| Autres villes minières | 90 000 | non établi | 4,0 % | 60,5 % | 5,6 % | 5,4 % |
| Villages agricoles du Sud | 350 000 | non établi | 1,5 % | 67,6 % | 48,9 % | 3,3 % |
| Autres villes, villages et campagnes (résiduel) | 422 000 | non établi | 1,5 % | 67,6 % | 42,4 % | 3,3 % |

### Storm Islands

Contexte : [SB p. 168](Sources/sb.md), [SB p. 169](Sources/sb.md), [SB p. 170](Sources/sb.md), [SB p. 171](Sources/sb.md), [SB p. 172](Sources/sb.md), [SB p. 173](Sources/sb.md). Les pages soutiennent mécanismes, cultures et institutions ; les parts ci-dessous sont proposées.

| Lieu | Habitants | Nobles / habitants | Privilégiés / habitants | Actifs / habitants | Vivrier / habitants | Sans emploi / actifs |
|---|---:|---|---:|---:|---:|---:|
| Night Mansions | 95 000 | non établi | 3,0 % | 72,0 % | 1,3 % | 2,0 % |
| Autres villes, villages et campagnes (résiduel) | 291 000 | non établi | 3,0 % | 72,0 % | 11,0 % | 2,0 % |

### Taii’Maku City States

Contexte : [SB p. 174](Sources/sb.md), [SB p. 175](Sources/sb.md), [SB p. 176](Sources/sb.md), [SB p. 177](Sources/sb.md), [SB p. 178](Sources/sb.md), [SB p. 179](Sources/sb.md), [SB p. 180](Sources/sb.md), [SB p. 181](Sources/sb.md). Les pages soutiennent mécanismes, cultures et institutions ; les parts ci-dessous sont proposées.

| Lieu | Habitants | Nobles / habitants | Privilégiés / habitants | Actifs / habitants | Vivrier / habitants | Sans emploi / actifs |
|---|---:|---|---:|---:|---:|---:|
| Awo Irin Illu | 130 000 | non établi | 2,0 % | 44,1 % | 1,1 % | 2,0 % |
| G’bagede Illu | 100 000 | non établi | 2,0 % | 24,0 % | 0,0 % | 0,0 % |
| Ilaorun Illu | 115 000 | non établi | 2,0 % | 44,1 % | 0,8 % | 2,0 % |
| Maro’Si Illu | 85 000 | non établi | 2,0 % | 44,1 % | 1,9 % | 2,0 % |
| Autres Illus | 198 000 | non établi | 2,0 % | 44,1 % | 1,9 % | 2,0 % |
| Villages humains et autres communautés | 70 000 | non établi | 2,0 % | 67,5 % | 44,3 % | 3,3 % |

### Theocracy of Kepesh

Contexte : [SB p. 182](Sources/sb.md), [SB p. 183](Sources/sb.md), [SB p. 184](Sources/sb.md), [SB p. 185](Sources/sb.md), [SB p. 186](Sources/sb.md), [SB p. 187](Sources/sb.md), [SB p. 188](Sources/sb.md), [SB p. 189](Sources/sb.md). Les pages soutiennent mécanismes, cultures et institutions ; les parts ci-dessous sont proposées.

| Lieu | Habitants | Nobles / habitants | Privilégiés / habitants | Actifs / habitants | Vivrier / habitants | Sans emploi / actifs |
|---|---:|---|---:|---:|---:|---:|
| Pakaitos | 40 000 | non établi | 15,0 % | 59,5 % | 6,7 % | 5,1 % |
| Bright Coast (villages résidents) | 75 000 | non établi | 3,0 % | 67,3 % | 46,8 % | 3,3 % |
| Brightlight — Sirocchi | 40 000 | non établi | 3,0 % | 67,3 % | 42,2 % | 3,3 % |
| Brightlight — Zaphyrus | 30 000 | non établi | 3,0 % | 67,3 % | 46,8 % | 3,3 % |
| Brightlight — Verdani | 35 000 | non établi | 3,0 % | 67,3 % | 44,2 % | 3,3 % |
| Autres villes, villages et campagnes (résiduel) | 475 000 | non établi | 3,0 % | 67,3 % | 42,2 % | 3,3 % |

### Tsvetan

Contexte : [SB p. 190](Sources/sb.md), [SB p. 191](Sources/sb.md), [SB p. 192](Sources/sb.md), [SB p. 193](Sources/sb.md), [SB p. 194](Sources/sb.md), [SB p. 195](Sources/sb.md), [SB p. 196](Sources/sb.md), [SB p. 197](Sources/sb.md). Les pages soutiennent mécanismes, cultures et institutions ; les parts ci-dessous sont proposées.

| Lieu | Habitants | Nobles / habitants | Privilégiés / habitants | Actifs / habitants | Vivrier / habitants | Sans emploi / actifs |
|---|---:|---|---:|---:|---:|---:|
| Feargus | 20 000 | non établi | 2,0 % | 60,2 % | 8,2 % | 7,8 % |
| Eferhild Citadel | 12 000 | non établi | 3,0 % | 60,6 % | 14,1 % | 5,4 % |
| Hot Bloods (campements) | 90 000 | non établi | 3,0 % | 67,3 % | 29,9 % | 3,3 % |
| Spiked Bones (campements) | 120 000 | non établi | 3,0 % | 67,3 % | 45,5 % | 3,3 % |
| Stone Fangs (campements) | 90 000 | non établi | 3,0 % | 67,3 % | 42,2 % | 3,3 % |
| Strong Fists (villages et champs) | 136 000 | non établi | 3,0 % | 67,3 % | 48,1 % | 3,3 % |

### Yama

Contexte : [SB p. 198](Sources/sb.md), [SB p. 199](Sources/sb.md), [SB p. 200](Sources/sb.md), [SB p. 201](Sources/sb.md), [SB p. 202](Sources/sb.md), [SB p. 203](Sources/sb.md), [SB p. 204](Sources/sb.md), [SB p. 205](Sources/sb.md). Les pages soutiennent mécanismes, cultures et institutions ; les parts ci-dessous sont proposées.

| Lieu | Habitants | Nobles / habitants | Privilégiés / habitants | Actifs / habitants | Vivrier / habitants | Sans emploi / actifs |
|---|---:|---|---:|---:|---:|---:|
| Yamanoma | 45 000 | 8,0 % | 6,4 % | 58,8 % | 5,5 % | 5,4 % |
| Tiger Monastery | 2 500 | 2,0 % | 4,0 % | 60,1 % | 3,8 % | 5,4 % |
| Neshin | 5 000 | 1,0 % | 1,5 % | 67,4 % | 42,9 % | 3,3 % |
| Umay | 15 000 | 3,0 % | 4,0 % | 59,9 % | 12,3 % | 5,4 % |
| Bushi | 5 000 | 1,0 % | 1,5 % | 67,4 % | 42,9 % | 3,3 % |
| Autres villes, villages et campagnes (résiduel) | 720 500 | 1,5 % | 1,5 % | 67,3 % | 42,8 % | 3,3 % |

### Undertanares

Contexte : [SB p. 206](Sources/sb.md), [SB p. 207](Sources/sb.md). Les pages soutiennent mécanismes, cultures et institutions ; les parts ci-dessous sont proposées.

| Lieu | Habitants | Nobles / habitants | Privilégiés / habitants | Actifs / habitants | Vivrier / habitants | Sans emploi / actifs |
|---|---:|---|---:|---:|---:|---:|
| Autres cités naines | n.r. | non établi | 4,0 % | 60,5 % | 14,1 % | 5,4 % |
| Dorsian Forge (occupants duergars) | n.r. | non établi | 8,0 % | 60,1 % | 2,8 % | 5,3 % |
| Invisible Patrol Hive / autres ruches | n.r. | non établi | 0,0 % | 68,0 % | 40,8 % | 3,0 % |
| Communautés Stonehide | n.r. | non établi | 1,5 % | 67,6 % | 26,1 % | 3,3 % |
| Communautés Bloodgod / Skullcrusher / Shadoweye | n.r. | non établi | 1,5 % | 67,6 % | 35,9 % | 3,3 % |

Référence régionale relative : Autres cités naines 35 %, Dorsian Forge (occupants duergars) 15 %, Invisible Patrol Hive / autres ruches 25 %, Communautés Stonehide 15 %, Communautés Bloodgod / Skullcrusher / Shadoweye 10 %. Ces poids de mélange sont proposés, aucun recensement ni effectif absolu n’est connu.

### Darkall

Contexte : [SB p. 208](Sources/sb.md), [SB p. 209](Sources/sb.md), [SB p. 210](Sources/sb.md). Les pages soutiennent mécanismes, cultures et institutions ; les parts ci-dessous sont proposées.

| Lieu | Habitants | Nobles / habitants | Privilégiés / habitants | Actifs / habitants | Vivrier / habitants | Sans emploi / actifs |
|---|---:|---|---:|---:|---:|---:|
| North — cités-États kemets | n.r. | non établi | 10,0 % | 62,0 % | 6,8 % | 2,0 % |
| Central — villes murées et forteresses | n.r. | non établi | 2,0 % | 70,0 % | 36,2 % | 2,0 % |

Référence régionale relative : North — cités-États kemets 50 %, Central — villes murées et forteresses 50 %. Ces poids de mélange sont proposés, aucun recensement ni effectif absolu n’est connu.

### Mystical / Wasteland

Contexte : [SB p. 210](Sources/sb.md), [SB p. 211](Sources/sb.md). Les pages soutiennent mécanismes, cultures et institutions ; les parts ci-dessous sont proposées.

Aucun profil de population civile vivante ordinaire. Arcana conserve ses habitants et spécialistes morts-vivants dans le registre, avec effectifs et convention de citoyenneté inconnus ; les visiteurs vivants ont leur résidence ailleurs. Les soins et récupération impossibles au centre, réduits aux frontières, doivent être résolus avant tout camp permanent proposé.

## Chaque métier expose sa preuve, son accès social et son calcul

La justification d’une ligne hérite de règles réelles et résolues : **filière**, métier de **base**, **spécialité**, **région**, **localité**, **milieu social** et mode de **calcul**. La filière explique travailleurs, apprentissage, ressources, saisons et clients ; la spécialité ajoute site, licence ou rareté ; le contexte local explique demande et résidence ; les strates expliquent capital, accès et activité. L’explorateur expose cette chaîne avec les sources lisibles, le budget civil, le coefficient technique choisi, sa normalisation et la contribution de chaque strate. Les zéros affichent le motif de ressource, formation, site, culte ou absence d’établissement dans le scénario. L’export CSV inclut les distributions nobles/peuple et milieux privilégiés, les parts conditionnelles et les explications. Les références source prouvent l’activité ou le contexte ; **les nombres sont toujours P**.

Pour une strate s de part résidente r_s, taux d’activité a_s et chômage actif u_s, sa part d’occupés parmi tous habitants vaut **r_s × a_s × (1 − u_s)** en fractions. La somme donne E/H ; la somme r_s × a_s donne A/H. Chaque métier civil reçoit son budget de filière, puis son coefficient technique normalisé parmi les métiers admissibles ; les soldats sont réintégrés au stock occupé. Les préférences professionnelles de chaque strate sont ajustées à ces marges de métiers, en conservant les emplois, chômeurs et inactifs de chaque strate. Ainsi **% métier parmi actifs = % métier parmi habitants ÷ (A/H)**. Les filtres nobles, peuple, privilégiés ou ordinaires changent explicitement le dénominateur ; ils ne réétiquettent pas les chiffres d’ensemble.

Les habitants sans métier principal comprennent chômeurs disponibles et personnes hors activité. Les enfants, apprentis et retraités sont actifs seulement s’ils produisent effectivement ; aucun âge humain de 18 ans n’est imposé aux espèces. Les niveaux apprenti/compagnon/maître, charges d’officier ou porte-étendard, affiliations et métiers appris restent des attributs. **La mendicité est transversale** : salarié pauvre, chômeur, retraité ou personne incapable peut mendier. Ses trois contributions occupés/chômeurs/inactifs sont comptées séparément, sans deuxième individu. Un taux de noble ou de privilégié porte également sur les enfants et inactifs, pas seulement les employés.

Les **42 contrôles numériques** couvrent sommes des deux dénominateurs, strates, matrice métier–milieu, vues conditionnelles, marges d’espèces, totaux locaux, garnisons, résidence Downtown, clergés, sites rares et vivrier, ainsi que présence de sources contextuelles et résolution des règles héritées. Ils démontrent validité des comptes et contraintes ciblées, **pas besoins alimentaires ou prix équilibrés**. Le fichier de contrôle indique séparément les tests de l’explorateur et l’absence de vérification visuelle.

### Catalogue proposé conservé

**A** signifie activité ou intitulé attesté, **D** filière/spécialisation déduite, **P** proposition conservée. La hiérarchie entière est une décision de jeu. Les bases ne s’ajoutent pas à leurs enfants ; chaque occupé possède une seule feuille principale. Barbier, service domestique, guide, garde, combattant et contrôleur arcanique sont des disciplines distinctes ; aucune progression automatique du guide au mage. Le maître de cérémonie du thé est un service rituel, distinct de fabriquer des boissons. Les compétences secondaires couvrent les croisements sans double compte. Boursier reste fabricant de bourses en cuir ; terrassier conserve ici l’entretien urbain et les déchets.

| Métier de base proposé | Feuilles principales et appui documentaire |
|---|---|
| Agriculteur | Agriculteur généraliste (A, SB90, SB198) ; Céréalier (D, SB90, SB198) ; Riziculteur (A, SB198) ; Vigneron (A, MJ128) ; Cultivateur d’épices (A, SB182) ; Cultivateur d’herbes pour thé (D, SB198) ; Maraîcher (D, SB90, SB198) ; Cultivateur de tubercules (A, SB120, SB168) |
| Horticulteur | Jardinier (A, SB29, SB161) ; Fleuriste (A, SB29, SB161) ; Arboriculteur de verger (D, SB29, SB161) ; Jardinier de roses magiques (A, SB157) ; Arboriculteur de breithwood (D, SB152) |
| Éleveur | Éleveur généraliste (A, SB120, SB182) ; Berger (A, MJ135) ; Éleveur de yaks (A, SB120) ; Éleveur de chevaux (A, SB182) ; Éleveur de chameaux (A, SB182) ; Éleveur de vers à soie (A, SB198) ; Éleveur de loups géants (A, SB191) ; Éleveur de montures volantes (A, SB124, SB107) ; Apiculteur (P, SB152) |
| Chasseur | Chasseur de gibier (A, MJ139, PG20) ; Trappeur (A, MJ140) ; Chasseur de monstres (A, PG58) ; Chasseur de monstres marins (A, SB148) ; Chasseur de dragons (A, SB220) |
| Collecteur de ressources | Cueilleur (A, MJ139, SB153) ; Herboriste de collecte (D, BR55) ; Collecteur de composants de créatures (A, SB104, SB139) ; Collecteur de perles (D, SB149) ; Récupérateur de reliques penumbrales (A, PG8) |
| Travailleur forestier | Bûcheron (A, MJ135, SB107) ; Forestier (A, MJ140) ; Scieur (D, SB99) |
| Pêcheur | Pêcheur maritime (A, SB110, SB168) ; Pêcheur d’eau douce (A, SB138) ; Cultivateur marin (P, SB149) |
| Extracteur de ressources minérales | Mineur (A, MJ135, SB160) ; Carrier (D, MJ135, SB160) ; Salinier (P, SB120) ; Mineur de bauronite (A, SB174, SB182) ; Mineur de tameranium (A, SB168, SB198) ; Extracteur d’obsidienne (A, SB190) ; Extracteur de soufre (A, SB190) ; Prospecteur (D, SB104) |
| Meunier | Meunier (D, SB121) |
| Boucher | Boucher (D, SB99) ; Écorcheur (A, MJ128) |
| Boulanger | Boulanger (A, MJ128) |
| Cuisinier | Cuisinier (A, MJ128) ; Cuisinier de haute cuisine (A, PG28, CC52) |
| Transformateur alimentaire | Poissonnier (D, SB120, SB149) ; Saleur et sécheur alimentaire (D, SB120, SB149) ; Fromager (A, SB120, SB149) ; Huilier (P, SB120, SB149) |
| Fabricant de boissons | Brasseur (A, MJ128, SB120) ; Distillateur (A, MJ128, SB120) ; Distillateur de Highlandtuber (A, SB120, SB121) |
| Alchimiste | Alchimiste (A, MJ128, BR55) ; Apothicaire (A, MJ128, BR55) ; Préparateur de poisons (D, BR55, SB193) ; Préparateur de potions (A, SB138) ; Préparateur d’Estelindea (A, SB153) |
| Charbonnier | Charbonnier (P, SB128) |
| Métallurgiste | Fondeur et affineur (D, SB198, SB160) ; Aciériste (D, SB198) |
| Forgeron | Forgeron (A, MJ128) ; Armurier (A, MJ128) ; Coutelier (D, MJ128) ; Rémouleur (D, MJ128) |
| Mécanicien et artisan du métal | Serrurier (A, MJ128, SB174) ; Rétameur (A, MJ128, SB174) ; Réparateur et bricoleur (A, MJ128, SB174) ; Horloger (D, SB174) ; Fabricant d’outils de précision (A, SB174) ; Fabricant d’instruments de navigation (D, SB174) |
| Bijoutier | Bijoutier (A, MJ128) ; Orfèvre (A, MJ128) ; Lapidaire et tailleur de gemmes (A, MJ128) |
| Tanneur | Tanneur (A, MJ128) ; Fourreur (D, SB120, SB133) |
| Artisan du cuir | Maroquinier (A, MJ128) ; Bourrelier et sellier (D, MJ128, SB163) ; Boursier, fabricant de bourses (D, MJ128) ; Gantier (D, MJ128) ; Cordonnier (A, MJ128) |
| Artisan textile | Fileur (D, MJ128) ; Tisserand (A, MJ128) ; Teinturier (A, MJ128) |
| Tailleur de vêtements | Tailleur (D, MJ128, SB139) ; Modiste et fabricant de coiffes (D, SB139, SB120) |
| Tapissier | Tapissier (D, SB200) |
| Menuisier | Menuisier (D, MJ128, SB152) ; Ébéniste (D, MJ128) ; Sculpteur sur bois (A, MJ128) ; Tonnelier (A, MJ128) ; Charron (A, MJ128) |
| Charpentier | Charpentier (A, MJ128) ; Couvreur (A, MJ128) |
| Constructeur naval | Constructeur naval (A, MJ128, SB148) ; Calfat (D, MJ128, SB148) ; Constructeur de drakkars (A, SB130) |
| Cordier | Cordier (D, SB130) ; Voilier (A, MJ128) |
| Facteur d’arcs | Facteur d’arcs (A, MJ128, SB152) ; Fabricant de flèches (A, SB152) |
| Luthier | Luthier et facteur d’instruments (D, BR55) |
| Tailleur de pierre | Tailleur de pierre (A, MJ128, SB161) ; Sculpteur sur pierre (D, MJ128, SB161) ; Sculpteur de statues de Stone Spirits (A, SB161) |
| Maçon | Maçon (A, MJ128, SB90) ; Plâtrier (A, MJ128, SB90) ; Manœuvre de chantier (A, SB90) |
| Architecte | Architecte (A, SB174) ; Géomètre et arpenteur (A, MJ128) |
| Potier | Potier (A, MJ128, SB200) ; Tuilier (A, MJ128, SB200) ; Porcelainier (D, SB200) |
| Verrier | Souffleur de verre (A, MJ128, SB174) ; Vitrier (A, MJ128, SB174) ; Opticien et fabricant de lentilles (D, SB174) |
| Papetier et artisan du livre | Papetier (A, SB138) ; Relieur (D, SB138, MJ128) |
| Chandelier | Chandelier (P, SB98) |
| Peintre | Peintre (A, MJ128, SB190) ; Fabricant d’enseignes (A, MJ128, SB190) ; Enlumineur (A, MJ128, SB190) ; Peintre de guerre spirituel (A, SB193) ; Tatoueur rituel (D, SB200, SB204) |
| Transporteur terrestre | Portefaix (D, MJ132, SB121) ; Docker (D, MJ132, SB121) ; Magasinier (D, MJ132, SB121) ; Charretier et cocher (D, MJ132, SB121) ; Chef de caravane (A, MJ132) ; Coursier et messager (D, MJ132, SB121) ; Porteur d’eau (P, MJ132, SB121) ; Transporteur de canopée (D, SB154) ; Opérateur de Stone Disks (A, PG13) ; Palefrenier et soigneur d’écurie (D, SB123) |
| Marin | Marin (A, MJ136) ; Navigateur (A, MJ136) ; Pilote de port (D, MJ136) ; Capitaine de navire (A, MJ136) ; Pilote de véhicule volant (D, SB142, SB174) |
| Hôte professionnel | Aubergiste (D, SB110, SB123) ; Tavernier (A, SB108, SB149) |
| Employé domestique et aide familiale | Domestique (A, MJ135, PG40) ; Gardien d’enfants (A, PG40) |
| Agent d’entretien | Terrassier d’hygiène urbaine (P, SB90) ; Ramoneur (P, SB90) |
| Agent funéraire | Fossoyeur (A, MJ135, SB99, SB182) ; Gardien de cimetière (A, MJ135, SB99, SB182) ; Momificateur (A, SB182) ; Gardien d’arbres funéraires (D, SB155) |
| Marchand | Marchand (A, MJ128, SB139) ; Colporteur (A, SB121) ; Courtier (A, SB149) ; Commissaire-priseur d’objets magiques (A, SB139) |
| Professionnel de finance | Comptable (D, SB212, SB213) ; Banquier et employé de banque (A, SB212, SB213) ; Usurier et prêteur sur gages (D, SB212, SB213) ; Changeur (D, SB212, SB213) ; Assureur (D, SB212, SB213) ; Estimateur (A, SB212, SB213) ; Négociateur (A, SB212, SB213) |
| Scribe et auteur | Scribe (A, MJ128, SB32) ; Calligraphe (A, MJ128, SB32) ; Écrivain (A, MJ128, SB32) ; Journaliste et rédacteur (A, CC9) ; Traducteur (D, SB198) |
| Érudit | Bibliothécaire (A, MJ138) ; Conservateur de musée (A, PG48) ; Historien (A, PG46) ; Astronome (A, MJ138) ; Chercheur non arcanique (A, MJ138, PG46) ; Mathématicien (A, SB174) ; Philosophe (A, SB178) ; Archéologue (D, PG48) |
| Enseignant | Professeur (A, MJ138, SB141) ; Enseignant de magie arcanique (A, SB141) ; Instructeur martial (A, SB94) ; Formateur de tir à l’arc (A, SB155) |
| Ingénieur | Ingénieur (A, SB174) ; Inventeur (A, SB178) ; Ingénieur mystique (A, SB174) ; Créateur et mainteneur de golems (D, SB174) ; Chercheur en golems (A, SB178) ; Ingénieur de réacteurs de bauronite (D, SB174) ; Technicien de communication runique (D, SB174) |
| Praticien des services arcaniques | Chercheur en magie (A, SB138, SB139) ; Fabricant d’objets magiques (A, SB138) ; Fabricant de parchemins magiques (A, SB138) ; Nécromancien de service (D, SB108, SB170) ; Illusionniste de service (D, SB107, SB142) ; Chercheur en aethermancy (A, SB140) ; Chercheur en biomancy (A, SB140) ; Désenchanteur et récupérateur arcanique (A, SB139) ; Extracteur de mémoire (A, SB140) ; Certificateur et inspecteur arcanique (A, SB139) ; Opérateur de transport magique (D, SB142) ; Restaurateur de runes de tunnels (A, SB161) ; Artificier psychique (A, PG8) |
| Soigneur | Guérisseur (A, MJ141, PG36) ; Chirurgien (P, MJ141, PG36) ; Praticien de psychosurgery (D, SB94) ; Opérateur de thérapie onirique (D, SB141, SB228) |
| Officiant religieux | Prêtre et officiant (A, MJ127, SB182) ; Acolyte (A, MJ127, SB182) ; Shaman (A, SB129, SB191) ; Sugenja (A, SB198) ; Gardien et officiant druidique (A, SB153) ; Gardien-purificateur de Mother Tree (A, SB153) ; Officiant des rites Ba-Akhu (A, SB184) |
| Garde et surveillant | Garde et sentinelle (A, MJ140, SB90) ; Garde du corps (A, MJ140, SB90) ; Veilleur de nuit (P, MJ140, SB90) ; Gardien de domaine (A, MJ140) ; Inquisiteur (A, SB29) |
| Enquêteur et agent de renseignement | Détective (A, PG9, BR42) ; Espion (A, PG9, BR42) ; Détective arcanique (A, SB140) |
| Administrateur et juriste | Fonctionnaire (A, SB90, SB213) ; Percepteur (A, SB132) ; Juge (A, SB90, SB213) ; Avocat (A, SB90, SB213) ; Diplomate et émissaire (A, PG46) ; Recruteur et agent de missions (D, SB105) ; Bourreau (A, SB148) |
| Artiste du spectacle | Acteur et comédien (A, MJ129) ; Danseur (A, MJ129) ; Musicien (A, MJ129) ; Chanteur (A, MJ129) ; Poète (A, MJ129) ; Conteur (A, MJ129) ; Bouffon (A, MJ129) ; Jongleur (A, MJ129) ; Acrobate (A, MJ129) ; Cracheur de feu (A, MJ129) ; Compositeur (A, PG28) ; Crieur public (P, MJ129) |
| Professionnel du jeu | Joueur professionnel (P, SB99) ; Croupier (D, SB99) ; Preneur de paris (D, SB99) |
| Opérateur d’activités illicites | Maître-chanteur (A, BR42) ; Cambrioleur (A, BR42) ; Homme de main (A, BR42) ; Receleur (A, BR42) ; Voleur de grand chemin (A, BR42) ; Tueur à gages (A, BR42) ; Pickpocket (A, BR42) ; Contrebandier (A, BR42) ; Pirate (A, MJ136) |
| Cartographe | Cartographe (A, MJ128) |
| Barbier | Barbier (P, MJ135, PG40) |
| Guide | Guide (A, MJ140) |
| Protecteur et contrôleur arcanique | Spellshield (A, SB140) ; Warden des Arcane Enforcers (A, SB140) ; Mage impérial chargé du contrôle (A, SB98) |
| Combattant professionnel | Soldat (A, MJ140, SB90) ; Mercenaire (A, MJ140, SB90) ; Éclaireur (A, MJ140, SB90) ; Gladiateur (A, MJ130) ; Champion d’arène (A, SB90) ; Chasseur de primes (A, MJ140) ; Chasseur de morts-vivants (A, SB210) |
| Maître de cérémonie du thé | Maître de cérémonie du thé (A, SB201) |

### Les 49 entrées initiales restent identifiées

| Entrée initiale | Classement proposé | Métier de base de rattachement | Feuille(s) de comptage |
|---|---|---|---|
| Apothicaire | specialisation | Alchimiste | Apothicaire |
| Architecte | base | Architecte | Architecte |
| Armurier | specialisation | Forgeron | Armurier |
| Aubergiste | specialisation | Hôte professionnel | Aubergiste |
| Barbier | base | Barbier | Barbier |
| Bibliothécaire | specialisation | Érudit | Bibliothécaire |
| Bijoutier | base | Bijoutier | Bijoutier |
| Boucher | base | Boucher | Boucher |
| Boulanger | base | Boulanger | Boulanger |
| Bourrelier/Sellier | specialisation | Artisan du cuir | Bourrelier et sellier |
| Boursier/Gantier | specialisation | Artisan du cuir | Boursier, fabricant de bourses ; Gantier |
| Brasseur | specialisation | Fabricant de boissons | Brasseur |
| Cartographe | base | Cartographe | Cartographe |
| Chandelier | base | Chandelier | Chandelier |
| Charbonnier | base | Charbonnier | Charbonnier |
| Charpentier | base | Charpentier | Charpentier |
| Comptable | specialisation | Professionnel de finance | Comptable |
| Cordier | base | Cordier | Cordier |
| Cordonnier | specialisation | Artisan du cuir | Cordonnier |
| Coursier/Messager | specialisation | Transporteur terrestre | Coursier et messager |
| Coutelier | specialisation | Forgeron | Coutelier |
| Crieur | specialisation | Artiste du spectacle | Crieur public |
| Forgeron | base | Forgeron | Forgeron |
| Fourreur | specialisation | Tanneur | Fourreur |
| Joueur professionnel | specialisation | Professionnel du jeu | Joueur professionnel |
| Maçon | base | Maçon | Maçon |
| Marchand | base | Marchand | Marchand |
| Menuisier | base | Menuisier | Menuisier |
| Papetier | specialisation | Papetier et artisan du livre | Papetier |
| Pêcheur | base | Pêcheur | Pêcheur maritime |
| Peintre | base | Peintre | Peintre |
| Poissonnier | specialisation | Transformateur alimentaire | Poissonnier |
| Porteur d’eau | specialisation | Transporteur terrestre | Porteur d’eau |
| Potier | base | Potier | Potier |
| Ramoneur | specialisation | Agent d’entretien | Ramoneur |
| Relieur | specialisation | Papetier et artisan du livre | Relieur |
| Rémouleur | specialisation | Forgeron | Rémouleur |
| Scribe | specialisation | Scribe et auteur | Scribe |
| Serrurier | specialisation | Mécanicien et artisan du métal | Serrurier |
| Souffleur de verre | specialisation | Verrier | Souffleur de verre |
| Tailleur de pierre | base | Tailleur de pierre | Tailleur de pierre |
| Tapissier | base | Tapissier | Tapissier |
| Tanneur | base | Tanneur | Tanneur |
| Tavernier | specialisation | Hôte professionnel | Tavernier |
| Terrassier | specialisation | Agent d’entretien | Terrassier d’hygiène urbaine |
| Tisserand | specialisation | Artisan textile | Tisserand |
| Tonnelier | specialisation | Menuisier | Tonnelier |
| Usurier/Prêteur sur gages | specialisation | Professionnel de finance | Usurier et prêteur sur gages |
| Veilleur de nuit | specialisation | Garde et surveillant | Veilleur de nuit |

### Les décisions encore ouvertes

Restent à valider les tailles et milieux sociaux proposés, les titres reconnus dans les sociétés où la catégorie demeure inconnue, les cycles de vie et la participation effective par espèce, les aides sociales, navettes et visiteurs, les personnes mortes-vivantes intelligentes, les consommations, rendements, flux et capacités surnaturelles. Les traditions orientent les droits, formations et clientèle sans enfermer biologiquement une espèce dans un métier ; seule l’opération des Stone Disks garde la restriction sourcée aux prêtres nains Dorsi formés. Les modèles ordinaires peuvent évoluer avec saisons, migration et installation d’un atelier ; un zéro de scénario ne clôt pas le monde.

Sources : [Tanares Sourcebook](Sources/sb.md), [Player’s Guide to Tanares](Sources/pg.md), [Manuel des Joueurs](Sources/mj.md), [Basic Rules](Sources/br.md), [Character Compendium](Sources/cc.md), [Guide du Maître](Sources/gm.md). Tous les numéros cités sont les pages imprimées. Les données de fréquences et de noblesse proposées n’existent pas comme tableaux statistiques dans ces livres.

## Révision alimentaire V3 : les réaffectations restent visibles

Les mêmes personnes du budget vivrier changent de spécialisation principale selon culture et habitat. Les parts sociales, espèces, garnisons, taux d’activité et totaux régionaux sont conservés. Les profils gardent leur ancienne répartition et le delta exact ; les rôles de maintenance des serviteurs et de récolte saisonnière sont des temps secondaires retirés de leurs métiers principaux. Le panneau alimentaire de l’explorateur affiche consommations, production, desserte, stocks, contraintes et stress.

| Région | Couverture énergétique après échanges | Hectares cultivés/an | Cargaisons importées réelles (t/an) | Réserve de sécurité (jours) |
|---|---:|---:|---:|---:|
| Central Empire | 129.9 % | 1,232,877 | 900 | 90 |
| Republic of Freelands | 100.0 % | 760,549 | 56,110 | 90 |
| Imperial Ben’net | 100.0 % | 106,667 | 11,922 | 180 |
| Kingdom of Kolbjörn | 100.0 % | 390,174 | 88,962 | 180 |
| Magocracy of Mage Tower | 136.5 % | 482,759 | 0 | 90 |
| Seashores | 100.0 % | 78,571 | 35,255 | 90 |
| Sindile Forest | 107.9 % | 179,592 | 0 | 90 |
| Stravian Domains | 136.2 % | 664,617 | 0 | 90 |
| Storm Islands | 109.3 % | 418,821 | 0 | 180 |
| Taii’Maku City States | 100.0 % | 168,718 | 127,227 | 90 |
| Theocracy of Kepesh | 100.1 % | 344,828 | 167,558 | 90 |
| Tsvetan | 100.9 % | 284,746 | 0 | 90 |
| Yama | 118.4 % | 298,574 | 0 | 90 |
