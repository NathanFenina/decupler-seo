"""Rapport mensuel et demande : les chiffres du client viennent de ces calculs."""

import re
import sys
import unittest

from _outils import SCRIPTS

sys.path.insert(0, str(SCRIPTS))
import demande  # noqa: E402
import rapport  # noqa: E402


def l(cle, valeur, clics, impr, pos=5.0):
    return {cle: valeur, "clics": clics, "impressions": impr, "position": pos}


class TestPeriodes(unittest.TestCase):
    def test_bornes_et_decalages(self):
        self.assertEqual(rapport.bornes("2026-02"), ("2026-02-01", "2026-02-28"))
        self.assertEqual(rapport.decaler("2026-01", -1), "2025-12")
        self.assertEqual(rapport.decaler("2026-09", -12), "2025-09")
        import datetime as dt
        self.assertEqual(rapport.mois_precedent(dt.date(2026, 1, 15)), "2025-12")


class TestCalculs(unittest.TestCase):
    def test_totaux_position_ponderee(self):
        t = rapport.totaux([l("page", "a", 10, 100, 2.0), l("page", "b", 0, 300, 10.0)])
        self.assertEqual((t["clics"], t["impressions"], t["position_moyenne"]), (10, 400, 8.0))

    def test_variation_sans_base(self):
        self.assertIsNone(rapport.variation(10, 0))
        self.assertEqual(rapport.variation(120, 100), 20.0)

    def test_hausses_et_baisses(self):
        avant = [l("page", "a", 50, 1000), l("page", "b", 10, 200)]
        apres = [l("page", "a", 20, 900), l("page", "b", 30, 400), l("page", "c", 0, 50)]
        e = rapport.ecarts(avant, apres, "page")
        self.assertEqual([x["page"] for x in e["hausses"]], ["b", "c"])
        self.assertEqual([x["page"] for x in e["baisses"]], ["a"])

    def test_requetes_nouvelles_et_marque(self):
        avant = [l("requete", "tva", 1, 10)]
        apres = [l("requete", "tva", 1, 10), l("requete", "nitaqat", 0, 40), l("requete", "tasis avis", 2, 5)]
        self.assertEqual([x["requete"] for x in rapport.requetes_nouvelles(avant, apres)], ["nitaqat", "tasis avis"])
        marque, autres = rapport.separer_marque(apres, [re.compile("tasis", re.I)])
        self.assertEqual((marque["clics"], autres["impressions"]), (2, 50))

    def test_journal_du_mois(self):
        journal = [{"date": "2026-09-03", "type": "title", "date_mesure": "2026-10-01", "verdict": ""},
                   {"date": "2026-08-01", "type": "meta", "date_mesure": "2026-09-01", "verdict": "perte", "id": "1", "url": "u"},
                   {"date": "2026-08-02", "type": "faq", "date_mesure": "2026-09-02", "verdict": "gain"}]
        b = rapport.bilan_journal(journal, "2026-09")
        self.assertEqual((b["modifications"], b["gains"], b["pertes"]), (1, 1, 1))
        self.assertEqual(b["pertes_detail"][0]["id"], "1")

    def test_runs_et_a_valider(self):
        noms = ["2026-09-01-veille.md", "2026-09-02-veille.md", "2026-09-04-optimisation.md", "2026-08-31-veille.md"]
        r = rapport.bilan_runs(noms, "2026-09")
        self.assertEqual((r["veille_trouvees"], r["veille_attendues"], r["trouves"]["optimisation"]), (2, 30, 1))
        self.assertEqual(rapport.a_valider("- [ ] a\n- [x] b\n- c\n"), 2)


class TestDemande(unittest.TestCase):
    def test_pays_inconnu_demande_un_lieu(self):
        class A:
            pays, lieu, langue = "ZZ", None, "fr"
        with self.assertRaises(SystemExit):
            demande.lieu_et_langue(A())

    def test_lieu_depuis_code_pays(self):
        class A:
            pays, lieu, langue = "sa", None, "AR"
        self.assertEqual(demande.lieu_et_langue(A()), ("Saudi Arabia", "ar"))

    def test_identifiants_absents(self):
        import os
        avant = {k: os.environ.pop(k, None) for k in ("DATAFORSEO_LOGIN", "DATAFORSEO_USERNAME", "DATAFORSEO_PASSWORD")}
        try:
            with self.assertRaises(demande.ErreurAPI):
                demande.identifiants()
        finally:
            os.environ.update({k: v for k, v in avant.items() if v})


if __name__ == "__main__":
    unittest.main()
