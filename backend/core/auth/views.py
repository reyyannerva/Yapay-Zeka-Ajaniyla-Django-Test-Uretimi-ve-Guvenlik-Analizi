"""Kimlik doğrulama uç noktaları — H4-02 / Issue #34."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .exceptions import AccountLocked
from .serializers import (
    LockoutTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    make_reset_uid_token,
)
from .throttling import LoginRateThrottle

User = get_user_model()


class LoginView(TokenObtainPairView):
    """POST kullanıcı adı+parola → access/refresh token. Kilitliyse 429, hatalıysa 401."""

    serializer_class = LockoutTokenObtainPairSerializer
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except AccountLocked as exc:
            # H5-03 / #41: kilit yanıtı code/locked_until/retry_after_seconds ve Retry-After ile döner.
            return exc.to_response()


class LogoutView(APIView):
    """POST {refresh} → refresh token'ı blacklist'e alır (çıkış)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        token_str = request.data.get("refresh")
        if not token_str:
            return Response({"detail": "refresh alanı zorunludur."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(token_str).blacklist()
        except TokenError:
            return Response({"detail": "Geçersiz veya süresi dolmuş token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    """GET → kimliği doğrulanmış kullanıcının temel bilgileri (hassas alan döndürülmez)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response({"id": u.id, "username": u.username, "email": u.email})


class PasswordResetRequestView(APIView):
    """POST {email} → kayıtlı kullanıcıya sıfırlama bağlantısı gönderir. Yanıt her zaman geneldir."""

    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    GENERIC = {"detail": "E-posta kayıtlıysa şifre sıfırlama bağlantısı gönderildi."}

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        for user in User.objects.filter(email__iexact=email, is_active=True):
            self._send_reset_email(user)
        # Hesap varlığını ifşa etmemek için her durumda aynı yanıt.
        return Response(self.GENERIC, status=status.HTTP_200_OK)

    @staticmethod
    def _send_reset_email(user):
        uid, token = make_reset_uid_token(user)
        link = f"{settings.FRONTEND_PASSWORD_RESET_URL}?uid={uid}&token={token}"
        try:
            send_mail(
                subject="Şifre sıfırlama",
                message=f"Parolanızı sıfırlamak için: {link}\nBağlantı sınırlı süre geçerlidir.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,  # e-posta hatası kullanıcıya hesap varlığını sızdırmaz
            )
        except Exception:  # pragma: no cover — gönderim hatasında da genel yanıt döner
            pass


class PasswordResetConfirmView(APIView):
    """POST {uid, token, new_password} → parolayı günceller. Geçersiz bağlantı 400."""

    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Parola güncellendi."}, status=status.HTTP_200_OK)
