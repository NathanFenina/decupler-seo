"""Cartographie : un mot-clé principal et un prompt principal par page, suivis chaque mois.

Aucun appel réseau : Search Console est remplacé par des exports CSV, les
moteurs IA par des relevés déjà écrits.
"""

import csv
import json
import re
import sys
import unittest
from pathlib import Path

from _outils import SCRIPTS, DossierIsole, lancer

sys.path.insert(0, str(SCRIPTS))
import cartographie as carto  # noqa: E402
import rapport  # noqa: E402

CONFIG = """projet:
  nom: "Atlas Conseil"
  domaine: "atlas-conseil.example"
  pays_cible: FR
  langues: [fr]
sorties:
  langue: fr
"""
SITE = "https://atlas-conseil.example"

# requête, page, clics, impressions, position — août puis septembre 2026
AOUT = [
    ("création entreprise lyon", "/creation-entreprise-lyon", 22, 800, 7.9),
    ("creer sa societe lyon", "/creation-entreprise-lyon", 3, 250, 10.0),
    ("atlas conseil création", "/creation-entreprise-lyon", 30, 60, 1.0),
    ("tva auto entrepreneur", "/blog/tva-auto-entrepreneur", 20, 1400, 8.1),
    ("expert comptable lyon", "/expert-comptable-lyon", 6, 1100, 6.9),
    ("comment choisir son expert comptable", "/blog/choisir-expert-comptable", 1, 350, 11.0),
    ("atlas conseil", "/", 90, 280, 1.0),
]
SEPTEMBRE = [
    ("création entreprise lyon", "/creation-entreprise-lyon", 40, 900, 4.2),
    ("creer sa societe lyon", "/creation-entreprise-lyon", 5, 300, 9.0),
    ("atlas conseil création", "/creation-entreprise-lyon", 35, 70, 1.0),
    ("tva auto entrepreneur", "/blog/tva-auto-entrepreneur", 12, 1500, 12.4),
    ("expert comptable lyon", "/expert-comptable-lyon", 8, 1200, 6.5),
    ("expert comptable lyon", "/blog/choisir-expert-comptable", 2, 300, 5.1),
    ("comment choisir son expert comptable", "/blog/choisir-expert-comptable", 3, 400, 9.0),
    ("atlas conseil", "/", 100, 300, 1.0),
]
CALENDRIER = """# Calendrier éditorial

| Semaine | Type | Funnel | Requête | Page | Action | Schéma | Statut |
|---|---|---|---|---|---|---|---|
| 2026-10-05 | création | MOFU | holding patrimoniale | à créer | Créer une page | — | à planifier |
| 2026-10-05 | optimisation | TOFU | tva auto entrepreneur | atlas-conseil.example/blog/tva-auto-entrepreneur | Réécrire | — | à planifier |
| 2026-10-12 | création | TOFU | création entreprise lyon | à créer | Créer une page | — | à planifier |
"""
PROMPT_HUMAIN = "Quel cabinet choisir pour créer mon entreprise à Lyon ?"


def export(lignes) -> str:
    texte = "query,page,clicks,impressions,position\n"
    return texte + "".join(f"{q},{SITE}{p},{c},{i},{pos}\n" for q, p, c, i, pos in lignes)


def releves(lignes) -> str:
    """moteur, prompt, cite, rang, nomme, concurrents, sources — format de share_of_model.py."""
    texte = "moteur,famille,funnel,poids,prompt,cite,rang,nomme,rang_liste,concurrents_nommes,sources,extrait\n"
    return texte + "".join(f'{m},visibilite,BOFU,3,"{p}",{c},{r},{n},0,"{conc}","{src}",\n'
                           for m, p, c, r, n, conc, src in lignes)


