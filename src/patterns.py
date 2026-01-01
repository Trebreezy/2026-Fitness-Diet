"""
Pattern learning for the Fitness & Diet Logger.
Learns common meals, workouts, and habits from historical data.
"""
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import json
from pathlib import Path


class PatternLearner:
    """
    Learns patterns from logged data to provide personalized suggestions.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"
        self.patterns_file = self.data_dir / "patterns.json"
        self._load_patterns()

    def _load_patterns(self):
        """Load learned patterns from file."""
        if self.patterns_file.exists():
            with open(self.patterns_file) as f:
                data = json.load(f)
                self.common_meals = data.get("common_meals", {})
                self.common_workouts = data.get("common_workouts", {})
                self.meal_times = data.get("meal_times", {})
                self.workout_days = data.get("workout_days", [])
                self.favorite_foods = data.get("favorite_foods", [])
        else:
            self.common_meals = {}
            self.common_workouts = {}
            self.meal_times = {}
            self.workout_days = []
            self.favorite_foods = []

    def _save_patterns(self):
        """Save patterns to file."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.patterns_file, "w") as f:
            json.dump({
                "common_meals": self.common_meals,
                "common_workouts": self.common_workouts,
                "meal_times": self.meal_times,
                "workout_days": self.workout_days,
                "favorite_foods": self.favorite_foods,
            }, f, indent=2)

    def learn_from_logs(self, logs: List[Dict[str, Any]]):
        """
        Analyze logs to learn patterns.

        Args:
            logs: List of log entries with extracted data
        """
        meal_counter = Counter()
        workout_counter = Counter()
        meal_by_time = defaultdict(list)
        workout_by_day = defaultdict(int)
        food_counter = Counter()

        for log in logs:
            log_type = log.get("type")
            name = log.get("name", "").lower()
            log_date = log.get("date")

            if log_type == "Meal":
                meal_counter[name] += 1
                # Track by category (meal time)
                categories = log.get("categories", [])
                for cat in categories:
                    if cat in ["Breakfast", "Lunch", "Dinner", "Snack"]:
                        meal_by_time[cat].append({
                            "name": log.get("name"),
                            "calories": log.get("calories"),
                            "protein": log.get("protein"),
                        })
                # Track individual foods mentioned
                for word in name.split():
                    if len(word) > 3:  # Skip short words
                        food_counter[word] += 1

            elif log_type == "Workout":
                workout_counter[name] += 1
                # Track workout days
                if log_date:
                    try:
                        if isinstance(log_date, str):
                            d = datetime.fromisoformat(log_date.replace("Z", "+00:00"))
                        else:
                            d = log_date
                        workout_by_day[d.strftime("%A")] += 1
                    except Exception:
                        pass

        # Update patterns
        self.common_meals = {
            name: count for name, count in meal_counter.most_common(20)
        }
        self.common_workouts = {
            name: count for name, count in workout_counter.most_common(10)
        }
        self.favorite_foods = [word for word, _ in food_counter.most_common(15)]

        # Track meal patterns by time
        for meal_time, meals in meal_by_time.items():
            self.meal_times[meal_time] = meals[-10:]  # Keep last 10

        # Track workout days
        self.workout_days = [
            day for day, count in sorted(
                workout_by_day.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        ]

        self._save_patterns()

    def get_meal_suggestions(
        self,
        meal_type: str,
        current_calories: int = 0,
        current_protein: float = 0,
        calorie_target: int = 1800,
        protein_target: float = 150,
    ) -> List[Dict[str, Any]]:
        """
        Get personalized meal suggestions.

        Args:
            meal_type: "Breakfast", "Lunch", "Dinner", or "Snack"
            current_calories: Calories consumed today
            current_protein: Protein consumed today
            calorie_target: Daily calorie target
            protein_target: Daily protein target

        Returns:
            List of meal suggestions
        """
        suggestions = []
        calories_remaining = calorie_target - current_calories
        protein_remaining = protein_target - current_protein

        # Get past meals for this time
        past_meals = self.meal_times.get(meal_type, [])

        # Filter to appropriate calorie range
        for meal in past_meals:
            if meal.get("calories"):
                if meal["calories"] <= calories_remaining * 0.5:  # Allow up to 50% of remaining
                    suggestions.append({
                        "name": meal["name"],
                        "calories": meal["calories"],
                        "protein": meal.get("protein", 0),
                        "source": "your_history",
                    })

        # Add default suggestions based on meal type and remaining macros
        if meal_type == "Breakfast":
            if protein_remaining > 30:
                suggestions.extend([
                    {"name": "Eggs with bacon and avocado", "calories": 450, "protein": 28, "source": "keto_suggestion"},
                    {"name": "Omelette with cheese and spinach", "calories": 380, "protein": 26, "source": "keto_suggestion"},
                    {"name": "Eggs with black beans (slow carb)", "calories": 350, "protein": 24, "source": "slow_carb_suggestion"},
                ])
        elif meal_type == "Lunch":
            if protein_remaining > 40:
                suggestions.extend([
                    {"name": "Grilled chicken salad with olive oil", "calories": 450, "protein": 42, "source": "keto_suggestion"},
                    {"name": "Steak salad with avocado", "calories": 550, "protein": 45, "source": "keto_suggestion"},
                    {"name": "Chicken with lentils and vegetables", "calories": 480, "protein": 48, "source": "slow_carb_suggestion"},
                ])
        elif meal_type == "Dinner":
            suggestions.extend([
                {"name": "Salmon with roasted broccoli", "calories": 420, "protein": 38, "source": "keto_suggestion"},
                {"name": "Grilled steak with asparagus", "calories": 480, "protein": 42, "source": "keto_suggestion"},
                {"name": "Ground beef with black beans and peppers", "calories": 520, "protein": 45, "source": "slow_carb_suggestion"},
            ])
        elif meal_type == "Snack":
            if calories_remaining > 200:
                suggestions.extend([
                    {"name": "Handful of almonds", "calories": 164, "protein": 6, "source": "keto_suggestion"},
                    {"name": "String cheese", "calories": 80, "protein": 7, "source": "keto_suggestion"},
                    {"name": "Hard boiled eggs (2)", "calories": 156, "protein": 12, "source": "both"},
                ])

        # Filter out meals that would exceed calorie limit
        suggestions = [s for s in suggestions if s["calories"] <= calories_remaining + 100]

        # Remove duplicates and sort by protein
        seen = set()
        unique_suggestions = []
        for s in sorted(suggestions, key=lambda x: x.get("protein", 0), reverse=True):
            if s["name"].lower() not in seen:
                seen.add(s["name"].lower())
                unique_suggestions.append(s)

        return unique_suggestions[:5]  # Return top 5

    def get_workout_suggestions(
        self,
        recent_workouts: List[Dict[str, Any]],
        day_of_week: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get workout suggestions based on patterns.

        Args:
            recent_workouts: Workouts from the last 7 days
            day_of_week: Current day of week

        Returns:
            List of workout suggestions
        """
        suggestions = []
        day_of_week = day_of_week or datetime.now().strftime("%A")

        # Analyze what muscle groups were worked recently
        recent_categories = []
        for workout in recent_workouts:
            categories = workout.get("categories", [])
            recent_categories.extend(categories)

        category_counts = Counter(recent_categories)

        # Suggest based on what hasn't been done
        if "Cardio" not in recent_categories or category_counts.get("Cardio", 0) < 2:
            suggestions.append({
                "name": "Cardio Session",
                "category": "Cardio",
                "description": "30-min run, cycling, or HIIT",
                "duration": 30,
                "reason": "Improve stamina and burn calories",
            })

        if "Strength" not in recent_categories or category_counts.get("Strength", 0) < 2:
            suggestions.append({
                "name": "Strength Training",
                "category": "Strength",
                "description": "Full body or focus on major muscle groups",
                "duration": 45,
                "reason": "Build muscle and increase metabolism",
            })

        if "Flexibility" not in recent_categories:
            suggestions.append({
                "name": "Flexibility/Yoga",
                "category": "Flexibility",
                "description": "Stretching routine or yoga session",
                "duration": 20,
                "reason": "Improve flexibility and recovery",
            })

        # Add specific workout suggestions
        if day_of_week in ["Monday", "Wednesday", "Friday"]:
            suggestions.append({
                "name": "Upper Body Strength",
                "category": "Strength",
                "description": "Push-ups, rows, shoulder press, bicep curls",
                "duration": 40,
                "reason": "Typical strength day",
            })
        elif day_of_week in ["Tuesday", "Thursday"]:
            suggestions.append({
                "name": "Lower Body + Cardio",
                "category": "Strength",
                "description": "Squats, lunges, followed by 20-min cardio",
                "duration": 45,
                "reason": "Build leg strength and endurance",
            })
        else:
            suggestions.append({
                "name": "Active Recovery",
                "category": "Flexibility",
                "description": "Light walk, stretching, or yoga",
                "duration": 30,
                "reason": "Rest day with light activity",
            })

        # Include common workouts from history
        for workout_name, count in list(self.common_workouts.items())[:3]:
            suggestions.append({
                "name": workout_name.title(),
                "category": "History",
                "description": f"You've done this {count} times",
                "duration": 30,
                "reason": "Based on your workout history",
            })

        return suggestions[:5]

    def suggest_same_as_previous(
        self,
        meal_type: str,
        days_back: int = 1,
    ) -> Optional[Dict[str, Any]]:
        """
        Suggest the same meal as a previous day.

        Args:
            meal_type: "Breakfast", "Lunch", "Dinner"
            days_back: How many days back to look

        Returns:
            Previous meal info if found
        """
        past_meals = self.meal_times.get(meal_type, [])
        if past_meals and len(past_meals) >= days_back:
            return past_meals[-days_back]
        return None

    def detect_cheat_day(self, logs: List[Dict], calorie_target: int = 1800) -> bool:
        """
        Detect if today might be a cheat day based on intake.

        Args:
            logs: Today's logs
            calorie_target: Normal daily target

        Returns:
            True if appears to be a cheat day
        """
        total_calories = sum(log.get("calories") or 0 for log in logs)
        total_carbs = sum(log.get("carbs") or 0 for log in logs)

        # Cheat day indicators: significantly over calories or high carbs
        if total_calories > calorie_target * 1.5:
            return True
        if total_carbs > 100:  # Way over keto limits
            return True

        # Check for "cheat" foods
        for log in logs:
            name = log.get("name", "").lower()
            if any(word in name for word in ["pizza", "burger", "fries", "cake", "ice cream", "pasta", "bread"]):
                return True

        return False

    def get_habit_streak(self, logs: List[Dict], habit: str) -> int:
        """
        Calculate streak for a habit (e.g., consecutive workout days).

        Args:
            logs: Historical logs
            habit: "workout", "weight_log", "meal_log"

        Returns:
            Number of consecutive days
        """
        dates_with_habit = set()

        for log in logs:
            log_date = log.get("date")
            if not log_date:
                continue

            if isinstance(log_date, str):
                log_date = log_date.split("T")[0]

            if habit == "workout" and log.get("type") == "Workout":
                dates_with_habit.add(log_date)
            elif habit == "weight_log" and log.get("type") == "Weight":
                dates_with_habit.add(log_date)
            elif habit == "meal_log" and log.get("type") == "Meal":
                dates_with_habit.add(log_date)

        # Count consecutive days ending today
        streak = 0
        check_date = date.today()

        while check_date.isoformat() in dates_with_habit:
            streak += 1
            check_date -= timedelta(days=1)

        return streak
