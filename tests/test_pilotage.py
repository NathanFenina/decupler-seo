"""Tableau de bord partagé : l'état de la page et les décisions du client ne se perdent jamais."""

import json
import sys
import unittest
from pathlib import Path

from _outils import SCRIPTS, DossierIsole, lancer

sys.path.insert(0, str(SCRIPTS))
import pilotage as P  # noqa: E402

GABARIT = (Path(SCRIPTS).parent / "templates" / "pilotage.html").read_text(encoding="utf-8")


class TestEtat(unittest.TestCase):
    def test_aller_retour_sans_toucher_au_reste(self):
        etat = {"maj": "2026-10-01", "projets": [{"id": "atlas", "nom": "Atlas </script> Conseil", "actions": []}]}
        html = P.ecrire_etat(GABARIT, etat)
        self.assertEqual(P.lire_etat(html), etat)
        self.assertNotIn("Atlas </script>", html)                      # le JSON ne ferme jamais la balise
        self.assertEqual(html.replace(html[html.index('id="etat">'):html.index("</script>", html.index('id="etat">'))], ""),
                         GABARIT.replace(GABARIT[GABARIT.index('id="etat">'):GABARIT.index("</script>", GABARIT.index('id="etat">'))], ""))

    def test_les_decisions_ne_sont_jamais_ecrasees(self):
        existantes = [{"id": "a", "titre": "Ancien", "statut": "validee", "note": "go"},
                      {"id": "b", "titre": "Refusée", "statut": "refusee"},
                      {"id": "c", "titre": "Proposée", "statut": "proposee", "gain": "+3 clics/mois"}]
        nouvelles = [{"id": "a", "titre": "Nouveau titre"}, {"id": "b", "titre": "Revient ?"},
                     {"id": "c", "titre": "Proposée", "gain": "+9 clics/mois"}, {"id": "d", "titre": "Neuve"}]
        actions, n = P.fusionner_actions(existantes, nouvelles, "2026-10-01")
        par = {a["id"]: a for a in actions}
        self.assertEqual(n, 1)
        self.assertEqual((par["a"]["titre"], par["a"]["statut"], par["a"]["note"]), ("Ancien", "validee", "go"))
        self.assertEqual(par["b"]["statut"], "refusee")
        self.assertEqual(par["c"]["gain"], "+9 clics/mois")               # une proposition se rafraîchit
        self.assertEqual(par["d"]["statut"], "proposee")

    def test_marquer(self):
        p = {"id": "atlas", "actions": [{"id": "a", "titre": "T", "statut": "validee"}]}
        P.marquer_action(p, "a", "faite", lien="https://exemple.test/pr/1", date="2026-10-02")
        self.assertEqual((p["actions"][0]["statut"], p["actions"][0]["lien"]), ("faite", "https://exemple.test/pr/1"))
        with self.assertRaises(SystemExit):
            P.marquer_action(p, "zz", "faite")
        with self.assertRaises(SystemExit):
            P.marquer_action(p, "a", "inconnu")


class TestIntegration(unittest.TestCase):
    HOTE = ('<!doctype html><html><head><meta charset=utf8><style>:root{color-scheme:light}</style></head><body>\n'
            '<title>Chantiers Atlas</title>\n<style>.bloc{color:red}</style><div class="wrap"><h1>Compte rendu</h1></div>\n'
            '</body></html>')

    def test_contenu_d_origine_conserve_et_titre_repris(self):
        etat = {"projets": [{"id": "atlas", "actions": [{"id": "a", "titre": "T", "statut": "proposee"}]}]}
        html = P.integrer(GABARIT, self.HOTE, etat)
        self.assertIn('<template id="hote"><style>.bloc{color:red}</style><div class="wrap"><h1>Compte rendu</h1></div></template>', html)
        self.assertIn("<title>Chantiers Atlas</title>", html)
        self.assertNotIn('<style id="css-page">body', html)                   # le fond reste celui de l'hôte
        self.assertEqual(P.lire_etat(html)["projets"][0]["actions"][0]["id"], "a")
        # réintégrer une page déjà intégrée ne l'emboîte pas
        deux = P.integrer(GABARIT, html, P.lire_etat(html))
        self.assertEqual(deux.count('<template id="hote"><style>.bloc'), 1)


