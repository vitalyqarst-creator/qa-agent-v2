from __future__ import annotations

import locale
import os
import platform
import shutil
import sys


CYRILLIC_PROBE = "Проверка кириллицы: Карточка заявки, Код требования, Заёмщик"


def _presence(name: str) -> str:
    return "set" if os.environ.get(name) else "unset"


def _shell_hint() -> str:
    shell = os.environ.get("SHELL", "")
    comspec = os.environ.get("COMSPEC", "")
    ps_module_path = os.environ.get("PSModulePath", "")

    if ps_module_path:
        return "powershell-likely"
    if shell:
        shell_name = os.path.basename(shell).lower()
        if "bash" in shell_name or "zsh" in shell_name or "sh" == shell_name:
            return "bash-or-posix-likely"
        return "posix-shell-likely"
    if comspec:
        return "cmd-or-windows-shell-likely"
    return "unknown"


def _safe_path(value: str | None) -> str:
    if not value:
        return "none"
    return value.replace("\n", " ").replace("\r", " ")


def main() -> int:
    preferred_encoding = locale.getencoding() if hasattr(locale, "getencoding") else locale.getpreferredencoding(False)
    lines = [
        f"platform_system={platform.system()}",
        f"platform_release={platform.release()}",
        f"platform_version={platform.version()}",
        f"os_name={os.name}",
        f"python_version={platform.python_version()}",
        f"python_executable={_safe_path(sys.executable)}",
        f"stdout_encoding={sys.stdout.encoding or 'unknown'}",
        f"stderr_encoding={sys.stderr.encoding or 'unknown'}",
        f"preferred_locale_encoding={preferred_encoding or 'unknown'}",
        f"filesystem_encoding={sys.getfilesystemencoding() or 'unknown'}",
        f"env_SHELL={_presence('SHELL')}",
        f"env_SHELL_value={_safe_path(os.environ.get('SHELL'))}",
        f"env_COMSPEC={_presence('COMSPEC')}",
        f"env_COMSPEC_value={_safe_path(os.environ.get('COMSPEC'))}",
        f"env_PSModulePath={_presence('PSModulePath')}",
        f"detected_shell_hint={_shell_hint()}",
        f"python_on_path={_safe_path(shutil.which('python'))}",
        f"py_on_path={_safe_path(shutil.which('py'))}",
        f"cyrillic_probe={CYRILLIC_PROBE}",
        "cyrillic_probe_status=printed",
    ]
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
