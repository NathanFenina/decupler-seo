---
name: seo-reporting
description: >
  Produit le rapport SEO périodique en croisant Search Console, GA4, les
  positions et le score GEO : évolutions, causes, ce qui a été fait, ce que ça
  a donné, et les priorités du mois suivant. Déclencher sur "rapport",
  "reporting", "bilan mensuel", "rapport SEO", "comment ça évolue", "résultats
  du mois", "point mensuel", "rapport client", "évolution du trafic".
---

# Rapport — dire ce qui s'est passé et pourquoi

Un rapport SEO qui aligne des courbes sans expliquer ne sert à rien. Le
livrable, c'est : **ce qui a bougé, pourquoi, et ce qu'on fait maintenant.**

## Étape 1 — Collecter

| Source | Ce qu'on prend | Période |
|--------|----------------|---------|
| Search Console | clics, impressions, CTR, position moyenne, par page et par requête | M vs M-1 **et** M vs M-12 |
| GA4 | sessions organiques, conversions, revenu par canal, pages d'entrée | Idem |
| Positions | top 3, top 10, top 20 sur les requêtes suivies | Idem |
| Index | pages indexées, erreurs de couverture | État actuel |
| Autorité | domaines référents, liens gagnés/perdus | Sur la période |
| GEO | share of model par moteur | Mensuel |
| Roadmap | actions réalisées, actions à mesurer | Sur la période |

**Comparez toujours à M-12, pas seulement à M-1.** Une baisse de 15 % en
août est normale ; une baisse de 15 % par rapport à août dernier ne l'est
pas. Le mois précédent ne dit presque rien sur une activité saisonnière.

## Étape 2 — La structure du rapport

### 1. L'essentiel — 5 lignes maximum

```
Trafic organique     4 210 clics    +18 % vs M-1    +34 % vs M-12   🟢
Conversions            47           +12 %           +52 %           🟢
Position moyenne       14,2         −1,8 place      −4,1            🟢
Domaines référents     84           +3              +19             🟢
Share of model         27 %         +3 pts          n/d             🟢
```

Une personne pressée doit avoir compris en dix secondes.

### 2. Ce qui explique les chiffres

C'est la partie qui a de la valeur. Pas de graphique sans cause.

> **+18 % de clics ce mois-ci.** Trois quarts de la hausse viennent de
> 4 pages retravaillées le mois dernier (`/guide-x`, `/comparatif-y`,
> `/prix-z`, `/faq-w`) : elles sont passées d'une position moyenne de 11,3 à
> 6,1, ce qui a triplé leur CTR. Le quart restant vient de la page
> `/etude-2026` publiée le 8, qui a capté 340 clics en trois semaines.

> **Conversions en hausse plus lente que le trafic** (+12 % contre +18 %).
> La croissance vient majoritairement de pages informationnelles, qui
> convertissent moins. C'est attendu à ce stade du plan, mais il faudra
> renforcer le maillage de ces pages vers `/devis` — c'est dans la roadmap
> du mois prochain.

### 3. Ce qui a été fait

Repris de la roadmap : les actions terminées sur la période, avec leur
résultat mesuré quand la date de mesure est passée.

| Action | Date | Résultat mesuré |
|--------|------|-----------------|
| Réécriture des titles sur 12 pages | 04/03 | CTR moyen 2,1 % → 3,4 % |
| Correction des 8 pages orphelines | 11/03 | +2 900 impressions/mois |
| Publication de l'étude annuelle | 08/03 | 6 domaines référents, 340 clics |

Les actions dont la mesure n'est pas encore due sont listées à part, avec
leur date de relevé.

### 4. Ce qui n'a pas marché

**Ne sautez jamais cette section.** Un rapport qui ne présente que des
succès n'est pas crédible, et il empêche d'apprendre.

> Les 15 pages ville publiées en janvier : 3 indexées sur 15 à deux mois.
> Le gabarit ne produit pas assez de contenu propre à chaque zone.
> Décision : on n'en publie pas d'autres, on enrichit les 15 existantes
> avec des réalisations locales réelles, et on re-mesure à J+45.

### 5. Le mois prochain

3 à 5 actions, reprises de la roadmap, triées par priorité, avec le gain
attendu. Pas 15.

## Étape 3 — Adapter au destinataire

| Destinataire | Ce qui l'intéresse | À éviter |
|--------------|-------------------|----------|
| **Dirigeant** | Leads, chiffre d'affaires, une phrase de synthèse | Positions, impressions, jargon |
| **Marketing** | Trafic par page, contenus performants, prochaines publications | Détails techniques |
| **Technique** | Erreurs d'indexation, CWV, correctifs à déployer | Considérations éditoriales |
| **Agence → client** | Ce qui a été fait, ce que ça a produit, ce qui vient | Tout ce qui ne sert pas la décision |

Pour un dirigeant, la ligne qui compte est : « le SEO a généré 47 leads ce
mois-ci, pour une valeur estimée de 94 000 € ». Le reste est du détail.

## Étape 4 — Le format

- **Markdown** — par défaut, lisible partout
- **HTML** — voir `/seo dashboard` pour une version visuelle autonome
- **Notion** — les valeurs poussées dans la base Objectifs & KPI

Gardez chaque rapport dans `seo-output/rapports/AAAA-MM.md`. L'historique
est ce qui donne de la valeur au dispositif : au bout de six mois, vous
lisez une trajectoire, pas un instantané.

## Règles

- **Aucun chiffre sans source.** Chaque donnée vient d'un outil nommé.
- **Aucun graphique sans explication.** Une courbe qui monte sans cause
  identifiée n'est pas un résultat, c'est du bruit.
- **Annoncer l'incertitude.** « La hausse coïncide avec un core update, on ne
  peut pas isoler la part de nos actions » est une phrase honnête et utile.
- **Ne jamais gonfler.** Un rapport qui embellit se paie au trimestre suivant.

## Automatiser

```
/loop 30d /seo rapport
```

Ou une Routine mensuelle. Le rapport se génère, vous relisez la partie
analyse — c'est la seule qui demande du jugement.

## Livrables

- `rapports/AAAA-MM.md` — le rapport
- `rapports/AAAA-MM-donnees.csv` — les données brutes
- `historique-kpi.csv` — la série temporelle, alimentée à chaque rapport