class TestPropositions(unittest.TestCase):
    def test_opportunites_hors_pages_en_mesure(self):
        res = {"opportunites": [
            {"requete": "tva atlas", "page": "https://a.example/tva", "action": "ctr", "score": 40, "position": 3.1,
             "impressions_mois": 900, "gain_clics_mois": 22},
            {"requete": "sci", "page": "https://a.example/sci", "action": "page-1", "score": 30, "position": 7,
             "impressions_mois": 300, "gain_clics_mois": 9, "en_mesure_jusqu_au": "2026-10-20"},
            {"requete": "holding", "page": "", "action": "a-creer", "score": 12, "position": None, "volume_mois": 480,
             "gain_clics_mois": 14}]}
        a = P.depuis_opportunites(res, "atlas")
        self.assertEqual([x["type"] for x in a], ["optimisation", "contenu"])
        self.assertEqual(a[0]["page"], "/tva")
        self.assertIn("+22", a[0]["gain"])

    def test_points_ouverts_et_journal(self):
        pts = P.depuis_points_ouverts("# À traiter\n- [ ] Fusionner /a et /b\n- [x] Fait\n", "atlas")
        self.assertEqual([p["titre"] for p in pts], ["Fusionner /a et /b"])
        j = P.depuis_journal([{"id": "4", "url": "https://a.example/x", "type": "title", "verdict": "perte"},
                              {"id": "5", "url": "https://a.example/y", "type": "meta", "verdict": "gain"}], "atlas")
        self.assertEqual(len(j), 1)
        self.assertIn("n° 4", j[0]["titre"])

    def test_priorite_decisions_puis_gain(self):
        a = [{"id": "1", "type": "optimisation", "gain": "+5 clics/mois", "effort": "S"},
             {"id": "2", "type": "contenu", "gain": "+50 clics/mois", "effort": "L"},
             {"id": "3", "type": "decision", "gain": "", "effort": "M"},
             {"id": "4", "type": "optimisation", "gain": "+20 clics/mois", "effort": "M"},
             {"id": "4", "type": "optimisation", "gain": "+20 clics/mois", "effort": "M"}]
        self.assertEqual([x["id"] for x in P.prioriser(a, 3)], ["3", "2", "4"])
        beaucoup = [{"id": f"d{i}", "type": "decision", "gain": "", "effort": "M"} for i in range(6)] + a[:2]
        self.assertEqual([x["id"] for x in P.prioriser(beaucoup, 5)], ["d0", "d1", "d2", "2", "1"])

    def test_point_ouvert_sur_plusieurs_lignes_et_doublon(self):
        texte = "- [ ] Vérifier dans Search Console qu'aucune\n      action n'est en cours.\n- [ ] « tva » : /a et /b\n"
        pts = P.depuis_points_ouverts(texte, "atlas")
        self.assertEqual(pts[0]["titre"], "Vérifier dans Search Console qu'aucune action n'est en cours.")
        canni = P.depuis_cartographie({"cannibalisation": {"tva": ["/a", "/b"]}}, "atlas")
        self.assertEqual([x["titre"] for x in P.sans_doublons(canni + pts)],
                         ["Trancher la cannibalisation — tva", "Vérifier dans Search Console qu'aucune action n'est en cours."])

    def test_serie_hebdo(self):
        lignes = [{"keys": ["2026-09-21"], "clicks": 2, "impressions": 10},
                  {"keys": ["2026-09-22"], "clicks": 3, "impressions": 20},
                  {"keys": ["2026-09-28"], "clicks": 1, "impressions": 5}]
        self.assertEqual(P.serie_hebdo(lignes), [{"semaine": "2026-09-21", "clics": 5, "impressions": 30},
                                                 {"semaine": "2026-09-28", "clics": 1, "impressions": 5}])


