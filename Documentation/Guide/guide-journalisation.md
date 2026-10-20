# Journalisation et assertions

Le diagnostic des règles vit dans `Source/JustAnotherRpgGame/Core/Diagnostics`, avec
un en-tête de macros par catégorie (`Core/CoreLog.h`, `Core/Ecs/EcsLog.h`,
`Core/Levels/LevelsLog.h`). Dans le jeu, `Bridge/JadgLog.cpp` relaie ces messages
vers le journal d’Unreal, dans la catégorie `LogJadg`.

## Pourquoi journaliser dans un jeu vidéo

Un jeu compilé en **Release**, lancé par un joueur, n'a **pas** de console attachée ni de
débogueur : impossible d'y poser un point d'arrêt ou d'inspecter une variable en direct. Si un
comportement anormal survient — un niveau ne se charge pas, une ressource graphique échoue à se
créer — la seule trace disponible après coup est ce que le programme a **explicitement enregistré**
pendant son exécution. La **journalisation** consiste précisément à écrire, au fil de l'exécution,
des messages textuels horodatés décrivant les événements significatifs (démarrage, chargement d'un
niveau, erreur récupérable…), pour reconstituer après coup ce qui s'est passé sans avoir dû le
prévoir en amont dans un débogueur.

C'est un outil **différent** d'une assertion (voir la dernière section) : le journal enregistre des
faits pour un usage **ultérieur** et humain (diagnostic après coup), sans jamais interrompre le
programme ; une assertion vérifie un invariant **immédiatement** et signale un **bug** s'il est
violé.

## Les niveaux de gravité : `core::LogLevel`

Tous les messages ne se valent pas : un message peut être un détail de mise au point sans intérêt
en usage normal, ou au contraire signaler une erreur qu'il faut voir absolument. `core::LogLevel`
distingue quatre niveaux, en **gravité croissante** :

| Niveau | Usage |
|--------|-------|
| `Trace` | Détails fins de débogage — verbeux, utile en cours de développement d'une fonctionnalité précise. |
| `Info` | Fonctionnement normal — démarrage, niveau chargé, ressource créée. |
| `Warning` | Anomalie **non bloquante** — le jeu continue, mais quelque chose méritait attention. |
| `Error` | Erreur nécessitant attention — un échec qui affecte le déroulement. |

Le fait que ces niveaux soient **ordonnés** permet de **filtrer** : en développement, on veut
généralement tout voir (`Trace` et au-dessus) ; pour une session de test plus ciblée, ne garder que
`Warning` et `Error` évite de noyer les messages importants dans le bruit des détails `Trace`/`Info`.
C'est le rôle du `Logger`, ci-dessous.

## `core::Logger` : filtrer puis diffuser

`core::Logger` a exactement deux responsabilités, séparées volontairement de toute écriture réelle
sur un support (fichier, console, etc.) :

- **filtrer** : `setMinimumLevel(niveau)` fixe un seuil ; un message dont le niveau est **inférieur**
  à ce seuil est ignoré avant même d'être formaté (`isEnabled(level)` permet de vérifier ce filtre
  **avant** de construire un message coûteux, voir plus bas) ;
- **diffuser** : un message qui passe le filtre est transmis à **tous** les sinks enregistrés
  (`addSink`).

Le `Logger` **ne fait aucune entrée-sortie lui-même** — il ne sait pas écrire sur un fichier, une
console, ou ailleurs. C'est une décision de conception délibérée : séparer « décider si un message
doit être vu » (le `Logger`) de « où et comment l'écrire réellement » (les sinks) permet de changer
librement les destinations sans toucher au code qui produit les messages, et de tester le filtrage
sans jamais toucher un vrai fichier ou une vraie console (voir `MemoryLogSink` plus bas).

Une instance **unique**, globale, est accessible via `core::defaultLogger()` — c'est elle que les
macros de journalisation (voir plus bas) utilisent implicitement, pour éviter d'avoir à faire
transiter une référence de `Logger` à travers tout le code applicatif.

## Les sinks : où finissent les messages

