"""Indexation : annoncer sans casser quand une brique manque, suivre sans Search Console."""

import csv
import unittest

from _outils import DossierIsole, lancer


class TestIndexation(DossierIsole):
    def test_cle_generee(self):
        r = lancer("indexation.py", "cle", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("INDEXNOW_KEY", r.stdout)

    def test_annoncer_sans_cle_ni_gsc_remplit_le_registre(self):
        r = lancer("indexation.py", "annoncer", "https://www.exemple.com/a/", "https://www.exemple.com/b/",
                   "pas-une-url", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("sans clé", r.stdout)
        self.assertIn("non fait", r.stdout)
        with open(self.dossier / "donnees/indexation.csv", encoding="utf-8") as f:
            lignes = list(csv.DictReader(f))
        self.assertEqual([l["url"] for l in lignes], ["https://www.exemple.com/a/", "https://www.exemple.com/b/"])
        self.assertTrue(all(l["statut"] == "en attente" for l in lignes))

    def test_annoncer_sans_url(self):
        r = lancer("indexation.py", "annoncer", cwd=self.dossier)
        self.assertEqual(r.returncode, 1)

    def test_suivre_respecte_le_delai(self):
        lancer("indexation.py", "annoncer", "https://www.exemple.com/a/", cwd=self.dossier)
        r = lancer("indexation.py", "suivre", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Rien à vérifier", r.stdout)

    def test_suivre_sans_search_console(self):
        lancer("indexation.py", "annoncer", "https://www.exemple.com/a/", cwd=self.dossier)
        r = lancer("indexation.py", "suivre", "--delai", "0", cwd=self.dossier)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("Inspection impossible", r.stdout)


class TestConstatEtAuto(DossierIsole):
    def test_constat_regroupe_par_cause_et_se_remplace(self):
        import importlib, os, sys
        from _outils import SCRIPTS
        sys.path.insert(0, str(SCRIPTS))
        os.environ["SEO_DECUPLER_PROJET"] = str(self.dossier)
        try:
            indexation = importlib.import_module("indexation")
            lot = [{"url": "https://ex.fr/a/", "annoncee_le": "2026-10-01", "detail": "Détectée, actuellement non indexée"},
                   {"url": "https://ex.fr/b/", "annoncee_le": "2026-10-01", "detail": "Explorée, actuellement non indexée"},
                   {"url": "https://ex.fr/c/", "annoncee_le": "2026-10-01", "detail": "Détectée, actuellement non indexée"}]
            indexation.remonter_constat(lot)
            indexation.remonter_constat(lot[:1])
        finally:
            del os.environ["SEO_DECUPLER_PROJET"]
        texte = (self.dossier / "rapports/a-valider.md").read_text(encoding="utf-8")
        self.assertEqual(texte.count("<!-- indexation:debut -->"), 1)
        self.assertIn("1 URL : Google la connaît sans l'explorer", texte)
        self.assertNotIn("https://ex.fr/b/", texte)

    def test_auto_annonce_seulement_les_pages_recentes(self):
        import datetime as dt
        import functools
        import http.server
        import threading
        aujourd_hui = dt.date.today().isoformat()
        self.ecrire("site/sitemap_index.xml", '<sitemapindex><sitemap><loc>{base}/pages.xml</loc></sitemap></sitemapindex>')
        self.ecrire("site/pages.xml", "<urlset>"
                    f"<url><loc>https://ex.fr/neuve/</loc><lastmod>{aujourd_hui}</lastmod></url>"
                    "<url><loc>https://ex.fr/vieille/</loc><lastmod>2020-01-01</lastmod></url></urlset>")
        gestion = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(self.dossier / "site"))
        gestion.log_message = lambda *a: None
        serveur = http.server.ThreadingHTTPServer(("127.0.0.1", 0), gestion)
        base = f"http://127.0.0.1:{serveur.server_address[1]}"
        index = self.dossier / "site/sitemap_index.xml"
        index.write_text(index.read_text().replace("{base}", base))
        self.ecrire("site/robots.txt", f"User-agent: *\nSitemap: {base}/sitemap_index.xml\n")
        threading.Thread(target=serveur.serve_forever, daemon=True).start()
        try:
            r = lancer("indexation.py", "auto", "--jours", "2", "--sans-registre", cwd=self.dossier,
                       SEO_SITE_URL=base, NO_PROXY="127.0.0.1", no_proxy="127.0.0.1")
        finally:
            serveur.shutdown()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("2 URL dans le sitemap · 1 modifiée(s)", r.stdout)
        self.assertFalse((self.dossier / "donnees/indexation.csv").exists())


if __name__ == "__main__":
    unittest.main()
