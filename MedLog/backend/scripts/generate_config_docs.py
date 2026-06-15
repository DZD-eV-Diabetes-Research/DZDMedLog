#!/usr/bin/env python3
"""Generate docs/configuration.md from medlogserver Config using psyplus.

Run from the repo root via:
    ./build_config_docs.sh
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Silence psyplus warnings about nested models without env_nested_delimiter —
# Config uses '__' as delimiter, which psyplus resolves at runtime per-field.
os.environ.setdefault("PSYPLUS_SUPPRESS_ENV_WARNING", "true")

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
REPO_ROOT = BACKEND_DIR.parent.parent
OUTPUT_FILE = REPO_ROOT / "docs" / "configuration.md"

# Make medlogserver importable without a package install
sys.path.insert(0, str(BACKEND_DIR))

try:
    from psyplus import YamlSettingsPlus
except ImportError:
    print("psyplus not found. Install it with: pip install psyplus")
    sys.exit(1)

from medlogserver.config import Config

PREAMBLE = """\
# Configuration Reference

> [!NOTE]
> This file is auto-generated from [`MedLog/backend/medlogserver/config.py`](../MedLog/backend/medlogserver/config.py).
> Run `./build_config_docs.sh` from the repo root to regenerate it.

All settings are supplied via **environment variables** or a `.env` file placed at
`MedLog/backend/medlogserver/.env`. Nested settings use `__` as the delimiter
(e.g. `AUTH_OIDC_PROVIDERS__0__ENABLED`).

---

"""


def main() -> None:
    raw = YamlSettingsPlus(Config).render_markdown()

    # psyplus prepends its own H1 + description + hr — strip those and use
    # our own preamble so the file fits the project docs style.
    lines = raw.splitlines(keepends=True)
    content_start = next(
        (i for i, ln in enumerate(lines) if ln.startswith("## ")),
        0,
    )
    body = "".join(lines[content_start:])

    # Config field defaults can contain absolute paths built at import time
    # (e.g. FRONTEND_FILES_DIR, DRUG_TABLE_PROVISIONING_SOURCE_DIR).  Replace
    # any occurrence of the repo-root prefix so the docs stay machine-agnostic.
    body = body.replace(str(REPO_ROOT) + "/", "")

    OUTPUT_FILE.write_text(PREAMBLE + body)
    rel = OUTPUT_FILE.relative_to(REPO_ROOT)
    print(f"Written: {rel}  ({len((PREAMBLE + body).splitlines())} lines)")


if __name__ == "__main__":
    main()
