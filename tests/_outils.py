"""Outils communs aux tests : dossiers isolés et exécution des scripts.

Chaque test tourne dans un dossier temporaire, avec un environnement vidé
des variables du dispositif : un .env ou un GSC_SA_JSON présent sur la
machine ne doit jamais changer le résultat d'un test.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPTS = RACINE / "scripts"
VARIABLES_DU_DISPOSITIF = ("SEO_", "GSC_", "GA4_", "WP_", "WEBFLOW_", "INDEXNOW_")


def environnement_propre(**extra: str) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith(VARIABLES_DU_DISPOSITIF)}
    env.update(extra)
    return env


def lancer(script: str, *args: str, cwd: Path, **env: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args], cwd=cwd,
                          env=environnement_propre(**env), capture_output=True, text=True, timeout=120)


class DossierIsole(unittest.TestCase):
    def setUp(self) -> None:
        self._tempo = tempfile.TemporaryDirectory(prefix="decupler-test-")
        self.dossier = Path(self._tempo.name)

    def tearDown(self) -> None:
        self._tempo.cleanup()

    def ecrire(self, chemin: str, contenu: str) -> Path:
        f = self.dossier / chemin
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(contenu, encoding="utf-8")
        return f
