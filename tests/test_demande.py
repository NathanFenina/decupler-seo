import argparse
import io
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import demande  # noqa: E402


def args(**kw):
    base = dict(pays=None, lieu=None, langue="en", graines="it marketing", lexique=False,
                mode="suggestions", max=10)
    base.update(kw)
    return argparse.Namespace(**base)


class TestRepliDeMarche(unittest.TestCase):
    def setUp(self):
        self.appels = []
        self.origine, self.valeur = demande.appel, demande.lire_valeur
        demande.lire_valeur = lambda cle: "FR"

        def faux(chemin, taches):
            self.appels.append(taches[0]["location_name"])
            if taches[0]["location_name"] == "France" and taches[0]["language_code"] == "en":
                raise demande.ErreurAPI("tâche 40501 Invalid Field: 'language_code'.")
            return [{"items": [{"keyword": "it marketing agency", "keyword_info": {"search_volume": 90}}]}], 0.01
        demande.appel = faux

    def tearDown(self):
        demande.appel, demande.lire_valeur = self.origine, self.valeur

    def test_anglais_en_france_lu_sur_les_etats_unis(self):
        with redirect_stderr(io.StringIO()) as err:
            res = demande.cmd_idees(args())
        self.assertEqual(self.appels, ["France", "United States"])
        self.assertEqual(res["lieu"], "United States")
        self.assertEqual(res["lignes"][0]["requete"], "it marketing agency")
        self.assertIn("United States", err.getvalue())

    def test_pays_explicite_pas_de_repli(self):
        with self.assertRaises(demande.ErreurAPI):
            demande.cmd_idees(args(pays="FR"))


if __name__ == "__main__":
    unittest.main()
