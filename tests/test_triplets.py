"""Triplets et entités : ce que la page affirme, ce que le registre exige, ce qui se contredit.

Tout est hors réseau : pages écrites à la main, registre en CSV temporaire,
API Wikidata simulée.
"""

import json
import sys
import unittest
import urllib.error
from unittest import mock

from _outils import RACINE, SCRIPTS, DossierIsole, lancer

sys.path.insert(0, str(SCRIPTS))
import triplets as t  # noqa: E402

SITE = "https://www.atlas-conseil.example"

ENTITES_CSV = """entite,type,qid,sameAs,definition,alias
# Exemple,Thing,Q1,https://fr.wikipedia.org/wiki/Exemple,Ligne ignorée,
Atlas Conseil,Organization,,https://www.atlas-conseil.example/#organization | https://www.atlas-conseil.example/,Cabinet d'expertise comptable à Lyon,
Expertise comptable,Thing,Q111111,https://fr.wikipedia.org/wiki/Expertise_comptable,Profession réglementée,expert-comptable
Lyon,City,Q222222,https://fr.wikipedia.org/wiki/Lyon,Commune française,
Liasse fiscale,DefinedTerm,,,Ensemble des formulaires fiscaux joints à la déclaration de résultat,
"""

TRIPLETS_CSV = """sujet,predicat,objet,source,date_verif,pages
# Atlas Conseil,est situé à,Lyon,exemple commenté,2026-09-01,*
Atlas Conseil,est situé à,Lyon,mentions légales,2026-09-01,*
Le bilan annuel,coûte,1 200 € HT,grille tarifaire 2026,2026-09-01,bilan-annuel
Le bilan annuel,dure,3 semaines,grille tarifaire 2026,2026-09-01,/offres/bilan-annuel/
La liasse fiscale,accompagne,la déclaration de résultat,impots.gouv.fr,2026-09-01,bilan-annuel
Le forfait social,représente,5 %,texte officiel,2026-09-01,autre-page
"""

GRAPHE = {"@context": "https://schema.org", "@graph": [
    {"@type": "Organization", "@id": f"{SITE}/#organization", "name": "Atlas Conseil", "url": f"{SITE}/",
     "knowsAbout": [{"@type": "Thing", "name": "Expertise comptable",
                     "sameAs": ["https://www.wikidata.org/wiki/Q111111"]}]},
    {"@type": "WebPage", "@id": f"{SITE}/offres/bilan-annuel/#webpage", "name": "Bilan annuel",
     "about": {"@type": "Thing", "name": "Bilan comptable"},
     "mentions": [{"@type": "City", "name": "Lyon", "sameAs": ["https://www.wikidata.org/wiki/Q999"]},
                  {"@type": "Thing", "name": "Expertise comptable"},
                  {"@type": "Thing", "name": "Comptabilité analytique"}]},
    {"@type": "Service", "@id": f"{SITE}/offres/bilan-annuel/#service", "name": "Bilan annuel",
     "provider": {"@id": f"{SITE}/#organization"}},
]}


def page_html(corps, graphe=None, titre="Bilan annuel à Lyon — Atlas Conseil"):
    ld = f'<script type="application/ld+json">{json.dumps(graphe, ensure_ascii=False)}</script>' if graphe else ""
    return (f"<!doctype html><html><head><title>{titre}</title>{ld}</head><body>"
            f"<nav><a href='/'>Accueil</a> Le bilan annuel coûte 990 € HT</nav>"
            f"<main>{corps}</main><footer>Atlas Conseil — Lyon</footer></body></html>")


CORPS = ("<h1>Bilan annuel pour les TPE à Lyon</h1>"
         "<p>Atlas Conseil est un cabinet d'expertise comptable situé à Lyon. "
         "Le bilan annuel coûte 1 200 € HT et dure trois semaines.</p>"
         "<p>Il comprend la liasse fiscale. La liasse fiscale accompagne la déclaration de résultat de "
         "l'entreprise. Chaque expert-comptable du cabinet suit au plus 40 dossiers par an.</p>"
         "<p>Le bilan comptable résume la situation financière de l'entreprise à la clôture de l'exercice.</p>")


