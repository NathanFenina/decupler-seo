<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 11 · Indexation

**Skills** : `seo-indexation` · **Commande** : `/seo index`

**Objectif** : Que Google explore et indexe tes pages neuves ou corrigées, sans tricher.

**Quand** : Après chaque publication, et chaque semaine pour les pages importantes.

**Dis à Claude** : « Annonce les pages publiées aujourd'hui » (juste après une mise en ligne), puis le vendredi : « Suis l'indexation et donne-moi les URL à demander. »

## Étapes

0. Juste après chaque mise en ligne : `indexation.py annoncer <URL…>`. Le script envoie les URL à IndexNow (Bing et les moteurs partenaires ; Bing alimente Copilot), resoumet les sitemaps à Google par l'API, et inscrit chaque URL dans `donnees/indexation.csv`. C'est ce que font les extensions d'« indexation instantanée » de WordPress, sans l'Indexing API de Google. Clé IndexNow : `indexation.py cle`, une seule fois par site.
1. À partir de J+3 : `indexation.py suivre`. Le script inspecte les URL annoncées par l'API, met le registre à jour et sort les 10 URL non indexées à passer à la main. Pour une inspection ponctuelle : Inspection par l'API de Search Console (`gsc.py inspect --fichier urls.txt`) : indexée ou non, date du dernier passage, canonique retenue par Google.
2. Diagnostic des pages non indexées : découverte mais pas explorée, explorée mais pas indexée, canonique, noindex, doublon.
3. Des sitemaps propres (seulement des URL indexables), resoumis par l'API (`gsc.py sitemap --resoumettre`).
4. Un lien vers chaque page neuve depuis une page que Google visite souvent : l'accueil ou une page hub.
5. La liste du jour, une dizaine d'URL, à passer dans Search Console : Inspection de l'URL, puis « Demander l'indexation ».

**MCP nécessaires** : Search Console, avec un compte de service. L'écriture complète n'est nécessaire que pour resoumettre les sitemaps.

**Livrable** : L'état d'indexation page par page et la liste priorisée des demandes du jour.

## Pièges

- Croire qu'une API permet de « Demander l'indexation » : il n'en existe pas de publique. L'Indexing API ne couvre que les offres d'emploi et les vidéos en direct.
- Payer un service d'indexation, ou brancher l'Indexing API de Google sur des articles (c'est ce que fait l'extension « Instant Indexing for Google ») : Google l'a réservée aux offres d'emploi et aux vidéos en direct, et a écrit en 2024 que les abus peuvent faire couper l'accès.
- Croire qu'IndexNow touche Google : Google n'y participe pas. Pour Google, c'est le sitemap, les liens internes et la demande manuelle.
- Se fier au rapport d'indexation, qui a plusieurs jours de retard. La vérité page par page vient de l'inspection.

**Astuce, à tester avec prudence** : Claude Code peut piloter ton Chrome (`claude --chrome`, extension Claude in Chrome) dans ta session déjà connectée, et cliquer sur « Demander l'indexation » pour les URL de la liste du jour. Google ne publie pas le quota (environ une dizaine par jour et par propriété, d'après des tests extérieurs) et dit qu'insister n'accélère rien. Réserve-le à quelques URL stratégiques, reste devant l'écran, et ne le mets jamais dans une routine.

> Chez nous : Semaine du 22 au 25/09/2026 sur decupler.com : 459 URL inspectées une par une par l'API, sitemaps resoumis (154 pages lues, zéro erreur).
