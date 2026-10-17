"""Deploy the demo to a Hugging Face Space (Docker).

    uv run --with huggingface_hub python scripts/deploy_space.py            # private
    uv run --with huggingface_hub python scripts/deploy_space.py --public   # needs user OK

Creates the Space if needed, sets secrets from .env (never committed, never printed),
and uploads only what the container needs. Going public is a separate, explicit flag
(docs/PRINCIPLES.md: confirm before publishing anything public).
"""

from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[1]
SECRETS = [
    "TOOL_SECRET",
    "DEMO_ACCESS_CODE",
    "ELEVENLABS_WEBHOOK_SECRET",
    "ELEVENLABS_INBOUND_AGENT_ID",
]
INCLUDE = [
    "pyproject.toml",
    "uv.lock",
    "Dockerfile",
    "voiceops.toml",
    "slotback",
    "db",
    "evidence",
    "metrics",
]


def main() -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser()
    parser.add_argument("--space", default=None, help="owner/name (default: <you>/slotback)")
    parser.add_argument("--public", action="store_true")
    parser.add_argument(
        "--static",
        action="store_true",
        help="deploy dist/site (scripts/export_static.py) as a free static Space",
    )
    args = parser.parse_args()
    if args.static:
        return deploy_static(args)
    api = HfApi()
    owner = api.whoami()["name"]
    repo = args.space or f"{owner}/slotback"
    api.create_repo(
        repo, repo_type="space", space_sdk="docker", private=not args.public, exist_ok=True
    )
    api.update_repo_settings(repo, repo_type="space", private=not args.public)
    for name in SECRETS:
        value = os.environ.get(name)
        if value:
            api.add_space_secret(repo, name, value)
    with tempfile.TemporaryDirectory() as tmp:
        for item in INCLUDE:
            src = ROOT / item
            dst = Path(tmp) / item
            if src.is_dir():
                shutil.copytree(
                    src,
                    dst,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests", ".pytest_cache"),
                )
            else:
                shutil.copy2(src, dst)
        shutil.copy2(ROOT / "deploy" / "SPACE_README.md", Path(tmp) / "README.md")
        api.upload_folder(
            folder_path=tmp,
            repo_id=repo,
            repo_type="space",
            commit_message="Deploy Slotback demo",
            delete_patterns=["*"],
        )
    host = repo.replace("/", "-").lower().replace("_", "-")
    print(f"deployed {repo} ({'public' if args.public else 'private'})")
    print(f"url: https://{host}.hf.space")


STATIC_README = """---
title: Slotback
emoji: 📅
colorFrom: gray
colorTo: blue
sdk: static
pinned: false
short_description: Freed slots, back to the waiting list in order
---
"""


def deploy_static(args) -> None:
    site = ROOT / "dist" / "site"
    if not (site / "index.html").exists():
        raise SystemExit("run scripts/export_static.py first")
    api = HfApi()
    repo = args.space or f"{api.whoami()['name']}/slotback"
    api.create_repo(
        repo, repo_type="space", space_sdk="static", private=not args.public, exist_ok=True
    )
    api.update_repo_settings(repo, repo_type="space", private=not args.public)
    (site / "README.md").write_text(STATIC_README)
    api.upload_folder(
        folder_path=str(site),
        repo_id=repo,
        repo_type="space",
        commit_message="Deploy Slotback static showcase",
        delete_patterns=["*"],
    )
    host = repo.replace("/", "-").lower().replace("_", "-")
    print(f"deployed {repo} (static, {'public' if args.public else 'private'})")
    print(f"url: https://{host}.static.hf.space  ·  page: https://huggingface.co/spaces/{repo}")


if __name__ == "__main__":
    main()