def un(phrase, predicat):
    return next(x for x in t.triplets_phrase(phrase) if x["predicat"] == predicat)


class TestQuantites(unittest.TestCase):
    def q(self, phrase):
        return [(x["min"], x["max"], x["unite"]) for x in t.quantites(phrase)]

    def test_monnaies_taxes_et_periodes(self):
        self.assertEqual(self.q("Le bilan coûte 1 200 € HT."), [(1200, 1200, "EUR HT")])
        self.assertEqual(self.q("Comptez 45 €/mois."), [(45, 45, "EUR/mois")])
        self.assertEqual(self.q("Le logiciel coûte 45 € HT par mois."), [(45, 45, "EUR HT/mois")])
        self.assertEqual(self.q("Un budget de 1,5 million d'euros."), [(1500000, 1500000, "EUR")])
        self.assertEqual(self.q("The review costs €1,500 per year."), [(1500, 1500, "EUR/an")])
        self.assertEqual(self.q("Une avance de 50 k€."), [(50000, 50000, "EUR")])

    def test_fourchettes(self):
        self.assertEqual(self.q("Entre 3 000 et 5 000 euros."), [(3000, 5000, "EUR")])
        self.assertEqual(self.q("De 1 200 € à 2 000 €."), [(1200, 2000, "EUR")])
        self.assertEqual(self.q("Il faut 3 à 5 jours ouvrés."), [(3, 5, "jour ouvré")])

    def test_pourcentages_durees_et_comptes(self):
        self.assertEqual(self.q("Le taux normal est de 20 %."), [(20, 20, "%")])
        self.assertEqual(self.q("Le taux réduit est de 5,5 %."), [(5.5, 5.5, "%")])
        self.assertEqual(self.q("La mission dure trois semaines."), [(3, 3, "semaine")])
        self.assertEqual(self.q("Le cabinet compte 14 collaborateurs."), [(14, 14, "salarié")])

    def test_dates_et_annees(self):
        self.assertEqual(self.q("Depuis le 1er septembre 2026, la règle change."), [("2026-09-01", "2026-09-01", "date")])
        self.assertEqual(self.q("Échéance au 15/05/2027."), [("2027-05-15", "2027-05-15", "date")])
        self.assertEqual(self.q("Fondé en 2009."), [(2009, 2009, "année")])
        self.assertEqual(self.q("En mars 2026, tout change."), [("2026-03", "2026-03", "date")])

    def test_articles_ne_sont_pas_des_chiffres(self):
        self.assertEqual(self.q("Atlas Conseil est une entreprise familiale."), [])
        self.assertEqual(self.q("La mission dure un an."), [(1, 1, "an")])

    def test_formatage(self):
        self.assertEqual(t.formater(t.quantites("1 200 € HT")[0]), "1 200 EUR HT")
        self.assertEqual(t.formater(t.quantites("3 à 5 jours")[0]), "3–5 jour")
        self.assertEqual(t.formater(t.quantites("fondé en 2009")[0]), "2009")


