#!/usr/bin/env python
"""Kontrollü DRF hedef uygulaması için Django yönetim betiği (H3-01 / Issue #27)."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Django bulunamadı. Sanal ortamı etkinleştirip 'pip install -r requirements.txt' "
            "komutunu çalıştırın."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
