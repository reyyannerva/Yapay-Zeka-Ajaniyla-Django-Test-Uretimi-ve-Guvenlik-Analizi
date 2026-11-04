"""
Reference Django ORM models — H2-02 / Issue #24.

This module is the ORM form of docs/database/database_schema.sql. It is a design
reference and is not imported by the running application. When the models are
moved into an application's models.py, the schema must be created with
`makemigrations` / `migrate`, not with the reference SQL.

Requires Django 5.1+ (CheckConstraint uses `condition=`) and PostgreSQL.
User accounts come from settings.AUTH_USER_MODEL (django.contrib.auth by default).
No model stores passwords, JWT tokens, LLM API keys or other secrets.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q

SHA256_HEX_REGEX = r"^[0-9a-f]{64}$"


class Project(models.Model):
    class SourceType(models.TextChoices):
        ARCHIVE = "ARCHIVE", "Uploaded archive"
        REPOSITORY = "REPOSITORY", "Repository URL"

    class ValidationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        VALID = "VALID", "Valid"
        INVALID = "INVALID", "Invalid"

    id = models.BigAutoField(primary_key=True)
    # Indexed through uq_projects_owner_name (owner_id is its leading column).
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
        db_index=False,
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, default="")
    source_type = models.CharField(
        max_length=20, choices=SourceType.choices, default=SourceType.ARCHIVE
    )
    # Storage-relative key; the absolute location is resolved by the storage backend.
    source_archive = models.FileField(
        upload_to="project_archives/%Y/%m/", max_length=255, blank=True, default=""
    )
    source_repository_url = models.URLField(max_length=500, blank=True, default="")
    archive_sha256 = models.CharField(max_length=64, blank=True, default="")
    validation_status = models.CharField(
        max_length=20,
        choices=ValidationStatus.choices,
        default=ValidationStatus.PENDING,
    )
    validation_report = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"], name="uq_projects_owner_name"
            ),
            models.CheckConstraint(
                condition=~Q(name=""), name="ck_projects_name_not_blank"
            ),
            models.CheckConstraint(
                condition=Q(source_type__in=["ARCHIVE", "REPOSITORY"]),
                name="ck_projects_source_type_valid",
            ),
            models.CheckConstraint(
                condition=Q(validation_status__in=["PENDING", "VALID", "INVALID"]),
                name="ck_projects_validation_status_valid",
            ),
            models.CheckConstraint(
                condition=~Q(source_type="ARCHIVE") | ~Q(source_archive=""),
                name="ck_projects_archive_source_present",
            ),
            models.CheckConstraint(
                condition=~Q(source_type="REPOSITORY") | ~Q(source_repository_url=""),
                name="ck_projects_repository_source_present",
            ),
            models.CheckConstraint(
                condition=~Q(source_archive__startswith="/")
                & ~Q(source_archive__contains=".."),
                name="ck_projects_source_archive_relative",
            ),
            models.CheckConstraint(
                condition=Q(archive_sha256="") | Q(archive_sha256__regex=SHA256_HEX_REGEX),
                name="ck_projects_archive_sha256_format",
            ),
        ]

    def __str__(self):
        return self.name


class ReferenceRequirement(models.Model):
    """Expected behaviour defined independently of what AST analysis observes."""

    class Category(models.TextChoices):
        AUTHENTICATION = "AUTHENTICATION", "Authentication"
        AUTHORIZATION = "AUTHORIZATION", "Authorization"
        INPUT_VALIDATION = "INPUT_VALIDATION", "Input validation"
        HTTP_BEHAVIOR = "HTTP_BEHAVIOR", "HTTP behavior"
        SECURITY_CONFIGURATION = "SECURITY_CONFIGURATION", "Security configuration"

    id = models.BigAutoField(primary_key=True)
    # Indexed through uq_reference_requirements_project_code.
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="reference_requirements",
        db_index=False,
    )
    requirement_code = models.CharField(max_length=50)
    category = models.CharField(max_length=30, choices=Category.choices)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    expected_result = models.TextField()
    specification = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    # Incremented by the application whenever expected behaviour changes.
    revision = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reference_requirements"
        ordering = ["requirement_code"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "requirement_code"],
                name="uq_reference_requirements_project_code",
            ),
            models.CheckConstraint(
                condition=Q(requirement_code__regex=r"^[A-Za-z0-9][A-Za-z0-9._-]*$"),
                name="ck_reference_requirements_code_format",
            ),
            models.CheckConstraint(
                condition=Q(
                    category__in=[
                        "AUTHENTICATION",
                        "AUTHORIZATION",
                        "INPUT_VALIDATION",
                        "HTTP_BEHAVIOR",
                        "SECURITY_CONFIGURATION",
                    ]
                ),
                name="ck_reference_requirements_category_valid",
            ),
            models.CheckConstraint(
                condition=~Q(title=""),
                name="ck_reference_requirements_title_not_blank",
            ),
            models.CheckConstraint(
                condition=~Q(expected_result=""),
                name="ck_reference_requirements_expected_result_not_blank",
            ),
            models.CheckConstraint(
                condition=Q(revision__gte=1),
                name="ck_reference_requirements_revision_positive",
            ),
        ]

    def __str__(self):
        return f"{self.requirement_code} (r{self.revision})"


class AnalysisRun(models.Model):
    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        ANALYZING = "ANALYZING", "Analyzing"
        GENERATING = "GENERATING", "Generating tests"
        EXECUTING = "EXECUTING", "Executing tests"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    ACTIVE_STATUSES = ["QUEUED", "ANALYZING", "GENERATING", "EXECUTING"]
    TERMINAL_STATUSES = ["COMPLETED", "FAILED"]

    id = models.BigAutoField(primary_key=True)
    # Indexed through ix_analysisrun_project_created.
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="analysis_runs",
        db_index=False,
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.QUEUED
    )
    # NULL until the task is dispatched to Celery; unique when present.
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    requirements_snapshot = models.JSONField(default=list, blank=True)
    ast_results = models.JSONField(default=dict, blank=True)
    processing_metadata = models.JSONField(default=dict, blank=True)
    error_code = models.CharField(max_length=50, blank=True, default="")
    error_message = models.CharField(max_length=2000, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analysis_runs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["project", "-created_at"],
                name="ix_analysisrun_project_created",
            ),
            models.Index(
                fields=["status", "created_at"],
                name="ix_analysisrun_status_created",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["celery_task_id"], name="uq_analysis_runs_celery_task_id"
            ),
            models.UniqueConstraint(
                fields=["project"],
                condition=Q(status__in=["QUEUED", "ANALYZING", "GENERATING", "EXECUTING"]),
                name="uq_analysis_runs_one_active_per_project",
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "QUEUED",
                        "ANALYZING",
                        "GENERATING",
                        "EXECUTING",
                        "COMPLETED",
                        "FAILED",
                    ]
                ),
                name="ck_analysis_runs_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(retry_count__gte=0),
                name="ck_analysis_runs_retry_count_non_negative",
            ),
            models.CheckConstraint(
                condition=~Q(status="QUEUED") | Q(started_at__isnull=True),
                name="ck_analysis_runs_queued_not_started",
            ),
            models.CheckConstraint(
                condition=~Q(
                    status__in=["ANALYZING", "GENERATING", "EXECUTING", "COMPLETED"]
                )
                | Q(started_at__isnull=False),
                name="ck_analysis_runs_progress_requires_start",
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=["COMPLETED", "FAILED"], finished_at__isnull=False
                )
                | (
                    ~Q(status__in=["COMPLETED", "FAILED"])
                    & Q(finished_at__isnull=True)
                ),
                name="ck_analysis_runs_finished_iff_terminal",
            ),
            models.CheckConstraint(
                condition=Q(started_at__isnull=True)
                | Q(finished_at__isnull=True)
                | Q(finished_at__gte=models.F("started_at")),
                name="ck_analysis_runs_time_order",
            ),
            models.CheckConstraint(
                condition=~Q(status="FAILED") | ~Q(error_code=""),
                name="ck_analysis_runs_failure_has_error_code",
            ),
        ]

    def __str__(self):
        return f"AnalysisRun #{self.pk} ({self.status})"


class GeneratedTest(models.Model):
    class GenerationMethod(models.TextChoices):
        RULE_BASED = "RULE_BASED", "Rule-based"
        LLM = "LLM", "LLM"
        HYBRID = "HYBRID", "Hybrid"

    class ValidationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        VALID = "VALID", "Valid"
        INVALID_SYNTAX = "INVALID_SYNTAX", "Invalid syntax"
        REJECTED_POLICY = "REJECTED_POLICY", "Rejected by policy"

    id = models.BigAutoField(primary_key=True)
    # Indexed through uq_generated_tests_run_module_name.
    analysis_run = models.ForeignKey(
        AnalysisRun,
        on_delete=models.CASCADE,
        related_name="generated_tests",
        db_index=False,
    )
    test_module = models.CharField(max_length=150)
    test_name = models.CharField(max_length=150)
    generation_method = models.CharField(
        max_length=20, choices=GenerationMethod.choices
    )
    # Matches an entry of AnalysisRun.requirements_snapshot, not a live FK.
    requirement_code = models.CharField(max_length=50, blank=True, default="")
    source_code = models.TextField()
    code_sha256 = models.CharField(max_length=64)
    # Only VALID tests are eligible for execution (enforced by the application).
    validation_status = models.CharField(
        max_length=20,
        choices=ValidationStatus.choices,
        default=ValidationStatus.PENDING,
    )
    validation_errors = models.JSONField(default=list, blank=True)
    generation_metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "generated_tests"
        ordering = ["test_module", "test_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["analysis_run", "test_module", "test_name"],
                name="uq_generated_tests_run_module_name",
            ),
            models.CheckConstraint(
                condition=Q(test_module__regex=r"^test_[A-Za-z0-9_]+\.py$"),
                name="ck_generated_tests_module_format",
            ),
            models.CheckConstraint(
                condition=Q(test_name__regex=r"^test_[A-Za-z0-9_]+$"),
                name="ck_generated_tests_name_format",
            ),
            models.CheckConstraint(
                condition=Q(generation_method__in=["RULE_BASED", "LLM", "HYBRID"]),
                name="ck_generated_tests_method_valid",
            ),
            models.CheckConstraint(
                condition=Q(
                    validation_status__in=[
                        "PENDING",
                        "VALID",
                        "INVALID_SYNTAX",
                        "REJECTED_POLICY",
                    ]
                ),
                name="ck_generated_tests_validation_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(code_sha256__regex=SHA256_HEX_REGEX),
                name="ck_generated_tests_code_sha256_format",
            ),
        ]

    def __str__(self):
        return f"{self.test_module}::{self.test_name}"


class TestExecution(models.Model):
    """One execution attempt. The analysis run is reached via generated_test."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        PASSED = "PASSED", "Passed"
        FAILED = "FAILED", "Failed"
        ERROR = "ERROR", "Error"
        SKIPPED = "SKIPPED", "Skipped"

    # Keeps pytest from collecting this model class as a test case.
    __test__ = False

    id = models.BigAutoField(primary_key=True)
    # Indexed through uq_test_executions_test_attempt.
    generated_test = models.ForeignKey(
        GeneratedTest,
        on_delete=models.CASCADE,
        related_name="executions",
        db_index=False,
    )
    attempt_number = models.IntegerField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    output_excerpt = models.CharField(max_length=10000, blank=True, default="")
    error_summary = models.CharField(max_length=2000, blank=True, default="")
    result_details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "test_executions"
        ordering = ["generated_test_id", "attempt_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["generated_test", "attempt_number"],
                name="uq_test_executions_test_attempt",
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "PENDING",
                        "RUNNING",
                        "PASSED",
                        "FAILED",
                        "ERROR",
                        "SKIPPED",
                    ]
                ),
                name="ck_test_executions_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(attempt_number__gte=1),
                name="ck_test_executions_attempt_positive",
            ),
            models.CheckConstraint(
                condition=Q(duration_ms__isnull=True) | Q(duration_ms__gte=0),
                name="ck_test_executions_duration_non_negative",
            ),
            models.CheckConstraint(
                condition=~Q(status="PENDING")
                | Q(started_at__isnull=True, finished_at__isnull=True),
                name="ck_test_executions_pending_not_started",
            ),
            models.CheckConstraint(
                condition=~Q(status="RUNNING")
                | Q(started_at__isnull=False, finished_at__isnull=True),
                name="ck_test_executions_running_started",
            ),
            models.CheckConstraint(
                condition=~Q(status__in=["PASSED", "FAILED", "ERROR", "SKIPPED"])
                | Q(finished_at__isnull=False),
                name="ck_test_executions_terminal_finished",
            ),
            models.CheckConstraint(
                condition=~Q(status__in=["PASSED", "FAILED"])
                | Q(started_at__isnull=False),
                name="ck_test_executions_outcome_requires_start",
            ),
            models.CheckConstraint(
                condition=Q(started_at__isnull=True)
                | Q(finished_at__isnull=True)
                | Q(finished_at__gte=models.F("started_at")),
                name="ck_test_executions_time_order",
            ),
            models.CheckConstraint(
                condition=Q(duration_ms__isnull=True) | Q(finished_at__isnull=False),
                name="ck_test_executions_duration_requires_finish",
            ),
        ]

    def __str__(self):
        return f"{self.generated_test} attempt {self.attempt_number}: {self.status}"