class TestTriplets(unittest.TestCase):
    def test_definition_par_la_copule(self):
        x = un("Atlas Conseil est un cabinet d'expertise comptable situé à Lyon.", "est")
        self.assertEqual((x["sujet"], x["objet"], x["genre"]),
                         ("Atlas Conseil", "un cabinet d'expertise comptable situé à Lyon", "definition"))
        self.assertFalse(x["sujet_implicite"])

    def test_permet_de_et_verbe_relationnel(self):
        x = un("Le logiciel de paie permet de produire la DSN chaque mois.", "permet de")
        self.assertEqual((x["sujet"], x["objet"]), ("Le logiciel de paie", "produire la DSN chaque mois"))
        x = un("Le barème classe les entreprises selon leur chiffre d'affaires.", "classe")
        self.assertEqual(x["objet"], "les entreprises selon leur chiffre d'affaires")

    def test_prix_et_duree_coordonnes(self):
        ts = t.triplets_phrase("Le bilan annuel coûte 1 200 € HT et dure trois semaines.")
        faits = {(x["sujet"], x["predicat"], t.formater(x["valeur"])) for x in ts}
        self.assertIn(("Le bilan annuel", "coûte", "1 200 EUR HT"), faits)
        self.assertIn(("Le bilan annuel", "dure", "3 semaine"), faits)

    def test_copule_chiffree_et_contexte(self):
        x = un("En 2026, le taux normal de TVA est de 20 %.", "est")
        self.assertEqual((x["sujet"], x["objet"], x["contexte"]), ("le taux normal de TVA", "20 %", "En 2026"))

    def test_apposition_est_une_definition(self):
        ts = t.triplets_phrase("Atlas Conseil, cabinet d'expertise comptable, accompagne les TPE du Rhône.")
        self.assertIn(("Atlas Conseil", "est", "cabinet d'expertise comptable"),
                      {(x["sujet"], x["predicat"], x["objet"]) for x in ts})
        self.assertEqual(un("Atlas Conseil, cabinet d'expertise comptable, accompagne les TPE du Rhône.",
                            "accompagne")["sujet"], "Atlas Conseil")

    def test_sigle_defini(self):
        x = un("La déclaration sociale nominative (DSN) remplace la plupart des déclarations sociales.", "désigne")
        self.assertEqual((x["sujet"], x["objet"]), ("DSN", "déclaration sociale nominative"))
        self.assertEqual(un("La déclaration sociale nominative (DSN) remplace les déclarations.", "remplace")["sujet"],
                         "La déclaration sociale nominative")

    def test_sujet_implicite_et_historique(self):
        self.assertTrue(un("Il coûte 45 € par mois.", "coûte")["sujet_implicite"])
        self.assertTrue(un("Cette offre coûte 45 € par mois.", "coûte")["sujet_implicite"])
        self.assertTrue(un("Auparavant, le bilan annuel coûtait 1 000 € HT.", "coûte")["historique"])

    def test_negation_question_et_idiome(self):
        x = un("Le bilan annuel n'est pas obligatoire pour une micro-entreprise.", "n'est pas")
        self.assertEqual((x["sujet"], x["objet"]), ("Le bilan annuel", "obligatoire pour une micro-entreprise"))
        x = un("L'audit, l'optimisation et la mesure ne nécessitent pas de présence sur place.", "n'exige pas")
        self.assertEqual(x["sujet"], "L'audit, l'optimisation et la mesure")
        self.assertEqual(t.triplets_phrase("Le bilan annuel est-il obligatoire ?"), [])
        self.assertEqual(t.triplets_phrase("Mieux vaut trois pages solides."), [])  # « vaut » sans montant
        self.assertEqual(un("L'aide au recrutement coûte 500 €.", "coûte")["sujet"], "L'aide au recrutement")

    def test_contexte_seul_rend_le_sujet_implicite(self):
        x = un("Sur un marché saturé, c'est la citation qui compte.", "est")
        self.assertEqual((x["sujet"], x["contexte"]), ("", "Sur un marché saturé"))
        self.assertTrue(x["sujet_implicite"])

    def test_anglais_vers_predicat_francais(self):
        x = un("The annual review costs €1,500.", "coûte")
        self.assertEqual((x["sujet"], t.formater(x["valeur"])), ("The annual review", "1 500 EUR"))
        self.assertEqual(un("Atlas Conseil is based in Lyon.", "est situé à")["objet"], "Lyon")

    def test_verbe_en_tete_de_sujet_ignore(self):
        # « compte » est ici un nom : le vrai verbe est « coûte ».
        self.assertEqual(un("Le compte pro coûte 9 € par mois.", "coûte")["sujet"], "Le compte pro")

    def test_predicat_canonique(self):
        self.assertEqual(t.predicat_canonique("sont situés à"), "est situé à")
        self.assertEqual(t.predicat_canonique("is based in"), "est situé à")
        self.assertEqual(t.predicat_canonique("rédige"), "redige")


