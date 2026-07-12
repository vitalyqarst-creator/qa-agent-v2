from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REQ_SKILLS={
    "ft-source-locator",
    "ft-scope-analyzer",
    "ft-test-case-iteration",
    "ft-test-case-writer",
    "ft-test-case-reviewer",
    "ft-ui-automation-prep",
    "agent-architecture-auditor",
}
REQ_AGENT={"content-placement.md","skill-boundaries.md","duplication-policy.md","maintenance-checklist.md","audit-output-format.md","task-start-skill-routing-format.md","session-based-review-cycle-format.md","codex-sdk-orchestration-format.md"}
REQ_QA={
    "test-case-format.md",
    "coverage-checklist.md",
    "traceability-rules.md",
    "review-findings-format.md",
    "traceability-matrix-format.md",
    "ui-automation-prep-format.md",
}
STALE=("uv run ft-test-agent"," ft-test-agent "," list-sections ","skills/ft-test-case-writer/references","/output/")
SECTIONS=("## Входы","## Выходы","## Ограничения")
INSTRUCTION_CONTEXT_SCENARIOS=(
    "source_locator.discovery",
    "writer.initial_draft.simple",
    "writer.initial_draft.table",
    "writer.initial_draft.ui",
    "writer.initial_draft.numeric",
    "writer.initial_draft.integration",
    "writer.revision_from_findings",
    "writer.remediation.style",
    "writer.remediation.validator_failure",
    "writer.session_initial_draft",
    "writer.session_semantic_revision",
    "writer.session_format_revision",
    "reviewer.full_existing_cases",
    "reviewer.scope_gap_review",
    "reviewer.structure_preflight",
    "reviewer.semantic_traceability_test_design",
    "reviewer.structure_format_final",
    "reviewer.semantic_regression",
    "scope.manual",
    "scope.agent_proposed",
    "iteration.full_loop",
    "ui_automation_prep.signed_off",
    "architecture.audit",
    "sdk_orchestration.review_cycle",
)
TASK_ROUTING_RE=re.compile(r"<!--\s*task-start-skill-routing:v1\s*-->\s*```json\s*(.*?)\s*```",re.DOTALL)

def args_parser():
    p=argparse.ArgumentParser(description="Read-only audit for agent-layer architecture.")
    p.add_argument("--root",type=Path)
    p.add_argument("--json",action="store_true",dest="json_only")
    p.add_argument("--text",action="store_true",dest="text_only")
    p.add_argument("--output",type=Path)
    p.add_argument("--fail-on",choices=("error","warning"))
    return p.parse_args()

def root_default()->Path:
    return Path(__file__).resolve().parents[3]

def txt(path:Path)->str:
    try:return path.read_text(encoding="utf-8")
    except FileNotFoundError:return ""

def rel(path:Path,root:Path)->str:
    try:return path.relative_to(root).as_posix()
    except ValueError:return path.as_posix()

def add_check(checks,name,status,details,paths=None):
    checks.append({"name":name,"status":status,"details":details,"paths":paths or []})

def add_finding(findings,fid,severity,category,title,details,evidence=None,move="",paths=None):
    findings.append({"id":fid,"severity":severity,"category":category,"title":title,"details":details,"evidence":evidence or [],"recommended_move":move,"paths":paths or []})

def load_instruction_resolver(root:Path):
    script=root/"scripts"/"resolve_instruction_context.py"
    if not script.exists():
        return None
    spec=importlib.util.spec_from_file_location("resolve_instruction_context",script)
    if spec is None or spec.loader is None:
        return None
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module

