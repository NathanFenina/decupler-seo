"""Empreinte de style : les règles écrites dans memoire/style.md viennent de ces mesures."""

import json
import sys
import unittest

from _outils import SCRIPTS, DossierIsole, lancer

sys.path.insert(0, str(SCRIPTS))
import _contenu as C  # noqa: E402
import style_maison as M  # noqa: E402


def article(sujet, question=True, appel=True):
    """Une page « maison » : vouvoiement, « nous », phrases courtes, une formule qui revient."""
    ouverture = f"Vous cherchez {sujet} ?" if question else f"Le sujet {sujet} revient souvent."
    corps = (f"<p>{ouverture} Nous vous expliquons tout. Chez nous, chaque dossier est suivi de près. "
             f"Votre projet mérite une méthode claire.</p>"
             f"<h2>Comment choisir {sujet} ?</h2>"
             f"<p>Commencez par vos besoins. Notre équipe compare les options avec vous. "
             f"Le bon choix dépend du budget, du délai et de la surface. Vous gagnez du temps.</p>"
             f"<ul><li>Budget</li><li>Délai</li></ul>"
             f"<h2>Les erreurs à éviter</h2>"
             f"<p>Ne signez pas trop vite. Nous voyons souvent des devis incomplets. Vérifiez les garanties. "
             f"Posez vos questions avant de vous engager, pas après.</p>"
             f"<p>{'Demandez votre devis gratuit en deux minutes, notre équipe vous répond sous 48 heures.' if appel else 'Bonne lecture à vous et à bientôt sur ce blog.'}"
             f" Une question ? Notre équipe vous répond.</p>")
    return C.lire_html(f"<main>{corps}</main>", "")


class TestEmpreinte(unittest.TestCase):
    def setUp(self):
        self.pages = [article("un expert-comptable"), article("un logiciel de paie", appel=False),
                      article("une mutuelle d'entreprise", question=False)]
        self.e = M.empreinte(self.pages)

    def test_adresse_personne(self):
        self.assertEqual(self.e["adresse"]["adresse"], "vouvoiement")
        self.assertEqual(self.e["adresse"]["personne"], "nous")

    def test_rythme(self):
        ph = self.e["phrase"]
        self.assertLess(ph["moyenne"], 10)
        self.assertGreater(ph["courtes_pct"], 40)
        self.assertEqual(ph["longues_pct"], 0)
        self.assertGreater(ph["questions_pct"], 0)
        self.assertIsNotNone(self.e["paragraphe"]["mediane"])

    def test_structure_ouvertures_clotures(self):
        self.assertEqual(self.e["h2_questions_pct"], 50.0)
        self.assertEqual(self.e["ouvertures"], {"question": 2, "situation / affirmation": 1})
        self.assertEqual(self.e["clotures_avec_appel"], 2)
        self.assertEqual(self.e["pages_avec_tableau"], 0)
        self.assertGreater(self.e["listes_pour_1000"], 0)

    def test_expressions_et_vocabulaire(self):
        expr = [x["expression"] for x in self.e["expressions"]]
        self.assertIn("équipe vous répond", expr)          # « notre » est un mot vide : l'expression commence après
        self.assertIn("équipe", [x["mot"] for x in self.e["vocabulaire"]])

    def test_fragile_sous_1500_mots(self):
        self.assertTrue(self.e["fragile"])

    def test_regles_et_contradiction_avec_la_config(self):
        r = M.regles(self.e, "false")
        self.assertTrue(r[0].startswith("Vouvoyer le lecteur"))
        self.assertTrue(any("La config dit tutoiement" in x for x in r))
        self.assertFalse(any("config" in x for x in M.regles(self.e, "true")))

    def test_ouverture_types(self):
        def p(texte):
            return {"paragraphes": [texte]}
        self.assertEqual(C.ouverture(p("Combien coûte un bilan ? Tout dépend.")), "question")
        self.assertEqual(C.ouverture(p("En 2025, 40 % des PME ont changé d'outil.")), "chiffre")
        self.assertEqual(C.ouverture(p("Vous lancez votre activité et tout va vite.")), "adresse directe")
        self.assertEqual(C.ouverture(p("La paie est un processus mensuel encadré.")), "définition")


class TestFichier(DossierIsole):
    def test_lecture_humaine_conservee_a_la_relance(self):
        pages = [article("un expert-comptable"), article("un logiciel de paie")]
        e = M.empreinte(pages)
        cible = self.dossier / "memoire" / "style.md"
        cible.parent.mkdir(parents=True)
        cible.write_text(M.fichier_style(e, ["a"], [], "2026-09-01", M.LECTURE_VIDE), encoding="utf-8")
        texte = cible.read_text(encoding="utf-8").replace("- Registre (expert, pédagogique, corporate, "
                                                          "conversationnel…) :", "- Registre : expert, sobre")
        cible.write_text(texte, encoding="utf-8")
        lecture = M.lecture_existante(cible)
        self.assertIn("Registre : expert, sobre", lecture)
        self.assertNotIn("## Pages mesurées", lecture)
        nouveau = M.fichier_style(e, ["a", "b"], [], "2026-09-29", lecture)
        self.assertIn("Registre : expert, sobre", nouveau)
        self.assertIn("Mesuré le 2026-09-29", nouveau)
        self.assertEqual(nouveau.count("## Lecture"), 1)

    def test_commande_sur_fichiers(self):
        textes = []
        for i, sujet in enumerate(("un expert-comptable", "un logiciel de paie", "une mutuelle")):
            textes.append(self.ecrire(f"contenus/p{i}.md", "---\ntitre: x\n---\n" + article(sujet)["markdown"]
                                      + "\n\n" + "Nous vous accompagnons à chaque étape du projet. " * 20))
        r = lancer("style_maison.py", *map(str, textes), cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        style = (self.dossier / "memoire" / "style.md").read_text(encoding="utf-8")
        self.assertIn("## Règles déduites", style)
        self.assertIn("Vouvoyer le lecteur", style)
        self.assertIn("## Lecture", style)
        r = lancer("style_maison.py", str(textes[0]), "--json", cwd=self.dossier)
        self.assertEqual(json.loads(r.stdout)["empreinte"]["pages"], 1)

    def test_sans_source(self):
        r = lancer("style_maison.py", cwd=self.dossier)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
