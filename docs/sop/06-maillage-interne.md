<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 6 · Maillage interne

**Skills** : `seo-maillage-interne` · **Commande** : `/seo maillage`

**Objectif** : Faire circuler l'autorité vers les pages qui rapportent, avec un plan applicable ligne par ligne.

**Quand** : Après chaque publication, et une fois par trimestre sur tout le site.

**Dis à Claude** : « Trouve mes pages orphelines et propose 20 liens internes : la page de départ, l'ancre et l'endroit exact. »

## Étapes

1. Crawl du site et autorité interne (`crawl_site.py`, `internal_pagerank.py`). Sur WordPress, la carte des liens du corps de texte (`wp.py carte`).
2. Cinq diagnostics : pages orphelines, pages qui convertissent mais reçoivent peu de liens, pages à plus de 3 clics de l'accueil, culs-de-sac, ancres vides ou sur-optimisées.
3. Le plan : depuis, vers, ancre, emplacement, raison. Une ligne doit pouvoir s'appliquer sans réfléchir.
4. Sur WordPress, `wp.py maillage --cible <url> --appliquer` pose le lien en révision quand l'ancre existe déjà dans le texte.
5. Positions de départ relevées, puis remesurées à J+30.

**MCP nécessaires** : Search Console, GA4 pour les conversions, WordPress pour appliquer.

**Livrable** : Le plan de liens en CSV et les révisions prêtes à valider.

## Pièges

- Compter sur le menu et le pied de page : un lien dans le texte pèse bien plus.
- « Cliquez ici » ou « en savoir plus » : ces ancres ne disent rien à Google.
- Poser 400 liens en un jour. Le rythme conseillé : 20 à 30 par semaine.
