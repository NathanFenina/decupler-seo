"""Lecture des concurrents : c'est de ces mesures que sortent la longueur cible et le plan du brief."""

import json
import sys
import unittest

from _outils import SCRIPTS, DossierIsole, lancer

sys.path.insert(0, str(SCRIPTS))
import _contenu as C  # noqa: E402
import serp_concurrents as S  # noqa: E402

PAGE = """<!doctype html><html lang="fr"><head>
<title>Pompe à chaleur air-eau : prix et aides 2026</title>
<meta name="description" content="Prix, aides et installation d'une pompe à chaleur air-eau.">
<meta property="article:modified_time" content="2026-06-01T08:00:00+02:00">
<script type="application/ld+json">{"@context":"https://schema.org","@graph":[
 {"@type":"Article","datePublished":"2025-11-02"},{"@type":"FAQPage","mainEntity":[]}]}</script>
<style>.x{color:red}</style><script>var menu = "ne pas compter ces mots";</script>
</head><body>
<header class="site-header"><nav class="menu"><a href="/">Accueil</a> <a href="/contact">Contact</a></nav>
<h1>Pompe à chaleur air-eau : le guide</h1></header>
<div class="cookie-banner">Nous utilisons des cookies pour mesurer l'audience.</div>
<main><article>
<p>Vous hésitez entre deux devis ? Une pompe à chaleur air-eau chauffe la maison et l'eau sanitaire.</p>
<h2>Quel est le <em>prix</em> d'une pompe à chaleur air-eau ?</h2>
<p>Le prix dépend de la puissance et de la pose. <strong>Comptez le matériel et la main-d'œuvre.</strong></p>
<ul><li><p>Matériel</p></li><li>Pose</li></ul>
<h3>Les aides</h3>
<ol><li>MaPrimeRénov'</li><li>Certificats d'économies d'énergie</li></ol>
<table><tr><th>Poste</th><td>Coût</td></tr></table>
<img src="a.webp" alt="Unité extérieure"><img src="b.webp">
<p>Voir <a href="/aides">nos aides</a>, <a href="https://www.exemple.fr/devis">le devis</a> et
<a href="https://www.ademe.fr/guide">le guide de l'Ademe</a>.</p>
<h2>FAQ</h2>
<details><summary>La PAC est-elle rentable ?</summary><p>Oui, en général.</p></details>
<details><summary>Quel entretien ?</summary><p>Une visite par an.</p></details>
</article>
<aside class="sidebar"><h2>Articles similaires</h2><p>Autre sujet de barre latérale très long.</p></aside>
</main>
<footer><p>Mentions légales · Plan du site</p></footer>
</body></html>"""


