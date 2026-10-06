"""Passe d'humanisation : le score repère les tics d'écriture générée, pas un texte sobre."""

import json
import sys
import unittest

from _outils import SCRIPTS, DossierIsole, lancer

sys.path.insert(0, str(SCRIPTS))
import humanisation as H  # noqa: E402

TEXTE_IA = """# Comment Optimiser Votre Stratégie SEO En 2026

Dans un monde où le digital est en constante évolution, il est crucial de comprendre les leviers essentiels du référencement. Plongeons ensemble dans cet univers fascinant.

## Pourquoi Le SEO Est Incontournable

Le SEO n'est pas une simple option, c'est un véritable levier de croissance. Il est important de noter que 90 % des entreprises investissent dans le référencement. Selon les experts, il s'agit de la meilleure stratégie pour booster votre visibilité. Vous voulez plus de clients ? Vous cherchez à vous démarquer ? Le SEO est fait pour vous !

- **Visibilité** : apparaître en tête des résultats.
- **Crédibilité** : renforcer la confiance des clients.
- **Rentabilité** : optimiser votre retour sur investissement.

## Les Leviers Essentiels — Ce Qu'il Faut Savoir

Une stratégie efficace repose sur trois piliers : la technique, le contenu et la popularité. Il peut être intéressant de travailler la vitesse, la structure et le maillage. Cela pourrait permettre d'optimiser votre trafic de manière durable, rapide et efficace. 🚀

En outre, des études montrent que le contenu joue un rôle clé dans le classement — et c'est là toute la différence. N'hésitez pas à exploiter tout le potentiel de vos pages.

## Conclusion

En conclusion, le SEO est un atout majeur pour toute entreprise qui souhaite optimiser sa présence en ligne de façon durable et pérenne.
"""

TEXTE_HUMAIN = """# Changer de chaudière sans se tromper de devis

Mardi dernier, un client de Rezé nous a montré trois devis pour la même maison. Écart : 4 200 euros. Le moins cher oubliait le désembouage du circuit.

C'est le piège classique. On compare un prix total, alors qu'il faut comparer une liste de travaux. Sans cette liste, deux devis ne parlent pas de la même chose et le moins cher n'en est souvent pas un.

## Ce que doit contenir un devis

Demandez le modèle exact de la chaudière, sa puissance et la référence du thermostat. Si l'artisan écrit « chaudière gaz condensation » sans marque, relancez-le. Vous ne pourrez rien vérifier.

Le désembouage se chiffre à part. Sur un circuit de plus de quinze ans, nous le faisons presque toujours, parce qu'une boue noire dans les radiateurs use la nouvelle chaudière en quelques hivers.

## Quand ne pas changer

Si votre chaudière a moins de dix ans et tombe en panne une fois, réparez-la. Le remplacement ne se justifie qu'à partir de pannes répétées ou d'un rendement mesuré très bas. Nous préférons perdre une vente que vendre une machine inutile.

Une question sur votre devis ? Envoyez-le nous, nous le relisons gratuitement.
"""

HTML_IA = """<!doctype html><html><head><title>Guide</title><style>p { color: red }</style></head><body><main>
<h1>Comment Optimiser Votre Stratégie SEO</h1>
<p>Dans un monde où le digital est en constante évolution, il est crucial de comprendre les leviers essentiels du référencement. Plongeons ensemble dans cet univers fascinant.</p>
<ul><li><strong>Visibilité</strong> : apparaître en tête.</li><li><strong>Crédibilité</strong> : renforcer la confiance.</li><li><strong>Rentabilité</strong> : optimiser le retour.</li></ul>
<p>Le SEO n'est pas une option, c'est un véritable levier &mdash; et un atout majeur. En conclusion, n'hésitez pas à booster votre visibilité.</p>
</main></body></html>
"""

APRES = """# Comment travailler son référencement en 2026

Le référencement demande trois chantiers, et aucun ne se règle en une semaine. [À COMPLÉTER : un cas client daté]

## Pourquoi s'en occuper

Une page bien placée attire des visiteurs sans payer chaque clic. 90 % des entreprises y investissent, d'après le baromètre cité par le client. Un site lent perd ce trafic, même avec de bons textes.

## Les trois chantiers

La technique passe en premier. Le contenu vient ensuite, page par page. La popularité se construit sur des mois, avec des liens que vous ne contrôlez pas.

Commencez par la vitesse : c'est le seul chantier dont vous verrez l'effet dès la semaine suivante.
"""


