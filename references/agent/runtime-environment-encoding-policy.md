# Runtime Environment and Encoding Policy

This reference is the canonical shell/UTF-8 safety policy for agent work. `AGENTS.md` keeps the mandatory short rule; this file keeps the operational details and acceptance criteria.

## Mandatory Preflight Probe

Before running commands that read, search, extract, transform or write Russian FT/source/test-case content, determine the execution environment. Use `python scripts/probe_environment.py` when Python is available, or record an equivalent manual probe when Python is not available.

The probe must identify:

- OS/platform;
- active shell hint: PowerShell, Bash/POSIX, `cmd`, or unknown;
- Python executable and version, if available;
- stdout/stderr encoding, preferred locale encoding and filesystem encoding;
- environment signs such as `SHELL`, `COMSPEC`, `PSModulePath`;
- whether a Cyrillic probe string prints without obvious mojibake.

Do not assume Bash because examples use heredoc. Do not assume PowerShell because the repository is on Windows. Pick the command strategy only after the probe or an already-current saved probe result.

## Command Strategy

For PowerShell:

- set UTF-8 console and Python environment before Cyrillic-sensitive commands:

```powershell
chcp 65001 > $null
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
```

- do not use Bash heredoc forms such as `python <<'PY'`;
- for multiline logic, create or reuse a UTF-8 `.py` helper file and run it with Python;
- read/write text files with explicit UTF-8, for example `Get-Content -Encoding UTF8` or `Path.read_text(encoding="utf-8")`.

For Bash/POSIX:

- heredoc is allowed only after the shell is confirmed as Bash/POSIX;
- set UTF-8 environment for Cyrillic-sensitive work:

```bash
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
```

For `cmd` or unknown shell:

- avoid shell-specific syntax;
- prefer short ASCII-only commands;
- for complex logic or Cyrillic-sensitive reads/searches/writes, create or reuse a UTF-8 `.py` helper file.

## Cyrillic Source Handling

Do not pass Russian search strings through risky inline command strings when shell encoding is not proven safe. Use UTF-8 scripts, existing helpers, normalized XHTML/source files, or file-based search inputs.

Requirement codes, row numbers and stable IDs such as BSR/DIT/GSR may anchor navigation and traceability, but they do not replace verification of the Russian requirement text. If Russian content cannot be read safely, stop the semantic step and record a technical fallback or `blocked-input`; do not infer behavior from codes alone.

## Artifact Boundary

Technical runtime details are diagnostic artifacts, not test-case content. Keep shell, heredoc, stdout/stderr encoding, mojibake and extractor debug details in session logs, debug artifacts or work folders.

Production test-case files under `fts/**/test-cases/*.md` and `fts/**/test-cases/automation-ready/*.md` must not contain:

- PowerShell/Bash/heredoc troubleshooting notes;
- stdout/stderr encoding dumps;
- mojibake samples;
- extractor debug logs;
- command-line workaround narratives that are not part of the executable test case.

## Source-Prep and Workflow Entry Points

Any source-prep workflow or script that opens Russian DOCX/PDF/XHTML/Markdown sources should run the environment probe first or require a saved probe result from the same runtime. If the probe reports unsafe output encoding, the workflow must use explicit UTF-8 file/script reads and must not use distorted console output as evidence.

## Acceptance Criteria

A change that touches source extraction, instruction loading, writer/reviewer workflows, artifact generation, or shell command examples passes this policy only when:

- the preflight probe path is documented or executed;
- PowerShell examples do not use Bash heredoc;
- Bash examples set UTF-8 environment before Cyrillic-sensitive work;
- unknown-shell guidance avoids shell-specific syntax;
- Cyrillic analysis relies on UTF-8 file/helper reads, not mojibake stdout;
- requirement codes are used only as anchors and Russian text remains verified;
- production test-case files stay free of runtime/debug encoding details;
- at least one local check runs `scripts/probe_environment.py` or a test that covers it.
