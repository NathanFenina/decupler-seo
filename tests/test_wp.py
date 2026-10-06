"""Publication WordPress : ce qui part sur un site en ligne doit être prévisible.

Aucun site réel n'est appelé : les fonctions pures sont testées sur des
réponses REST figées (fixtures/), le client sur un transport simulé, et la
ligne de commande sur un faux WordPress local (127.0.0.1).
"""

import contextlib
import csv
import io
import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from _outils import SCRIPTS, DossierIsole, lancer

sys.path.insert(0, str(SCRIPTS))
import wp  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SITE = "https://www.atlas-conseil.example"
MOT_DE_PASSE = "abcd efgh ijkl mnop qrst uvwx"


def fixture(nom):
    return json.loads((FIXTURES / nom).read_text(encoding="utf-8"))


def carte_fixture():
    lignes = [wp.ligne_carte(i, SITE, "pages", "yoast") for i in fixture("wp_pages.json")]
    lignes += [wp.ligne_carte(i, SITE, "posts", "yoast") for i in fixture("wp_posts.json")]
    return wp.calculer_entrants(lignes)


class TestSlug(unittest.TestCase):
    def test_accents_et_ponctuation(self):
        self.assertEqual(wp.slugifier("Référencement local : l’essentiel !"), "referencement-local-l-essentiel")

    def test_ligatures(self):
        self.assertEqual(wp.slugifier("Cœur de cible"), "coeur-de-cible")

    def test_coupe_sur_un_tiret(self):
        slug = wp.slugifier("audit " * 30, longueur_max=20)
        self.assertLessEqual(len(slug), 20)
        self.assertFalse(slug.endswith("-"))
        self.assertTrue(all(m == "audit" for m in slug.split("-")))


class TestCharge(unittest.TestCase):
    def test_seulement_les_champs_fournis(self):
        charge = wp.construire_charge(titre="T", html="<p>x</p>", statut="draft", slug="t")
        self.assertEqual(charge, {"title": "T", "content": "<p>x</p>", "status": "draft", "slug": "t"})

    def test_mise_a_jour_sans_statut_ne_depublie_pas(self):
        # Envoyer status=draft sur une page en ligne la retirerait du site.
        self.assertNotIn("status", wp.construire_charge(html="<p>x</p>"))

    def test_taxonomies_image_et_meta(self):
        charge = wp.construire_charge(titre="T", categories=[3], etiquettes=[7, 8], image_une=40,
                                      meta={"rank_math_title": "X"})
        self.assertEqual(charge["categories"], [3])
        self.assertEqual(charge["tags"], [7, 8])
        self.assertEqual(charge["featured_media"], 40)
        self.assertEqual(charge["meta"], {"rank_math_title": "X"})

    def test_mode_ecriture(self):
        self.assertEqual(wp.mode_ecriture(None, "draft"), "creation")
        self.assertEqual(wp.mode_ecriture("draft", None), "brouillon")
        self.assertEqual(wp.mode_ecriture("publish", None), "revision")
        self.assertEqual(wp.mode_ecriture("publish", "draft"), "revision")
        self.assertEqual(wp.mode_ecriture("publish", "publish"), "en-ligne")

    def test_decision_du_garde_fou(self):
        self.assertTrue(wp.decision_ecriture("AUTORISE", False)[0])
        self.assertFalse(wp.decision_ecriture("DEMANDE_VALIDATION", False)[0])
        self.assertTrue(wp.decision_ecriture("DEMANDE_VALIDATION", True)[0])
        self.assertFalse(wp.decision_ecriture("BLOQUE", True)[0], "--valide ne lève jamais un blocage")


