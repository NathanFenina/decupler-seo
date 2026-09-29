---
name: seo-reporting
description: >
  Produit le rapport SEO mensuel : les chiffres sont calculés par
  rapport.py (Search Console, journal des modifications, routines), l'agent
  rédige la lecture — causes, ce qui a marché, ce qu'on arrête, les 5 actions
  du mois suivant — et ajoute la santé des données structurées, l'exactitude
  de l'entité dans les IA, le croisement avec la roadmap et le point client.
  Déclencher sur "rapport", "reporting", "bilan mensuel", "rapport SEO",
  "comment ça évolue", "résultats du mois", "point mensuel", "rapport
  client", "évolution du trafic".
---

# Rapport — dire ce qui s'est passé et pourquoi

Un rapport SEO qui aligne des courbes sans expliquer ne sert à rien. Le
livrable, c'est : **ce qui a bougé, pourquoi, et ce qu'on fait maintenant.**

## Étape 1 — Les chiffres : un script, pas l'agent

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/rapport.py" [--mois AAAA-MM] [--site sc-domain:exemple.com] [--json]
```

Sans `--mois`, le mois précédent complet. Le script écrit :

- `rapports/AAAA-MM.md` — la partie factuelle : trafic du mois contre le
  mois précédent **et** le même mois de l'an passé ; marque, hors marque et
  requêtes anonymisées par Google ; pages et requêtes en hausse et en
  baisse ; requêtes apparues ; modifications du mois et verdicts des mesures
  arrivées à échéance (journal) ; routines exécutées trouvées dans
  `rapports/runs/` ; points en attente dans `rapports/a-valider.md`
- `rapports/AAAA-MM.json` — clés fixes (`clics`, `impressions`,
  `position_moyenne`, `clics_variation_pct`, `modifications`, `gains`,
  `neutres`, `pertes`, `a_valider`, `runs_attendus`, `runs_trouves`),
  additionnables d'un projet à l'autre

**L'agent n'écrit aucun chiffre de trafic.** Il rédige uniquement la section
`## Lecture et décisions`, à la fin du fichier. Relancer `rapport.py`
recalcule la partie chiffrée et **conserve cette section**. Pourquoi : un
chiffre recalculé à la main dans un texte est un chiffre qui finit faux.

**Comparez toujours à M-12, pas seulement à M-1.** Une baisse de 15 % en
août est normale ; une baisse de 15 % par rapport à août dernier ne l'est
pas. Le mois précédent ne dit presque rien sur une activité saisonnière.

## Étape 2 — Compléter ce que le script ne couvre pas

| Source | Ce qu'on prend | Où |
|--------|----------------|-----|
| GA4 | Sessions organiques, conversions, pages d'entrée | Si branché |
| Autorité | Domaines référents gagnés / perdus | Sur la période |
| GEO | Share of model par moteur (`geo-share-of-model`) | Mensuel |
| **Données structurées** | Erreurs Search Console → Améliorations ; pages sans balisage ; pages dont le socle diverge (`schema_validate.py --socle`) | Mensuel, crawl + GSC |
| **Entité dans les IA** | Attributs justes / faux quand on demande « qui est [marque] » : activité, lieu, dirigeant, date, offre | Mensuel. C'est la **réputation**, distincte du share of model (la présence) |
| Roadmap | Fait / restant / re-priorisé | Sur la période |

Une IA qui cite la marque avec la mauvaise ville ou une offre arrêtée est un
problème de réputation, pas de visibilité : il se corrige par le socle
JSON-LD, les pages « À propos » et les sources tierces, pas par du contenu.

## Étape 3 — La section « Lecture et décisions »

### 1. L'essentiel — 5 lignes maximum

Repris du tableau du script, avec un feu et une phrase. Une personne pressée
doit avoir compris en dix secondes.

### 2. Les causes, pas les courbes

C'est la partie qui a de la valeur.

