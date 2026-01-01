"""
Smart Assistant for conversational fitness/diet logging.
Provides intelligent follow-up questions, estimations, and suggestions.
"""
from datetime import date, datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .food_database import find_food, estimate_food, get_keto_suggestions, get_slow_carb_suggestions, FOOD_DATABASE
from .goals import GoalTracker
from .patterns import PatternLearner


@dataclass
class LogIntent:
    """Parsed intent from user input."""
    action: str  # "log_meal", "log_workout", "log_weight", "query", "suggest"
    meal_type: Optional[str] = None  # "Breakfast", "Lunch", etc.
    food_description: Optional[str] = None
    workout_description: Optional[str] = None
    weight: Optional[float] = None
    query: Optional[str] = None
    confidence: str = "high"


class SmartAssistant:
    """
    AI-powered assistant for fitness and diet logging.
    Handles:
    - Intelligent parsing of food descriptions
    - Follow-up questions for comprehensive logging
    - Meal and workout suggestions
    - Goal tracking integration
    """

    def __init__(self):
        self.goal_tracker = GoalTracker()
        self.pattern_learner = PatternLearner()

    def parse_food_entry(self, description: str) -> Dict[str, Any]:
        """
        Parse a food description and estimate nutritional info.

        Args:
            description: User's description of food eaten

        Returns:
            Parsed info with estimates and follow-up questions
        """
        # Try to estimate from description
        estimate = estimate_food(description)

        # Determine meal type from context
        meal_type = self._infer_meal_type(description)

        result = {
            "description": description,
            "meal_type": meal_type,
            "estimates": {
                "calories": estimate["estimated_calories"],
                "protein": estimate["estimated_protein"],
                "carbs": estimate.get("estimated_carbs", 0),
                "fat": estimate.get("estimated_fat", 0),
            },
            "confidence": estimate["confidence"],
            "matched_foods": estimate.get("matched_foods", []),
            "keto_friendly": estimate.get("keto_friendly", None),
            "slow_carb_friendly": estimate.get("slow_carb_friendly", None),
            "needs_clarification": False,
            "follow_up_questions": [],
            "warnings": [],
        }

        # Generate follow-up questions if needed
        if estimate["confidence"] == "low":
            result["needs_clarification"] = True
            result["follow_up_questions"] = [
                "What was the main protein (chicken, beef, fish, etc.)?",
                "How large was the portion (small, medium, large)?",
                "Were there any sides, sauces, or toppings?",
            ]

        elif estimate["confidence"] == "medium":
            result["follow_up_questions"] = [
                "Is my calorie estimate of {} calories accurate?".format(estimate["estimated_calories"]),
                "Any additions like cheese, dressing, or sauces?",
            ]

        # Add warnings for non-compliant foods
        if estimate.get("keto_friendly") is False:
            result["warnings"].append(
                "⚠️ This meal contains high carbs and may not be keto-friendly."
            )

        if estimate.get("slow_carb_friendly") is False and estimate.get("keto_friendly") is False:
            result["warnings"].append(
                "⚠️ This appears to be a 'white carb' food. Is this a cheat day?"
            )

        # Check against daily targets
        targets = self.goal_tracker.get_daily_targets()
        if estimate["estimated_calories"] > targets["calories"] * 0.4:
            result["warnings"].append(
                f"This meal is {estimate['estimated_calories']} cal - more than 40% of your daily target."
            )

        return result

    def _infer_meal_type(self, description: str) -> str:
        """Infer meal type from description or time of day."""
        desc_lower = description.lower()

        # Check for explicit meal type
        if any(word in desc_lower for word in ["breakfast", "morning"]):
            return "Breakfast"
        if any(word in desc_lower for word in ["lunch", "midday"]):
            return "Lunch"
        if any(word in desc_lower for word in ["dinner", "supper", "evening"]):
            return "Dinner"
        if any(word in desc_lower for word in ["snack", "bite"]):
            return "Snack"

        # Infer from time of day
        hour = datetime.now().hour
        if 5 <= hour < 11:
            return "Breakfast"
        elif 11 <= hour < 15:
            return "Lunch"
        elif 15 <= hour < 18:
            return "Snack"
        else:
            return "Dinner"

    def parse_workout_entry(self, description: str) -> Dict[str, Any]:
        """
        Parse a workout description.

        Args:
            description: User's description of workout

        Returns:
            Parsed workout info with follow-up questions
        """
        desc_lower = description.lower()

        # Detect workout type
        if any(word in desc_lower for word in ["run", "jog", "cardio", "bike", "swim", "hiit", "cycling"]):
            category = "Cardio"
        elif any(word in desc_lower for word in ["lift", "weight", "strength", "push", "pull", "squat", "deadlift"]):
            category = "Strength"
        elif any(word in desc_lower for word in ["yoga", "stretch", "flexibility", "pilates"]):
            category = "Flexibility"
        else:
            category = "General"

        # Try to detect duration
        duration = None
        import re
        duration_match = re.search(r'(\d+)\s*(min|minute|hr|hour)', desc_lower)
        if duration_match:
            num = int(duration_match.group(1))
            unit = duration_match.group(2)
            if "hr" in unit or "hour" in unit:
                duration = num * 60
            else:
                duration = num

        # Estimate calories burned
        calories_burned = None
        if duration:
            if category == "Cardio":
                calories_burned = int(duration * 10)  # ~10 cal/min
            elif category == "Strength":
                calories_burned = int(duration * 6)  # ~6 cal/min
            else:
                calories_burned = int(duration * 4)  # ~4 cal/min

        result = {
            "description": description,
            "category": category,
            "duration": duration,
            "calories_burned": calories_burned,
            "follow_up_questions": [],
        }

        if not duration:
            result["follow_up_questions"].append("How long was the workout (in minutes)?")

        if category == "Strength":
            result["follow_up_questions"].append("What muscle groups did you work (upper body, lower body, full body)?")

        if category == "Cardio":
            result["follow_up_questions"].append("What was the intensity (easy, moderate, hard)?")

        return result

    def get_meal_suggestions(self, meal_type: str = "any") -> List[Dict[str, Any]]:
        """
        Get personalized meal suggestions.

        Args:
            meal_type: Type of meal ("Breakfast", "Lunch", "Dinner", "Snack", or "any")

        Returns:
            List of meal suggestions
        """
        targets = self.goal_tracker.get_daily_targets()

        # Get pattern-based suggestions
        suggestions = self.pattern_learner.get_meal_suggestions(
            meal_type=meal_type if meal_type != "any" else "Lunch",
            current_calories=0,  # Would get from today's logs
            current_protein=0,
            calorie_target=targets["calories"],
            protein_target=targets["protein"],
        )

        # Add keto/slow-carb specific suggestions
        keto_foods = get_keto_suggestions(meal_type.lower() if meal_type != "any" else "any")
        slow_carb_foods = get_slow_carb_suggestions(meal_type.lower() if meal_type != "any" else "any")

        # Build sample meals from database
        sample_meals = []

        if meal_type in ["Breakfast", "any"]:
            sample_meals.extend([
                {
                    "name": "Eggs with bacon and avocado",
                    "description": "3 eggs, 3 strips bacon, 1/2 avocado",
                    "calories": 550,
                    "protein": 32,
                    "diet": "keto",
                },
                {
                    "name": "Eggs with black beans",
                    "description": "3 eggs, 1 cup black beans, salsa",
                    "calories": 420,
                    "protein": 30,
                    "diet": "slow_carb",
                },
            ])

        if meal_type in ["Lunch", "any"]:
            sample_meals.extend([
                {
                    "name": "Grilled chicken Caesar salad (no croutons)",
                    "description": "Grilled chicken, romaine, parmesan, olive oil dressing",
                    "calories": 480,
                    "protein": 45,
                    "diet": "keto",
                },
                {
                    "name": "Tuna salad lettuce wraps",
                    "description": "Tuna mixed with mayo, wrapped in lettuce",
                    "calories": 350,
                    "protein": 38,
                    "diet": "keto",
                },
            ])

        if meal_type in ["Dinner", "any"]:
            sample_meals.extend([
                {
                    "name": "Salmon with roasted vegetables",
                    "description": "6oz salmon, broccoli, asparagus with olive oil",
                    "calories": 520,
                    "protein": 42,
                    "diet": "keto",
                },
                {
                    "name": "Steak with lentils",
                    "description": "6oz ribeye, 1 cup lentils, side salad",
                    "calories": 650,
                    "protein": 55,
                    "diet": "slow_carb",
                },
            ])

        if meal_type in ["Snack", "any"]:
            sample_meals.extend([
                {
                    "name": "Almonds and cheese",
                    "description": "1oz almonds, 1oz cheddar",
                    "calories": 280,
                    "protein": 13,
                    "diet": "keto",
                },
                {
                    "name": "Hard boiled eggs",
                    "description": "2 eggs",
                    "calories": 156,
                    "protein": 12,
                    "diet": "both",
                },
            ])

        # Combine and dedupe
        all_suggestions = suggestions + sample_meals
        return all_suggestions[:8]

    def get_workout_suggestions(self) -> List[Dict[str, Any]]:
        """
        Get personalized workout suggestions.

        Returns:
            List of workout suggestions based on goals
        """
        suggestions = [
            {
                "name": "Full Body Strength",
                "category": "Strength",
                "duration": 45,
                "description": "Squats, lunges, push-ups, rows, planks",
                "benefits": ["Build muscle", "Boost metabolism", "Increase strength"],
            },
            {
                "name": "HIIT Cardio",
                "category": "Cardio",
                "duration": 25,
                "description": "30 sec work / 30 sec rest intervals",
                "benefits": ["Burn fat", "Improve stamina", "Time efficient"],
            },
            {
                "name": "5K Run/Walk",
                "category": "Cardio",
                "duration": 30,
                "description": "Jog at comfortable pace, walk if needed",
                "benefits": ["Build endurance", "Burn calories", "Stress relief"],
            },
            {
                "name": "Yoga Flow",
                "category": "Flexibility",
                "duration": 30,
                "description": "Sun salutations, warrior poses, stretching",
                "benefits": ["Improve flexibility", "Recovery", "Mental clarity"],
            },
            {
                "name": "Upper Body Focus",
                "category": "Strength",
                "duration": 40,
                "description": "Push-ups, rows, shoulder press, bicep curls",
                "benefits": ["Build upper body strength", "Improve posture"],
            },
            {
                "name": "Lower Body Focus",
                "category": "Strength",
                "duration": 40,
                "description": "Squats, lunges, glute bridges, calf raises",
                "benefits": ["Build leg strength", "Improve stability"],
            },
        ]

        return suggestions

    def get_daily_briefing(self, today_logs: List[Dict]) -> Dict[str, Any]:
        """
        Generate a daily briefing with progress and recommendations.

        Args:
            today_logs: Today's log entries

        Returns:
            Briefing with progress, remaining targets, and suggestions
        """
        targets = self.goal_tracker.get_daily_targets()
        weight_status = self.goal_tracker.get_weight_status()

        # Calculate today's totals
        total_calories = sum(log.get("calories") or 0 for log in today_logs)
        total_protein = sum(log.get("protein") or 0 for log in today_logs)
        workouts = [log for log in today_logs if log.get("type") == "Workout"]
        meals = [log for log in today_logs if log.get("type") == "Meal"]

        # Calculate remaining
        calories_remaining = targets["calories"] - total_calories
        protein_remaining = targets["protein"] - total_protein

        # Generate recommendations
        recommendations = []

        if calories_remaining > 500 and protein_remaining > 30:
            recommendations.append(
                f"You have {calories_remaining} cal and {protein_remaining:.0f}g protein remaining. "
                "Consider a protein-rich dinner like salmon or chicken."
            )
        elif calories_remaining < 200 and protein_remaining > 30:
            recommendations.append(
                "Low on calories but need protein? A protein shake or lean chicken would work."
            )
        elif calories_remaining < 0:
            recommendations.append(
                f"You're {abs(calories_remaining)} calories over target. "
                "Consider a light dinner or extra workout."
            )

        if not workouts:
            recommendations.append(
                "No workout logged today. Even a 20-minute walk helps with your goals!"
            )

        # Check for cheat day
        is_cheat_day = self.pattern_learner.detect_cheat_day(today_logs, targets["calories"])
        if is_cheat_day:
            recommendations.append(
                "🍕 Looks like a cheat day! Enjoy it, then get back on track tomorrow."
            )

        return {
            "date": date.today().isoformat(),
            "progress": {
                "calories": {
                    "consumed": total_calories,
                    "target": targets["calories"],
                    "remaining": max(0, calories_remaining),
                    "over": max(0, -calories_remaining),
                },
                "protein": {
                    "consumed": total_protein,
                    "target": targets["protein"],
                    "remaining": max(0, protein_remaining),
                },
                "meals_logged": len(meals),
                "workouts_completed": len(workouts),
            },
            "weight_goal": {
                "current": weight_status.get("current_weight"),
                "target": weight_status.get("target_weight"),
                "lost_so_far": weight_status.get("lost_so_far", 0),
                "on_track": weight_status.get("on_track", True),
            },
            "recommendations": recommendations,
            "is_cheat_day": is_cheat_day,
        }

    def generate_follow_up_questions(self, log_type: str, entry: Dict) -> List[str]:
        """
        Generate follow-up questions for a log entry.

        Args:
            log_type: "Meal", "Workout", "Weight", etc.
            entry: The entry data

        Returns:
            List of follow-up questions
        """
        questions = []

        if log_type == "Meal":
            if not entry.get("calories"):
                questions.append("Do you know approximately how many calories that was?")
            if not entry.get("protein"):
                questions.append("What was the protein source (chicken, fish, beef, eggs, etc.)?")
            if not entry.get("categories"):
                questions.append("Was this breakfast, lunch, dinner, or a snack?")

        elif log_type == "Workout":
            if not entry.get("duration"):
                questions.append("How long did you work out (in minutes)?")
            if not entry.get("categories"):
                questions.append("What type of workout was it (cardio, strength, flexibility)?")

        elif log_type == "Weight":
            if not entry.get("mood_score"):
                questions.append("How are you feeling about your progress (1-5)?")

        return questions

    def validate_entry(self, log_type: str, entry: Dict) -> Tuple[bool, List[str]]:
        """
        Validate a log entry and return any issues.

        Args:
            log_type: Type of log
            entry: Entry data

        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []

        if log_type == "Meal":
            if entry.get("calories", 0) > 3000:
                issues.append("Calorie count seems very high (>3000). Is this correct?")
            if entry.get("calories", 0) > 0 and entry.get("protein", 0) == 0:
                issues.append("Meal has calories but no protein logged. Did it contain protein?")

        elif log_type == "Workout":
            if entry.get("duration", 0) > 180:
                issues.append("Workout duration over 3 hours. Is this correct?")

        elif log_type == "Weight":
            weight = entry.get("weight", 0)
            last_weight = self.goal_tracker.weight_goal.current_weight if self.goal_tracker.weight_goal else None
            if last_weight and abs(weight - last_weight) > 5:
                issues.append(f"Weight changed by {abs(weight - last_weight):.1f} lbs since last weigh-in. Please confirm.")

        return len(issues) == 0, issues
