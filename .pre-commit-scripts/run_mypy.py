#!/usr/bin/env python3
import subprocess
import sys
import os
from pathlib import Path

def check_services():
    services_dir = Path("services")
    failed = False


    for service_dir in services_dir.iterdir():
        if not service_dir.is_dir():
            continue

        src_dir = service_dir / "src"
        if src_dir.exists() and (service_dir / "pyproject.toml").exists():
            print(f"Checking {service_dir}")

            original_dir = os.getcwd()
            os.chdir(service_dir)

            try:
                result = subprocess.run(
                    [
                        "mypy",
                        "src/",
                        "--ignore-missing-imports",
                        "--follow-imports=silent",
                        "--disable-error-code=call-overload"
                    ],
                    capture_output=True,
                    text=True
                )

                if result.stdout:
                    print(result.stdout, end='')
                if result.stderr:
                    print(result.stderr, file=sys.stderr, end='')

                if result.returncode != 0:
                    failed = True
            finally:
                os.chdir(original_dir)

    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(check_services())