> **+18 % de clics ce mois-ci.** Trois quarts de la hausse viennent de
> 4 pages retravaillées le mois dernier (`/guide-x`, `/comparatif-y`,
> `/prix-z`, `/faq-w`) : elles sont passées d'une position moyenne de 11,3 à
> 6,1, ce qui a triplé leur CTR. Le quart restant vient de la page
> `/etude-2026` publiée le 8, qui a capté 340 clics en trois semaines.

Croisez avec les conversions si GA4 est branché : « le trafic monte sur des
pages qui ne convertissent pas » est une information, « le trafic monte »
n'en est pas une.

### 3. Ce qui a marché

Les verdicts « gain » du journal, avec la modification qui les explique.

### 4. Ce qu'on arrête

**Ne sautez jamais cette section.** Les verdicts « perte » (proposés au
retour arrière par le script) et ce qui ne produit rien.

> Les 15 pages ville publiées en janvier : 3 indexées sur 15 à deux mois.
> Le gabarit ne produit pas assez de contenu propre à chaque zone.
> Décision : on n'en publie pas d'autres, on enrichit les 15 existantes
> avec des réalisations locales réelles, et on re-mesure à J+45.

### 5. Santé des données structurées et de l'entité

```
Données structurées   2 erreurs GSC (FAQPage)   4 pages sans balisage   socle identique partout   🟡
Entité dans les IA    5 attributs justes / 7    faux : ville (ancienne adresse), offre arrêtée    🔴
```

### 6. Roadmap

| Fait | Restant | Re-priorisé (et pourquoi) |
|------|---------|---------------------------|

### 7. Les 5 actions du mois prochain

Tirées de `opportunites.py`, triées par score, avec la page concernée et le
gain attendu. Cinq, pas quinze.

## Étape 4 — Le point client mensuel

Pour une agence, le rapport se double d'un point court, toujours dans le
même ordre :

| Fait | À faire | Demandes client | Wins |
|------|---------|-----------------|------|
| Ce qui a été livré ce mois-ci | Le mois prochain, les 5 actions | Ce qu'on attend du client (accès, validations, contenus), avec date | Les gains mesurés, chiffrés, avec la page |

Les demandes client en attente sont la première cause de retard d'un plan
SEO : les nommer chaque mois, avec la date de la première demande.

## Adapter au destinataire

| Destinataire | Ce qui l'intéresse | À éviter |
|--------------|-------------------|----------|
| **Dirigeant** | Leads, chiffre d'affaires, une phrase de synthèse | Positions, impressions, jargon |
| **Marketing** | Trafic par page, contenus performants, prochaines publications | Détails techniques |
| **Technique** | Erreurs d'indexation et de données structurées, CWV, correctifs | Considérations éditoriales |
| **Agence → client** | Fait / À faire / Demandes client / Wins | Tout ce qui ne sert pas la décision |

Pour un dirigeant, la ligne qui compte est : « le SEO a généré 47 leads ce
mois-ci, pour une valeur estimée de 94 000 € ». Le reste est du détail.

## Règles

- **Aucun chiffre sans source.** Les chiffres de trafic viennent de
  `rapport.py` ; les autres d'un outil nommé.
- **Aucune courbe sans cause.** Une hausse sans explication n'est pas un
  résultat, c'est du bruit.
- **Annoncer l'incertitude.** « La hausse coïncide avec un core update, on ne
  peut pas isoler la part de nos actions » est une phrase honnête et utile.
- **Ne jamais gonfler.** Un rapport qui embellit se paie au trimestre suivant.

## Format et automatisation

- **Markdown** — `rapports/AAAA-MM.md`, par défaut
- **HTML** — voir `seo-dashboard` pour une version visuelle autonome
- **Notion** — les valeurs du JSON poussées dans la base Objectifs & KPI

Une Routine mensuelle lance `rapport.py` ; vous relisez et rédigez la
lecture — la seule partie qui demande du jugement. L'historique des
`rapports/*.json` donne la trajectoire : au bout de six mois, on lit une
tendance, pas un instantané.
