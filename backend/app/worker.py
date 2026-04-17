from __future__ import annotations

import time

from .database import init_db


def main() -> None:
    init_db()
    print("SCNU Workbench worker ready. Queue integration is reserved for Celery/Redis jobs.")
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