class TestScore(unittest.TestCase):
    def setUp(self):
        self.marqueurs = H.charger_marqueurs()

    def test_texte_bourre_de_tics_score_eleve(self):
        r = H.analyser(TEXTE_IA, "md", self.marqueurs)
        self.assertGreater(r["score"], 60)
        self.assertEqual(r["niveau"], "élevé")
        for famille in ("vocabulaire", "structures", "ponctuation", "mise_en_forme", "flou", "ton",
                        "ouverture_cloture"):
            self.assertGreater(r["familles"][famille]["points"], 0, famille)

    def test_familles_detaillees(self):
        r = H.analyser(TEXTE_IA, "md", self.marqueurs)
        s = r["familles"]["structures"]["detail"]
        self.assertEqual(s["ce_n_est_pas_c_est"], 1)
        self.assertEqual(s["questions_en_serie"], 1)
        self.assertEqual(s["titres_majuscules"], "3/3")
        self.assertGreaterEqual(s["triades"], 3)
        p = r["familles"]["ponctuation"]["detail"]
        self.assertEqual((p["tirets_cadratins"], p["emojis"]), (2, 1))
        self.assertEqual(r["familles"]["mise_en_forme"]["detail"]["puces_en_gras"], 3)
        self.assertEqual(r["familles"]["flou"]["detail"]["pourcentages_ronds_sans_source"], 1)
        self.assertEqual(r["familles"]["ton"]["detail"]["exclamations"], 1)

    def test_signaux_avec_ligne_et_extrait(self):
        r = H.analyser(TEXTE_IA, "md", self.marqueurs)
        crucial = [s for s in r["signaux"] if s["raison"] == "« crucial »"]
        self.assertEqual(crucial[0]["ligne"], 3)
        self.assertIn("il est crucial de comprendre", crucial[0]["extrait"])
        titres = [s for s in r["signaux"] if "Majuscule" in s["raison"]]
        self.assertEqual([s["ligne"] for s in titres], [1, 5, 13])
        conclusion = [s for s in r["signaux"] if s["famille"] == "ouverture_cloture"]
        self.assertEqual({s["raison"] for s in conclusion},
                         {"ouverture générique", "conclusion-résumé", "titre « Conclusion »"})

    def test_texte_humain_sobre_score_bas(self):
        r = H.analyser(TEXTE_HUMAIN, "md", self.marqueurs)
        self.assertLessEqual(r["score"], 10)
        self.assertEqual(r["niveau"], "faible")
        self.assertEqual(r["familles"]["vocabulaire"]["points"], 0)
        self.assertEqual(r["familles"]["structures"]["detail"]["titres_majuscules"], "0/3")

    def test_expression_citee_entre_guillemets_ignoree(self):
        r = H.analyser("Évitez d'écrire « il est crucial de » dans vos pages.", "txt", self.marqueurs)
        self.assertEqual(r["familles"]["vocabulaire"]["detail"]["occurrences"], 0)

    def test_html_balises_retirees_et_lignes_conservees(self):
        r = H.analyser(HTML_IA, "html", self.marqueurs)
        self.assertGreater(r["score"], 40)
        self.assertFalse(any("color" in s["extrait"] for s in r["signaux"]))
        self.assertEqual(r["familles"]["mise_en_forme"]["detail"]["puces_en_gras"], 3)
        self.assertEqual(r["familles"]["ponctuation"]["detail"]["tirets_cadratins"], 1)
        crucial = [s for s in r["signaux"] if s["raison"] == "« crucial »"]
        self.assertEqual(crucial[0]["ligne"], 3)

    def test_titre_a_l_anglaise(self):
        self.assertTrue(H.titre_a_l_anglaise("Comment Choisir Son Expert-Comptable"))
        self.assertFalse(H.titre_a_l_anglaise("Créer une société en Arabie Saoudite"))
        self.assertFalse(H.titre_a_l_anglaise("Le guide SEO de Google"))

    def test_rythme_uniforme_signale(self):
        paragraphe = " ".join(["Le chantier commence par un relevé complet des pièces."] * 3)
        uniforme = "\n\n".join([paragraphe] * 4)
        r = H.analyser(uniforme, "txt", self.marqueurs)
        self.assertEqual(r["familles"]["rythme"]["points"], 10)
        self.assertTrue(any(s["famille"] == "rythme" for s in r["signaux"]))

    def test_texte_vide(self):
        r = H.analyser("", "md", self.marqueurs)
        self.assertEqual((r["score"], r["mots"]), (0, 0))