def audit_instruction_budgets(root:Path,checks,findings):
    resolver=load_instruction_resolver(root)
    manifest=root/"references"/"agent"/"instruction-loading-manifest.md"
    if resolver is None or not manifest.exists():
        paths=[rel(p,root) for p in (root/"scripts"/"resolve_instruction_context.py",manifest)]
        add_check(checks,"instruction-context-resolver","warn","Instruction context resolver or manifest is missing.",paths)
        add_finding(
            findings,
            "instruction-context-resolver-missing",
            "warning",
            "scripts",
            "Instruction context resolver is not wired",
            "Architecture audit cannot measure instruction budgets without scripts/resolve_instruction_context.py and references/agent/instruction-loading-manifest.md.",
            paths,
            "Add the resolver and manifest, then rerun architecture audit.",
            paths,
        )
        return []
    try:
        data=resolver.load_manifest(root)
    except Exception as exc:
        add_check(checks,"instruction-loading-manifest","warn",f"Manifest could not be parsed: {exc}",[rel(manifest,root)])
        add_finding(
            findings,
            "instruction-loading-manifest-invalid",
            "warning",
            "references",
            "Instruction loading manifest is invalid",
            "The manifest must expose a parseable instruction-loading-manifest:v1 JSON block.",
            [str(exc)],
            "Fix references/agent/instruction-loading-manifest.md.",
            [rel(manifest,root)],
        )
        return []
    rows=[]
    for scenario_id in INSTRUCTION_CONTEXT_SCENARIOS:
        try:
            result=resolver.resolve_instruction_context(root=root,manifest=data,scenario_id=scenario_id)
        except Exception as exc:
            add_check(checks,f"instruction-budget:{scenario_id}","warn",f"Scenario could not be resolved: {exc}",[rel(manifest,root)])
            add_finding(
                findings,
                f"instruction-budget-unresolved:{scenario_id}",
                "warning",
                "references",
                f"Instruction scenario {scenario_id} cannot be resolved",
                "Every required instruction-loading scenario must resolve to existing files.",
                [str(exc)],
                "Fix the scenario entry in instruction-loading-manifest.md.",
                [rel(manifest,root)],
            )
            continue
        budget=result["budget"]
        status="pass" if budget["status"]=="pass" and not result["missing"] else "warn"
        add_check(
            checks,
            f"instruction-budget:{scenario_id}",
            status,
            f"{budget['total_kib']} KiB / {budget['limit_kib']} KiB, headroom {budget.get('headroom_kib')} KiB",
            [item["path"] for item in result["files"]],
        )
        rows.append({
            "scenario": scenario_id,
            "files_count": len(result["files"]),
            "total_kib": budget["total_kib"],
            "limit_kib": budget["limit_kib"],
            "headroom_kib": budget.get("headroom_kib"),
            "min_headroom_kib": budget.get("min_headroom_kib"),
            "status": status,
        })
        if status!="pass":
            evidence=[
                f"{budget['total_kib']} KiB / {budget['limit_kib']} KiB",
                f"headroom {budget.get('headroom_kib')} KiB / min {budget.get('min_headroom_kib')} KiB",
                f"budget_status={budget['status']}",
            ]
            evidence+=result["missing"]
            title = (
                f"Instruction budget near limit for {scenario_id}"
                if budget["status"] == "near_limit"
                else f"Instruction budget exceeded for {scenario_id}"
            )
            add_finding(
                findings,
                f"instruction-budget:{scenario_id}",
                "warning",
                "references",
                title,
                "The scenario's runtime instruction context exceeds the manifest budget, violates safety headroom, or references missing files.",
                evidence,
                "Tighten the manifest groups, move rarely used references to conditional/audit-only, or explicitly raise the limit with rationale.",
                [rel(manifest,root)],
            )
    add_check(checks,"instruction-loading-manifest-scenarios","pass" if len(rows)==len(INSTRUCTION_CONTEXT_SCENARIOS) else "warn","Required instruction-loading scenarios resolved.",[rel(manifest,root)])
    return rows

def load_task_start_routing(root:Path):
    path=root/"references"/"agent"/"task-start-skill-routing-format.md"
    content=txt(path)
    if not path.exists():
        raise FileNotFoundError(path)
    match=TASK_ROUTING_RE.search(content)
    if not match:
        raise ValueError("task-start-skill-routing:v1 JSON block not found")
    data=json.loads(match.group(1))
    if data.get("version")!=1:
        raise ValueError(f"Unsupported task-start routing version: {data.get('version')}")
    return data

