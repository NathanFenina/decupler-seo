---
name: seo-pilotage-notion
description: >
  Crée et alimente dans Notion les 5 bases de pilotage d'une activité SEO :
  Leads & Prospects, Objectifs & KPI, Roadmap SEO, Briefs & Contenus,
  Backlinks. Connecte Notion, crée les bases avec leurs propriétés et leurs
  vues, puis les met à jour automatiquement à chaque action. Déclencher sur
  "Notion", "connecter Notion", "pilotage", "tracking de leads", "roadmap",
  "objectifs", "suivi de projet", "base de données SEO", "tableau de bord
  Notion", "où je suis dans mon SEO".
---

# Pilotage Notion — la mémoire du dispositif

Sans mémoire persistante, chaque session repart de zéro. Notion est ici le
cerveau : ce qu'on vise, ce qu'on a fait, ce que ça a donné, et qui ça a
amené.

## 1. Connecter Notion

**Méthode recommandée — le connecteur natif.**
Réglages Claude → Connecteurs → Notion → autoriser. Aucune clé, aucun
fichier. Il faut ensuite **partager les pages** avec l'intégration :
sur la page Notion → Partager → inviter Claude.

**Méthode alternative — intégration interne.**
1. https://www.notion.so/my-integrations → New integration
2. Capacités : lecture, écriture, insertion de contenu
3. Copier le token dans `.env` : `NOTION_TOKEN=secret_…`
4. Sur la page Notion qui accueillera les bases : « ••• » → Connexions →
   ajouter votre intégration

⚠️ Sans le partage explicite de la page, l'API renvoie « object not found »
même avec un token valide. C'est la cause de 90 % des échecs de connexion.

## 2. Créer les bases

Demandez la page parente, puis créez les 5 bases dedans. Ne créez rien sans
avoir demandé où.

---

### Base 1 · Leads & Prospects
*À quoi sert tout ce travail.*

| Propriété | Type | Options |
|-----------|------|---------|
| Nom | Titre | |
| Entreprise | Texte | |
| Email | Email | |
| Téléphone | Téléphone | |
| Source | Sélection | Organique, IA (ChatGPT/Perplexity), Direct, Référent, Social, Publicité |
| **Page d'entrée** | URL | La page SEO qui a amené le lead |
| **Requête** | Texte | La requête d'entrée, si connue |
| Statut | Sélection | Nouveau, Contacté, Qualifié, Proposition, Gagné, Perdu |
| Valeur estimée | Nombre (€) | |
| Date de création | Date | |
| Date de closing | Date | |
| Notes | Texte long | |

**Vues** : Pipeline (tableau kanban par statut) · Par page d'entrée (groupé,
somme des valeurs) · Ce mois-ci · Gagnés (avec la somme)

C'est la base qui permet de dire « la page /guide-x a généré 14 leads et
32 000 € cette année ». Ce chiffre change la conversation avec un dirigeant.

---

### Base 2 · Objectifs & KPI
*Où on va, et où on en est.*

| Propriété | Type | Options |
|-----------|------|---------|
| Indicateur | Titre | |
| Catégorie | Sélection | Trafic, Positions, Conversions, Autorité, GEO, Technique |
| Valeur de départ | Nombre | |
| Valeur actuelle | Nombre | |
| Objectif | Nombre | |
| **Progression** | Formule | `(actuelle − départ) / (objectif − départ)` |
| Échéance | Date | |
| Statut | Formule | 🟢 en avance · 🟠 dans les temps · 🔴 en retard |
| Fréquence de relevé | Sélection | Hebdo, Mensuel, Trimestriel |
| Dernier relevé | Date | |
| Responsable | Personne | |

Indicateurs de départ suggérés : clics organiques mensuels · impressions ·
position moyenne top 20 · pages indexées · domaines référents · score GEO ·
share of model · conversions organiques · Core Web Vitals au vert.

**Vues** : Tableau de bord (toutes catégories) · En retard · À relever cette
semaine

---

### Base 3 · Roadmap SEO
*Ce qu'on fait, dans quel ordre.*

