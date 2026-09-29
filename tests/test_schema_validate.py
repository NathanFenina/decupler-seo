"""Le contrôle JSON-LD bloque une livraison : il ne doit rater ni surbloquer."""

import copy
import json
import unittest

from _outils import DossierIsole, lancer

SITE = "https://exemple.com"
PAGE = f"{SITE}/plomberie/"

SOCLE = [
    {"@type": "Organization", "@id": f"{SITE}/#organization", "name": "Exemple SARL", "url": f"{SITE}/",
     "logo": {"@type": "ImageObject", "@id": f"{SITE}/#logo", "url": f"{SITE}/logo-sombre.png"},
     "sameAs": ["https://www.wikidata.org/wiki/Q42"]},
    {"@type": "WebSite", "@id": f"{SITE}/#website", "name": "Exemple", "url": f"{SITE}/",
     "publisher": {"@id": f"{SITE}/#organization"}},
]

NOEUDS_PAGE = [
    {"@type": "WebPage", "@id": f"{PAGE}#webpage", "url": PAGE, "name": "Plombier",
     "isPartOf": {"@id": f"{SITE}/#website"}, "about": {"@id": f"{SITE}/#organization"},
     "mainEntity": {"@id": f"{PAGE}#service"}, "breadcrumb": {"@id": f"{PAGE}#breadcrumb"},
     "dateModified": "2026-03-02"},
    {"@type": "Service", "@id": f"{PAGE}#service", "name": "Dépannage plomberie", "serviceType": "Plomberie",
     "provider": {"@id": f"{SITE}/#organization"},
     "mentions": [{"@type": "Thing", "name": "Plomberie",
                   "sameAs": ["https://fr.wikipedia.org/wiki/Plomberie", "https://www.wikidata.org/wiki/Q1"]}]},
    {"@type": "BreadcrumbList", "@id": f"{PAGE}#breadcrumb", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Accueil", "item": f"{SITE}/"},
        {"@type": "ListItem", "position": 2, "name": "Plomberie", "item": PAGE}]},
]


def graphe(noeuds):
    return {"@context": "https://schema.org", "@graph": noeuds}


def page_html(*blocs):
    scripts = "".join(f'<script type="application/ld+json">{json.dumps(b, ensure_ascii=False)}</script>'
                      for b in blocs)
    return f"<!doctype html><html><head><title>T</title>{scripts}</head><body><h1>T</h1></body></html>"