def audit_task_start_routing(root:Path,checks,findings):
    routing_path=root/"references"/"agent"/"task-start-skill-routing-format.md"
    paths=[rel(routing_path,root)]
    try:
        data=load_task_start_routing(root)
    except Exception as exc:
        add_check(checks,"task-start-skill-routing","warn",f"Task-start routing contract could not be parsed: {exc}",paths)
        add_finding(
            findings,
            "task-start-skill-routing-invalid",
            "warning",
            "dispatch-map",
            "Task-start skill routing contract is invalid",
            "The architecture layer cannot verify preflight skill routing without a parseable task-start-skill-routing:v1 JSON block.",
            [str(exc)],
            "Fix references/agent/task-start-skill-routing-format.md.",
            paths,
        )
        return {"status":"warn","routes_count":0,"golden_examples_count":0}

    active_skills={p.name for p in (root/"skills").iterdir() if p.is_dir()} if (root/"skills").exists() else set()
    resolver=load_instruction_resolver(root)
    manifest_scenarios=set()
    if resolver is not None and (root/"references"/"agent"/"instruction-loading-manifest.md").exists():
        try:
            manifest=resolver.load_manifest(root)
            manifest_scenarios={item["id"] for item in manifest.get("scenarios",[])}
        except Exception:
            manifest_scenarios=set()

    routes=data.get("routes",[])
    examples=data.get("golden_examples",[])
    route_ids=[item.get("id") for item in routes]
    duplicate_route_ids=sorted([rid for rid,count in Counter(route_ids).items() if rid and count>1])
    route_by_id={item.get("id"):item for item in routes if item.get("id")}
    route_skills={skill for item in routes for skill in item.get("skill_chain",[])}
    route_scenarios={entry.get("scenario") for item in routes for entry in item.get("instruction_scenarios",[]) if entry.get("scenario")}

    errors=[]
    missing_skills=sorted(active_skills-route_skills)
    unknown_skills=sorted(route_skills-active_skills)
    missing_scenarios=sorted(manifest_scenarios-route_scenarios)
    unknown_scenarios=sorted(route_scenarios-manifest_scenarios)
    if duplicate_route_ids:errors.append(f"duplicate route ids: {', '.join(duplicate_route_ids)}")
    if missing_skills:errors.append(f"active skills without route: {', '.join(missing_skills)}")
    if unknown_skills:errors.append(f"route skills not active: {', '.join(unknown_skills)}")
    if missing_scenarios:errors.append(f"manifest scenarios without route: {', '.join(missing_scenarios)}")
    if unknown_scenarios:errors.append(f"route scenarios not in manifest: {', '.join(unknown_scenarios)}")

    for idx,example in enumerate(examples,1):
        route_id=example.get("expected_route_id")
        route=route_by_id.get(route_id)
        if route is None:
            errors.append(f"golden example {idx} references unknown route: {route_id}")
            continue
        expected_chain=example.get("expected_skill_chain",[])
        actual_chain=route.get("skill_chain",[])
        if expected_chain!=actual_chain:
            errors.append(f"golden example {idx} skill chain mismatch for {route_id}")
        expected_scenarios=example.get("expected_instruction_scenarios",[])
        actual_scenarios=[entry.get("scenario") for entry in route.get("instruction_scenarios",[])]
        if expected_scenarios!=actual_scenarios:
            errors.append(f"golden example {idx} scenario mismatch for {route_id}")

    status="pass" if not errors else "warn"
    add_check(
        checks,
        "task-start-skill-routing",
        status,
        f"{len(routes)} routes, {len(examples)} golden examples.",
        paths,
    )
    if errors:
        add_finding(
            findings,
            "task-start-skill-routing-drift",
            "warning",
            "dispatch-map",
            "Task-start skill routing is out of sync",
            "Every active skill and instruction-loading scenario should be reachable from the preflight routing map, and golden examples must match their routes.",
            errors,
            "Update task-start-skill-routing-format.md or instruction-loading-manifest.md so routing and scenarios agree.",
            paths,
        )
    return {"status":status,"routes_count":len(routes),"golden_examples_count":len(examples)}

