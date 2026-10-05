"""Audit de contenu : un verdict par page, et un dégradé honnête sans Search Console."""

import datetime as dt
import json
import sys
import unittest

from _outils import SCRIPTS, DossierIsole, lancer

sys.path.insert(0, str(SCRIPTS))
import audit_contenu as ac  # noqa: E402

AUJOURDHUI = dt.date(2026, 10, 5)

CARTE = """id,type,statut,url,titre,meta_titre,meta_description,h1,h2,termes,nb_mots,liens_entrants,modifie
1,pages,publish,https://exemple.com/panier/,Panier,,,,,,10,0,2024-01-01
2,posts,publish,https://exemple.com/vide/,Vide,,,,,,40,0,2026-01-01
3,posts,publish,https://exemple.com/morte/,Morte,,,,,,900,2,2025-01-01
4,posts,publish,https://exemple.com/guide-seo/,Guide SEO 2024,,,,,,1200,4,2025-03-01
5,posts,publish,https://exemple.com/pousser/,Pousser,,,,,,1500,3,2026-05-01
6,posts,publish,https://exemple.com/mince/,Mince,,,,,,250,1,2026-05-01
7,posts,publish,https://exemple.com/saine/,Saine,,,,,,1500,5,2026-05-01
8,posts,draft,https://exemple.com/brouillon/,Brouillon,,,,,,10,0,2026-09-01
"""

GSC = {"rows": [
    {"keys": ["https://exemple.com/guide-seo/"], "clicks": 12, "impressions": 800, "position": 6.2},
    {"keys": ["https://exemple.com/pousser"], "clicks": 3, "impressions": 450, "position": 11.4},
    {"keys": ["https://exemple.com/mince/"], "clicks": 1, "impressions": 60, "position": 25},
    {"keys": ["https://exemple.com/saine/?utm=x"], "clicks": 90, "impressions": 3000, "position": 3.1},
]}


def page(**kw):
    base = {"impressions": 0, "clics": 0, "position": None, "mots": 1500, "age_jours": 30,
            "obsolete": [], "technique": False, "gsc": True}
    base.update(kw)
    return base


class TestVerdicts(unittest.TestCase):
    def test_vide_avant_tout_le_reste(self):
        self.assertEqual(ac.verdict(page(mots=40, age_jours=900))[0], "vide")

    def test_morte_seulement_apres_six_mois(self):
        self.assertEqual(ac.verdict(page(age_jours=200))[0], "morte")
        self.assertEqual(ac.verdict(page(age_jours=60))[0], "saine")

    def test_perimee_avec_trafic_se_met_a_jour(self):
        v, action = ac.verdict(page(impressions=500, obsolete=["titre daté 2023"]))
        self.assertEqual(v, "périmée")
        self.assertIn("trafic", action)

    def test_a_pousser_entre_8_et_20(self):
        self.assertEqual(ac.verdict(page(impressions=150, position=12))[0], "à pousser")
        self.assertEqual(ac.verdict(page(impressions=150, position=4))[0], "saine")
        self.assertEqual(ac.verdict(page(impressions=50, position=12))[0], "saine")

    def test_mince_seulement_si_montree(self):
        self.assertEqual(ac.verdict(page(mots=300, impressions=20, position=30))[0], "mince")

    def test_page_technique_jamais_jugee_sur_le_trafic(self):
        self.assertEqual(ac.verdict(page(mots=5, technique=True, age_jours=900))[0], "technique")

    def test_sans_gsc_pas_de_morte(self):
        # Sans données, zéro impression ne veut rien dire : on ne déclare pas une page morte.
        self.assertEqual(ac.verdict(page(gsc=False, age_jours=900))[0], "saine")


