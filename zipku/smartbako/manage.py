#!/usr/bin/env python
"""Utilitas command-line Django untuk tugas administratif."""

import os
import sys
from pathlib import Path


def main():
    # Folder config/ boleh berada di folder ini atau satu tingkat di atasnya.
    lokasi = Path(__file__).resolve().parent
    for folder in (lokasi, lokasi.parent):
        if (folder / "config").is_dir() and str(folder) not in sys.path:
            sys.path.insert(0, str(folder))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django tidak ditemukan. Pastikan Django sudah terpasang dan "
            "virtual environment sudah diaktifkan."
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()