def audit(root:Path):
    findings=[]; checks=[]; stale=[]
    instruction_budgets=audit_instruction_budgets(root,checks,findings)
    ap=root/"AGENTS.md"; ac=txt(ap); low=ac.lower(); steps=len(re.findall(r"(?m)^\d+\.\s",ac))
    if not ap.exists():
        add_check(checks,"agents-file","fail","AGENTS.md is missing.")
        add_finding(findings,"agents-file-missing","error","agents-policy","Missing AGENTS.md","The policy layer is missing.","Restore AGENTS.md as the single policy file.")
    else:
        bad=("## рабочий процесс" in low) or ("## workflow" in low) or steps>=3
        add_check(checks,"agents-procedural-workflow","fail" if bad else "pass","AGENTS.md workflow check.",[rel(ap,root)])
        if bad:
            add_finding(findings,"agents-procedural-workflow","error","agents-policy","AGENTS.md contains procedural workflow","Policy should stay thin and avoid step-by-step workflow.",[f"numbered_steps={steps}"],"Move workflow into the relevant skill and keep AGENTS.md policy-only.",[rel(ap,root)])
        miss=[s for s in sorted(REQ_SKILLS) if s not in ac]
        add_check(checks,"agents-routing","fail" if miss else "pass","AGENTS.md routing check.",[rel(ap,root)])
        if miss:
            add_finding(findings,"agents-missing-routing","error","agents-policy","AGENTS.md misses active skill routing","The routing section should mention every active skill.",miss,"Update AGENTS.md routing to cover all active skills.",[rel(ap,root)])
        if "не дублируй" not in low and "canonical" not in low:
            add_check(checks,"agents-dedup-policy","warn","AGENTS.md anti-duplication rule missing.",[rel(ap,root)])
            add_finding(findings,"agents-missing-dedup-rule","warning","agents-policy","AGENTS.md misses anti-duplication guidance","The policy layer should discourage duplication across AGENTS, skills and references.","Add a short anti-duplication rule and keep the detailed policy in references/agent/duplication-policy.md.",[rel(ap,root)])
        else:
            add_check(checks,"agents-dedup-policy","pass","AGENTS.md anti-duplication rule present.",[rel(ap,root)])

    sd=root/"skills"; skills=sorted([p for p in sd.iterdir() if p.is_dir()]) if sd.exists() else []
    add_check(checks,"skills-count","pass" if 4<=len(skills)<=7 else "warn",f"Detected {len(skills)} skill directories.",[rel(p,root) for p in skills])
    if not 4<=len(skills)<=7:
        add_finding(findings,"skills-count-out-of-range","warning","skills-structure","Skill count is outside the recommended range","Keep 4-7 active skills so the layer stays focused.",[f"skills_count={len(skills)}"],"Merge overlapping skills or split overloaded ones until the active set fits the 4-7 range.",[rel(sd,root)])
    for d in skills:
        sm=d/"SKILL.md"; oy=d/"agents"/"openai.yaml"; sp=rel(d,root)
        if not sm.exists() or not oy.exists():
            add_check(checks,f"skill-required:{d.name}","fail","Skill missing required files.",[sp])
            add_finding(findings,f"skill-missing-required-files:{d.name}","error","skills-structure",f"Skill {d.name} is missing required files","Every active skill must include SKILL.md and agents/openai.yaml.","Restore the missing files.",[sp])
            continue
        sc=txt(sm)
        miss_sec=[s for s in SECTIONS if s not in sc]
        add_check(checks,f"skill-sections:{d.name}","warn" if miss_sec else "pass","Skill section check.",[rel(sm,root)])
        if miss_sec:
            add_finding(findings,f"skill-missing-sections:{d.name}","warning","skill-content",f"Skill {d.name} misses canonical sections","Each skill should describe inputs, outputs and limitations.",miss_sec,"Add the missing sections to SKILL.md.",[rel(sm,root)])
        if "references/" not in sc:
            add_check(checks,f"skill-references:{d.name}","warn","Skill does not link to canonical references.",[rel(sm,root)])
            add_finding(findings,f"skill-missing-references:{d.name}","warning","skill-content",f"Skill {d.name} misses canonical references","Skills should point to shared references instead of embedding all rules locally.","Link the skill to references/agent or references/qa.",[rel(sm,root)])
        else:
            add_check(checks,f"skill-references:{d.name}","pass","Skill links to canonical references.",[rel(sm,root)])
        if d.name=="ft-test-case-writer":
            size=sm.stat().st_size
            limit=20*1024
            add_check(checks,"writer-skill-runtime-size","warn" if size>=limit else "pass",f"{round(size/1024,1)} KiB / 20.0 KiB",[rel(sm,root)])
            if size>=limit:
                add_finding(
                    findings,
                    "writer-skill-runtime-size",
                    "warning",
                    "skill-content",
                    "Writer skill is too large for runtime loading",
                    "The writer skill should stay a compact entrypoint; deep workflow belongs in writer workflow references.",
                    [f"{size} bytes"],
                    "Move procedural workflow back into references/agent/writer-*-workflow.md and keep SKILL.md below 20 KiB.",
                    [rel(sm,root)],
                )
        local_refs=d/"references"
        if local_refs.exists():
            rp=rel(local_refs,root); stale.append({"type":"skill-reference-dir","path":rp,"reason":"Prefer shared references/ unless the material is truly skill-local."})
            add_check(checks,f"skill-local-references:{d.name}","warn","Local references directory detected.",[rp])
            add_finding(findings,f"skill-local-references:{d.name}","warning","references",f"Skill {d.name} uses a local references directory","Shared governance and QA rules should live in references/.","Move shared material into references/agent or references/qa.",[rp])
        else:
            add_check(checks,f"skill-local-references:{d.name}","pass","No local references directory detected.",[sp])

    all_refs=[]
    for name,req in (("agent",REQ_AGENT),("qa",REQ_QA)):
        rd=root/"references"/name; got={p.name for p in rd.glob("*.md")} if rd.exists() else set(); all_refs+=list(rd.glob("*.md"))
        miss=sorted(req-got)
        add_check(checks,f"references:{name}","fail" if miss else "pass","Shared references check.",[rel(rd,root)])
        if miss:
            add_finding(findings,f"references-missing:{name}","error","references",f"Shared {name} references are incomplete","The shared knowledge layer is missing mandatory files.",miss,"Restore the missing canonical references under references/.",[rel(rd,root)])

    review_cycle_runner=root/"scripts"/"codex_review_cycle_runner.py"
    add_check(checks,"codex-review-cycle-runner","pass" if review_cycle_runner.exists() else "fail","Session-based review-cycle runner check.",[rel(review_cycle_runner,root)])
    if not review_cycle_runner.exists():
        add_finding(findings,"codex-review-cycle-runner-missing","error","scripts","Codex review-cycle runner is missing","The session-based review-cycle contract requires scripts/codex_review_cycle_runner.py for validation, dry-run orchestration and snapshots.","Create the runner or remove the SDK orchestration contract until it exists.",[rel(review_cycle_runner,root)])

    exec_runner=root/"scripts"/"codex_exec_review_cycle_runner.py"
    backend_dispatcher=root/"scripts"/"review_cycle_backend_dispatcher.py"
    readme=root/"README.md"
    readme_content=txt(readme).lower()
    exec_default_activated=(
        exec_runner.exists()
        and backend_dispatcher.exists()
        and "review_cycle_backend_dispatcher.py" in readme_content
        and "--backend auto" in readme_content
        and "--backend sdk" in readme_content
    )
    add_check(
        checks,
        "codex-exec-default-activation",
        "pass" if exec_default_activated else ("warn" if exec_runner.exists() else "fail"),
        "Verified exec backend dispatcher is the documented default."
        if exec_default_activated else "Exec backend default activation is incomplete.",
        [rel(exec_runner,root),rel(backend_dispatcher,root),rel(readme,root)],
    )
    if exec_runner.exists() and not exec_default_activated:
        add_finding(
            findings,
            "codex-exec-backend-not-default",
            "warning",
            "orchestration",
            "Codex exec exists but is not the default review-cycle backend",
            "The repository contains an exec runner, but the documented production route still selects the SDK runner by default.",
            ["Dispatcher file or explicit auto/SDK fallback documentation is missing."],
            "Add an explicit backend dispatcher and make exec the verified default, with SDK retained only as a declared fallback.",
            [rel(exec_runner,root),rel(backend_dispatcher,root),rel(review_cycle_runner,root),rel(readme,root)],
        )

    prepared_writer_profile=root/"references"/"agent"/"prepared-writer-runtime-profile.md"
    exec_content=txt(exec_runner)
    profile_content=txt(prepared_writer_profile).lower()
    structured_writer_default=(
        'DEFAULT_PREPARED_FAST_WRITER_MODE = "structured"' in exec_content
        and "runner alone atomically materializes" in profile_content
        and "zero-command budget" in profile_content
    )
    add_check(
        checks,
        "prepared-fast-structured-writer-default",
        "pass" if structured_writer_default else "warn",
        "Prepared-fast writer is read-only and runner-materialized by default."
        if structured_writer_default else "Prepared-fast structured writer activation is incomplete.",
        [rel(exec_runner,root),rel(prepared_writer_profile,root)],
    )
    if not structured_writer_default:
        add_finding(
            findings,
            "prepared-fast-structured-writer-not-default",
            "warning",
            "orchestration",
            "Prepared-fast writer still requires workspace interaction",
            "The simple-field-property route should return a structured draft from a read-only stage and let the runner materialize it.",
            ["Structured default constant, zero-command profile, or runner-owned materialization rule is missing."],
            "Restore the structured writer default or explicitly document and measure a replacement optimization.",
            [rel(exec_runner,root),rel(prepared_writer_profile,root)],
        )

    searchable=[txt(p) for p in [root/"AGENTS.md",root/"skills"/"README.md"] if p.exists()]
    searchable+=[txt(p) for p in [
        root/"references"/"agent"/"instruction-loading-manifest.md",
        root/"references"/"agent"/"instruction-contract-index.md",
        root/"references"/"agent"/"task-start-skill-routing-format.md",
    ] if p.exists()]
    searchable+=[txt(p) for p in root.glob("skills/*/SKILL.md")]
    searchable+=[txt(p) for p in root.glob("skills/*/scripts/*.py")]
    for rp in all_refs:
        r=rel(rp,root)
        if not any(rp.name in c or r in c for c in searchable):
            stale.append({"type":"orphan-reference","path":r,"reason":"No policy file, skill or script references this shared document."})
            add_check(checks,f"orphan-reference:{rp.name}","warn","Orphan shared reference detected.",[r])
            add_finding(findings,f"orphan-reference:{rp.name}","warning","references",f"Shared reference {rp.name} is orphaned","A canonical reference exists but is not linked from the active agent layer.","Either link the reference from the relevant skill or remove it from the shared layer.",[r])

    for sp in sorted(root.glob("skills/*/scripts/*.py")):
        r=rel(sp,root)
        if sp.name=="audit_agent_architecture.py":
            add_check(checks,f"script-stale-markers:{sp.name}","pass","Skipped self-scan to avoid matching the auditor pattern list.",[r])
            continue
        c=txt(sp); hits=[m for m in STALE if m in c];
        add_check(checks,f"script-stale-markers:{sp.name}","warn" if hits else "pass","Script stale marker check.",[r])
        if hits:
            stale.append({"type":"stale-script-marker","path":r,"reason":", ".join(hits)})
            add_finding(findings,f"script-stale-markers:{sp.stem}","warning","scripts",f"Script {sp.name} contains stale architecture markers","Helper scripts should not reference removed CLI flows or obsolete structure names.",hits,"Update the script to use the current skill names and Python API.",[r])

    sr=root/"skills"/"README.md"; src=txt(sr)
    if not sr.exists():
        add_check(checks,"skills-readme","fail","skills/README.md is missing.")
        add_finding(findings,"skills-readme-missing","error","dispatch-map","Skills dispatch map is missing","The active skills need a shared entry point that explains when to use each one.","Restore skills/README.md as the canonical dispatch map.",[rel(sr,root)])
    else:
        miss=[d.name for d in skills if f"`{d.name}`" not in src]
        add_check(checks,"skills-readme-entries","fail" if miss else "pass","skills/README.md listing check.",[rel(sr,root)])
        if miss:
            add_finding(findings,"skills-readme-missing-entries","error","dispatch-map","Skills dispatch map misses active skills","The dispatch map should enumerate every active skill.",miss,"Add the missing skills to skills/README.md.",[rel(sr,root)])
        if "script-first workflow" not in src or "audit_agent_architecture.py" not in src:
            add_check(checks,"skills-readme-auditor-flow","warn","Auditor script-first workflow missing from dispatch map.",[rel(sr,root)])
            add_finding(findings,"skills-readme-auditor-flow-missing","warning","dispatch-map","Dispatch map misses the auditor script-first workflow","The map should explain that agent-architecture-auditor starts with the helper script and then does manual interpretation.","Update skills/README.md to mention the auditor script-first workflow.",[rel(sr,root)])
        else:
            add_check(checks,"skills-readme-auditor-flow","pass","Dispatch map describes the auditor script-first workflow.",[rel(sr,root)])

    task_start_routing=audit_task_start_routing(root,checks,findings)

    docs={rel(p,root):txt(p).splitlines() for p in ([root/"AGENTS.md"]+sorted(root.glob("skills/*/SKILL.md"))) if p.exists()}
    dup=defaultdict(set)
    for name,lines in docs.items():
        for raw in lines:
            s=raw.strip()
            if len(s)<25 or "references/" in s or s.startswith("#") or s.startswith("```"):continue
            n=re.sub(r"\s+"," ",s.lower())
            if n.startswith(("- `","1. ","2. ","3. ")):n=n[3:].strip()
            if len(n)>=25:dup[n].add(name)
    dmap=[]
    for line,sources in sorted(dup.items()):
        if len(sources)<2:continue
        status="confirmed" if "AGENTS.md" in sources else "possible"
        dmap.append({"status":status,"line":line,"sources":sorted(sources),"canonical_target":"AGENTS.md" if status=="confirmed" else None})
        if status=="confirmed":
            add_finding(findings,f"confirmed-duplicate:{abs(hash(line))}","warning","duplication","Confirmed duplicate between AGENTS.md and skill docs","The same substantial instruction appears in AGENTS.md and at least one skill document.",sorted(sources),"Keep the policy statement in AGENTS.md and move procedural or domain detail into the relevant skill or shared reference.",sorted(sources))

    cnt=Counter(f["severity"] for f in findings)
    return {
        "summary":{"skills_count":len(skills),"findings_count":len(findings),"errors_count":cnt["error"],"warnings_count":cnt["warning"],"info_count":cnt["info"]},
        "findings":sorted(findings,key=lambda x:({"error":0,"warning":1,"info":2}[x["severity"]],x["id"])),
        "duplication_map":dmap,
        "stale_items":stale,
        "instruction_budgets":instruction_budgets,
        "task_start_routing":task_start_routing,
        "checks":checks,
    }

