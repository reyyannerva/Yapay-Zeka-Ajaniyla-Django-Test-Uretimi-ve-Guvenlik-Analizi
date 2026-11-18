"""Taşındı — H4-01 / Issue #33 (revizyon 4).

Bu dosya H2-02 (#24) ve revizyon 3'te (commit 9a4324b) çalışmayan bir **tasarım referansı** olarak ORM
modellerini içeriyordu. H4-01 ile modeller çalışan uygulamaya taşınmıştır ve tek kanonik ORM kaynağı
artık şudur:

    backend/core/models/   (migration: backend/core/migrations/0001_initial.py)

İki ayrı model tanımının zamanla birbirinden ayrışmaması için içerik burada tutulmaz. Önceki referans
sürüm git geçmişinde erişilebilir:

    git show 2c5f509:docs/database/django_models.py

Revizyon 3 → 4 farkları: docs/database/schema_changes_h4_01.md
"""
