"""
Goal tracking for the Fitness & Diet Logger.
Tracks weight loss, strength, stamina, and flexibility goals.
"""
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass
class WeightGoal:
    """Weight loss goal tracking."""
    starting_weight: float  # lbs
    target_weight: float  # lbs
    start_date: date
    target_date: date
    current_weight: Optional[float] = None
    last_weigh_in: Optional[date] = None

    @property
    def total_to_lose(self) -> float:
        return self.starting_weight - self.target_weight

    @property
    def lost_so_far(self) -> float:
        if self.current_weight:
            return self.starting_weight - self.current_weight
        return 0

    @property
    def remaining_to_lose(self) -> float:
        if self.current_weight:
            return self.current_weight - self.target_weight
        return self.total_to_lose

    @property
    def progress_percentage(self) -> float:
        if self.total_to_lose == 0:
            return 100.0
        return (self.lost_so_far / self.total_to_lose) * 100

    @property
    def days_remaining(self) -> int:
        return (self.target_date - date.today()).days

    @property
    def days_elapsed(self) -> int:
        return (date.today() - self.start_date).days

    @property
    def weekly_target(self) -> float:
        """Pounds to lose per week to stay on track."""
        weeks_remaining = self.days_remaining / 7
        if weeks_remaining <= 0:
            return 0
        return self.remaining_to_lose / weeks_remaining

    @property
    def on_track(self) -> bool:
        """Check if progress is on track."""
        if self.days_elapsed == 0:
            return True
        expected_loss = (self.total_to_lose / (self.target_date - self.start_date).days) * self.days_elapsed
        return self.lost_so_far >= expected_loss * 0.9  # Within 10%


@dataclass
class FitnessGoal:
    """Fitness goal (strength, stamina, flexibility)."""
    goal_type: str  # "strength", "stamina", "flexibility"
    metric: str  # e.g., "pushups", "run_distance", "touch_toes"
    starting_value: float
    target_value: float
    unit: str
    current_value: Optional[float] = None
    start_date: date = field(default_factory=date.today)
    target_date: Optional[date] = None

    @property
    def progress_percentage(self) -> float:
        if self.current_value is None:
            return 0
        total_change = self.target_value - self.starting_value
        if total_change == 0:
            return 100.0
        current_change = self.current_value - self.starting_value
        return (current_change / total_change) * 100


