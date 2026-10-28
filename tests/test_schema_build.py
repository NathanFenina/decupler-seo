"""Le générateur produit un graphe que le validateur accepte, et refuse les configurations fautives."""

import sys
import unittest

from _outils import SCRIPTS

sys.path.insert(0, str(SCRIPTS))
import schema_build as B  # noqa: E402

S = "https://exemple.com"
SOCLE = [
    {"@type": "Organization", "@id": f"{S}/#organization", "name": "Exemple", "url": f"{S}/",
     "logo": {"@type": "ImageObject", "@id": f"{S}/#logo", "url": f"{S}/logo.png"}},
    {"@type": "WebSite", "@id": f"{S}/#website", "name": "Exemple", "url": f"{S}/",
     "publisher": {"@id": f"{S}/#organization"}},
]
REGISTRE = [{"entite": "Plomberie", "type": "Thing", "qid": "Q1", "sameAs": [], "definition": "", "alias": []}]


def page(**kw):
    p = {"url": f"{S}/plombier-lyon/", "type": "service", "titre": "Plombier à Lyon",
         "fil": [["Accueil", f"{S}/"], ["Plombier à Lyon", f"{S}/plombier-lyon/"]],
         "about": ["Plomberie"], "mentions": ["Chauffe-eau"],
         "service": {"nom": "Dépannage plomberie", "type": "Plomberie", "zone": "Lyon"},
         "faq": [["Combien coûte un dépannage ?", "Le devis est gratuit et remis avant toute intervention."]]}
    p.update(kw)
    return p


class TestConstruire(unittest.TestCase):
    def test_page_service_valide(self):
        doc, avis = B.construire(page(), SOCLE, REGISTRE)
        types = [n["@type"] for n in doc["@graph"]]
        self.assertEqual(types, ["Organization", "WebSite", "WebPage", "Service", "BreadcrumbList", "FAQPage"])
        self.assertEqual([c for c in B.valider(doc) if c["gravite"] == "erreur"], [])
        webpage = doc["@graph"][2]
        self.assertEqual(webpage["about"]["sameAs"], ["https://www.wikidata.org/wiki/Q1"])
        self.assertTrue(any("Chauffe-eau" in a for a in avis))       # hors registre : signalé

    def test_article_porte_about_sur_le_billet(self):
        p = page(type="article", service=None,
                 article={"publie": "2026-10-01", "image": f"{S}/img/plomberie.jpg",
                          "auteur": {"nom": "Jeanne Martin", "url": f"{S}/auteur/jeanne/"}})
        doc, _ = B.construire(p, SOCLE, REGISTRE)
        billet = next(n for n in doc["@graph"] if n["@type"] == "BlogPosting")
        webpage = next(n for n in doc["@graph"] if n["@type"] == "WebPage")
        self.assertIn("about", billet)
        self.assertNotIn("about", webpage)
        self.assertEqual([c for c in B.valider(doc) if c["gravite"] == "erreur"], [])

    def test_refus(self):
        cas = [page(about=["a", "b", "c", "d"]), page(mentions=["Plomberie"]),
               page(type="article", service=None, article={"publie": "2026-10-01"}),
               page(fil=[["Services", f"{S}/services/"]]), page(faq=[["Q ?", " "]]),
               page(url="http://exemple.com/x/")]
        for p in cas:
            with self.assertRaises(B.ErreurConfig):
                B.construire(p, SOCLE, REGISTRE)


if __name__ == "__main__":
    unittest.main()
