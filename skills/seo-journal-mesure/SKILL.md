---
name: seo-journal-mesure
description: >
  Journalise chaque modification SEO publiée avec sa situation de départ,
  la remesure à J+28 contre un groupe témoin, rend un verdict (gain, neutre,
  perte), propose le retour arrière des pertes et tire les apprentissages du
  site. Déclencher après toute publication, et sur "journalise", "mesure",
  "est-ce que ça a marché", "effet de mes modifications", "retour arrière",
  "qu'est-ce qui marche sur ce site", "bilan des optimisations".
---

# Journal et mesure

Automatiser une modification est facile. Savoir si elle a aidé, c'est ce
que presque personne ne fait. Sans ça, une publication automatique n'est
qu'un pari répété chaque semaine.

Le script : `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/journal.py"`, lancé
depuis la racine du projet (il écrit dans `journal/modifications.csv`).

## Le mode automatique — à utiliser dès que Search Console est branché

```bash
# au moment de publier : la situation de départ est relevée toute seule
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/journal.py" ajouter --url <url> --type <type> \
  --avant "<ancienne valeur>" --apres "<nouvelle valeur>" --auto

# chaque mois : toutes les échéances, témoin compris
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/journal.py" mesurer-tout --auto
```

Les chiffres viennent de `gsc.py` (compte de service `GSC_SA_JSON` ou
`GSC_CREDENTIALS_JSON`, propriété `GSC_SITE_URL`). Le témoin est calculé en
excluant toutes les pages modifiées dans la période, et il est **écarté** s'il
repose sur moins de 200 clics : sur un petit site, 20 → 50 clics fait +150 %,
ce qui fausserait tous les verdicts. Le mode manuel ci-dessous reste la
référence quand Search Console n'est pas accessible.

## 1. Journaliser — au moment de publier

**Avant** de publier, relevez dans Search Console les 28 derniers jours de
la page : clics, impressions, position moyenne, CTR. Puis :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/journal.py" ajouter \
  --url <url> --type <title|meta|faq|schema|maillage|contenu|reecriture-section|page-neuve|technique> \
  --requete "<requête principale>" --avant "<ancienne valeur>" --apres "<nouvelle valeur>" \
  --clics <n> --impressions <n> --position <p> --ctr <pct>
```

- `--avant` est ce qui permettra le retour arrière. Pour un title ou une
  meta, la valeur exacte. Pour un contenu, le chemin de la sauvegarde.
- **Une modification par ligne.** Changer le title et la FAQ d'une même page
  le même jour rend impossible de savoir lequel a agi. Si c'est inévitable,
  une seule ligne de type `contenu`, et on l'accepte.
- Une page déjà en cours de mesure ne se modifie pas avant l'échéance.
- **Site en mode `depot`** : la publication, c'est la fusion de la PR. Les
  lignes du journal voyagent dans la PR, datées du jour où elle est ouverte ;
  si elle est fusionnée plus de deux jours après, redater les lignes au jour
  de la fusion, sinon la période « après » mélange l'ancienne et la nouvelle
  version. Le dire dans la description de la PR.

## 2. Mesurer — à l'échéance

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/journal.py" echeances
```

Pour chaque ligne, relevez les **28 derniers jours** de la page — la même
durée qu'au départ, sinon la comparaison ne vaut rien.

**Le groupe témoin.** Calculez la variation des clics, sur les mêmes deux
périodes, de l'ensemble des pages du site **non modifiées** depuis 56 jours.
Si tout le site a pris +12 % (saisonnalité, mise à jour Google), une page à
+15 % n'a gagné que 3 points grâce à la modification. Sans témoin, on
s'attribue le mérite de la météo.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/journal.py" mesurer --id <n> \
  --clics <n> --impressions <n> --position <p> --ctr <pct> --temoin <pct>
```

Le verdict :

| Situation | Critère |
|---|---|
| **insuffisant** | moins de 100 impressions au départ, ou donnée manquante |
| Page à 20 clics ou plus | variation des clics, témoin déduit : **gain** ≥ +10 % · **perte** ≤ −15 % |
| Page à moins de 20 clics | position : **gain** si elle monte de 2 places · **perte** si elle perd 3 places |

Les seuils se règlent dans `decupler-seo.config.yml` → `mesure`.

## 3. Revenir en arrière

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/journal.py" a-annuler
```

Une perte n'est pas annulée automatiquement : elle est **proposée** dans
`rapports/a-valider.md`. Une page peut baisser pour une raison extérieure
que le témoin n'a pas captée (un concurrent qui publie, une feature SERP
nouvelle). Un humain tranche. Un retour arrière validé est lui-même
journalisé.

## 4. Apprendre

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/journal.py" bilan
```

Le bilan ne propose un apprentissage qu'à partir de **3 mesures jugeables
du même type** et d'une majorité nette. Reportez ces lignes, et seulement
elles, dans `memoire/apprentissages.md`, datées, avec les chiffres.

C'est ce fichier qui rend le dispositif meilleur de mois en mois **sur ce
site précis** : si les réécritures de title y échouent quatre fois sur six,
le cycle cesse de les appliquer automatiquement et les passe en validation.

## Ce qu'il faut dire honnêtement au client

La mesure réduit l'incertitude, elle ne la supprime pas. Avec 28 jours et un
témoin, on distingue un vrai effet du bruit dans la plupart des cas — pas
dans tous. Présentez les verdicts comme des indications solides, pas comme
des preuves.