class TestProjet(DossierIsole):
    def test_marqueurs_du_projet_ignores_et_ajoutes(self):
        self.ecrire("memoire/marqueurs-ia.json", json.dumps({
            "ignorer": ["levier"], "ajouter": {"vocabulaire": ["\\bbest-seller\\b"]},
            "familles_ignorees": ["ponctuation"]}))
        f = self.ecrire("t.md", "Un levier simple. Un best-seller — vraiment.\n")
        r = json.loads(lancer("humanisation.py", str(f), "--json", cwd=self.dossier).stdout)
        raisons = [s["raison"] for s in r["signaux"]]
        self.assertIn("« best-seller »", raisons)
        self.assertNotIn("« levier »", raisons)
        self.assertTrue(r["familles"]["ponctuation"]["ignoree"])
        self.assertEqual(r["familles"]["ponctuation"]["points"], 0)

    def test_rythme_compare_au_style_maison(self):
        self.ecrire("memoire/style.md", "| Phrase moyenne / médiane (mots) | 25.0 / 22 |\n")
        f = self.ecrire("t.md", TEXTE_HUMAIN)
        r = json.loads(lancer("humanisation.py", str(f), "--json", cwd=self.dossier).stdout)
        self.assertEqual(r["style_maison"]["phrase_moyenne_maison"], 25.0)
        self.assertLess(r["style_maison"]["ecart"], -3)
        sortie = lancer("humanisation.py", str(f), cwd=self.dossier).stdout
        self.assertIn("écart > 3 mots", sortie)


class TestLigneDeCommande(DossierIsole):
    def test_sortie_texte(self):
        f = self.ecrire("ia.md", TEXTE_IA)
        r = lancer("humanisation.py", str(f), cwd=self.dossier)
        self.assertEqual(r.returncode, 0)
        self.assertIn("/100 (élevé)", r.stdout)
        self.assertIn("Signaux à réécrire", r.stdout)
        self.assertIn("L3", r.stdout)

    def test_json(self):
        f = self.ecrire("page.html", HTML_IA)
        r = lancer("humanisation.py", str(f), "--json", cwd=self.dossier)
        d = json.loads(r.stdout)
        self.assertEqual(set(d["familles"]), set(H.POINTS))
        self.assertEqual(sum(f["max"] for f in d["familles"].values()), 100)
        self.assertTrue(all({"famille", "ligne", "extrait", "raison"} <= set(s) for s in d["signaux"]))

    def test_seuil_code_de_sortie(self):
        ia, humain = self.ecrire("ia.md", TEXTE_IA), self.ecrire("humain.md", TEXTE_HUMAIN)
        self.assertEqual(lancer("humanisation.py", str(ia), "--seuil", "25", cwd=self.dossier).returncode, 1)
        self.assertEqual(lancer("humanisation.py", str(humain), "--seuil", "25", cwd=self.dossier).returncode, 0)

    def test_entree_standard(self):
        import subprocess
        from _outils import environnement_propre
        r = subprocess.run([sys.executable, str(SCRIPTS / "humanisation.py"), "-", "--json"], input=HTML_IA,
                           cwd=self.dossier, env=environnement_propre(), capture_output=True, text=True)
        self.assertEqual(json.loads(r.stdout)["familles"]["mise_en_forme"]["detail"]["puces_en_gras"], 3)

    def test_fichier_introuvable(self):
        r = lancer("humanisation.py", "absent.md", cwd=self.dossier)
        self.assertEqual(r.returncode, 2)

    def test_avant_apres(self):
        avant, apres = self.ecrire("avant.md", TEXTE_IA), self.ecrire("apres.md", APRES)
        r = lancer("humanisation.py", "--avant", str(avant), "--apres", str(apres), "--json", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        c = json.loads(r.stdout)
        self.assertLess(c["delta"], -50)
        self.assertEqual(c["chiffres"]["apparus"], [])
        self.assertEqual(c["apres"]["a_completer"], 1)
        self.assertIn("Mêmes chiffres", lancer("humanisation.py", "--avant", str(avant), "--apres", str(apres),
                                                cwd=self.dossier).stdout)

    def test_avant_apres_chiffre_invente_bloque(self):
        avant = self.ecrire("avant.md", TEXTE_IA)
        apres = self.ecrire("apres.md", APRES + "\nLe trafic progresse de 37 % en six mois.\n")
        r = lancer("humanisation.py", "--avant", str(avant), "--apres", str(apres), cwd=self.dossier)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Chiffres apparus", r.stdout)
        self.assertIn("37", r.stdout)

    def test_avant_sans_apres_refuse(self):
        r = lancer("humanisation.py", "--avant", "a.md", cwd=self.dossier)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
