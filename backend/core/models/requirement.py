from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from ..choices import HTTP_METHODS, values
from .project import Project


class RequirementCategory(models.TextChoices):
    ROLE = "ROLE", "Rol"
    ACCESS_RULE = "ACCESS_RULE", "Erişim kuralı"
    DEPLOY_EXPECTATION = "DEPLOY_EXPECTATION", "Dağıtım beklentisi"


class RequirementSource(models.TextChoices):
    FORM = "FORM", "Form"
    JSON_UPLOAD = "JSON_UPLOAD", "JSON yükleme"


class ReferenceRequirement(models.Model):
    """Kaynak koddan bağımsız beklenen davranış (veri sözlüğü 4.3, JSON yapısı 10.2).

    ``ACCESS_RULE`` satırlarında HTTP yöntemi ``specification["method"]`` içinde saklanır (kanonik tasarım:
    bir gereksinim = bir endpoint + bir yöntem). Yöntem GET/POST/PUT/PATCH/DELETE'ten biri olmalıdır; bu
    kural H4-01'de model doğrulamasına **ve** veritabanı kısıtına (ck_reference_requirements_access_rule_method)
    eklenmiştir.
    """

    Category = RequirementCategory
    Source = RequirementSource

    id = models.BigAutoField(primary_key=True)
    # İndeks uq_reference_requirements_project_code ile sağlanır.
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="reference_requirements", db_index=False
    )
    requirement_code = models.CharField(max_length=50)
    category = models.CharField(max_length=30, choices=RequirementCategory.choices)
    source = models.CharField(max_length=20, choices=RequirementSource.choices, default=RequirementSource.FORM)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    # Yalnızca ROLE satırlarında boş olabilir.
    expected_result = models.TextField(blank=True)
    specification = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    # Beklenen davranış her değiştiğinde uygulama tarafından artırılır.
    revision = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reference_requirements"
        ordering = ["requirement_code"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "requirement_code"], name="uq_reference_requirements_project_code"
            ),
            models.CheckConstraint(
                condition=Q(requirement_code__regex=r"^[A-Za-z0-9][A-Za-z0-9._-]*$"),
                name="ck_reference_requirements_code_format",
            ),
            models.CheckConstraint(
                condition=Q(category__in=values(RequirementCategory)), name="ck_reference_requirements_category_valid"
            ),
            models.CheckConstraint(
                condition=Q(source__in=values(RequirementSource)), name="ck_reference_requirements_source_valid"
            ),
            models.CheckConstraint(condition=~Q(title=""), name="ck_reference_requirements_title_not_blank"),
            models.CheckConstraint(
                condition=Q(category="ROLE") | ~Q(expected_result=""),
                name="ck_reference_requirements_expected_result_not_blank",
            ),
            models.CheckConstraint(condition=Q(revision__gte=1), name="ck_reference_requirements_revision_positive"),
            # H4-01 eki: ACCESS_RULE satırının yöntemi izinli beş değerden biri olmalı (JSONB anahtarı).
            models.CheckConstraint(
                # has_key: anahtar yoksa "->" SQL NULL döner ve CHECK NULL'ı geçerli sayardı.
                condition=~Q(category="ACCESS_RULE")
                | (Q(specification__has_key="method") & Q(specification__method__in=list(HTTP_METHODS))),
                name="ck_reference_requirements_access_rule_method",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.requirement_code} (r{self.revision})"

    @property
    def http_method(self) -> str | None:
        """ACCESS_RULE satırının HTTP yöntemi; diğer kategorilerde ``None``."""
        if self.category != self.Category.ACCESS_RULE or not isinstance(self.specification, dict):
            return None
        return self.specification.get("method")

    def clean(self) -> None:
        super().clean()
        if not isinstance(self.specification, dict):
            raise ValidationError({"specification": "specification bir JSON nesnesi olmalıdır."})
        if self.category == self.Category.ACCESS_RULE:
            method = self.specification.get("method")
            if method not in HTTP_METHODS:
                raise ValidationError(
                    {"specification": f"ACCESS_RULE için method {', '.join(HTTP_METHODS)} değerlerinden biri olmalıdır."}
                )
