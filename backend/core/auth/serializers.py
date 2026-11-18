"""Kimlik doğrulama serializer'ları — H4-02 / Issue #34.

Giriş, django-axes (H4-01 #33) kilidine entegre edilir: kilitliyken token üretilmez; başarısız
denemeler sayılır; başarılı girişte sayaç ``user_logged_in`` sinyaliyle sıfırlanır. Şifre sıfırlama,
Django'nun süreli token mekanizmasını kullanır ve hesap varlığını ifşa etmez.
"""
from axes.handlers.proxy import AxesProxyHandler
from axes.helpers import get_credentials
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .exceptions import AccountLocked

User = get_user_model()


class LockoutTokenObtainPairSerializer(TokenObtainPairSerializer):
    """SimpleJWT giriş + django-axes kilit entegrasyonu."""

    def validate(self, attrs):
        request = self.context.get("request")
        username = attrs.get(self.username_field)
        credentials = get_credentials(username=username)

        # Kilitliyse hiç denemeden 429 döndür (sayaç şişirmemek için).
        if AxesProxyHandler.is_locked(request, credentials):
            raise AccountLocked()

        try:
            data = super().validate(attrs)  # authenticate(request=...) → axes başarısızlığı sayar
        except AuthenticationFailed:
            # Bu başarısız deneme kilidi tetiklemiş olabilir (ör. üçüncü deneme).
            if AxesProxyHandler.is_locked(request, credentials):
                raise AccountLocked()
            raise  # tutarlı, hesap varlığını ifşa etmeyen 401

        # Başarılı giriş: axes sayacını user_logged_in sinyaliyle sıfırla (AXES_RESET_ON_SUCCESS).
        user_logged_in.send(sender=self.user.__class__, request=request, user=self.user)
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """Şifre sıfırlama talebi. Yanıt her zaman geneldir; hesap varlığı ifşa edilmez."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Yeni parola belirleme. Geçersiz/süresi dolmuş/kullanılmış bağlantı reddedilir."""

    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self._user_from_uid(attrs["uid"])
        if user is None or not default_token_generator.check_token(user, attrs["token"]):
            # Geçersiz/süresi dolmuş/tekrar kullanılmış bağlantı — genel hata.
            raise serializers.ValidationError({"token": "Bağlantı geçersiz veya süresi dolmuş."})
        try:
            validate_password(attrs["new_password"], user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)})
        attrs["user"] = user
        return attrs

    @staticmethod
    def _user_from_uid(uid):
        try:
            pk = force_str(urlsafe_base64_decode(uid))
            return User.objects.get(pk=pk)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])  # parola değişince eski sıfırlama token'ı geçersizleşir
        return user


def make_reset_uid_token(user) -> tuple[str, str]:
    """Kullanıcı için (uid, token) üretir (e-posta bağlantısında kullanılır)."""
    return urlsafe_base64_encode(force_bytes(user.pk)), default_token_generator.make_token(user)
