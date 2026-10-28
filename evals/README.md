# Évaluations des skills

Cas joués par `claude plugin eval` (Claude Code ≥ 2.1.269) : chaque cas est
lancé 3 fois avec le plugin et 3 fois sans, et le rapport donne le score des
deux bras et l'écart (Δ). Deux graders par cas : le skill attendu s'est-il
déclenché (`tool_used: Skill`), et le résultat est-il juste. Certains cas
vérifient qu'un skill ne se déclenche **pas** (`min: 0`, `max: 0`,
`arm: both`).

Deux familles : les cas **durcis** (règles propres à la méthode, avec
comparaison à Claude seul) et les cas **couverture** (`couv-*`, tag
`couverture`) : un par skill, qui vérifient qu'il se déclenche et livre
quelque chose d'utile même sans projet configuré ni données.

Le coût affiché est une estimation au tarif public de l'API ; avec un
abonnement Claude, il ne se paie pas en euros mais consomme le quota d'usage.

```bash
claude plugin eval . --runs 1 --ablation none --max-cost-usd 8 -j 6   # toute la suite, une fois
claude plugin eval . --tag couverture --runs 1 --ablation none        # couverture seule
claude plugin eval . --case onpage-* --runs 1 --ablation none   # itérer vite
```

À chaque nouvelle règle importante ou nouveau skill : un cas de plus. Un
skill dont le Δ reste nul n'apporte rien au modèle : à fusionner ou à
retirer.