class TestChampsSEO(unittest.TestCase):
    def test_detection_extension(self):
        self.assertEqual(wp.detecter_plugin_seo(["wp/v2", "yoast/v1"]), "yoast")
        self.assertEqual(wp.detecter_plugin_seo(["wp/v2", "rankmath/v1"]), "rankmath")
        self.assertIsNone(wp.detecter_plugin_seo(["wp/v2", "oembed/1.0"]))

    def test_correspondance_yoast_rankmath(self):
        self.assertEqual(wp.charge_meta_seo("yoast", "T", "D"),
                         {"_yoast_wpseo_title": "T", "_yoast_wpseo_metadesc": "D"})
        self.assertEqual(wp.charge_meta_seo("rankmath", description="D"), {"rank_math_description": "D"})
        self.assertEqual(wp.charge_meta_seo(None, "T", "D"), {})

    def test_champ_ignore_par_wordpress_detecte(self):
        attendu = {"_yoast_wpseo_metadesc": "Nouvelle"}
        self.assertEqual(wp.meta_non_ecrits({"meta": {}}, attendu), ["_yoast_wpseo_metadesc"])
        self.assertEqual(wp.meta_non_ecrits({"meta": dict(attendu)}, attendu), [])
        self.assertEqual(wp.meta_non_ecrits({"meta": []}, attendu), ["_yoast_wpseo_metadesc"])

    def test_le_mu_plugin_cite_existe(self):
        # Le message d'échec renvoie vers un fichier réel, livré avec la méthode.
        self.assertTrue(wp.MU_PLUGIN_SEO.is_file(), wp.MU_PLUGIN_SEO)
        source = wp.MU_PLUGIN_SEO.read_text(encoding="utf-8")
        for champs in wp.CHAMPS_SEO.values():
            for champ in champs.values():
                self.assertIn(f"'{champ}'", source, champ)
        sortie = io.StringIO()
        with contextlib.redirect_stdout(sortie):
            wp.expliquer_meta_non_ecrite("rankmath", ["rank_math_title"])
        self.assertIn(str(wp.MU_PLUGIN_SEO), sortie.getvalue())

    def test_valeur_affichee_et_brute(self):
        page = fixture("wp_pages.json")[0]
        titre, description = wp.lire_seo_affiche(page)
        self.assertTrue(titre.startswith("Audit SEO local"))
        self.assertIn("d'audit", description)
        self.assertEqual(wp.lire_seo_champs(page, "yoast"), {"_yoast_wpseo_title": "", "_yoast_wpseo_metadesc": ""})

    def test_head_d_une_page_publique(self):
        tete = wp.extraire_head('<html><head><title>Titre servi</title><meta name="description" '
                                'content="Desc servie"><link rel="canonical" href="https://x.example/a/"></head></html>')
        self.assertEqual((tete["title"], tete["description"], tete["canonical"]),
                         ("Titre servi", "Desc servie", "https://x.example/a/"))

    def test_longueurs(self):
        self.assertEqual(wp.problemes_meta(None, "x" * 130), [])
        self.assertTrue(wp.problemes_meta(None, "x" * 90))
        self.assertTrue(wp.problemes_meta("t" * 75, None))


