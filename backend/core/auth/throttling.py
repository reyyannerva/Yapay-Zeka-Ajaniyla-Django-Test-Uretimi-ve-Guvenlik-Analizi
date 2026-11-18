"""Giriş uç noktası için temel istek sınırlaması (İST-10) — H4-02 / Issue #34."""
from rest_framework.throttling import ScopedRateThrottle


class LoginRateThrottle(ScopedRateThrottle):
    """`login` oranıyla (settings.DEFAULT_THROTTLE_RATES) anonim giriş isteklerini sınırlar."""

    scope = "login"
