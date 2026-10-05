<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 12 · Analyse GSC / GA4

**Skills** : `seo-gsc-analyses`, `seo-quick-wins` · **Commande** : `/seo quickwins, ou /seo gsc`

**Objectif** : Répondre à une question précise avec tes vraies données, et en tirer une action.

**Quand** : Chaque semaine pour les quick wins, et dès qu'une courbe bouge.

**Dis à Claude** : « Quelles pages sont en position 4 à 20 avec des impressions ? Classe-les et écris les corrections. »

## Étapes

1. Brancher les données : `gsc.py` avec un compte de service (le plus fiable), le MCP Search Console, un connecteur, ou un export CSV.
2. Choisir la question parmi 21 analyses prêtes : gagnants et perdants, pages qui déclinent, cannibalisation, CTR anormal, requêtes sans page, saisonnalité, Google face aux IA…
3. Les quick wins : pages en position 4 à 20, triées en quatre paquets (snippet, contenu insuffisant, cannibalisation, presque là).
4. GA4 relie chaque page à ses conversions, pour chiffrer le potentiel en euros.
5. Chaque analyse se termine par une action et le skill qui l'exécute.

**MCP nécessaires** : Search Console et GA4.

**Livrable** : Le tableau de l'analyse et la liste d'actions, 10 pages au plus pour les quick wins.

## Pièges

- Une propriété de domaine s'écrit `sc-domain:exemple.com`, sinon l'API renvoie zéro ligne.
- Chercher plus de 16 mois d'historique : l'API s'arrête là.
- Donner le rôle propriétaire au compte de service. La lecture seule suffit.

> Chez nous : Quick wins de decupler.com du 30/08 au 26/09/2026 : 13 requêtes entre la position 8 et 20, dont « agence geo bordeaux », 219 impressions, position 8,1, aucun clic.
