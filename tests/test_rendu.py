"""rendu.py : enveloppe, sonde et cache, hors navigateur."""

import sys
import unittest

from _outils import SCRIPTS, DossierIsole

sys.path.insert(0, str(SCRIPTS))
import rendu  # noqa: E402


class TestEnveloppe(unittest.TestCase):
    def test_fragment_enveloppe_avec_sonde(self):
        doc = rendu.envelopper('<div class="dcp-page"><h1>Titre</h1></div>')
        self.assertTrue(doc.startswith("<!doctype html>"))
        self.assertIn('<meta charset="utf-8">', doc)
        self.assertIn("SONDE", doc)
        self.assertIn('<div class="dcp-page">', doc)

    def test_page_complete_sonde_dans_le_head(self):
        doc = rendu.envelopper("<html><head><title>x</title></head><body>y</body></html>")
        self.assertEqual(doc.count("<html"), 1)
        self.assertLess(doc.index("SONDE"), doc.index("</head>"))

    def test_page_sans_head(self):
        doc = rendu.envelopper("<html lang='fr'><body>y</body></html>")
        self.assertIn("<head><script>", doc)


class TestSonde(unittest.TestCase):
    def test_lecture_ok_et_debordement(self):
        ok = '<div id="SONDE" data-v="390" data-s="390" data-n="0" data-h="5000" data-q="" style="display: none;"></div>'
        self.assertTrue(rendu.lire_sonde(ok)["ok"])
        ko = ('<div id="SONDE" data-v="390" data-s="405" data-n="2" data-h="5000" '
              'data-q="IMG.photo right=2000 w=2000 || DIV.bande right=405 w=405"></div>')
        mesure = rendu.lire_sonde(ko)
        self.assertFalse(mesure["ok"])
        self.assertEqual(len(mesure["coupables"]), 2)

    def test_sonde_absente(self):
        self.assertIsNone(rendu.lire_sonde("<html></html>"))
        self.assertIsNone(rendu.lire_sonde(None))


class TestCache(DossierIsole):
    def test_images_et_polices_locales(self):
        self.ecrire("loc/photo.jpg", "x")
        self.ecrire("loc/fonts.css", "@font-face{font-family:Inter}")
        html = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter">'
                '<img src="https://exemple.com/wp-content/photo.jpg?v=2"><img src="https://exemple.com/absente.png">')
        sortie, manquantes = rendu.localiser(html, str(self.dossier / "loc"))
        self.assertIn("file://", sortie)
        self.assertIn("@font-face", sortie)
        self.assertNotIn("googleapis", sortie)
        self.assertEqual(manquantes, ["absente.png"])

    def test_sans_cache(self):
        self.assertEqual(rendu.localiser("<p>x</p>", None), ("<p>x</p>", []))

    def test_chrome_explicite(self):
        faux = self.ecrire("chrome", "")
        self.assertEqual(rendu.trouver_chrome(str(faux)), str(faux))


if __name__ == "__main__":
    unittest.main()
