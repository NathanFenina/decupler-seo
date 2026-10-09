import datetime as dt
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import agents_ia  # noqa: E402
import budget  # noqa: E402
import gsc  # noqa: E402
import maj_google  # noqa: E402


class TestMajGoogle(unittest.TestCase):
    INCIDENTS = [
        {"service_name": "Ranking", "external_desc": "September 2026 spam update", "begin": "2026-09-24T16:15:00+00:00",
         "end": "2026-10-08T08:00:00+00:00", "uri": "incidents/X", "most_recent_update": {"text": "complete"}},
        {"service_name": "Ranking", "external_desc": "November 2026 core update", "begin": "2026-11-02T10:00:00+00:00",
         "end": None, "uri": "incidents/Y"},
        {"service_name": "Serving", "external_desc": "Serving issue", "begin": "2026-02-25T00:00:00+00:00",
         "end": "2026-02-25T05:00:00+00:00", "uri": "incidents/Z"},
    ]

    def test_flux_garde_le_classement_seulement(self):
        maj = maj_google.depuis_flux(self.INCIDENTS)
        self.assertEqual([(m["nom"], m["type"], m["en_cours"]) for m in maj],
                         [("September 2026 spam update", "spam", False), ("November 2026 core update", "core", True)])

    def test_le_flux_remplace_l_historique_du_meme_mois(self):
        historique = {"mises_a_jour": [{"debut": "2026-09-24", "fin": None, "type": "spam",
                                        "nom": "September 2026 spam update", "source": "", "notes": ""}]}
        maj = maj_google.toutes(historique, self.INCIDENTS)
        sept = [m for m in maj if m["nom"].startswith("September")]
        self.assertEqual(len(sept), 1)
        self.assertEqual(sept[0]["fin"], "2026-10-08")

    def test_periode_avec_marge_de_7_jours(self):
        m = {"debut": "2026-09-24", "fin": "2026-10-08"}
        auj = dt.date(2026, 12, 1)
        self.assertTrue(maj_google.recouvre(m, dt.date(2026, 10, 14), dt.date(2026, 10, 20), auj))
        self.assertFalse(maj_google.recouvre(m, dt.date(2026, 10, 16), dt.date(2026, 10, 20), auj))
        en_cours = {"debut": "2026-11-02", "fin": None}
        self.assertTrue(maj_google.recouvre(en_cours, dt.date(2026, 11, 20), dt.date(2026, 11, 25), auj))

    def test_historique_livre_est_valide(self):
        h = json.loads(maj_google.HISTORIQUE.read_text(encoding="utf-8"))
        for m in h["mises_a_jour"]:
            self.assertIn(m["type"], maj_google.TYPES)
            self.assertTrue(m["source"].startswith("https://") and "google" in m["source"])
            if m["fin"]:
                self.assertLessEqual(m["debut"], m["fin"])


class TestAgentsIA(unittest.TestCase):
    ROBOTS = "User-agent: *\nDisallow: /admin\nContent-Signal: search=yes, ai-train=no\n\n" \
             "User-agent: GPTBot\nUser-agent: CCBot\nDisallow: /\n\nUser-agent: OAI-SearchBot\nAllow: /\n" \
             "Agentmap: /catalogue.json\n"

    def test_groupe_nomme_remplace_l_etoile(self):
        r = agents_ia.analyser_robots(self.ROBOTS)
        gpt = agents_ia.groupe_de(r, "gptbot")
        self.assertEqual(gpt["source"], "nommé")
        self.assertFalse(agents_ia.autorise(gpt["regles"], "/"))
        claude = agents_ia.groupe_de(r, "ClaudeBot")
        self.assertEqual(claude["source"], "*")
        self.assertTrue(agents_ia.autorise(claude["regles"], "/blog"))
        self.assertFalse(agents_ia.autorise(claude["regles"], "/admin/x"))
        self.assertEqual(claude["content_signal"], ["search=yes, ai-train=no"])
        self.assertEqual(r["agentmap"], ["/catalogue.json"])

    def test_regle_la_plus_longue_et_egalite(self):
        regles = [("disallow", "/dossier"), ("allow", "/dossier/public"), ("disallow", "*.pdf$")]
        self.assertTrue(agents_ia.autorise(regles, "/dossier/public/page"))
        self.assertFalse(agents_ia.autorise(regles, "/dossier/prive"))
        self.assertFalse(agents_ia.autorise(regles, "/doc.pdf"))
        self.assertTrue(agents_ia.autorise([("allow", "/a"), ("disallow", "/a")], "/a"))
        self.assertTrue(agents_ia.autorise([("disallow", "")], "/"))

    def test_content_signal(self):
        ok = agents_ia.lire_content_signal("search=yes, ai-input=yes, ai-train=no")
        self.assertEqual(ok["problemes"], [])
        ko = agents_ia.lire_content_signal("search=peut-etre, train=no, cassé")
        self.assertEqual(len(ko["problemes"]), 3)

    def test_llms_txt(self):
        bon = "# Décupler\n\n> Agence SEO.\n\n## Pages\n\n- [Accueil](https://decupler.com/)\n"
        self.assertEqual(agents_ia.evaluer_llms(200, bon)["verdict"], "ok")
        self.assertEqual(agents_ia.evaluer_llms(404, "")["verdict"], "absent")
        faux = agents_ia.evaluer_llms(200, "<!doctype html><html><body>Accueil</body></html>")
        self.assertEqual(faux["verdict"], "echec")

    def test_liens_markdown_et_catalogue(self):
        html = ('<link rel="alternate" type="text/markdown" href="/page.md">'
                '<link rel="ai-catalog" href="https://ex.fr/.well-known/ai-catalog.json">')
        ln = agents_ia.liens(html, "https://ex.fr/page")
        self.assertEqual(ln["markdown"], ["https://ex.fr/page.md"])
        self.assertEqual(ln["ai_catalog"], ["https://ex.fr/.well-known/ai-catalog.json"])

    def test_texte_visible_ignore_les_scripts(self):
        self.assertEqual(agents_ia.texte_visible("<p>Bonjour <b>vous</b></p><script>var x=1</script>"), "Bonjour vous")


