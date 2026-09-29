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
    ("creer societe lyon", "https://ex.com/creation", 30, 3000, 7.0),
    ("company formation lyon", "https://ex.com/en/formation", 5, 2000, 14.0),
    ("vivre a lyon", "https://ex.com/lyon", 60, 3000, 7.0),
    ("tva auto entrepreneur", "https://ex.com/tva", 10, 1500, 2.0),
    ("depot marque inpi", "https://ex.com/marque", 8, 800, 5.0),
    ("depot marque inpi", "https://ex.com/marque-cout", 6, 700, 6.0),
    ("atlas conseil avis", "https://ex.com/", 50, 200, 1.0),
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
            'mode: assisted\nprojet:\n  nom: "Atlas Conseil"\n  domaine: "https://www.atlas-conseil.example"\n'
            "mesure:\n  delai_jours: 28\n", encoding="utf-8")
        if journal:
            (self.dossier / "journal").mkdir()
            with open(self.dossier / "journal/modifications.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["id", "date", "url", "verdict", "requete"][:len(journal[0])])
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
        self.assertLess(ordre.index("creer societe lyon"), ordre.index("vivre a lyon"))

    def test_la_marque_est_hors_classement(self):
        self.preparer()
        res = self.classer()
        self.assertNotIn("atlas conseil avis", [o["requete"] for o in res["opportunites"]])
        self.assertEqual(res["marque"]["clics"], 50)

    def test_actions_selon_la_situation(self):
        self.preparer()
        actions = {o["requete"]: o["action"] for o in self.classer()["opportunites"]}
        self.assertEqual(actions["tva auto entrepreneur"], "ctr")          # top 3, CTR 0,7 %
        self.assertEqual(actions["company formation lyon"], "page-2")
        self.assertEqual(actions["depot marque inpi"], "cannibalisation")
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
            f.write("requete,volume,page\nvisa affaires canada,900,\ntva auto entrepreneur,500,\n"
                    "marque inpi prix,300,https://ex.com/marque-cout\n")
        res = self.classer("--demande", "demande.csv")
        a_creer = [o for o in res["opportunites"] if o["action"] == "a-creer"]
        self.assertEqual([o["requete"] for o in a_creer], ["visa affaires canada"])
        invisibles = [o["requete"] for o in res["opportunites"] if o["action"] == "invisible"]
        self.assertEqual(invisibles, ["marque inpi prix"])
        couverture = {c["theme"]: c for c in res["couverture"]}
        self.assertIsNone(couverture["visa"]["meilleure_position"])

    def test_page_neuve_du_journal_pas_proposee_a_creer(self):
        # Page publiée hier, pas encore d'impressions : sa requête ne doit pas revenir « à créer ».
        hier = (dt.date.today() - dt.timedelta(days=1)).isoformat()
        self.preparer(journal=[("1", hier, "https://ex.com/visa", "", "visa affaires canada | visa pro")])
        with open(self.dossier / "demande.csv", "w", newline="", encoding="utf-8") as f:
            f.write("requete,volume,page\nvisa affaires canada,900,\nvisa pro,200,\nvisa etudiant,300,\n")
        res = self.classer("--demande", "demande.csv")
        lignes = {o["requete"]: o for o in res["opportunites"] if o["requete"].startswith("visa")}
        self.assertEqual(lignes["visa affaires canada"]["page"], "https://ex.com/visa")
        self.assertEqual(lignes["visa affaires canada"]["score"], 0)          # en mesure
        self.assertEqual(lignes["visa pro"]["score"], 0)
        self.assertEqual(lignes["visa etudiant"]["action"], "a-creer")

    def test_demande_seule_sans_search_console(self):
        # Site jeune ou accès pas encore donné : on classe, mais sans prétendre connaître les positions.
        self.preparer()
        with open(self.dossier / "demande.csv", "w", newline="", encoding="utf-8") as f:
            f.write("requete,volume,page\ncreer societe marseille,400,https://ex.com/marseille\nvisa affaires,900,\n")
        r = lancer("opportunites.py", "--demande", "demande.csv", "--json", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        res = json.loads(r.stdout)
        actions = {o["requete"]: o["action"] for o in res["opportunites"]}
        self.assertEqual(actions, {"creer societe marseille": "a-verifier", "visa affaires": "a-creer"})
        self.assertFalse(res["gsc"])

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



class TestFunnelEtCalendrier(unittest.TestCase):
    def test_funnel_url_puis_requete(self):
        import opportunites as o
        self.assertEqual(o.funnel_de("https://ex.com/tarifs", "comment faire"), "BOFU")
        self.assertEqual(o.funnel_de("https://ex.com/p", "comparatif logiciel paie"), "MOFU")
        self.assertEqual(o.funnel_de("", "prix expert comptable"), "BOFU")
        self.assertEqual(o.funnel_de("", "tva auto entrepreneur"), "TOFU")

    def test_format_special_et_calendrier(self):
        import datetime as dt
        import opportunites as o
        res = {"opportunites": [
            {"requete": "modele facture gratuit", "page": "", "action": "a-creer", "a_faire": "", "type_journal": "",
             "score": 10.0, "gain_clics_mois": 5},
            {"requete": "prix expert comptable", "page": "", "action": "a-creer", "a_faire": "", "type_journal": "",
             "score": 8.0, "gain_clics_mois": 4},
            {"requete": "comment creer sa societe", "page": "", "action": "a-creer", "a_faire": "", "type_journal": "",
             "score": 6.0, "gain_clics_mois": 3},
            {"requete": "expert comptable lyon", "page": "https://ex.com/lyon", "action": "ctr", "a_faire": "",
             "type_journal": "", "score": 9.0, "gain_clics_mois": 4}]}
        res = o.enrichir(res, [])
        actions = {x["requete"]: x["action"] for x in res["opportunites"]}
        self.assertEqual(actions["modele facture gratuit"], "format-special")
        plan = o.calendrier(res, semaines=2, capacite=2, mix=o.lire_mix("50/25/25"), debut=dt.date(2026, 9, 29))
        self.assertEqual(len(plan), 4)
        self.assertEqual(sum(1 for e in plan if e["type"] == "optimisation"), 1)       # 20 % de 4
        self.assertEqual(plan[0]["semaine"], "2026-10-05")                              # lundi suivant
        with self.assertRaises(SystemExit):
            o.lire_mix("beaucoup")


class TestShareOfModel(unittest.TestCase):
    def test_citation_rang_et_sous_domaine(self):
        res = share_of_model.analyser({"texte": "Selon Atlas Conseil, il faut…",
                                       "sources": ["impots.gouv.fr", "impots.gouv.fr", "blog.atlas-conseil.example"]},
                                      "Atlas Conseil", "atlas-conseil.example")
        self.assertTrue(res["cite"])
        self.assertEqual(res["rang"], 2)                     # doublons retirés avant de compter
        self.assertTrue(res["nomme"])

    def test_garde_anti_homonyme(self):
        alias = share_of_model.alias_marque("Atlas", "atlas.example")
        self.assertFalse(share_of_model.mentionne("Le mot « atlas » est un terme de cartographie.", alias))
        self.assertTrue(share_of_model.mentionne("Atlas accompagne les créateurs d'entreprise.", alias))

    def test_verifier_la_liste(self):
        lignes = [{"famille": "visibilite", "funnel": "BOFU", "prompt": "Quel est le meilleur cabinet, Atlas ou un autre ?"},
                  {"famille": "visibilite", "funnel": "MOFU", "prompt": "Comment faire de la génération de leads ?"},
                  {"famille": "marque", "funnel": "", "prompt": "Que vaut Atlas ?"}]
        erreurs, _ = share_of_model.verifier(lignes, "Atlas", "atlas.example")
        self.assertTrue(any("ligne 2" in e and "marque" in e for e in erreurs))
        self.assertTrue(any("ligne 3" in e and "vendeur" in e for e in erreurs))
        self.assertFalse(any("ligne 4" in e for e in erreurs))     # famille marque : le nom est attendu

    def test_generation_2_3_3_et_verification(self):
        lignes = share_of_model.generer("cabinet comptable", ["création d'entreprise"], "France", "fr", "Atlas")
        funnels = [l["funnel"] for l in lignes if l["famille"] != "marque"]
        self.assertEqual((funnels.count("TOFU"), funnels.count("MOFU"), funnels.count("BOFU")), (2, 3, 3))
        erreurs, _ = share_of_model.verifier(lignes, "Atlas", "atlas.example")
        self.assertEqual(erreurs, [])

    def test_visibilite_ponderee_et_prompts_manquants(self):
        releves = [
            {"moteur": "openai", "famille": "visibilite", "poids": 3, "prompt": "b", "cite": False, "rang": 0,
             "nomme": True, "sources": "a.com", "concurrents_nommes": "X"},
            {"moteur": "openai", "famille": "visibilite", "poids": 1, "prompt": "t", "cite": False, "rang": 0,
             "nomme": False, "sources": "a.com", "concurrents_nommes": "X, Y"},
            {"moteur": "openai", "famille": "visibilite", "poids": 2, "prompt": "m", "cite": False, "rang": 0,
             "nomme": False, "sources": "", "concurrents_nommes": ""},
        ]
        b = share_of_model.synthese(releves)["openai"]
        self.assertEqual(b["taux_mention_pondere_pct"], 50.0)        # 3 sur 6
        self.assertEqual(b["sov_pct"], 25.0)                         # 1 mention contre 3
        self.assertEqual(b["visibilite"], 40.0)                      # 0,6 × 50 + 0,4 × 25
        self.assertEqual(share_of_model.prompts_manquants(releves), ["m"])

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