def page_concurrente(url, rang, h2, mots_par_section=60, extra=""):
    """Une page lisible de plus de 200 mots, H2 donnés, texte sur le sujet."""
    phrase = ("La pompe à chaleur air-eau réduit la facture de chauffage. Le coefficient de performance "
              "mesure son rendement réel. L'installation demande un professionnel certifié RGE. ")
    n = max(1, mots_par_section // C.compter_mots(phrase))
    corps = "".join(f"<h2>{t}</h2><p>{phrase * n}{extra}</p>" for t in h2)
    html = f"<html><head><title>{h2[0]}</title></head><body><main><h1>Titre {rang}</h1>{corps}</main></body></html>"
    p = C.lire_html(html, url)
    p["rang"] = rang
    return p


SERP_BRUTE = [{
    "item_types": ["ai_overview", "organic", "people_also_ask", "related_searches"],
    "items": [
        {"type": "ai_overview", "markdown": "Une **pompe à chaleur air-eau** coûte entre…",
         "items": [{"type": "ai_overview_element", "text": "…",
                    "references": [{"domain": "www.ademe.fr", "url": "https://www.ademe.fr/pac", "title": "PAC"}]}],
         "references": [{"domain": "atlas-conseil.fr", "url": "https://atlas-conseil.fr/pac", "title": "Guide"},
                        {"domain": "www.ademe.fr", "url": "https://www.ademe.fr/pac", "title": "PAC"}]},
        {"type": "organic", "rank_group": 1, "url": "https://a.fr/pac", "domain": "a.fr", "title": "A"},
        {"type": "people_also_ask", "items": [{"title": "Quel est le prix d'une pompe à chaleur air-eau ?"},
                                              {"title": "Quelle aide pour une pompe à chaleur ?"},
                                              {"title": "Quel bruit fait une pompe à chaleur ?"}]},
        {"type": "organic", "rank_group": 2, "url": "https://www.atlas-conseil.fr/pac", "domain": "www.atlas-conseil.fr",
         "title": "Atlas"},
        {"type": "related_searches", "items": ["pac air eau prix", "pac air eau avis"]},
        {"type": "featured_snippet", "url": "https://a.fr/pac", "domain": "a.fr", "title": "A"},
    ]}]


class TestLectureHtml(unittest.TestCase):
    def setUp(self):
        self.p = C.lire_html(PAGE, "https://www.exemple.fr/pac")

    def test_balises_et_plan(self):
        self.assertEqual(self.p["titre"], "Pompe à chaleur air-eau : prix et aides 2026")
        self.assertTrue(self.p["meta"].startswith("Prix, aides"))
        self.assertEqual(self.p["h1"], ["Pompe à chaleur air-eau : le guide"])
        self.assertEqual(self.p["plan"], [[1, "Pompe à chaleur air-eau : le guide"],
                                          [2, "Quel est le prix d'une pompe à chaleur air-eau ?"],
                                          [3, "Les aides"], [2, "FAQ"]])
        self.assertEqual(self.p["questions_titres"], ["Quel est le prix d'une pompe à chaleur air-eau ?"])

    def test_navigation_scripts_et_barre_laterale_exclus(self):
        texte = self.p["texte"]
        for absent in ("Accueil", "cookies", "ne pas compter", "Articles similaires", "Mentions légales", "color"):
            self.assertNotIn(absent, texte)
        self.assertIn("Vous hésitez", texte)

    def test_listes_tableaux_images_liens(self):
        self.assertEqual(self.p["listes"], {"puces": 1, "numerotees": 1, "items": 4})
        self.assertEqual((self.p["tableaux"], self.p["images"], self.p["images_sans_alt"]), (1, 2, 1))
        # /aides et www.exemple.fr/devis sont internes, l'Ademe externe ; le menu ne compte pas.
        self.assertEqual((self.p["liens_internes"], self.p["liens_externes"]), (2, 1))
        self.assertEqual(self.p["gras"], 1)

    def test_faq_schemas_dates(self):
        self.assertTrue(self.p["faq"])
        self.assertEqual(self.p["schemas"], ["Article", "FAQPage"])
        self.assertEqual(self.p["dates"], {"publiee": "2025-11-02", "modifiee": "2026-06-01"})

    def test_markdown_garde_la_structure(self):
        md = self.p["markdown"]
        self.assertIn("## Quel est le prix d'une pompe à chaleur air-eau ?", md)
        self.assertIn("### Les aides", md)
        self.assertIn("- Matériel", md)          # un <p> dans un <li> reste une puce
        self.assertIn("2. Certificats d'économies d'énergie", md)

    def test_page_mal_formee_ne_plante_pas(self):
        p = C.lire_html("<html><body><main><h2>Titre<p>texte <b>non fermé</main>", "")
        self.assertEqual(p["plan"][0][0], 2)
        self.assertGreater(p["mots"], 0)

    def test_sans_main_on_retire_seulement_le_decor(self):
        p = C.lire_html("<body><nav>Menu Accueil</nav><div class='contenu'><h2>Sujet</h2><p>Un deux trois.</p></div>"
                        "<footer>Pied</footer></body>")
        self.assertEqual(p["texte"].split("\n"), ["Sujet", "Un deux trois."])

    def test_lecture_markdown(self):
        md = "# Titre\n\nIntro de la page.\n\n## Prix\n\n- a\n- b\n\n1. un\n2. deux\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n" \
             "Voir [le guide](https://ademe.fr/x) et ![schéma](s.png).\n\n## FAQ\n"
        p = C.lire_markdown(md, "https://www.exemple.fr/p")
        self.assertEqual(p["plan"], [[1, "Titre"], [2, "Prix"], [2, "FAQ"]])
        self.assertEqual(p["listes"], {"puces": 1, "numerotees": 1, "items": 4})
        self.assertEqual((p["tableaux"], p["images"], p["liens_externes"], p["faq"]), (1, 1, 1, True))


class TestTexte(unittest.TestCase):
    def test_compter_mots(self):
        self.assertEqual(C.compter_mots("L'entreprise a vendu 300 pompes à chaleur, en 2025."), 9)

    def test_phrases(self):
        self.assertEqual(len(C.decouper_phrases("Première phrase. Deuxième ? Oui ! Et 3 pompes.")), 4)

    def test_adresse_et_personne(self):
        vous = C.adresse_et_personne("Vous avez un projet. Nous vous rappelons. Votre devis est prêt. " * 5)
        self.assertEqual((vous["adresse"], vous["personne"]), ("vouvoiement", "nous"))
        tu = C.adresse_et_personne("Tu veux changer ta chaudière ? Je te montre comment faire, pas à pas. " * 5)
        self.assertEqual((tu["adresse"], tu["personne"]), ("tutoiement", "je"))
        neutre = C.adresse_et_personne("La pompe à chaleur chauffe la maison. Le ton de la marque reste sobre. " * 5)
        self.assertEqual((neutre["adresse"], neutre["personne"]), ("impersonnel", "impersonnel"))

    def test_centiles(self):
        self.assertEqual(C.mediane([800, 1200, 1000, 3000]), 1100)
        self.assertEqual(C.centile([800, 1000, 1200, 3000], 75), 1650)
        self.assertIsNone(C.mediane([]))

    def test_lisibilite_texte_simple_plus_haute(self):
        simple = ["Le chat dort. Il fait beau. On part tôt. Le train est là. Tout va bien. " * 3]
        dense = ["L'optimisation thermodynamique des installations résidentielles nécessite une évaluation "
                 "approfondie des caractéristiques énergétiques, architecturales et réglementaires spécifiques. " * 3]
        self.assertGreater(C.lisibilite(simple), C.lisibilite(dense))

    def test_ngrammes_recurrents(self):
        textes = ["Prenez rendez-vous avec un conseiller dès aujourd'hui. Le reste change.",
                  "Autre sujet. Prenez rendez-vous avec un conseiller pour en parler.",
                  "Rien de commun ici, vraiment rien."]
        expr = [x["expression"] for x in C.ngrammes_recurrents(textes)]
        self.assertIn("prenez rendez-vous avec un conseiller", expr)

    def test_url_interne_refusee(self):
        with self.assertRaises(C.PageIllisible):
            C.verifier_url("http://127.0.0.1/admin")
        with self.assertRaises(C.PageIllisible):
            C.verifier_url("file:///etc/passwd")


class TestSerp(unittest.TestCase):
    def test_lire_serp(self):
        s = S.lire_serp(SERP_BRUTE)
        self.assertEqual([o["rang"] for o in s["organique"]], [1, 2])
        self.assertEqual(len(s["questions"]), 3)
        self.assertEqual(s["recherches_associees"], ["pac air eau prix", "pac air eau avis"])
        self.assertTrue(s["ai_overview"]["present"])
        self.assertEqual([x["url"] for x in s["ai_overview"]["sources"]],
                         ["https://atlas-conseil.fr/pac", "https://www.ademe.fr/pac"])   # dédoublonnées
        self.assertTrue(s["ai_overview"]["extrait"].startswith("Une **pompe"))
        self.assertEqual(s["extrait_optimise"]["domaine"], "a.fr")
        self.assertIn("people_also_ask", s["features"])

    def test_serp_vide(self):
        s = S.lire_serp([])
        self.assertEqual((s["organique"], s["ai_overview"]["present"]), ([], False))


class TestAgregation(unittest.TestCase):
    def test_longueur_cible(self):
        lg = S.longueur_cible([900, 1100, 1500, 2600, 40])     # 40 mots : page bloquée, écartée
        self.assertEqual((lg["pages"], lg["mediane"], lg["p75"]), (4, 1300, 1775))
        self.assertEqual(lg["fourchette"], [1300, 1800])
        self.assertIsNone(S.longueur_cible([1200, 80]))

    def test_sujets_recurrents_mot_cle_retire(self):
        pages = [
            page_concurrente("https://a.fr/1", 1, ["Quel est le prix d'une pompe à chaleur ?",
                                                    "Comment fonctionne une pompe à chaleur ?", "Sommaire"]),
            page_concurrente("https://b.fr/2", 2, ["Prix de la pompe à chaleur", "Les aides disponibles"]),
            page_concurrente("https://c.fr/3", 3, ["Fonctionnement d'une pompe à chaleur", "Entretien annuel",
                                                    "Les aides de l'État"]),
        ]
        s = S.sujets(pages, "pompe à chaleur")
        par_sujet = {x["sujet"]: x["pages"] for x in s}
        self.assertEqual(par_sujet["Quel est le prix d'une pompe à chaleur ?"], 2)
        self.assertEqual(par_sujet["Comment fonctionne une pompe à chaleur ?"], 2)
        self.assertEqual(par_sujet["Les aides disponibles"], 2)
        self.assertEqual(par_sujet["Entretien annuel"], 1)
        self.assertNotIn("Sommaire", par_sujet)
        self.assertEqual(s[0]["pages"], 2)            # les récurrents d'abord

    def test_titre_generique(self):
        for t in ("FAQ", "Questions fréquentes", "En conclusion", "Articles similaires :", "Sommaire"):
            self.assertTrue(S.titre_generique(t), t)
        self.assertFalse(S.titre_generique("Conclusion du diagnostic thermique"))

    def test_question_couverte(self):
        titres = ["Quel est le prix d'une pompe à chaleur air-eau ?", "Les aides de l'État"]
        self.assertTrue(S.couvert("Quel prix pour une pompe à chaleur air-eau ?", titres, "pompe à chaleur"))
        self.assertFalse(S.couvert("Quel bruit fait une pompe à chaleur ?", titres, "pompe à chaleur"))

    def test_champ_commun_et_absents_du_client(self):
        pages = [page_concurrente(f"https://{x}.fr/p", i, ["Prix", "Aides"], mots_par_section=150,
                                  extra=" Le plancher chauffant aussi.")
                 for i, x in enumerate("abc", 1)]
        client = C.lire_html("<main><h2>Prix</h2><p>" + "La pompe à chaleur air-eau réduit la facture. " * 30
                             + "</p></main>", "https://www.atlas-conseil.fr/pac")
        ch = S.champ_commun(pages, client)
        self.assertEqual((ch["seuil_pages"], ch["pages_lues"]), (2, 3))
        termes = {x["terme"] for x in ch["expressions"]}
        self.assertIn("plancher chauffant", termes)
        absents = {x["terme"] for x in ch["absents_client"]}
        self.assertIn("plancher chauffant", absents)
        self.assertIn("coefficient", {x["terme"] for x in ch["absents_client"]})
        self.assertNotIn("facture", absents)

    def test_rapport_complet_et_rendu(self):
        pages = [page_concurrente("https://a.fr/pac", 1, ["Quel est le prix d'une pompe à chaleur air-eau ?",
                                                          "Les aides"], mots_par_section=400),
                 page_concurrente("https://c.fr/pac", 3, ["Prix d'une pompe à chaleur air-eau", "Les aides",
                                                          "Entretien"], mots_par_section=300)]
        client = page_concurrente("https://www.atlas-conseil.fr/pac", 2, ["Prix d'une pompe à chaleur air-eau"])
        serp = S.lire_serp(SERP_BRUTE)
        r = S.construire("pompe à chaleur air-eau", "France", "fr", serp, pages, client, "2026-09-29",
                         [{"url": "https://b.fr", "raison": "HTTP 403"}])
        self.assertEqual(r["structure"]["pages_lues"], 2)
        self.assertIsNotNone(r["longueur"])
        q = {x["question"]: x["traitee_par_le_top"] for x in r["questions"]}
        self.assertTrue(q["Quel est le prix d'une pompe à chaleur air-eau ?"])
        self.assertFalse(q["Quel bruit fait une pompe à chaleur ?"])
        c = r["client"]
        self.assertEqual(c["position"], 2)
        self.assertTrue(c["cite_par_ai_overview"])
        self.assertEqual([x["sujet"] for x in c["sujets_manquants"]], ["Les aides"])
        self.assertIn("Quelle aide pour une pompe à chaleur ?", c["questions_non_traitees"])
        self.assertNotIn("Quel est le prix d'une pompe à chaleur air-eau ?", c["questions_non_traitees"])
        json.dumps(r, ensure_ascii=False)              # sérialisable tel quel pour --json
        md = S.markdown(r)
        for attendu in ("# SERP — « pompe à chaleur air-eau »", "**Fourchette cible**", "## Sujets récurrents",
                        "| Quel bruit fait une pompe à chaleur ? | PAA | **non** |", "## Page du client face au top",
                        "https://b.fr (HTTP 403)", "- H2 Les aides"):
            self.assertIn(attendu, md)
        self.assertIn("## Source : https://a.fr/pac", S.contenus(r, pages))

    def test_slug(self):
        self.assertEqual(S.slug("Pompe à chaleur : prix 2026 ?"), "pompe-a-chaleur-prix-2026")


class TestEntitesEtMedias(unittest.TestCase):
    def test_entites_nommees(self):
        texte = ("Pour être cité par ChatGPT, Perplexity et Google AI Overviews, soignez votre E-E-A-T.\n"
                 "L'audit mesure la visibilité dans les LLM. Google Search Console ne le montre pas.\n"
                 "Perplexity cite ses sources. Ensuite, on agit. Selon Gartner, le trafic baisse.")
        e = {x["entite"]: x["occurrences"] for x in C.entites_nommees(texte)}
        self.assertEqual(e["Perplexity"], 2)                 # en tête de phrase, mais vu ailleurs au milieu
        for attendu in ("ChatGPT", "Google AI Overviews", "E-E-A-T", "LLM", "Google Search Console", "Gartner"):
            self.assertIn(attendu, e)
        self.assertNotIn("ChatGPT Perplexity", e)            # la virgule coupe la suite
        for absent in ("Ensuite", "Pour", "Selon", "L'audit"):
            self.assertNotIn(absent, e)

    def test_videos(self):
        html = '<main><p>x</p><iframe src="https://www.youtube.com/embed/abc"></iframe><video src="a.mp4"></video></main>'
        self.assertEqual(C.lire_html(html)["videos"], 2)
        self.assertEqual(C.lire_markdown("Voir [la démo](https://www.youtube.com/watch?v=abc).")["videos"], 1)

    def test_entites_communes_sans_le_mot_cle(self):
        extra = " Google Search Console et ChatGPT le confirment. Le GEO aussi."
        pages = [page_concurrente(f"https://{x}.fr/p", i, ["Prix", "Aides"], mots_par_section=150, extra=extra)
                 for i, x in enumerate("ab", 1)]
        pages.append(page_concurrente("https://c.fr/p", 3, ["Prix"], mots_par_section=250, extra=" Selon Semrush."))
        en = S.entites_communes(pages, "audit geo")
        communes = {x["entite"]: x["pages"] for x in en["communes"]}
        self.assertEqual(communes["Google Search Console"], 2)
        self.assertNotIn("GEO", communes)
        self.assertIn("Semrush", {x["entite"] for x in en["isolees"]})


class TestReplisSansDataForSEO(unittest.TestCase):
    def test_serp_firecrawl(self):
        brut = {"success": True, "data": {"web": [
            {"url": "https://b.fr/x", "title": "B", "description": "d", "position": 2},
            {"url": "https://www.a.fr/y", "title": "A", "description": "d", "position": 1}]}}
        s = S.lire_serp_firecrawl(brut)
        self.assertEqual([(o["rang"], o["domaine"]) for o in s["organique"]], [(1, "a.fr"), (2, "b.fr")])
        self.assertEqual(s["source"], "Firecrawl")
        self.assertFalse(s["ai_overview"]["mesure"])         # non mesuré, pas « absent »
        self.assertEqual(S.lire_serp_firecrawl([{"url": "https://c.fr"}])["organique"][0]["rang"], 1)

    def test_rapport_dit_non_mesure(self):
        s = S.lire_serp_firecrawl({"web": [{"url": "https://a.fr/pac", "title": "A"}]})
        r = S.construire("pompe à chaleur", "France", "fr", s, [], None, "2026-10-05")
        md = S.markdown(r)
        self.assertIn("| AI Overview | non mesuré", md)
        self.assertIn("SERP Firecrawl", md)
        self.assertTrue(S.lire_serp([])["ai_overview"]["mesure"])

    def test_questions_et_pages_relevees(self):
        self.assertEqual(S.lire_questions("# PAA du 5/10\n- Qu'est-ce que le GEO ?\n\nCombien coûte un audit ?\n"),
                         ["Qu'est-ce que le GEO ?", "Combien coûte un audit ?"])
        md = "# Titre\n\n## Prix\n\n" + "La pompe à chaleur air-eau réduit la facture de chauffage. " * 40
        relevees = S.lire_pages_json([{"url": "https://a.fr/pac", "markdown": md},
                                      {"data": {"markdown": md, "metadata": {"sourceURL": "https://b.fr/pac",
                                                                             "title": "B"}}},
                                      {"url": "https://vide.fr"}])
        self.assertEqual(sorted(relevees), ["https://a.fr/pac", "https://b.fr/pac"])
        page, raison, cout = S.lire_page("https://b.fr/pac", "fr", False, relevees)
        self.assertEqual((raison, cout, page["titre"]), (None, 0.0, "Titre"))
        self.assertGreater(page["mots"], 200)

    def test_candidats_maillage(self):
        urls = ["https://www.decupler.com/", "https://www.decupler.com/audit-geo/",
                "https://www.decupler.com/blog/visibilite-chatgpt/", "https://www.decupler.com/mentions-legales/",
                "https://www.decupler.com/blog/geo-ou-seo/"]
        champ = {"expressions": [], "mots": [{"terme": "visibilité"}, {"terme": "chatgpt"}]}
        c = S.candidats_maillage(urls, "audit geo", champ)
        self.assertEqual(c[0]["url"], "https://www.decupler.com/audit-geo/")
        trouvees = [x["url"] for x in c]
        self.assertIn("https://www.decupler.com/blog/visibilite-chatgpt/", trouvees)
        self.assertNotIn("https://www.decupler.com/mentions-legales/", trouvees)


class TestCommande(DossierIsole):
    def test_hors_ligne_depuis_firecrawl(self):
        md = "# Audit GEO\n\n## Méthode\n\n" + "L'audit GEO mesure la visibilité dans ChatGPT et Perplexity. " * 40
        serp = self.ecrire("serp.json", json.dumps({"data": {"web": [
            {"url": "https://a.fr/audit-geo", "title": "A", "position": 1}]}}))
        pages = self.ecrire("pages.json", json.dumps([{"url": "https://a.fr/audit-geo", "markdown": md}]))
        paa = self.ecrire("paa.txt", "Qu'est-ce qu'un audit GEO ?\n")
        plan = self.ecrire("sitemap.xml", "<urlset><url><loc>https://x.fr/audit-geo/</loc></url>"
                                          "<url><loc>https://x.fr/contact/</loc></url></urlset>")
        r = lancer("serp_concurrents.py", "--mot", "audit geo", "--langue", "fr", "--pays", "FR",
                   "--serp-firecrawl", str(serp), "--pages-json", str(pages), "--questions", str(paa),
                   "--sitemap", str(plan), "--json", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertEqual(d["serp"]["source"], "Firecrawl")
        self.assertEqual(d["pages"][0]["mots"], C.lire_markdown(md)["mots"])
        self.assertEqual(d["questions"][0]["question"], "Qu'est-ce qu'un audit GEO ?")
        self.assertEqual([x["url"] for x in d["maillage"]["candidats"]], ["https://x.fr/audit-geo/"])
        rapport = next((self.dossier / "recherche").glob("serp-audit-geo-*[0-9].md")).read_text(encoding="utf-8")
        self.assertIn("## Maillage interne — candidates du sitemap", rapport)

    def test_hors_ligne_depuis_une_serp_enregistree(self):
        # Sans résultat organique, aucune page n'est téléchargée : le test reste hors réseau.
        serp = [{"item_types": ["people_also_ask"], "items": [
            {"type": "people_also_ask", "items": [{"title": "Quel prix pour une PAC ?"}]}]}]
        f = self.ecrire("serp.json", json.dumps({"tasks": [{"result": serp}]}))
        r = lancer("serp_concurrents.py", "--mot", "pompe à chaleur", "--langue", "fr", "--pays", "FR",
                   "--serp-json", str(f), "--json", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertEqual(d["questions"][0]["question"], "Quel prix pour une PAC ?")
        self.assertIsNone(d["longueur"])
        fichiers = sorted(p.name for p in (self.dossier / "recherche").iterdir())
        self.assertEqual(len(fichiers), 2)
        self.assertTrue(fichiers[0].startswith("serp-pompe-a-chaleur-"))


if __name__ == "__main__":
    unittest.main()
