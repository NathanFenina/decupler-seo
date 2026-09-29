# Registre des entités et vérification Wikidata

Un `sameAs` vers Wikidata affirme que la chose décrite **est** l'élément
Wikidata. Une erreur n'est pas neutre : elle rattache la page à une autre
entité, et les moteurs IA propagent la confusion.

## Le registre du projet

`memoire/entites.csv` — une ligne par entité, vérifiée une fois, réutilisée
partout. C'est la seule source des `sameAs` : aucun QID n'est écrit de
mémoire dans un balisage.

```csv
entite,type,qid,sameAs,definition,alias
Plomberie,Thing,Q…,https://fr.wikipedia.org/wiki/Plomberie,Ensemble des techniques d'installation des réseaux d'eau,plombier
Lyon,City,Q…,https://fr.wikipedia.org/wiki/Lyon,Commune française,
```

Format complet (colonnes, `@id` du socle, alias, commentaires) et registre
des faits (`memoire/triplets.csv`) : `seo-entites-triplets/references/registre.md`.
L'ancien format JSON (`memoire/entites.json`) reste lu par `triplets.py` ;
migrez-le vers le CSV à la prochaine mise à jour.

## Le processus, pour chaque nouvelle entité

1. **Chercher** : `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/triplets.py" wikidata "<terme>"`
   (API `wbsearchentities`, sans clé ; `--site <domaine>` pour une
   organisation : seul l'élément dont le site officiel P856 est ce domaine
   est retenu).
2. **Lire la description** de chaque candidat. Le libellé ne suffit pas :
   « Mercure » renvoie une planète, un élément, un dieu, un journal.
3. **Ouvrir l'élément retenu** et vérifier l'article Wikipédia lié en
   français (le lien de la section « Wikipédia »), pas une traduction devinée.
4. **Inscrire** l'entité au registre avec sa définition et son QID ; la
   date de vérification va dans le journal du run.
5. **Pas de candidat certain → pas de `sameAs`.** L'entité part avec son
   seul `name`. Un balisage incomplet est corrigible ; un faux `sameAs` est
   une affirmation fausse.

## Re-vérification trimestrielle

Les éléments Wikidata fusionnent, changent de description, sont supprimés.
Chaque trimestre : relire chaque QID du registre avec `triplets.py wikidata`,
comparer la description au sens de l'entité dans les pages. Un élément
fusionné redirige vers un autre QID : remplacer dans le registre, puis
`triplets.py verifier --strict` sur les pages signale chaque balisage resté
sur l'ancien.

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
