"""scores_page.py : six notes sur 100 (SEO, AI Search, rédaction, conversion, UX, design)."""

import sys
import unittest

from _outils import SCRIPTS

sys.path.insert(0, str(SCRIPTS))
try:
    from bs4 import BeautifulSoup
    import scores_page as SP  # noqa: E402
except ImportError:  # pragma: no cover
    BeautifulSoup = None

PAGE = """<h1>Audit SEO : ce que tu obtiens</h1>
<p>Un audit SEO dit en une demi-journée ce que ton site doit corriger, dans quel ordre, et ce que chaque
correction peut rapporter. Tu repars avec une liste priorisée, les pages à reprendre et les liens à créer.</p>
<p><a href="/rendez-vous/">Réserver ma consultation</a></p>
<h2>Que contient l'audit ?</h2><ul><li>Technique</li><li>Contenu</li><li>Liens</li></ul>
<h2>Combien de temps faut-il ?</h2><ol><li>Relevé</li><li>Analyse</li><li>Restitution</li></ol>
<table><tr><td>Étape</td><td>Durée</td></tr></table>
<script type="application/ld+json">{"@type":"FAQPage","about":{"@id":"https://exemple.fr/#organization"}}</script>
"""


@unittest.skipIf(BeautifulSoup is None, "beautifulsoup4 absent")
class Notes(unittest.TestCase):
    def test_ai_search_reperes(self):
        note, manques = SP.note_ai_search(BeautifulSoup(PAGE, "html.parser"))
        self.assertGreaterEqual(note, 50)
        self.assertTrue(any("FAQPage" in m for m in manques))  # aucune Question dans le JSON-LD

    def test_design_sans_image(self):
        note, manques = SP.note_design(BeautifulSoup(PAGE, "html.parser"))
        self.assertLess(note, 60)
        self.assertTrue(any("image" in m for m in manques))

    def test_ux_cta_en_haut(self):
        note, manques = SP.note_ux(BeautifulSoup(PAGE, "html.parser"))
        self.assertFalse(any("en haut" in m for m in manques))


if __name__ == "__main__":
    unittest.main()
