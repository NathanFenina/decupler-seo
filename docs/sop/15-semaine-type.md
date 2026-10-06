<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 15 · La semaine type d'un projet

**Skills** : `seo-cycle`, `seo-pilotage`, `seo-journal-mesure` · **Commande** : la routine `hebdo`, puis `/seo-maj` le lundi

**Objectif** : Que chaque projet avance chaque semaine, au même rythme, quel que soit celui qui le tient : vous, un prestataire ou la routine.

**Quand** : Toutes les semaines, sur chaque projet.

**Dis à Claude** : « Où en est le projet cette semaine : ce qui est fait, ce qui attend une décision, ce qui est bloqué ? »

## Étapes

1. **Lundi, 10 minutes (humain)** : fusionner la PR « Méthode decupler-seo <version> » si elle est là (`/seo-maj` explique ce qui change). Déposer dans `notes/` ce que le client a dit la semaine passée, avec `#a-traiter` : la routine le lira dès mercredi.
2. **Mercredi 7 h (routine `hebdo`)** : contrôle du site, chiffres, mesure à J+28, suivi de l'indexation, actions validées, notes `#a-traiter`, bilan de la semaine sur la page de suivi, PR.
3. **Mercredi, 20 minutes (humain)** : ouvrir la page de suivi, onglet du mois. Valider ou refuser ce qui est « À décider » (SOP 16 pour arbitrer), débloquer ce qui attend quelqu'un, fusionner les PR « à fusionner par un humain ».
4. **Mercredi au mardi suivant (humain ou prestataire, avec Claude)** : exécuter les actions validées dans la journée, une SOP par action : brief (SOP 3), rédaction (SOP 4), optimisation (SOP 5), maillage (SOP 6), technique (`/seo fix`). Après chaque mise en ligne : SOP 11 (`indexation.py annoncer`) et une ligne dans `journal/modifications.csv` (SOP 14). Ce qui est livré avant mardi soir apparaît dans le bilan du mercredi suivant.
5. **Premier mercredi du mois** : la routine fait aussi le rapport (SOP 14) et propose les actions du mois ; vous en validez 3 à 5, pas plus.

**MCP nécessaires** : Search Console (compte de service), le CMS ; Notion si le client suit dans Notion.

**Livrable** : La page de suivi à jour (fait, à décider, bloqué, wins chiffrés), le journal de run `rapports/runs/<date>-hebdo.md`, le journal des modifications.

## Pièges

- Lancer une page neuve qui n'a pas été validée sur la page de suivi : la routine refuse, et elle a raison.
- Faire tourner la routine `hebdo` et les quatre routines séparées sur le même projet : elles écrivent les mêmes fichiers.
- Juger une modification avant J+28 : Search Console bouge trop lentement, on mesure contre un groupe témoin.
- Croire qu'un statut vert dans la liste des routines veut dire « travail fait » : seul le journal de run le dit.
