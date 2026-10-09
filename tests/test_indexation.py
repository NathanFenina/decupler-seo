"""Indexation : annoncer sans casser quand une brique manque, suivre sans Search Console."""

import csv
import json
import os
import sys
import threading
import unittest
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

from _outils import SCRIPTS, DossierIsole, environnement_propre, lancer

sys.path.insert(0, str(SCRIPTS))
import indexation  # noqa: E402

CLE = "0123456789abcdef0123456789abcdef"


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


class _Reponse:
    status = 200

    def __init__(self, texte):
        self.texte = texte

    def read(self):
        return self.texte.encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestReessais(unittest.TestCase):
    def test_coupure_reseau_retentee(self):
        effets = [urllib.error.URLError("connexion coupée"), ConnectionResetError("reset"), _Reponse("ok")]
        with mock.patch("urllib.request.urlopen", side_effect=effets) as appel, \
                mock.patch.object(indexation.time, "sleep") as pause:
            self.assertEqual(indexation.http("https://ex.fr/"), (200, "ok"))
        self.assertEqual(appel.call_count, 3)
        self.assertEqual(pause.call_count, 2)

    def test_trois_essais_au_plus(self):
        with mock.patch("urllib.request.urlopen", side_effect=TimeoutError("délai")) as appel, \
                mock.patch.object(indexation.time, "sleep"):
            code, texte = indexation.http("https://ex.fr/")
        self.assertEqual((code, appel.call_count), (0, 3))
        self.assertIn("3 essais", texte)

    def test_erreur_http_jamais_retentee(self):
        erreur = urllib.error.HTTPError("https://ex.fr/", 404, "Not Found", {}, None)
        with mock.patch("urllib.request.urlopen", side_effect=erreur) as appel, \
                mock.patch.object(indexation.time, "sleep") as pause:
            self.assertEqual(indexation.http("https://ex.fr/")[0], 404)
        self.assertEqual((appel.call_count, pause.call_count), (1, 0))


class FauxSite(BaseHTTPRequestHandler):
    etat: dict = {}

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.etat["requetes"].append((self.path, self.headers.get("Authorization", "")))
        if self.path.startswith("/wp-json/seo-indexnow/v1/etat") and self.etat.get("extension"):
            corps, code = json.dumps({"cle": CLE, "fichier": f"/{CLE}.txt"}).encode(), 200
        else:
            corps, code = json.dumps({"code": "rest_no_route"}).encode(), 404
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)


class TestCleLueSurLeSite(DossierIsole):
    def setUp(self):
        super().setUp()
        self.serveur = ThreadingHTTPServer(("127.0.0.1", 0), FauxSite)
        self.hote = f"127.0.0.1:{self.serveur.server_port}"
        FauxSite.etat = {"requetes": [], "extension": True}
        threading.Thread(target=self.serveur.serve_forever, daemon=True).start()
        env = environnement_propre(WP_SITE_URL=f"http://{self.hote}", WP_USER="robot",
                                   WP_APP_PASSWORD="abcd efgh ijkl mnop", SEO_DECUPLER_PROJET=str(self.dossier),
                                   NO_PROXY="127.0.0.1", no_proxy="127.0.0.1", HTTP_PROXY="", http_proxy="")
        self.env = mock.patch.dict(os.environ, env, clear=True)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.serveur.shutdown()
        self.serveur.server_close()
        super().tearDown()

    def test_cle_lue_par_l_api_de_l_extension(self):
        cle, origine = indexation.cle_indexnow(self.hote)
        self.assertEqual(cle, CLE)
        self.assertNotIn(CLE, origine)
        self.assertIn("seo-indexnow", origine)
        chemin, auth = FauxSite.etat["requetes"][0]
        self.assertTrue(chemin.startswith("/wp-json/seo-indexnow/v1/etat"))
        self.assertTrue(auth.startswith("Basic "))

    def test_la_variable_passe_avant_le_site(self):
        os.environ["INDEXNOW_KEY"] = "cle-de-la-variable"
        self.assertEqual(indexation.cle_indexnow(self.hote), ("cle-de-la-variable", "INDEXNOW_KEY"))
        self.assertEqual(FauxSite.etat["requetes"], [])

    def test_extension_absente_ou_autre_site(self):
        FauxSite.etat["extension"] = False
        cle, origine = indexation.cle_indexnow(self.hote)
        self.assertEqual(cle, "")
        self.assertIn("seo-indexnow", origine)
        self.assertEqual(indexation.cle_indexnow("www.autre-site.fr")[0], "")

    def test_la_cle_n_apparait_jamais_en_entier(self):
        envois = []

        def faux_http(url, donnees=None):
            envois.append((url, donnees))
            return (404, "") if url.endswith(".txt") else (200, "")

        url = f"http://{self.hote}/page/"
        with mock.patch.object(indexation, "http", side_effect=faux_http):
            refus = indexation.indexnow([url])
            self.assertNotIn(CLE, refus)
            self.assertIn("refusé", refus)
            envois.clear()
            with mock.patch.object(indexation, "http", side_effect=lambda u, d=None: envois.append((u, d)) or
                                   ((200, CLE) if u.endswith(".txt") else (202, ""))):
                statut = indexation.indexnow([url])
        self.assertTrue(statut.startswith("ok"), statut)
        self.assertNotIn(CLE, statut)
        self.assertEqual(json.loads(envois[-1][1])["key"], CLE)

    def test_sans_identifiants_wordpress(self):
        for nom in ("WP_SITE_URL", "WP_USER", "WP_APP_PASSWORD"):
            os.environ.pop(nom)
        self.assertEqual(indexation.indexnow([f"http://{self.hote}/a/"]),
                         "sans clé (INDEXNOW_KEY absente, identifiants WordPress absents)")


if __name__ == "__main__":
    unittest.main()
