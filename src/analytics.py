"""
Analytics and trends for the Fitness & Diet Logger.
Provides insights and answers questions about logged data.
"""
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import statistics
from collections import defaultdict

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from .notion_client import NotionLogger


class LogAnalytics:
    """
    Analytics engine for fitness and diet logs.
    Provides:
    - Trend analysis
    - Statistical summaries
    - Goal tracking
    - Natural language queries
    """

    def __init__(self, notion_logger: NotionLogger):
        """
        Initialize analytics with a Notion logger.

        Args:
            notion_logger: Configured NotionLogger instance
        """
        self.notion = notion_logger

    def _get_logs_as_data(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        log_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get logs and extract data."""
        logs = self.notion.query_logs(
            start_date=start_date,
            end_date=end_date,
            log_type=log_type,
            limit=1000,
        )
        return [self.notion.extract_log_data(log) for log in logs]

    def get_calorie_trends(
        self,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Analyze calorie intake trends.

        Args:
            days: Number of days to analyze

        Returns:
            Trend analysis including averages, highs, lows
        """
        start_date = date.today() - timedelta(days=days - 1)
        logs = self._get_logs_as_data(start_date=start_date)

        # Group by date
        daily_calories = defaultdict(int)
        for log in logs:
            if log.get("calories") and log.get("date"):
                log_date = log["date"]
                if isinstance(log_date, str):
                    log_date = log_date.split("T")[0]
                daily_calories[log_date] += log["calories"]

        if not daily_calories:
            return {
                "days_analyzed": days,
                "days_with_data": 0,
                "average_daily": 0,
                "max_daily": 0,
                "min_daily": 0,
                "total": 0,
                "trend": "no data",
                "daily_breakdown": {},
            }

        values = list(daily_calories.values())
        avg = statistics.mean(values)

        # Calculate trend (compare first half to second half)
        sorted_dates = sorted(daily_calories.keys())
        mid = len(sorted_dates) // 2
        if mid > 0:
            first_half = [daily_calories[d] for d in sorted_dates[:mid]]
            second_half = [daily_calories[d] for d in sorted_dates[mid:]]
            first_avg = statistics.mean(first_half) if first_half else 0
            second_avg = statistics.mean(second_half) if second_half else 0

            if second_avg > first_avg * 1.1:
                trend = "increasing"
            elif second_avg < first_avg * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient data"

        return {
            "days_analyzed": days,
            "days_with_data": len(daily_calories),
            "average_daily": round(avg, 1),
            "max_daily": max(values),
            "min_daily": min(values),
            "total": sum(values),
            "trend": trend,
            "daily_breakdown": dict(daily_calories),
        }

    def get_protein_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze protein intake trends.

        Args:
            days: Number of days to analyze

        Returns:
            Trend analysis for protein
        """
        start_date = date.today() - timedelta(days=days - 1)
        logs = self._get_logs_as_data(start_date=start_date)

        daily_protein = defaultdict(float)
        for log in logs:
            if log.get("protein") and log.get("date"):
                log_date = log["date"]
                if isinstance(log_date, str):
                    log_date = log_date.split("T")[0]
                daily_protein[log_date] += log["protein"]

        if not daily_protein:
            return {
                "days_analyzed": days,
                "days_with_data": 0,
                "average_daily": 0,
                "total": 0,
                "daily_breakdown": {},
            }

        values = list(daily_protein.values())
        return {
            "days_analyzed": days,
            "days_with_data": len(daily_protein),
            "average_daily": round(statistics.mean(values), 1),
            "max_daily": round(max(values), 1),
            "min_daily": round(min(values), 1),
            "total": round(sum(values), 1),
            "daily_breakdown": {k: round(v, 1) for k, v in daily_protein.items()},
        }

    def get_workout_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze workout frequency and duration trends.

        Args:
            days: Number of days to analyze

        Returns:
            Workout trend analysis
        """
        start_date = date.today() - timedelta(days=days - 1)
        logs = self._get_logs_as_data(start_date=start_date, log_type="Workout")

        daily_workouts = defaultdict(list)
        total_duration = 0
        categories = defaultdict(int)

        for log in logs:
            log_date = log.get("date", "")
            if isinstance(log_date, str):
                log_date = log_date.split("T")[0]

            daily_workouts[log_date].append(log)

            if log.get("duration"):
                total_duration += log["duration"]

            for cat in log.get("categories", []):
                categories[cat] += 1

        workout_counts = [len(w) for w in daily_workouts.values()]

        return {
            "days_analyzed": days,
            "total_workouts": len(logs),
            "days_with_workouts": len(daily_workouts),
            "total_duration_minutes": total_duration,
            "average_duration_minutes": round(total_duration / len(logs), 1) if logs else 0,
            "workouts_per_week": round(len(logs) / (days / 7), 1),
            "category_breakdown": dict(categories),
            "consistency_score": round(len(daily_workouts) / days * 100, 1),
        }

    def get_weight_trends(self, days: int = 90) -> Dict[str, Any]:
        """
        Analyze weight trends over time.

        Args:
            days: Number of days to analyze

        Returns:
            Weight trend analysis
        """
        start_date = date.today() - timedelta(days=days - 1)
        logs = self._get_logs_as_data(start_date=start_date, log_type="Weight")

        weights = []
        weight_by_date = {}

        for log in logs:
            if log.get("weight") and log.get("date"):
                log_date = log["date"]
                if isinstance(log_date, str):
                    log_date = log_date.split("T")[0]
                weights.append(log["weight"])
                weight_by_date[log_date] = log["weight"]

        if not weights:
            return {
                "days_analyzed": days,
                "measurements": 0,
                "current_weight": None,
                "starting_weight": None,
                "change": None,
                "trend": "no data",
            }

        sorted_dates = sorted(weight_by_date.keys())
        starting = weight_by_date[sorted_dates[0]]
        current = weight_by_date[sorted_dates[-1]]
        change = current - starting

        if change > 2:
            trend = "gaining"
        elif change < -2:
            trend = "losing"
        else:
            trend = "stable"

        return {
            "days_analyzed": days,
            "measurements": len(weights),
            "current_weight": current,
            "starting_weight": starting,
            "change": round(change, 1),
            "average_weight": round(statistics.mean(weights), 1),
            "min_weight": min(weights),
            "max_weight": max(weights),
            "trend": trend,
            "history": weight_by_date,
        }

    def get_mood_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze mood and energy trends.

        Args:
            days: Number of days to analyze

        Returns:
            Mood trend analysis
        """
        start_date = date.today() - timedelta(days=days - 1)
        logs = self._get_logs_as_data(start_date=start_date)

        mood_scores = []
        energy_levels = []
        mood_by_date = defaultdict(list)
        energy_by_date = defaultdict(list)

        def score_to_number(score: str) -> int:
            """Convert score string to number."""
            if score:
                try:
                    return int(score.split(" ")[0])
                except (ValueError, IndexError):
                    return 3
            return 3

        for log in logs:
            log_date = log.get("date", "")
            if isinstance(log_date, str):
                log_date = log_date.split("T")[0]

            if log.get("mood_score"):
                score = score_to_number(log["mood_score"])
                mood_scores.append(score)
                mood_by_date[log_date].append(score)

            if log.get("energy_level"):
                level = score_to_number(log["energy_level"])
                energy_levels.append(level)
                energy_by_date[log_date].append(level)

        # Calculate daily averages
        daily_mood_avg = {
            d: round(statistics.mean(scores), 1)
            for d, scores in mood_by_date.items()
        }
        daily_energy_avg = {
            d: round(statistics.mean(levels), 1)
            for d, levels in energy_by_date.items()
        }

        return {
            "days_analyzed": days,
            "mood_entries": len(mood_scores),
            "energy_entries": len(energy_levels),
            "average_mood": round(statistics.mean(mood_scores), 2) if mood_scores else None,
            "average_energy": round(statistics.mean(energy_levels), 2) if energy_levels else None,
            "mood_trend": daily_mood_avg,
            "energy_trend": daily_energy_avg,
        }

    def get_weekly_summary(
        self,
        week_start: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get a comprehensive summary for a week.

        Args:
            week_start: Start date of the week (defaults to current week)

        Returns:
            Weekly summary with all metrics
        """
        if week_start is None:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())

        week_end = week_start + timedelta(days=6)
        logs = self._get_logs_as_data(start_date=week_start, end_date=week_end)

        summary = {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "total_entries": len(logs),
            "by_type": defaultdict(int),
            "by_day": defaultdict(list),
            "totals": {
                "calories": 0,
                "protein": 0,
                "workout_minutes": 0,
                "workouts": 0,
            },
            "averages": {},
        }

        for log in logs:
            log_type = log.get("type", "Unknown")
            summary["by_type"][log_type] += 1

            log_date = log.get("date", "")
            if isinstance(log_date, str):
                log_date = log_date.split("T")[0]
            summary["by_day"][log_date].append(log_type)

            if log.get("calories"):
                summary["totals"]["calories"] += log["calories"]
            if log.get("protein"):
                summary["totals"]["protein"] += log["protein"]
            if log.get("duration") and log_type == "Workout":
                summary["totals"]["workout_minutes"] += log["duration"]
                summary["totals"]["workouts"] += 1

        # Calculate averages
        days_with_data = len(summary["by_day"])
        if days_with_data > 0:
            summary["averages"]["calories_per_day"] = round(
                summary["totals"]["calories"] / days_with_data, 1
            )
            summary["averages"]["protein_per_day"] = round(
                summary["totals"]["protein"] / days_with_data, 1
            )

        summary["by_type"] = dict(summary["by_type"])
        summary["by_day"] = {k: len(v) for k, v in summary["by_day"].items()}

        return summary

    def get_monthly_summary(
        self,
        year: int,
        month: int,
    ) -> Dict[str, Any]:
        """
        Get a comprehensive summary for a month.

        Args:
            year: Year
            month: Month (1-12)

        Returns:
            Monthly summary
        """
        import calendar

        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)

        logs = self._get_logs_as_data(start_date=start_date, end_date=end_date)

        return {
            "month": f"{year}-{month:02d}",
            "total_entries": len(logs),
            "calorie_trends": self.get_calorie_trends(days=last_day),
            "workout_trends": self.get_workout_trends(days=last_day),
            "weight_trends": self.get_weight_trends(days=last_day),
            "mood_trends": self.get_mood_trends(days=last_day),
        }

    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer natural language questions about the data.

        Args:
            question: Natural language question

        Returns:
            Answer with supporting data
        """
        question_lower = question.lower()

        # Calorie questions
        if any(word in question_lower for word in ["calorie", "calories", "eat", "ate", "eating"]):
            if "today" in question_lower:
                logs = self._get_logs_as_data(
                    start_date=date.today(), end_date=date.today()
                )
                total = sum(log.get("calories") or 0 for log in logs)
                return {
                    "question": question,
                    "answer": f"You've logged {total} calories today.",
                    "data": {"calories_today": total, "meal_count": len([l for l in logs if l.get("calories")])},
                }
            elif "week" in question_lower:
                trends = self.get_calorie_trends(days=7)
                return {
                    "question": question,
                    "answer": f"This week you averaged {trends['average_daily']} calories per day. Total: {trends['total']} calories.",
                    "data": trends,
                }
            else:
                trends = self.get_calorie_trends(days=30)
                return {
                    "question": question,
                    "answer": f"Over the last 30 days, you averaged {trends['average_daily']} calories per day.",
                    "data": trends,
                }

        # Workout questions
        if any(word in question_lower for word in ["workout", "exercise", "gym", "train"]):
            trends = self.get_workout_trends(days=30)
            return {
                "question": question,
                "answer": f"In the last 30 days, you completed {trends['total_workouts']} workouts "
                         f"averaging {trends['workouts_per_week']} per week. "
                         f"Total time: {trends['total_duration_minutes']} minutes.",
                "data": trends,
            }

        # Weight questions
        if any(word in question_lower for word in ["weight", "weigh", "pounds", "lbs"]):
            trends = self.get_weight_trends(days=90)
            if trends["current_weight"]:
                return {
                    "question": question,
                    "answer": f"Your current weight is {trends['current_weight']} lbs. "
                             f"Change over 90 days: {trends['change']:+.1f} lbs ({trends['trend']}).",
                    "data": trends,
                }
            return {
                "question": question,
                "answer": "No weight data found. Log your weight to start tracking.",
                "data": trends,
            }

        # Protein questions
        if "protein" in question_lower:
            trends = self.get_protein_trends(days=30)
            return {
                "question": question,
                "answer": f"Over the last 30 days, you averaged {trends['average_daily']}g of protein per day.",
                "data": trends,
            }

        # Mood questions
        if any(word in question_lower for word in ["mood", "feel", "energy", "happy"]):
            trends = self.get_mood_trends(days=30)
            mood_avg = trends.get("average_mood")
            energy_avg = trends.get("average_energy")
            answer_parts = []
            if mood_avg:
                answer_parts.append(f"Average mood score: {mood_avg}/5")
            if energy_avg:
                answer_parts.append(f"Average energy level: {energy_avg}/5")
            return {
                "question": question,
                "answer": ". ".join(answer_parts) if answer_parts else "No mood data logged yet.",
                "data": trends,
            }

        # Summary questions
        if any(word in question_lower for word in ["summary", "overview", "how am i doing"]):
            weekly = self.get_weekly_summary()
            return {
                "question": question,
                "answer": f"This week: {weekly['total_entries']} entries logged. "
                         f"Calories: {weekly['totals']['calories']}, "
                         f"Protein: {weekly['totals']['protein']}g, "
                         f"Workouts: {weekly['totals']['workouts']}.",
                "data": weekly,
            }

        # Default response
        return {
            "question": question,
            "answer": "I can help with questions about calories, protein, workouts, weight, mood, and weekly summaries. Try asking about specific metrics!",
            "data": None,
        }

    def get_insights(self, days: int = 30) -> List[str]:
        """
        Generate actionable insights based on recent data.

        Args:
            days: Number of days to analyze

        Returns:
            List of insight strings
        """
        insights = []

        # Calorie insights
        calorie_trends = self.get_calorie_trends(days=days)
        if calorie_trends["days_with_data"] > 0:
            if calorie_trends["trend"] == "increasing":
                insights.append("📈 Your calorie intake has been increasing lately.")
            elif calorie_trends["trend"] == "decreasing":
                insights.append("📉 Your calorie intake has been decreasing.")

            if calorie_trends["average_daily"] < 1200:
                insights.append("⚠️ Your average calorie intake seems low. Make sure you're eating enough!")
            elif calorie_trends["average_daily"] > 3000:
                insights.append("📊 High calorie days detected. Track those indulgences!")

        # Workout insights
        workout_trends = self.get_workout_trends(days=days)
        if workout_trends["total_workouts"] > 0:
            if workout_trends["consistency_score"] >= 70:
                insights.append("💪 Great workout consistency! Keep it up!")
            elif workout_trends["consistency_score"] < 30:
                insights.append("🏋️ Try to fit in more workouts this week.")

            if workout_trends["workouts_per_week"] >= 5:
                insights.append("🌟 Excellent! You're working out 5+ times per week!")

        # Weight insights
        weight_trends = self.get_weight_trends(days=days)
        if weight_trends["measurements"] > 1:
            if weight_trends["trend"] == "losing" and weight_trends["change"] < -5:
                insights.append("⚡ Significant weight loss detected. Make sure it's healthy!")
            elif weight_trends["trend"] == "gaining" and weight_trends["change"] > 5:
                insights.append("📊 Weight has increased recently. Check your nutrition plan.")

        # General insights
        if not insights:
            insights.append("📝 Keep logging to get personalized insights!")

        return insights

    def export_to_dataframe(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ):
        """
        Export logs to a pandas DataFrame.

        Args:
            start_date: Start date filter
            end_date: End date filter

        Returns:
            pandas DataFrame (or None if pandas not installed)
        """
        if not HAS_PANDAS:
            raise ImportError("pandas is required for DataFrame export")

        logs = self._get_logs_as_data(start_date=start_date, end_date=end_date)
        return pd.DataFrame(logs)
