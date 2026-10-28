# Évaluations des skills

Cas joués par `claude plugin eval` (Claude Code ≥ 2.1.269) : chaque cas est
lancé 3 fois avec le plugin et 3 fois sans, et le rapport donne le score des
deux bras et l'écart (Δ). Deux graders par cas : le skill attendu s'est-il
déclenché (`tool_used: Skill`), et le résultat est-il juste. Certains cas
vérifient qu'un skill ne se déclenche **pas** (`min: 0`, `max: 0`,
`arm: both`).

```bash
claude plugin eval .                        # toute la suite (payant : appels au modèle)
claude plugin eval . --case onpage-* --runs 1 --ablation none   # itérer vite
```

À chaque nouvelle règle importante ou nouveau skill : un cas de plus. Un
skill dont le Δ reste nul n'apporte rien au modèle : à fusionner ou à
retirer.
