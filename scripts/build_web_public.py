from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = PROJECT_ROOT / "web"
WEB_DIST = WEB_ROOT / "dist"
PUBLIC_DIR = PROJECT_ROOT / "public"


def main() -> None:
    subprocess.run(["npm", "run", "build"], cwd=WEB_ROOT, check=True)

    if PUBLIC_DIR.exists():
        shutil.rmtree(PUBLIC_DIR)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    for item in WEB_DIST.iterdir():
        target = PUBLIC_DIR / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


if __name__ == "__main__":
    main()