Un **sink** (« puits », au sens d'un point de destination) implémente l'interface `core::ILogSink`
— une seule méthode, `write(level, message)`. Trois implémentations existent :

- `core::ConsoleLogSink` : écrit sur la sortie standard et, sous Windows, vers le débogueur (visible
  par exemple dans la fenêtre de sortie de Visual Studio même sans console ouverte) ;
- `core::FileLogSink` : écrit chaque ligne dans un fichier sur disque (dossier parent créé au
  besoin) ;
- `core::MemoryLogSink` : ne fait **aucune** entrée-sortie — il **mémorise** les messages reçus dans
  un vecteur, consultable via `entries()`, notamment pour vérifier les messages dans les
  tests automatisés sans dépendre d'un fichier ou d'une console.

Comme le `Logger` **possède** ses sinks (`std::unique_ptr`, RAII), ajouter un nouveau type de
destination revient à écrire une nouvelle classe implémentant `ILogSink`, sans toucher au `Logger`
ni au code qui journalise.

## Les macros de journalisation, par catégorie

Écrire `core::defaultLogger().log(core::LogLevel::Info, "...")` à chaque site d'appel serait
verbeux et n'indiquerait pas d'où vient le message. `Core/Diagnostics/Log.h` définit une macro
générique, `JADG_LOG(catégorie, niveau, message)`, et ses quatre raccourcis
`JADG_LOG_TRACE/INFO/WARNING/ERROR(catégorie, message)`.

**Pourquoi une macro plutôt qu'une fonction.** Deux raisons concrètes :

- `__FILE__`/`__LINE__` (fichier et ligne source du site d'appel) ne peuvent être capturés
  automatiquement que par une macro préprocesseur — une fonction ordinaire ne verrait que le fichier
  où **elle-même** est définie, jamais celui de l'appelant ;
- la macro teste `isEnabled(level)` **avant** de construire la chaîne de message. Un appel comme
  `JADG_LOG_TRACE("Core", "Position : " + std::to_string(x) + ...)` construirait une
  concaténation de chaînes à **chaque** appel si c'était une fonction ordinaire, même quand le
  niveau `Trace` est filtré — un coût inutile, potentiellement significatif si l'appel est fréquent.
  En macro, si le niveau est désactivé, le message n'est **jamais évalué**.

### Chaque module a sa propre catégorie

Chaque catégorie possède ses raccourcis : `Core/CoreLog.h` pour `Core`,
`Core/Ecs/EcsLog.h` pour `Ecs`, `Core/Levels/LevelsLog.h` pour `Levels`.

```cpp
#include "Core/CoreLog.h"

CORE_LOG_INFO("Niveau charge");
CORE_LOG_ERROR(std::string("Fichier introuvable : ") + chemin);
```

La catégorie apparaît dans chaque ligne formatée par Core. Le pont vers Unreal
conserve le message et traduit sa gravité dans `LogJadg`.

### Une règle de performance à respecter

Le commentaire de `Core/CoreLog.h` le rappelle explicitement : ces macros sont **à réserver aux
événements de cycle de vie** (démarrage, chargement d'un niveau, création d'une ressource) — **jamais
dans un chemin exécuté à chaque frame ou à chaque pas fixe** ([Boucle de jeu et pas de temps fixe](guide-boucle.md)). Un jeu tourne à
60 pas par seconde ; journaliser à cette fréquence, même avec un niveau filtré, resterait coûteux
(construction de chaînes, appel de fonction, éventuelle écriture) et pourrait à lui seul dégrader le
*framerate* — le symptôme inverse de ce que la journalisation est censée aider à diagnostiquer.

## Le format d'une ligne : `core::formatLogLine`

`core::formatLogLine(timestamp, level, category, file, line, message)` compose une ligne de la
forme :

```
[14:32:07][INFO][HMI][main.cpp:148] Fenetre creee (1280x720)
```

Deux détails valent d'être notés :

- `fileName(path)` réduit un chemin complet (tel que fourni par `__FILE__`, qui peut être un chemin
  absolu très long selon la configuration de build) à son seul nom de fichier — la ligne complète
  resterait lisible sans encombrer chaque message du chemin entier du projet ;
- l'horodatage (`currentTimestamp()`) est calculé **séparément** puis **injecté** en paramètre de
  `formatLogLine`, plutôt que lu directement à l'intérieur de la fonction de formatage. Cela rend
  `formatLogLine` **pure** et testable : un test peut lui passer un horodatage fixe et vérifier la
  ligne produite **exactement**, sans dépendre de l'heure réelle à laquelle le test s'exécute — un
  cas particulier du principe déjà rencontré en [Boucle de jeu et pas de temps fixe](guide-boucle.md) (isoler ce qui dépend du temps
  réel derrière un paramètre injecté, pas une lecture directe de l'horloge système).

## Configurer le niveau minimal

`core::defaultLogger().setMinimumLevel(core::LogLevel::Info)` règle le seuil de Core.
`core::parseLogLevel(text)` convertit un nom de niveau en `std::optional<LogLevel>` ;
une valeur inconnue donne `std::nullopt`.

`core::ScopedLogLevel(logger, plancher)` relève temporairement ce seuil, puis le
restaure à la fin de sa portée. Il ne rend jamais plus permissif un seuil déjà
plus strict. Le `Logger` coordonne les portées qui se chevauchent.

Dans le jeu, `FJadgCoreLogBridge::Install()` ajoute le sink Unreal. Les niveaux
`Error`, `Warning`, `Info` et `Trace` deviennent respectivement `Error`, `Warning`,
`Log` et `Verbose` dans `LogJadg`. `Uninstall()` retire les sinks au démontage.
Les journaux du moteur sont dans `Saved/Logs/`.

## Assertions : `JADG_ASSERT`, un outil différent

Une **assertion** vérifie qu'une condition, censée être **toujours vraie** si le code est correct
(une précondition, un invariant), l'est effectivement à un point précis de l'exécution — sa
violation signale un **bug** dans le programme lui-même, pas un événement à consigner pour
information. C'est déjà ce que `ComponentPool`/`World` utilisent abondamment ([ECS : entités, composants, systèmes](guide-ecs.md)) :
`JADG_ASSERT(has(entity), "...")` avant d'accéder à un composant, par exemple.

Deux différences fondamentales avec la journalisation :

- **active seulement en Debug** : en Release (`NDEBUG` défini), `JADG_ASSERT(condition,
  message)` ne produit **aucune instruction** et **n'évalue même pas** `condition` — coût nul en
  production, contrairement à un message de log qui peut rester actif (filtré, mais présent) des
  deux côtés. Le raisonnement : une assertion protège le **développement** contre des bugs
  introduits par erreur ; en Release, on présuppose le code déjà correct plutôt que de payer un
  coût de vérification permanent pour des invariants qu'on a déjà validés ;
- **gestionnaire remplaçable** : `core::setAssertionHandler(handler)` permet de substituer le
  comportement par défaut (qui interromprait normalement le programme) par un gestionnaire
  personnalisé — utile en test, pour vérifier qu'une fonction **déclenche bien** une assertion sur
  une entrée invalide, sans faire planter la suite de tests elle-même. Un gestionnaire nul rend
  l'échec silencieux. Ce que la macro appelle quand la condition est fausse est
  `core::handleAssertionFailure(condition, message, fichier, ligne)` : elle invoque le
  gestionnaire courant avec le texte de la condition (`#condition`), le message, `__FILE__` et
  `__LINE__` — c'est là, et nulle part ailleurs, que le choix du gestionnaire se lit.

En résumé : **journaliser** un événement (« la carte du Colisée a été chargée ») documente un fait pour un
humain qui lira le journal plus tard ; **asserter** une condition (« cette entité doit être vivante
ici ») protège contre un bug du code, et n'a de sens qu'en développement.

## Voir aussi
- `core::Logger`, `core::LogLevel`, `core::ILogSink`, `core::ConsoleLogSink`, `core::MemoryLogSink`.
- `core::formatLogLine`, `core::parseLogLevel`, `core::defaultLogger`, `core::ScopedLogLevel`.
- `JADG_ASSERT`, `core::setAssertionHandler`, `core::handleAssertionFailure`.
- [Boucle de jeu et pas de temps fixe](guide-boucle.md) — la règle « jamais de log dans le chemin exécuté à chaque pas fixe ».
- [ECS : entités, composants, systèmes](guide-ecs.md) — usage concret des assertions pour les préconditions du `World`/`ComponentPool`.