class TestCarte(unittest.TestCase):
    def test_ligne_depuis_la_reponse_rest(self):
        ligne = wp.ligne_carte(fixture("wp_pages.json")[0], SITE, "pages", "yoast")
        self.assertEqual(ligne["titre"], "Audit SEO local : la méthode en 7 étapes")
        self.assertEqual(ligne["h2"], "Pourquoi un audit local | Les 7 étapes")
        self.assertEqual(ligne["meta_titre"], "Audit SEO local : méthode en 7 étapes | Atlas Conseil")
        # Ni l'ancre vers soi-même, ni les médias, ni le lien externe.
        self.assertEqual(ligne["liens_internes"], "https://www.atlas-conseil.example/referencement-local/")
        self.assertEqual(ligne["nb_liens_externes"], 1)
        self.assertEqual(ligne["modifie"], "2026-08-02")

    def test_page_elementor_comptee_depuis_la_meta(self):
        # Régression : une page construite dans Elementor a un content presque vide ;
        # la carte la comptait à 0 mot et l'audit de contenu la déclarait « vide ».
        donnees = [{"elements": [{"widgetType": "heading", "settings": {"title": "Pourquoi un audit", "header_size": "h2"}},
                                 {"widgetType": "text-editor", "settings": {"editor": "<p>" + "mot " * 120 + "</p>",
                                                                            "_margin": {"top": "10"}}},
                                 {"widgetType": "toggle", "settings": {"tabs": [{"tab_title": "Q",
                                                                                  "tab_content": "Réponse courte ici."}]}}]}]
        item = {"id": 7, "link": f"{SITE}/audit/", "title": {"rendered": "Audit"}, "content": {"rendered": "<p>Bonjour</p>"},
                "meta": {"_elementor_data": json.dumps(donnees)}}
        ligne = wp.ligne_carte(item, SITE, "pages")
        self.assertGreater(ligne["nb_mots"], 120)
        self.assertEqual(ligne["h2"], "Pourquoi un audit")

    def test_page_sans_constructeur_inchangee(self):
        item = {"id": 8, "link": f"{SITE}/a/", "title": {"rendered": "A"}, "content": {"rendered": "<p>Un deux</p>"},
                "meta": {"_elementor_data": "[]"}}
        self.assertEqual(wp.ligne_carte(item, SITE, "pages")["nb_mots"], 2)
        self.assertEqual(wp.html_constructeur({"meta": {"_elementor_data": "{pas du json"}}), "")
        self.assertEqual(wp.html_constructeur({"meta": []}), "")

    def test_mots_sans_script(self):
        analyse = wp.analyser_contenu("<p>Un deux trois.</p><script>var a = b;</script><style>p{x:y}</style>", SITE)
        self.assertEqual(analyse["nb_mots"], 3)

    def test_liens_entrants(self):
        lignes = {l["url"]: l for l in carte_fixture()}
        self.assertEqual(lignes[f"{SITE}/referencement-local/"]["liens_entrants"], 1)
        self.assertEqual(lignes[f"{SITE}/audit-seo-local/"]["liens_entrants"], 0)

    def test_lien_relatif_et_www(self):
        self.assertEqual(wp.lien_interne("/contact/?utm=x#form", SITE), f"{SITE}/contact/")
        self.assertIsNotNone(wp.lien_interne("https://atlas-conseil.example/contact/", SITE))
        self.assertIsNone(wp.lien_interne("mailto:a@b.example", SITE))

    def test_doublons_potentiels(self):
        lignes = [{"url": f"{SITE}/audit-seo-local/", "titre": "Audit SEO local"},
                  {"url": f"{SITE}/blog/audit-local-seo/", "titre": "Audit local SEO"},
                  {"url": f"{SITE}/tarifs/", "titre": "Nos tarifs"}]
        paires = wp.doublons_potentiels(lignes)
        self.assertEqual(len(paires), 1)
        self.assertEqual({paires[0][1]["url"], paires[0][2]["url"]},
                         {f"{SITE}/audit-seo-local/", f"{SITE}/blog/audit-local-seo/"})


