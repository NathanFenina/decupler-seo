# Hebdo — le mercredi

La seule routine du projet quand il tourne au rythme hebdomadaire. Elle fait
en un passage ce que faisaient la veille, l'optimisation, le contenu et le
rapport. Lis `routines/_commun.md` (mode `hebdo`), puis, dans l'ordre :

## 1. Contrôle du site (lecture seule)
Skill `seo-cycle`, mode veille : `seo_live.py --json`, pages prioritaires,
robots.txt, sitemap. Retour du spam ou page clé cassée → une action
`bloquee` sur la page de suivi (étape 5) et une entrée dans `rapports/a-valider.md`.

## 2. Les chiffres
`gsc.py instantane` puis `journal.py mesurer-tout --auto` : on mesure ce qui a
été fait avant d'en faire plus.

## 2 bis. L'indexation
`indexation.py auto` (pages du sitemap modifiées dans la semaine), puis
`indexation.py suivre` : les URL annoncées depuis au moins 3 jours, indexées ou
non. Le constat part dans `rapports/a-valider.md`, regroupé par cause : c'est un
humain qui décide. Les URL à demander à la main vont dans le bilan.

## 3. Les actions validées
Lis la page de suivi ; `pilotage.py etat --statut validee`. Exécute-les, la
remarque du client faisant foi : `marquer --statut en-cours` et republie ;
livrée : `--statut faite --lien <URL>` ; impossible sans quelqu'un :
`--statut bloquee --attend "<qui ou quoi>"`. Les `decision` attendent l'humain.
Rien de validé : le travail automatique du mode optimisation, dans ses plafonds.
Une page neuve ne part jamais sans action validée.

## 3 bis. Les notes humaines
Lis les notes de `notes/` étiquetées `#a-traiter` (voir `notes/README.md`) :
chacune devient une action `a-valider` ou `validee` sur la page de suivi, ou
une ligne de `memoire/decisions.md` si c'est une décision. Remplace ensuite
l'étiquette par `#traite` suivie du lien vers ce que tu as créé. Un
`#fait-client` ne va dans `memoire/faits.md` qu'avec sa source et sa date.

## 4. Le premier mercredi du mois, en plus
Le rapport du mois écoulé (skill `seo-cycle`, mode rapport) et les propositions
du mois (`pilotage.py donnees`, `proposer`, `injecter`).

## 5. Le bilan de la semaine dans la page
Écris `donnees/semaine.json` puis `pilotage.py mois --fichier donnees/semaine.json` :
```json
{"mois": "AAAA-MM",
 "semaine": {"date": "<lundi de la semaine>", "resume": "3 lignes : fait, appris, bloqué",
             "chiffres": {"clics": 0, "impressions": 0}},
 "wins": [{"texte": "un gain mesuré, chiffré", "lien": "preuve"}],
 "contenus": [{"titre": "", "url": "", "statut": "brouillon|publié|mis à jour", "date": "AAAA-MM-JJ", "notion": ""}],
 "reporting": {"clics": 0, "impressions": 0}}
```
Un win est un fait mesuré (position, clics, citation IA, page indexée), jamais
une intention. Chaque point bloquant devient une action `bloquee` qui dit qui
on attend : il apparaît dans « À décider ». Republie la page, puis
`pilotage.py sauvegarder` : la copie `journal/pilotage.json` part dans git.

## 6. Livrer
Journal de run `rapports/runs/<date>-hebdo.md`, commit sur `claude/hebdo-<date>`,
push, PR. Fusionne si la session le permet, sinon règle « étape refusée ».