class TestCommandes(DossierIsole):
    def test_injecter_puis_marquer(self):
        page = self.dossier / "tableau.html"
        page.write_text(GABARIT, encoding="utf-8")
        (self.dossier / "actions.json").write_text(json.dumps([{"id": "x1", "titre": "Réécrire le title", "type": "optimisation"}]),
                                                   encoding="utf-8")
        (self.dossier / "donnees.json").write_text(json.dumps({"nom": "Atlas Conseil", "kpis": {"clics_4s": 12}}),
                                                   encoding="utf-8")
        r = lancer("pilotage.py", "injecter", "--html", "tableau.html", "--projet-id", "atlas", "--donnees", "donnees.json",
                   "--actions", "actions.json", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = lancer("pilotage.py", "marquer", "--html", "tableau.html", "--projet-id", "atlas", "--id", "x1",
                   "--statut", "validee", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = lancer("pilotage.py", "etat", "--html", "tableau.html", "--projet-id", "atlas", "--statut", "validee", "--json",
                   cwd=self.dossier)
        self.assertEqual([a["id"] for a in json.loads(r.stdout)], ["x1"])
        etat = P.lire_etat(page.read_text(encoding="utf-8"))
        self.assertEqual(etat["projets"][0]["nom"], "Atlas Conseil")

    def test_titre_et_action_consignee_depuis_une_conversation(self):
        page = self.dossier / "tableau.html"
        page.write_text(GABARIT, encoding="utf-8")
        r = lancer("pilotage.py", "injecter", "--html", "tableau.html", "--projet-id", "atlas", "--titre", "Pilotage Atlas Conseil",
                   cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        for _ in range(2):                                   # consignée deux fois : une seule ligne
            r = lancer("pilotage.py", "ajouter", "--html", "tableau.html", "--projet-id", "atlas", "--titre",
                       "Refonte de la page TVA", "--statut", "faite", "--lien", "https://exemple.test/pr/3", cwd=self.dossier)
            self.assertEqual(r.returncode, 0, r.stderr)
        html = page.read_text(encoding="utf-8")
        self.assertIn("<title>Pilotage Atlas Conseil</title>", html)
        actions = P.lire_etat(html)["projets"][0]["actions"]
        self.assertEqual([(a["statut"], a["source"]) for a in actions], [("faite", "conversation")])

    def test_chantier_bloquee_et_historique(self):
        page = self.dossier / "tableau.html"
        page.write_text(GABARIT, encoding="utf-8")
        r = lancer("pilotage.py", "ajouter", "--html", "tableau.html", "--projet-id", "atlas", "--titre", "Scan Wordfence",
                   "--type", "technique", "--chantier", "securite", "--statut", "bloquee", "--attend", "la freelance",
                   cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = lancer("pilotage.py", "ajouter", "--html", "tableau.html", "--projet-id", "atlas", "--titre", "Pages villes",
                   "--type", "contenu", "--date", "2026-09-24", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        actions = {a["titre"]: a for a in P.lire_etat(page.read_text(encoding="utf-8"))["projets"][0]["actions"]}
        self.assertEqual((actions["Scan Wordfence"]["chantier"], actions["Scan Wordfence"]["attend"]), ("securite", "la freelance"))
        self.assertEqual((actions["Pages villes"]["chantier"], actions["Pages villes"]["maj"], actions["Pages villes"]["mois"]),
                         ("contenus", "2026-09-24", "2026-09"))          # un historique se range dans son mois

    def test_bilan_de_semaine_rejoue_sans_doublon_puis_sauvegarde_et_restauration(self):
        page = self.dossier / "tableau.html"
        page.write_text(GABARIT, encoding="utf-8")
        bilan = {"mois": "2026-10", "synthese": "Mois de reprise.",
                 "wins": [{"texte": "/jev-seo/ en page 1", "lien": "https://exemple.test/jev"}],
                 "contenus": [{"titre": "Jev SEO", "url": "https://exemple.test/jev", "statut": "publié"}],
                 "semaine": {"date": "2026-10-02", "resume": "3 actions livrées"}}
        (self.dossier / "semaine.json").write_text(json.dumps(bilan), encoding="utf-8")
        for _ in range(2):                                   # la routine relancée ne double rien
            r = lancer("pilotage.py", "mois", "--html", "tableau.html", "--projet-id", "atlas", "--fichier", "semaine.json",
                       cwd=self.dossier)
            self.assertEqual(r.returncode, 0, r.stderr)
        m = P.lire_etat(page.read_text(encoding="utf-8"))["projets"][0]["mois"]["2026-10"]
        self.assertEqual((len(m["wins"]), len(m["contenus"]), len(m["semaines"])), (1, 1, 1))
        r = lancer("pilotage.py", "sauvegarder", "--html", "tableau.html", "--projet-id", "atlas", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        copie = json.loads((self.dossier / "journal" / "pilotage.json").read_text(encoding="utf-8"))
        self.assertEqual(copie["id"], "atlas")
        page.write_text(GABARIT, encoding="utf-8")           # page perdue : on la reconstruit depuis git
        r = lancer("pilotage.py", "restaurer", "--html", "tableau.html", "--projet-id", "atlas", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(P.lire_etat(page.read_text(encoding="utf-8"))["projets"][0]["mois"]["2026-10"]["synthese"],
                         "Mois de reprise.")
        r = lancer("pilotage.py", "restaurer", "--html", "tableau.html", "--projet-id", "autre", cwd=self.dossier)
        self.assertNotEqual(r.returncode, 0)                 # jamais la copie d'un projet dans un autre


    def test_charte_du_projet(self):
        page = self.dossier / "tableau.html"
        page.write_text(GABARIT, encoding="utf-8")
        (self.dossier / "theme.json").write_text(json.dumps({"mode": "sombre", "fond": "#07080f", "accent": "#9d86ff"}),
                                                 encoding="utf-8")
        r = lancer("pilotage.py", "injecter", "--html", "tableau.html", "--projet-id", "atlas", "--theme", "theme.json",
                   cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        p = P.lire_etat(page.read_text(encoding="utf-8"))["projets"][0]
        self.assertEqual(p["theme"]["mode"], "sombre")
        self.assertIn("appliquerTheme", GABARIT)                      # la page applique la charte du projet


class TestProgramme(DossierIsole):
    """Programme sur plusieurs mois : liens obtenus, actions programmées, pages de l'ancien format."""

    def page(self, contenu=GABARIT):
        (self.dossier / "tableau.html").write_text(contenu, encoding="utf-8")
        return self.dossier / "tableau.html"

    def test_lien_ajoute_puis_mis_a_jour_sans_doublon(self):
        page = self.page()
        args = ("pilotage.py", "lien", "--html", "tableau.html", "--projet-id", "atlas",
                "--url", "https://www.media.example/article-geo/", "--cible", "/audit-geo/", "--ancre", "audit GEO",
                "--prix", "180,50 €", "--attribut", "Dofollow", "--date", "2026-11-04")
        r = lancer(*args, cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = lancer(*args[:-2], "--statut", "à relancer", "--date", "2026-11-04", cwd=self.dossier)   # même URL : mise à jour
        self.assertEqual(r.returncode, 0, r.stderr)
        r = lancer("pilotage.py", "lien", "--html", "tableau.html", "--projet-id", "atlas", "--url",
                   "https://annuaire.example/decupler", "--date", "2026-10-20", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        liens = P.lire_etat(page.read_text(encoding="utf-8"))["projets"][0]["liens"]
        self.assertEqual([l["domaine"] for l in liens], ["annuaire.example", "media.example"])      # rangés par date
        l = liens[1]
        self.assertEqual((l["prix"], l["attribut"], l["statut"], l["cible"], l["ancre"]),
                         (180.5, "dofollow", "à relancer", "/audit-geo/", "audit GEO"))
        self.assertEqual(liens[0]["statut"], "en-ligne")                                          # défaut
        self.assertNotIn("prix", liens[0])                                                        # lien gratuit
        for mauvais in (("--url", "media.example/x"), ("--url", "https://m.example/x", "--prix", "cher"),
                        ("--url", "https://m.example/x", "--date", "04/11/2026")):
            r = lancer("pilotage.py", "lien", "--html", "tableau.html", "--projet-id", "atlas", *mauvais, cwd=self.dossier)
            self.assertNotEqual(r.returncode, 0, mauvais)
        self.assertEqual(len(P.lire_etat(page.read_text(encoding="utf-8"))["projets"][0]["liens"]), 2)

    def test_mois_cible_programme_et_masque_aux_routines(self):
        page = self.page()
        for titre in ("Page « audit SEO »", "Page « consultant SEO Lille »"):
            r = lancer("pilotage.py", "ajouter", "--html", "tableau.html", "--projet-id", "atlas", "--titre", titre,
                       "--type", "contenu", "--statut", "validee", cwd=self.dossier)
            self.assertEqual(r.returncode, 0, r.stderr)
        actions = P.lire_etat(page.read_text(encoding="utf-8"))["projets"][0]["actions"]
        lille = next(a["id"] for a in actions if "Lille" in a["titre"])
        r = lancer("pilotage.py", "mois-cible", "--html", "tableau.html", "--projet-id", "atlas", "--id", lille,
                   "--mois", "2099-11", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        a = next(x for x in P.lire_etat(page.read_text(encoding="utf-8"))["projets"][0]["actions"] if x["id"] == lille)
        self.assertEqual(a["mois_cible"], "2099-11")
        # la routine ne lance pas une action validée programmée plus tard…
        r = lancer("pilotage.py", "etat", "--html", "tableau.html", "--projet-id", "atlas", "--statut", "validee", "--json",
                   cwd=self.dossier)
        self.assertEqual([x["titre"] for x in json.loads(r.stdout)], ["Page « audit SEO »"])
        self.assertIn("programmée", r.stderr)
        # … mais elle reste visible
        r = lancer("pilotage.py", "etat", "--html", "tableau.html", "--projet-id", "atlas", "--statut", "validee", "--toutes",
                   "--json", cwd=self.dossier)
        self.assertEqual(len(json.loads(r.stdout)), 2)
        r = lancer("pilotage.py", "etat", "--html", "tableau.html", "--projet-id", "atlas", cwd=self.dossier)
        self.assertEqual(r.stdout.count("[validee"), 2)
        self.assertIn("prévue 2099-11", r.stdout)
        for mauvais in (("--id", lille, "--mois", "2026-13"), ("--id", lille, "--mois", "novembre"),
                        ("--id", "inconnu", "--mois", "2026-11"), ("--id", lille)):
            r = lancer("pilotage.py", "mois-cible", "--html", "tableau.html", "--projet-id", "atlas", *mauvais, cwd=self.dossier)
            self.assertNotEqual(r.returncode, 0, mauvais)
        r = lancer("pilotage.py", "mois-cible", "--html", "tableau.html", "--projet-id", "atlas", "--id", lille, "--retirer",
                   cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        a = next(x for x in P.lire_etat(page.read_text(encoding="utf-8"))["projets"][0]["actions"] if x["id"] == lille)
        self.assertNotIn("mois_cible", a)
        # programmée dès sa création, et jamais effacée quand la proposition se rafraîchit
        r = lancer("pilotage.py", "ajouter", "--html", "tableau.html", "--projet-id", "atlas", "--titre", "Sortir de WordPress",
                   "--type", "decision", "--statut", "proposee", "--mois-cible", "2027-03", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        p = P.lire_etat(page.read_text(encoding="utf-8"))["projets"][0]
        x = next(a for a in p["actions"] if a["titre"] == "Sortir de WordPress")
        self.assertEqual(x["mois_cible"], "2027-03")
        P.fusionner_actions(p["actions"], [{"id": x["id"], "titre": "Sortir de WordPress", "mois_cible": "2026-10"}], "2026-10-09")
        self.assertEqual(x["mois_cible"], "2027-03")

    def test_page_de_l_ancien_format_lue_et_reinjectee_sans_perte(self):
        ancien = (Path(__file__).parent / "fixtures" / "pilotage-3.10.html").read_text(encoding="utf-8")
        avant = P.lire_etat(ancien)
        self.assertNotIn("vueRoadmap", ancien)                                   # c'est bien l'ancien gabarit
        # les commandes lisent et écrivent l'ancienne page sans toucher à son code
        page = self.page(ancien)
        r = lancer("pilotage.py", "etat", "--html", "tableau.html", "--projet-id", "atlas", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.count("\n"), len(avant["projets"][0]["actions"]))
        # réinjection dans le nouveau gabarit : même état, même contenu hôte, même titre
        r = lancer("pilotage.py", "integrer", "--hote", "tableau.html", "--etat-depuis", "tableau.html",
                   "--sortie", "nouveau.html", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        nouveau = (self.dossier / "nouveau.html").read_text(encoding="utf-8")
        self.assertEqual(P.lire_etat(nouveau), avant)
        self.assertIn("vueRoadmap", nouveau)
        hote = ancien[ancien.index('<template id="hote">'):ancien.index("</template>") + len("</template>")]
        self.assertEqual(nouveau.count(hote), 1)
        self.assertIn("<title>Pilotage Atlas Conseil</title>", nouveau)
        # puis les commandes habituelles sur la nouvelle page ne perdent rien
        (self.dossier / "tableau.html").write_text(nouveau, encoding="utf-8")
        (self.dossier / "theme.json").write_text(json.dumps(avant["projets"][0]["theme"]), encoding="utf-8")
        for args in (("injecter", "--theme", "theme.json"), ("marquer", "--id", "a2", "--statut", "validee"),
                     ("mois-cible", "--id", "a4", "--mois", "2026-12"),
                     ("lien", "--url", "https://media.example/a", "--date", "2026-10-02")):
            r = lancer("pilotage.py", args[0], "--html", "tableau.html", "--projet-id", "atlas", *args[1:], cwd=self.dossier)
            self.assertEqual(r.returncode, 0, r.stderr)
        apres = P.lire_etat(page.read_text(encoding="utf-8"))
        pa, pb = avant["projets"][0], apres["projets"][0]
        for cle in pa:
            if cle != "actions":
                self.assertEqual(pb[cle], pa[cle], cle)
        self.assertEqual([a["id"] for a in pb["actions"]], [a["id"] for a in pa["actions"]])
        self.assertEqual(next(a for a in pb["actions"] if a["id"] == "a4")["mois_cible"], "2026-12")
        self.assertEqual(len(pb["liens"]), 1)
        self.assertEqual(apres["hote_mois"], avant["hote_mois"])
        # réintégrer une seconde fois n'emboîte pas le contenu hôte
        r = lancer("pilotage.py", "integrer", "--hote", "tableau.html", "--etat-depuis", "tableau.html",
                   "--sortie", "encore.html", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.dossier / "encore.html").read_text(encoding="utf-8").count(hote), 1)

    def test_gabarit_programme(self):
        for vue in ("vueSynthese", "vueDecider", "vueRoadmap", "vuePlan", "vueLiens", "vueReporting", "appliquerTheme",
                    "mois_cible", "p.liens"):
            self.assertIn(vue, GABARIT)
        self.assertNotRegex(GABARIT, r"opacity:\s*0[;}]")                     # rien d'invisible au chargement
        sans = P.integrer(GABARIT, P.ecrire_etat(GABARIT, {"projets": []}), {"projets": []})
        self.assertIn('<template id="hote"></template>', sans)                 # jamais le code de la page comme contenu


class TestBacklinksEtProgramme(DossierIsole):
    """Vue Backlinks organisée par mois, en-tête et phases du programme : relancer ne double rien."""

    PLAN = {"synthese": "Profil de liens propre en six mois", "responsable": "Consultant",
            "brief": {"titre": "Brief", "url": "https://exemple.test/brief"},
            "indicateurs": [{"nom": "Domaines propres", "depart": "10"}],
            "regles": [{"titre": "Ancres", "texte": "Marque d'abord"}],
            "mois": {"2026-10": {"titre": "Fondations", "cible": "+8 à 11",
                                 "taches": [{"qui": "Consultant", "texte": "Fiche annuaire A", "statut": "a-faire"},
                                            {"qui": "Client", "texte": "Valider la commande", "action": "a1"}],
                                 "cibles": [{"nom": "Annuaire A", "priorite": "0"}]},
                     "2026-11": {"titre": "Premiers achats"}}}

    def test_plan_fusionne_sans_doublon(self):
        p = {"id": "atlas"}
        P.fusionner_backlinks(p, self.PLAN)
        P.fusionner_backlinks(p, {"mois": {"2026-10": {"taches": [{"texte": "fiche annuaire a", "statut": "fait"}],
                                                          "cibles": [{"nom": "Annuaire B"}]}},
                                  "indicateurs": [{"nom": "Domaines propres", "cible_3m": "+20"}]})
        b = p["backlinks"]
        octobre = b["mois"]["2026-10"]
        self.assertEqual(len(octobre["taches"]), 2)
        self.assertEqual(octobre["taches"][0]["statut"], "fait")                 # mise à jour, pas de doublon
        self.assertEqual(octobre["taches"][0]["qui"], "Consultant")              # le reste est conservé
        self.assertEqual([c["nom"] for c in octobre["cibles"]], ["Annuaire A", "Annuaire B"])
        self.assertEqual(b["indicateurs"], [{"nom": "Domaines propres", "depart": "10", "cible_3m": "+20"}])
        self.assertEqual(list(b["mois"]), ["2026-10", "2026-11"])
        self.assertEqual(octobre["titre"], "Fondations")
        with self.assertRaises(SystemExit):
            P.fusionner_backlinks(p, {"mois": {"octobre": {}}})

    def test_commandes_backlinks_et_programme(self):
        page = self.dossier / "tableau.html"
        page.write_text(GABARIT, encoding="utf-8")
        (self.dossier / "plan.json").write_text(json.dumps(self.PLAN), encoding="utf-8")
        prog = {"surtitre": "Atlas · SEO", "intro": "Le programme", "debut": "2026-09", "fin": "2027-03",
                "phases": [{"titre": "Presse", "debut": "2027-01", "fin": "2027-03"},
                           {"titre": "Fondations", "debut": "2026-10", "fin": "2026-12"}]}
        (self.dossier / "prog.json").write_text(json.dumps(prog), encoding="utf-8")
        for _ in range(2):
            for cmd, f in (("backlinks", "plan.json"), ("programme", "prog.json")):
                r = lancer("pilotage.py", cmd, "--html", "tableau.html", "--projet-id", "atlas", "--fichier", f,
                           cwd=self.dossier)
                self.assertEqual(r.returncode, 0, r.stderr)
        p = P.lire_etat(page.read_text(encoding="utf-8"))["projets"][0]
        self.assertEqual(len(p["backlinks"]["mois"]["2026-10"]["taches"]), 2)
        self.assertEqual([x["titre"] for x in p["programme"]["phases"]], ["Fondations", "Presse"])   # rangées par date
        self.assertEqual(p["programme"]["surtitre"], "Atlas · SEO")
        (self.dossier / "faux.json").write_text(json.dumps({"phases": [{"titre": "X", "debut": "oct."}]}), encoding="utf-8")
        r = lancer("pilotage.py", "programme", "--html", "tableau.html", "--projet-id", "atlas", "--fichier", "faux.json",
                   cwd=self.dossier)
        self.assertNotEqual(r.returncode, 0)

    def test_guide_autonome_et_retrait(self):
        p = {"id": "atlas"}
        P.fusionner_backlinks(p, self.PLAN)
        P.fusionner_backlinks(p, {"documents": [{"titre": "Doc", "url": "https://exemple.test/doc"}],
                                  "guide": [{"titre": "Bloc NAP", "blocs": [{"copie": "Nom : Atlas"}]},
                                            {"titre": "Checklist", "intro": "Note sur 20",
                                             "blocs": [{"cases": ["Pertinence"]}, {"table": {"colonnes": ["A"], "lignes": [["1"]]}},
                                                       {"titre": "Ordre", "liste": ["un", "deux"], "ordonnee": True},
                                                       {"note": "Attention"}, {"texte": "Voir **https://exemple.test**"}]}]})
        P.fusionner_backlinks(p, {"guide": [{"titre": "bloc nap", "blocs": [{"copie": "Nom : Atlas SAS"}]}],
                                  "retirer": ["brief", {"documents": "https://EXEMPLE.test/doc"}],
                                  "mois": {"2026-10": {"retirer": [{"taches": "fiche annuaire a"}]},
                                           "2027-05": {"retirer": [{"taches": "rien"}]}}})
        b = p["backlinks"]
        self.assertEqual([s["titre"].lower() for s in b["guide"]], ["bloc nap", "checklist"])     # pas de doublon
        self.assertEqual(b["guide"][0]["blocs"], [{"copie": "Nom : Atlas SAS"}])                  # section remplacée
        self.assertNotIn("brief", b)
        self.assertEqual(b["documents"], [])
        self.assertEqual([t["texte"] for t in b["mois"]["2026-10"]["taches"]], ["Valider la commande"])
        self.assertNotIn("2027-05", b["mois"])                                                    # rien de créé pour rien
        for faux in ({"guide": [{"titre": "", "blocs": []}]}, {"guide": [{"titre": "X", "blocs": [{"texte": "a", "liste": []}]}]},
                     {"guide": [{"titre": "X", "blocs": [{"titre": "seul"}]}]}, {"retirer": [{"inconnue": "x"}]}):
            with self.assertRaises(SystemExit):
                P.fusionner_backlinks(p, faux)

    def test_gabarit_backlinks_par_mois_theme_clair_et_hote_isole(self):
        for marque in ("detailBacklinks", "moisBacklinks", "statutTache", "frise(", "p.programme", "rendreHote",
                       "attachShadow", "pl-theme", "theme.clair", 'prefers-color-scheme:dark', ':root[data-theme="dark"]'):
            self.assertIn(marque, GABARIT)
        self.assertIn("valeurSure", GABARIT)                                        # pas d'injection CSS par la charte
        for marque in ("guideBacklinks", "sommaireGuide", "blocGuide", "copier(", "execCommand", "pl-cases", "pl-copie"):
            self.assertIn(marque, GABARIT)                                         # guide autonome, bouton Copier avec repli
        self.assertNotIn("innerHTML", GABARIT[GABARIT.index("function riche"):GABARIT.index("function vueLiens")])


class TestMois(unittest.TestCase):
    def test_semaine_remplacee_et_wins_mis_a_jour(self):
        p = {"id": "atlas"}
        P.fusionner_mois(p, {"mois": "2026-10", "semaine": {"date": "2026-10-02", "resume": "v1"},
                             "wins": [{"texte": "Top 3 sur « tva »"}]})
        P.fusionner_mois(p, {"mois": "2026-10", "semaine": {"date": "2026-10-02", "resume": "v2"},
                             "wins": [{"texte": "top 3 sur « tva »", "lien": "https://exemple.test"}]})
        m = p["mois"]["2026-10"]
        self.assertEqual([s["resume"] for s in m["semaines"]], ["v2"])
        self.assertEqual(len(m["wins"]), 1)
        self.assertEqual(m["wins"][0]["lien"], "https://exemple.test")

    def test_bloquee_efface_l_attente_en_repartant(self):
        p = {"id": "atlas", "actions": [{"id": "a", "titre": "T", "statut": "validee"}]}
        P.marquer_action(p, "a", "bloquee", attend="accès FTP")
        self.assertEqual(p["actions"][0]["attend"], "accès FTP")
        P.marquer_action(p, "a", "validee")
        self.assertNotIn("attend", p["actions"][0])

    def test_chantier_deduit(self):
        self.assertEqual(P.chantier_de({"type": "contenu"}), "contenus")
        self.assertEqual(P.chantier_de({"type": "decision", "source": "points-ouverts"}), "pilotage")
        self.assertEqual(P.chantier_de({"type": "optimisation", "chantier": "geo"}), "geo")


if __name__ == "__main__":
    unittest.main()


class TestExport(DossierIsole):
    """Vue exportée pour un intervenant externe : rien d'interne n'est écrit dans la page, et elle reste en lecture seule."""

    ETAT = {"maj": "2026-10-09", "titre": "Pilotage Atlas", "hote_mois": "2026-09", "projets": [{
        "id": "atlas", "nom": "Atlas", "site": "atlas.example", "session": "https://claude.ai/code/session_x",
        "depot": "atlas/site", "notion": "https://notion.example/base", "kpis": {"clics_4s": 12},
        "livrables": [{"titre": "Kit interne", "url": "https://interne.example/kit"}],
        "mois": {"2026-10": {"synthese": "Bilan interne"}}, "theme": {"mode": "sombre", "fond": "#07080f"},
        "programme": {"surtitre": "Atlas · SEO", "intro": "Programme complet", "debut": "2026-09", "fin": "2027-03",
                      "phases": [{"titre": "Nettoyage du piratage", "debut": "2026-09", "fin": "2026-09"}]},
        "actions": [
            {"id": "o1", "titre": "Annuaire sectoriel", "chantier": "off-page", "statut": "validee", "note": "remarque interne",
             "lien": "https://github.com/atlas/site/pull/3", "pourquoi": "Aucun lien depuis le piratage", "source": "conversation"},
            {"id": "o2", "titre": "Commander deux articles", "chantier": "off-page", "statut": "faite", "maj": "2026-10-08",
             "lien": "https://media.example/article"},
            {"id": "o3", "titre": "Fiche rejetée", "chantier": "off-page", "statut": "refusee"},
            {"id": "o4", "titre": "Changer le mot de passe admin", "chantier": "off-page", "statut": "proposee"},
            {"id": "s1", "titre": "Mettre à jour Wordfence", "chantier": "securite", "statut": "faite"},
            {"id": "c1", "titre": "Brouillon 21200 à relire", "chantier": "contenus", "statut": "validee"}],
        "liens": [{"url": "https://media.example/article", "domaine": "media.example", "date": "2026-10-08"}],
        "backlinks": {
            "synthese": "Dix domaines propres.", "responsable": "Le consultant",
            "documents": [{"titre": "Brief", "url": "https://github.com/atlas/site/blob/main/brief.md"}],
            "mois": {"2026-10": {"taches": [{"qui": "Consultant", "texte": "Commander", "action": "o2"},
                                            {"qui": "Claude", "texte": "Sécuriser", "action": "s1"},
                                            {"qui": "Claude", "texte": "Voir https://claude.ai/code/session_x"}]}},
            "guide": [{"titre": "Contexte", "blocs": [
                {"liste": ["Site nettoyé chez l'hébergeur OVH", "Dix domaines propres"]},
                {"table": {"colonnes": ["Cible", "Note"], "lignes": [["Média A", "ok"], ["Dépôt", "https://github.com/atlas"]]}},
                {"note": "Accès : jamais par e-mail, WP_APP_PASSWORD dans le .env"}]},
                {"titre": "Accès OVH", "blocs": [{"texte": "interne"}]}]}}]}

    def exporter(self, *extra):
        (self.dossier / "tableau.html").write_text(P.ecrire_etat(GABARIT, self.ETAT), encoding="utf-8")
        return lancer("pilotage.py", "exporter", "--html", "tableau.html", "--projet-id", "atlas", "--vue", "backlinks",
                      "--sortie", "vue.html", *extra, cwd=self.dossier)

    def test_vue_backlinks_sans_rien_d_interne(self):
        r = self.exporter("--interdit", r"\bOVH\b", "--interdit", "piratage|wordfence")
        self.assertEqual(r.returncode, 0, r.stderr)
        html = (self.dossier / "vue.html").read_text(encoding="utf-8")
        etat = P.lire_etat(html)
        q = etat["projets"][0]
        self.assertEqual(etat["vue"], {"nom": "backlinks", "onglets": ["liens", "roadmap", "actions"], "lecture_seule": True,
                                       "message": P.VUES_EXPORT["backlinks"]["message"]})
        self.assertEqual(set(q), {"id", "nom", "site", "theme", "backlinks", "liens", "actions", "programme"})
        self.assertEqual(q["programme"], {"surtitre": "Atlas · SEO", "intro": "Programme complet", "debut": "2026-09",
                                          "fin": "2027-03"})                     # en-tête réduit : pas de phases
        self.assertEqual([a["id"] for a in q["actions"]], ["o1", "o2"])          # off-page seulement, ni refusée ni secret
        o1 = q["actions"][0]
        self.assertEqual(set(o1), {"id", "titre", "chantier", "statut"})        # ni note, ni source, ni lien de dépôt
        taches = q["backlinks"]["mois"]["2026-10"]["taches"]
        self.assertEqual(taches[0]["action"], "o2")                              # action exportée : lien gardé
        self.assertEqual((taches[1].get("action"), taches[1]["statut"]), (None, "fait"))   # absente : son statut reste
        self.assertEqual(len(taches), 2)                                          # la tâche au lien de session tombe
        g = q["backlinks"]["guide"]
        self.assertEqual([s["titre"] for s in g], ["Contexte"])                  # section au titre interdit retirée
        self.assertEqual(g[0]["blocs"][0]["liste"], ["Dix domaines propres"])
        self.assertEqual(g[0]["blocs"][1]["table"]["lignes"], [["Média A", "ok"]])   # ligne entière, colonnes intactes
        self.assertEqual(len(g[0]["blocs"]), 2)                                   # bloc vidé retiré
        self.assertFalse(q["backlinks"].get("documents"))                      # document au lien de dépôt retiré
        self.assertEqual(etat["titre"], "Programme backlinks · Atlas")
        donnees = json.dumps(etat, ensure_ascii=False)
        for interdit in ("claude.ai/code", "github", "atlas/site", "Wordfence", "OVH", "piratage", "21200", "mot de passe",
                         "Kit interne", "Bilan interne", "notion.example", "remarque interne", "hote_mois", "PASSWORD"):
            self.assertNotIn(interdit, donnees, interdit)
        self.assertNotIn('<template id="hote">', html.split('<script type="application/json" id="etat">')[0])  # ni contenu hôte
        self.assertIn("FIGEE", html)                                              # lecture seule, sans republication
        self.assertIn("élément(s) retiré(s)", r.stdout)

    def test_interdits_par_fichier_et_vue_inconnue(self):
        (self.dossier / "interdits.txt").write_text("# motifs du projet\nAnnuaire\n", encoding="utf-8")
        r = self.exporter("--interdits", "interdits.txt", "--titre", "Programme backlinks Atlas", "--intro", "Pour le consultant")
        self.assertEqual(r.returncode, 0, r.stderr)
        etat = P.lire_etat((self.dossier / "vue.html").read_text(encoding="utf-8"))
        self.assertEqual([a["id"] for a in etat["projets"][0]["actions"]], ["o2"])
        self.assertEqual((etat["titre"], etat["projets"][0]["programme"]["intro"]), ("Programme backlinks Atlas", "Pour le consultant"))
        self.assertIn("<title>Programme backlinks Atlas</title>", (self.dossier / "vue.html").read_text(encoding="utf-8"))
        for mauvais in (("--vue", "tout"), ("--interdit", "(")):
            r = lancer("pilotage.py", "exporter", "--html", "tableau.html", "--projet-id", "atlas", "--vue", "backlinks",
                       "--sortie", "x.html", *mauvais, cwd=self.dossier)
            self.assertNotEqual(r.returncode, 0, mauvais)
        r = lancer("pilotage.py", "exporter", "--html", "tableau.html", "--projet-id", "autre", "--vue", "backlinks",
                   "--sortie", "x.html", cwd=self.dossier)
        self.assertNotEqual(r.returncode, 0)

    def test_purge_et_dernier_filet(self):
        motif = P._compiler_interdits(["secret"])
        retraits = []
        self.assertIsNone(P.purger({"titre": "un secret", "texte": "x"}, motif, "a", retraits))
        self.assertEqual(P.purger({"titre": "ok", "lien": "secret"}, motif, "b", retraits), {"titre": "ok"})
        self.assertEqual(len(retraits), 2)
        etat = {"maj": "", "projets": [{"id": "atlas", "actions": []}], "decideur": "secret"}
        with self.assertRaises(SystemExit):                                       # rien ne sort s'il reste un motif
            P.vue_exportee(etat, "atlas", "backlinks", ["secret"])

    def test_gabarit_vue_exportee(self):
        for marque in ("VUES_PAGE", "EXPORT.onglets.map(", "EXPORT.message", "if(FIGEE){li.append(corps);return li}", "lien(p.depot_url,\"Dépôt\")"):
            self.assertIn(marque, GABARIT)
        self.assertNotIn("github.com", GABARIT)                                  # aucun hébergeur de code dans le code de la page

    def test_injecter_depot_en_adresse(self):
        (self.dossier / "tableau.html").write_text(GABARIT, encoding="utf-8")
        r = lancer("pilotage.py", "injecter", "--html", "tableau.html", "--projet-id", "atlas", "--depot", "atlas/site",
                   cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        p = P.lire_etat((self.dossier / "tableau.html").read_text(encoding="utf-8"))["projets"][0]
        self.assertEqual((p["depot"], p["depot_url"]), ("atlas/site", "https://github.com/atlas/site"))