class TestMaillage(unittest.TestCase):
    def test_orpheline_recoit_une_source_pertinente(self):
        suggestions = wp.suggerer_liens(carte_fixture(), cible=f"{SITE}/audit-seo-local/")
        sources = [s["source"] for s in suggestions]
        self.assertIn(f"{SITE}/referencement-local/", sources)
        self.assertNotIn(f"{SITE}/blog/recette-crepes/", sources)

    def test_pas_de_suggestion_deja_posee(self):
        suggestions = wp.suggerer_liens(carte_fixture(), cible=f"{SITE}/referencement-local/", seuil=0.1)
        self.assertNotIn(f"{SITE}/audit-seo-local/", [s["source"] for s in suggestions])

    def test_pertinence_asymetrique(self):
        self.assertEqual(wp.pertinence({"audit", "local"}, {"audit", "local", "seo", "fiche"}), 1.0)
        self.assertEqual(wp.pertinence({"audit", "local", "seo"}, {"audit"}), 0.0)

    def test_sortants_et_cannibalisation_d_un_brouillon(self):
        lignes = carte_fixture()
        brouillon = {"url": "", "titre": "Audit SEO local : 7 étapes", "h2": "Fiche d'établissement | Avis",
                     "liens_internes": []}
        self.assertIn(f"{SITE}/audit-seo-local/", [l["url"] for _, l in wp.cannibalisation(brouillon, lignes)])
        cibles = [s["cible"] for s in wp.suggerer_sortants(brouillon, lignes)]
        self.assertNotIn(f"{SITE}/blog/recette-crepes/", cibles)

    def test_insertion_insensible_aux_accents(self):
        html = "<h2>Référencement local</h2><p>Le referencement local des PME.</p>"
        neuf, ancre = wp.inserer_lien(html, ["Référencement local"], f"{SITE}/referencement-local/")
        self.assertEqual(ancre, "referencement local")
        self.assertIn('<h2>Référencement local</h2>', neuf, "jamais dans un titre")
        self.assertIn(f'<p>Le <a href="{SITE}/referencement-local/">referencement local</a> des PME.</p>', neuf)

    def test_jamais_dans_un_lien_existant(self):
        html = '<p><a href="/x/">audit SEO local</a> puis audit SEO local.</p>'
        neuf, _ = wp.inserer_lien(html, ["audit SEO local"], "/y/")
        self.assertEqual(neuf, '<p><a href="/x/">audit SEO local</a> puis <a href="/y/">audit SEO local</a>.</p>')

    def test_ancre_absente_rien_n_est_invente(self):
        html = "<p>Rien à voir.</p>"
        self.assertEqual(wp.inserer_lien(html, ["audit SEO local"], "/y/"), (html, None))

    def test_mot_partiel_ignore(self):
        self.assertIsNone(wp.inserer_lien("<p>Les auditeurs locaux.</p>", ["audit"], "/y/")[1])

    def test_deja_lie(self):
        self.assertTrue(wp.deja_lie('<a href="/referencement-local">x</a>', f"{SITE}/referencement-local/", SITE))
        self.assertFalse(wp.deja_lie('<a href="/autre/">x</a>', f"{SITE}/referencement-local/", SITE))

    def test_ancres_candidates(self):
        ligne = {"titre": "Audit SEO local : la méthode", "meta_titre": "", "url": f"{SITE}/audit-seo-local/"}
        # Le titre court et le slug disent la même chose : une seule ancre, jamais le titre entier.
        self.assertEqual(wp.ancres_candidates(ligne), ["Audit SEO local"])
        self.assertEqual(wp.ancre_suggeree(ligne), "Audit SEO local")


class TestDurcir(unittest.TestCase):
    def test_lignes_vides_dans_style_et_script(self):
        html = "<style>\na{x:y}\n\n\nb{z:w}\n</style>\n\n<p>Texte</p>\n\n<script>\nf();\n\ng();\n</script>"
        durci = wp.durcir_html(html)
        self.assertEqual(durci.split("<style>")[1].split("</style>")[0], "\na{x:y}\nb{z:w}\n")
        self.assertIn("<script>\nf();\ng();\n</script>", durci)
        self.assertIn("\n\n<p>Texte</p>\n\n", durci, "les paragraphes restent à wpautop")

    def test_noscript_sur_une_ligne(self):
        self.assertEqual(wp.durcir_html("<noscript>\n<style>a{}</style>\n</noscript>"),
                         "<noscript><style>a{}</style></noscript>")


