"""
MCP (Model Context Protocol) Server for Fitness & Diet Logger.
Enhanced with smart conversational logging, suggestions, and goal tracking.

To use with Claude Code, add to your MCP settings:
{
    "mcpServers": {
        "fitness-diet-logger": {
            "command": "python",
            "args": ["/path/to/mcp_server/server.py"],
            "env": {
                "NOTION_API_KEY": "your-api-key",
                "NOTION_DATABASE_ID": "your-database-id"
            }
        }
    }
}
"""
import asyncio
import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional, List, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    Prompt,
    PromptMessage,
    GetPromptResult,
)

from src.notion_client import NotionLogger
from src.logger import FitnessDietLogger
from src.analytics import LogAnalytics
from src.smart_assistant import SmartAssistant
from src.goals import GoalTracker
from src.patterns import PatternLearner
from src.food_database import find_food, estimate_food


# Initialize the MCP server
server = Server("fitness-diet-logger")

# Global instances (initialized on first use)
_logger: Optional[FitnessDietLogger] = None
_analytics: Optional[LogAnalytics] = None
_assistant: Optional[SmartAssistant] = None
_goal_tracker: Optional[GoalTracker] = None
_pattern_learner: Optional[PatternLearner] = None


def get_logger() -> FitnessDietLogger:
    global _logger
    if _logger is None:
        _logger = FitnessDietLogger()
    return _logger


def get_analytics() -> LogAnalytics:
    global _analytics
    if _analytics is None:
        _analytics = LogAnalytics(get_logger().notion)
    return _analytics


def get_assistant() -> SmartAssistant:
    global _assistant
    if _assistant is None:
        _assistant = SmartAssistant()
    return _assistant


def get_goal_tracker() -> GoalTracker:
    global _goal_tracker
    if _goal_tracker is None:
        _goal_tracker = GoalTracker()
    return _goal_tracker


