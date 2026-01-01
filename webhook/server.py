"""
Webhook server for Fitness & Diet logging from anywhere.
Accepts POST requests to log meals, workouts, weight, and notes to Notion.
"""
import os
import sys
from datetime import datetime, date
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.notion_client import NotionLogger
from src.smart_assistant import SmartAssistant
from src.goals import GoalTracker

app = FastAPI(
    title="Fitness & Diet Logger API",
    description="Log meals, workouts, and health data to Notion from anywhere",
    version="1.0.0"
)

# Enable CORS for mobile/web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key for authentication (set in environment)
API_KEY = os.getenv("WEBHOOK_API_KEY", "your-secret-key-here")


def verify_api_key(x_api_key: str = Header(None)):
    """Verify the API key from request header."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


# Request models
class MealLog(BaseModel):
    description: str
    meal_type: Optional[str] = None  # breakfast, lunch, dinner, snack
    notes: Optional[str] = None


class WorkoutLog(BaseModel):
    description: str
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None


class WeightLog(BaseModel):
    weight: float
    notes: Optional[str] = None


class QuickLog(BaseModel):
    text: str  # Natural language input, will be parsed automatically


class MoodLog(BaseModel):
    mood: str  # great, good, okay, tired, stressed
    notes: Optional[str] = None


# Initialize services
notion = NotionLogger()
assistant = SmartAssistant()
goals = GoalTracker()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Fitness & Diet Logger",
        "endpoints": ["/log/meal", "/log/workout", "/log/weight", "/log/quick", "/status"]
    }


@app.post("/log/meal")
async def log_meal(meal: MealLog, x_api_key: str = Header(None)):
    """Log a meal to Notion."""
    verify_api_key(x_api_key)

    # Parse the meal using smart assistant
    parsed = assistant.parse_food_entry(meal.description)

    # Determine meal type
    meal_type = meal.meal_type
    if not meal_type:
        hour = datetime.now().hour
        if hour < 10:
            meal_type = "Breakfast"
        elif hour < 14:
            meal_type = "Lunch"
        elif hour < 17:
            meal_type = "Snack"
        else:
            meal_type = "Dinner"

    # Build notes with health flags
    notes_parts = []
    if meal.notes:
        notes_parts.append(meal.notes)
    if parsed.get("warnings"):
        notes_parts.append("⚠️ " + "; ".join(parsed["warnings"]))
    if parsed.get("health_notes"):
        notes_parts.append(parsed["health_notes"])

    # Log to Notion
    entry = notion.create_entry(
        entry_type="Meal",
        title=f"{meal_type}: {meal.description[:50]}",
        notes="\n".join(notes_parts) if notes_parts else None,
        calories=parsed.get("estimated_calories"),
        protein=parsed.get("estimated_protein"),
        mood=None,
    )

    return {
        "success": True,
        "entry_id": entry.get("id"),
        "parsed": {
            "calories": parsed.get("estimated_calories"),
            "protein": parsed.get("estimated_protein"),
            "meal_type": meal_type,
        },
        "warnings": parsed.get("warnings", []),
        "follow_up_questions": parsed.get("follow_up_questions", []),
    }


@app.post("/log/workout")
async def log_workout(workout: WorkoutLog, x_api_key: str = Header(None)):
    """Log a workout to Notion."""
    verify_api_key(x_api_key)

    # Parse the workout
    parsed = assistant.parse_workout_entry(workout.description)

    duration = workout.duration_minutes or parsed.get("estimated_duration", 30)

    # Log to Notion
    entry = notion.create_entry(
        entry_type="Workout",
        title=f"Workout: {workout.description[:50]}",
        notes=workout.notes,
        duration=duration,
        workout_type=parsed.get("category", "General"),
    )

    return {
        "success": True,
        "entry_id": entry.get("id"),
        "parsed": {
            "category": parsed.get("category"),
            "duration": duration,
            "calories_burned": parsed.get("estimated_calories_burned"),
        }
    }


@app.post("/log/weight")
async def log_weight(weight_log: WeightLog, x_api_key: str = Header(None)):
    """Log weight to Notion and update goals."""
    verify_api_key(x_api_key)

    # Update goal tracker
    goals.update_weight(weight_log.weight)
    status = goals.get_weight_status()

    # Log to Notion
    entry = notion.create_entry(
        entry_type="Weight",
        title=f"Weight: {weight_log.weight} lbs",
        notes=weight_log.notes,
    )

    return {
        "success": True,
        "entry_id": entry.get("id"),
        "weight": weight_log.weight,
        "progress": {
            "lost_so_far": status.get("lost_so_far"),
            "remaining": status.get("remaining_to_lose"),
            "progress_percent": status.get("progress_percentage"),
            "on_track": status.get("on_track"),
        }
    }


@app.post("/log/mood")
async def log_mood(mood_log: MoodLog, x_api_key: str = Header(None)):
    """Log mood to Notion."""
    verify_api_key(x_api_key)

    entry = notion.create_entry(
        entry_type="Mood",
        title=f"Mood: {mood_log.mood}",
        notes=mood_log.notes,
        mood=mood_log.mood,
    )

    return {
        "success": True,
        "entry_id": entry.get("id"),
        "mood": mood_log.mood,
    }


@app.post("/log/quick")
async def quick_log(log: QuickLog, x_api_key: str = Header(None)):
    """
    Smart logging - automatically detect what type of entry this is.
    Examples:
    - "eggs and bacon for breakfast" → Meal
    - "ran 3 miles" → Workout
    - "245 lbs" → Weight
    - "feeling tired today" → Mood
    """
    verify_api_key(x_api_key)

    text = log.text.lower()

    # Detect weight
    import re
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lbs?|pounds?)', text)
    if weight_match:
        weight = float(weight_match.group(1))
        return await log_weight(WeightLog(weight=weight, notes=log.text), x_api_key)

    # Detect workout keywords
    workout_keywords = ['ran', 'run', 'walked', 'walk', 'workout', 'gym', 'lifted',
                       'swim', 'bike', 'yoga', 'hiit', 'cardio', 'exercise', 'training',
                       'pushups', 'squats', 'stretch']
    if any(kw in text for kw in workout_keywords):
        return await log_workout(WorkoutLog(description=log.text), x_api_key)

    # Detect mood keywords
    mood_keywords = ['feeling', 'mood', 'tired', 'stressed', 'great', 'happy', 'sad', 'anxious']
    if any(kw in text for kw in mood_keywords):
        mood = "okay"  # Default
        if any(w in text for w in ['great', 'amazing', 'excellent', 'happy']):
            mood = "great"
        elif any(w in text for w in ['good', 'fine', 'well']):
            mood = "good"
        elif any(w in text for w in ['tired', 'exhausted', 'sleepy']):
            mood = "tired"
        elif any(w in text for w in ['stressed', 'anxious', 'worried']):
            mood = "stressed"
        return await log_mood(MoodLog(mood=mood, notes=log.text), x_api_key)

    # Default to meal
    return await log_meal(MealLog(description=log.text), x_api_key)


@app.get("/status")
async def get_status(x_api_key: str = Header(None)):
    """Get today's progress and goal status."""
    verify_api_key(x_api_key)

    # Get today's logs
    today = date.today().isoformat()
    logs = notion.query_logs(start_date=today, end_date=today)

    # Calculate daily progress
    daily_progress = goals.check_daily_progress(logs)
    weight_status = goals.get_weight_status()

    return {
        "date": today,
        "calories": daily_progress["calories"],
        "protein": daily_progress["protein"],
        "workouts": daily_progress["workouts"],
        "weight_goal": weight_status,
        "recommendations": daily_progress["recommendations"],
    }


@app.get("/suggest/meal")
async def suggest_meal(x_api_key: str = Header(None)):
    """Get meal suggestions based on today's intake and health profile."""
    verify_api_key(x_api_key)

    suggestions = assistant.get_meal_suggestions()
    return {
        "suggestions": suggestions,
        "health_focus": ["low_sodium", "iron_rich", "high_protein"],
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
