---
name: seo-eeat
description: >
  Évalue et renforce les signaux E-E-A-T (Experience, Expertise,
  Authoritativeness, Trustworthiness) d'une page ou d'un site, selon les
  Quality Rater Guidelines. Note sur 40, verdict publier/réviser/réécrire, et
  correctifs localisés. Déclencher sur "E-E-A-T", "EEAT", "autorité",
  "crédibilité", "signaux de confiance", "YMYL", "quality rater", "pourquoi
  Google ne me fait pas confiance", "page auteur", "expertise".
---

# E-E-A-T — prouver, pas déclarer

E-E-A-T n'est pas un score que Google calcule. C'est un faisceau de signaux
que les évaluateurs humains vérifient et que les systèmes tentent
d'approximer. Sur les sujets YMYL (santé, finance, droit, sécurité), c'est
décisif. Sur le reste, c'est un départage.

C'est aussi, en 2026, l'un des principaux critères de **citation par les
LLM** : un modèle cite ce qu'il peut attribuer à quelqu'un d'identifiable.

Notez sans complaisance. Un audit E-E-A-T indulgent ne sert à rien.

## Experience — l'expérience de première main (10 pts)

Le « E » ajouté en 2022, et le plus discriminant aujourd'hui.

Ce qui compte : avoir fait la chose. Testé le produit, mené la mission, vécu
la situation.

| Signal | Pts |
|--------|-----|
| Récit d'une situation vécue, datée et située | 3 |
| Résultats mesurés et chiffrés issus de votre pratique | 3 |
| Éléments de preuve : photos, captures, données propres | 2 |
| Mention des limites et des échecs rencontrés | 2 |

> ❌ « Nous avons une expertise reconnue en optimisation de sites e-commerce. »
> ✅ « Sur les 34 refontes e-commerce que nous avons pilotées entre 2023 et
> 2025, 6 ont perdu du trafic les trois premiers mois. Dans 5 cas sur 6, la
> cause était la même : les redirections faites après la mise en ligne. »

La deuxième version est invérifiable elle aussi, mais elle est **spécifique**,
et la spécificité est le marqueur que les évaluateurs cherchent.

## Expertise — la maîtrise du sujet (10 pts)

| Signal | Pts |
|--------|-----|
| Auteur identifié, avec ses qualifications | 3 |
| Vocabulaire technique exact, employé à bon escient | 2 |
| Nuances et cas limites traités | 2 |
| Profondeur : le « comment », pas seulement le « quoi » | 2 |
| Absence d'erreurs factuelles | 1 |

Un article signé « L'équipe » perd des points. Une page auteur avec un
parcours, des publications et des profils externes vérifiables en gagne.

L'expertise se voit surtout aux **cas particuliers**. N'importe qui peut
écrire la règle générale ; seul quelqu'un du métier sait dire quand elle ne
s'applique pas.

## Authoritativeness — la reconnaissance (10 pts)

C'est le seul des quatre qui ne se construit pas depuis votre site.

| Signal | Pts |
|--------|-----|
| Citations et mentions sur des sources externes reconnues | 3 |
| Backlinks depuis des sites d'autorité du domaine | 3 |
| Entité identifiée : Wikipedia, Wikidata, base de connaissances | 2 |
| Présence dans la presse, en conférence, en podcast | 2 |

Ces signaux sont aussi ceux que les LLM utilisent le plus. Une entité que
les modèles « connaissent » est une entité citée. Voir `/seo geo`.

## Trustworthiness — la confiance (10 pts)

Le plus important des quatre selon les guidelines de Google : les trois
autres sans celui-ci ne valent rien.

| Signal | Pts |
|--------|-----|
| Coordonnées réelles et vérifiables (adresse, téléphone) | 2 |
| Pages légales complètes | 1 |
| Dates de publication et de dernière mise à jour affichées | 2 |
| Sources citées et liées | 2 |
| HTTPS et sécurité des données | 1 |
| Transparence : affiliations, sponsoring, conflits d'intérêts | 2 |

Sur un e-commerce, ajoutez : politique de retour claire, avis clients
vérifiables, moyens de paiement identifiables. Un site marchand sans adresse
physique déclenche un signal de défiance immédiat chez les évaluateurs.

## Le verdict

```
E-E-A-T : 24/40  🟡  RÉVISER

  Experience         5/10  🟠  affirmations générales, aucun cas concret
  Expertise          7/10  🟠  bon niveau technique, mais article non signé
  Autorité           4/10  🔴  aucune mention externe, 2 domaines référents
  Confiance          8/10  🟢  solide, manque les dates de mise à jour
```

- **32-40 🟢 PUBLIER** — les signaux sont là
- **20-31 🟡 RÉVISER** — corrections ciblées, la base est saine
- **< 20 🔴 RÉÉCRIRE** — sur un sujet YMYL, cette page ne rankera pas

## Les correctifs, localisés

Toujours dire **où** et **quoi écrire**, jamais « améliorez votre E-E-A-T ».

> **Autorité — 4/10 🔴, priorité 1**
>
> 1. *Ajoutez une signature sous le H1* : « Par [Prénom Nom], [titre],
>    [X] ans dans [domaine] », avec un lien vers une page auteur.
> 2. *Créez la page auteur* : parcours, formations, réalisations, profils
>    LinkedIn et externes, schema `Person` avec `sameAs`.
> 3. *Section « Nos résultats »* : 3 cas clients chiffrés, avec le contexte
>    de départ, ce qui a été fait, et le résultat mesuré.
> 4. *Hors site* : 2 interventions (podcast sectoriel, article invité,
>    commentaire d'expert dans la presse pro) sur les 90 prochains jours.
>    C'est le seul levier qui déplace vraiment ce score.

## Le socle site (à faire une fois, sert partout)

- Une page « À propos » réelle : histoire, équipe, photos, adresse
- Des pages auteur pour chaque signataire, avec schema `Person`
- Schema `Organization` sur la home, avec `sameAs` vers tous vos profils
- Page contact avec des coordonnées vérifiables
- Pages légales à jour
- Une politique éditoriale, si vous produisez du contenu d'information

Ce socle profite à toutes les pages du site. Faites-le avant d'optimiser
page par page.

## Livrables

- `EEAT-<slug>.md` — scorecard, verdict, top 3 faiblesses
- `CORRECTIFS-EEAT.md` — les textes à ajouter, prêts à coller
- `person.jsonld` / `organization.jsonld` — les schemas d'entité
