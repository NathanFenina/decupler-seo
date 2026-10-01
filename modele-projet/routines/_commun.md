# Règles communes aux routines de {{NOM}}

Chaque routine lit ce fichier, puis le sien. Personne ne lit pendant une
routine : elle ne pose jamais de question et ne reste jamais en attente.

- **Partir de main à jour** : `git fetch origin main && git checkout -B claude/<mode>-<AAAA-MM-JJ> origin/main`.
- **Lire** `CLAUDE.md` et `memoire/decisions.md` : une proposition refusée ne revient pas.
- **Page de suivi** (skill `seo-pilotage`) : son adresse est `pilotage.tableau_de_bord`
  dans `decupler-seo.config.yml`, l'identifiant du projet `pilotage.projet_id`.
  Lire la page (outil Artifact, action read) et l'enregistrer dans
  `donnees/tableau-de-bord.html` ; republier avec l'outil Artifact (publish,
  `url` = cette adresse, `file_path` = ce fichier, sans capabilities). En cas
  de conflit : relire, refaire la modification, republier une fois.
- **Fichiers de travail** : `donnees/tableau-de-bord.html`, `donnees/pilotage.json`,
  `donnees/actions-*.json` sont ignorés par git. Ne pas les commiter, ne pas les supprimer.
- **Journal de run** `rapports/runs/<AAAA-MM-JJ>-<mode>.md` écrit dès le démarrage,
  complété à la fin : c'est la preuve que la routine a travaillé.
- **Étape refusée** par les permissions de la session (fusion, suppression,
  push) : ne pas insister. Laisser la PR ouverte avec « à fusionner par un
  humain » dans sa description et dans le journal de run, l'ajouter à la page
  de suivi (`pilotage.py ajouter --titre "Fusionner la PR <n°>" --statut validee --lien <PR>`),
  republier, terminer.
