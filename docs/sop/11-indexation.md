<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 11 · Indexation

**Skills** : `seo-indexation` · **Commande** : `/seo index`

**Objectif** : Que Google explore et indexe tes pages neuves ou corrigées, sans tricher.

**Quand** : Après chaque publication, et chaque semaine pour les pages importantes.

**Dis à Claude** : « Inspecte les pages publiées ce mois-ci, resoumets les sitemaps et prépare-moi les 10 URL à demander aujourd'hui. »

## Étapes

1. Inspection par l'API de Search Console (`gsc.py inspect --fichier urls.txt`) : indexée ou non, date du dernier passage, canonique retenue par Google.
2. Diagnostic des pages non indexées : découverte mais pas explorée, explorée mais pas indexée, canonique, noindex, doublon.
3. Des sitemaps propres (seulement des URL indexables), resoumis par l'API (`gsc.py sitemap --resoumettre`).
4. Un lien vers chaque page neuve depuis une page que Google visite souvent : l'accueil ou une page hub.
5. La liste du jour, une dizaine d'URL, à passer dans Search Console : Inspection de l'URL, puis « Demander l'indexation ».

**MCP nécessaires** : Search Console, avec un compte de service. L'écriture complète n'est nécessaire que pour resoumettre les sitemaps.

**Livrable** : L'état d'indexation page par page et la liste priorisée des demandes du jour.

## Pièges

- Croire qu'une API permet de « Demander l'indexation » : il n'en existe pas de publique. L'Indexing API ne couvre que les offres d'emploi et les vidéos en direct.
- Payer un service d'indexation : ça ne sert à rien.
- Se fier au rapport d'indexation, qui a plusieurs jours de retard. La vérité page par page vient de l'inspection.

**Astuce, à tester** : Claude Code peut piloter ton Chrome (`claude --chrome`, extension Claude in Chrome) dans ta session déjà connectée. Tu peux lui demander d'ouvrir l'inspection de chaque URL de la liste du jour et de cliquer sur « Demander l'indexation ». Je ne l'ai pas encore éprouvé à grande échelle : regarde-le faire la première fois, reste à une dizaine d'URL par jour, et il s'arrête de lui-même sur un CAPTCHA.

> Chez nous : Semaine du 22 au 25/09/2026 sur decupler.com : 459 URL inspectées une par une par l'API, sitemaps resoumis (154 pages lues, zéro erreur).
