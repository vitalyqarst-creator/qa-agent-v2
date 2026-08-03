from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.lean_production import (  # noqa: E402
    LeanProductionError,
    audit_handoff,
    build_timing_report,
    finish_phase,
    finish_run,
    load_run,
    reconcile_codex_turn,
    reconcile_external_elapsed,
    render_timing_markdown,
    start_phase,
    start_run,
    terminalize_run,
    transition_phase,
)


def _metrics(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LeanProductionError("phase metrics JSON must be an object")
    return payload


def _combined_metrics(
    path: str | None,
    stage_metric_paths: Sequence[Path] = (),
) -> dict[str, Any]:
    payload = _metrics(path)
    stages: list[dict[str, Any]] = []
    for stage_path in stage_metric_paths:
        stage = json.loads(stage_path.read_text(encoding="utf-8"))
        if not isinstance(stage, dict):
            raise LeanProductionError(f"stage metrics JSON must be an object: {stage_path}")
        stages.append(stage)
    if stages:
        existing = payload.get("stage_metrics")
        if existing is not None and not isinstance(existing, list):
            raise LeanProductionError("metrics stage_metrics must be an array")
        payload["stage_metrics"] = [*(existing or []), *stages]
    return payload


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(value, encoding="utf-8", newline="\n")
    temporary.replace(path)


def _has_exact_codex_reconciliation(payload: Mapping[str, Any]) -> bool:
    observation = payload.get("observation")
    if not isinstance(observation, Mapping):
        return False
    turn_id = observation.get("codex_turn_id")
    external_observations = observation.get("external_observations")
    if not isinstance(external_observations, list):
        return False
    return any(
        isinstance(item, Mapping)
        and item.get("source") == "codex-rollout-task-complete"
        and item.get("endpoint") == "task-complete"
        and item.get("turn_id") == turn_id
        and item.get("claim_full_user_wall") is True
        for item in external_observations
    )


def _write_timing_reports(
    payload: Mapping[str, Any],
    *,
    json_output: Path | None,
    markdown_output: Path | None,
) -> str:
    report = build_timing_report(payload)
    rendered_json = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if json_output:
        _write_text(json_output, rendered_json)
    if markdown_output:
        _write_text(markdown_output, render_timing_markdown(report))
    return rendered_json


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Measure workflow wall-clock in legacy SLO or observation-only mode."
    )
    sub = result.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start")
    start.add_argument("--output", type=Path, required=True)
    start.add_argument("--ft-slug", required=True)
    start.add_argument("--scope-slug", required=True)
    start.add_argument("--baseline-label")
    start.add_argument("--baseline-wall-ms", type=int)
    start.add_argument("--profile", default="lean-production")
    start.add_argument("--request-started-epoch-ms", type=int)
    start.add_argument("--measurement-mode", choices=("slo", "observational"), default="slo")
    start.add_argument("--request-start-source")
    start.add_argument("--request-start-precision-ms", type=int, default=1)
    start.add_argument("--codex-turn-id")
    start.add_argument("--end-anchor", default="workflow-terminal")
    start.add_argument("--initial-phase")

    phase_start = sub.add_parser("phase-start")
    phase_start.add_argument("--output", type=Path, required=True)
    phase_start.add_argument("--phase", required=True)
    phase_start.add_argument("--input-artifact-root", action="append", type=Path, default=[])

    phase_end = sub.add_parser("phase-end")
    phase_end.add_argument("--output", type=Path, required=True)
    phase_end.add_argument("--phase", required=True)
    phase_end.add_argument("--status", required=True)
    phase_end.add_argument("--metrics-json")
    phase_end.add_argument("--stage-metrics-json", action="append", type=Path, default=[])
    phase_end.add_argument("--input-artifact-root", action="append", type=Path, default=[])
    phase_end.add_argument("--output-artifact-root", action="append", type=Path, default=[])

    transition = sub.add_parser("transition")
    transition.add_argument("--output", type=Path, required=True)
    transition.add_argument("--phase", required=True)
    transition.add_argument("--status", required=True)
    transition.add_argument("--next-phase", required=True)
    transition.add_argument("--metrics-json")
    transition.add_argument("--stage-metrics-json", action="append", type=Path, default=[])
    transition.add_argument("--input-artifact-root", action="append", type=Path, default=[])
    transition.add_argument("--output-artifact-root", action="append", type=Path, default=[])
    transition.add_argument(
        "--next-input-artifact-root", action="append", type=Path, default=[]
    )

    finish = sub.add_parser("finish")
    finish.add_argument("--output", type=Path, required=True)
    finish.add_argument("--status", required=True)
    finish.add_argument("--test-case-count", type=int, required=True)
    finish.add_argument("--artifact-root", action="append", type=Path, default=[])
    finish.add_argument("--active-phase")
    finish.add_argument("--phase-status", default="completed")
    finish.add_argument("--phase-metrics-json")
    finish.add_argument("--stage-metrics-json", action="append", type=Path, default=[])
    finish.add_argument(
        "--phase-input-artifact-root", action="append", type=Path, default=[]
    )
    finish.add_argument(
        "--phase-output-artifact-root", action="append", type=Path, default=[]
    )
    finish.add_argument(
        "--compact",
        action="store_true",
        help="Print only the terminal timing summary; the complete record remains in --output.",
    )

    terminal = sub.add_parser("terminalize")
    terminal.add_argument("--output", type=Path, required=True)
    terminal.add_argument("--status", required=True)
    terminal.add_argument("--error-type", required=True)
    terminal.add_argument("--error", required=True)
    terminal.add_argument("--test-case-count", type=int, default=0)
    terminal.add_argument("--artifact-root", action="append", type=Path, default=[])
    terminal.add_argument(
        "--finished-epoch-ms",
        type=int,
        help=(
            "Exact historical terminal boundary for recovery after an external "
            "root-turn failure. Omit during an active turn."
        ),
    )

    audit = sub.add_parser("audit-handoff")
    audit.add_argument("--handoff", type=Path, required=True)
    audit.add_argument("--fail", action="store_true")

    report = sub.add_parser("report")
    report.add_argument("--output", type=Path, required=True)
    report.add_argument("--json-output", type=Path)
    report.add_argument("--markdown-output", type=Path)

    reconcile_ui = sub.add_parser("reconcile-ui")
    reconcile_ui.add_argument("--output", type=Path, required=True)
    reconcile_ui.add_argument("--elapsed-ms", type=int, required=True)
    reconcile_ui.add_argument("--source", default="codex-ui-display")
    reconcile_ui.add_argument("--endpoint", default="ui-final")
    reconcile_ui.add_argument("--precision-ms", type=int, default=1000)
    reconcile_ui.add_argument("--turn-id")
    reconcile_ui.add_argument("--note")
    reconcile_ui.add_argument(
        "--claim-full-user-wall",
        action="store_true",
        help="Explicitly accept this UI-final observation as the full user wall.",
    )

    reconcile_codex = sub.add_parser("reconcile-codex-turn")
    reconcile_codex.add_argument("--output", type=Path, required=True)
    reconcile_codex.add_argument(
        "--sessions-root", type=Path, default=Path.home() / ".codex" / "sessions"
    )
    reconcile_codex.add_argument("--turn-id")

    reconcile_report = sub.add_parser("reconcile-report")
    reconcile_report.add_argument("--output", type=Path, required=True)
    reconcile_report.add_argument(
        "--sessions-root", type=Path, default=Path.home() / ".codex" / "sessions"
    )
    reconcile_report.add_argument("--json-output", type=Path)
    reconcile_report.add_argument("--markdown-output", type=Path)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "start":
            payload = start_run(
                args.output,
                ft_slug=args.ft_slug,
                scope_slug=args.scope_slug,
                baseline_label=args.baseline_label,
                baseline_wall_ms=args.baseline_wall_ms,
                profile=args.profile,
                request_started_epoch_ms=args.request_started_epoch_ms,
                measurement_mode=args.measurement_mode,
                request_start_source=args.request_start_source,
                request_start_precision_ms=args.request_start_precision_ms,
                codex_turn_id=args.codex_turn_id,
                end_anchor=args.end_anchor,
                initial_phase=args.initial_phase,
            )
        elif args.command == "phase-start":
            payload = start_phase(
                args.output,
                phase=args.phase,
                input_artifact_roots=args.input_artifact_root,
            )
        elif args.command == "phase-end":
            payload = finish_phase(
                args.output,
                phase=args.phase,
                status=args.status,
                metrics=_combined_metrics(args.metrics_json, args.stage_metrics_json),
                input_artifact_roots=args.input_artifact_root,
                output_artifact_roots=args.output_artifact_root,
            )
        elif args.command == "transition":
            payload = transition_phase(
                args.output,
                phase=args.phase,
                status=args.status,
                next_phase=args.next_phase,
                metrics=_combined_metrics(args.metrics_json, args.stage_metrics_json),
                input_artifact_roots=args.input_artifact_root,
                output_artifact_roots=args.output_artifact_root,
                next_input_artifact_roots=args.next_input_artifact_root,
            )
        elif args.command == "finish":
            payload = finish_run(
                args.output,
                status=args.status,
                test_case_count=args.test_case_count,
                artifact_roots=args.artifact_root,
                active_phase=args.active_phase,
                phase_status=args.phase_status,
                phase_metrics=_combined_metrics(
                    args.phase_metrics_json, args.stage_metrics_json
                ),
                phase_input_artifact_roots=args.phase_input_artifact_root,
                phase_output_artifact_roots=args.phase_output_artifact_root,
            )
        elif args.command == "terminalize":
            payload = terminalize_run(
                args.output,
                status=args.status,
                error_type=args.error_type,
                error=args.error,
                test_case_count=args.test_case_count,
                artifact_roots=args.artifact_root,
                finished_epoch_ms=args.finished_epoch_ms,
            )
        elif args.command == "audit-handoff":
            payload = audit_handoff(args.handoff)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 2 if args.fail and payload["status"] != "pass" else 0
        elif args.command == "report":
            payload = build_timing_report(load_run(args.output))
            rendered_json = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
            if args.json_output:
                _write_text(args.json_output, rendered_json)
            if args.markdown_output:
                _write_text(args.markdown_output, render_timing_markdown(payload))
            print(rendered_json, end="")
            return 0
        elif args.command == "reconcile-report":
            current = load_run(args.output)
            if _has_exact_codex_reconciliation(current):
                payload = current
            else:
                try:
                    payload = reconcile_codex_turn(
                        args.output,
                        sessions_root=args.sessions_root,
                    )
                except LeanProductionError as exc:
                    if not str(exc).startswith(
                        "Codex task_complete is not available for turn "
                    ):
                        raise
                    observation = current.get("observation")
                    turn_id = (
                        observation.get("codex_turn_id")
                        if isinstance(observation, Mapping)
                        else None
                    )
                    pending = {
                        "schema_version": 1,
                        "status": "pending-task-complete",
                        "turn_id": turn_id,
                        "timer": str(args.output.resolve()),
                        "full_user_wall_ms": current.get("full_user_wall_ms"),
                        "timer_mutated": False,
                        "reports_written": False,
                    }
                    print(json.dumps(pending, ensure_ascii=False, indent=2))
                    return 3
            print(
                _write_timing_reports(
                    payload,
                    json_output=args.json_output,
                    markdown_output=args.markdown_output,
                ),
                end="",
            )
            return 0
        elif args.command == "reconcile-ui":
            payload = reconcile_external_elapsed(
                args.output,
                elapsed_ms=args.elapsed_ms,
                source=args.source,
                endpoint=args.endpoint,
                precision_ms=args.precision_ms,
                turn_id=args.turn_id,
                note=args.note,
                claim_full_user_wall=args.claim_full_user_wall,
            )
        else:
            payload = reconcile_codex_turn(
                args.output,
                sessions_root=args.sessions_root,
                turn_id=args.turn_id,
            )
        printable = payload
        if args.command == "finish" and args.compact:
            printable = {
                "status": payload.get("status"),
                "observed_window_ms": payload.get("observed_window_ms"),
                "full_user_wall_ms": payload.get("full_user_wall_ms"),
                "slo_status": payload.get("slo_status"),
                "test_case_count": payload.get("test_case_count"),
                "timer": str(args.output.resolve()),
            }
        print(json.dumps(printable, ensure_ascii=False, indent=2))
        return 0
    except (LeanProductionError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
