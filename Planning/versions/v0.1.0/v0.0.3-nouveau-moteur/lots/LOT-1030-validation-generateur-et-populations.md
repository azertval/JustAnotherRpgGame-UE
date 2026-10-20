+++
id = "LOT-1030"
titre = "Le générateur : validation en jeu et passage en production"
version = "0.0.3"
filiere = "pnj"
statut = "a-faire"
taille = "M"
resume = "Le créateur, les personnages et les créatures passent une recette commune de qualité, performances et reconstruction avant le peuplement en volume."
prerequis = ["LOT-1025", "LOT-1029"]
livrables = ["Le dossier de recette du générateur : matrice espèces/paramètres/vêtements, captures, tests empaquetés et écarts résolus.", "Les mesures groupe proche, rue et arène à densité croissante, avec niveaux de détail, animations, cheveux et tissus réellement retenus.", "La stratégie PNJ fixes / personnages équipables : préassemblage ou génération à la demande, cache et partage de ressources, avec mesures de stockage et chargement.", "Le standard final de production, le guide d'ajout d'une base et d'un vêtement, les limites connues, versions des outils et contrôles de migration."]
criteres = ["Les seuils fixés au LOT-1024 sont respectés dans le paquet final avec personnages habillés ; huit mannequins ne servent pas de preuve de capacité.", "Les changements de LOD, générations successives, équipement, sauvegarde/reprise et traversée de scène n'altèrent pas l'identité et ne créent pas de dérive mémoire.", "La chaîne est reconstruite depuis les sources conservées ; toute dépendance externe de fabrication est déclarée et absente des opérations de création en jeu.", "La démo active présente ses héros, PNJ et rencontre des fauves ; les lots de peuplement disposent d'un contrat publié et d'une densité validée par scène."]
+++

## Pourquoi

Les performances d'un seul personnage dans l'éditeur ne préjugent ni du créateur en jeu,
ni d'une foule dans la capitale. Ce lot clôt le chantier avant la recette de version LOT-1023.

## Périmètre

Dedans : validation et durcissement de la chaîne, mesures et contrat de production.
Dehors : production de toute la population, remplissage des gradins, nouveaux systèmes
d'IA ou recours imposé à Mass. Une population de test est isolée et reproductible.

## Conception

Rejouer le protocole du LOT-1024 avec les vrais assets, puis mesurer la scène active autour
de l'arène. Publier matériel, résolution, qualité, nombre visible/animé, distances caméra,
temps CPU/GPU, mémoire permanente et transitoire, chargement, changements d'équipement et
taille des ressources. Séparer le coût des personnages de celui du décor ; conserver les
objectifs globaux du projet et expliquer toute limite.

Préassembler les PNJ à tenue fixe lorsque le gain est démontré ; conserver une génération
au changement pour les personnages équipables. Ne pas cuire toutes les combinaisons :
mesurer stockage, cache et réutilisation. Le partage de sources ne signifie pas automatiquement
partage intégral des meshes et textures générés.

La recette comprend les cas difficiles, les extrêmes combinés et les changements rapides,
les créatures, les corps enfants et les morts-vivants. Livrer captures midi/22 h à la caméra
du joueur. Les tests Core portent sur contrats et migration ; les contrôles Unreal et le
paquet final portent sur rendu, animation et reconstruction.

Mettre à jour standard, guide, scripts de vérification et références de planning. Retirer
uniquement les prototypes et dépendances remplacés dont les références ont été vérifiées.
Le LOT-314 réutilise le créateur d'apparence pour son parcours de règles.

## Risques et questions ouvertes

Si une cible n'est pas tenue, corriger le lot concerné ou faire approuver un changement explicite
de portée ; ne pas déclarer livré en reportant silencieusement le défaut à la foule future.
Les outils expérimentaux ou interfaces privées retenus disposent d'un test de compatibilité
à chaque changement de version moteur.