class TestLecture(unittest.TestCase):
    def test_contenu_principal_seulement(self):
        p = t.lire_html(page_html(CORPS, GRAPHE))
        self.assertNotIn("990", p["texte"])  # menu et pied de page exclus
        self.assertEqual(p["h1"], "Bilan annuel pour les TPE à Lyon")
        self.assertTrue(p["phrases"][0]["phrase"].startswith("Atlas Conseil est"))

    def test_markdown_et_json(self):
        p = t.lire_markdown("---\ntitle: x\n---\n# Titre\n\nLe bilan annuel coûte 1 500 € HT.\n\n- Atlas Conseil est situé à Lyon.")
        self.assertEqual([x["phrase"] for x in p["phrases"]],
                         ["Le bilan annuel coûte 1 500 € HT.", "Atlas Conseil est situé à Lyon."])
        j = t.lire_json(json.dumps({"slug": "bilan", "faq": [{"question": "Combien coûte le bilan ?",
                                                             "answer": "Le bilan annuel coûte 1 200 € HT."}]}))
        self.assertEqual([x["phrase"] for x in j["phrases"]], ["Le bilan annuel coûte 1 200 € HT."])

    def test_entites_jsonld_references_resolues(self):
        ents = t.entites_jsonld(t.lire_html(page_html(CORPS, GRAPHE))["jsonld"])
        par_role = {(e["role"], e["nom"]): e for e in ents}
        self.assertEqual(par_role[("mentions", "Lyon")]["qid"], "Q999")
        self.assertEqual(par_role[("knowsAbout", "Expertise comptable")]["qid"], "Q111111")
        self.assertIn(("provider", "Atlas Conseil"), par_role)  # {"@id"} résolu dans le graphe
        self.assertIn(("about", "Bilan comptable"), par_role)
        self.assertEqual(sum(1 for e in ents if e["nom"] == "Lyon"), 1)  # pas de doublon « noeud »

    def test_extraction_signale_sujet_implicite_en_tete(self):
        r = t.extraire(t.lire_html(page_html(CORPS, GRAPHE)))
        self.assertIn("Il comprend la liasse fiscale.", r["sujets_implicites_en_tete"])