def text_report(report):
    s=report["summary"]
    lines=["Agent architecture audit summary",f"- skills: {s['skills_count']}",f"- findings: {s['findings_count']} (errors: {s['errors_count']}, warnings: {s['warnings_count']}, info: {s['info_count']})",f"- checks: {len(report['checks'])}"]
    if report["findings"]:
        lines.append("- top findings:")
        for f in report["findings"][:5]:lines.append(f"  - [{f['severity']}] {f['id']}: {f['title']}")
    else:lines.append("- top findings: none")
    if report.get("instruction_budgets"):
        lines.append("- instruction budgets:")
        for b in report["instruction_budgets"]:
            lines.append(f"  - [{b['status']}] {b['scenario']}: {b['total_kib']} KiB / {b['limit_kib']} KiB, headroom {b.get('headroom_kib')} KiB ({b['files_count']} files)")
    if report.get("task_start_routing"):
        r=report["task_start_routing"]
        lines.append(f"- task start routing: {r['status']} ({r['routes_count']} routes, {r['golden_examples_count']} golden examples)")
    if report["stale_items"]:lines.append(f"- stale items: {len(report['stale_items'])}")
    return "\n".join(lines)

def main():
    a=args_parser(); root=(a.root or root_default()).resolve(); report=audit(root)
    js=json.dumps(report,ensure_ascii=False,indent=2); tx=text_report(report)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(js+"\n",encoding="utf-8")
    emit_json=a.json_only or (not a.json_only and not a.text_only)
    emit_text=a.text_only or (not a.json_only and not a.text_only)
    if emit_text:print(tx)
    if emit_text and emit_json:print()
    if emit_json:print(js)
    s=report["summary"]
    if a.fail_on=="error" and s["errors_count"]>0:return 1
    if a.fail_on=="warning" and (s["errors_count"]>0 or s["warnings_count"]>0):return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
