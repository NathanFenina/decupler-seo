# Règles communes à tous les projets

Nées de corrections humaines sur de vrais projets, retirées de tout nom de client. Elles
s'appliquent partout, avant les préférences de style, sauf décision contraire écrite dans
`memoire/decisions.md` du projet. Chaque skill de rédaction, de page et de relecture les lit ;
`controle_contenu.py`, `humanisation.py`, `copywriting.py` et `scores_page.py` en vérifient une
partie. Une règle nouvelle entre ici par une remontée (`projet.py remonter`), avec sa date.

## Écriture

1. **Zéro tiret cadratin (—) ni demi-cadratin (–) de ponctuation.** Virgule, deux-points,
   parenthèses ou point.
2. **Un fait consigné s'écrit comme un fait.** Pas de formule d'attribution ni de précaution
   (« selon le fondateur », « d'après X, qui suit le compte », « sans capture publiée », bloc
   « ce que ces chiffres ne disent pas »). Si le fait n'est pas dans `memoire/faits.md`, on ne
   l'écrit pas.
3. **Ne jamais annoncer ce qu'on tait** : ni « non publié », ni « on ne publie pas », ni « nom
   non communiqué ». On écrit ce qu'on sait.
4. **Pas de formule de franchise** : « je te le dis », « autant le dire », « soyons honnêtes ».
5. **Vendre en positif** : une limite s'écrit comme une condition, pas comme l'argument. Pas de
   section défensive ou hors sujet (« pourquoi nous refusons… », « pourquoi attendre 6 mois »).
6. **Une section sert une décision du lecteur** (faire, payer, attendre, éviter) ; sinon elle sort.
7. **L'adresse du lecteur (tu ou vous) est celle de `memoire/marque.md`**, partout, y compris
   dans les menus, boutons, FAQ et légendes.

## Preuves et cas clients

8. **Aucun chiffre hors de `memoire/faits.md`**, aucune preuve inventée (témoignage, logo,
   compteur, certification, statut de partenaire).
9. **Études de cas sans date de mission ni de relevé** : durées relatives (« sur 3 mois », « le
   trimestre suivant »). Pas de frise de dates.
10. **Jamais d'audit public du site d'un client** dans son étude de cas : on montre la méthode et
    les résultats, pas ses défauts.
11. **Captures de tiers** : noms et numéros des autres entreprises floutés.
12. **Unités des outils** : les CPC de DataForSEO sont en dollars US ; une conversion en euros
    cite le taux et sa date.

## Images

13. **Une image générée n'est jamais présentée comme une scène réelle**, un client ou un lieu
    réel ; jamais de fausse capture, de faux tableau de bord ni de courbe de résultat dans une
    image générée.
14. **Une page sans matière visuelle réelle est une page plate** : captures, logos d'outils et de
    clients réels, schémas, exemples. Chaque image porte `alt`, `width` et `height`.

## Pages et contenus

15. **Avant chaque page** : SERP et top 5 lus en entier (`seo-benchmark`), mot-clé SMART (volume
    et difficulté relevés et datés, intention lue, aucune cannibalisation), au moins 3 éléments
    d'information gain, et 6 notes sur 100 (`scores_page.py` : SEO 85, AI Search, rédaction,
    conversion, UX, design 80).
16. **Relecture avant publication** par l'agent `seo-relecteur`, et face à la SERP par
    `seo-challenger-serp` pour une page neuve ou une refonte.
17. **Ressources contre e-mail** : le fichier (ZIP, PDF) ne part qu'après l'e-mail ; le texte de
    la page reste lisible par Google, aucune adresse de fichier en clair.

## Pilotage

18. **Une seule validation par semaine** : le lot de la page de suivi ; rien de neuf ne part sans
    validation, le niveau automatique part seul et se journalise.
19. **Chaque retour humain s'écrit le jour même** (décision, skill `projet-*`, carnet de
    rédaction ou contrôle automatique) ; s'il vaut pour tous les projets, il remonte ici.
20. **Indexation** : IndexNow, sitemaps et maillage ; ne jamais demander à l'humain des demandes
    d'indexation manuelles.
21. **Réponses de fin de tâche** : une seule liste numérotée, pour qu'on puisse répondre point par
    point.
