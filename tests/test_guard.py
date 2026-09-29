"""Le garde-fou : c'est lui qui empêche le mode autonome de faire des dégâts."""

import json
import unittest

from _outils import DossierIsole, lancer

AUTORISE, VALIDATION, BLOQUE = 0, 1, 2


class TestGardeFou(DossierIsole):
    def verdict(self, action, cible="https://exemple.com/page", *extra, **env):
        r = lancer("guard.py", "--action", action, "--cible", cible, *extra, cwd=self.dossier, **env)
        return r.returncode, json.loads(r.stdout)

    def test_autonome_domaine_autorise(self):
        self.ecrire("decupler-seo.config.yml", "mode: autonomous\n")
        code, _ = self.verdict("publier", SEO_ALLOWED_DOMAINS="exemple.com")
        self.assertEqual(code, AUTORISE)

    def test_sans_domaine_declare_tout_est_bloque(self):
        self.ecrire("decupler-seo.config.yml", "mode: autonomous\n")
        code, d = self.verdict("publier")
        self.assertEqual(code, BLOQUE)
        self.assertIn("Aucun domaine", d["explication"])

    def test_domaine_hors_liste_bloque(self):
        self.ecrire("decupler-seo.config.yml", "mode: autonomous\n")
        code, _ = self.verdict("publier", "https://autre.com/x", SEO_ALLOWED_DOMAINS="exemple.com")
        self.assertEqual(code, BLOQUE)

    def test_www_est_equivalent(self):
        self.ecrire("decupler-seo.config.yml", "mode: autonomous\n")
        code, _ = self.verdict("publier", "https://www.exemple.com/x", SEO_ALLOWED_DOMAINS="exemple.com")
        self.assertEqual(code, AUTORISE)

    def test_kill_switch_par_variable(self):
        self.ecrire("decupler-seo.config.yml", "mode: autonomous\n")
        for valeur in ("1", "true", "oui", "YES"):
            code, _ = self.verdict("publier", SEO_ALLOWED_DOMAINS="exemple.com", SEO_SAFE_MODE=valeur)
            self.assertEqual(code, BLOQUE, f"SEO_SAFE_MODE={valeur}")

    def test_kill_switch_dans_le_env_du_projet(self):
        # Régression : le .env du projet n'était pas lu, ce kill-switch ne faisait rien.
        self.ecrire("decupler-seo.config.yml", "mode: autonomous\n")
        self.ecrire(".env", "SEO_SAFE_MODE=1\nSEO_ALLOWED_DOMAINS=exemple.com\n")
        code, _ = self.verdict("publier")
        self.assertEqual(code, BLOQUE)

    def test_flag_safe(self):
        self.ecrire("decupler-seo.config.yml", "mode: autonomous\n")
        code, _ = self.verdict("publier", "https://exemple.com/x", "--safe", SEO_ALLOWED_DOMAINS="exemple.com")
        self.assertEqual(code, BLOQUE)

    def test_mode_assisted_demande_validation(self):
        self.ecrire("decupler-seo.config.yml", "mode: assisted\n")
        code, _ = self.verdict("publier", SEO_ALLOWED_DOMAINS="exemple.com")
        self.assertEqual(code, VALIDATION)

    def test_mode_inconnu_repli_sur_safe(self):
        self.ecrire("decupler-seo.config.yml", "mode: turbo\n")
        code, _ = self.verdict("publier", SEO_ALLOWED_DOMAINS="exemple.com")
        self.assertEqual(code, BLOQUE)

    def test_suppression_toujours_interdite(self):
        self.ecrire("decupler-seo.config.yml", "mode: autonomous\n")
        code, _ = self.verdict("supprimer-contenu", SEO_ALLOWED_DOMAINS="exemple.com")
        self.assertEqual(code, BLOQUE)

    def test_communaute_et_email_toujours_valides_par_un_humain(self):
        self.ecrire("decupler-seo.config.yml", "mode: autonomous\n")
        for action in ("poster-communaute", "envoyer-email"):
            code, _ = self.verdict(action, SEO_ALLOWED_DOMAINS="exemple.com")
            self.assertEqual(code, VALIDATION, action)

    def test_seuils_de_pages_programmatiques(self):
        self.ecrire("decupler-seo.config.yml", "mode: autonomous\n")
        attendus = {"50": AUTORISE, "150": VALIDATION, "800": BLOQUE}
        for volume, attendu in attendus.items():
            code, _ = self.verdict("generer-pages", "https://exemple.com/", "--volume", volume,
                                   SEO_ALLOWED_DOMAINS="exemple.com")
            self.assertEqual(code, attendu, f"{volume} pages")

    def test_chaque_projet_a_sa_config(self):
        self.ecrire("client-a/decupler-seo.config.yml", "mode: safe\n")
        self.ecrire("client-b/decupler-seo.config.yml", "mode: autonomous\n")
        for client, attendu in (("client-a", "safe"), ("client-b", "autonomous")):
            r = lancer("guard.py", "--statut", cwd=self.dossier / client)
            self.assertEqual(json.loads(r.stdout)["mode"], attendu)


if __name__ == "__main__":
    unittest.main()
