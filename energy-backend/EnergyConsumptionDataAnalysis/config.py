"""Load repository environment settings, including legacy PowerShell-style lines."""

from io import StringIO
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]


def load_project_env():
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return
    normalized = []
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.lstrip()
        if stripped.startswith("$env:"):
            indent = line[: len(line) - len(stripped)]
            line = indent + stripped[5:]
        normalized.append(line)
    load_dotenv(stream=StringIO("\n".join(normalized)), override=False)


load_project_env()
