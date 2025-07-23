# ABOUTME: Package initialization for typing pattern analyzer
"""
Advanced macOS Typing Pattern Analyzer

A comprehensive tool for analyzing typing patterns, efficiency metrics,
and behavioral insights from keystroke data.
"""

__version__ = "1.0.0"
__author__ = "Braydon Fuller"
__description__ = (
    "Advanced macOS typing pattern analyzer with comprehensive behavioral insights"
)

from .keylogger import TypingAnalyzerKeylogger, MacOSAppTracker
from .analyzer import TypingPatternAnalyzer
from .utils import KeystrokeEvent, ConfigManager, DataManager

__all__ = [
    "TypingAnalyzerKeylogger",
    "MacOSAppTracker",
    "TypingPatternAnalyzer",
    "KeystrokeEvent",
    "ConfigManager",
    "DataManager",
]
