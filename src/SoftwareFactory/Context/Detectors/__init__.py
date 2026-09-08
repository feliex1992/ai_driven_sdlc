"""
Detectors package — every built-in context detector lives here.

Each detector is a focused module implementing the
SoftwareFactory.Context.Core.detector.Detector interface.

Import order:
  Core (models + engine) → Detectors (concrete detectors)
"""

from .architecture import ArchitectureDetector
from .api import ApiDetector
from .database import DatabaseDetector
from .dependencies import DependencyDetector
from .filesystem import FilesystemDetector
from .git import GitDetector
from .language import LanguageDetector
from .test import TestDetector

__all__ = [
    "ArchitectureDetector",
    "ApiDetector",
    "DatabaseDetector",
    "DependencyDetector",
    "FilesystemDetector",
    "GitDetector",
    "LanguageDetector",
    "TestDetector",
]
