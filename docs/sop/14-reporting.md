<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 14 · Reporting

**Skills** : `seo-reporting`, `seo-dashboard`, `seo-pilotage` · **Commande** : `/seo rapport, puis /seo dashboard`

**Objectif** : Un bilan mensuel où chaque chiffre vient d'un script et chaque courbe a sa cause.

**Quand** : Le premier mercredi du mois.

**Dis à Claude** : « Fais le rapport du mois : ce qui a bougé, pourquoi, ce qui n'a pas marché, et les 5 actions du mois prochain. »

## Étapes

1. Le relevé de la cartographie (`cartographie.py mensuel`), puis les chiffres (`rapport.py`) : le mois contre le mois précédent et contre le même mois l'an passé.
2. Les modifications du mois, et le verdict de celles arrivées à J+28, mesurées contre un groupe témoin de pages qui n'ont pas bougé.
3. Claude n'écrit que la section « Lecture et décisions » : les causes, ce qui n'a pas marché, les 5 actions.
4. Le tableau de bord HTML (`/seo dashboard`) ou les bases Notion (`/seo notion`) pour le client.
5. La page de suivi : ce qui attend une décision, ce qui est fait, les wins.

**MCP nécessaires** : Search Console et GA4. Notion en option.

**Livrable** : `rapports/<mois>.md`, le tableau de bord et la page de suivi à jour.

## Pièges

- Un chiffre recalculé à la main dans un texte finit faux.
- Comparer seulement au mois précédent. Compare aussi au même mois de l'an passé.
- Appeler « win » une intention. Un win est un fait mesuré.

> Chez nous : Septembre 2026 sur decupler.com : 71 clics sur 4 semaines contre 33 les 4 semaines d'avant, et 1 impression sur les pages de spam du piratage contre 3 308 en mai.
