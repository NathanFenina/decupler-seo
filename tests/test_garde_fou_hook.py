"""Le hook garde-fou : il doit bloquer les écritures improvisées, et laisser passer le reste."""

import json
import subprocess
import unittest

from _outils import RACINE, DossierIsole, environnement_propre

HOOK = RACINE / "hooks" / "garde-fou.sh"


class TestHookGardeFou(DossierIsole):
    def appel(self, commande, **env):
        entree = json.dumps({"tool_name": "Bash", "tool_input": {"command": commande}})
        return subprocess.run(["bash", str(HOOK)], input=entree, cwd=self.dossier, capture_output=True, text=True,
                              env=environnement_propre(CLAUDE_PROJECT_DIR=str(self.dossier), **env), timeout=60)

    def setUp(self):
        super().setUp()
        self.ecrire("decupler-seo.config.yml", "mode: assisted\n")

    def test_lecture_passe(self):
        r = self.appel("curl -s https://exemple.com/wp-json/wp/v2/posts?per_page=5")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_lecture_robots_passe(self):
        r = self.appel("curl -s https://exemple.com/robots.txt 2>&1 | head")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_post_wordpress_methode_avant_url(self):
        # Régression : « curl -X POST https://…/wp-json » passait sans contrôle.
        r = self.appel('curl -X POST -u a:b https://exemple.com/wp-json/wp/v2/posts -d \'{"title":"x"}\'',
                       SEO_ALLOWED_DOMAINS="exemple.com")
        self.assertEqual(r.returncode, 2)
        self.assertIn("validation humaine", r.stderr)

    def test_post_wordpress_autorise_en_autonome(self):
        self.ecrire("decupler-seo.config.yml", "mode: autonomous\n")
        r = self.appel("curl --request PATCH https://exemple.com/wp-json/wp/v2/pages/3 --data title=x",
                       SEO_ALLOWED_DOMAINS="exemple.com")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_envoi_robots_par_ftp_bloque(self):
        r = self.appel("lftp -e 'put robots.txt' ftp://hote.example")
        self.assertEqual(r.returncode, 2)

    def test_commande_ordinaire_passe(self):
        r = self.appel("git status && python3 scripts/wp.py carte")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_entree_illisible_passe(self):
        r = subprocess.run(["bash", str(HOOK)], input="pas du json", cwd=self.dossier,
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
