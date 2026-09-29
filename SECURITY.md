# Politique de sécurité

## Signaler une vulnérabilité

Ne publiez pas de vulnérabilité dans une issue publique. Utilisez le
signalement privé de GitHub : onglet **Security** du dépôt → **Report a
vulnerability**. Décrivez le script ou le skill concerné, comment reproduire,
et l'impact.

Sont dans le périmètre :
- un contournement des garde-fous (`scripts/guard.py`, kill-switch
  `SEO_SAFE_MODE`, domaines autorisés, actions interdites) ;
- une fuite possible de secret : clé imprimée dans une sortie, écrite dans
  un fichier suivi par Git, envoyée à un service tiers ;
- une requête vers une adresse interne provoquée par une URL fournie
  (`scripts/fetch_page.py` protège contre ce cas) ;
- un fichier de méthode qui écraserait, à la synchronisation, un fichier du
  projet sans le signaler.

## Versions

Seule la dernière version publiée reçoit des correctifs. Mettez à jour le
plugin par `claude plugin update decupler-seo@decupler`, et la méthode embarquée dans un
projet par `python3 .claude/decupler-seo/scripts/projet.py sync .`.

## Pour les utilisateurs

Les garde-fous, le kill-switch et la gestion des clés sont décrits dans
[docs/SECURITE.md](docs/SECURITE.md). En résumé : aucune clé dans un dépôt,
des comptes de service Google en lecture seule, et une branche principale
protégée sur les sites où une fusion déclenche un déploiement.
