"""
Reference Django ORM models — H2-02 / Issue #24 (revision 2: mockup alignment).

This module is the ORM form of docs/database/database_schema.sql. It is a design
reference and is not imported by the running application. When the models are
moved into an application's models.py, the schema must be created with
`makemigrations` / `migrate`, not with the reference SQL.

Requires Django 5.1+ (CheckConstraint uses `condition=`) and PostgreSQL.
User accounts come from settings.AUTH_USER_MODEL (django.contrib.auth by default).
Login lockout uses django-axes, whose tables are created by its own migrations.
No model stores passwords, JWT tokens, LLM API keys or other secrets.
Controlled values are stored in UPPER CASE; lower-case spellings in diagrams and
documents denote the same values.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q

SHA256_HEX_REGEX = r"^[0-9a-f]{64}$"


class Project(models.Model):
    class SourceType(models.TextChoices):
        ARCHIVE = "ARCHIVE", "Uploaded archive"
        ALLOWED_DIRECTORY = "ALLOWED_DIRECTORY", "Allowed directory"

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
    # NULL for directory projects (ck_projects_directory_source_present).
    source_archive = models.FileField(
        upload_to="project_archives/%Y/%m/", max_length=255, null=True, blank=True
    )
    # Relative to the configured allowed root directory; NULL for archive projects.
    source_directory = models.CharField(max_length=500, null=True, blank=True)
    archive_sha256 = models.CharField(max_length=64, null=True, blank=True)
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
                condition=Q(source_type__in=["ARCHIVE", "ALLOWED_DIRECTORY"]),
                name="ck_projects_source_type_valid",
            ),
            models.CheckConstraint(
                condition=Q(validation_status__in=["PENDING", "VALID", "INVALID"]),
                name="ck_projects_validation_status_valid",
            ),
            models.CheckConstraint(
                condition=~Q(source_type="ARCHIVE")
                | (
                    Q(source_archive__isnull=False)
                    & ~Q(source_archive="")
                    & Q(archive_sha256__isnull=False, source_directory__isnull=True)
                ),
                name="ck_projects_archive_source_present",
            ),
            models.CheckConstraint(
                condition=~Q(source_type="ALLOWED_DIRECTORY")
                | (
                    Q(source_directory__isnull=False)
                    & ~Q(source_directory="")
                    & Q(source_archive__isnull=True, archive_sha256__isnull=True)
                ),
                name="ck_projects_directory_source_present",
            ),
            models.CheckConstraint(
                condition=Q(source_archive__isnull=True)
                | (~Q(source_archive__startswith="/")
                   & ~Q(source_archive__contains="..")),
                name="ck_projects_source_archive_relative",
            ),
            models.CheckConstraint(
                condition=Q(source_directory__isnull=True)
                | (~Q(source_directory__startswith="/")
                   & ~Q(source_directory__contains="..")),
                name="ck_projects_source_directory_relative",
            ),
            models.CheckConstraint(
                condition=Q(archive_sha256__isnull=True)
                | Q(archive_sha256__regex=SHA256_HEX_REGEX),
                name="ck_projects_archive_sha256_format",
            ),
        ]

    def __str__(self):
        return self.name


class ReferenceRequirement(models.Model):
    """Expected behaviour defined independently of what AST analysis observes."""

    class Category(models.TextChoices):
        ROLE = "ROLE", "Role"
        ACCESS_RULE = "ACCESS_RULE", "Access rule"
        DEPLOY_EXPECTATION = "DEPLOY_EXPECTATION", "Deployment expectation"

    class Source(models.TextChoices):
        FORM = "FORM", "Form"
        JSON_UPLOAD = "JSON_UPLOAD", "JSON upload"

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
    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.FORM
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    # Empty only for ROLE rows (ck_reference_requirements_expected_result_not_blank).
    expected_result = models.TextField(blank=True)
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
                condition=Q(category__in=["ROLE", "ACCESS_RULE", "DEPLOY_EXPECTATION"]),
                name="ck_reference_requirements_category_valid",
            ),
            models.CheckConstraint(
                condition=Q(source__in=["FORM", "JSON_UPLOAD"]),
                name="ck_reference_requirements_source_valid",
            ),
            models.CheckConstraint(
                condition=~Q(title=""),
                name="ck_reference_requirements_title_not_blank",
            ),
            models.CheckConstraint(
                condition=Q(category="ROLE") | ~Q(expected_result=""),
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
        VALIDATING = "VALIDATING", "Validating tests"
        EXECUTING = "EXECUTING", "Executing tests"
        SCANNING = "SCANNING", "Security scanning"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    class Method(models.TextChoices):
        RULE_BASED = "RULE_BASED", "Rule-based"
        DIRECT_LLM = "DIRECT_LLM", "Direct LLM"
        HYBRID = "HYBRID", "Hybrid"

    class LlmProvider(models.TextChoices):
        GROQ = "GROQ", "Groq"
        GEMINI = "GEMINI", "Gemini"
        OLLAMA = "OLLAMA", "Ollama"

    ACTIVE_STATUSES = ["QUEUED", "ANALYZING", "GENERATING", "VALIDATING",
                       "EXECUTING", "SCANNING"]
    TERMINAL_STATUSES = ["COMPLETED", "FAILED", "CANCELLED"]

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
    method = models.CharField(max_length=20, choices=Method.choices)
    llm_provider = models.CharField(
        max_length=20, choices=LlmProvider.choices, null=True, blank=True
    )
    llm_model = models.CharField(max_length=100, null=True, blank=True)
    # When the selected model is unreachable, fall back to rule-based generation.
    # On by default, matching the switch on mockup screen 05.
    fallback_enabled = models.BooleanField(default=True)
    # NULL until the task is dispatched to Celery; unique when present.
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)
    requirements_snapshot = models.JSONField(default=list, blank=True)
    ast_results = models.JSONField(default=dict, blank=True)
    processing_metadata = models.JSONField(default=dict, blank=True)
    coverage_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
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
                condition=Q(status__in=["QUEUED", "ANALYZING", "GENERATING",
                                        "VALIDATING", "EXECUTING", "SCANNING"]),
                name="uq_analysis_runs_one_active_per_project",
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "QUEUED",
                        "ANALYZING",
                        "GENERATING",
                        "VALIDATING",
                        "EXECUTING",
                        "SCANNING",
                        "COMPLETED",
                        "FAILED",
                        "CANCELLED",
                    ]
                ),
                name="ck_analysis_runs_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(method__in=["RULE_BASED", "DIRECT_LLM", "HYBRID"]),
                name="ck_analysis_runs_method_valid",
            ),
            models.CheckConstraint(
                condition=Q(llm_provider__isnull=True)
                | Q(llm_provider__in=["GROQ", "GEMINI", "OLLAMA"]),
                name="ck_analysis_runs_llm_provider_valid",
            ),
            models.CheckConstraint(
                condition=Q(
                    method="RULE_BASED",
                    llm_provider__isnull=True,
                    llm_model__isnull=True,
                )
                | (
                    ~Q(method="RULE_BASED")
                    & Q(llm_provider__isnull=False, llm_model__isnull=False)
                    & ~Q(llm_model="")
                ),
                name="ck_analysis_runs_llm_settings",
            ),
            models.CheckConstraint(
                condition=Q(coverage_percent__isnull=True)
                | Q(coverage_percent__gte=0, coverage_percent__lte=100),
                name="ck_analysis_runs_coverage_range",
            ),
            models.CheckConstraint(
                condition=~Q(status="QUEUED") | Q(started_at__isnull=True),
                name="ck_analysis_runs_queued_not_started",
            ),
            models.CheckConstraint(
                condition=~Q(
                    status__in=["ANALYZING", "GENERATING", "VALIDATING", "EXECUTING",
                                "SCANNING", "COMPLETED"]
                )
                | Q(started_at__isnull=False),
                name="ck_analysis_runs_progress_requires_start",
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=["COMPLETED", "FAILED", "CANCELLED"],
                    finished_at__isnull=False,
                )
                | (
                    ~Q(status__in=["COMPLETED", "FAILED", "CANCELLED"])
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


class Endpoint(models.Model):
    """One HTTP endpoint found by AST analysis; ast_results keeps the raw output."""

    class HttpMethod(models.TextChoices):
        GET = "GET", "GET"
        POST = "POST", "POST"
        PUT = "PUT", "PUT"
        PATCH = "PATCH", "PATCH"
        DELETE = "DELETE", "DELETE"

    class UnsupportedReason(models.TextChoices):
        DYNAMIC_ROUTE = "DYNAMIC_ROUTE", "Dynamic route"
        CUSTOM_PERMISSION = "CUSTOM_PERMISSION", "Custom permission class"

    id = models.BigAutoField(primary_key=True)
    # Indexed through uq_endpoints_run_path_method.
    analysis_run = models.ForeignKey(
        AnalysisRun,
        on_delete=models.CASCADE,
        related_name="endpoints",
        db_index=False,
    )
    path = models.CharField(max_length=500)
    http_method = models.CharField(max_length=10, choices=HttpMethod.choices)
    view_name = models.CharField(max_length=255)
    auth_type = models.CharField(max_length=50, blank=True, default="")
    permission_classes = models.JSONField(default=list, blank=True)
    is_supported = models.BooleanField(default=True)
    unsupported_reason = models.CharField(
        max_length=50, choices=UnsupportedReason.choices, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "endpoints"
        ordering = ["path", "http_method"]
        constraints = [
            models.UniqueConstraint(
                fields=["analysis_run", "path", "http_method"],
                name="uq_endpoints_run_path_method",
            ),
            models.CheckConstraint(
                condition=~Q(path=""), name="ck_endpoints_path_not_blank"
            ),
            models.CheckConstraint(
                condition=Q(http_method__in=["GET", "POST", "PUT", "PATCH", "DELETE"]),
                name="ck_endpoints_http_method_valid",
            ),
            models.CheckConstraint(
                condition=Q(unsupported_reason__isnull=True)
                | Q(unsupported_reason__in=["DYNAMIC_ROUTE", "CUSTOM_PERMISSION"]),
                name="ck_endpoints_unsupported_reason_valid",
            ),
            models.CheckConstraint(
                condition=Q(is_supported=True) | Q(unsupported_reason__isnull=False),
                name="ck_endpoints_unsupported_has_reason",
            ),
        ]

    def __str__(self):
        return f"{self.http_method} {self.path}"


class GeneratedTest(models.Model):
    class GenerationMethod(models.TextChoices):
        LLM = "LLM", "LLM"
        RULE_BASED = "RULE_BASED", "Rule-based"

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
    # Must belong to the same analysis run (application rule, data_dictionary 7.2).
    endpoint = models.ForeignKey(
        Endpoint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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
    role = models.CharField(max_length=50, blank=True, default="")
    expected_status = models.SmallIntegerField(null=True, blank=True)
    is_security_test = models.BooleanField(default=False)
    source_code = models.TextField()
    code_sha256 = models.CharField(max_length=64)
    # Only VALID tests are eligible for execution (enforced by the application).
    validation_status = models.CharField(
        max_length=20,
        choices=ValidationStatus.choices,
        default=ValidationStatus.PENDING,
    )
    validation_errors = models.JSONField(default=list, blank=True)
    repair_count = models.SmallIntegerField(default=0)
    generation_metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "generated_tests"
        ordering = ["test_module", "test_name"]
        indexes = [
            models.Index(fields=["endpoint"], name="ix_gentest_endpoint"),
        ]
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
                condition=Q(generation_method__in=["LLM", "RULE_BASED"]),
                name="ck_generated_tests_method_valid",
            ),
            models.CheckConstraint(
                condition=Q(expected_status__isnull=True)
                | Q(expected_status__gte=100, expected_status__lte=599),
                name="ck_generated_tests_expected_status_range",
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
                condition=Q(repair_count__gte=0, repair_count__lte=1),
                name="ck_generated_tests_repair_count_range",
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
        QUEUED = "QUEUED", "Queued"
        RUNNING = "RUNNING", "Running"
        PASS = "PASS", "Pass"
        FAIL = "FAIL", "Fail"
        TECHNICAL_ERROR = "TECHNICAL_ERROR", "Technical error"
        STOPPED = "STOPPED", "Stopped"
        NOT_RUN = "NOT_RUN", "Not run"

    class ErrorType(models.TextChoices):
        IMPORT = "IMPORT", "Import error"
        FIXTURE = "FIXTURE", "Fixture error"
        SYNTAX = "SYNTAX", "Syntax error"
        TIMEOUT = "TIMEOUT", "Timeout"
        OOM = "OOM", "Out of memory"
        OTHER = "OTHER", "Other"

    class ErrorOrigin(models.TextChoices):
        TEST_CODE = "TEST_CODE", "Generated test code"
        TARGET_APP = "TARGET_APP", "Target application"
        INFRASTRUCTURE = "INFRASTRUCTURE", "Infrastructure"

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
        max_length=20, choices=Status.choices, default=Status.QUEUED
    )
    observed_status = models.SmallIntegerField(null=True, blank=True)
    error_type = models.CharField(
        max_length=20, choices=ErrorType.choices, null=True, blank=True
    )
    error_origin = models.CharField(
        max_length=20, choices=ErrorOrigin.choices, null=True, blank=True
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
                        "QUEUED",
                        "RUNNING",
                        "PASS",
                        "FAIL",
                        "TECHNICAL_ERROR",
                        "STOPPED",
                        "NOT_RUN",
                    ]
                ),
                name="ck_test_executions_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(observed_status__isnull=True)
                | Q(observed_status__gte=100, observed_status__lte=599),
                name="ck_test_executions_observed_status_range",
            ),
            models.CheckConstraint(
                condition=Q(error_type__isnull=True)
                | Q(error_type__in=["IMPORT", "FIXTURE", "SYNTAX", "TIMEOUT", "OOM",
                                    "OTHER"]),
                name="ck_test_executions_error_type_valid",
            ),
            models.CheckConstraint(
                condition=Q(error_origin__isnull=True)
                | Q(error_origin__in=["TEST_CODE", "TARGET_APP", "INFRASTRUCTURE"]),
                name="ck_test_executions_error_origin_valid",
            ),
            models.CheckConstraint(
                condition=~Q(status="TECHNICAL_ERROR") | Q(error_type__isnull=False),
                name="ck_test_executions_technical_error_has_type",
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
                condition=~Q(status="QUEUED")
                | Q(started_at__isnull=True, finished_at__isnull=True),
                name="ck_test_executions_queued_not_started",
            ),
            models.CheckConstraint(
                condition=~Q(status="NOT_RUN")
                | Q(started_at__isnull=True, finished_at__isnull=True),
                name="ck_test_executions_not_run_not_started",
            ),
            models.CheckConstraint(
                condition=~Q(status="RUNNING")
                | Q(started_at__isnull=False, finished_at__isnull=True),
                name="ck_test_executions_running_started",
            ),
            models.CheckConstraint(
                condition=~Q(status__in=["PASS", "FAIL", "TECHNICAL_ERROR", "STOPPED"])
                | Q(finished_at__isnull=False),
                name="ck_test_executions_terminal_finished",
            ),
            models.CheckConstraint(
                condition=~Q(status__in=["PASS", "FAIL"]) | Q(started_at__isnull=False),
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
        AUTH_TEST = "AUTH_TEST", "Authorization test"
        BANDIT = "BANDIT", "Bandit"
        CHECK_DEPLOY = "CHECK_DEPLOY", "manage.py check --deploy"

    class Severity(models.TextChoices):
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"
        UNKNOWN = "UNKNOWN", "Unknown"

    class Classification(models.TextChoices):
        VERIFIED = "VERIFIED", "Verified"
        POSSIBLE = "POSSIBLE", "Possible"
        UNCERTAIN = "UNCERTAIN", "Uncertain"

    id = models.BigAutoField(primary_key=True)
    # Indexed through uq_security_findings_run_fingerprint.
    analysis_run = models.ForeignKey(
        AnalysisRun,
        on_delete=models.CASCADE,
        related_name="security_findings",
        db_index=False,
    )
    # Execution that proves the finding; same analysis run (application rule).
    test_execution = models.ForeignKey(
        TestExecution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_findings",
        db_index=False,
    )
    endpoint = models.ForeignKey(
        Endpoint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_findings",
        db_index=False,
    )
    source = models.CharField(max_length=20, choices=Source.choices)
    rule_id = models.CharField(max_length=100)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    classification = models.CharField(
        max_length=20,
        choices=Classification.choices,
        default=Classification.POSSIBLE,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    file_path = models.CharField(max_length=500, blank=True, default="")
    line_number = models.IntegerField(null=True, blank=True)
    # Masked excerpt; secrets found in the analysed project are never stored.
    evidence_excerpt = models.CharField(max_length=1000, blank=True, default="")
    # Key of the ready-made remediation template for this finding type.
    recommendation_key = models.CharField(max_length=50, null=True, blank=True)
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
            models.Index(fields=["test_execution"], name="ix_finding_execution"),
            models.Index(fields=["endpoint"], name="ix_finding_endpoint"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["analysis_run", "fingerprint"],
                name="uq_security_findings_run_fingerprint",
            ),
            models.CheckConstraint(
                condition=Q(source__in=["AUTH_TEST", "BANDIT", "CHECK_DEPLOY"]),
                name="ck_security_findings_source_valid",
            ),
            models.CheckConstraint(
                condition=Q(severity__in=["HIGH", "MEDIUM", "LOW", "UNKNOWN"]),
                name="ck_security_findings_severity_valid",
            ),
            models.CheckConstraint(
                condition=Q(classification__in=["VERIFIED", "POSSIBLE", "UNCERTAIN"]),
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


class Report(models.Model):
    """An exported report file. The file is deleted from storage by the application."""

    class Format(models.TextChoices):
        PDF = "PDF", "PDF"
        JSON = "JSON", "JSON"

    class Scope(models.TextChoices):
        FULL = "FULL", "Full"
        PARTIAL = "PARTIAL", "Partial"

    id = models.BigAutoField(primary_key=True)
    # Indexed through ix_report_run_created.
    analysis_run = models.ForeignKey(
        AnalysisRun,
        on_delete=models.CASCADE,
        related_name="reports",
        db_index=False,
    )
    format = models.CharField(max_length=10, choices=Format.choices)
    # PARTIAL for FAILED and CANCELLED runs (application rule, data_dictionary 7.2).
    scope = models.CharField(max_length=10, choices=Scope.choices)
    sections = models.JSONField(default=list, blank=True)
    file_path = models.CharField(max_length=500)
    file_size_bytes = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["analysis_run", "-created_at"],
                name="ix_report_run_created",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(format__in=["PDF", "JSON"]),
                name="ck_reports_format_valid",
            ),
            models.CheckConstraint(
                condition=Q(scope__in=["FULL", "PARTIAL"]),
                name="ck_reports_scope_valid",
            ),
            models.CheckConstraint(
                condition=~Q(file_path="")
                & ~Q(file_path__startswith="/")
                & ~Q(file_path__contains=".."),
                name="ck_reports_file_path_relative",
            ),
            models.CheckConstraint(
                condition=Q(file_size_bytes__gte=0),
                name="ck_reports_file_size_non_negative",
            ),
        ]

    def __str__(self):
        return f"Report #{self.pk} ({self.format}, {self.scope})"


class LlmCall(models.Model):
    """One language-model call made through LiteLLM (İST-13 token metrics)."""

    class Provider(models.TextChoices):
        GROQ = "GROQ", "Groq"
        GEMINI = "GEMINI", "Gemini"
        OLLAMA = "OLLAMA", "Ollama"

    class Purpose(models.TextChoices):
        GENERATE = "GENERATE", "Generate"
        REPAIR = "REPAIR", "Repair"

    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        ERROR = "ERROR", "Error"
        QUOTA_EXCEEDED = "QUOTA_EXCEEDED", "Quota exceeded"
        TIMEOUT = "TIMEOUT", "Timeout"

    id = models.BigAutoField(primary_key=True)
    # Indexed through ix_llmcall_run_created.
    analysis_run = models.ForeignKey(
        AnalysisRun,
        on_delete=models.CASCADE,
        related_name="llm_calls",
        db_index=False,
    )
    generated_test = models.ForeignKey(
        GeneratedTest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="llm_calls",
        db_index=False,
    )
    provider = models.CharField(max_length=20, choices=Provider.choices)
    model = models.CharField(max_length=100)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    prompt_tokens = models.IntegerField(null=True, blank=True)
    completion_tokens = models.IntegerField(null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    error_message = models.CharField(max_length=2000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "llm_calls"
        ordering = ["analysis_run_id", "created_at"]
        indexes = [
            models.Index(
                fields=["analysis_run", "created_at"],
                name="ix_llmcall_run_created",
            ),
            models.Index(fields=["generated_test"], name="ix_llmcall_generated_test"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(provider__in=["GROQ", "GEMINI", "OLLAMA"]),
                name="ck_llm_calls_provider_valid",
            ),
            models.CheckConstraint(
                condition=~Q(model=""), name="ck_llm_calls_model_not_blank"
            ),
            models.CheckConstraint(
                condition=Q(purpose__in=["GENERATE", "REPAIR"]),
                name="ck_llm_calls_purpose_valid",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["SUCCESS", "ERROR", "QUOTA_EXCEEDED", "TIMEOUT"]),
                name="ck_llm_calls_status_valid",
            ),
            models.CheckConstraint(
                condition=(Q(prompt_tokens__isnull=True) | Q(prompt_tokens__gte=0))
                & (Q(completion_tokens__isnull=True) | Q(completion_tokens__gte=0)),
                name="ck_llm_calls_tokens_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(latency_ms__isnull=True) | Q(latency_ms__gte=0),
                name="ck_llm_calls_latency_non_negative",
            ),
            models.CheckConstraint(
                condition=~Q(status="SUCCESS")
                | Q(prompt_tokens__isnull=False, completion_tokens__isnull=False),
                name="ck_llm_calls_success_has_tokens",
            ),
        ]

    def __str__(self):
        return f"{self.provider}/{self.model} {self.purpose}: {self.status}"