class TestObsolescence(unittest.TestCase):
    def test_annee_passee_dans_le_titre(self):
        ligne = {"titre": "Guide du SEO local 2024", "h2": "Les étapes"}
        self.assertEqual(ac.signaux_obsolescence(ligne, 2026), ["titre daté 2024"])

    def test_annee_courante_ou_corps_ne_comptent_pas(self):
        ligne = {"titre": "Guide 2026", "termes": "étude 2021 citée dans le texte"}
        self.assertEqual(ac.signaux_obsolescence(ligne, 2026), [])

    def test_motifs_du_site_avec_libelle(self):
        motifs = ac.compiler_obsoletes([r"gpt-?3\.5|gpt-4o::anciens modèles", "windows 7"])
        ligne = {"titre": "Comparer GPT-4o et Claude", "termes": "windows 7"}
        self.assertEqual(ac.signaux_obsolescence(ligne, 2026, motifs), ["anciens modèles", "windows 7"])

    def test_motif_invalide_ignore(self):
        self.assertEqual(ac.compiler_obsoletes(["(sans fin"]), [])


class TestLectureGSC(unittest.TestCase):
    def test_cle_url_commune(self):
        self.assertEqual(ac.cle_url("https://exemple.com/Guide/?a=1"), ac.cle_url("/guide"))

    def test_export_csv_de_l_interface(self):
        csv = "Pages les plus populaires,Clics,Impressions,CTR,Position\n" \
              "https://exemple.com/a/,\"1 204\",\"30 512\",\"3,9 %\",\"7,4\"\n"
        perf = ac.lire_gsc_csv(csv)
        self.assertEqual(perf["a"], {"impressions": 30512, "clics": 1204, "position": 7.4})


class TestAuditComplet(DossierIsole):
    def test_un_verdict_par_page_publiee(self):
        self.ecrire("carte.csv", CARTE)
        self.ecrire("gsc.json", json.dumps(GSC))
        r = lancer("audit_contenu.py", "--carte", "carte.csv", "--gsc", "gsc.json", "--sortie", "sortie",
                   "--aujourdhui", AUJOURDHUI.isoformat(), "--json", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        doc = json.loads(r.stdout)
        verdicts = {p["url"].split("/")[3]: p["verdict"] for p in doc["pages"]}
        self.assertEqual(verdicts, {"panier": "technique", "vide": "vide", "morte": "morte",
                                    "guide-seo": "périmée", "pousser": "à pousser",
                                    "mince": "mince", "saine": "saine"})
        md = (self.dossier / "sortie/audit-contenu.md").read_text(encoding="utf-8")
        self.assertIn("Les 5 actions les plus rentables", md)

    def test_degrade_sans_search_console_et_le_dit(self):
        self.ecrire("carte.csv", CARTE)
        r = lancer("audit_contenu.py", "--carte", "carte.csv", "--sortie", "sortie",
                   "--aujourdhui", AUJOURDHUI.isoformat(), cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        md = (self.dossier / "sortie/audit-contenu.md").read_text(encoding="utf-8")
        self.assertIn("Sans Search Console", md)
        self.assertNotIn("## Morte", md)

    def test_carte_absente_erreur_claire(self):
        r = lancer("audit_contenu.py", "--carte", "absente.csv", cwd=self.dossier)
        self.assertEqual(r.returncode, 1)
        self.assertIn("wp.py carte", r.stderr)

    def test_motifs_lus_dans_la_config(self):
        self.ecrire("decupler-seo.config.yml", "audit_contenu:\n  obsolete:\n    - \"saine::modèle retiré\"\n")
        self.ecrire("carte.csv", CARTE)
        r = lancer("audit_contenu.py", "--carte", "carte.csv", "--sortie", "sortie",
                   "--aujourdhui", AUJOURDHUI.isoformat(), "--json", cwd=self.dossier)
        doc = json.loads(r.stdout)
        saine = next(p for p in doc["pages"] if p["url"].endswith("/saine/"))
        self.assertEqual(saine["obsolete"], ["modèle retiré"])


if __name__ == "__main__":
    unittest.main()
