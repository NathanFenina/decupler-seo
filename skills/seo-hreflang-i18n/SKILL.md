---
name: seo-hreflang-i18n
description: >
  Audite et génère le balisage hreflang pour les sites multilingues ou
  multi-pays : validation des liens retour, x-default, codes langue/région,
  choix de l'architecture (ccTLD, sous-domaine, sous-dossier), diagnostic des
  erreurs GSC. Déclencher sur "hreflang", "multilingue", "international",
  "plusieurs langues", "site en plusieurs pays", "x-default", "traduction
  SEO", "version anglaise de mon site", "SEO international".
---

# Hreflang et SEO international

Le hreflang ne fait pas ranker. Il dit à Google **quelle version montrer à
qui**. Mal fait, il fait apparaître la version espagnole aux Français.

C'est l'un des sujets les plus mal implémentés du SEO, parce qu'une seule
règle mal comprise casse l'ensemble.

## Étape 0 — Le bon choix d'architecture

| Architecture | Exemple | Pour | Contre |
|--------------|---------|------|--------|
| **ccTLD** | `exemple.fr`, `exemple.de` | Signal géographique le plus fort, confiance locale | Autorité à construire pour chaque domaine, coût élevé |
| **Sous-domaine** | `fr.exemple.com` | Séparation nette, hébergement distinct possible | Autorité partiellement séparée |
| **Sous-dossier** | `exemple.com/fr/` | **Autorité mutualisée** — le meilleur défaut | Signal géographique plus faible |

Dans la grande majorité des cas : **sous-dossier**. Un seul domaine à
renforcer, une seule autorité. Les ccTLD ne se justifient que si vous avez
des équipes et des budgets par pays.

À éviter absolument : les paramètres d'URL (`?lang=fr`) et la détection
automatique par IP avec redirection forcée. La redirection automatique
empêche Googlebot — qui crawle depuis les États-Unis — de voir vos autres
versions.

## Les 4 règles du hreflang

### 1. Auto-référence obligatoire
Chaque page se déclare elle-même dans sa propre liste. Une page qui liste
ses alternatives sans se lister est ignorée.

### 2. Réciprocité obligatoire
Si A déclare B, alors B **doit** déclarer A. Un lien retour manquant
invalide la paire entière. C'est l'erreur numéro un.

### 3. URL absolues
Toujours. Avec le protocole et le domaine complet.

### 4. Cohérence avec canonical
La canonical de chaque page pointe vers **elle-même**, jamais vers une
autre version linguistique. Une canonical cross-langue annule le hreflang :
vous dites à Google « ces pages sont la même », donc il n'en garde qu'une.

C'est la deuxième erreur la plus fréquente, et la plus coûteuse.

## Les codes

- **Langue** : ISO 639-1, deux lettres — `fr`, `en`, `de`
- **Région** : ISO 3166-1 alpha-2, en option, majuscules — `FR`, `BE`, `CA`
- **Format** : `fr` ou `fr-BE`. Jamais de région seule.

| ❌ Erreur | ✅ Correct | Pourquoi |
|-----------|-----------|----------|
| `fr-FRA` | `fr-FR` | Alpha-2, pas alpha-3 |
| `en-UK` | `en-GB` | Le code du Royaume-Uni est GB |
| `BE` | `fr-BE` ou `nl-BE` | La région seule n'existe pas |
| `fr_FR` | `fr-FR` | Tiret, pas underscore |
| `zh-CN` (pour du traditionnel) | `zh-Hant` | Le script prime sur la région |

## x-default

Indique la page pour les visiteurs dont la langue n'est pas couverte.
Mettez-y le sélecteur de langue, ou la version internationale par défaut.
Un seul par groupe. Fortement recommandé, souvent oublié.

## Les 3 emplacements possibles

**HTML `<head>`** — le plus courant, le plus simple à déboguer :
```html
<link rel="alternate" hreflang="fr-FR" href="https://exemple.com/fr/page" />
<link rel="alternate" hreflang="en-US" href="https://exemple.com/en/page" />
<link rel="alternate" hreflang="x-default" href="https://exemple.com/" />
```

**En-têtes HTTP** — pour les PDF et fichiers non HTML.

**Sitemap XML** — recommandé au-delà de quelques centaines de pages : plus
facile à maintenir, et ça n'alourdit pas chaque page.

Un seul emplacement à la fois. Deux implémentations concurrentes se
contredisent.

## L'audit

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/hreflang_check.py" <url> --recursif
```

Vérifie : auto-référence, réciprocité, codes valides, URL absolues,
accessibilité de chaque cible (pas de 404 ni de 301), présence du x-default,
cohérence des canonicals, absence de doublon.

Puis Search Console → Ciblage international, qui remonte les erreurs
constatées en production.

## Au-delà du hreflang

Le balisage n'est que la plomberie. Ce qui fait le SEO international :

- **Traduire, pas dupliquer.** Une traduction automatique non relue est du
  contenu de faible qualité, avec les conséquences habituelles.
- **Adapter les mots-clés.** Ce ne sont pas des traductions littérales : les
  Québécois et les Français ne cherchent pas avec les mêmes mots.
- **Localiser réellement** : devise, unités, format de date, coordonnées
  locales, exemples culturellement pertinents, mentions légales du pays.
- **Contenu unique par marché** quand le marché diffère. Deux pages
  identiques en `en-US` et `en-GB` n'apportent rien à personne.
- **Ne jamais rediriger automatiquement par IP.** Proposez, ne forcez pas —
  avec une bannière discrète et un choix mémorisé.

## Livrables

- `HREFLANG-AUDIT.md` — erreurs par page, sévérité, correctifs
- `hreflang.html` — les balises générées, par page
- `sitemap-hreflang.xml` — si implémentation par sitemap
- `matrice-langues.csv` — la carte complète des correspondances
