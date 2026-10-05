"""Duplication dans un lot de pages : la redite éditoriale bloque, le chrome commun non."""

import json
import sys
import unittest

from _outils import SCRIPTS, DossierIsole, lancer

sys.path.insert(0, str(SCRIPTS))
import similarite_lot as sl  # noqa: E402

COMMUN = ('<div class="bandeau" data-gabarit="commun"><div><p>Plus de quinze ans d\'expérience au service '
          'des entreprises de toute la région, avec une équipe qui intervient chaque semaine.</p></div>'
          '<p>Appelez-nous dès aujourd\'hui pour obtenir un devis gratuit et détaillé sous quarante-huit heures.</p></div>')

REDITE = [
    "Notre équipe intervient rapidement sur toute la ville pour répondre à vos besoins urgents.",
    "Chaque chantier commence par une visite technique gratuite et un devis détaillé.",
    "Nous utilisons uniquement des matériaux certifiés et garantis pendant dix ans au minimum.",
    "Les délais annoncés sont tenus dans la très grande majorité des cas que nous traitons.",
]


def page_ville(ville: str, propre: str, redite: bool = False) -> str:
    corps = " ".join(REDITE) if redite else ""
    return f"<h1>Couvreur à {ville}</h1>{COMMUN}<p>{propre}</p><p>{corps}</p>"


class TestFonctions(unittest.TestCase):
    def test_bloc_commun_retire_avec_ses_enfants(self):
        html = '<p>avant</p><div data-gabarit="commun"><div><span>dedans</span></div></div><p>après</p>'
        self.assertNotIn("dedans", sl.retirer_communs(html))
        self.assertIn("après", sl.retirer_communs(html))

    def test_phrases_courtes_ignorees_et_normalisees(self):
        ph = sl.phrases("Trop court. Une phrase assez longue pour être comparée entre les pages du lot.")
        self.assertEqual(list(ph), ["une phrase assez longue pour etre comparee entre les pages du lot"])

    def test_part_unique(self):
        a = "Une phrase propre à la page A qui parle de Nantes et de son port. " + " ".join(REDITE)
        b = "Une phrase propre à la page B qui parle de Rennes et de ses toits. " + " ".join(REDITE)
        res = sl.analyser({"a": a, "b": b})
        self.assertTrue(res["bloquant"])
        self.assertEqual(res["paires"][0]["communes"], 4)
        self.assertLess(res["par_page"][0]["unique_pct"], 60)


class TestLot(DossierIsole):
    def test_lot_differencie_passe_malgre_le_chrome(self):
        self.ecrire("lot/nantes.html", page_ville("Nantes", "Les toitures en ardoise du centre de Nantes "
                                                   "demandent un entretien régulier à cause des pluies atlantiques."))
        self.ecrire("lot/rennes.html", page_ville("Rennes", "À Rennes, les maisons à pans de bois du vieux "
                                                   "centre imposent des couvertures légères et des artisans qualifiés."))
        r = lancer("similarite_lot.py", "lot", "--strict", "--json", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(json.loads(r.stdout)["bloquant"])

    def test_lot_repetitif_bloque_en_strict(self):
        self.ecrire("lot/nantes.html", page_ville("Nantes", "Une phrase propre à Nantes et à son port fluvial.", True))
        self.ecrire("lot/rennes.html", page_ville("Rennes", "Une phrase propre à Rennes et à ses toits anciens.", True))
        r = lancer("similarite_lot.py", "lot", "--strict", cwd=self.dossier)
        self.assertEqual(r.returncode, 1)
        self.assertIn("phrases communes", r.stdout)
        # Sans --strict, le rapport s'affiche mais la commande ne bloque pas.
        self.assertEqual(lancer("similarite_lot.py", "lot", cwd=self.dossier).returncode, 0)

    def test_une_seule_page_refusee(self):
        self.ecrire("lot/seule.md", "# Une page\n\nRien à comparer avec une seule page dans ce dossier.")
        r = lancer("similarite_lot.py", "lot", cwd=self.dossier)
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
