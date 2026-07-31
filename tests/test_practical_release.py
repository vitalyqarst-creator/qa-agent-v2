from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_case_agent.practical_release import build_practical_release


def _case(
    tc_id: str,
    *,
    title: str = "Проверка пункта меню",
    traceability: str = "`AS.1`; Table 1; PDF page 7; `ATOM-001`",
    status: str = "`confirmed`",
    extra: str = "",
) -> str:
    return f"""## {tc_id}
**Название:** {title}
**Тип:** Positive
**Приоритет:** High
**package_id:** `WP-01`
**Трассировка:** {traceability}
**Статус тест-кейса:** {status}

**Цель:** Проверить поведение.

**Предусловия:**
1. Открыть раздел.

**Тестовые данные:**
- Не требуются.

**Шаги:**
1. Нажать кнопку.

**Итоговый ожидаемый результат:** Открыт нужный раздел.

**Постусловия:**
- Не требуются.
{extra}
"""


class PracticalReleaseTests(unittest.TestCase):
    def _write_package(self, root: Path, files: dict[str, str]) -> Path:
        ft_root = root / "fts" / "Demo" / "Demo-v1"
        tc_dir = ft_root / "test-cases"
        tc_dir.mkdir(parents=True)
        for name, content in files.items():
            (tc_dir / name).write_text(content, encoding="utf-8")
        return ft_root

    def test_builds_combined_file_and_matrix_with_continuous_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            ft_root = self._write_package(
                Path(temporary),
                {
                    "9.2-card.md": "# 9.2 Карточка\n\n" + _case("TC-DEMO-002", traceability="`AS.2`; Table 2; `ATOM-002`"),
                    "9.1-menu.md": "# 9.1 Меню\n\n" + _case("TC-DEMO-001"),
                    "demo-summary.md": "# Summary\n\nNot a TC file.\n",
                },
            )

            result, findings = build_practical_release(
                ft_root,
                release_name="demo-all",
                source_files=[
                    Path("test-cases/9.1-menu.md"),
                    Path("test-cases/9.2-card.md"),
                ],
            )
            combined = Path(result.combined_file).read_text(encoding="utf-8")
            matrix = Path(result.coverage_matrix).read_text(encoding="utf-8")

        self.assertEqual("passed", result.status)
        self.assertEqual([], findings)
        self.assertEqual(2, result.test_case_count)
        self.assertIn("### TC-001 — TC-DEMO-001", combined)
        self.assertIn("### TC-002 — TC-DEMO-002", combined)
        self.assertNotIn("Summary", combined)
        self.assertIn("TC-DEMO-001", matrix)
        self.assertIn("AS.2", matrix)

    def test_release_gate_fails_on_future_ft_placeholder_and_internal_rationale(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            ft_root = self._write_package(
                Path(temporary),
                {
                    "9.1-menu.md": "# 9.1 Меню\n\n"
                    + _case(
                        "TC-DEMO-001",
                        extra="\n**Сценарное обоснование:** internal.\n\nКонкретная учетная запись будет определена в ФТ 11.\n",
                    ),
                },
            )

            result, findings = build_practical_release(ft_root, release_name="demo-all")

        self.assertEqual("failed", result.status)
        self.assertGreaterEqual(result.finding_counts["error"], 2)
        self.assertIn("release-agent-rationale-leak", {finding.finding_id for finding in findings})
        self.assertIn("release-future-ft-runtime-placeholder", {finding.finding_id for finding in findings})

    def test_release_gate_rejects_unknown_status_and_missing_traceability_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            ft_root = self._write_package(
                Path(temporary),
                {
                    "9.1-menu.md": "# 9.1 Меню\n\n"
                    + _case(
                        "TC-DEMO-001",
                        traceability="требование из источника",
                        status="`ready-for-review`",
                    ),
                },
            )

            result, findings = build_practical_release(ft_root, release_name="demo-all")

        self.assertEqual("failed", result.status)
        self.assertIn("release-test-case-invalid-status", {finding.finding_id for finding in findings})
        self.assertIn("release-test-case-unparseable-traceability", {finding.finding_id for finding in findings})


if __name__ == "__main__":
    unittest.main()
