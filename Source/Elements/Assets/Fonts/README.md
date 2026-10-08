# Elements/Assets/Fonts/

Polices TTF des écrans du jeu et leurs licences, déployées à côté de l'exécutable. Aucune police
n'est dessinée dans la scène rendue : tout le texte passe par Qt Quick. L'éditeur, outil interne,
écrit avec la police du système (style Fusion) depuis le `LOT-EDITOR-01`, qui a retiré *Inter*, sa
police embarquée.

## Règles communes

**Licences.** Toutes les polices de ce dossier sont sous SIL Open Font License 1.1, donc
redistribuables avec le jeu ; chaque `*-LICENSE.txt` accompagne sa famille et doit le rester.

**Accents.** Chaque police couvre `E A E C U OE` accentues et la ponctuation employee par les
catalogues de traduction : une police qui s'arrete a l'ASCII rend le francais illisible sans que
rien ne le signale.

## Polices des ecrans du jeu, charte v2 (`LOT-87`, `T2.3`)

Enregistrees par `registerIdentityFonts()` (`App/Game/Main.cpp`) : ce sont les polices des ecrans
du jeu. `Tokens.qml` designe les familles par leur nom
(`bodyFamily`, `titleFamily`, `loreFamily`) : Design Studio les voit via `FontFiles` du
`.qmlproject`, qui pointe sur ce dossier entier — aucune liste de fichiers a tenir a jour ailleurs.

| Fichier | Famille rapportee a Qt | Sert a |
|---|---|---|
| `Cinzel-Regular.ttf` | `Cinzel`, style `Regular` | Titres, plaques et bandeaux (`titleFamily`). |
| `Cinzel-SemiBold.ttf` | `Cinzel SemiBold`, style `Regular` | Graisse intermediaire ; famille legacy distincte faute d'entree `STAT` a 600 dans la police source, nom typographique prefere `Cinzel`/`SemiBold` conserve pour les moteurs qui le lisent. |
| `Cinzel-Bold.ttf` | `Cinzel`, style `Bold` | Emphase de titre. |
| `IMFellEnglish-Regular.ttf` | `IM Fell English`, style `Regular` | Corps de texte (`bodyFamily`) et citations (`loreFamily`). |
| `IMFellEnglish-Italic.ttf` | `IM Fell English`, style `Italic` | Citations et texte d'ambiance (`font.italic: true` sur `loreFamily`). |
| `PinyonScript-Regular.ttf` | `Pinyon Script`, style `Regular` | Signature a la plume de la fiche de personnage (`signatureFamily`). |

**Provenance.** Extraites de [google/fonts](https://github.com/google/fonts) (`ofl/cinzel`,
`ofl/imfellenglish`, `ofl/pinyonscript`), SIL Open Font License 1.1 — `Cinzel-LICENSE.txt`,
`IMFellEnglish-LICENSE.txt` et `PinyonScript-LICENSE.txt` accompagnent leurs familles. `Cinzel` n'existe en amont qu'en police
variable (axe `wght`, 400 a 900) : les trois graisses deposees ici sont des instances statiques
figees par `fonttools varLib.instancer`, sans modification de dessin — seul le nom de la graisse
600 a ete pose a la main, faute d'instance nommee correspondante en amont. Aucun nom n'est reserve
par les deux licences (pas de `Reserved Font Name` apres la mention de copyright) : cette
derivation reste couverte par l'OFL.

**Repli.** Un fichier absent ou refuse par Qt journalise un avertissement (`EX-NFR-040`) et Qt
Quick retombe sur la famille demandee telle quelle, resolue par le systeme.
