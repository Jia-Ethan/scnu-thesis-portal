from __future__ import annotations

import os
import shutil
from pathlib import Path


TEST_ROOT = Path(__file__).resolve().parents[1] / "tmp" / "test-workbench"

if TEST_ROOT.exists():
    shutil.rmtree(TEST_ROOT)
TEST_ROOT.mkdir(parents=True, exist_ok=True)

os.environ["SCNU_DATABASE_URL"] = f"sqlite:///{TEST_ROOT / 'workbench.db'}"
os.environ["SCNU_STORAGE_DIR"] = str(TEST_ROOT / "storage")
