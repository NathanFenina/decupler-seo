<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 8 · Données structurées

**Skills** : `seo-schema-jsonld` · **Commande** : `/seo schema`

**Objectif** : Un balisage JSON-LD valide, fidèle à ce qu'on voit sur la page, relié à ton entité.

**Quand** : À chaque page publiée ou refondue.

**Dis à Claude** : « Génère le JSON-LD de cette page, valide-le, et vérifie qu'il correspond au contenu visible. »

## Étapes

1. Un seul `@graph` par page : un socle identique partout (Organization et WebSite), puis les nœuds du type de page (WebPage, Service, BlogPosting, FAQPage, Person…).
2. Les `@id` : une entité, un identifiant, réutilisé sur tout le site.
3. Génération selon le type de page : service, article, page locale, FAQ, page auteur.
4. Validation par `schema_validate.py --strict`, sur le HTML initial : ce que voient les robots qui n'exécutent pas le JavaScript.
5. Contrôle à l'œil : chaque prix, note ou avis balisé apparaît bien sur la page.

**MCP nécessaires** : Aucun. Chrome DevTools pour vérifier le rendu.

**Livrable** : Le JSON-LD de la page, validé, et le socle commun à tout le site.

## Pièges

- Un outil cité se balise `Thing` avec `sameAs`, pas `SoftwareApplication`.
- Pas d'`aggregateRating` sur ta propre Organisation : avis auto-attribués, ignorés et sanctionnables.
- `SearchAction` ne sert plus : le champ de recherche des sitelinks a disparu en novembre 2024.
- `headline` reprend le H1, en 110 caractères au plus.