class TestErreurs(unittest.TestCase):
    def test_401_dit_quoi_faire(self):
        m = wp.message_erreur(401, b'{"code":"invalid_username","message":"Nom inconnu"}')
        self.assertIn("mot de passe d'application", m)
        self.assertIn("invalid_username", m)

    def test_403_droits_ou_pare_feu(self):
        m = wp.message_erreur(403, b'{"code":"rest_cannot_create"}', "/wp-json/wp/v2/pages")
        self.assertIn("Éditeur", m)
        self.assertIn("pare-feu", m)

    def test_404_sans_json(self):
        self.assertIn("permaliens", wp.message_erreur(404, b"<html>Not found</html>"))


class TestSauvegarde(unittest.TestCase):
    def test_format_de_cms_restore(self):
        import datetime as dt
        item = dict(fixture("wp_pages.json")[0], title={"raw": "Titre brut", "rendered": "Titre"},
                    content={"raw": "<p>brut</p>", "rendered": "<p>rendu</p>"}, excerpt={"raw": "", "rendered": "auto"})
        d = wp.donnees_sauvegarde(item, "pages", "yoast", dt.datetime(2026, 9, 1, 10, 30))
        for cle in ("cms", "type", "id", "url", "titre", "date", "title", "content", "excerpt", "status", "slug"):
            self.assertIn(cle, d)
        self.assertEqual((d["cms"], d["type"], d["content"], d["excerpt"]), ("wordpress", "pages", "<p>brut</p>", ""))
        self.assertEqual(d["meta"], {"_yoast_wpseo_title": "", "_yoast_wpseo_metadesc": ""})
        self.assertEqual(wp.nom_sauvegarde(item, dt.datetime(2026, 9, 1, 10, 30)), "2026-09-01-103000-audit-seo-local.json")

    def test_commande_journal(self):
        cmd = wp.commande_journal("https://x.example/a/", "meta", "avant", "après", requete="audit local")
        self.assertEqual(cmd[2:5], ["ajouter", "--url", "https://x.example/a/"])
        self.assertIn("--requete", cmd)
        self.assertNotIn("--auto", cmd)


class TestClient(unittest.TestCase):
    def client(self, reponses):
        appels = []

        def transport(methode, url, corps, entetes):
            appels.append((methode, url, corps, entetes))
            r = reponses.pop(0)
            if isinstance(r, Exception):
                raise r
            return r
        return wp.ClientWP(SITE, "robot", MOT_DE_PASSE, transport=transport, attendre=lambda s: None), appels

    def test_pagination_par_en_tete(self):
        pages = [(200, {"x-wp-totalpages": "3"}, json.dumps([{"id": i}]).encode()) for i in (1, 2, 3)]
        client, appels = self.client(pages)
        self.assertEqual([i["id"] for i in client.lister("/wp/v2/posts", par_page=1)], [1, 2, 3])
        self.assertIn("page=3", appels[-1][1])

    def test_pagination_sans_en_tete(self):
        client, appels = self.client([(200, {}, json.dumps([{"id": 1}, {"id": 2}]).encode()),
                                      (200, {}, b"[]")])
        self.assertEqual(len(list(client.lister("/wp/v2/pages", par_page=2))), 2)

    def test_coupure_reseau_retentee(self):
        client, appels = self.client([ConnectionResetError("coupé"), (503, {}, b""), (200, {}, b'{"ok": true}')])
        self.assertEqual(client.get("/wp/v2/pages/1"), {"ok": True})
        self.assertEqual(len(appels), 3)

    def test_erreur_4xx_jamais_retentee(self):
        client, appels = self.client([(401, {}, b'{"code":"incorrect_password"}')])
        with self.assertRaises(wp.ErreurWP) as ctx:
            client.get("/wp/v2/users/me")
        self.assertEqual(len(appels), 1)
        self.assertNotIn("abcd", str(ctx.exception))

    def test_creation_non_retentee(self):
        client, appels = self.client([ConnectionResetError("coupé")])
        with self.assertRaises(wp.ErreurConnexion):
            client.post("/wp/v2/posts", {"title": "x"}, reessayer=False)
        self.assertEqual(len(appels), 1)

    def test_authentification_sans_fuite(self):
        client, appels = self.client([(200, {}, b"{}")])
        client.get("/")
        self.assertTrue(appels[0][3]["Authorization"].startswith("Basic "))
        self.assertNotIn(MOT_DE_PASSE.replace(" ", ""), repr(client) + repr(vars(client).keys()))

    def test_reponse_non_json(self):
        client, _ = self.client([(200, {}, b"<html>maintenance</html>")])
        with self.assertRaises(wp.ErreurWP):
            client.get("/wp/v2/pages")