class TestCalculsPurs(unittest.TestCase):
    MARQUE = [re.compile("atlas", re.I)]

    def test_mot_cle_principal_clics_puis_impressions_hors_marque(self):
        lignes = [{"requete": "atlas conseil avis", "clics": 50, "impressions": 60},
                  {"requete": "tva", "clics": 0, "impressions": 900},
                  {"requete": "tva auto entrepreneur", "clics": 4, "impressions": 100},
                  {"requete": "TVA  Auto entrepreneur", "clics": 1, "impressions": 20}]
        principal, secondaires = carto.choisir_mot_cle(lignes, self.MARQUE)
        self.assertEqual(principal, "tva auto entrepreneur")        # 5 clics cumulés, la marque exclue
        self.assertEqual(secondaires, ["tva"])
        sans_clic = [{"requete": "a", "clics": 0, "impressions": 10}, {"requete": "b", "clics": 0, "impressions": 90}]
        self.assertEqual(carto.choisir_mot_cle(sans_clic, [])[0], "b")
        self.assertEqual(carto.choisir_mot_cle([lignes[0]], self.MARQUE), ("", []))

    def test_prompts_fr_en_ar_et_question_gardee(self):
        self.assertEqual(carto.proposer_prompt("expert comptable lyon", "transactionnel"),
                         "Qui me recommandes-tu pour expert comptable lyon ?")
        self.assertEqual(carto.proposer_prompt("comment créer une sarl", "informationnel"), "Comment créer une sarl ?")
        self.assertEqual(carto.proposer_prompt("company formation dubai", "informationnel", "en"),
                         "What should I know about company formation dubai?")
        self.assertTrue(carto.proposer_prompt("إنشاء شركة", "transactionnel", "ar").endswith("؟"))
        # Avec une catégorie, le gabarit BOFU de share_of_model : les deux mesures restent comparables.
        self.assertEqual(carto.proposer_prompt("création entreprise", "transactionnel", "fr", "cabinet comptable"),
                         "Quel est le meilleur cabinet comptable pour création entreprise ?")

    def test_langue_et_type(self):
        self.assertEqual(carto.langue_de("company formation dubai"), "en")
        self.assertEqual(carto.langue_de("prix création entreprise"), "fr")
        self.assertEqual(carto.langue_de("إنشاء شركة"), "ar")
        self.assertEqual(carto.langue_de("x", "https://a.example/en/x"), "en")
        self.assertEqual(carto.type_de("https://a.example/"), "offre")
        self.assertEqual(carto.type_de("https://a.example/blog/tva"), "article")
        self.assertEqual(carto.type_de("https://a.example/simulateur-tva"), "outil")
        self.assertEqual(carto.type_de("https://a.example/modele-business-plan"), "lead-magnet")

    def test_fusion_ne_ecrase_jamais(self):
        existantes = [{**{c: "" for c in carto.COLONNES}, "url": "https://a.example/tva", "statut": "existante",
                       "mot_cle_principal": "tva auto entrepreneur", "prompt_principal": "Mon prompt ?",
                       "a_valider": ""},
                      {**{c: "" for c in carto.COLONNES}, "statut": "a-creer", "mot_cle_principal": "holding"}]
        propositions = [
            {"url": "https://www.a.example/tva/", "statut": "existante", "mot_cle_principal": "tva",
             "prompt_principal": "Autre ?", "silo": "fiscalite", "a_valider": "mot_cle_principal;prompt_principal"},
            {"url": "https://a.example/holding", "statut": "existante", "mot_cle_principal": "holding"},
            {"url": "", "statut": "a-creer", "mot_cle_principal": "tva auto entrepreneur"},
            {"url": "https://a.example/nouvelle", "statut": "existante", "mot_cle_principal": "sci",
             "_source": "gsc", "a_valider": "prompt_principal"}]
        stats = carto.fusionner(existantes, propositions, "2026-09-29")
        tva = existantes[0]
        self.assertEqual((tva["mot_cle_principal"], tva["prompt_principal"]), ("tva auto entrepreneur", "Mon prompt ?"))
        self.assertEqual(tva["silo"], "fiscalite")                   # cellule vide : complétée
        self.assertEqual(tva["a_valider"], "")                        # seules les cellules remplies sont à valider
        self.assertEqual((existantes[1]["url"], existantes[1]["statut"]), ("https://a.example/holding", "publiee"))
        self.assertEqual(len(existantes), 3)                          # pas de doublon « à créer » sur un mot-clé pris
        self.assertNotIn("_source", existantes[2])
        self.assertEqual(stats, {"ajoutees": 1, "completees": 1, "publiees": 1})

    def test_page_prevue_publiee_d_apres_le_journal(self):
        lignes = [{**{c: "" for c in carto.COLONNES}, "statut": "a-creer", "mot_cle_principal": "Holding"}]
        carto.fusionner(lignes, [], "2026-09-29", {"holding": "https://a.example/holding"})
        self.assertEqual((lignes[0]["statut"], lignes[0]["url"]), ("publiee", "https://a.example/holding"))

    def test_cannibalisation(self):
        lignes = [{"url": "https://a.example/a", "mot_cle_principal": "TVA"},
                  {"url": "https://a.example/b", "mot_cle_principal": "tva"},
                  {"url": "", "mot_cle_principal": "sci"}]
        self.assertEqual(carto.doublons(lignes), {"tva": ["/a", "/b"]})

    def test_sitemap_et_calendrier(self):
        xml = ("<urlset><url><loc>https://a.example/x?a=1&amp;b=2</loc><image:image><image:loc>https://a.example/i.jpg"
               "</image:loc></image:image></url></urlset>")
        self.assertEqual(carto.urls_du_sitemap(xml), (["https://a.example/x?a=1&b=2"], False))
        self.assertTrue(carto.urls_du_sitemap("<sitemapindex><sitemap><loc>https://a.example/s.xml</loc>")[1])
        self.assertTrue(carto.PAS_UNE_PAGE.search("https://a.example/tag/tva/"))
        prevues = carto.propositions_calendrier(carto.lire_calendrier(CALENDRIER))
        self.assertEqual([p["mot_cle_principal"] for p in prevues], ["holding patrimoniale", "création entreprise lyon"])
        self.assertEqual(prevues[0]["funnel"], "MOFU")

    def test_releves_le_plus_recent_gagne_sans_web_ecarte(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "ia-2026-08.csv").write_text(releves([("openai", "Q ?", "False", 0, "False", "", "rival.example")]),
                                              encoding="utf-8")
            (d / "ia-2026-09.csv").write_text(releves([("openai", "Q ?", "True", 2, "True", "", "atlas-conseil.example")]),
                                              encoding="utf-8")
            (d / "ia-2026-09-sans-web.csv").write_text(releves([("gemini", "Q ?", "True", 1, "True", "", "")]),
                                                       encoding="utf-8")
            (d / "ia-2026-11.csv").write_text(releves([("claude", "Q ?", "True", 1, "True", "", "")]), encoding="utf-8")
            (d / "grille.csv").write_text("famille,funnel,poids,prompt,moteur,cite,rang,nomme,sources,extrait\n"
                                          "visibilite,MOFU,2,Q ?,ChatGPT,,,,,\n", encoding="utf-8")
            (d / "ia-2026-10.csv").write_text(releves([("openai", "Q ?", "False", 0, "False", "", ""),
                                                       ("openai", "Neuf ?", "True", 1, "True", "", "")]),
                                              encoding="utf-8")
            ia = carto.lire_releves(sorted(d.glob("*.csv")), "2026-09", "atlas-conseil.example")
            self.assertEqual(ia["neuf ?"]["openai"], "cite:1")        # jamais mesuré avant : relevé du 1er du mois suivant
            self.assertEqual(ia["q ?"]["openai"], "cite:2")
            self.assertNotIn("gemini", ia["q ?"])                      # notoriété sans web : autre mesure
            self.assertNotIn("claude", ia["q ?"])                      # deux mois plus tard : écarté
            self.assertEqual(ia["q ?"]["mesure"], "2026-09")
        self.assertEqual(carto.etat_ia({"cite": "non", "nomme": "oui"}), "nomme")
        self.assertEqual(carto.etat_ia({"cite": "", "nomme": ""}), "")

    def test_actions_suggerees(self):
        base = {"statut": "existante", "mot_cle_principal": "x", "impressions": 500, "funnel": "BOFU"}
        self.assertEqual(carto.action_suggeree({**base, "position_mc": 6.0})[0], "Optimiser → top 3")
        self.assertEqual(carto.action_suggeree({**base, "position_mc": 14.0})[0], "Mettre à jour (quick win)")
        self.assertIn("Perd 4,3 places", carto.action_suggeree({**base, "position_mc": 12.4, "delta_position_mc": -4.3})[1])
        self.assertEqual(carto.action_suggeree({**base, "impressions": 0})[0], "Vérifier indexation / Relancer")
        self.assertIn("peu cliquée", carto.action_suggeree({**base, "position_mc": 2.0, "impressions_mc": 400,
                                                            "ctr_mc": 1.0})[1])
        geo = carto.action_suggeree({**base, "position_mc": 2.0, "ia_openai": "absent", "ia_gemini": "absent"})[1]
        self.assertIn("GEO", geo)
        self.assertIn("ne pas toucher", carto.action_suggeree({**base, "en_mesure": "2026-10-20"})[1])
        self.assertEqual(carto.action_suggeree({"statut": "a-creer"})[1], "Créer la page : benchmark, brief, rédaction")

    def test_construire_mois_page_sur_son_mot_cle(self):
        def lignes(donnees):
            return [{"requete": q, "page": SITE + p, "clics": c, "impressions": i, "position": pos}
                    for q, p, c, i, pos in donnees]
        ligne = {**{c: "" for c in carto.COLONNES}, "url": SITE + "/expert-comptable-lyon", "statut": "existante",
                 "mot_cle_principal": "expert comptable lyon", "prompt_principal": "P ?", "funnel": "BOFU"}
        hist = {carto.cle_de(ligne): {"ia_openai": "absent", "ia_gemini": "cite:1"}}
        ia = {"p ?": {"openai": "cite:3", "gemini": "absent", "mesure": "2026-09", "concurrent": "rival.example"}}
        r = carto.construire_mois([ligne], carto.indexer(lignes(SEPTEMBRE)), carto.indexer(lignes(AOUT)),
                                  carto.indexer(lignes(SEPTEMBRE), True), carto.indexer(lignes(AOUT), True),
                                  ia, hist, "2026-09")[0]
        self.assertEqual((r["position_mc"], r["position_mc_prec"], r["delta_position_mc"]), (6.5, 6.9, 0.4))
        self.assertEqual((r["clics_mc"], r["delta_clics_mc"]), (8, 2))
        self.assertTrue(r["page_mieux_placee"].endswith("/blog/choisir-expert-comptable"))
        self.assertIn("cannibalisation", r["action"])
        self.assertEqual(r["ia_evolution"], "+openai -gemini")
        s = carto.synthese([r])
        self.assertEqual((s["en_hausse"], len(s["prompts_gagnes"]), len(s["prompts_perdus"])), (1, 1, 1))

    def test_export_notion(self):
        ligne = {**{c: "" for c in carto.COLONNES}, "url": SITE + "/blog/tva", "statut": "a-creer", "type": "lead-magnet",
                 "mot_cle_principal": "tva", "prompt_principal": "P ?", "intention": "informationnel",
                 "a_valider": "prompt_principal"}
        n = carto.lignes_notion([ligne], {carto.cle_de(ligne): {"position_mc": "4.2", "ia_openai": "cite:2",
                                                                 "action_notion": "Optimiser → top 3"}})[0]
        self.assertEqual(list(n), carto.COLONNES_NOTION)
        self.assertEqual((n["Mot clé"], n["Statut"], n["Type"], n["Intention"], n["Slug"]),
                         ("tva", "À créer", "lead magnet", "Informationnel", "/blog/tva"))
        self.assertEqual((n["ChatGPT"], n["Canal"], n["À valider"], n["Dans inventaire"]),
                         ("cité (rang 2)", "SEO, GEO", "prompt", "No"))


