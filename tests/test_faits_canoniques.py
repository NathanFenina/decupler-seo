"""Des affirmations SEO réfutées ou retirées ne doivent pas revenir dans la méthode.

Chaque motif est une erreur déjà corrigée ; s'il réapparaît, c'est qu'une
modification a ramené un fait périmé. Sources : skills/seo-optimisation-onpage/
references/preuves-2026.md.
"""

import re
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DOSSIERS = ["skills", "agents", "commands", "templates", "modele-projet"]
INTERDITS = {
    r"densité cible": "plus de densité cible : méthode par entités, aucun quota",
    r"1,5 ?(?:à|-) ?2,5 ?%": "densité 1,5-2,5 % abandonnée (la densité n'est pas un facteur)",
    r"15 à 20 occurrences": "pas de quota d'occurrences par défaut",
    r"40 à 120 mots": "réponses de FAQ : 40 à 80 mots",
    r"restreint depuis août 2023": "rich results FAQ retirés le 7 mai 2026",
    r"sitelinks search box (?:est|reste) (?:active|disponible)|active la sitelinks": "SearchAction retirée en novembre 2024",
    r"\bFID\b(?! (?:a été|a disparu|was))(?=.*(?:seuil|objectif|cible|< ?100 ?ms))": "FID remplacé par INP",
}


class TestFaitsCanoniques(unittest.TestCase):
    def test_aucune_affirmation_perimee(self):
        trouves = []
        for dossier in DOSSIERS:
            for f in (RACINE / dossier).rglob("*"):
                if f.suffix not in {".md", ".html", ".yml", ".py"} or not f.is_file():
                    continue
                for n, ligne in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                    for motif, raison in INTERDITS.items():
                        if re.search(motif, ligne, re.I):
                            trouves.append(f"{f.relative_to(RACINE)}:{n} — {raison}")
        self.assertEqual(trouves, [], "\n".join(trouves))


if __name__ == "__main__":
    unittest.main()
