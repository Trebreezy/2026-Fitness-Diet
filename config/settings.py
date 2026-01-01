"""
Configuration settings for the Notion Photo & Voice Logger.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Notion Configuration
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

# Database Schema Configuration
DATABASE_NAME = "Fitness & Diet Log"
DATABASE_PROPERTIES = {
    "Name": {"title": {}},
    "Date": {"date": {}},
    "Type": {
        "select": {
            "options": [
                {"name": "Photo", "color": "blue"},
                {"name": "Voice Note", "color": "green"},
                {"name": "Text Note", "color": "yellow"},
                {"name": "Meal", "color": "orange"},
                {"name": "Workout", "color": "red"},
                {"name": "Weight", "color": "purple"},
                {"name": "Mood", "color": "pink"},
            ]
        }
    },
    "Category": {
        "multi_select": {
            "options": [
                {"name": "Breakfast", "color": "orange"},
                {"name": "Lunch", "color": "yellow"},
                {"name": "Dinner", "color": "red"},
                {"name": "Snack", "color": "pink"},
                {"name": "Cardio", "color": "blue"},
                {"name": "Strength", "color": "purple"},
                {"name": "Flexibility", "color": "green"},
                {"name": "Progress", "color": "gray"},
            ]
        }
    },
    "Description": {"rich_text": {}},
    "Calories": {"number": {"format": "number"}},
    "Protein (g)": {"number": {"format": "number"}},
    "Duration (min)": {"number": {"format": "number"}},
    "Weight (lbs)": {"number": {"format": "number"}},
    "Mood Score": {
        "select": {
            "options": [
                {"name": "1 - Very Low", "color": "red"},
                {"name": "2 - Low", "color": "orange"},
                {"name": "3 - Neutral", "color": "yellow"},
                {"name": "4 - Good", "color": "green"},
                {"name": "5 - Excellent", "color": "blue"},
            ]
        }
    },
    "Energy Level": {
        "select": {
            "options": [
                {"name": "1 - Exhausted", "color": "red"},
                {"name": "2 - Tired", "color": "orange"},
                {"name": "3 - Normal", "color": "yellow"},
                {"name": "4 - Energetic", "color": "green"},
                {"name": "5 - Peak", "color": "blue"},
            ]
        }
    },
    "Image URL": {"url": {}},
    "Transcription": {"rich_text": {}},
    "Tags": {
        "multi_select": {
            "options": [
                {"name": "healthy", "color": "green"},
                {"name": "cheat meal", "color": "red"},
                {"name": "high protein", "color": "blue"},
                {"name": "low carb", "color": "yellow"},
                {"name": "hydration", "color": "blue"},
                {"name": "sleep", "color": "purple"},
            ]
        }
    },
}

# File paths
DATA_DIR = Path(__file__).parent.parent / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
VOICE_DIR = DATA_DIR / "voice_notes"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
VOICE_DIR.mkdir(exist_ok=True)