class TestRegistre(DossierIsole):
    def setUp(self):
        super().setUp()
        self.ecrire("memoire/entites.csv", ENTITES_CSV)
        self.ecrire("memoire/triplets.csv", TRIPLETS_CSV)
        self.entites = t.charger_entites(self.dossier / "memoire/entites.csv")
        self.triplets = t.charger_triplets(self.dossier / "memoire/triplets.csv")

    def test_commentaires_ignores(self):
        self.assertEqual([e["entite"] for e in self.entites],
                         ["Atlas Conseil", "Expertise comptable", "Lyon", "Liasse fiscale"])
        self.assertEqual(len(self.triplets), 5)
        self.assertEqual(self.entites[1]["alias"], ["expert-comptable"])
        self.assertEqual(self.entites[0]["sameAs"], [f"{SITE}/#organization", f"{SITE}/"])

    def test_ancien_registre_json(self):
        self.ecrire("memoire/entites.json", json.dumps({"lyon": {
            "name": "Lyon", "type": "City", "wikidata": "https://www.wikidata.org/wiki/Q222222",
            "wikipedia": "https://fr.wikipedia.org/wiki/Lyon", "description_wikidata": "commune"}}))
        e = t.charger_entites(self.dossier / "memoire/entites.json")[0]
        self.assertEqual((e["entite"], e["qid"], e["sameAs"]), ("Lyon", "Q222222", ["https://fr.wikipedia.org/wiki/Lyon"]))

    def test_pages_concernees(self):
        pour = [x["objet"] for x in self.triplets if t.concerne(x, f"{SITE}/offres/bilan-annuel/")]
        self.assertEqual(pour, ["Lyon", "1 200 € HT", "3 semaines", "la déclaration de résultat"])
        self.assertEqual(t.id_page("contenus/bilan-annuel.html"), "bilan-annuel")
        self.assertEqual(t.id_page(f"{SITE}/"), "")

    def verifier(self, corps=CORPS, graphe=GRAPHE):
        return t.verifier(t.lire_html(page_html(corps, graphe)), self.entites, self.triplets,
                          f"{SITE}/offres/bilan-annuel/")

    def test_triplets_requis_affirmes(self):
        r = self.verifier()
        self.assertEqual({s["objet"]: s["statut"] for s in r["triplets"]},
                         {"Lyon": "affirmé", "1 200 € HT": "affirmé", "3 semaines": "affirmé",
                          "la déclaration de résultat": "affirmé"})
        self.assertEqual(r["couverture_triplets"], 100)
        self.assertEqual(r["en_tete"], 4)

    def test_contredit_implicite_absent(self):
        corps = ("<h1>Bilan annuel</h1><p>Atlas Conseil est situé à Villeurbanne. Le bilan annuel coûte 1 500 € HT. "
                 "Notre mission de bilan annuel est rapide. Elle dure 3 semaines.</p>")
        r = self.verifier(corps)
        statuts = {s["objet"]: s for s in r["triplets"]}
        self.assertEqual(statuts["1 200 € HT"]["statut"], "contredit")
        self.assertEqual(statuts["1 200 € HT"]["trouve"], "1 500 EUR HT")
        self.assertEqual(statuts["3 semaines"]["statut"], "implicite")
        self.assertEqual(statuts["la déclaration de résultat"]["statut"], "absent")
        self.assertEqual((statuts["Lyon"]["statut"], statuts["Lyon"]["trouve"]), ("contredit", "Villeurbanne"))
        self.assertEqual(r["couverture_triplets"], 0)
        self.assertEqual(r["contredits"], 2)

    def test_entites_sans_sameas_qid_faux_et_invisibles(self):
        r = self.verifier()
        msg = {(c["gravite"], c["entite"]): c["message"] for c in r["constats"]}
        self.assertIn("Q999 ≠ registre Q222222", msg[("erreur", "Lyon")])
        self.assertIn("sans sameAs Wikidata", msg[("attention", "Expertise comptable")])
        self.assertIn("absente du JSON-LD", msg[("attention", "Liasse fiscale")])
        self.assertIn("invisible", msg[("attention", "Comptabilité analytique")])
        self.assertNotIn(("attention", "Atlas Conseil"), msg)  # le nœud Organization du socle compte

    def test_saillance(self):
        r = self.verifier()
        self.assertEqual(r["saillance"][0]["entite"], "Lyon")  # H1 + title + introduction
        self.assertTrue(any("peu saillant" in c["message"] for c in r["constats"] if c["entite"] == "Bilan comptable"))

    def test_cli_verifier_strict(self):
        self.ecrire("bilan-annuel.html", page_html(CORPS, GRAPHE))
        r = lancer("triplets.py", "verifier", "bilan-annuel.html", "--json", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["couverture_triplets"], 100)
        # QID faux sur Lyon : --strict bloque.
        r = lancer("triplets.py", "verifier", "bilan-annuel.html", "--strict", cwd=self.dossier)
        self.assertEqual(r.returncode, 1, r.stdout)
        graphe = json.loads(json.dumps(GRAPHE))
        graphe["@graph"][1]["mentions"][0]["sameAs"] = ["https://www.wikidata.org/wiki/Q222222"]
        self.ecrire("bilan-annuel.html", page_html(CORPS, graphe))
        r = lancer("triplets.py", "verifier", "bilan-annuel.html", "--strict", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_coherence_contradictions(self):
        self.ecrire("contenus/bilan-annuel.html", page_html(CORPS, GRAPHE))
        self.ecrire("contenus/tarifs.md", "# Tarifs\n\nLe bilan annuel coûte 1 500 € HT pour une TPE. "
                                          "Auparavant, le bilan annuel coûtait 1 000 € HT.\n\n"
                                          "Atlas Conseil est situé à Villeurbanne.\n")
        self.ecrire("contenus/faq.json", json.dumps({"faq": [{"answer": "Le bilan annuel coûte 1 200 € HT."}]}))
        pages = t.pages_de([str(self.dossier / "contenus")])
        r = t.coherence(pages, self.entites, self.triplets)
        lignes = {(l["nature"], l["sujet"], l["predicat"]): l for l in r["lignes"]}
        prix = lignes[("contradiction chiffrée", "Le bilan annuel", "coûte")]["valeurs"]
        self.assertEqual(set(prix), {"1 200 EUR HT", "1 500 EUR HT"})  # 1 000 € : historique, ignoré
        self.assertIn(("écart au registre", "Atlas Conseil", "est situé à"), lignes)
        self.assertIn(("écart au registre", "Le bilan annuel", "coûte"), lignes)
        r = lancer("triplets.py", "coherence", "contenus", "--strict", cwd=self.dossier)
        self.assertEqual(r.returncode, 1)
        self.assertIn("contradiction chiffrée", r.stdout)

    def test_autre_montant_d_un_autre_predicat_n_est_pas_un_ecart(self):
        self.ecrire("contenus/a.md", "Le bilan annuel coûte 1 200 € HT. Le bilan annuel exige un acompte de 400 € HT.")
        r = t.coherence(t.pages_de([str(self.dossier / "contenus")]), self.entites, self.triplets)
        self.assertEqual(r["lignes"], [])
        page = t.lire_markdown("Le bilan annuel exige un acompte de 400 € HT.")
        req = next(x for x in self.triplets if x["predicat"] == "coûte")
        self.assertEqual(t.statut_triplet(req, page, self.entites)["statut"], "absent")

    def test_coherence_sans_contradiction(self):
        self.ecrire("contenus/a.md", "Le bilan annuel coûte 1 200 € HT.")
        self.ecrire("contenus/b.md", "Chez nous, le bilan annuel coûte 1 200 € HT.")
        r = lancer("triplets.py", "coherence", "contenus", "--strict", "--json", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(json.loads(r.stdout)["lignes"], [])

    def test_fragment_jsonld(self):
        frag, avis = t.fragment_jsonld(self.entites, ["Expertise comptable"],
                                       ["Lyon", "Atlas Conseil", "Expertise comptable", "Liasse fiscale", "Inconnue"],
                                       f"{SITE}/offres/bilan-annuel/", f"{SITE}/glossaire/#termes")
        self.assertEqual(frag["@id"], f"{SITE}/offres/bilan-annuel/#webpage")
        self.assertEqual(frag["about"]["sameAs"][0], "https://www.wikidata.org/wiki/Q111111")
        noms = [m.get("name") or m.get("@id") for m in frag["mentions"]]
        self.assertEqual(noms, ["Lyon", f"{SITE}/#organization", "Liasse fiscale", "Inconnue"])  # about retiré
        self.assertEqual(frag["mentions"][1], {"@id": f"{SITE}/#organization"})  # référence, pas une 2e Organization
        terme = frag["mentions"][2]
        self.assertEqual((terme["@type"], terme["inDefinedTermSet"]["@id"]), ("DefinedTerm", f"{SITE}/glossaire/#termes"))
        self.assertNotIn("sameAs", frag["mentions"][3])
        self.assertTrue(any("Inconnue" in a for a in avis))

    def test_types_risques_ramenes_a_thing(self):
        n = t.noeud_entite({"entite": "Logiciel de paie X", "type": "SoftwareApplication", "qid": "Q5", "sameAs": []})
        self.assertEqual(n, {"@type": "Thing", "name": "Logiciel de paie X",
                             "sameAs": ["https://www.wikidata.org/wiki/Q5"]})

    def test_fragment_valide_par_schema_validate(self):
        frag, _ = t.fragment_jsonld(self.entites, ["Expertise comptable"], ["Lyon", "Atlas Conseil"],
                                    f"{SITE}/page/")
        graphe = {"@context": "https://schema.org", "@graph": [
            {"@type": "Organization", "@id": f"{SITE}/#organization", "name": "Atlas Conseil", "url": f"{SITE}/",
             "logo": f"{SITE}/logo.png"},
            {"@type": "WebSite", "@id": f"{SITE}/#website", "name": "Atlas", "url": f"{SITE}/",
             "publisher": {"@id": f"{SITE}/#organization"}},
            {"@type": "WebPage", "url": f"{SITE}/page/", "name": "Page", "isPartOf": {"@id": f"{SITE}/#website"},
             **frag}]}
        self.ecrire("page.jsonld", json.dumps(graphe, ensure_ascii=False))
        r = lancer("schema_validate.py", "page.jsonld", "--json", cwd=self.dossier)
        erreurs = [c["message"] for c in json.loads(r.stdout)["constats"] if c["gravite"] == "erreur"]
        self.assertEqual(erreurs, [])

    def test_cli_jsonld_depuis_page(self):
        self.ecrire("page.html", page_html(CORPS, GRAPHE))
        r = lancer("triplets.py", "jsonld", "--about", "Expertise comptable", "--depuis", "page.html", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        frag = json.loads(r.stdout)
        self.assertEqual(frag["about"]["name"], "Expertise comptable")
        self.assertEqual(frag["mentions"][0]["name"], "Lyon")  # le plus saillant d'abord
        r = lancer("triplets.py", "jsonld", "--organisation", cwd=self.dossier)
        self.assertEqual([k["name"] for k in json.loads(r.stdout)["knowsAbout"]], ["Expertise comptable", "Liasse fiscale"])

    def test_cli_extraire_texte(self):
        r = lancer("triplets.py", "extraire", "--texte", "Atlas Conseil est situé à Lyon. Il compte 14 collaborateurs.",
                   "--json", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertEqual(d["triplets"][0]["predicat"], "est situé à")
        self.assertEqual(d["sujets_implicites_en_tete"], ["Il compte 14 collaborateurs."])


class TestWikidata(unittest.TestCase):
    RECHERCHE = {"search": [
        {"id": "Q10", "label": "Atlas Conseil", "description": "maison d'édition"},
        {"id": "Q20", "label": "Atlas Conseil", "description": "cabinet d'expertise comptable à Lyon"}]}
    DETAILS = {"entities": {
        "Q10": {"claims": {"P856": [{"mainsnak": {"datavalue": {"value": "https://atlas-editions.example/"}}}]}},
        "Q20": {"claims": {"P856": [{"mainsnak": {"datavalue": {"value": f"{SITE}/"}}}]},
                "sitelinks": {"frwiki": {"title": "Atlas Conseil (cabinet)"}}}}}

    def test_candidats_et_site_officiel(self):
        c = t.enrichir_candidats(t.candidats_wikidata(self.RECHERCHE), self.DETAILS, "atlas-conseil.example")
        self.assertEqual([x["qid"] for x in c if x["correspond_au_site"]], ["Q20"])  # l'homonyme est écarté
        self.assertEqual(c[1]["wikipedia"], "https://fr.wikipedia.org/wiki/Atlas_Conseil_%28cabinet%29")
        self.assertEqual(c[0]["url"], "https://www.wikidata.org/wiki/Q10")

    def test_panne_reseau_sans_exception(self):
        with mock.patch.object(t, "_get_json", side_effect=urllib.error.URLError("hors ligne")):
            r = t.chercher_wikidata("Atlas Conseil")
        self.assertEqual(r["candidats"], [])
        self.assertIn("injoignable", r["erreur"])

    def test_details_en_panne_garde_les_candidats(self):
        reponses = [self.RECHERCHE, urllib.error.URLError("coupure")]

        def faux(params, delai=10.0):
            r = reponses.pop(0)
            if isinstance(r, Exception):
                raise r
            return r

        with mock.patch.object(t, "_get_json", side_effect=faux):
            r = t.chercher_wikidata("Atlas Conseil", domaine="atlas-conseil.example")
        self.assertIsNone(r["erreur"])
        self.assertEqual([c["qid"] for c in r["candidats"]], ["Q10", "Q20"])


class TestGabarit(unittest.TestCase):
    def test_registre_du_modele_lisible_et_vide(self):
        self.assertEqual(t.charger_entites(RACINE / "modele-projet/memoire/entites.csv"), [])
        self.assertEqual(t.charger_triplets(RACINE / "modele-projet/memoire/triplets.csv"), [])
        entete = (RACINE / "modele-projet/memoire/entites.csv").read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(entete.split(",")[:5], ["entite", "type", "qid", "sameAs", "definition"])
        entete = (RACINE / "modele-projet/memoire/triplets.csv").read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(entete.split(","), ["sujet", "predicat", "objet", "source", "date_verif", "pages"])


if __name__ == "__main__":
    unittest.main()