class TestBudget(unittest.TestCase):
    def test_estimation_dataforseo(self):
        e = budget.estimer("mcp__dataforseo__api_request", {"path": "/v3/serp/google/organic/live/advanced"})
        self.assertEqual((e["fournisseur"], e["cout_usd"]), ("dataforseo", 0.002))
        e = budget.estimer("mcp__dataforseo__api_request", {"path": "/v3/keywords_data/google_ads/search_volume/live",
                                                              "data": [{}, {}]})
        self.assertEqual(e["cout_usd"], 0.1)
        self.assertTrue(budget.estimer("mcp__dataforseo__docs_search", {})["gratuit"])
        self.assertIsNone(budget.estimer("mcp__ahrefs__site-explorer-metrics", {})["cout_usd"])
        self.assertIsNone(budget.estimer("Bash", {})["fournisseur"])

    def test_decision(self):
        est = {"fournisseur": "dataforseo", "operation": "x", "cout_usd": 0.05, "gratuit": False}
        self.assertEqual(budget.decision(est, 0, {"mensuel": None, "demander": 0.5})[0], "allow")
        self.assertEqual(budget.decision(est, 9.98, {"mensuel": 10, "demander": 0.5})[0], "deny")
        cher = {**est, "cout_usd": 0.8}
        self.assertEqual(budget.decision(cher, 0, {"mensuel": 10, "demander": 0.5})[0], "ask")

    def test_cout_reel(self):
        self.assertEqual(budget.cout_reel('{"status_code":20000,"cost":0.0025}'), 0.0025)
        self.assertEqual(budget.cout_reel({"tasks": [{"cost": 0.01}, {"cost": 0.02}]}), 0.03)
        self.assertEqual(budget.cout_reel('texte [{"type":"text","text":"{\\"cost\\": 0.05}"}]'), 0.05)
        self.assertIsNone(budget.cout_reel("rien"))

    def test_journal_et_total_du_mois(self):
        with tempfile.TemporaryDirectory() as d:
            chemin = Path(d) / "depenses.csv"
            budget.consigner("dataforseo", "serp", 0.002, False, chemin=chemin)
            budget.consigner("ahrefs", "dr", None, True, chemin=chemin)
            m = budget.mois(budget.lire_journal(chemin))
        self.assertEqual(m["total_usd"], 0.002)
        self.assertEqual(m["par_outil"]["ahrefs"], {"appels": 1, "usd": 0.0})


class TestGscGcloud(unittest.TestCase):
    def test_fichier_adc_authorized_user_seulement(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "application_default_credentials.json").write_text(
                json.dumps({"type": "service_account"}), encoding="utf-8")
            ancien = {k: os.environ.get(k) for k in ("CLOUDSDK_CONFIG", "GOOGLE_APPLICATION_CREDENTIALS", "HOME")}
            os.environ.update({"CLOUDSDK_CONFIG": d, "HOME": d})
            os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
            try:
                self.assertIsNone(gsc.fichier_adc())
                (Path(d) / "application_default_credentials.json").write_text(
                    json.dumps({"type": "authorized_user", "client_id": "a", "client_secret": "b",
                                "refresh_token": "c"}), encoding="utf-8")
                self.assertEqual(gsc.fichier_adc(), Path(d) / "application_default_credentials.json")
            finally:
                for k, v in ancien.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v


if __name__ == "__main__":
    unittest.main()
