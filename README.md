# Claude Code SEO Décupler

**La machine de guerre SEO + GEO pour Claude Code.**
43 skills, 15 agents spécialisés, 13 MCP préconfigurés. Ça audite, ça corrige,
ça rédige, ça publie, ça mesure — en autonomie.

[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-blue)](https://claude.ai/claude-code)
[![Licence MIT](https://img.shields.io/badge/Licence-MIT-yellow.svg)](LICENSE)
[![Français](https://img.shields.io/badge/Langue-Français-red.svg)](#)

---

## Le problème

Le SEO en 2026, ce n'est plus « écrire un article optimisé ». C'est croiser
Search Console, la SERP live, les concurrents, les moteurs IA, corriger la
technique, produire le contenu, le publier, et mesurer. Sept outils, quatre
onglets, trois heures pour une tâche qui devrait en prendre dix minutes.

Ce dépôt branche tout ça dans Claude Code et enchaîne les étapes tout seul.

| Tâche | À la main | Ici |
|-------|-----------|-----|
| Quick wins du mois | ~2 h | 6 min |
| Brief adossé à la SERP | ~1 h 30 | 4 min |
| Article + visuels + publication | ~4 h | 9 min |
| Mesure de visibilité IA | ~2 h | 5 min |
| Rapport mensuel | ~3 h | 3 min |

---

## Installation

### Option 1 — Plugin Claude Code (recommandé)

```
/plugin marketplace add NathanFenina/decupler-seo
/plugin install decupler-seo@decupler
```

Skills, agents, commandes et MCP sont branchés d'un coup.

### Option 2 — Script d'installation

```bash
curl -fsSL https://raw.githubusercontent.com/NathanFenina/decupler-seo/main/install.sh | bash
```

Windows :
```powershell
irm https://raw.githubusercontent.com/NathanFenina/decupler-seo/main/install.ps1 | iex
```

### Option 3 — Manuelle

```bash
git clone https://github.com/NathanFenina/decupler-seo.git
cd decupler-seo
./install.sh
```

### Puis, dans Claude Code

```
/seo doctor
```

Il vous dit ce qui est branché, ce qui manque, ce que ça coûte, et il lance
la première action utile. **Vous n'avez rien à lire d'autre pour démarrer.**

---

## Deux façons de l'utiliser

| | **Plugin** | **Projet** |
|---|---|---|
| Pour | travailler avec Claude, en direct | laisser tourner des routines sans vous |
| Mise en place | `/plugin install` | un dépôt privé par site : `projet.py init` |
| Mémoire du site | — | `CLAUDE.md` + `memoire/` |
| Tourne dans une routine | non | **oui** |

Une routine Claude Code ne charge pas les plugins : elle ne voit que ce qui
est commité dans le dépôt qu'elle clone. Pour piloter un site en autonomie,
créez-lui un projet — dites « nouveau projet » à Claude, ou lisez
[docs/PROJETS.md](docs/PROJETS.md).

---

## Ce que ça sait faire

### Les 5 chaînes agentiques

**1. Quick wins** — `/seo quickwins` *(≈ 6 min)*
Search Console → repère les pages en position 4-20 → SERP live → scrape le
top 3 → identifie l'écart éditorial → écrit les sections manquantes et les
nouvelles balises → met à jour la page.

**2. Brief adossé à la SERP** — `/seo brief <mot-clé>` *(≈ 4 min)*
Expansion sémantique → volumes → SERP live → intention réelle → plans Hn des
5 premiers → brief complet avec la réponse directe et la FAQ déjà rédigées →
journalisé dans Notion.

**3. Article vérifié** — `/seo article` *(≈ 9 min)*
Lit le brief → recherche obligatoire → rédige (style humain, zéro chiffre
inventé) → génère le schema → vérifie le rendu dans un navigateur réel →
publie en brouillon.

**4. Score de visibilité IA** — `/seo geo` *(≈ 5 min)*
Pose 20 questions d'acheteur aux moteurs IA → relève qui est cité et dans
quel ordre → calcule votre part de voix → compare aux concurrents →
feuille de route 90 jours.

**5. Rapport mensuel** — `/seo rapport` *(≈ 3 min)*
Search Console + GA4 + positions + score GEO → évolutions M-1 et M-12 →
**les causes**, pas seulement les courbes → ce qui a marché, ce qui n'a pas
marché → les priorités du mois suivant.

### Et aussi

- **Corrige la technique tout seul** — robots.txt, canonicals, redirections,
  balises, images, Core Web Vitals. Il détecte, il patche, il vérifie.
- **Construit des pages HTML** prêtes à coller dans Elementor, Webflow ou
  WordPress. Autonomes, responsive, accessibles.
- **Génère des pages à l'échelle** avec des garde-fous durs contre le contenu
  mince (blocage à 500 pages sans audit qualité).
- **Pilote le netlinking** — prospection, qualification sur 20 points,
  emails rédigés, suivi des liens perdus.
- **Tient votre Notion à jour** — leads, objectifs, roadmap, contenus,
  backlinks. Alimenté automatiquement à chaque action.

---

## Les commandes

| Commande | Ce qu'elle fait |
|----------|-----------------|
| `/seo doctor` | Diagnostic, onboarding, première action |
| `/seo audit <url>` | Audit complet, 8 agents en parallèle, score /100 |
| `/seo quickwins` | Les pages à rattraper, chiffrées |
| `/seo fix <url>` | Détecte **et corrige** les problèmes techniques |
| `/seo brief <mot-clé>` | Brief rédactionnel complet |
| `/seo article` | Rédaction, style humain, sources vérifiées |
| `/seo onpage <url> <mot-clé>` | Note /100 **puis réécrit** |
| `/seo page <type> <sujet>` | Page HTML prête à coller |
| `/seo geo <url>` | Visibilité dans les moteurs IA |
| `/seo backlink <url>` | Campagne de netlinking |
| `/seo publish` | Publication WordPress / Webflow |
| `/seo rapport` | Rapport périodique |
| `/seo notion setup` | Les 5 bases de pilotage |
| `/seo veille` | Surveillance et alertes |

Le routeur `/seo` comprend aussi le langage naturel : « audite mon site »,
« pourquoi ChatGPT ne me cite pas », « j'ai perdu du trafic ».

---

## Les 43 skills

<details>
<summary><b>Diagnostic et technique</b> (8)</summary>

`seo-onboarding` · `seo-audit-360` · `seo-technique-autofix` ·
`seo-crawl-architecture` · `seo-core-web-vitals` · `seo-indexation` ·
`seo-migration` · `seo-veille`
</details>

<details>
<summary><b>Recherche et stratégie</b> (6)</summary>

`seo-quick-wins` · `seo-keyword-research` · `seo-competitor-gap` · `seo-cocon-semantique` ·
`seo-serp-analysis` · `seo-traffic-drop`
</details>

<details>
<summary><b>Contenu</b> (7)</summary>

`seo-brief` · `seo-redaction` · `seo-optimisation-onpage` · `seo-meta-serp` ·
`seo-faq-paa` · `seo-eeat` · `seo-comparatifs`
</details>

<details>
<summary><b>Structure et échelle</b> (6)</summary>

`seo-page-builder-html` · `seo-programmatique` · `seo-maillage-interne` ·
`seo-schema-jsonld` · `seo-hreflang-i18n` · `seo-images`
</details>

<details>
<summary><b>GEO / moteurs IA</b> (4)</summary>

`geo-visibilite-ia` · `geo-citation-tracker` · `geo-llms-txt` ·
`geo-share-of-model`
</details>

<details>
<summary><b>Autorité et acquisition</b> (4)</summary>

`seo-netlinking` · `seo-reddit-communautes` · `seo-local` · `seo-digital-pr`
</details>

<details>
<summary><b>Production et pilotage</b> (8)</summary>

`seo-nouveau-projet` · `seo-cycle` · `seo-journal-mesure` ·
`seo-publication-cms` · `seo-pilotage-notion` · `seo-reporting` ·
`seo-dashboard` · `seo-ecommerce`
</details>

Détail complet : [docs/SKILLS.md](docs/SKILLS.md)

---

## Les 13 MCP

Tous préconfigurés dans `.mcp.json`. **Aucun n'est obligatoire** : les skills
s'adaptent à ce qui est branché et vous disent ce qui manque.

| Niveau | Outils | Coût |
|--------|--------|------|
| **1 — le socle** | Search Console · GA4 · Chrome DevTools | gratuit |
| **2 — la donnée marché** | Firecrawl · DataForSEO · Ubersuggest | gratuit à quelques € |
| **3 — production** | WordPress · Webflow · Notion · Semrush · Ahrefs | variable |
| **4 — visibilité IA** | Perplexity · Reddit | quelques € |

**Les trois premiers sont gratuits et couvrent 70 % de la valeur.**
Guide de branchement : [docs/MCP.md](docs/MCP.md)

---

## Les 15 agents

`seo-technique` · `seo-performance` · `seo-contenu` · `seo-redacteur` ·
`seo-data` · `seo-serp` · `seo-schema` · `seo-geo` · `seo-netlinking` ·
`seo-frontend` · `seo-crawler` · `seo-strategiste` · `seo-publisher` ·
`seo-analyste-concurrence` · `seo-manager`

Ils tournent **en parallèle** sur un audit : huit spécialistes plutôt qu'un
généraliste qui passe huit fois.

---

## Mode autonome et kill-switch

Par défaut, le dispositif est en **mode autonome** : il écrit, il publie, il
corrige. Trois façons de l'arrêter :

```bash
# 1 · la variable d'environnement — gagne toujours
SEO_SAFE_MODE=1

# 2 · le flag, sur n'importe quelle commande
/seo fix https://exemple.com --safe

# 3 · la config
mode: safe        # dans ./decupler-seo.config.yml du projet
```

Ou dites simplement à Claude : « passe en safe mode ».

### Les garde-fous qui ne se désactivent pas

Ils existent parce que chacun correspond à une façon connue de se faire mal.

- ❌ **Jamais de suppression de contenu.** Dépublier, oui. Supprimer, non.
- ❌ **Jamais de post sur un forum ou de mail d'outreach sans validation.**
  Le compte banni serait le vôtre.
- ❌ **Jamais d'écriture sur un domaine non déclaré.**
- ❌ **Jamais plus de 500 pages générées** sans audit qualité d'un échantillon.
- ✅ **Sauvegarde systématique** avant toute écriture, avec restauration en
  une commande.
- ✅ **Diff obligatoire** sur robots.txt, redirections et canonicals.
- ✅ **Jamais de chiffre inventé.** Donnée absente = « nécessite tel outil ».

---

## Configuration

```bash
cp config/.env.example .env      # vos clés, dans le dossier du projet — jamais commité
```

Puis copiez `config/decupler-seo.config.yml` à la racine du projet et remplissez
la section `projet` : domaine,
proposition de valeur, concurrents, pages prioritaires, ton. Une fois pour
toutes — tous les skills s'en servent et arrêtent de vous poser les mêmes
questions.

---

## Prérequis

- **Claude Code** (CLI, desktop, web ou extension IDE)
- **Node** — pour les MCP en npx
- **Python 3.8+** — pour les scripts d'analyse
- **Chrome** — optionnel, pour les Core Web Vitals réels

```bash
pip install -r requirements.txt
```

---

## Documentation

- [Installation](docs/INSTALLATION.md) — les trois méthodes, pas à pas
- [Branchement des MCP](docs/MCP.md) — Search Console, GA4, et les 11 autres
- [Les skills](docs/SKILLS.md) — ce que fait chacun, quand l'utiliser
- [Les agents](docs/AGENTS.md)
- [Piloter des projets en autonomie](docs/PROJETS.md) — mémoire, routines, mesure
- [Les workflows](docs/WORKFLOWS.md) — les 5 chaînes, détaillées
- [Sécurité et garde-fous](docs/SECURITE.md)
- [Dépannage](docs/DEPANNAGE.md)

---

## Ce que ça ne fait pas

Par honnêteté, et pour vous éviter d'être déçu :

- **Ça ne remplace pas un stratège SEO.** Ça exécute vite et bien, ça
  priorise correctement, mais les arbitrages business restent les vôtres.
- **Ça ne garantit aucun résultat.** Personne ne le peut. Ça fait le travail
  correctement, ce qui est déjà la partie difficile.
- **Ça ne triche pas.** Pas de génération de contenu vide à l'échelle, pas de
  spam de forums, pas de faux avis. Les garde-fous sont là pour ça.
- **Ça n'invente pas de chiffres.** Si la donnée manque, il le dit.

---

## Licence

MIT — voir [LICENSE](LICENSE). Faites-en ce que vous voulez.

---

## Contribuer

Les contributions sont bienvenues : un nouveau skill, un MCP supplémentaire,
une correction. Voir [CONTRIBUTING.md](CONTRIBUTING.md).

---

<div align="center">

**Construit par [Décupler](https://decupler.com)** — agence SEO & GEO

[decupler.com](https://decupler.com) · [Nathan Fenina](https://www.linkedin.com/in/nathanfenina/)

</div>
