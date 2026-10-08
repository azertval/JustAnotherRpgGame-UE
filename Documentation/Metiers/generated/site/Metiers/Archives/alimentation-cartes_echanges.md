# Carte, corridors et approvisionnement de Tanares

Lecture du 7 octobre 2026 : pixels réellement inspectés du VTT mondial et de Map - Capital.jpg. Standard cartographique lu ; aucune carte, référence ou donnée canonique modifiée. Les recadrages analytiques restent dans ce dossier de recherche.

## Échelle physique trouvée et limites de surface

**Le VTT mondial possède une barre 0–500 Miles**. Lecture image originale 9933×7016 : segment x=8263..9782 inclus, ligne y=6820, **1520 pixels**. Donc 0,328947 mile/pixel = 0,5294105 km/pixel ; carré projeté 0,2802755 km²/pixel. Incertitude de lecture ±1 % conservatrice, indépendamment d’erreur de tracé/relief (au moins 10–20 % sur itinéraires manuels). La carte entière représente un cadre ~5258×3714 km incluant mers ; ce n’est pas surface continentale. Aucune latitude, projection ou grille géodésique trouvée. [Carte primaire](../Sources/cartes.md#carte-monde).

Le standard interdit la conversion des coordonnées graphiques des illustrations du jeu en mètres/cases. Cette lecture concerne exclusivement la référence géographique VTT, son échelle réellement imprimée, avec géographie de référence ; aucun anchor artistique ne sert de mesure. Les FRAMES du script sont des cadres de consultation et non limites de régions, encore moins surfaces agricoles. Les coordonnées de nodes du JSON servent au graphique ; les chords sont bornes inférieures géométriques et jamais trajets navigables. [Standard](../Sources/cartes.md#convention).

**Surface agricole** : tracer un masque terrestre/contours régionaux puis retirer glace, lave, rocher, pente, zones humides impropres, implantations, forêt sacrée/protégée ; rendre explicites les fractions P de cultures/pâtures/bois. Le relief peint ne donne pas pente mesurée ni sol profond ; aire projetée ne vaut pas aire exploitée. Aucun hectare numérique régional fiable n’est établi dans cette passe.

## Réseau attesté et corridors proposés

Légende VTT lue en pixels : orange Imperial Road, vert Secondary Road, pointillé frontière, symboles séparés village/town/city/capital/fort/site. Les routes visibles établissent présence et voisinage, pas largeur, entretien, débit journalier ni liberté politique.

- **Mirare → Stonelair** [A], stone_disks : food, workers, ore reverse flow. SB254 explicitly most-used StoneDisks connection; subterranean course unknown Risque : Runes/qualified dwarven priest, no open continental tunnel map. ; chord cartographique 378.5 miles minimum, **pas distance routière/maritime**. [SB p. 14, 160, 254](../Sources/sb.md).
- **Stonelair → Mirare** [A_trade_D_route], surface_road : ores, tools, food reverse flow. Orange VTT trunk through Orgoth Valley; road rather than invented direct tunnel Risque : Bandits, imperial sabotage; secure settlements do not secure roads. ; chord cartographique 378.5 miles minimum, **pas distance routière/maritime**. [SB p. 14, 160, 162](../Sources/sb.md).
- **Kolbjörn → Stonelair** [A_trade_D_route], road_via_Hammer_Passing_Tigers_Bridge : livestock, leather, drakkars only if navigable water separate. Road via Hangedelf–Hammer Passing–Tiger’s Bridge–Mirare/Stonelair, observed VTT. No carriage carries full ship. Risque : Mountain pass/weather, costs crossing Republic/Stravian territory, bandits. ; chord cartographique 1106.8 miles minimum, **pas distance routière/maritime**. [SB p. 128, 160](../Sources/sb.md).
- **Fisherman’s Wharf → Stonelair** [A_trade_D_route], road_via_Cragplateaus_Mirare : livestock, leather, ores reverse flow. Map orange road through Cragplateaus approach, Heroes Rise area and Mirare road junction. Exact complete trace not metrically surveyed. Risque : Passes, monster frontier, escort demand. ; chord cartographique 1216.9 miles minimum, **pas distance routière/maritime**. [SB p. 104, 160](../Sources/sb.md).
- **Northharbor → Fisherman’s Wharf** [A], sea_Storm_Sea : ships, marine goods, furs, leather. Both ports and trade stated; coastal sea course west of Kolbjörn then south, NEVER a line through mainland. Risque : Kemets/Storm Islands raids; temples Bás expand cold; armed shipping. ; chord cartographique 790.6 miles minimum, **pas distance routière/maritime**. [SB p. 128, 133, 113](../Sources/sb.md).
- **Northharbor → Kepesh western coastal landing** [A_trade_D_landing], sea_Storm_Sea_then_road : ships, furs, leather, horses_spices reverse flow. Kolbjörn trade with Kepesh explicit; coast landing unnamed D, Pakaitos not a seaport. Risque : Kemet fleet, escort, coast incursions, desert last mile.. [SB p. 128, 133, 182](../Sources/sb.md).
- **Fisherman’s Wharf → Goldraft** [D], surface_road : grain, fish_preserved, goods_between_two_seas. Map roads and passes cross peninsula; FW western Storm Sea and Goldraft eastern Central Sea. NO short sea edge across land. Risque : Cragplateaus/Ruricans relief, road costs, Goldraft plague. ; chord cartographique 725.9 miles minimum, **pas distance routière/maritime**. [SB p. 110, 111, 113](../Sources/sb.md).
- **Goldraft → Bluhaven** [D], sea_Central_Sea : merchant_goods, preserved_food, fish, ship_services. Republic main commercial flows through Goldraft; Central Sea ports provide plausible marine corridor. No exact bilateral volume stated. Risque : Pirate tribute, theft, Goldraft contagion; no unconditional tax-free friendship. ; chord cartographique 362.4 miles minimum, **pas distance routière/maritime**. [SB p. 110, 113, 146, 150](../Sources/sb.md).
- **Imperial Capital → Northcross** [D], imperial_road : grain, barley, livestock, manufactured_goods. VTT orange road Capital–Southcross–Northcross around forest settlements; book Capital farming supply. Risque : Bak protected sacred core, taxes/inspection; not free forest conversion. ; chord cartographique 193.2 miles minimum, **pas distance routière/maritime**. [SB p. 90, 98, 99](../Sources/sb.md).
- **Northcross → Hajal** [D], imperial_road_via_Fox_Crossing : food, luxury, contracts. VTT orange road via river crossings/Fox Crossing; Hajal not fixed as seaport. Risque : Bridge capacity, northern climate, contract enforcement. ; chord cartographique 211.1 miles minimum, **pas distance routière/maritime**. [SB p. 93](../Sources/sb.md).
- **Hajal → Begraense** [A_trade_D_route], imperial_road_via_Septentrional_Passing : textiles, distillates, tools_food reverse flow. Southern Ben’net imperial road meets lowland network via named VTT pass. Large caravans stop Begraense. Risque : Cold/steep pass, tolls, Highlandtuber illicit; not same legal rate all alcohol. ; chord cartographique 250.6 miles minimum, **pas distance routière/maritime**. [SB p. 120, 121, 123](../Sources/sb.md).
- **Begraense → Cirrus mountain communities** [A], small_caravan_aerial_mixed : local_tubers, fish, rare_herbs, small_goods. Small local exchange attested. Mountain community endpoints not fixed; mounts/aerial access, not open grain motorway. Risque : Orders trust/access, cold, noncontinuous land access.. [SB p. 120, 124](../Sources/sb.md).
- **Northcross → Mesoriver** [D], imperial_road_via_Vault_Village : food, paper, magic_goods reverse flow. VTT northern road through Vault Village toward Mesoriver, border river crossing. Risque : Political frontier, magic certification; flux demand not volume. ; chord cartographique 455.2 miles minimum, **pas distance routière/maritime**. [SB p. 15, 138, 142](../Sources/sb.md).
- **Mesoriver → Imperial Capital** [A_trade_D_route], road_or_sea_multimodal : magic_goods, food reverse flow. Books frequent international trade; visible eastern road via Dawn of Light toward Capital. Region navigable rivers SB15 but no specific cargo draft/depth. Risque : Imperial magic restrictions; imports licensed, no invented universal embargo. ; chord cartographique 534.5 miles minimum, **pas distance routière/maritime**. [SB p. 138, 142, 98](../Sources/sb.md).
- **Sindile Forest → Seashores shipyards** [A_commodity_D_route], road_and_sea_or_specialist_delivery : breithwood. Shipcrafters explicitly need Sindile breithwood. Prefer forest→Yama eastern/northern bypass→Imperial coast then Central Sea, subject permissions; NOT direct road through Mystical. Risque : Protected forest/ecology, elite masters connections; costly logistics, high-value cargo not cereal highway.. [SB p. 152, 148](../Sources/sb.md).
- **Stonelair → Seashores shipyards** [A_commodity_D_route], road_to_Central_Sea_then_sea : bauronite, tameranium. Dwarven mines source shipcrafters material. Route via Mirare/Deverell-Central Sea landing unspecified then ship. Risque : Bauronite shock sensitive SB176; padded barrels lower useful payload.. [SB p. 148, 160](../Sources/sb.md).
- **Mesoriver → Seashores shipyards** [A_commodity_D_route], water_and_sea_multimodal : enchanted_crystals. Material sourced Mage Tower; regional waterways lead toward Central Sea, specific river leg navigability to verify. Risque : Certification and pirates, handling fragile material.. [SB p. 148, 15, 142](../Sources/sb.md).
- **Central Empire → Seashores shipyards** [A_commodity_D_route], road_and_sea : high_quality_steel. SB148 Imperial mines finest steel. Capital bay/docks VTT supplies plausible transshipment, no source exports tonnes. Risque : Tolls, Parliament control, scarcity and cargo losses.. [SB p. 148](../Sources/sb.md).
- **Freelands or Stravian food farms → Kepesh** [A_import_need_D_supplier], road_or_western_Central_Sea : fruits, legumes, staples_if_surplus. Kepesh imports fruits/legumes; supplying region not named. Northern land access from Freelands exists on VTT, desert road into Pakaitos. Risque : Water/feed for caravan, seasonal fruit perishability, oasis moving HagSalar unsuitable fixed depot SB186.. [SB p. 182, 160](../Sources/sb.md).
- **Kepesh → Taii’maku City States** [D], surface_road_or_train_if_authorized : bauronite, metals, engineering reverse flow. Nearby mineral rich region and explicit bauronite demand, southern road chain through Illus. No exact bilateral shipment claim. Risque : Border disputes and reactor secrets; mobile Illus not permanent rails everywhere.. [SB p. 174, 176, 182](../Sources/sb.md).
- **Yama trade gateway → Central Empire** [A_exports_D_route], road_northern_bypass_of_Mystical : rice, silk, steel, tea, tameranium reverse flow. Map orange eastern road connects Yama to northern temperate Empire, skirting Mystical. Open borders create trade, specific customer allocations P. Risque : Rare goods escorts, clan permissions, monsters; protected deposits policy.. [SB p. 198, 201](../Sources/sb.md).
- **Tsvetan → neighbors_via_coastal_or_southern_roads** [A_need_D_route], road_or_Central_Sea_coast : obsidian, platinum, sulfur, wood_metal reverse flow. VTT coast ports/roads west of Mystical and southern route by Ubelian Cauldron; destination unspecified. Risque : Trade can fail and cause raids; volcanic routes and tribal instability.. [SB p. 190](../Sources/sb.md).
- **Darkall → Storm Islands** [A], sea_unmapped : resources, military_supplies. Darkall west unmapped; no mainland metric endpoint or distance assigned. Risque : Kemet military network, no free trade to hostile Tanarean ports.. [SB p. 168, 208](../Sources/sb.md).
- **Yama → Freelands** [A], penumbral_secret_route : high_value_contraband. Third Eye two rifts route takes SIX HOURS source; endpoints/capacity not public. Risque : Bulk caravans attract creatures; exclude from ordinary baseline grain supply.. [SB p. 254](../Sources/sb.md).
- **Capital_and_Heroes_Rise_portal_network → unspecified_portal_destinations** [A_exists_D_edges], portal : small_high_value, emergency_supplies_if_capacity_P. Portals in Capital and Resistance Heroes Rise expanded. Individual pair edges and tonnes/use unknown. Risque : Each use consumes bauronite; 3 large tameranium stones construction; no free unlimited bulk freight.. [SB p. 254](../Sources/sb.md).

A = lien/produit explicitement décrit ; D = corridor ou fournisseur déduit. Une liaison positive n’établit aucune quantité. Les flux peuvent être orientés, retours différents ou interdits par changement politique. Un port non nommé reste nœud logistique hypothétique, pas nouvelle cité canonique.

## Terrain et filières par région

### Central Empire

Temperate grasslands and fertile river valleys, wooded Bak, salt marsh O’Myre, mountainous north. High potential on plains/river farms; separate settlement/cultivation from protected Bak and sacred core; wetlands not automatic fields. Commerce : Wheat,barley,meat; export details bilateral mostly unspecified. Goulots : Capital≥680k food basin must include Neckoffoods + hinterland + bay imports; bridges/gates/docks and storage needed. [SB p. 90, 93, 98, 99](../Sources/sb.md).

### Freelands

Cragplateaus divides western Storm Sea ports and eastern Central Sea; northern moors/wetlands and south forests. Valley/settled frontier patches medium-high; wetlands/mountains/Shortfall forest not wholesale cropland. Commerce : Iron,copper,tin,timber,monster parts; livestock/leather→Stravian attested; luxury imported. Goulots : Fisherman Wharf western seafood; Goldraft principal merchant access east, plague threatens provisioning; pass transfer between seas. [SB p. 104, 108, 110, 113](../Sources/sb.md).

### Ben’net

Glaciers/high icy mountains; southern tundra/valleys, access Septentrional Passing. Very low arable; pastoral range seasonally usable; tubers pocket fields. Glacier area contributes no cultivated hectares. Commerce : Wool/textiles/distilled drinks exports; oil,salt,spices,tools,ceramics imports local villages. Goulots : Large caravans stop Begraense; small caravans and aerial mounts onward; severe seasonal closures. [SB p. 120, 121, 123, 124](../Sources/sb.md).

### Kolbjörn

Northern tundra/fjords/pines; Maed separates south settlement from giant lands, extensive coast. Low-medium cropland in southern valleys; pasture/fishing/hunting large roles; giant territories and sacred islands not freely available. Commerce : Drakkars→Republic/Kepesh; leather/livestock→Stravian; furs/herbs; timber export transport challenge unresolved. Goulots : Sea wars, icy seasons, Hammer Passing; heavy logs best route requires water validation not free continental carriage. [SB p. 128, 130, 133, 135](../Sources/sb.md).

### Mage Tower

Northern ice, southern lakes/rivers connected toward Central Sea; navigable rivers explicitly stated regionally SB15. Valleys/pockets usable medium; wetlands and mountains excluded; water access not proof every colored river navigable. Commerce : Magic/potions/scrolls/teaching; fresh fish,paper; enchanted crystals→shipyards. Goulots : Portage/locks/draft to define; elementals and air transport localized with unknown tonnes/day. [SB p. 15, 138, 142](../Sources/sb.md).

### Seashores

Archipelago Central Sea, mountainous wooded islands, waterfalls/reefs/coves. Limited island plots, marine food strong; no continental agricultural area from sea polygons. Commerce : Fish,pearls,ships,black market; ship material supply Sindile/MageTower/Imperial/dwarven mines explicit. Goulots : Ship routes must follow water and landings; pirates/tribute/sea monsters and whirling hazards. [SB p. 146, 148, 150](../Sources/sb.md).

### Sindile

Forested southeast, outskirts/deep woods, lakes and faerie ecology. Cultivated woodland/gathering/gardens rather than fields by arbitrary clearing; no forced surplus staple export. Commerce : Self-sufficient; honey,herbs,magic bows,breithwood,Estelindea; metals and rare minerals needed. Goulots : Forestry permissions and ecological constraints; Mystical barrier west/northwest means bypass or expensive special transit. [SB p. 152, 153, 157](../Sources/sb.md).

### Stravian

Cold northern mountains; fertile southern valleys/rivers/farms, underground dwarf cities. Southern farmland high potential with halfling aid; northern mines not arable. Commerce : Food exported many regions; ores global; imports livestock/leather from Kolbjörn/Freelands. Goulots : Mirare→Stonelair StoneDisks key; surface bandits, imperial sabotage; underground network not unlimited or continuous mapped. [SB p. 14, 160, 162, 254](../Sources/sb.md).

### Storm Islands

Western islands frozen from former tropical terrain by Bás magic; coastal ice barriers. Limited ice-adapted tubers/cereals and fishing; undead labor not climate cancellation. Commerce : Near self-sufficient, resources Darkall, raids/tameranium. Goulots : No ordinary hostile trade; sea ice manipulable to block ships, Kemet military priority. [SB p. 17, 168, 170](../Sources/sb.md).

### Taii’maku

Ubel deserts, volcanoes/lava/firepits; moving Illus along southern arid terrain. Very low arable outside irrigated/project fields; constructs do not make lava fertile. Commerce : Compasses/clocks/precision/glass/engineering exported; bauronite and metals required. Goulots : Reactor logistics/bauronite barrel cushioning; train capacity exists but routes/mobile hubs and throughput unspecified. [SB p. 17, 174, 176, 253](../Sources/sb.md).

### Kepesh

Deserts/scrub; northern milder interface Freelands, west StormSea coast and NE CentralSea interface. Low naturally cultivable; irrigation/magic water needed; oasis moving every3 dawns cannot fixed unrestricted depot. Commerce : Spices,gold/iron/bauronite/gems,jewelry,horses/camels; fruit/legume imports explicit; coastal catch local. Goulots : Water bottleneck, Kemet naval raids, desert nomads; Pakaitos inland road transfer, not seaport invented. [SB p. 182, 185, 186](../Sources/sb.md).

### Tsvetan

Volcanic rough terrain, few wood/metal resources, coastal western towns around hot terrain. Very low cropland in harsh core; select valleys/river pockets P, hunting/livestock not free calorie abundance. Commerce : Obsidian,sulfur,platinum/hides; demands wood/metal, sometimes raids when trade fails. Goulots : Unstable clan relations, hot passes; route away from toxic Mystical. [SB p. 190, 192, 194](../Sources/sb.md).

### Yama

Humid forests/valleys in east, mountains, rivers/lakes and rice plains. High rice potential in cultivated valleys, woodland tea/silkworms noncaloric area separated; realm near self-sufficient. Commerce : Rice,silk,steel,tea exports; seeks tameranium elsewhere despite own deposits. Goulots : North route to Empire, river shops do not prove all rivers navigable; export permits/military escort cultural. [SB p. 198, 200, 201](../Sources/sb.md).

### Undertanares

Underground chain halls,caves,magma,fish lakes,fungi. No sunlight arable area; fungi/aquatic production separate, not millions hectares surface crop by map. Commerce : Dwarven ores, underground produce/trade plausible local not measured. Goulots : StoneDisk chain partial known, chasms and tribes block; no straight continent-wide underground highway. [SB p. 206, 207, 254](../Sources/sb.md).

### Darkall

Separate unmapped continent to west, forests/hills/ruins/demonic wasteland. No VTT polygon/scale transfer; productive areas unspecified, wars constrain. Commerce : Limited resources→Storm Islands explicit. Goulots : Intercontinental distance/shore unknown; exact shipping days cannot be measured this VTT. [SB p. 208, 209](../Sources/sb.md).

### Mystical

Necrotic purple wasteland between Empire,Yama,Sindile,Tsvetan,Seashores. Ordinary staple field baseline0; no resident-living crop basin magically restored without scenario. Commerce : Ruins/artifacts and secret transport, not net cereal exporter. Goulots : Toxic/necrotic land; bypass ordinary caravans, secretroads rumors not ordinary corridor. [SB p. 210, 211](../Sources/sb.md).

## Capital : hinterland, quais et marchés

Map - Capital.jpg observée : Tourmaline Bay au nord-ouest, Docks District et Warehouses of Orin au bord de l’eau, Rubicund River au nord, Oldtown scierie/abattoir/forge, Martpart marché municipal, Neckoffoods cultures/farmers market au sud-est. SB99 affirme que Neckoffoods fournit les marchés de la capitale. Cette relation soutient le premier bassin nourricier ; elle ne prouve pas que ce seul quartier nourrit 680 000 habitants. Routes/portes et ponts distribuent hinterland et quais aux marchés et autres quartiers. Lecture de baie/quais soutient accès bateau local ; tirant d’eau, accès exact baie→CentralSea, fleuve navigable et capacité annuelle non publiés. [Plan primaire](../Sources/cartes.md#carte-capital), [SB p. 98–99](../Sources/sb.md).

Le plan Capital est une illustration oblique : aucune barre physique trouvée sur cette vue, ne pas mesurer hectares Neckoffoods ou mètres de quais depuis leurs pixels. La géographie mondiale situe Capital sur une baie ; les coordonnées graphiques du nouveau plan ne sont pas échelle jouable. Garder personnes/emplois/résidence, marchés de consommation et lieux de production distincts.

## Temps, capacités et bilan annuel

**Sources quantitatives utilisables** : SB253 fournit vitesses normales/rapides et capacité en livres : carriage deux chevaux 1000 lb ; quatre chevaux 2000 lb ; magical carriage 6/8 miles/h et 1200 lb ; camel 5/6,5 miles/h et 480 lb ; magic train 13 miles/h rapide et 10000+ lb. SB254 StoneDisks jusqu’à 50 personnes, sans charge massique alimentaire donnée. Aucun débit tonnes/jour ne découle d’une capacité seule. **Calendrier 360 jours/an**, douze mois de trente jours (SB255).

**Scénarios P à tester**, pas vitesses mesurées historiques : caravanes chargées 15–30 miles/jour en voie ordinaire, 5–15 en cols/hiver ; navires côtiers 40–100 miles/jour selon météo ; manutention 0,5–2 jours par terminal. Ne pas multiplier 6 miles/h cheval par 24 heures pour une caravane. Le fret utile retranche passagers, équipage, équipement, fourrage/eau ; le train n’existe pas gratuitement sur tout continent.

Calcul corridor : jours rotation = 2×distance-route/vitesse + manutention + attente ; arrivées/jour = nombre véhicules/jours rotation ; flux annuel net = charge utile×flotte×jours opérables/jours rotation×(1−pertes). Taxe/escorte modifient coût et temps ; flotte affectée ne se compte pas simultanément dans deux lignes. Les deux rives des Cragplateaus ne se relient jamais par une ligne de mer à travers terre.

Privilégier grains/légumineuses secs, fromage, viande/poisson conservés et denrées de valeur pour transports longs. Fruits/légumes frais et lait demandent proximité, calendrier ou conservation magique explicitement financée. Les ressources demandées n’établissent pas automatiquement un déficit calorique ; alcool, thé/soie, minerai et montures ne nourrissent pas leurs producteurs.

**Transport magique** : portails consomment bauronite par usage, endpoint/capacité inconnus ; StoneDisks utiles entre Mirare/Stonelair mais tunnels pas tous cartographiés ; route Penumbrale Yama–Freelands SIX HEURES est clandestine Third Eye et dangereuse pour grosses caravanes ; aucun approvisionnement national gratuit implicite. [SB253–254](../Sources/sb.md).

## Décisions nécessaires pour la simulation

- Mesurer vraie longueur des routes/cabotages sur VTT par polylignes suivant routes et eau ; chord n’est qu’une borne. Pas d’arête maritime coupant terre, ni capacité illimitée d’un col.
- Définir terres exploitables et hectares réellement cultivés par bassin ; conserver protégés Bak, Sindile, terres géantes fermées et zone Mystical necrotique.
- Identifier flotte, opérabilité saisonnière, charge nette, stockage/semences/pertes, permis et escorte ; effets frontières/arènes/conflict ne deviennent pas embargo total inventé.
- Définir rendements naturels puis capacités magiques locales séparées ; population source et nobles/peuple ne changent pas silencieusement quand une filière manque de nourriture.
- Faire bilan demande alimentation humaine/espèces particulières + garnisons/visiteurs/animaux ; production/calories, transferts stock et consommation 360 jours. Surface immense peu peuplée ne suffit pas : distance et main-d’œuvre limitent collecte.

## Scénario chiffré exploitable pour le rédacteur

Les valeurs de cette section **définissent un scénario P** ; elles ne deviennent ni distance publiée ni rendement historique établi. Les productions disponibles, calories réelles, coûts et capacité des fournisseurs doivent encore être rapprochés de ces plafonds. Les chiffres offrent un premier ledger et ne disent pas que les villes consomment exactement 500 tonnes de matière quelconque.

### Huit métriques de corridors

- Imperial Capital → Northcross : **251.2 miles P**, plage [222.2, 309.1] ; VTT scaled endpoint chord multiplied by explicit scenario curvature factor; route identity observed on VTT, full path not metrically surveyed

- Northcross → Hajal : **295.5 miles P**, plage [253.3, 380.0] ; VTT scaled endpoint chord multiplied by explicit scenario curvature factor; route identity observed on VTT, full path not metrically surveyed

- Hajal → Begraense : **375.9 miles P**, plage [300.7, 501.2] ; VTT scaled endpoint chord multiplied by explicit scenario curvature factor; route identity observed on VTT, full path not metrically surveyed

- Mirare → Stonelair : **529.9 miles P**, plage [454.2, 681.3] ; VTT scaled endpoint chord multiplied by explicit scenario curvature factor; route identity observed on VTT, full path not metrically surveyed

- Fisherman’s Wharf → Goldraft : **1088.8 miles P**, plage [871.1, 1379.2] ; VTT scaled endpoint chord multiplied by explicit scenario curvature factor; route identity observed on VTT, full path not metrically surveyed

- Northcross → Mesoriver : **637.3 miles P**, plage [546.2, 819.4] ; VTT scaled endpoint chord multiplied by explicit scenario curvature factor; route identity observed on VTT, full path not metrically surveyed

- Northharbor → Fisherman’s Wharf : **1027.6 miles P**, plage [924.8, 1233.1] ; Manual coastal polyline following open western water outside peninsula; archipelago channel/tide additional scenario uncertainty

- Goldraft → Bluhaven west-coast landing : **318.9 miles P**, plage [287.0, 402.7] ; Manual sea polyline through Central Sea south of Left Island, avoiding the Bluhaven peninsula interior. Landing name P, not extra canonical settlement. Last-mile city transfer P 30–70 miles.


### Enveloppe 500 tonnes alimentaires livrées par jour à chaque grande ville

Capital P : 250 t/j champs périphériques/Neckoffoods et marchés locaux, 100 t/j arrière-pays via routes/portes, 150 t/j production côtière impériale par vrais quais de Tourmaline Bay. Le fleuve ne reçoit aucun débit cargo inventé ; canal/barge reste capacité additionnelle seulement si navigation autorisée. Fisherman’s Wharf P : 300 t/j exploitations proches, 100 t/j pêche/côte proche, 100 t/j complément conservé de Kolbjörn par mer. Cela atteint capacité500t/j chacune ; le calcul de production du rédacteur décide les flux réellement employés.

- **Imperial Capital / Neckoffoods/peripheral farms→Farmers Market and gates** : cible 250 t/j ; charge alimentaire nette 0.75 t/voyage ; distance 15 miles P ; rotation 3.5 jours ; **1203 véhicules/navires dédiés** pour couvrir 360 jours avec 360 jours opérables ; stock minimum hors saison 0 t, pertes 3 %.

- **Imperial Capital / Wider permitted hinterland→Imperial roads/gates** : cible 100 t/j ; charge alimentaire nette 0.75 t/voyage ; distance 50 miles P ; rotation 7.0 jours ; **1073 véhicules/navires dédiés** pour couvrir 360 jours avec 330 jours opérables ; stock minimum hors saison 3000 t, pertes 5 %.

- **Imperial Capital / Southern Imperial coastal production→Tourmaline Bay docks/warehouses** : cible 150 t/j ; charge alimentaire nette 50 t/voyage ; distance 100 miles P ; rotation 5.33 jours ; **20 véhicules/navires dédiés** pour couvrir 360 jours avec 330 jours opérables ; stock minimum hors saison 4500 t, pertes 7 %.

- **Fisherman’s Wharf / Settled local farms→Hope Square/open markets** : cible 300 t/j ; charge alimentaire nette 0.75 t/voyage ; distance 20 miles P ; rotation 4.0 jours ; **1667 véhicules/navires dédiés** pour couvrir 360 jours avec 360 jours opérables ; stock minimum hors saison 0 t, pertes 4 %.

- **Fisherman’s Wharf / Local fishing/near coast→Fisherman port** : cible 100 t/j ; charge alimentaire nette 15 t/voyage ; distance 30 miles P ; rotation 3.5 jours ; **28 véhicules/navires dédiés** pour couvrir 360 jours avec 330 jours opérables ; stock minimum hors saison 3000 t, pertes 5 %.

- **Fisherman’s Wharf / Kolbjörn Northharbor→western port preserved marine/food supplement** : cible 100 t/j ; charge alimentaire nette 80 t/voyage ; distance 1027.6 miles P ; rotation 36.25 jours ; **56 véhicules/navires dédiés** pour couvrir 360 jours avec 330 jours opérables ; stock minimum hors saison 3000 t, pertes 10 %.

- **Kepesh / Northern Freelands farming basin→northern land entry→Pakaitos market** : cible 100 t/j ; charge alimentaire nette 1.5 t/voyage ; distance 180 miles P ; rotation 26.0 jours ; **2312 véhicules/navires dédiés** pour couvrir 360 jours avec 300 jours opérables ; stock minimum hors saison 6000 t, pertes 10 %.

- **Taii’maku Illus / Neighboring food-producing northern fringe→Illus authorized depots** : cible 80 t/j ; charge alimentaire nette 80 t/voyage ; distance 180 miles P ; rotation 6.5 jours ; **8 véhicules/navires dédiés** pour couvrir 360 jours avec 330 jours opérables ; stock minimum hors saison 2400 t, pertes 5 %.


Le débit maritime50–80t/navire est P, **pas** capacité canonique de drakkar. La charge chariot0,75t/aliments est sous les2000lb≈0,907t brutes de la voiture4chevaux SB253 ; fourrage, équipage et outils devront rentrer dans la marge ou un train de soutien. Les500t/j ne sont pas transportables magiquement à coût nul. Le train80t P est une rame multiunités, pas un seul véhicule SB253(10000+lb). Sa ligne/fréquence/énergie et autorisation doivent être financées ; si absence d’accord, capacité0 et remplacer par terrestre/coastal avec déficit expliqué. Aucun débit portail ajouté baseline.

Les trajets de proximité15/20/50/100miles sont **distances de bassins logistiques P**, pas positions de villages inventées. Kepesh180miles et Taii180miles sont segments d’accès P depuis franges nourricières, pas distances mesurées entre capitales ; portée locale doit être ajustée au maillage réel. Le cabotage Northharbor–FW et CentralSea dispose de polylignes VTT ; aucune liaison mer n’est employée pour traverser Cragplateaus.

### Minimum de surface de cultures pour une enveloppe de500t/j équivalent sec

360jours×500=180000tonnes nettes annuelles. Sous **rendement net P0,5–1,5t/ha/an**, min120000–360000ha cultivés (1200–3600km²), pour chacune des deux grandes villes si tout venait de cultures. Avec part cultivée P25% du bassin, territoire desservant4800–14400km², rayon circulaire plat39–68km : **calcul demande/rendement, pas surface lue sur Neckoffoods**. Ajouter pâtures/fourrage/rotation, contraintes d’accès/protection et substituer régime réel poisson/viande/légumes ; poisson et magie ne donnent pas champs gratuits. La carte paraît offrir bassins terrestres vastes, mais le relief et main-d’œuvre déterminent leur exploitabilité.

Sur le recadrage bas-droit de Map-Capital réellement lu : Grain Road, The Crops et The Northwoods apparaissent ; cela confirme champs périphériques et frontière forestière, **pas** leur nombre d’hectares ni périmètre légal municipal. Il n’y a aucune barre d’échelle visible sur ce plan oblique.

Kolbjörn Capital, complément interne P : 25t/j de vallées méridionales autorisées, charge0,75t, parcours25miles à15miles/j, rotation5,33j, pertes5%,300jours opérables, pic30t/j et225chariots dédiés, réserve1500t pour60jours nonopérables. Ce flux est transfert ville/campagne, pas production régionale nouvelle. Grands symbolesVTT schématiques : position du centre de ville ne donne pas quai exact ; les polylignes de mer aboutissent à un débarquementP identifié et le dernier segment terrestre reste distinct.
