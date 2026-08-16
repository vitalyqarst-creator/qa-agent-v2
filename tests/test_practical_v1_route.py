from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ROUTE_PATH = ROOT_DIR / "references" / "agent" / "practical-test-case-route-v1.md"
CLARIFICATION_FORMAT_PATH = (
    ROOT_DIR / "references" / "agent" / "practical-v1-clarification-requests-format.md"
)
SCOPE_SKILL_PATH = ROOT_DIR / "skills" / "ft-scope-analyzer" / "SKILL.md"
WRITER_SKILL_PATH = ROOT_DIR / "skills" / "ft-test-case-writer" / "SKILL.md"
REVIEWER_SKILL_PATH = ROOT_DIR / "skills" / "ft-test-case-reviewer" / "SKILL.md"


class PracticalV1RouteTests(unittest.TestCase):
    def test_default_route_preserves_design_before_test_case_order(self) -> None:
        content = ROUTE_PATH.read_text(encoding="utf-8")
        self.assertIn("source scope → matrix → independent matrix review", content)
        self.assertIn("Только после `matrix-accepted` writer создаёт тест-кейсы", content)
        self.assertIn("Отдельная верхнеуровневая Codex-сессия", content)

    def test_default_route_has_bounded_reviews_without_controller_artifacts(self) -> None:
        content = ROUTE_PATH.read_text(encoding="utf-8")
        self.assertIn("один раз исправляет", content)
        self.assertIn("один `micro-closure`", content)
        self.assertIn("не меняющая покрываемое поведение", content)
        self.assertIn("`review-failed`", content)
        self.assertIn("Не создавай `workflow-state`, immutable manifest, attestation", content)

    def test_default_route_keeps_nonblocking_execution_limits_visible(self) -> None:
        content = ROUTE_PATH.read_text(encoding="utf-8")
        self.assertIn("`scope-clarification-requests.md`", content)
        self.assertIn("`needs-test-data`", content)
        self.assertIn("`candidate-ui-calibration`", content)
        self.assertIn("`blocked-observability`", content)

    def test_v1_ba_question_file_is_a_self_service_document(self) -> None:
        content = CLARIFICATION_FORMAT_PATH.read_text(encoding="utf-8")
        self.assertIn("**Статус:** `open`", content)
        self.assertIn("**Ответ БА:**", content)
        self.assertIn("**Решение для тест-дизайна:**", content)
        self.assertIn("сохраняет текст **«Ответ БА»** дословно", content)
        self.assertNotIn("Источник и дата ответа", content)

    def test_v1_route_requires_code_partition_and_lifecycle_closure(self) -> None:
        content = ROUTE_PATH.read_text(encoding="utf-8")
        self.assertIn("граница и соседний недопустимый класс", content)
        self.assertIn("для ограничения уникальности", content)
        self.assertIn("entry-state:", content)
        self.assertIn("редактирование и повторное открытие", content)
        self.assertIn("коды требований из `source-scope.md`", content)

    def test_route_requires_global_rules_and_local_preflight(self) -> None:
        content = ROUTE_PATH.read_text(encoding="utf-8")
        self.assertIn("глобальные правила типа данных", content)
        self.assertIn("корректная test-строка данных не нарушает другое применимое", content)
        self.assertIn("параметризованной строки явно записано", content)

    def test_phase_skills_keep_targeted_preflight_and_reviewer_scope(self) -> None:
        scope_skill = SCOPE_SKILL_PATH.read_text(encoding="utf-8")
        writer_skill = WRITER_SKILL_PATH.read_text(encoding="utf-8")
        reviewer_skill = REVIEWER_SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("глобальные правила типов данных", scope_skill)
        self.assertIn("полноту зависимых обязательных данных", writer_skill)
        self.assertIn("одно действие, одну реакцию", writer_skill)
        self.assertIn("не перечитывай весь пакет без cross-reference", reviewer_skill)
        self.assertIn("не ищи другие Codex-задачи", reviewer_skill)
        self.assertIn("micro-closure", reviewer_skill)
        self.assertIn("Решение для тест-дизайна", reviewer_skill)
        self.assertNotIn("list_threads", reviewer_skill)


if __name__ == "__main__":
    unittest.main()
