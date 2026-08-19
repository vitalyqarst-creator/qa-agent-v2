from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any


PROFILE_ID = "runtime-v1"
EXPECTED_SKILLS = {
    "ft-source-locator",
    "ft-scope-analyzer",
    "ft-test-case-writer",
    "ft-test-case-reviewer",
}
PROFILE_MARKERS = (
    "AGENTS.md",
    "scripts/validate_runtime_tree.py",
    "references/runtime",
    *tuple(f"skills/{name}/SKILL.md" for name in sorted(EXPECTED_SKILLS)),
)
STALE_TEXT_MARKERS = {
    "practical route v0.6": "ссылка на устаревший practical route",
    "ft-test-case-iteration": "ссылка на legacy skill",
    "ft-ui-automation-prep": "ссылка на skill вне runtime-v1",
    "references/agent/": "ссылка на legacy references",
    "references/qa/": "ссылка на legacy references",
    "test_case_agent/": "ссылка на удалённый runtime-слой",
    "codex_review_cycle_runner": "ссылка на legacy orchestration runner",
}
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
ROOT_PATH_RE = re.compile(
    r"(?<![\w./-])((?:references/runtime|skills/[a-z0-9-]+)/[a-zA-Z0-9_.\-/]+\.md)"
)


def configure_utf8_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only architecture audit for the lean QA runtime."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Root of the runtime-v1 repository (default: current directory).",
    )
    parser.add_argument("--profile", choices=("auto", PROFILE_ID), default="auto")
    parser.add_argument("--json", action="store_true", dest="json_only")
    parser.add_argument("--text", action="store_true", dest="text_only")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on", choices=("error", "warning"))
    parser.add_argument(
        "--with-tests",
        action="store_true",
        help="Also run tests.test_runtime_contract. Disabled by default for a fast audit.",
    )
    return parser.parse_args()


def relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return ""


def detect_profile(root: Path) -> tuple[str | None, list[str]]:
    missing = [marker for marker in PROFILE_MARKERS if not (root / marker).exists()]
    return (PROFILE_ID if not missing else None), missing


def add_check(
    checks: list[dict[str, Any]],
    check_id: str,
    status: str,
    details: str,
    paths: list[str] | None = None,
) -> None:
    checks.append(
        {"id": check_id, "status": status, "details": details, "paths": paths or []}
    )


def add_finding(
    findings: list[dict[str, Any]],
    finding_id: str,
    severity: str,
    category: str,
    title: str,
    details: str,
    *,
    evidence: list[str] | None = None,
    recommended_move: str,
    paths: list[str] | None = None,
) -> None:
    findings.append(
        {
            "id": finding_id,
            "severity": severity,
            "category": category,
            "title": title,
            "details": details,
            "evidence": evidence or [],
            "recommended_move": recommended_move,
            "paths": paths or [],
        }
    )


