"""Indexation : annoncer sans casser quand une brique manque, suivre sans Search Console."""

import csv
import unittest

from _outils import DossierIsole, lancer


class TestIndexation(DossierIsole):
    def test_cle_generee(self):
        r = lancer("indexation.py", "cle", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("INDEXNOW_KEY", r.stdout)

    def test_annoncer_sans_cle_ni_gsc_remplit_le_registre(self):
        r = lancer("indexation.py", "annoncer", "https://www.exemple.com/a/", "https://www.exemple.com/b/",
                   "pas-une-url", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("sans clé", r.stdout)
        self.assertIn("non fait", r.stdout)
        with open(self.dossier / "donnees/indexation.csv", encoding="utf-8") as f:
            lignes = list(csv.DictReader(f))
        self.assertEqual([l["url"] for l in lignes], ["https://www.exemple.com/a/", "https://www.exemple.com/b/"])
        self.assertTrue(all(l["statut"] == "en attente" for l in lignes))

    def test_annoncer_sans_url(self):
        r = lancer("indexation.py", "annoncer", cwd=self.dossier)
        self.assertEqual(r.returncode, 1)

    def test_suivre_respecte_le_delai(self):
        lancer("indexation.py", "annoncer", "https://www.exemple.com/a/", cwd=self.dossier)
        r = lancer("indexation.py", "suivre", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Rien à vérifier", r.stdout)

    def test_suivre_sans_search_console(self):
        lancer("indexation.py", "annoncer", "https://www.exemple.com/a/", cwd=self.dossier)
        r = lancer("indexation.py", "suivre", "--delai", "0", cwd=self.dossier)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("Inspection impossible", r.stdout)


if __name__ == "__main__":
    unittest.main()
