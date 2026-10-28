"""Le maillage entrant dit où poser des liens : ancres et dosage doivent être justes."""

import sys
import unittest

from _outils import SCRIPTS

sys.path.insert(0, str(SCRIPTS))
import maillage_entrant as m  # noqa: E402

S = "https://exemple.com"


def lien(source, cible, ancre, zone="contenu"):
    return {"source": f"{S}{source}", "cible": f"{S}{cible}", "ancre": ancre, "zone": zone}


class TestAncres(unittest.TestCase):
    def test_types(self):
        cle = "pompe à chaleur"
        self.assertEqual(m.type_ancre("Pompe a chaleur", cle), "exacte")
        self.assertEqual(m.type_ancre("installer une pompe à chaleur air-eau", cle), "exacte")
        self.assertEqual(m.type_ancre("chaleur de la pompe", cle), "partielle")
        self.assertEqual(m.type_ancre("Cliquez ici", cle), "générique")
        self.assertEqual(m.type_ancre("Exemple Énergie", cle, marque="Exemple"), "marque")
        self.assertEqual(m.type_ancre("nos tarifs", cle), "autre")

    def test_dosage_selon_la_force(self):
        self.assertEqual(m.nb_liens_a_ajouter(0.1), (5, "faible"))
        self.assertEqual(m.nb_liens_a_ajouter(0.5), (3, "moyenne"))
        self.assertEqual(m.nb_liens_a_ajouter(0.9), (2, "forte"))

    def test_gsc_json_et_csv(self):
        import json
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            j = Path(d) / "g.json"
            j.write_text(json.dumps({"rows": [{"keys": [f"{S}/a/"], "clicks": 3, "impressions": 40}]}))
            self.assertEqual(m.charger_gsc(str(j))["exemple.com/a"], {"clics": 3.0, "impressions": 40.0})
            c = Path(d) / "g.csv"
            c.write_text("page,clics,impressions\nhttps://www.exemple.com/b,1,9\n")
            self.assertEqual(m.charger_gsc(str(c))["exemple.com/b"]["impressions"], 9.0)


class TestAnalyse(unittest.TestCase):
    def setUp(self):
        self.liens = [
            lien("/", "/pompe-a-chaleur/", "Pompe à chaleur", "menu"),
            lien("/blog/aides/", "/pompe-a-chaleur/", "cliquez ici"),
            lien("/blog/cop/", "/guide-pompe-a-chaleur/", "pompe à chaleur"),   # ancre concurrente
            lien("/", "/blog/cop/", "le COP expliqué"),
            lien("/", "/blog/chaudiere/", "chaudière gaz"),
            lien("/blog/chaudiere/", "/blog/cop/", "COP"),
            lien("/blog/cop/", "/", "accueil"),
        ]
        self.pages = {m.normaliser_url(f"{S}{u}"): {"url": f"{S}{u}", "title": t, "h1": t, "indexable": "True",
                                                    "statut": "200"}
                      for u, t in [("/", "Exemple"), ("/blog/cop/", "Le COP d'une pompe à chaleur"),
                                   ("/blog/chaudiere/", "Chaudière gaz"), ("/blog/aides/", "Les aides")]}

    def test_existant_concurrentes_et_opportunites(self):
        r = m.analyser(self.liens, f"{S}/pompe-a-chaleur/", "pompe à chaleur", ["COP"], self.pages)
        statuts = {e["statut"] for e in r["existants"]}
        self.assertEqual(statuts, {"hors contenu", "ancre générique"})
        self.assertEqual(r["sources_contenu"], 1)
        self.assertEqual(len(r["ancres_concurrentes"]), 1)
        sources = [o["source"] for o in r["opportunites"]]
        self.assertIn("exemple.com/blog/cop", sources)
        self.assertNotIn("exemple.com/blog/aides", sources)          # lie déjà la cible
        ancres = [o["ancre"] for o in r["opportunites"]]
        self.assertEqual(ancres.count("pompe à chaleur"), 1)          # l'exacte une seule fois
        self.assertEqual(len(ancres), len(set(ancres)))              # jamais deux fois la même

    def test_pas_d_exacte_si_deja_portee_en_contenu(self):
        liens = self.liens + [lien("/blog/chaudiere/", "/pompe-a-chaleur/", "pompe à chaleur")]
        r = m.analyser(liens, f"{S}/pompe-a-chaleur/", "pompe à chaleur", ["COP"], self.pages)
        self.assertNotIn("pompe à chaleur", [o["ancre"] for o in r["opportunites"]])


if __name__ == "__main__":
    unittest.main()