def load_runtime_tree_validator(root: Path):
    path = root / "scripts" / "validate_runtime_tree.py"
    spec = importlib.util.spec_from_file_location("runtime_v1_tree_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(root))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    if not callable(getattr(module, "validate", None)):
        raise RuntimeError("validate_runtime_tree.py does not expose validate(root)")
    return module.validate


def audit_runtime_tree(
    root: Path,
    checks: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> None:
    validator_path = root / "scripts" / "validate_runtime_tree.py"
    try:
        errors = list(load_runtime_tree_validator(root)(root))
    except Exception as exc:
        add_check(
            checks,
            "runtime-tree-validator",
            "fail",
            f"Не удалось запустить канонический validator: {exc}",
            [relative(validator_path, root)],
        )
        add_finding(
            findings,
            "runtime-tree-validator-unavailable",
            "error",
            "runtime-structure",
            "Канонический validator runtime-дерева не запускается",
            "Аудитор не подменяет встроенную проверку структуры.",
            evidence=[str(exc)],
            recommended_move="Исправить scripts/validate_runtime_tree.py и повторить аудит.",
            paths=[relative(validator_path, root)],
        )
        return

    status = "pass" if not errors else "fail"
    add_check(
        checks,
        "runtime-tree-validator",
        status,
        "Канонический runtime tree валиден."
        if not errors
        else f"Канонический validator вернул {len(errors)} ошибок.",
        [relative(validator_path, root)],
    )
    for index, error in enumerate(errors, 1):
        add_finding(
            findings,
            f"runtime-tree-{index:03d}",
            "error",
            "runtime-structure",
            "Нарушен контракт runtime-дерева",
            error,
            evidence=[error],
            recommended_move=(
                "Исправить runtime artifact или обоснованно изменить "
                "validate_runtime_tree.py."
            ),
            paths=[relative(validator_path, root)],
        )


def active_documents(root: Path) -> list[Path]:
    result = [root / "AGENTS.md"]
    result.extend(sorted(root.glob("skills/*/SKILL.md")))
    result.extend(sorted(root.glob("references/runtime/*.md")))
    return [path for path in result if path.is_file()]


def resolve_document_targets(path: Path, content: str, root: Path) -> set[Path]:
    targets: set[Path] = set()
    for raw_target in MARKDOWN_LINK_RE.findall(content):
        target = raw_target.strip().split("#", 1)[0]
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        resolved = (path.parent / target).resolve()
        if resolved.suffix.casefold() == ".md":
            targets.add(resolved)
    for target in ROOT_PATH_RE.findall(content):
        targets.add((root / target).resolve())
    return targets


def audit_reference_graph(
    root: Path,
    checks: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> dict[Path, set[Path]]:
    documents = active_documents(root)
    graph: dict[Path, set[Path]] = {}
    broken: list[tuple[Path, Path]] = []
    for path in documents:
        targets = resolve_document_targets(path, read_text(path), root)
        graph[path.resolve()] = targets
        broken.extend((path, target) for target in targets if not target.is_file())

    add_check(
        checks,
        "reference-links",
        "pass" if not broken else "fail",
        "Все локальные Markdown/reference links разрешаются."
        if not broken
        else f"Найдено {len(broken)} битых ссылок.",
        sorted({relative(source, root) for source, _ in broken}),
    )
    for index, (source, target) in enumerate(broken, 1):
        add_finding(
            findings,
            f"broken-reference-{index:03d}",
            "error",
            "references",
            "Битая ссылка в активной инструкции",
            f"{relative(source, root)} ссылается на {relative(target, root)}.",
            evidence=[relative(source, root), relative(target, root)],
            recommended_move="Исправить ссылку либо удалить недостижимую инструкцию.",
            paths=[relative(source, root)],
        )

    roots = [root / "AGENTS.md", *sorted(root.glob("skills/*/SKILL.md"))]
    queue = deque(path.resolve() for path in roots if path.is_file())
    reachable: set[Path] = set(queue)
    while queue:
        current = queue.popleft()
        for target in graph.get(current, set()):
            if target.is_file() and target not in reachable:
                reachable.add(target)
                queue.append(target)

    orphaned = [
        path
        for path in sorted(root.glob("references/runtime/*.md"))
        if path.resolve() not in reachable
    ]
    add_check(
        checks,
        "reference-reachability",
        "pass" if not orphaned else "warn",
        "Все runtime references достижимы из AGENTS.md или active skills."
        if not orphaned
        else f"Найдено {len(orphaned)} недостижимых runtime references.",
        [relative(path, root) for path in orphaned],
    )
    for path in orphaned:
        add_finding(
            findings,
            f"orphan-reference:{path.name}",
            "warning",
            "references",
            "Runtime reference недостижим из активных инструкций",
            "Файл не загружается AGENTS.md или active skill прямо/транзитивно.",
            recommended_move="Связать reference с consumer-ом или удалить устаревший файл.",
            paths=[relative(path, root)],
        )
    return graph


def audit_stale_markers(
    root: Path,
    checks: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> list[dict[str, str]]:
    stale_items: list[dict[str, str]] = []
    for path in active_documents(root):
        content = read_text(path).casefold()
        for marker, reason in STALE_TEXT_MARKERS.items():
            if marker.casefold() not in content:
                continue
            item = {
                "type": "legacy-marker",
                "path": relative(path, root),
                "marker": marker,
                "reason": reason,
            }
            stale_items.append(item)
            add_finding(
                findings,
                f"stale-marker:{relative(path, root)}:{marker}",
                "warning",
                "stale-items",
                "Устаревший маркер в активной инструкции",
                reason,
                evidence=[marker],
                recommended_move="Удалить legacy-ссылку или заменить её runtime-v1 контрактом.",
                paths=[relative(path, root)],
            )
    add_check(
        checks,
        "stale-instruction-markers",
        "pass" if not stale_items else "warn",
        "Legacy markers в активных инструкциях не найдены."
        if not stale_items
        else f"Найдено {len(stale_items)} legacy markers.",
        sorted({item["path"] for item in stale_items}),
    )
    return stale_items


def normalized_instruction_lines(path: Path) -> set[str]:
    result: set[str] = set()
    in_fence = False
    for raw in read_text(path).splitlines():
        line = raw.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line or line.startswith(("#", "|", "[")):
            continue
        line = re.sub(r"^(?:[-*+]\s+|\d+[.)]\s+)", "", line)
        normalized = re.sub(r"\s+", " ", line).casefold().strip()
        if len(normalized) >= 80 and "references/runtime/" not in normalized:
            result.add(normalized)
    return result


def build_duplication_map(root: Path) -> list[dict[str, Any]]:
    occurrences: dict[str, list[str]] = defaultdict(list)
    for path in active_documents(root):
        for line in normalized_instruction_lines(path):
            occurrences[line].append(relative(path, root))
    return [
        {
            "status": "possible",
            "text": line,
            "sources": sorted(paths),
            "note": "Точное нормализованное совпадение; нужна ручная оценка.",
        }
        for line, paths in sorted(occurrences.items())
        if len(paths) > 1
    ]


def instruction_contexts(root: Path, graph: dict[Path, set[Path]]) -> list[dict[str, Any]]:
    agents = (root / "AGENTS.md").resolve()
    rows: list[dict[str, Any]] = []
    for skill_path in sorted(root.glob("skills/*/SKILL.md")):
        queue = deque([skill_path.resolve()])
        included = {agents, skill_path.resolve()}
        while queue:
            current = queue.popleft()
            for target in graph.get(current, set()):
                try:
                    target.relative_to((root / "references" / "runtime").resolve())
                except ValueError:
                    continue
                if target.is_file() and target not in included:
                    included.add(target)
                    queue.append(target)
        files = sorted(relative(path, root) for path in included if path.is_file())
        total_bytes = sum((root / path).stat().st_size for path in files)
        rows.append(
            {
                "role": skill_path.parent.name,
                "files": files,
                "files_count": len(files),
                "total_bytes": total_bytes,
                "total_kib": round(total_bytes / 1024, 1),
                "measurement": "reachable-linked-upper-bound",
                "status": "info",
            }
        )
    return rows


def run_runtime_tests(
    root: Path,
    checks: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> None:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "tests.test_runtime_contract"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        check=False,
        env=env,
    )
    status = "pass" if completed.returncode == 0 else "fail"
    add_check(
        checks,
        "runtime-contract-tests",
        status,
        "tests.test_runtime_contract проходит."
        if status == "pass"
        else "tests.test_runtime_contract не проходит.",
        ["tests/test_runtime_contract.py"],
    )
    if status == "fail":
        evidence = (completed.stdout + "\n" + completed.stderr).strip()[-4000:]
        add_finding(
            findings,
            "runtime-contract-tests-failed",
            "error",
            "tests",
            "Контрактные runtime-тесты не проходят",
            "До публикации agent-layer нужно вернуть зелёный runtime contract.",
            evidence=[evidence],
            recommended_move="Исправить первую содержательную ошибку теста и повторить аудит.",
            paths=["tests/test_runtime_contract.py"],
        )


def unsupported_report(root: Path, requested_profile: str, missing: list[str]) -> dict[str, Any]:
    finding = {
        "id": "unsupported-architecture-profile",
        "severity": "error",
        "category": "profile",
        "title": "Целевой каталог не соответствует runtime-v1",
        "details": "Аудитор не применяет legacy-инварианты к неизвестной архитектуре.",
        "evidence": missing,
        "recommended_move": "Указать --root актуального runtime-v1 репозитория.",
        "paths": [],
    }
    return {
        "profile": {"requested": requested_profile, "resolved": None, "target_root": str(root)},
        "summary": {
            "valid": False,
            "skills_count": 0,
            "checks_count": 1,
            "findings_count": 1,
            "errors_count": 1,
            "warnings_count": 0,
            "info_count": 0,
        },
        "findings": [finding],
        "duplication_map": [],
        "stale_items": [],
        "instruction_contexts": [],
        "skipped_checks": [{"id": "runtime-audit", "reason": "unsupported architecture profile"}],
        "checks": [
            {
                "id": "profile-detection",
                "status": "fail",
                "details": "runtime-v1 profile markers are incomplete",
                "paths": missing,
            }
        ],
    }


def audit(root: Path, requested_profile: str, with_tests: bool) -> dict[str, Any]:
    detected, missing = detect_profile(root)
    if detected is None:
        return unsupported_report(root, requested_profile, missing)

    checks: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    skipped_checks: list[dict[str, str]] = []
    add_check(
        checks,
        "profile-detection",
        "pass",
        "Активирован профиль runtime-v1.",
        list(PROFILE_MARKERS),
    )

    actual_skills = {path.name for path in (root / "skills").iterdir() if path.is_dir()}
    skill_delta = sorted(actual_skills.symmetric_difference(EXPECTED_SKILLS))
    add_check(
        checks,
        "active-skills",
        "pass" if not skill_delta else "fail",
        "Активны ровно четыре runtime skill."
        if not skill_delta
        else "Набор active skills отличается от runtime-v1.",
        [f"skills/{name}" for name in skill_delta],
    )
    if skill_delta:
        add_finding(
            findings,
            "active-skill-set-drift",
            "error",
            "skills-structure",
            "Набор runtime skills изменён без изменения профиля",
            "Профиль runtime-v1 содержит locator, analyzer, writer и reviewer.",
            evidence=skill_delta,
            recommended_move="Вернуть канонический набор либо оформить новую версию профиля.",
            paths=[f"skills/{name}" for name in skill_delta],
        )

    audit_runtime_tree(root, checks, findings)
    graph = audit_reference_graph(root, checks, findings)
    stale_items = audit_stale_markers(root, checks, findings)
    duplication_map = build_duplication_map(root)
    contexts = instruction_contexts(root, graph)
    add_check(
        checks,
        "instruction-context-size",
        "info",
        (
            f"Замерена верхняя оценка {len(contexts)} объявленных runtime contexts "
            "без произвольного fail-threshold."
        ),
        [f"skills/{row['role']}/SKILL.md" for row in contexts],
    )
    add_check(
        checks,
        "exact-duplication-candidates",
        "info",
        (
            f"Найдено {len(duplication_map)} точных совпадений; они не считаются "
            "ошибками без ручной оценки."
        ),
    )

    if with_tests:
        run_runtime_tests(root, checks, findings)
    else:
        skipped_checks.append(
            {
                "id": "runtime-contract-tests",
                "reason": "не запрошен --with-tests; baseline audit остаётся быстрым",
            }
        )

    counts = defaultdict(int)
    for finding in findings:
        counts[finding["severity"]] += 1
    summary = {
        "valid": counts["error"] == 0,
        "skills_count": len(actual_skills),
        "checks_count": len(checks),
        "findings_count": len(findings),
        "errors_count": counts["error"],
        "warnings_count": counts["warning"],
        "info_count": counts["info"],
    }
    return {
        "profile": {
            "requested": requested_profile,
            "resolved": PROFILE_ID,
            "target_root": str(root),
        },
        "summary": summary,
        "findings": sorted(
            findings,
            key=lambda item: ({"error": 0, "warning": 1, "info": 2}[item["severity"]], item["id"]),
        ),
        "duplication_map": duplication_map,
        "stale_items": stale_items,
        "instruction_contexts": contexts,
        "skipped_checks": skipped_checks,
        "checks": checks,
    }


def text_report(report: dict[str, Any]) -> str:
    profile = report["profile"]
    summary = report["summary"]
    lines = [
        "Аудит архитектуры QA runtime",
        f"- профиль: {profile['resolved'] or 'не определён'}",
        f"- корень: {profile['target_root']}",
        f"- валиден: {'да' if summary['valid'] else 'нет'}",
        (
            f"- findings: {summary['findings_count']} "
            f"(errors: {summary['errors_count']}, warnings: {summary['warnings_count']})"
        ),
        f"- checks: {summary['checks_count']}",
    ]
    if report["findings"]:
        lines.append("- основные findings:")
        for finding in report["findings"][:10]:
            lines.append(f"  - [{finding['severity']}] {finding['id']}: {finding['title']}")
    else:
        lines.append("- findings: нет")
    if report.get("instruction_contexts"):
        lines.append("- верхняя оценка объявленных instruction contexts:")
        for row in report["instruction_contexts"]:
            lines.append(f"  - {row['role']}: {row['total_kib']} KiB ({row['files_count']} files)")
    if report.get("skipped_checks"):
        lines.append("- пропущенные проверки:")
        for item in report["skipped_checks"]:
            lines.append(f"  - {item['id']}: {item['reason']}")
    return "\n".join(lines)


def exit_code(report: dict[str, Any], fail_on: str | None) -> int:
    if fail_on == "error" and report["summary"]["errors_count"]:
        return 1
    if fail_on == "warning" and (
        report["summary"]["errors_count"] or report["summary"]["warnings_count"]
    ):
        return 1
    return 0


def main() -> int:
    configure_utf8_stdio()
    args = parse_args()
    root = args.root.resolve()
    report = audit(root, args.profile, args.with_tests)
    json_report = json.dumps(report, ensure_ascii=False, indent=2)
    rendered_text = text_report(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json_report + "\n", encoding="utf-8")
    emit_json = args.json_only or not (args.json_only or args.text_only)
    emit_text = args.text_only or not (args.json_only or args.text_only)
    if emit_text:
        print(rendered_text)
    if emit_text and emit_json:
        print()
    if emit_json:
        print(json_report)
    return exit_code(report, args.fail_on)


if __name__ == "__main__":
    raise SystemExit(main())