class TestSchemaValidate(DossierIsole):
    def controler(self, contenu, *args, nom="page.html"):
        self.ecrire(nom, contenu if isinstance(contenu, str) else json.dumps(contenu, ensure_ascii=False))
        r = lancer("schema_validate.py", nom, "--json", "--strict", *args, cwd=self.dossier)
        return r.returncode, json.loads(r.stdout)

    def erreurs(self, d):
        return [c["message"] for c in d["constats"] if c["gravite"] == "erreur"]

    def avertissements(self, d):
        return [c["message"] for c in d["constats"] if c["gravite"] == "attention"]

    def noeuds(self):
        return copy.deepcopy(SOCLE + NOEUDS_PAGE)

    def test_graphe_propre_passe(self):
        code, d = self.controler(page_html(graphe(self.noeuds())))
        self.assertEqual(code, 0, d)
        self.assertEqual(self.erreurs(d), [])
        self.assertEqual(d["scripts"], 1)
        self.assertIn({"type": "Service", "id": f"{PAGE}#service"}, d["noeuds"])

    def test_fichier_jsonld_toujours_accepte(self):
        code, d = self.controler(graphe(self.noeuds()), nom="page.jsonld")
        self.assertEqual(code, 0, d)

    def test_plusieurs_scripts_signales(self):
        n = self.noeuds()
        code, d = self.controler(page_html(graphe(n[:2]), graphe(n[2:])))
        self.assertEqual(d["scripts"], 2)
        self.assertTrue(any("scripts JSON-LD" in m for m in self.avertissements(d)))

    def test_reference_orpheline(self):
        n = self.noeuds()
        n[2]["author"] = {"@id": f"{SITE}/#/schema/person/inconnu"}
        code, d = self.controler(page_html(graphe(n)))
        self.assertEqual(code, 1)
        self.assertTrue(any("introuvable" in m for m in self.erreurs(d)))

    def test_id_defini_deux_fois_differemment(self):
        n = self.noeuds()
        n.append({"@type": "Service", "@id": f"{PAGE}#service", "name": "Autre", "provider": {"@id": f"{SITE}/#organization"}})
        code, d = self.controler(page_html(graphe(n)))
        self.assertEqual(code, 1)
        self.assertTrue(any("défini plusieurs fois" in m for m in self.erreurs(d)))

    def test_texte_provisoire_bloque(self):
        n = self.noeuds()
        n[0]["vatID"] = "A_CONFIRMER"
        code, d = self.controler(page_html(graphe(n)))
        self.assertEqual(code, 1)
        self.assertTrue(any("non confirmée" in m for m in self.erreurs(d)))

    def test_url_relative_et_date_non_iso(self):
        n = self.noeuds()
        n[2]["url"] = "/plomberie/"
        n[2]["dateModified"] = "02/03/2026"
        code, d = self.controler(page_html(graphe(n)))
        self.assertEqual(code, 1)
        self.assertTrue(any("URL relative" in m for m in self.erreurs(d)))
        self.assertTrue(any("ISO 8601" in m for m in self.erreurs(d)))

    def test_sameas_mal_forme(self):
        n = self.noeuds()
        n[3]["mentions"][0]["sameAs"] = ["https://www.wikidata.org/entity/Q1", "https://fr.wikipedia.org/Plomberie"]
        _, d = self.controler(page_html(graphe(n)))
        msgs = self.avertissements(d)
        self.assertTrue(any("format Wikidata" in m for m in msgs))
        self.assertTrue(any("format Wikipédia" in m for m in msgs))

    def test_logiciel_cite_en_softwareapplication(self):
        n = self.noeuds()
        n[3]["mentions"].append({"@type": "SoftwareApplication", "name": "Un tableur"})
        _, d = self.controler(page_html(graphe(n)))
        self.assertTrue(any("SoftwareApplication" in m and "Thing" in m for m in self.avertissements(d)))

    def test_logiciel_sujet_de_la_page_accepte(self):
        n = self.noeuds()
        n[2]["mainEntity"] = {"@id": f"{PAGE}#app"}
        n.append({"@type": "SoftwareApplication", "@id": f"{PAGE}#app", "name": "App", "applicationCategory":
                  "BusinessApplication", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR",
                                                    "availability": "https://schema.org/InStock"}})
        n[2]["about"] = {"@id": f"{SITE}/#organization"}
        _, d = self.controler(page_html(graphe(n)))
        self.assertFalse(any("Thing avec sameAs" in m for m in self.avertissements(d)))

    def test_socle_identique_puis_divergent(self):
        self.ecrire("socle-global.json", json.dumps(graphe(SOCLE)))
        code, d = self.controler(page_html(graphe(self.noeuds())), "--socle", "socle-global.json")
        self.assertEqual(code, 0, d)
        n = self.noeuds()
        n[0]["name"] = "Exemple SAS"
        code, d = self.controler(page_html(graphe(n)), "--socle", "socle-global.json")
        self.assertEqual(code, 1)
        self.assertTrue(any("diverge du socle" in m and "name" in m for m in self.erreurs(d)))

    def test_pieges_signales(self):
        n = self.noeuds()
        n[1]["potentialAction"] = {"@type": "SearchAction", "target": f"{SITE}/?s={{search_term_string}}"}
        n[0]["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": 5, "reviewCount": 3}
        _, d = self.controler(page_html(graphe(n)))
        msgs = self.avertissements(d)
        self.assertTrue(any("novembre 2024" in m for m in msgs))
        self.assertTrue(any("auto-attribués" in m for m in msgs))

    def test_doublon_organization_en_ligne(self):
        n = self.noeuds()
        n.append({"@type": "BlogPosting", "@id": f"{PAGE}#article", "headline": "T", "image": f"{SITE}/a.webp",
                  "datePublished": "2026-01-01", "dateModified": "2026-02-01", "mainEntityOfPage": {"@id": f"{PAGE}#webpage"},
                  "author": {"@id": f"{SITE}/#organization"},
                  "publisher": {"@type": "Organization", "name": "Exemple SARL", "url": f"{SITE}/"}})
        code, d = self.controler(page_html(graphe(n)))
        self.assertEqual(code, 1)
        self.assertTrue(any("entités « Organization »" in m for m in self.erreurs(d)))

    def test_json_invalide(self):
        code, d = self.controler('<html><head><script type="application/ld+json">{"@type": "WebPage",}</script></head></html>')
        self.assertEqual(code, 1)
        self.assertTrue(d["erreurs_parsing"])


if __name__ == "__main__":
    unittest.main()
