"""La boucle de mesure : ses verdicts décident de ce qui sera annulé."""

import csv
import unittest
from pathlib import Path

from _outils import DossierIsole, lancer


class TestJournal(DossierIsole):
    def ajouter(self, type_="title", clics="40", impressions="3000", position="11"):
        return lancer("journal.py", "ajouter", "--url", "https://exemple.com/p", "--type", type_,
                      "--avant", "ancien", "--apres", "nouveau", "--clics", clics,
                      "--impressions", impressions, "--position", position, cwd=self.dossier)

    def mesurer(self, id_, *args):
        return lancer("journal.py", "mesurer", "--id", str(id_), *args, cwd=self.dossier)

    def lignes(self):
        with open(self.dossier / "journal" / "modifications.csv", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def verdict(self, id_):
        return next(l for l in self.lignes() if l["id"] == str(id_))["verdict"]

    def test_gain(self):
        self.ajouter()
        self.mesurer(1, "--clics", "96", "--impressions", "3300", "--temoin", "0")
        self.assertEqual(self.verdict(1), "gain")

    def test_le_temoin_neutralise_la_saison(self):
        # +17 % brut, mais le site entier a pris +12 % : l'effet réel est de +5 %.
        self.ajouter(clics="60", impressions="5000")
        self.mesurer(1, "--clics", "70", "--impressions", "5100", "--temoin", "12")
        self.assertEqual(self.verdict(1), "neutre")

    def test_perte(self):
        self.ajouter(clics="50", impressions="4000")
        self.mesurer(1, "--clics", "34", "--impressions", "3900", "--temoin", "12")
        self.assertEqual(self.verdict(1), "perte")

    def test_trop_peu_d_impressions(self):
        self.ajouter(clics="5", impressions="60")
        self.mesurer(1, "--clics", "9", "--impressions", "70")
        self.assertEqual(self.verdict(1), "insuffisant")

    def test_petite_page_jugee_sur_la_position(self):
        self.ajouter(clics="8", impressions="900", position="14")
        self.mesurer(1, "--clics", "11", "--impressions", "950", "--position", "9")
        self.assertEqual(self.verdict(1), "gain")

    def test_perte_proposee_au_retour_arriere(self):
        self.ajouter(clics="50", impressions="4000")
        self.mesurer(1, "--clics", "20", "--impressions", "3800")
        r = lancer("journal.py", "a-annuler", cwd=self.dossier)
        self.assertIn("ancien", r.stdout)

    def test_pas_d_apprentissage_sur_un_cas_isole(self):
        self.ajouter()
        self.mesurer(1, "--clics", "96", "--impressions", "3300")
        r = lancer("journal.py", "bilan", cwd=self.dossier)
        self.assertNotIn("À reporter", r.stdout)

    def test_apprentissage_a_partir_de_trois_mesures(self):
        for _ in range(3):
            self.ajouter()
        for i in (1, 2, 3):
            self.mesurer(i, "--clics", "90", "--impressions", "3200")
        r = lancer("journal.py", "bilan", cwd=self.dossier)
        self.assertIn("fonctionne sur ce site", r.stdout)

    def test_mesure_sans_chiffres_refusee_hors_mode_auto(self):
        self.ajouter()
        r = self.mesurer(1)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
