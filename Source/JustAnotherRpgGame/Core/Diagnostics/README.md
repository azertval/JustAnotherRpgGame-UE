# Core/Diagnostics/

Outils transverses de diagnostic : **journalisation** et **assertions**.

## Journalisation
- `LogLevel` — niveaux `Trace` / `Info` / `Warning` / `Error`.
- `Logger` — filtre par niveau minimal et diffuse vers des sinks ; `defaultLogger()` est l'instance globale.
- `ILogSink` — destination ; implémentations : `ConsoleLogSink` (console + débogueur), `MemoryLogSink` (tests, export manuel via `hmi::OptionsModel::saveLogs`), `FileLogSink` (fichier, flush immédiat à chaque message — survit à un arrêt brutal/crash, contrairement aux deux autres).
- `Log.h` — macros génériques capturant **catégorie**, niveau, fichier/ligne et horodatage.
- `LogFormat.h` (`formatLogLine`) — compose une ligne de log (horodatage, niveau, catégorie, fichier/ligne, message), fonction pure et testable.
- `LogLevelParse.h` (`parseLogLevel`) — convertit une chaîne (« trace », « info », « warning », « error ») en `LogLevel`, pour configurer le niveau minimal au lancement sans recompiler.

### Catégories (« sous-dossiers » de log)
Chaque module possède son **en-tête de catégorie** définissant des macros courtes, par exemple `HMI/HmiLog.h` :
```cpp
#include "HMI/HmiLog.h"

HMI_LOG_INFO("Niveau charge");
HMI_LOG_ERROR(std::string("Fichier introuvable : ") + chemin);
```
Modèle à dupliquer par module (`Core`, `Ecs`, `Graphics`…). En direct, sans en-tête dédié :
```cpp
#include "Core/Diagnostics/Log.h"
JADG_LOG_INFO("HMI", "message");
```
Sortie : `[HH:MM:SS][INFO][HMI][fichier:ligne] message` (le chemin `__FILE__` est réduit au nom de fichier).

Configuration (une fois, au démarrage) :
```cpp
core::defaultLogger().addSink(std::make_unique<core::ConsoleLogSink>());
core::defaultLogger().setMinimumLevel(core::LogLevel::Info);
```

## Assertions
- `JADG_ASSERT(condition, message)` — vérifie une précondition/invariant. **Active en Debug**, **sans effet en Release** (condition non évaluée).
- Une assertion signale un **bug de programmation**, jamais une erreur d'exécution normale (cf. conventions §9).
- Le gestionnaire d'échec est surchargeable via `setAssertionHandler(...)` (les tests l'exploitent pour capturer l'échec sans abandonner).

```cpp
#include "Core/Diagnostics/Assert.h"

JADG_ASSERT(index < taille, "index hors bornes");
```

Réf. : guide de conventions §10 ; [guide de la journalisation](../../../Documentation/Guide/guide-journalisation.md).
