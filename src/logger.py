"""
Main logger interface for the Fitness & Diet Logger.
Combines photo handling, voice notes, and Notion integration.
"""
from datetime import date, datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from .notion_client import NotionLogger
from .photo_handler import PhotoHandler
from .voice_handler import VoiceHandler


class FitnessDietLogger:
    """
    Main interface for logging fitness and diet data.
    Provides a unified API for:
    - Logging meals with photos
    - Recording voice notes
    - Tracking workouts
    - Monitoring weight and mood
    """

    def __init__(
        self,
        notion_api_key: Optional[str] = None,
        notion_database_id: Optional[str] = None,
    ):
        """
        Initialize the logger.

        Args:
            notion_api_key: Notion API key
            notion_database_id: Notion database ID
        """
        self.notion = NotionLogger(
            api_key=notion_api_key,
            database_id=notion_database_id,
        )
        self.photo_handler = PhotoHandler()
        self.voice_handler = VoiceHandler()

    def log_meal(
        self,
        name: str,
        meal_type: str = "Meal",
        categories: Optional[List[str]] = None,
        description: Optional[str] = None,
        calories: Optional[int] = None,
        protein: Optional[float] = None,
        photo_path: Optional[Union[str, Path]] = None,
        image_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
        log_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Log a meal entry.

        Args:
            name: Name of the meal
            meal_type: Type category (default: "Meal")
            categories: Meal categories (Breakfast, Lunch, Dinner, Snack)
            description: Description of the meal
            calories: Calorie count
            protein: Protein in grams
            photo_path: Local path to a photo of the meal
            image_url: URL of the meal photo (if already hosted)
            tags: Tags for the entry
            log_date: Date of the log (defaults to today)

        Returns:
            Created log entry
        """
        # Process photo if provided
        processed_image_url = image_url
        if photo_path and not image_url:
            photo_path = Path(photo_path)
            is_valid, error = self.photo_handler.validate_image(photo_path)
            if is_valid:
                processed_path = self.photo_handler.process_image(photo_path)
                # Note: You'll need to host the image somewhere to get a URL
                # This could be S3, Cloudinary, or any image hosting service
                processed_image_url = f"file://{processed_path}"

        return self.notion.create_log_entry(
            name=name,
            log_type=meal_type,
            log_date=log_date,
            description=description,
            categories=categories,
            calories=calories,
            protein=protein,
            image_url=processed_image_url,
            tags=tags,
        )

    def log_workout(
        self,
        name: str,
        categories: Optional[List[str]] = None,
        description: Optional[str] = None,
        duration: Optional[int] = None,
        calories_burned: Optional[int] = None,
        tags: Optional[List[str]] = None,
        mood_score: Optional[str] = None,
        energy_level: Optional[str] = None,
        log_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Log a workout entry.

        Args:
            name: Name/description of the workout
            categories: Workout categories (Cardio, Strength, Flexibility)
            description: Detailed description
            duration: Duration in minutes
            calories_burned: Estimated calories burned
            tags: Tags for the entry
            mood_score: Mood after workout
            energy_level: Energy level after workout
            log_date: Date of the log

        Returns:
            Created log entry
        """
        return self.notion.create_log_entry(
            name=name,
            log_type="Workout",
            log_date=log_date,
            description=description,
            categories=categories,
            duration=duration,
            calories=calories_burned,
            mood_score=mood_score,
            energy_level=energy_level,
            tags=tags,
        )

    def log_weight(
        self,
        weight: float,
        description: Optional[str] = None,
        mood_score: Optional[str] = None,
        energy_level: Optional[str] = None,
        tags: Optional[List[str]] = None,
        log_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Log a weight entry.

        Args:
            weight: Weight in pounds
            description: Optional notes
            mood_score: Current mood
            energy_level: Current energy level
            tags: Tags for the entry
            log_date: Date of the log

        Returns:
            Created log entry
        """
        date_str = (log_date or date.today()).strftime("%B %d, %Y")
        return self.notion.create_log_entry(
            name=f"Weight: {weight} lbs - {date_str}",
            log_type="Weight",
            log_date=log_date,
            description=description,
            weight=weight,
            mood_score=mood_score,
            energy_level=energy_level,
            tags=tags,
        )

    def log_mood(
        self,
        mood_score: str,
        energy_level: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        log_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Log a mood/wellness entry.

        Args:
            mood_score: Mood score (1-5)
            energy_level: Energy level (1-5)
            description: Notes about mood/feelings
            tags: Tags for the entry
            log_date: Date of the log

        Returns:
            Created log entry
        """
        date_str = (log_date or date.today()).strftime("%B %d, %Y")
        return self.notion.create_log_entry(
            name=f"Mood Check-in - {date_str}",
            log_type="Mood",
            log_date=log_date,
            description=description,
            mood_score=mood_score,
            energy_level=energy_level,
            tags=tags,
        )

    def log_photo(
        self,
        photo_path: Union[str, Path],
        name: Optional[str] = None,
        description: Optional[str] = None,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        log_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Log a photo entry (progress pic, food, etc.).

        Args:
            photo_path: Path to the photo
            name: Name for the entry
            description: Description
            categories: Categories
            tags: Tags
            log_date: Date of the log

        Returns:
            Created log entry
        """
        photo_path = Path(photo_path)

        # Validate and process photo
        is_valid, error = self.photo_handler.validate_image(photo_path)
        if not is_valid:
            raise ValueError(f"Invalid photo: {error}")

        processed_path = self.photo_handler.process_image(photo_path)
        metadata = self.photo_handler.extract_metadata(photo_path)

        # Generate name if not provided
        if not name:
            timestamp = datetime.now().strftime("%I:%M %p")
            name = f"Photo - {timestamp}"

        # Build description with metadata
        full_description = description or ""
        if metadata.get("camera"):
            full_description += f"\n\nCamera: {metadata['camera']}"

        return self.notion.create_log_entry(
            name=name,
            log_type="Photo",
            log_date=log_date,
            description=full_description.strip(),
            categories=categories,
            image_url=f"file://{processed_path}",
            tags=tags,
        )

    def log_voice_note(
        self,
        audio_path: Union[str, Path],
        name: Optional[str] = None,
        transcribe: bool = True,
        description: Optional[str] = None,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        log_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Log a voice note entry.

        Args:
            audio_path: Path to the audio file
            name: Name for the entry
            transcribe: Whether to transcribe the audio
            description: Additional description
            categories: Categories
            tags: Tags
            log_date: Date of the log

        Returns:
            Created log entry
        """
        audio_path = Path(audio_path)

        # Process voice note
        result = self.voice_handler.process_voice_note(
            audio_path,
            transcribe=transcribe,
        )

        if not result["success"]:
            raise ValueError(f"Failed to process voice note: {result['error']}")

        # Extract transcription
        transcription = ""
        if result.get("transcription") and result["transcription"].get("success"):
            transcription = result["transcription"]["text"]

        # Generate name if not provided
        if not name:
            timestamp = datetime.now().strftime("%I:%M %p")
            name = f"Voice Note - {timestamp}"

        # Build description
        full_description = description or ""
        if result["metadata"].get("duration_seconds"):
            duration = result["metadata"]["duration_seconds"]
            full_description += f"\n\nDuration: {duration:.1f} seconds"

        return self.notion.create_log_entry(
            name=name,
            log_type="Voice Note",
            log_date=log_date,
            description=full_description.strip(),
            categories=categories,
            transcription=transcription,
            tags=tags,
        )

    def log_text_note(
        self,
        content: str,
        name: Optional[str] = None,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        log_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Log a simple text note.

        Args:
            content: The note content
            name: Name for the entry
            categories: Categories
            tags: Tags
            log_date: Date of the log

        Returns:
            Created log entry
        """
        if not name:
            # Use first line or first 50 chars as name
            first_line = content.split("\n")[0][:50]
            name = first_line if first_line else "Text Note"

        return self.notion.create_log_entry(
            name=name,
            log_type="Text Note",
            log_date=log_date,
            description=content,
            categories=categories,
            tags=tags,
        )

    def get_today_logs(self) -> List[Dict[str, Any]]:
        """Get all logs for today."""
        logs = self.notion.get_logs_for_date(date.today())
        return [self.notion.extract_log_data(log) for log in logs]

    def get_logs_by_date(self, target_date: date) -> List[Dict[str, Any]]:
        """Get all logs for a specific date."""
        logs = self.notion.get_logs_for_date(target_date)
        return [self.notion.extract_log_data(log) for log in logs]

    def get_recent_logs(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get logs from the last N days."""
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days - 1)
        logs = self.notion.query_logs(start_date=start_date)
        return [self.notion.extract_log_data(log) for log in logs]

    def search_logs(
        self,
        log_type: Optional[str] = None,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search logs with filters.

        Args:
            log_type: Filter by type
            categories: Filter by categories
            tags: Filter by tags
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum results

        Returns:
            List of matching logs
        """
        logs = self.notion.query_logs(
            log_type=log_type,
            categories=categories,
            tags=tags,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return [self.notion.extract_log_data(log) for log in logs]

    def get_daily_summary(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get a summary of logs for a specific day.

        Args:
            target_date: Date to summarize (defaults to today)

        Returns:
            Summary statistics
        """
        target_date = target_date or date.today()
        logs = self.get_logs_by_date(target_date)

        summary = {
            "date": target_date.isoformat(),
            "total_entries": len(logs),
            "by_type": {},
            "total_calories": 0,
            "total_protein": 0,
            "total_workout_minutes": 0,
            "weight": None,
            "mood_scores": [],
            "energy_levels": [],
        }

        for log in logs:
            # Count by type
            log_type = log.get("type", "Unknown")
            summary["by_type"][log_type] = summary["by_type"].get(log_type, 0) + 1

            # Sum calories
            if log.get("calories"):
                summary["total_calories"] += log["calories"]

            # Sum protein
            if log.get("protein"):
                summary["total_protein"] += log["protein"]

            # Sum workout duration
            if log.get("duration") and log_type == "Workout":
                summary["total_workout_minutes"] += log["duration"]

            # Track weight (use most recent)
            if log.get("weight"):
                summary["weight"] = log["weight"]

            # Collect mood scores
            if log.get("mood_score"):
                summary["mood_scores"].append(log["mood_score"])

            # Collect energy levels
            if log.get("energy_level"):
                summary["energy_levels"].append(log["energy_level"])

        return summary
