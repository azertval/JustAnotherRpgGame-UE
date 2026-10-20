+++
id = "LOT-1027"
titre = "Le générateur : garde-robe et adaptation aux corps"
version = "0.0.3"
filiere = "assets"
statut = "a-faire"
taille = "L"
resume = "Une garde-robe réutilisable suit les réglages corporels et distingue métiers, cultures et affiliations sans retouche par personnage."
prerequis = ["LOT-1026"]
livrables = ["Un catalogue texte des vêtements et accessoires : emplacements, familles compatibles, superpositions, masques du corps et exclusions.", "Un kit initial de coupes réutilisables couvrant civil, artisan et combattant : tunique, bas, robe ou manteau, tablier, chaussures, gants et protection rigide.", "Les déformations de vêtements correspondant aux paramètres corporels, les matériaux paramétrés et les variantes culturelles/professionnelles nécessaires à la démo.", "Le protocole et les mesures d'ajout d'un nouveau vêtement, avec sources, tailles préparées, corrections initiales et contrôle animé."]
criteres = ["Les vêtements suivent les extrêmes combinés autorisés ; aucune intersection ou déformation refusée dans les poses et animations de contrôle.", "Les incompatibilités anatomiques et superpositions sont traitées explicitement ; aucun gant humain à cinq doigts ni pantalon bipède n'est imposé aux anatomies incompatibles.", "Couleur, matière, motif et usure changent sans dupliquer les géométries ; modifier une coupe utilise la pièce appropriée.", "Après préparation d'une pièce pour une famille, plusieurs personnages distincts l'utilisent sans correction manuelle individuelle ; le temps d'intégration est consigné."]
+++

## Pourquoi

La garde-robe constitue un investissement durable. Elle dépend de plages de morphologie
validées ; les 267 branches professionnelles ne justifient pas 267 modèles de tenue complets.

## Périmètre

Dedans : kit de départ, adaptation, masquage, couleurs/matières et règles de compatibilité.
Dehors : totalité des tenues du monde, production de chaque PNJ et simulation de tissu
systématique. La simulation ne remplace pas l'ajustement initial du vêtement.

## Conception

Séparer coupe 3D, matière, palette, usure, insigne et outil. Métiers, milieu social, culture
et affiliation sont des axes distincts ; un métier n'impose pas une espèce.
Les coupes de base servent à plusieurs professions avec leurs accessoires.

Références de conception : Hajal (Sourcebook p. 93, vêtements et insignes d'employeur),
Mage Tower (p. 139, chapeaux et runes), Sindile (p. 152, formes végétales) ;
`Documentation/Metiers/choix-et-sources.md` distingue attesté, déduit et proposé.
Conserver ces distinctions dans le catalogue, sans recopier d'image du livre dans les assets.

Adapter par morphs correspondants, transfert contrôlé ou tailles préparées selon le choix
du LOT-1024. Masquer les parties couvertes et traiter cape/cheveux/casque, queue/ceinture,
gants/doigts, épaulières et manteau en mouvement. Les zones rigides gardent leur volume.
Tester marche, course, assise et attaque avec les paramètres extrêmes combinés.
Les cheveux en meshes/cards et les grooms sont évalués selon le budget et les limites du
backend ; un statut expérimental ne doit pas devenir une dépendance implicite.

Produire captures à midi et à 22 h, vues rapprochées et cadrages du joueur, ainsi que
mesures de préparation initiale et d'ajout d'une variante. Tous les matériaux, masques et
formes nécessaires à la reconstruction font partie des sources.

## Risques et questions ouvertes

La déformation automatique n'est pas un ajustement universel. Si une coupe échoue, corriger
sa source partagée ou réduire explicitement sa plage admise ; ne pas réparer chaque PNJ.
Les tenues de portée culturelle large attendent leur lot de contenu après validation du kit.
