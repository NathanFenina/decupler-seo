# Registre des entités et vérification Wikidata

Un `sameAs` vers Wikidata affirme que la chose décrite **est** l'élément
Wikidata. Une erreur n'est pas neutre : elle rattache la page à une autre
entité, et les moteurs IA propagent la confusion.

## Le registre du projet

`memoire/entites.json` — une entrée par entité, vérifiée une fois, réutilisée
partout. C'est la seule source des `sameAs` : aucun QID n'est écrit de
mémoire dans un balisage.

```json
{
  "plomberie": {
    "name": "Plomberie",
    "type": "Thing",
    "wikidata": "https://www.wikidata.org/wiki/Q…",
    "wikipedia": "https://fr.wikipedia.org/wiki/Plomberie",
    "description_wikidata": "ensemble des techniques…",
    "verifie_le": "2026-09-01",
    "par": "agent"
  },
  "lyon": {
    "name": "Lyon",
    "type": "City",
    "wikidata": "https://www.wikidata.org/wiki/Q…",
    "wikipedia": "https://fr.wikipedia.org/wiki/Lyon",
    "description_wikidata": "commune française, chef-lieu…",
    "verifie_le": "2026-09-01",
    "par": "agent"
  }
}
```

## Le processus, pour chaque nouvelle entité

1. **Chercher** : `https://www.wikidata.org/w/api.php?action=wbsearchentities&search=<terme>&language=fr&format=json`
   (ou la recherche du site Wikidata).
2. **Lire la description** de chaque candidat. Le libellé ne suffit pas :
   « Mercure » renvoie une planète, un élément, un dieu, un journal.
3. **Ouvrir l'élément retenu** et vérifier l'article Wikipédia lié en
   français (le lien de la section « Wikipédia »), pas une traduction devinée.
4. **Inscrire** l'entité au registre avec la description lue et la date.
5. **Pas de candidat certain → pas de `sameAs`.** L'entité part avec son
   seul `name`. Un balisage incomplet est corrigible ; un faux `sameAs` est
   une affirmation fausse.

## Re-vérification trimestrielle

Les éléments Wikidata fusionnent, changent de description, sont supprimés.
Chaque trimestre : relire chaque QID du registre, comparer la description à
celle enregistrée, mettre à jour `verifie_le`. Un élément fusionné redirige
vers un autre QID : remplacer partout.

## Choisir about ou mentions

| Question | Réponse | Propriété |
|----------|---------|-----------|
| Sans cette entité, la page est-elle hors sujet ? | Oui | `about` (3 maximum) |
| L'entité est-elle nommée dans le contenu principal ? | Oui | `mentions` (12 maximum) |
| Elle n'apparaît que dans le menu ou le pied de page | — | Rien |

## Types à utiliser

| Entité | Type |
|--------|------|
| Concept, discipline, technique | `Thing` |
| Logiciel **cité** | `Thing` — jamais `SoftwareApplication` |
| Ville, pays | `City`, `Country` (dans `areaServed` ou `mentions`) |
| Organisation tierce | `Organization` avec son propre `@id` externe, sinon `Thing` |
| Personne publique | `Person` avec `sameAs` |
