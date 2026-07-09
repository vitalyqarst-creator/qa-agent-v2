from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class ProbeEnvironmentTest(unittest.TestCase):
    def test_probe_environment_reports_runtime_and_cyrillic_probe(self) -> None:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        result = subprocess.run(
            [sys.executable, str(ROOT_DIR / "scripts" / "probe_environment.py")],
            cwd=ROOT_DIR,
            env=env,
            check=True,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        output = result.stdout
        self.assertIn("platform_system=", output)
        self.assertIn("python_version=", output)
        self.assertIn("stdout_encoding=", output)
        self.assertIn("stderr_encoding=", output)
        self.assertIn("preferred_locale_encoding=", output)
        self.assertIn("detected_shell_hint=", output)
        self.assertIn("cyrillic_probe=Проверка кириллицы: Карточка заявки, Код требования, Заёмщик", output)


if __name__ == "__main__":
    unittest.main()
