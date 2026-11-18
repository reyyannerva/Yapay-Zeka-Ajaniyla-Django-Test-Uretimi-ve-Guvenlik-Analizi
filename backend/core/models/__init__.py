"""Uygulama modelleri — H4-01 / Issue #33.

Kanonik tasarım: ``docs/database/`` (revizyon 3, 9 uygulama tablosu). Issue #33'ün yedi temel varlığı:
User (``settings.AUTH_USER_MODEL`` → ``auth_user``), Project, ReferenceRequirement, AnalysisRun,
GeneratedTest, TestExecution, SecurityFinding. Endpoint, Report ve LlmCall kanonik şemanın destek
tablolarıdır (GeneratedTest/SecurityFinding → Endpoint yabancı anahtarları bu tabloya bağlıdır).
"""
from .analysis import AnalysisRun
from .endpoint import Endpoint
from .execution import TestExecution
from .generation import GeneratedTest
from .llm import LlmCall
from .project import Project
from .reporting import Report
from .requirement import ReferenceRequirement
from .security import SecurityFinding

__all__ = [
    "AnalysisRun",
    "Endpoint",
    "GeneratedTest",
    "LlmCall",
    "Project",
    "ReferenceRequirement",
    "Report",
    "SecurityFinding",
    "TestExecution",
]
