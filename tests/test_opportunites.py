"""Classement des opportunités : c'est lui qui décide où les routines agissent."""

import csv
import datetime as dt
import json
import sys
import unittest

from _outils import SCRIPTS, DossierIsole, lancer

sys.path.insert(0, str(SCRIPTS))
import share_of_model  # noqa: E402

EXPORT = [
    # requête, page, clics, impressions, position
    ("creer societe arabie saoudite", "https://ex.com/creation", 30, 3000, 7.0),
    ("company formation saudi arabia", "https://ex.com/en/formation", 5, 2000, 14.0),
    ("vivre a riyad", "https://ex.com/riyad", 60, 3000, 7.0),
    ("tva arabie saoudite", "https://ex.com/tva", 10, 1500, 2.0),
    ("depot marque arabie", "https://ex.com/marque", 8, 800, 5.0),
    ("depot marque arabie", "https://ex.com/marque-cout", 6, 700, 6.0),
    ("tasis partners avis", "https://ex.com/", 50, 200, 1.0),
    ("requete rare", "https://ex.com/x", 0, 5, 30.0),
]

LEXIQUE = [
    ("creation-societe", 3, r"cr[ée]+er? (une )?soci[ée]t[ée]"),
    ("creation-societe", 3, r"company formation"),
    ("tva", 2, r"\btva\b"),
    ("marque", 2, r"marque"),
    ("vie-locale", 1, r"vivre"),
    ("visa", 3, r"visa"),
]


class TestOpportunites(DossierIsole):
    def preparer(self, journal=None):
        (self.dossier / "memoire").mkdir()
        with open(self.dossier / "memoire/lexique.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["theme", "valeur", "motif"])
            w.writerows(LEXIQUE)
        with open(self.dossier / "export.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Query", "Page", "Clicks", "Impressions", "Position"])
            w.writerows(EXPORT)
        (self.dossier / "decupler-seo.config.yml").write_text(
            'mode: assisted\nprojet:\n  nom: "Tasis Partners"\n  domaine: "https://www.tasispartners.com"\n'
            "mesure:\n  delai_jours: 28\n", encoding="utf-8")
        if journal:
            (self.dossier / "journal").mkdir()
            with open(self.dossier / "journal/modifications.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["id", "date", "url", "verdict"])
                w.writerows(journal)

    def classer(self, *args):
        r = lancer("opportunites.py", "--csv", "export.csv", "--json", "--jours", "30", *args, cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return json.loads(r.stdout)

    def test_la_valeur_du_theme_passe_avant_le_trafic(self):
        self.preparer()
        res = self.classer()
        ordre = [o["requete"] for o in res["opportunites"]]
        # Même position et même volume : le thème qui se vend passe devant le thème d'information.
        self.assertLess(ordre.index("creer societe arabie saoudite"), ordre.index("vivre a riyad"))

    def test_la_marque_est_hors_classement(self):
        self.preparer()
        res = self.classer()
        self.assertNotIn("tasis partners avis", [o["requete"] for o in res["opportunites"]])
        self.assertEqual(res["marque"]["clics"], 50)

    def test_actions_selon_la_situation(self):
        self.preparer()
        actions = {o["requete"]: o["action"] for o in self.classer()["opportunites"]}
        self.assertEqual(actions["tva arabie saoudite"], "ctr")          # top 3, CTR 0,7 %
        self.assertEqual(actions["company formation saudi arabia"], "page-2")
        self.assertEqual(actions["depot marque arabie"], "cannibalisation")
        self.assertNotIn("requete rare", actions)                         # sous le seuil d'impressions

    def test_page_en_cours_de_mesure_exclue(self):
        hier = (dt.date.today() - dt.timedelta(days=1)).isoformat()
        self.preparer(journal=[("1", hier, "https://ex.com/creation/", "")])
        res = self.classer()
        ligne = next(o for o in res["opportunites"] if o["page"] == "https://ex.com/creation")
        self.assertEqual(ligne["score"], 0)
        self.assertTrue(ligne["en_mesure_jusqu_au"])
        self.assertNotIn("https://ex.com/creation", [p["page"] for p in res["pages"]])

    def test_theme_non_couvert_et_demande(self):
        self.preparer()
        with open(self.dossier / "demande.csv", "w", newline="", encoding="utf-8") as f:
            f.write("requete,volume\nvisa affaires arabie saoudite,900\ntva arabie saoudite,500\n")
        res = self.classer("--demande", "demande.csv")
        a_creer = [o for o in res["opportunites"] if o["action"] == "a-creer"]
        self.assertEqual([o["requete"] for o in a_creer], ["visa affaires arabie saoudite"])
        couverture = {c["theme"]: c for c in res["couverture"]}
        self.assertIsNone(couverture["visa"]["meilleure_position"])

    def test_sans_lexique_le_rapport_le_dit(self):
        self.preparer()
        (self.dossier / "memoire/lexique.csv").unlink()
        r = lancer("opportunites.py", "--csv", "export.csv", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Aucun lexique", r.stdout)

    def test_propriete_gsc_propre_au_projet(self):
        # Un environnement cloud partagé entre clients : la propriété vient de chaque projet.
        import os
        import gsc
        (self.dossier / "decupler-seo.config.yml").write_text(
            'projet:\n  domaine: "https://www.ex.com"\n  propriete_gsc: "sc-domain:ex.com"\n', encoding="utf-8")
        avant = {k: os.environ.pop(k, None) for k in ("GSC_SITE_URL", "SEO_DECUPLER_CONFIG")}
        os.environ["SEO_DECUPLER_PROJET"] = str(self.dossier)
        try:
            self.assertEqual(gsc.site_par_defaut(), "sc-domain:ex.com")
        finally:
            os.environ.pop("SEO_DECUPLER_PROJET")
            os.environ.update({k: v for k, v in avant.items() if v})


class TestShareOfModel(unittest.TestCase):
    def test_citation_rang_et_sous_domaine(self):
        res = share_of_model.analyser({"texte": "Selon Tasis Partners, il faut…",
                                       "sources": ["misa.gov.sa", "misa.gov.sa", "blog.tasispartners.com"]},
                                      "Tasis Partners", "tasispartners.com")
        self.assertTrue(res["cite"])
        self.assertEqual(res["rang"], 2)                     # doublons retirés avant de compter
        self.assertTrue(res["nomme"])

    def test_la_famille_marque_ne_compte_pas_dans_la_visibilite(self):
        releves = [
            {"moteur": "openai", "famille": "decouverte", "cite": False, "rang": 0, "nomme": False, "sources": "a.com"},
            {"moteur": "openai", "famille": "marque", "cite": True, "rang": 1, "nomme": True, "sources": "ex.com"},
        ]
        bilan = share_of_model.synthese(releves)["openai"]
        self.assertEqual(bilan["taux_citation_pct"], 0.0)
        self.assertEqual(bilan["reputation"], 1)

    def test_moteur_sans_cle_ignore(self):
        import os
        avant = {k: os.environ.pop(k, None) for k in ("OPENAI_API_KEY", "GEMINI_API_KEY",
                                                      "ANTHROPIC_API_KEY", "PERPLEXITY_API_KEY")}
        try:
            os.environ["GEMINI_API_KEY"] = "x"
            self.assertEqual(share_of_model.moteurs_disponibles(), ["gemini"])
        finally:
            os.environ.pop("GEMINI_API_KEY")
            os.environ.update({k: v for k, v in avant.items() if v})


if __name__ == "__main__":
    unittest.main()
