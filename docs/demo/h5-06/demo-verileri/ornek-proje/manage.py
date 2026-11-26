#!/usr/bin/env python
"""Örnek Django projesi yönetim betiği (H5-06 demo verisi — güvenli, gerçek sır içermez)."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "magaza_projesi.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
