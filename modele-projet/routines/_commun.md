# Règles communes aux routines de {{NOM}}

Chaque routine lit ce fichier, puis le sien. Personne ne lit pendant une
routine : elle ne pose jamais de question et ne reste jamais en attente.

- **Partir de main à jour** : `git fetch origin main && git checkout -B claude/<mode>-<AAAA-MM-JJ> origin/main`
  (`<mode>` : `hebdo`, ou `veille`, `optimisation`, `contenu`, `rapport` pour un gros site).
- **Lire** `CLAUDE.md` et `memoire/decisions.md` : une proposition refusée ne revient pas.
- **Page de suivi** (skill `seo-pilotage`) : son adresse est `pilotage.tableau_de_bord`
  dans `decupler-seo.config.yml`, l'identifiant du projet `pilotage.projet_id`.
  Lire la page (outil Artifact, action read) et l'enregistrer dans
  `donnees/tableau-de-bord.html` ; republier avec l'outil Artifact (publish,
  `url` = cette adresse, `file_path` = ce fichier, sans capabilities). En cas
  de conflit : relire, refaire la modification, republier une fois.
- **Fichiers de travail** : `donnees/tableau-de-bord.html`, `donnees/pilotage.json`,
  `donnees/actions-*.json`, `donnees/semaine.json` sont ignorés par git : ne pas
  les commiter, ne pas les supprimer. La copie de sûreté de la roadmap, elle, est
  commitée : `journal/pilotage.json` (`pilotage.py sauvegarder`, après chaque republication).
- **Journal de run** `rapports/runs/<AAAA-MM-JJ>-<mode>.md` écrit dès le démarrage,
  complété à la fin : c'est la preuve que la routine a travaillé.
- **Jamais de fusion par la routine elle-même** : PR ouverte, action `bloquee`
  « relire et fusionner » sur la page de suivi. Une routine qui demande « fusionner
  ou non ? » reste bloquée jusqu'à la réponse : c'est arrivé le 02/10/2026.
- **Étape refusée** par les permissions de la session (suppression, push) : ne pas insister. Laisser la PR ouverte avec « à fusionner par un
  humain » dans sa description et dans le journal de run, l'ajouter à la page
  de suivi (`pilotage.py ajouter --titre "Fusionner la PR <n°>" --statut validee --lien <PR>`),
  republier, terminer.
