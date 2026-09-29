# GSC — Incident avant / après

**Groupe :** Diagnostiquer · **Source :** Google Search Console

## La question à laquelle ce skill répond

Un incident a eu lieu à une date connue (piratage, problème de sécurité, migration, refonte) : qu'a-t-il coûté, qu'est-ce qui est revenu, et que faut-il reprioriser ?

## Données à récupérer

Deux périodes de même longueur, de part et d'autre de la date de l'incident (mêmes jours de semaine), en excluant la semaine de l'incident elle-même : clics, impressions, CTR, position, par page et par requête. Plus la série quotidienne sur 6 mois pour voir la rupture et la reprise, et la roadmap SEO en cours du projet.

`gsc.py perf --par date --jours 180 --json` donne la série quotidienne ; pour les requêtes et les pages sur des dates précises, utiliser le MCP `search-console` (dates de début et de fin libres) ou l'export de l'interface en mode « Comparer ».

Accès aux données : voir « Récupérer les données » dans `../SKILL.md`.

## Méthode

1. Dater la rupture sur la série quotidienne ; vérifier qu'elle coïncide avec l'incident et pas avec une mise à jour Google ou un creux saisonnier (`saisonnalite.md`).
2. Comparer avant / après par page puis par requête, en volume absolu : pages perdues, pages revenues, pages qui ne sont jamais revenues.
3. **Longue traîne locale** : regrouper les requêtes par regex large plutôt qu'une à une — fautes de frappe, accents présents ou absents, pluriels, variantes « métier + ville », « métier + département » (nom et numéro). Exemple de motif : `(plomb|plom)i?er?s?.*(nantes|44|loire[- ]atlantique)`. Isolément, chaque requête pèse 1 à 5 impressions ; regroupées, elles révèlent la vraie perte.
4. Évaluer le besoin d'une **page hub département ou région** : si les variantes locales perdues sont dispersées sur plusieurs pages ville sans page qui les chapeaute, et que le cumul est significatif, une page hub est à créer (→ `page-a-creer.md`, `seo-local`).
5. Croiser avec la roadmap existante : ce qui est **fait**, ce qui **reste**, ce qui est **à reprioriser** à la lumière de l'incident. Une action prévue sur une page qui n'a pas récupéré passe devant.

## Sortie attendue

Un verdict en une phrase (« l'incident a coûté X clics sur 28 jours, Y % sont revenus, la perte restante est concentrée sur la longue traîne locale »), puis trois tableaux triés par impact :

| Page | Clics avant | Clics après | Écart | Revenue ? |
|---|---|---|---|---|

| Groupe de requêtes (regex) | Impressions avant | Impressions après | Écart | Page qui les sert |
|---|---|---|---|---|

| Action de la roadmap | Statut (fait / reste / à reprioriser) | Raison | Impact estimé |
|---|---|---|---|

## Le prompt

```
Contexte : site {domaine}. Incident le {date} : {nature — piratage,
migration, refonte, problème de sécurité}.
Objectif : mesurer ce que l'incident a coûté et reprioriser la roadmap.

1. Prends la série quotidienne des clics sur 6 mois. Date la rupture et
   vérifie qu'elle coïncide avec l'incident, pas avec une mise à jour
   Google ou un creux saisonnier (compare au même mois l'an dernier).
2. Compare deux périodes de même longueur avant et après l'incident, en
   excluant la semaine de l'incident, mêmes jours de semaine. Par page
   puis par requête, en clics et impressions absolus.
3. Regroupe la longue traîne locale par expressions régulières larges :
   fautes de frappe, accents présents ou absents, pluriels, variantes
   « métier + ville » et « métier + département » (nom et numéro). Donne
   chaque motif utilisé.
4. Dis si une page hub département ou région est nécessaire : variantes
   locales perdues dispersées sur plusieurs pages, cumul significatif,
   aucune page qui les chapeaute.
5. Croise avec la roadmap que je te fournis : fait / reste / à
   reprioriser, avec la raison.

Rends d'abord le verdict en une phrase, puis trois tableaux triés par
impact : pages, groupes de requêtes, actions de la roadmap.
Termine par les trois actions à mener en premier.

Ne jamais inventer un chiffre : si la donnée manque ou si le volume
est trop faible pour conclure, dis-le explicitement.
Indique toujours la période et le volume qui portent tes conclusions.
```

Règles communes : voir `../SKILL.md`.
