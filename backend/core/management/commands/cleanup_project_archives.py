"""Hiçbir projeye bağlı olmayan (öksüz) arşiv dosyalarını bulur ve isteğe bağlı siler — H4-03 / Issue #35.

Dosya deposu ile veritabanı birlikte atomik olmadığından, depo silme işleminin başarısız olduğu nadir
durumlarda öksüz dosya kalabilir (bkz. core/projects/services.py). Varsayılan çalışma yalnızca listeler.
"""
from django.core.management.base import BaseCommand

from core.models import Project


class Command(BaseCommand):
    help = "Projeye bağlı olmayan arşiv dosyalarını listeler; --delete ile siler."

    def add_arguments(self, parser):
        parser.add_argument("--delete", action="store_true", help="Öksüz dosyaları sil (varsayılan: yalnızca listele).")

    def handle(self, *args, **options):
        storage = Project._meta.get_field("source_archive").storage
        referenced = set(Project.objects.exclude(source_archive__isnull=True).values_list("source_archive", flat=True))
        orphans = []

        def walk(prefix):
            try:
                dirs, files = storage.listdir(prefix)
            except FileNotFoundError:
                return
            for d in dirs:
                walk(f"{prefix}/{d}" if prefix else d)
            for f in files:
                name = f"{prefix}/{f}" if prefix else f
                if name not in referenced:
                    orphans.append(name)

        walk("project_archives")
        for name in sorted(orphans):
            if options["delete"]:
                storage.delete(name)
                self.stdout.write(f"silindi: {name}")
            else:
                self.stdout.write(f"öksüz: {name}")
        self.stdout.write(self.style.SUCCESS(f"{len(orphans)} öksüz arşiv {'silindi' if options['delete'] else 'bulundu'}."))
