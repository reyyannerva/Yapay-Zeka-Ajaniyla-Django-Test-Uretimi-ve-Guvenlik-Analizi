"""ReferenceRequirement için asgari doğrulama sözleşmesi — H4-01 / Issue #33.

API uç noktaları H4-04 (#36) kapsamındadır; burada yalnızca izinli HTTP yöntemlerini ve
``specification`` yapısını (veri sözlüğü 10.2) doğrulayan serializer'lar tanımlanır. Aynı kural
veritabanında ``ck_reference_requirements_access_rule_method`` kısıtıyla da zorlanır.
"""
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema_field
from rest_framework import serializers

from .choices import HTTP_METHODS
from .models import ReferenceRequirement


class AccessRuleSpecificationSerializer(serializers.Serializer):
    schema_version = serializers.IntegerField(min_value=1, max_value=1)
    endpoint = serializers.CharField(max_length=500, allow_blank=False)
    method = serializers.ChoiceField(choices=list(HTTP_METHODS))
    expected_status_by_role = serializers.DictField(
        child=serializers.IntegerField(min_value=100, max_value=599), allow_empty=False
    )


class RoleSpecificationSerializer(serializers.Serializer):
    schema_version = serializers.IntegerField(min_value=1, max_value=1)
    role = serializers.CharField(max_length=50)


class DeployExpectationSpecificationSerializer(serializers.Serializer):
    schema_version = serializers.IntegerField(min_value=1, max_value=1)
    setting = serializers.CharField(max_length=100)
    expected_value = serializers.JSONField()
    check_id = serializers.CharField(max_length=50, required=False)


@extend_schema_field(PolymorphicProxySerializer(
    component_name="ReferenceSpecification",
    serializers=[RoleSpecificationSerializer, AccessRuleSpecificationSerializer, DeployExpectationSpecificationSerializer],
    resource_type_field_name=None,
))
class SpecificationField(serializers.JSONField):
    """``specification`` JSON'u; davranış ``JSONField`` ile aynıdır, yalnızca OpenAPI şeması kategoriye göre
    yapıyı (oneOf) ve ``ACCESS_RULE.method`` enum'unu gösterir (H4-05 / Issue #37). Doğrulama ``validate``'tedir."""


@extend_schema_field({"type": "string", "enum": list(HTTP_METHODS), "nullable": True, "readOnly": True,
                      "description": "ACCESS_RULE satırının HTTP metodu; diğer kategorilerde null."})
class HttpMethodReadField(serializers.CharField):
    pass


SPECIFICATION_SERIALIZERS = {
    ReferenceRequirement.Category.ROLE: RoleSpecificationSerializer,
    ReferenceRequirement.Category.ACCESS_RULE: AccessRuleSpecificationSerializer,
    ReferenceRequirement.Category.DEPLOY_EXPECTATION: DeployExpectationSpecificationSerializer,
}


class ReferenceRequirementSerializer(serializers.ModelSerializer):
    http_method = HttpMethodReadField(read_only=True)
    specification = SpecificationField(required=False)

    class Meta:
        model = ReferenceRequirement
        fields = [
            "id", "project", "requirement_code", "category", "source", "title", "description",
            "expected_result", "specification", "is_active", "revision", "http_method", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "revision", "created_at", "updated_at"]

    def validate(self, attrs):
        category = attrs.get("category", getattr(self.instance, "category", None))
        spec = attrs.get("specification", getattr(self.instance, "specification", {}))
        if not isinstance(spec, dict):
            raise serializers.ValidationError({"specification": "JSON nesnesi olmalıdır."})
        spec_serializer = SPECIFICATION_SERIALIZERS[category](data=spec)
        if not spec_serializer.is_valid():
            raise serializers.ValidationError({"specification": spec_serializer.errors})
        if category != ReferenceRequirement.Category.ROLE and not attrs.get(
            "expected_result", getattr(self.instance, "expected_result", "")
        ):
            raise serializers.ValidationError({"expected_result": "ROLE dışındaki kategorilerde zorunludur."})
        return attrs
