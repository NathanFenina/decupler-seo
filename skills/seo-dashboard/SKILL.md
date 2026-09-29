---
name: seo-dashboard
description: >
  Génère un tableau de bord SEO en HTML autonome : KPI, évolutions, roadmap,
  pipeline de leads, score GEO, pages à travailler — un seul fichier, sans
  dépendance, publiable en artifact ou partageable par email. Déclencher sur
  "dashboard", "tableau de bord", "visualiser mes données", "rapport visuel",
  "graphique SEO", "vue d'ensemble", "présenter les résultats", "artifact".
---

# Tableau de bord — voir l'état du SEO en dix secondes

Un rapport se lit. Un tableau de bord se regarde. Les deux sont utiles à des
moments différents : le rapport explique, le tableau de bord alerte.

## Contraintes

1. **Un seul fichier HTML.** Pas de CDN, pas de bibliothèque de graphiques,
   pas d'appel réseau. Il doit s'ouvrir depuis une pièce jointe, sur un
   ordinateur hors ligne, dans trois ans.
2. **Graphiques en SVG inline**, générés à la main. C'est largement suffisant
   pour des courbes et des barres, et ça ne casse jamais.
3. **Lisible en clair et en sombre** — définissez la palette claire sur
   `:root`, la sombre sous `@media (prefers-color-scheme: dark)`.
4. **Responsive** sans point de rupture complexe : `clamp()`, `grid` avec
   `auto-fit`.
5. **Imprimable** — une feuille `@media print` correcte, parce que quelqu'un
   l'imprimera pour un comité de direction.

## La structure

### Bandeau de KPI
4 à 6 tuiles, pas plus. Par tuile : la valeur actuelle en grand, la
variation avec sa flèche et sa couleur, et la période de comparaison en
petit.

```
┌──────────────────┐  ┌──────────────────┐
│ CLICS ORGANIQUES │  │  CONVERSIONS     │
│      4 210       │  │       47         │
│  ▲ +18 % vs M-1  │  │  ▲ +12 % vs M-1  │
└──────────────────┘  └──────────────────┘
```

Le choix des KPI dépend du destinataire — voir `seo-reporting`. Pour un
dirigeant, mettez les leads en premier, pas les impressions.

### Courbes d'évolution
Clics et impressions sur 12 mois. Deux séries, deux axes. Marquez les
événements sur la courbe (publications importantes, core updates,
migrations) : c'est ce qui rend un graphique explicatif au lieu de
décoratif.

### Pages à travailler
Un tableau des 10 pages en position 5-20 avec le plus d'impressions, et le
gain estimé pour chacune. C'est la partie actionnable.

### Roadmap
Les 8 prochaines actions, avec impact, effort et statut. Un rappel visuel
de ce qui est en cours.

### Score GEO
Le share of model par moteur, en barres horizontales, avec la variation par
rapport au mois précédent.

### Pipeline de leads
Si GA4 et la base Notion sont branchés : nombre de leads, valeur, et
répartition par page d'entrée.

## Les couleurs

Suivez une logique de sens, pas d'esthétique :

- **Vert** : au-dessus de l'objectif, ou en progression
- **Orange** : dans les temps, à surveiller
- **Rouge** : en retard, ou en régression
- **Neutre** : informatif, sans jugement

Vérifiez le contraste (4,5:1 minimum) et ne codez jamais une information
**uniquement** par la couleur : ajoutez une flèche, un signe, un mot. Une
partie de vos lecteurs ne distingue pas le rouge du vert.

## Publier

Le fichier peut être :
- ouvert localement
- envoyé en pièce jointe
- publié en **artifact** — une page privée avec une URL partageable, ce qui
  est le plus pratique pour un client

Pour l'artifact, chargez la compétence de design d'artifact avant de
générer, et déclarez les capacités nécessaires si le tableau de bord doit
lire des données en direct ou mémoriser un état.

## Mettre à jour

Régénérez avec les données du mois. Gardez le même nom de fichier et la
même URL d'artifact : le destinataire garde son lien.

```
/loop 30d /seo dashboard
```

## Une précision honnête

Un tableau de bord ne remplace pas Looker Studio ou une vraie solution de
BI si vous avez besoin de filtres dynamiques et de données en temps réel.
Il remplace avantageusement le PowerPoint mensuel qu'on refait à la main :
c'est un instantané, propre, autonome, produit en une minute.

## Livrables

- `dashboard-AAAA-MM.html` — le fichier autonome
- L'URL de l'artifact, si publié
- `dashboard-donnees.json` — les données, pour régénérer sans tout recollecter