| Propriété | Type | Options |
|-----------|------|---------|
| Action | Titre | |
| Type | Sélection | Technique, Contenu, Netlinking, GEO, Local, Analyse |
| Impact estimé | Sélection | 🔴 Critique, 🟠 Fort, 🟡 Moyen, ⚪ Faible |
| Effort | Sélection | XS (<1h), S (½j), M (1-2j), L (1 sem), XL (+) |
| **Priorité** | Formule | Impact ÷ Effort |
| Statut | Sélection | À faire, En cours, En attente, Terminé, Abandonné |
| URL concernée | URL | |
| Gain estimé | Nombre | clics/mois ou € |
| Date de réalisation | Date | |
| **Date de mesure** | Date | réalisation + 30 j |
| Résultat mesuré | Texte | |
| Skill utilisé | Texte | ex. `seo-quick-wins` |

**Vues** : Prochaines actions (trié par priorité) · En cours · À mesurer
(date de mesure passée, résultat vide) · Terminé ce trimestre

La vue **« À mesurer »** est la plus importante et celle que tout le monde
oublie. Sans elle, on ne sait jamais ce qui a marché.

---

### Base 4 · Briefs & Contenus
*Le pipeline éditorial.*

| Propriété | Type | Options |
|-----------|------|---------|
| Titre | Titre | |
| Mot-clé cible | Texte | |
| Volume | Nombre | |
| Difficulté | Nombre | |
| Intention | Sélection | Informationnelle, Commerciale, Transactionnelle |
| Silo | Relation → Roadmap | |
| Statut | Sélection | Idée, Brief fait, En rédaction, En relecture, Publié, À mettre à jour |
| URL publiée | URL | |
| Date de publication | Date | |
| Score on-page | Nombre | le /100 de `seo-optimisation-onpage` |
| Position à J+30 | Nombre | |
| Position actuelle | Nombre | |
| Clics/mois | Nombre | |
| Auteur | Personne | |

**Vues** : Pipeline éditorial (kanban) · Calendrier (par date de publication) ·
Performances (publiés, triés par clics) · À rafraîchir (publiés il y a plus
de 12 mois)

---

### Base 5 · Backlinks
*L'autorité, ligne par ligne.*

| Propriété | Type | Options |
|-----------|------|---------|
| Domaine | Titre | |
| URL du lien | URL | |
| Page cible | URL | |
| Ancre | Texte | |
| Autorité (DR) | Nombre | |
| Trafic du domaine | Nombre | |
| Score de qualification | Nombre | /20 |
| Type | Sélection | Éditorial, Article invité, Mention non liée, Annuaire, Partenaire, PR |
| Statut | Sélection | Prospect, Contacté, Relancé, Obtenu, Refusé, Perdu |
| Date de contact | Date | |
| Date d'obtention | Date | |
| Dofollow | Case à cocher | |

**Vues** : Prospection (kanban par statut) · Liens obtenus · Liens perdus
(à réclamer) · Par page cible

---

## 3. Alimenter automatiquement

C'est ce qui fait la différence entre un Notion vivant et un Notion mort au
bout de trois semaines. Chaque skill écrit dans sa base :

| Skill | Écrit dans |
|-------|-----------|
| `seo-audit-360` | Roadmap — une ligne par correctif, avec impact et effort |
| `seo-quick-wins` | Roadmap — une ligne par page, avec la position de départ |
| `seo-brief` | Briefs & Contenus — statut « Brief fait » |
| `seo-redaction` | Briefs & Contenus — statut « En relecture » |
| `seo-publication-cms` | Briefs & Contenus — statut « Publié », URL, date |
| `seo-netlinking` | Backlinks — les prospects qualifiés |
| `seo-reporting` | Objectifs & KPI — les valeurs du mois |
| `geo-share-of-model` | Objectifs & KPI — le score GEO |

Règle : **ne jamais écraser une note humaine.** Complétez les champs
automatiques, laissez les champs de commentaire intacts.

## 4. La page de synthèse

Créez une page « Tableau de bord SEO » qui rassemble en vues liées :

- Les 5 objectifs les plus en retard
- Les 10 prochaines actions de la roadmap, triées par priorité
- Le pipeline éditorial de la semaine
- Les leads du mois, avec leur somme
- Les actions à mesurer

C'est la page qu'on ouvre le lundi matin. Si elle demande plus de trois
minutes à lire, elle est trop chargée.

## 5. Si Notion n'est pas branché

Ne bloquez pas. Produisez les mêmes structures en CSV dans
`seo-output/pilotage/`, importables dans Notion, Airtable ou un tableur.
Le dispositif fonctionne sans Notion — il est simplement moins agréable.

## Livrables

- Les 5 bases créées, avec leurs propriétés et leurs vues
- La page de synthèse
- `NOTION-IDS.json` — les identifiants des bases, pour les écritures futures
- `pilotage/*.csv` — le repli sans Notion