# ─── Faux WordPress local, pour la ligne de commande ─────────────────

class FauxWordPress(BaseHTTPRequestHandler):
    etat: dict = {}

    def log_message(self, *args):
        pass

    def repondre(self, statut, donnees, entetes=None):
        corps = json.dumps(donnees).encode()
        self.send_response(statut)
        self.send_header("Content-Type", "application/json")
        for k, v in (entetes or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        e = self.etat
        e["requetes"].append(("GET", self.path, self.headers.get("Authorization", "")))
        if u.path == "/wp-json/":
            return self.repondre(200, {"namespaces": ["wp/v2", "yoast/v1"]})
        base = u.path.removeprefix("/wp-json/wp/v2/").strip("/")
        if base in ("pages", "posts"):
            items = [i for i in e[base] if not q.get("slug") or i["slug"] == q["slug"]]
            par_page, page = int(q.get("per_page", 10)), int(q.get("page", 1))
            total = max(1, -(-len(items) // par_page))
            lot = items[(page - 1) * par_page: page * par_page]
            return self.repondre(200, lot, {"X-WP-TotalPages": str(total)})
        if "/" in base:
            type_, ident = base.split("/", 1)
            for i in e.get(type_, []):
                if str(i["id"]) == ident:
                    return self.repondre(200, i)
        return self.repondre(404, {"code": "rest_post_invalid_id"})

    def do_POST(self):
        longueur = int(self.headers.get("Content-Length", 0))
        corps = json.loads(self.rfile.read(longueur) or b"{}")
        e = self.etat
        e["requetes"].append(("POST", self.path, corps))
        chemin = urlparse(self.path).path.removeprefix("/wp-json/wp/v2/").strip("/")
        parties = chemin.split("/")
        if len(parties) == 1:
            cree = {"id": 99, "status": corps.get("status"), "link": f"{e['site']}/{corps.get('slug')}/",
                    "title": {"rendered": corps.get("title")}, "meta": {}}
            return self.repondre(201, cree)
        if len(parties) == 3 and parties[2] == "autosaves":
            return self.repondre(200, {"id": 500, "parent": int(parties[1])})
        for i in e.get(parties[0], []):
            if str(i["id"]) == parties[1]:
                i.setdefault("meta", {}).update(corps.get("meta", {}))
                return self.repondre(200, i)
        return self.repondre(404, {"code": "rest_post_invalid_id"})


class TestLigneDeCommande(DossierIsole):
    def setUp(self):
        super().setUp()
        self.serveur = ThreadingHTTPServer(("127.0.0.1", 0), FauxWordPress)
        self.site = f"http://127.0.0.1:{self.serveur.server_port}"
        FauxWordPress.etat = {"site": self.site, "requetes": []}
        for base, fichier in (("pages", "wp_pages.json"), ("posts", "wp_posts.json")):
            items = fixture(fichier)
            for i in items:
                i["link"] = i["link"].replace(SITE, self.site)
                i["content"]["rendered"] = i["content"]["rendered"].replace(SITE, self.site)
                i["content"]["raw"] = i["content"]["rendered"]
            FauxWordPress.etat[base] = items
        threading.Thread(target=self.serveur.serve_forever, daemon=True).start()
        self.ecrire("contenus/guide.html", "<p>Un guide.</p>\n\n<h2>Partie</h2>\n<p>Suite.</p>")

    def tearDown(self):
        self.serveur.shutdown()
        self.serveur.server_close()
        super().tearDown()

    def wp(self, *args, mode="autonomous", **env):
        if mode:
            self.ecrire("decupler-seo.config.yml", f"mode: {mode}\npublication:\n  statut_par_defaut: draft\n")
        variables = {"WP_SITE_URL": self.site, "WP_USER": "robot", "WP_APP_PASSWORD": MOT_DE_PASSE,
                     "SEO_ALLOWED_DOMAINS": f"127.0.0.1:{self.serveur.server_port}",
                     "NO_PROXY": "127.0.0.1", "no_proxy": "127.0.0.1", "HTTP_PROXY": "", "http_proxy": ""}
        variables.update(env)
        r = lancer("wp.py", *args, cwd=self.dossier, **variables)
        self.assertNotIn(MOT_DE_PASSE, r.stdout + r.stderr)
        self.assertNotIn(MOT_DE_PASSE.replace(" ", ""), r.stdout + r.stderr)
        return r

    def ecritures(self):
        return [r for r in FauxWordPress.etat["requetes"] if r[0] == "POST"]

    def test_brouillon_par_defaut(self):
        r = self.wp("publier", "--html", "contenus/guide.html", "--titre", "Guide de l'audit")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        (_, chemin, corps), = self.ecritures()
        self.assertTrue(chemin.startswith("/wp-json/wp/v2/posts"))
        self.assertEqual((corps["status"], corps["slug"]), ("draft", "guide-de-l-audit"))
        self.assertFalse((self.dossier / "journal/modifications.csv").exists(), "un brouillon ne se mesure pas")

    def test_publication_directe_refusee_en_assisted(self):
        r = self.wp("publier", "--html", "contenus/guide.html", "--titre", "Guide", "--statut", "publish",
                    mode="assisted")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(self.ecritures(), [])

    def test_mode_safe_rien_ne_part(self):
        r = self.wp("publier", "--html", "contenus/guide.html", "--titre", "Guide", mode="safe")
        self.assertEqual(r.returncode, 2)
        r = self.wp("publier", "--html", "contenus/guide.html", "--titre", "Guide", SEO_SAFE_MODE="1")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(self.ecritures(), [])

    def test_slug_existant_refuse(self):
        r = self.wp("publier", "--html", "contenus/guide.html", "--titre", "X", "--slug", "audit-seo-local",
                    "--type", "page")
        self.assertEqual(r.returncode, 1)
        self.assertIn("--id 12", r.stderr)

    def test_simulation_n_ecrit_rien(self):
        r = self.wp("publier", "--html", "contenus/guide.html", "--titre", "Guide", "--statut", "publish", "--simuler")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Simulation", r.stdout)
        self.assertEqual(self.ecritures(), [])

    def test_meta_sauvegardee_et_journalisee(self):
        nouvelle = ("Audit SEO local en 7 étapes : fiche d'établissement, avis clients, pages locales et "
                    "suivi des positions, la méthode complète pour les PME.")
        r = self.wp("meta", "--url", f"{self.site}/audit-seo-local/", "--description", nouvelle,
                    "--requete", "audit seo local")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        (_, chemin, corps), = self.ecritures()
        self.assertEqual(corps, {"meta": {"_yoast_wpseo_metadesc": nouvelle}})
        sauvegardes = list(self.dossier.glob(".*/backups/*.json"))
        self.assertEqual(len(sauvegardes), 1)
        self.assertEqual(json.loads(sauvegardes[0].read_text())["id"], 12)
        with open(self.dossier / "journal/modifications.csv", encoding="utf-8") as f:
            (ligne,) = list(csv.DictReader(f))
        self.assertEqual((ligne["type"], ligne["apres"], ligne["requete"]), ("meta", nouvelle, "audit seo local"))
        self.assertEqual(ligne["avant"], "Ancienne description de la page d'audit local.")

    def test_controle_contenu_bloquant(self):
        self.ecrire("contenus/mauvais.html", "<p>Résultats garantis en 30 jours.</p>")
        r = self.wp("publier", "--html", "contenus/mauvais.html", "--titre", "Mauvais")
        self.assertEqual(r.returncode, 1)
        self.assertIn("controle_contenu", r.stderr)
        self.assertEqual(self.ecritures(), [])

    def test_mise_a_jour_d_une_page_en_ligne_part_en_revision(self):
        r = self.wp("publier", "--html", "contenus/guide.html", "--id", "12", "--type", "page")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        (_, chemin, corps), = self.ecritures()
        self.assertEqual(chemin, "/wp-json/wp/v2/pages/12/autosaves")
        self.assertNotIn("status", corps)
        self.assertEqual(len(list(self.dossier.glob(".*/backups/*.json"))), 1)

    def test_mise_en_ligne_directe_journalisee(self):
        r = self.wp("publier", "--html", "contenus/guide.html", "--id", "12", "--type", "page",
                    "--statut", "publish")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        (_, chemin, corps), = self.ecritures()
        self.assertEqual((chemin, corps["status"]), ("/wp-json/wp/v2/pages/12", "publish"))
        with open(self.dossier / "journal/modifications.csv", encoding="utf-8") as f:
            self.assertEqual(list(csv.DictReader(f))[0]["type"], "contenu")

    def test_meta_deja_a_jour(self):
        r = self.wp("meta", "--url", f"{self.site}/audit-seo-local/", "--titre-seo",
                    "Audit SEO local : méthode en 7 étapes | Atlas Conseil", "--hors-format")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Déjà à jour", r.stdout)
        self.assertEqual(self.ecritures(), [])

    def test_remplacer_ignore_les_pages_ambigues(self):
        FauxWordPress.etat["pages"][0]["content"]["raw"] += "<!-- b -->x<!-- /b --><!-- b -->y<!-- /b -->"
        FauxWordPress.etat["pages"][1]["content"]["raw"] += "<!-- b -->ancien<!-- /b -->"
        r = self.wp("remplacer", "--motif", "<!-- b -->.*?<!-- /b -->", "--par", "<!-- b -->neuf<!-- /b -->",
                    "--types", "pages")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("2 occurrences, page ignorée", r.stdout)
        (_, chemin, corps), = self.ecritures()
        self.assertEqual(chemin, "/wp-json/wp/v2/pages/14/autosaves")
        self.assertIn("<!-- b -->neuf<!-- /b -->", corps["content"])

    def test_carte_puis_maillage_en_revision(self):
        r = self.wp("carte", "--types", "pages,posts")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(self.dossier / "donnees/carte-contenu.csv", encoding="utf-8") as f:
            lignes = list(csv.DictReader(f))
        self.assertEqual(len(lignes), 4)
        r = self.wp("maillage", "--cible", f"{self.site}/audit-seo-local/", "--appliquer")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        chemins = [c for _, c, _ in self.ecritures()]
        self.assertTrue(chemins, r.stdout)
        # Les sources sont en ligne : jamais de modification directe, une révision.
        self.assertTrue(all(c.endswith("/autosaves") for c in chemins), chemins)
        corps = self.ecritures()[0][2]["content"]
        self.assertIn(f'href="{self.site}/audit-seo-local/"', corps)


class TestSansIdentifiants(DossierIsole):
    def test_message_clair(self):
        self.ecrire("g.html", "<p>x</p>")
        r = lancer("wp.py", "publier", "--html", "g.html", "--titre", "G", cwd=self.dossier)
        self.assertEqual(r.returncode, 1)
        self.assertIn("WP_APP_PASSWORD", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_simulation_hors_ligne(self):
        self.ecrire("g.html", "<p>x</p>")
        r = lancer("wp.py", "publier", "--html", "g.html", "--titre", "G", "--simuler", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Simulation", r.stdout)


if __name__ == "__main__":
    unittest.main()
