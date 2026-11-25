"""PostgreSQL doğrulama yardımcısı — H5-03 / #41 uçtan uca testleri.

Gerçek geliştirme veritabanını Django ORM ile sorgular ve sonucu JSON olarak yazar. Parola, token veya
kişisel veri yazdırmaz. ``axes-expire`` ve ``blacklist-refresh`` yalnızca test kullanıcıları için,
sırasıyla 15 dakikalık kilidin dolmasını ve refresh token'ın sunucuda iptalini simüle eder.

    cd backend && python ../e2e/h5-03/db_probe.py project 12
"""
import json
import os
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from axes.models import AccessAttempt, AccessAttemptExpiration  # noqa: E402
from django.db import connection  # noqa: E402
from django.utils import timezone  # noqa: E402
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken  # noqa: E402

from core.models import AnalysisRun, Project, ReferenceRequirement  # noqa: E402

TEST_USER_PREFIX = "e2e_"


def _require_test_user(username: str) -> None:
    if not username.startswith(TEST_USER_PREFIX):
        raise SystemExit("Yalnızca e2e_ önekli test kullanıcıları değiştirilebilir.")


def main(argv: list[str]) -> dict:
    command, *args = argv
    if command == "backend":
        return {"vendor": connection.vendor, "engine": connection.settings_dict["ENGINE"],
                "server_version": connection.cursor().connection.info.server_version}
    if command == "project":
        project = Project.objects.filter(pk=int(args[0])).select_related("owner").first()
        if project is None:
            return {"exists": False}
        return {"exists": True, "id": project.pk, "name": project.name, "description": project.description,
                "owner": project.owner.username, "validation_status": project.validation_status,
                "analysis_runs": project.analysis_runs.count(),
                "reference_requirements": project.reference_requirements.count()}
    if command == "run":
        run = AnalysisRun.objects.filter(pk=int(args[0])).select_related("project__owner").first()
        if run is None:
            return {"exists": False}
        return {"exists": True, "id": run.pk, "status": run.status, "method": run.method, "project": run.project_id,
                "owner": run.project.owner.username,
                "snapshot_codes": [r.get("requirement_code") for r in run.requirements_snapshot]}
    if command == "requirements":
        rows = ReferenceRequirement.objects.filter(project_id=int(args[0])).order_by("requirement_code")
        return {"items": [{"id": r.pk, "code": r.requirement_code, "category": r.category, "source": r.source,
                           "method": r.http_method, "revision": r.revision, "is_active": r.is_active,
                           "specification": r.specification} for r in rows]}
    if command == "requirement-count":
        return {"count": ReferenceRequirement.objects.filter(requirement_code=args[0]).count()}
    if command == "axes-expire":
        _require_test_user(args[0])
        past = timezone.now() - timedelta(minutes=15, seconds=1)
        AccessAttempt.objects.filter(username=args[0]).update(attempt_time=past)
        n = AccessAttemptExpiration.objects.filter(access_attempt__username=args[0]).update(expires_at=past)
        return {"expired_locks": n}
    if command == "axes-state":
        attempt = AccessAttempt.objects.filter(username=args[0]).first()
        if attempt is None:
            return {"failures": 0, "locked_until": None}
        exp = getattr(attempt, "expiration", None)
        return {"failures": attempt.failures_since_start,
                "locked_until": exp.expires_at.isoformat() if exp else None}
    if command == "finish-run":
        # Analiz motoru bu sürümde çalışmadığından, testte bir analizin sonlanması simüle edilir
        # (yalnızca test kullanıcısının kaydı).
        run = AnalysisRun.objects.select_related("project__owner").get(pk=int(args[0]))
        _require_test_user(run.project.owner.username)
        AnalysisRun.objects.filter(pk=run.pk).update(status="CANCELLED", finished_at=timezone.now())
        return {"id": run.pk, "status": "CANCELLED"}
    if command == "blacklist-refresh":
        _require_test_user(args[0])
        tokens = OutstandingToken.objects.filter(user__username=args[0])
        created = sum(BlacklistedToken.objects.get_or_create(token=t)[1] for t in tokens)
        return {"blacklisted": created}
    raise SystemExit(f"Bilinmeyen komut: {command}")


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1:]), ensure_ascii=False, default=str))