class GoalTracker:
    """
    Tracks all fitness and diet goals.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"
        self.goals_file = self.data_dir / "goals.json"
        self._load_goals()

    def _load_goals(self):
        """Load goals from file."""
        if self.goals_file.exists():
            with open(self.goals_file) as f:
                data = json.load(f)
                self._parse_goals(data)
        else:
            self._set_default_goals()

    def _set_default_goals(self):
        """Set default goals based on user's stated objectives."""
        # User stats: 250 lbs, 5'8"
        # Health concerns: high blood pressure, cholesterol, glucose; low MCH
        # Goal: Lose 50 lbs in 2026
        self.weight_goal = WeightGoal(
            starting_weight=250,  # User's actual starting weight
            target_weight=200,    # 50 lbs less
            start_date=date(2026, 1, 1),
            target_date=date(2026, 12, 31),
        )

        # Health profile for personalized recommendations
        self.health_profile = {
            "height_inches": 68,  # 5'8"
            "starting_weight": 250,
            "conditions": [
                "high_blood_pressure",
                "high_cholesterol",
                "high_glucose",
                "low_mch",  # May indicate iron deficiency
            ],
            "dietary_restrictions": [
                "low_sodium",      # For blood pressure
                "low_saturated_fat",  # For cholesterol
                "low_glycemic",    # For glucose
                "iron_rich",       # For low MCH
            ],
        }

        # Strength goals
        self.strength_goals = [
            FitnessGoal(
                goal_type="strength",
                metric="pushups",
                starting_value=10,
                target_value=50,
                unit="reps",
                target_date=date(2026, 12, 31)
            ),
            FitnessGoal(
                goal_type="strength",
                metric="squats",
                starting_value=15,
                target_value=100,
                unit="reps",
                target_date=date(2026, 12, 31)
            ),
            FitnessGoal(
                goal_type="strength",
                metric="plank",
                starting_value=30,
                target_value=180,
                unit="seconds",
                target_date=date(2026, 12, 31)
            ),
        ]

        # Stamina goals
        self.stamina_goals = [
            FitnessGoal(
                goal_type="stamina",
                metric="run_distance",
                starting_value=1,
                target_value=10,
                unit="km",
                target_date=date(2026, 12, 31)
            ),
            FitnessGoal(
                goal_type="stamina",
                metric="workout_duration",
                starting_value=20,
                target_value=60,
                unit="minutes",
                target_date=date(2026, 12, 31)
            ),
        ]

        # Flexibility goals
        self.flexibility_goals = [
            FitnessGoal(
                goal_type="flexibility",
                metric="touch_toes",
                starting_value=0,
                target_value=1,
                unit="yes/no (1=yes)",
                target_date=date(2026, 12, 31)
            ),
        ]

        # Daily targets (from "Body of an Athlete" plan)
        self.daily_targets = {
            "calories": 2000,      # From user's plan
            "protein": 200,        # From user's plan (high for muscle preservation)
            "carbs": 50,           # Low carb for glucose management
            "fat": 100,            # Moderate fat (prioritize unsaturated for cholesterol)
            "sodium": 1500,        # Low sodium for blood pressure (mg)
            "fiber": 30,           # High fiber for cholesterol (g)
            "water": 100,          # 100 fl oz from user's plan
            "workouts_per_week": 5,  # 5-6 days from plan
            "steps": 10000,
        }

        # Training schedule from "Body of an Athlete"
        self.training_schedule = {
            "strength_days": 3,           # 3 strength training days
            "distance_cardio_days": 1,    # 30min to 1hr
            "hiit_days": 1,               # HIIT/sprints + 45min yoga
            "sports_days": 1,             # Optional
            "recovery_days": 1,           # Foam roller/massage
        }

        self._save_goals()

    def _parse_goals(self, data: Dict):
        """Parse goals from JSON data."""
        if "weight_goal" in data:
            wg = data["weight_goal"]
            self.weight_goal = WeightGoal(
                starting_weight=wg["starting_weight"],
                target_weight=wg["target_weight"],
                start_date=date.fromisoformat(wg["start_date"]),
                target_date=date.fromisoformat(wg["target_date"]),
                current_weight=wg.get("current_weight"),
                last_weigh_in=date.fromisoformat(wg["last_weigh_in"]) if wg.get("last_weigh_in") else None,
            )
        else:
            self.weight_goal = None

        self.strength_goals = []
        self.stamina_goals = []
        self.flexibility_goals = []

        for fg in data.get("fitness_goals", []):
            goal = FitnessGoal(
                goal_type=fg["goal_type"],
                metric=fg["metric"],
                starting_value=fg["starting_value"],
                target_value=fg["target_value"],
                unit=fg["unit"],
                current_value=fg.get("current_value"),
                start_date=date.fromisoformat(fg.get("start_date", date.today().isoformat())),
                target_date=date.fromisoformat(fg["target_date"]) if fg.get("target_date") else None,
            )
            if fg["goal_type"] == "strength":
                self.strength_goals.append(goal)
            elif fg["goal_type"] == "stamina":
                self.stamina_goals.append(goal)
            elif fg["goal_type"] == "flexibility":
                self.flexibility_goals.append(goal)

        self.daily_targets = data.get("daily_targets", {
            "calories": 1800,
            "protein": 150,
            "carbs": 50,
            "fat": 120,
            "water": 8,
            "workouts_per_week": 5,
            "steps": 10000,
        })

    def _save_goals(self):
        """Save goals to file."""
        data = {
            "daily_targets": self.daily_targets,
            "fitness_goals": [],
        }

        if self.weight_goal:
            data["weight_goal"] = {
                "starting_weight": self.weight_goal.starting_weight,
                "target_weight": self.weight_goal.target_weight,
                "start_date": self.weight_goal.start_date.isoformat(),
                "target_date": self.weight_goal.target_date.isoformat(),
                "current_weight": self.weight_goal.current_weight,
                "last_weigh_in": self.weight_goal.last_weigh_in.isoformat() if self.weight_goal.last_weigh_in else None,
            }

        for goal in self.strength_goals + self.stamina_goals + self.flexibility_goals:
            data["fitness_goals"].append({
                "goal_type": goal.goal_type,
                "metric": goal.metric,
                "starting_value": goal.starting_value,
                "target_value": goal.target_value,
                "unit": goal.unit,
                "current_value": goal.current_value,
                "start_date": goal.start_date.isoformat(),
                "target_date": goal.target_date.isoformat() if goal.target_date else None,
            })

        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.goals_file, "w") as f:
            json.dump(data, f, indent=2)

    def update_weight(self, weight: float, weigh_date: Optional[date] = None):
        """Update current weight."""
        weigh_date = weigh_date or date.today()
        if self.weight_goal:
            # Update starting weight if this is the first weigh-in
            if self.weight_goal.current_weight is None:
                self.weight_goal.starting_weight = weight
            self.weight_goal.current_weight = weight
            self.weight_goal.last_weigh_in = weigh_date
            self._save_goals()

    def get_weight_status(self) -> Dict[str, Any]:
        """Get current weight goal status."""
        if not self.weight_goal:
            return {"has_goal": False}

        wg = self.weight_goal
        return {
            "has_goal": True,
            "starting_weight": wg.starting_weight,
            "current_weight": wg.current_weight,
            "target_weight": wg.target_weight,
            "lost_so_far": round(wg.lost_so_far, 1),
            "remaining_to_lose": round(wg.remaining_to_lose, 1),
            "progress_percentage": round(wg.progress_percentage, 1),
            "days_remaining": wg.days_remaining,
            "weekly_target": round(wg.weekly_target, 2),
            "on_track": wg.on_track,
            "last_weigh_in": wg.last_weigh_in.isoformat() if wg.last_weigh_in else None,
        }

    def get_daily_targets(self) -> Dict[str, Any]:
        """Get daily nutrition and activity targets."""
        return self.daily_targets.copy()

    def check_daily_progress(self, logs: List[Dict]) -> Dict[str, Any]:
        """
        Check progress against daily targets.

        Args:
            logs: Today's log entries

        Returns:
            Progress report
        """
        # Sum up today's intake
        total_calories = sum(log.get("calories") or 0 for log in logs)
        total_protein = sum(log.get("protein") or 0 for log in logs)
        workout_count = sum(1 for log in logs if log.get("type") == "Workout")
        workout_minutes = sum(log.get("duration") or 0 for log in logs if log.get("type") == "Workout")

        targets = self.daily_targets
        return {
            "calories": {
                "consumed": total_calories,
                "target": targets["calories"],
                "remaining": targets["calories"] - total_calories,
                "on_track": total_calories <= targets["calories"],
            },
            "protein": {
                "consumed": total_protein,
                "target": targets["protein"],
                "remaining": max(0, targets["protein"] - total_protein),
                "on_track": total_protein >= targets["protein"] * 0.8,
            },
            "workouts": {
                "completed_today": workout_count,
                "minutes_today": workout_minutes,
                "weekly_target": targets["workouts_per_week"],
            },
            "recommendations": self._get_recommendations(total_calories, total_protein, workout_count),
        }

    def _get_recommendations(self, calories: int, protein: float, workouts: int) -> List[str]:
        """Generate recommendations based on progress and health profile."""
        recs = []
        targets = self.daily_targets

        calories_remaining = targets["calories"] - calories
        protein_remaining = targets["protein"] - protein

        if calories_remaining > 600:
            recs.append(f"You have {calories_remaining} calories remaining. Consider a protein-rich meal.")

        if protein_remaining > 40:
            # Recommend iron-rich protein sources for low MCH
            recs.append(f"You need {protein_remaining:.0f}g more protein. Try iron-rich options: beef, salmon, spinach, or lentils.")

        if calories_remaining < 200 and protein_remaining > 20:
            recs.append("Low on calories but need protein? Try a protein shake or lean chicken breast.")

        if workouts == 0:
            recs.append("No workout logged today. Even a 20-minute walk helps!")

        # Health-specific recommendations
        health_tips = self._get_health_tips()
        if health_tips:
            recs.extend(health_tips)

        if not recs:
            recs.append("Great job! You're on track with your goals today.")

        return recs

    def _get_health_tips(self) -> List[str]:
        """Get health-specific tips based on user's conditions."""
        tips = []
        profile = getattr(self, 'health_profile', None)
        if not profile:
            return tips

        conditions = profile.get('conditions', [])

        if 'high_blood_pressure' in conditions:
            tips.append("💡 BP tip: Choose low-sodium options. Season with herbs, lemon, and spices instead of salt.")

        if 'high_cholesterol' in conditions:
            tips.append("💡 Cholesterol tip: Include omega-3 rich foods (salmon, sardines, walnuts) and soluble fiber (oats, beans).")

        if 'high_glucose' in conditions:
            tips.append("💡 Blood sugar tip: Eat protein with every meal, avoid simple carbs, and consider a post-meal walk.")

        if 'low_mch' in conditions:
            tips.append("💡 Iron tip: Pair iron-rich foods (red meat, spinach, lentils) with vitamin C for better absorption.")

        return tips[:2]  # Limit to 2 tips per check

    def get_full_status(self) -> Dict[str, Any]:
        """Get comprehensive goal status."""
        return {
            "weight": self.get_weight_status(),
            "daily_targets": self.daily_targets,
            "strength_goals": [
                {
                    "metric": g.metric,
                    "current": g.current_value,
                    "target": g.target_value,
                    "unit": g.unit,
                    "progress": round(g.progress_percentage, 1),
                }
                for g in self.strength_goals
            ],
            "stamina_goals": [
                {
                    "metric": g.metric,
                    "current": g.current_value,
                    "target": g.target_value,
                    "unit": g.unit,
                    "progress": round(g.progress_percentage, 1),
                }
                for g in self.stamina_goals
            ],
            "flexibility_goals": [
                {
                    "metric": g.metric,
                    "current": g.current_value,
                    "target": g.target_value,
                    "unit": g.unit,
                    "progress": round(g.progress_percentage, 1),
                }
                for g in self.flexibility_goals
            ],
        }

    def update_starting_weight(self, weight: float):
        """Update the starting weight for the goal."""
        if self.weight_goal:
            self.weight_goal.starting_weight = weight
            self.weight_goal.target_weight = weight - 50  # Maintain 50 lb goal
            if self.weight_goal.current_weight is None:
                self.weight_goal.current_weight = weight
            self._save_goals()

    def set_daily_target(self, key: str, value: float):
        """Update a daily target."""
        if key in self.daily_targets:
            self.daily_targets[key] = value
            self._save_goals()