class TestCartographieDeBoutEnBout(DossierIsole):
    """initialiser → édition humaine → initialiser → mensuel ×2 → rapport → exporter, sans réseau."""

    def preparer(self):
        self.ecrire("decupler-seo.config.yml", CONFIG)
        self.ecrire("aout.csv", export(AOUT))
        self.ecrire("septembre.csv", export(SEPTEMBRE))
        self.ecrire("rapports/calendrier-2026-09-01.md", CALENDRIER)
        self.ecrire("memoire/lexique.csv", "theme,valeur,motif\ncreation,3,cr[ée]+(ation|er)\ncomptable,2,comptable\n")

    def carto(self) -> list[dict]:
        with open(self.dossier / "memoire/cartographie.csv", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def test_parcours_complet(self):
        self.preparer()
        r = lancer("cartographie.py", "initialiser", "--csv", "septembre.csv", "--sans-sitemap", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        lignes = {l["url"].replace(SITE, "") or l["mot_cle_principal"]: l for l in self.carto()}
        creation = lignes["/creation-entreprise-lyon"]
        self.assertEqual(creation["mot_cle_principal"], "création entreprise lyon")   # la marque exclue
        self.assertEqual((creation["silo"], creation["priorite"], creation["funnel"]), ("creation", "P1", "TOFU"))
        self.assertEqual(creation["a_valider"], "mot_cle_principal;prompt_principal")
        self.assertEqual(lignes["/"]["mot_cle_principal"], "")                         # accueil : marque seule
        self.assertEqual(lignes["holding patrimoniale"]["statut"], "a-creer")
        self.assertNotIn("création entreprise lyon", [l["mot_cle_principal"] for l in self.carto()
                                                      if l["statut"] == "a-creer"])

        # Le client valide : prompt réécrit, drapeau retiré, colonne ajoutée à la main.
        texte = (self.dossier / "memoire/cartographie.csv").read_text(encoding="utf-8")
        texte = texte.replace(creation["prompt_principal"], PROMPT_HUMAIN)
        texte = texte.replace("mot_cle_principal;prompt_principal", "", 1)
        texte = texte.replace("notes\n", "notes,responsable\n", 1)
        (self.dossier / "memoire/cartographie.csv").write_text(texte, encoding="utf-8")
        r = lancer("cartographie.py", "initialiser", "--csv", "aout.csv", "--sans-sitemap", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        apres = {l["url"].replace(SITE, ""): l for l in self.carto() if l["url"]}
        self.assertEqual(apres["/creation-entreprise-lyon"]["prompt_principal"], PROMPT_HUMAIN)
        self.assertEqual(apres["/creation-entreprise-lyon"]["a_valider"], "")
        self.assertIn("responsable", self.carto()[0])

        prompt_ec = apres["/expert-comptable-lyon"]["prompt_principal"]
        self.ecrire("donnees/ia-2026-08.csv", releves([
            ("openai", PROMPT_HUMAIN, "True", 3, "True", "", "atlas-conseil.example"),
            ("gemini", PROMPT_HUMAIN, "False", 0, "False", "", "rival.example"),
            ("claude", PROMPT_HUMAIN, "True", 1, "True", "", "atlas-conseil.example"),
            ("openai", prompt_ec, "False", 0, "False", "Cabinet Horizon", "horizon.example")]))
        self.ecrire("donnees/ia-2026-09.csv", releves([
            ("openai", PROMPT_HUMAIN, "True", 2, "True", "", "atlas-conseil.example"),
            ("gemini", PROMPT_HUMAIN, "False", 0, "True", "", "rival.example"),
            ("claude", PROMPT_HUMAIN, "False", 0, "False", "", "rival.example"),
            ("openai", prompt_ec, "False", 0, "False", "Cabinet Horizon", "horizon.example"),
            ("gemini", prompt_ec, "False", 0, "False", "Cabinet Horizon", "horizon.example"),
            ("claude", prompt_ec, "False", 0, "False", "", "horizon.example")]))

        r = lancer("cartographie.py", "mensuel", "--mois", "2026-08", "--csv", "aout.csv", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = lancer("cartographie.py", "mensuel", "--mois", "2026-09", "--csv", "septembre.csv",
                   "--csv-precedent", "aout.csv", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        md = (self.dossier / "rapports/cartographie-2026-09.md").read_text(encoding="utf-8")
        self.assertIn("| Page | Mot-clé principal | Pos. M | Pos. M-1 | Δ | Clics (Δ) | Prompt principal", md)
        self.assertIn("| /creation-entreprise-lyon | création entreprise lyon | 4,2 | 7,9 | +3,7 | 40 (+18) |", md)
        self.assertIn("| ✓ 2 | nommé | ✗ |", md)
        self.assertIn("Perd 4,3 places", md)
        self.assertIn("gagné sur Gemini, perdu sur Claude", md)
        self.assertIn("Cabinet Horizon", md)
        self.assertIn("| *à créer* | holding patrimoniale |", md)
        self.assertTrue(md.rstrip().endswith("-->"))

        # La lecture rédigée survit à une relance ; l'historique ne double pas.
        (self.dossier / "rapports/cartographie-2026-09.md").write_text(
            md.replace("<!-- À rédiger", "Lecture de l'agent.\n<!-- À rédiger"), encoding="utf-8")
        lancer("cartographie.py", "mensuel", "--mois", "2026-09", "--csv", "septembre.csv",
               "--csv-precedent", "aout.csv", cwd=self.dossier)
        self.assertIn("Lecture de l'agent.", (self.dossier / "rapports/cartographie-2026-09.md").read_text(encoding="utf-8"))
        with open(self.dossier / "donnees/cartographie-historique.csv", encoding="utf-8") as f:
            mois = [l["mois"] for l in csv.DictReader(f)]
        self.assertEqual(mois.count("2026-09"), mois.count("2026-08"))
        donnees = json.loads((self.dossier / "rapports/cartographie-2026-09.json").read_text(encoding="utf-8"))
        self.assertEqual(donnees["synthese"]["prompts_presents"], 1)

        # rapport.py : la section et la clé JSON, sans toucher aux clés existantes.
        resume = rapport.cartographie(self.dossier, "2026-09")
        self.assertEqual(resume["hausses"][0]["mot_cle_principal"], "création entreprise lyon")
        self.assertEqual(resume["baisses"][0]["mot_cle_principal"], "tva auto entrepreneur")
        section = "\n".join(rapport.section_cartographie(resume))
        self.assertIn("## Cartographie : mots-clés et prompts principaux", section)
        self.assertIn("| baisse | atlas-conseil.example/blog/tva-auto-entrepreneur | tva auto entrepreneur | 8,1 → 12,4 | -4,3 |",
                      section)
        self.assertIsNone(rapport.cartographie(self.dossier, "2026-07"))

        r = lancer("cartographie.py", "exporter", "--notion-csv", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(self.dossier / "rapports/cartographie-notion.csv", encoding="utf-8-sig") as f:
            notion = list(csv.DictReader(f))
        ligne = next(l for l in notion if l["Slug"] == "/creation-entreprise-lyon")
        self.assertEqual((ligne["Position"], ligne["Évolution position"], ligne["ChatGPT"], ligne["Statut"]),
                         ("4.2", "3.7", "cité (rang 2)", "Existant"))

    def test_verifier_signale_la_cannibalisation(self):
        self.ecrire("decupler-seo.config.yml", CONFIG)
        self.ecrire("memoire/cartographie.csv", ",".join(carto.COLONNES) + "\n"
                    f"{SITE}/a,existante,article,,,tva,,Que faut-il savoir sur la tva ?,fr,,,,,,,,\n"
                    f"{SITE}/b,existante,article,,,tva,,Que faut-il savoir sur la tva ?,fr,,,,,,,,\n")
        r = lancer("cartographie.py", "verifier", cwd=self.dossier)
        self.assertEqual(r.returncode, 1)
        self.assertIn("cannibalisation", r.stdout)
        self.assertIn("un prompt, une page", r.stdout)


class TestRapportJson(unittest.TestCase):
    def test_cles_historiques_intactes(self):
        r = {"projet": "Atlas Conseil", "mois": "2026-09",
             "trafic": {"mois": {"clics": 1, "impressions": 2, "position_moyenne": 3.0}, "clics_variation_pct": None},
             "journal": {"modifications": 0, "gains": 0, "neutres": 0, "pertes": 0}, "a_valider": 0,
             "runs": {"veille_attendues": 30, "veille_trouvees": 0}, "cartographie": None}
        cles = list(rapport.json_standard(r))
        self.assertEqual(cles[:13], ["projet", "mois", "clics", "impressions", "position_moyenne", "clics_variation_pct",
                                     "modifications", "gains", "neutres", "pertes", "a_valider", "runs_attendus",
                                     "runs_trouves"])
        self.assertIn("cartographie", cles)
        self.assertEqual(rapport.section_cartographie(None), [])


if __name__ == "__main__":
    unittest.main()
