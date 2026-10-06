"""netlinking_score.py : classement des cibles d'une campagne de netlinking."""

import json
import sys
import unittest

from _outils import SCRIPTS, DossierIsole, lancer

sys.path.insert(0, str(SCRIPTS))
import netlinking_score as ns  # noqa: E402

CIBLES = [
    {"domaine": "annuaire-metier.example", "da": 10, "trafic": 46, "ref_domains": 48, "pertinence": 40,
     "accessibilite": 20, "offre": "analyse", "preuve": "ranke sur la requête visée (pos. 10)"},
    {"domaine": "grand-media.example", "da": 76, "trafic": 120000, "ref_domains": 9000, "pertinence": 20,
     "accessibilite": 2, "offre": "etude", "preuve": "rubrique dédiée"},
    {"domaine": "mort.example", "da": 1, "trafic": "", "ref_domains": 0, "backlinks": 0, "pertinence": 35,
     "accessibilite": 15, "offre": "analyse"},
    {"domaine": "sans-preuve.example", "da": 20, "trafic": 300, "pertinence": 30, "accessibilite": 15, "offre": "analyse"},
]


class TestNotes(unittest.TestCase):
    def test_autorite_logarithmique(self):
        self.assertEqual(ns.note_autorite(10), 12.5)
        self.assertEqual(ns.note_autorite(100), 25)
        self.assertEqual(ns.note_autorite(None), 0)
        # 10 → 30 pèse plus que 70 → 90.
        self.assertGreater(ns.note_autorite(30) - ns.note_autorite(10), ns.note_autorite(90) - ns.note_autorite(70))

    def test_trafic_inconnu_vaut_zero_et_plafonne(self):
        self.assertEqual(ns.note_trafic(None), 0)
        self.assertEqual(ns.note_trafic(""), 0)
        self.assertEqual(ns.note_trafic(10 ** 7), 15)

    def test_notes_manuelles_bornees(self):
        s, detail = ns.score({"pertinence": 99, "accessibilite": -3, "da": 1})
        self.assertEqual(detail["pertinence"], 40)
        self.assertEqual(detail["accessibilite"], 0)
        self.assertEqual(s, 40)


class TestClassement(unittest.TestCase):
    def test_accessible_avant_autorite_injoignable(self):
        classees, _ = ns.classer(CIBLES)
        ordre = [c["domaine"] for c in classees]
        self.assertLess(ordre.index("annuaire-metier.example"), ordre.index("grand-media.example"))

    def test_domaine_sans_donnee_ecarte_avec_raison(self):
        classees, ecartees = ns.classer(CIBLES)
        self.assertNotIn("mort.example", [c["domaine"] for c in classees])
        self.assertIn("aucune donnée", ecartees[0]["raison"])

    def test_cible_sans_preuve_signalee(self):
        classees, _ = ns.classer(CIBLES)
        sans = next(c for c in classees if c["domaine"] == "sans-preuve.example")
        self.assertEqual(sans["avertissements"], ["sans preuve mesurée"])

    def test_filtre_offre_et_minimum(self):
        classees, ecartees = ns.classer(CIBLES, offre="analyse", minimum=75)
        self.assertEqual([c["domaine"] for c in classees], ["annuaire-metier.example"])
        self.assertTrue(any("sous le minimum" in e["raison"] for e in ecartees))


class TestLigneDeCommande(DossierIsole):
    def test_json(self):
        self.ecrire("cibles.json", json.dumps({"mesure": "2026-09-01", "cibles": CIBLES,
                                               "ecartes": [{"domaine": "x.example", "raison": "hors sujet"}]}))
        r = lancer("netlinking_score.py", "cibles.json", "--json", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        doc = json.loads(r.stdout)
        self.assertEqual(doc["cibles"][0]["domaine"], "annuaire-metier.example")
        self.assertEqual(len(doc["ecartees"]), 2)

    def test_csv_lisible(self):
        self.ecrire("prospects.csv", "domaine,da,trafic,pertinence,accessibilite,preuve\n"
                                     "a.example,15,25,40,18,classement des prestataires\n")
        r = lancer("netlinking_score.py", "prospects.csv", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("a.example", r.stdout)
        self.assertIn("jamais comparées", r.stdout)

    def test_fichier_absent_ou_invalide(self):
        self.assertEqual(lancer("netlinking_score.py", "absent.json", cwd=self.dossier).returncode, 1)
        self.ecrire("mauvais.csv", "site,da\nx,3\n")
        r = lancer("netlinking_score.py", "mauvais.csv", cwd=self.dossier)
        self.assertEqual(r.returncode, 1)
        self.assertIn("domaine", r.stderr)


if __name__ == "__main__":
    unittest.main()
