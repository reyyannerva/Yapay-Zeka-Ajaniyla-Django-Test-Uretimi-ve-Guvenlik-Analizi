"""Proje API istisnaları — H4-03 / Issue #35."""
from rest_framework import status
from rest_framework.exceptions import APIException


class UploadTooLarge(APIException):
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = "Yüklenen dosya izin verilen boyutu aşıyor."
    default_code = "upload_too_large"


class ProjectBusy(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Projenin devam eden bir analizi var; analiz bitmeden proje silinemez."
    default_code = "project_busy"