class SecurityFinding(models.Model):
    class Source(models.TextChoices):
        BANDIT = "BANDIT", "Bandit"
        DJANGO_CHECKLIST = "DJANGO_CHECKLIST", "Django security checklist"
        AST_RULE = "AST_RULE", "AST rule"

    class Severity(models.TextChoices):
        INFO = "INFO", "Info"
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    class Classification(models.TextChoices):
        CONFIRMED = "CONFIRMED", "Confirmed"
        POTENTIAL = "POTENTIAL", "Potential"
        INFORMATIONAL = "INFORMATIONAL", "Informational"

    id = models.BigAutoField(primary_key=True)
    # Indexed through uq_security_findings_run_fingerprint.
    analysis_run = models.ForeignKey(
        AnalysisRun,
        on_delete=models.CASCADE,
        related_name="security_findings",
        db_index=False,
    )
    source = models.CharField(max_length=20, choices=Source.choices)
    rule_id = models.CharField(max_length=100)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    classification = models.CharField(
        max_length=20,
        choices=Classification.choices,
        default=Classification.POTENTIAL,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    file_path = models.CharField(max_length=500, blank=True, default="")
    line_number = models.IntegerField(null=True, blank=True)
    # Masked excerpt; secrets found in the analysed project are never stored.
    evidence_excerpt = models.CharField(max_length=1000, blank=True, default="")
    details = models.JSONField(default=dict, blank=True)
    fingerprint = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "security_findings"
        ordering = ["analysis_run_id", "-created_at"]
        indexes = [
            models.Index(
                fields=["analysis_run", "severity"],
                name="ix_finding_run_severity",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["analysis_run", "fingerprint"],
                name="uq_security_findings_run_fingerprint",
            ),
            models.CheckConstraint(
                condition=Q(source__in=["BANDIT", "DJANGO_CHECKLIST", "AST_RULE"]),
                name="ck_security_findings_source_valid",
            ),
            models.CheckConstraint(
                condition=Q(severity__in=["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]),
                name="ck_security_findings_severity_valid",
            ),
            models.CheckConstraint(
                condition=Q(
                    classification__in=["CONFIRMED", "POTENTIAL", "INFORMATIONAL"]
                ),
                name="ck_security_findings_classification_valid",
            ),
            models.CheckConstraint(
                condition=~Q(rule_id=""), name="ck_security_findings_rule_id_not_blank"
            ),
            models.CheckConstraint(
                condition=~Q(title=""), name="ck_security_findings_title_not_blank"
            ),
            models.CheckConstraint(
                condition=~Q(file_path__startswith="/") & ~Q(file_path__contains=".."),
                name="ck_security_findings_file_path_relative",
            ),
            models.CheckConstraint(
                condition=Q(line_number__isnull=True) | Q(line_number__gte=1),
                name="ck_security_findings_line_number_positive",
            ),
            models.CheckConstraint(
                condition=Q(fingerprint__regex=SHA256_HEX_REGEX),
                name="ck_security_findings_fingerprint_format",
            ),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.rule_id}: {self.title}"