def get_pattern_learner() -> PatternLearner:
    global _pattern_learner
    if _pattern_learner is None:
        _pattern_learner = PatternLearner()
    return _pattern_learner


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for Claude."""
    return [
        # === SMART LOGGING TOOLS ===
        Tool(
            name="smart_log_meal",
            description="""Intelligently log a meal with automatic calorie/protein estimation.
            Claude should use this to parse natural descriptions like "I had a chicken salad for lunch".
            The tool will estimate nutrition and return any clarifying questions.
            IMPORTANT: Always ask follow-up questions if the response indicates clarification is needed.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Natural description of the meal (e.g., 'grilled chicken with salad')"
                    },
                    "meal_type": {
                        "type": "string",
                        "enum": ["Breakfast", "Lunch", "Dinner", "Snack"],
                        "description": "Optional meal type. Will be inferred from time of day if not provided."
                    },
                    "confirmed_calories": {
                        "type": "integer",
                        "description": "If user confirmed/corrected the calorie estimate"
                    },
                    "confirmed_protein": {
                        "type": "number",
                        "description": "If user confirmed/corrected the protein estimate"
                    }
                },
                "required": ["description"]
            }
        ),
        Tool(
            name="smart_log_workout",
            description="""Log a workout with intelligent parsing.
            Parses descriptions like "30 minute run" or "upper body strength training".
            Returns clarifying questions if details are missing.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of the workout"
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Duration in minutes (if known)"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["Cardio", "Strength", "Flexibility"],
                        "description": "Workout category (if known)"
                    }
                },
                "required": ["description"]
            }
        ),
        Tool(
            name="log_weight",
            description="Log current weight and update goal progress.",
            inputSchema={
                "type": "object",
                "properties": {
                    "weight": {
                        "type": "number",
                        "description": "Weight in pounds"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes"
                    }
                },
                "required": ["weight"]
            }
        ),

        # === SUGGESTION TOOLS ===
        Tool(
            name="suggest_meal",
            description="""Get personalized meal suggestions based on:
            - Keto and slow-carb diet principles
            - Remaining daily calories/protein
            - User's meal history and preferences
            Use this when user asks what to eat or needs meal ideas.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "meal_type": {
                        "type": "string",
                        "enum": ["Breakfast", "Lunch", "Dinner", "Snack", "any"],
                        "description": "Type of meal"
                    }
                },
                "required": ["meal_type"]
            }
        ),
        Tool(
            name="suggest_workout",
            description="""Get personalized workout suggestions based on:
            - User's goals (strength, stamina, flexibility)
            - Recent workout history
            - Current day of week
            Use this when user asks what workout to do.""",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),

        # === GOAL & PROGRESS TOOLS ===
        Tool(
            name="get_daily_briefing",
            description="""Get today's progress summary including:
            - Calories/protein consumed vs targets
            - Weight goal progress
            - Recommendations for rest of day
            Use this at start of conversation or when user asks about progress.""",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_goal_status",
            description="Get detailed status of weight loss and fitness goals.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="update_starting_weight",
            description="Set or update the starting weight for goal tracking.",
            inputSchema={
                "type": "object",
                "properties": {
                    "weight": {
                        "type": "number",
                        "description": "Starting weight in pounds"
                    }
                },
                "required": ["weight"]
            }
        ),

        # === QUERY TOOLS ===
        Tool(
            name="get_today_logs",
            description="Get all logs for today.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="ask_database",
            description="Ask a natural language question about fitness/diet data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question about the data"
                    }
                },
                "required": ["question"]
            }
        ),
        Tool(
            name="get_trends",
            description="Get calorie, workout, or weight trends.",
            inputSchema={
                "type": "object",
                "properties": {
                    "trend_type": {
                        "type": "string",
                        "enum": ["calories", "workouts", "weight", "all"],
                        "description": "Type of trend to analyze"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to analyze (default 30)"
                    }
                },
                "required": ["trend_type"]
            }
        ),

        # === FOOD DATABASE TOOLS ===
        Tool(
            name="lookup_food",
            description="Look up nutritional info for a specific food.",
            inputSchema={
                "type": "object",
                "properties": {
                    "food": {
                        "type": "string",
                        "description": "Name of food to look up"
                    }
                },
                "required": ["food"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls from Claude."""
    try:
        logger = get_logger()
        analytics = get_analytics()
        assistant = get_assistant()
        goals = get_goal_tracker()

        # === SMART LOGGING ===
        if name == "smart_log_meal":
            description = arguments["description"]
            parsed = assistant.parse_food_entry(description)

            # Use confirmed values if provided, otherwise use estimates
            calories = arguments.get("confirmed_calories") or parsed["estimates"]["calories"]
            protein = arguments.get("confirmed_protein") or parsed["estimates"]["protein"]
            meal_type = arguments.get("meal_type") or parsed["meal_type"]

            # Log the meal
            result = logger.log_meal(
                name=description[:100],
                categories=[meal_type],
                description=description,
                calories=calories,
                protein=protein,
                tags=["keto"] if parsed.get("keto_friendly") else (["slow_carb"] if parsed.get("slow_carb_friendly") else []),
            )

            # Build response
            response = f"✅ Logged: {description}\n"
            response += f"📊 {calories} cal | {protein}g protein | {meal_type}\n"

            if parsed.get("warnings"):
                response += "\n" + "\n".join(parsed["warnings"]) + "\n"

            if parsed["needs_clarification"] or parsed.get("follow_up_questions"):
                response += "\n❓ To improve accuracy, I should ask:\n"
                for q in parsed.get("follow_up_questions", [])[:2]:
                    response += f"   • {q}\n"

            # Show remaining targets
            today_logs = logger.get_today_logs()
            total_cal = sum(log.get("calories") or 0 for log in today_logs)
            total_pro = sum(log.get("protein") or 0 for log in today_logs)
            targets = goals.get_daily_targets()
            response += f"\n📈 Today: {total_cal}/{targets['calories']} cal | {total_pro:.0f}/{targets['protein']}g protein"

            return [TextContent(type="text", text=response)]

        elif name == "smart_log_workout":
            description = arguments["description"]
            parsed = assistant.parse_workout_entry(description)

            duration = arguments.get("duration") or parsed.get("duration") or 30
            category = arguments.get("category") or parsed.get("category") or "General"
            calories = parsed.get("calories_burned")

            result = logger.log_workout(
                name=description[:100],
                categories=[category],
                description=description,
                duration=duration,
                calories_burned=calories,
            )

            response = f"💪 Logged: {description}\n"
            response += f"⏱️ {duration} min | {category}"
            if calories:
                response += f" | ~{calories} cal burned"
            response += "\n"

            if parsed.get("follow_up_questions"):
                response += "\n❓ For better tracking:\n"
                for q in parsed["follow_up_questions"]:
                    response += f"   • {q}\n"

            return [TextContent(type="text", text=response)]

        elif name == "log_weight":
            weight = arguments["weight"]
            goals.update_weight(weight)

            result = logger.log_weight(
                weight=weight,
                description=arguments.get("notes"),
            )

            status = goals.get_weight_status()
            response = f"⚖️ Weight logged: {weight} lbs\n\n"
            response += f"📊 Progress:\n"
            response += f"   Started: {status['starting_weight']} lbs\n"
            response += f"   Current: {status['current_weight']} lbs\n"
            response += f"   Lost: {status['lost_so_far']} lbs\n"
            response += f"   Target: {status['target_weight']} lbs ({status['remaining_to_lose']} to go)\n"
            response += f"   Progress: {status['progress_percentage']:.1f}%\n"
            response += f"\n{'✅ On track!' if status['on_track'] else '⚠️ Behind pace - need to lose ~' + str(round(status['weekly_target'], 1)) + ' lbs/week'}"

            return [TextContent(type="text", text=response)]

        # === SUGGESTIONS ===
        elif name == "suggest_meal":
            meal_type = arguments.get("meal_type", "any")
            suggestions = assistant.get_meal_suggestions(meal_type)

            response = f"🍽️ {meal_type} Suggestions:\n\n"
            for i, s in enumerate(suggestions[:5], 1):
                diet_tag = f"[{s.get('diet', 'keto').upper()}]" if s.get('diet') else ""
                response += f"{i}. **{s['name']}** {diet_tag}\n"
                if s.get('description'):
                    response += f"   {s['description']}\n"
                response += f"   📊 {s['calories']} cal | {s['protein']}g protein\n\n"

            response += "_These follow keto/slow-carb principles for your weight loss goal._"
            return [TextContent(type="text", text=response)]

        elif name == "suggest_workout":
            suggestions = assistant.get_workout_suggestions()

            response = "💪 Workout Suggestions:\n\n"
            for i, s in enumerate(suggestions[:5], 1):
                response += f"{i}. **{s['name']}** [{s['category']}]\n"
                response += f"   ⏱️ {s['duration']} min\n"
                response += f"   {s['description']}\n"
                if s.get('benefits'):
                    response += f"   ✨ {', '.join(s['benefits'])}\n"
                response += "\n"

            response += "_These support your goals: strength, stamina, flexibility._"
            return [TextContent(type="text", text=response)]

        # === PROGRESS ===
        elif name == "get_daily_briefing":
            today_logs = logger.get_today_logs()
            briefing = assistant.get_daily_briefing(today_logs)

            p = briefing["progress"]
            response = f"📅 **Daily Briefing** - {briefing['date']}\n\n"

            response += "**Nutrition:**\n"
            response += f"   🔥 Calories: {p['calories']['consumed']}/{p['calories']['target']}"
            if p['calories']['remaining'] > 0:
                response += f" ({p['calories']['remaining']} remaining)\n"
            else:
                response += f" (⚠️ {p['calories']['over']} over)\n"

            response += f"   🥩 Protein: {p['protein']['consumed']:.0f}/{p['protein']['target']}g"
            if p['protein']['remaining'] > 0:
                response += f" ({p['protein']['remaining']:.0f}g to go)\n"
            else:
                response += " ✅\n"

            response += f"\n**Activity:**\n"
            response += f"   🏋️ Workouts: {p['workouts_completed']}\n"
            response += f"   🍽️ Meals logged: {p['meals_logged']}\n"

            wg = briefing["weight_goal"]
            if wg.get("current"):
                response += f"\n**Weight Goal:**\n"
                response += f"   Current: {wg['current']} lbs | Target: {wg['target']} lbs\n"
                response += f"   Lost so far: {wg['lost_so_far']} lbs\n"

            if briefing.get("is_cheat_day"):
                response += "\n🍕 **Cheat Day Detected** - Enjoy it!\n"

            if briefing.get("recommendations"):
                response += "\n**Recommendations:**\n"
                for rec in briefing["recommendations"]:
                    response += f"   • {rec}\n"

            return [TextContent(type="text", text=response)]

        elif name == "get_goal_status":
            status = goals.get_full_status()
            wg = status["weight"]

            response = "🎯 **Goal Status**\n\n"

            response += "**Weight Loss Goal:**\n"
            if wg["has_goal"]:
                response += f"   Start: {wg['starting_weight']} lbs → Target: {wg['target_weight']} lbs\n"
                response += f"   Current: {wg['current_weight'] or 'Not logged'} lbs\n"
                response += f"   Progress: {wg['progress_percentage']:.1f}%\n"
                response += f"   Days remaining: {wg['days_remaining']}\n"
            else:
                response += "   Not set\n"

            response += "\n**Daily Targets:**\n"
            dt = status["daily_targets"]
            response += f"   Calories: {dt['calories']} | Protein: {dt['protein']}g\n"
            response += f"   Carbs: {dt['carbs']}g | Fat: {dt['fat']}g\n"
            response += f"   Workouts/week: {dt['workouts_per_week']}\n"

            if status.get("strength_goals"):
                response += "\n**Strength Goals:**\n"
                for g in status["strength_goals"]:
                    response += f"   {g['metric']}: {g['current'] or 'N/A'}/{g['target']} {g['unit']}\n"

            return [TextContent(type="text", text=response)]

        elif name == "update_starting_weight":
            weight = arguments["weight"]
            goals.update_starting_weight(weight)
            return [TextContent(type="text", text=f"✅ Starting weight set to {weight} lbs. Target: {weight - 50} lbs.")]

        # === QUERIES ===
        elif name == "get_today_logs":
            logs = logger.get_today_logs()
            if not logs:
                return [TextContent(type="text", text="No logs for today yet.")]

            response = f"📅 Today's Logs ({len(logs)} entries):\n\n"
            for log in logs:
                response += f"• [{log['type']}] {log['name']}\n"
                if log.get('calories'):
                    response += f"  {log['calories']} cal"
                if log.get('protein'):
                    response += f" | {log['protein']}g protein"
                if log.get('duration'):
                    response += f" | {log['duration']} min"
                response += "\n"
            return [TextContent(type="text", text=response)]

        elif name == "ask_database":
            result = analytics.answer_question(arguments["question"])
            return [TextContent(type="text", text=f"❓ {arguments['question']}\n\n💬 {result['answer']}")]

        elif name == "get_trends":
            trend_type = arguments["trend_type"]
            days = arguments.get("days", 30)

            response = f"📈 Trends (Last {days} days)\n\n"

            if trend_type in ["calories", "all"]:
                cal = analytics.get_calorie_trends(days=days)
                response += "**Calories:**\n"
                response += f"   Average: {cal['average_daily']}/day\n"
                response += f"   Trend: {cal['trend']}\n\n"

            if trend_type in ["workouts", "all"]:
                work = analytics.get_workout_trends(days=days)
                response += "**Workouts:**\n"
                response += f"   Total: {work['total_workouts']}\n"
                response += f"   Per week: {work['workouts_per_week']}\n"
                response += f"   Consistency: {work['consistency_score']}%\n\n"

            if trend_type in ["weight", "all"]:
                wt = analytics.get_weight_trends(days=days)
                if wt['current_weight']:
                    response += "**Weight:**\n"
                    response += f"   Current: {wt['current_weight']} lbs\n"
                    response += f"   Change: {wt['change']:+.1f} lbs\n"
                    response += f"   Trend: {wt['trend']}\n"

            return [TextContent(type="text", text=response)]

        elif name == "lookup_food":
            food = find_food(arguments["food"])
            if food:
                keto = "✅" if food.keto_friendly else "❌"
                slow_carb = "✅" if food.slow_carb_friendly else "❌"
                response = f"🍽️ **{food.name}**\n"
                response += f"Serving: {food.serving_size}\n\n"
                response += f"📊 Nutrition:\n"
                response += f"   Calories: {food.calories}\n"
                response += f"   Protein: {food.protein}g\n"
                response += f"   Carbs: {food.carbs}g\n"
                response += f"   Fat: {food.fat}g\n\n"
                response += f"Keto: {keto} | Slow Carb: {slow_carb}"
            else:
                response = f"Food '{arguments['food']}' not found in database."
            return [TextContent(type="text", text=response)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        import traceback
        return [TextContent(type="text", text=f"Error: {str(e)}\n{traceback.format_exc()}")]


@server.list_prompts()
async def list_prompts() -> List[Prompt]:
    """List available prompts."""
    return [
        Prompt(
            name="daily-checkin",
            description="Start a guided daily check-in for logging meals, workouts, and wellness",
            arguments=[],
        ),
        Prompt(
            name="weekly-review",
            description="Review the week's progress and get insights",
            arguments=[],
        ),
        Prompt(
            name="meal-planning",
            description="Get help planning meals for the day based on your goals",
            arguments=[],
        ),
    ]


@server.get_prompt()
async def get_prompt(name: str, arguments: Optional[dict] = None) -> GetPromptResult:
    """Get a prompt template."""
    if name == "daily-checkin":
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text="""Start my daily check-in! First get my daily briefing to see where I stand, then help me:

1. Log any meals I haven't recorded yet
2. Log any workouts
3. Check my progress toward goals

Ask me what I've eaten today and help estimate the nutrition. Follow up with clarifying questions to make the log accurate."""
                    )
                )
            ]
        )

    elif name == "weekly-review":
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text="""Give me a comprehensive weekly review:

1. Get my goal status
2. Show calorie, workout, and weight trends
3. Ask the database about my progress
4. Provide insights and recommendations for next week"""
                    )
                )
            ]
        )

    elif name == "meal-planning":
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text="""Help me plan my meals for today. First get my daily briefing to see what I've eaten and how much I have left, then:

1. Suggest meals that fit my remaining calories and protein
2. Follow keto and slow-carb principles
3. Give me specific meal ideas with portions

Remember my goals: lose 50 lbs, increase strength, stamina, and flexibility."""
                    )
                )
            ]
        )

    return GetPromptResult(messages=[])


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
