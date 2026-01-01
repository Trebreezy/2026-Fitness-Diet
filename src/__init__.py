"""
Notion Photo & Voice Logger - Main package
"""
from .notion_client import NotionLogger
from .logger import FitnessDietLogger
from .photo_handler import PhotoHandler
from .voice_handler import VoiceHandler
from .analytics import LogAnalytics

__all__ = [
    "NotionLogger",
    "FitnessDietLogger",
    "PhotoHandler",
    "VoiceHandler",
    "LogAnalytics",
]

__version__ = "1.0.0"
