"""
MCP (Model Context Protocol) Server for Fitness & Diet Logger.
This server enables Claude Code to interact with the logging system.

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
import base64
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
    ImageContent,
    Resource,
    Prompt,
    PromptMessage,
    GetPromptResult,
)

from src.notion_client import NotionLogger
from src.logger import FitnessDietLogger
from src.photo_handler import PhotoHandler
from src.voice_handler import VoiceHandler
from src.analytics import LogAnalytics


# Initialize the MCP server
server = Server("fitness-diet-logger")

# Global instances (initialized on first use)
_logger: Optional[FitnessDietLogger] = None
_analytics: Optional[LogAnalytics] = None


def get_logger() -> FitnessDietLogger:
    """Get or create the logger instance."""
    global _logger
    if _logger is None:
        _logger = FitnessDietLogger()
    return _logger


def get_analytics() -> LogAnalytics:
    """Get or create the analytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = LogAnalytics(get_logger().notion)
    return _analytics


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for Claude."""
    return [
        Tool(
            name="log_meal",
            description="Log a meal with optional photo, calories, and nutritional info. Records to Notion calendar.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the meal (e.g., 'Grilled Chicken Salad')"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["Breakfast", "Lunch", "Dinner", "Snack"],
                        "description": "Meal category"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the meal"
                    },
                    "calories": {
                        "type": "integer",
                        "description": "Calorie count"
                    },
                    "protein": {
                        "type": "number",
                        "description": "Protein in grams"
                    },
                    "photo_path": {
                        "type": "string",
                        "description": "Path to a photo of the meal"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags like 'healthy', 'high protein', etc."
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="log_workout",
            description="Log a workout session with duration and details.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name/type of workout (e.g., 'Morning Run', 'Upper Body')"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["Cardio", "Strength", "Flexibility"],
                        "description": "Workout category"
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Duration in minutes"
                    },
                    "description": {
                        "type": "string",
                        "description": "Workout details (exercises, sets, reps)"
                    },
                    "calories_burned": {
                        "type": "integer",
                        "description": "Estimated calories burned"
                    },
                    "mood_after": {
                        "type": "string",
                        "enum": ["1 - Very Low", "2 - Low", "3 - Neutral", "4 - Good", "5 - Excellent"],
                        "description": "Mood after workout"
                    },
                    "energy_after": {
                        "type": "string",
                        "enum": ["1 - Exhausted", "2 - Tired", "3 - Normal", "4 - Energetic", "5 - Peak"],
                        "description": "Energy level after workout"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="log_weight",
            description="Log your current weight.",
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
                    },
                    "mood": {
                        "type": "string",
                        "enum": ["1 - Very Low", "2 - Low", "3 - Neutral", "4 - Good", "5 - Excellent"],
                        "description": "Current mood"
                    }
                },
                "required": ["weight"]
            }
        ),
        Tool(
            name="log_mood",
            description="Log your current mood and energy level.",
            inputSchema={
                "type": "object",
                "properties": {
                    "mood": {
                        "type": "string",
                        "enum": ["1 - Very Low", "2 - Low", "3 - Neutral", "4 - Good", "5 - Excellent"],
                        "description": "Current mood score"
                    },
                    "energy": {
                        "type": "string",
                        "enum": ["1 - Exhausted", "2 - Tired", "3 - Normal", "4 - Energetic", "5 - Peak"],
                        "description": "Current energy level"
                    },
                    "notes": {
                        "type": "string",
                        "description": "How you're feeling, what's on your mind"
                    }
                },
                "required": ["mood"]
            }
        ),
        Tool(
            name="log_photo",
            description="Log a photo (progress pic, food, etc.) to your Notion calendar.",
            inputSchema={
                "type": "object",
                "properties": {
                    "photo_path": {
                        "type": "string",
                        "description": "Path to the photo file"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name/title for the photo"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the photo"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["Progress", "Meal", "Workout"],
                        "description": "Photo category"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for the photo"
                    }
                },
                "required": ["photo_path"]
            }
        ),
        Tool(
            name="log_voice_note",
            description="Log a voice note. Transcribes the audio and saves to Notion.",
            inputSchema={
                "type": "object",
                "properties": {
                    "audio_path": {
                        "type": "string",
                        "description": "Path to the audio file"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name/title for the voice note"
                    },
                    "transcribe": {
                        "type": "boolean",
                        "description": "Whether to transcribe the audio (default: true)"
                    }
                },
                "required": ["audio_path"]
            }
        ),
        Tool(
            name="log_note",
            description="Log a simple text note.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The note content"
                    },
                    "name": {
                        "type": "string",
                        "description": "Optional title for the note"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for the note"
                    }
                },
                "required": ["content"]
            }
        ),
        Tool(
            name="get_today_logs",
            description="Get all logs for today.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_logs_by_date",
            description="Get all logs for a specific date.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format"
                    }
                },
                "required": ["date"]
            }
        ),
        Tool(
            name="get_weekly_summary",
            description="Get a summary of the current week's logs.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_calorie_trends",
            description="Analyze calorie intake trends over time.",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to analyze (default: 30)"
                    }
                }
            }
        ),
        Tool(
            name="get_workout_trends",
            description="Analyze workout frequency and duration trends.",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to analyze (default: 30)"
                    }
                }
            }
        ),
        Tool(
            name="get_weight_trends",
            description="Analyze weight trends over time.",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to analyze (default: 90)"
                    }
                }
            }
        ),
        Tool(
            name="ask_database",
            description="Ask a natural language question about your fitness and diet data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Your question (e.g., 'How many calories did I eat this week?')"
                    }
                },
                "required": ["question"]
            }
        ),
        Tool(
            name="get_insights",
            description="Get personalized insights based on your recent data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to analyze (default: 30)"
                    }
                }
            }
        ),
        Tool(
            name="search_logs",
            description="Search logs with filters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "log_type": {
                        "type": "string",
                        "enum": ["Meal", "Workout", "Weight", "Mood", "Photo", "Voice Note", "Text Note"],
                        "description": "Filter by log type"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 20)"
                    }
                }
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls from Claude."""
    try:
        logger = get_logger()
        analytics = get_analytics()

        if name == "log_meal":
            categories = [arguments.get("category")] if arguments.get("category") else None
            result = logger.log_meal(
                name=arguments["name"],
                categories=categories,
                description=arguments.get("description"),
                calories=arguments.get("calories"),
                protein=arguments.get("protein"),
                photo_path=arguments.get("photo_path"),
                tags=arguments.get("tags"),
            )
            return [TextContent(
                type="text",
                text=f"✅ Meal logged: {arguments['name']}\n"
                     f"📅 Date: {date.today().isoformat()}\n"
                     f"{'🔥 Calories: ' + str(arguments.get('calories')) if arguments.get('calories') else ''}"
            )]

        elif name == "log_workout":
            categories = [arguments.get("category")] if arguments.get("category") else None
            result = logger.log_workout(
                name=arguments["name"],
                categories=categories,
                description=arguments.get("description"),
                duration=arguments.get("duration"),
                calories_burned=arguments.get("calories_burned"),
                mood_score=arguments.get("mood_after"),
                energy_level=arguments.get("energy_after"),
            )
            return [TextContent(
                type="text",
                text=f"💪 Workout logged: {arguments['name']}\n"
                     f"📅 Date: {date.today().isoformat()}\n"
                     f"{'⏱️ Duration: ' + str(arguments.get('duration')) + ' min' if arguments.get('duration') else ''}"
            )]

        elif name == "log_weight":
            result = logger.log_weight(
                weight=arguments["weight"],
                description=arguments.get("notes"),
                mood_score=arguments.get("mood"),
            )
            return [TextContent(
                type="text",
                text=f"⚖️ Weight logged: {arguments['weight']} lbs\n"
                     f"📅 Date: {date.today().isoformat()}"
            )]

        elif name == "log_mood":
            result = logger.log_mood(
                mood_score=arguments["mood"],
                energy_level=arguments.get("energy"),
                description=arguments.get("notes"),
            )
            return [TextContent(
                type="text",
                text=f"😊 Mood logged\n"
                     f"Mood: {arguments['mood']}\n"
                     f"{'Energy: ' + arguments.get('energy') if arguments.get('energy') else ''}"
            )]

        elif name == "log_photo":
            result = logger.log_photo(
                photo_path=arguments["photo_path"],
                name=arguments.get("name"),
                description=arguments.get("description"),
                categories=[arguments.get("category")] if arguments.get("category") else None,
                tags=arguments.get("tags"),
            )
            return [TextContent(
                type="text",
                text=f"📸 Photo logged successfully!\n"
                     f"📅 Date: {date.today().isoformat()}"
            )]

        elif name == "log_voice_note":
            result = logger.log_voice_note(
                audio_path=arguments["audio_path"],
                name=arguments.get("name"),
                transcribe=arguments.get("transcribe", True),
            )
            return [TextContent(
                type="text",
                text=f"🎤 Voice note logged!\n"
                     f"📅 Date: {date.today().isoformat()}"
            )]

        elif name == "log_note":
            result = logger.log_text_note(
                content=arguments["content"],
                name=arguments.get("name"),
                tags=arguments.get("tags"),
            )
            return [TextContent(
                type="text",
                text=f"📝 Note logged!\n"
                     f"📅 Date: {date.today().isoformat()}"
            )]

        elif name == "get_today_logs":
            logs = logger.get_today_logs()
            if not logs:
                return [TextContent(type="text", text="No logs for today yet.")]

            summary = f"📅 Today's Logs ({len(logs)} entries):\n\n"
            for log in logs:
                summary += f"• [{log['type']}] {log['name']}\n"
                if log.get('calories'):
                    summary += f"  Calories: {log['calories']}\n"
                if log.get('duration'):
                    summary += f"  Duration: {log['duration']} min\n"
            return [TextContent(type="text", text=summary)]

        elif name == "get_logs_by_date":
            target_date = date.fromisoformat(arguments["date"])
            logs = logger.get_logs_by_date(target_date)
            if not logs:
                return [TextContent(type="text", text=f"No logs for {arguments['date']}.")]

            summary = f"📅 Logs for {arguments['date']} ({len(logs)} entries):\n\n"
            for log in logs:
                summary += f"• [{log['type']}] {log['name']}\n"
            return [TextContent(type="text", text=summary)]

        elif name == "get_weekly_summary":
            summary = analytics.get_weekly_summary()
            text = f"📊 Weekly Summary ({summary['week_start']} to {summary['week_end']})\n\n"
            text += f"Total entries: {summary['total_entries']}\n"
            text += f"Calories: {summary['totals']['calories']}\n"
            text += f"Protein: {summary['totals']['protein']}g\n"
            text += f"Workouts: {summary['totals']['workouts']}\n"
            text += f"Workout time: {summary['totals']['workout_minutes']} min\n"
            return [TextContent(type="text", text=text)]

        elif name == "get_calorie_trends":
            days = arguments.get("days", 30)
            trends = analytics.get_calorie_trends(days=days)
            text = f"🔥 Calorie Trends ({days} days)\n\n"
            text += f"Average daily: {trends['average_daily']} cal\n"
            text += f"Max day: {trends['max_daily']} cal\n"
            text += f"Min day: {trends['min_daily']} cal\n"
            text += f"Trend: {trends['trend']}\n"
            return [TextContent(type="text", text=text)]

        elif name == "get_workout_trends":
            days = arguments.get("days", 30)
            trends = analytics.get_workout_trends(days=days)
            text = f"💪 Workout Trends ({days} days)\n\n"
            text += f"Total workouts: {trends['total_workouts']}\n"
            text += f"Per week: {trends['workouts_per_week']}\n"
            text += f"Total time: {trends['total_duration_minutes']} min\n"
            text += f"Consistency: {trends['consistency_score']}%\n"
            return [TextContent(type="text", text=text)]

        elif name == "get_weight_trends":
            days = arguments.get("days", 90)
            trends = analytics.get_weight_trends(days=days)
            if trends['current_weight']:
                text = f"⚖️ Weight Trends ({days} days)\n\n"
                text += f"Current: {trends['current_weight']} lbs\n"
                text += f"Starting: {trends['starting_weight']} lbs\n"
                text += f"Change: {trends['change']:+.1f} lbs\n"
                text += f"Trend: {trends['trend']}\n"
            else:
                text = "No weight data found. Start logging your weight!"
            return [TextContent(type="text", text=text)]

        elif name == "ask_database":
            result = analytics.answer_question(arguments["question"])
            return [TextContent(
                type="text",
                text=f"❓ {arguments['question']}\n\n💬 {result['answer']}"
            )]

        elif name == "get_insights":
            days = arguments.get("days", 30)
            insights = analytics.get_insights(days=days)
            text = f"💡 Insights (last {days} days):\n\n"
            for insight in insights:
                text += f"{insight}\n"
            return [TextContent(type="text", text=text)]

        elif name == "search_logs":
            start = date.fromisoformat(arguments["start_date"]) if arguments.get("start_date") else None
            end = date.fromisoformat(arguments["end_date"]) if arguments.get("end_date") else None
            logs = logger.search_logs(
                log_type=arguments.get("log_type"),
                tags=arguments.get("tags"),
                start_date=start,
                end_date=end,
                limit=arguments.get("limit", 20),
            )
            if not logs:
                return [TextContent(type="text", text="No logs found matching your criteria.")]

            text = f"🔍 Search Results ({len(logs)} found):\n\n"
            for log in logs:
                text += f"• [{log['date']}] [{log['type']}] {log['name']}\n"
            return [TextContent(type="text", text=text)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@server.list_prompts()
async def list_prompts() -> List[Prompt]:
    """List available prompts."""
    return [
        Prompt(
            name="daily-checkin",
            description="Guided daily check-in for logging meals, mood, and activities",
            arguments=[],
        ),
        Prompt(
            name="weekly-review",
            description="Review your week's progress and get insights",
            arguments=[],
        ),
        Prompt(
            name="log-meal-helper",
            description="Help log a meal with nutritional estimates",
            arguments=[
                {"name": "meal_description", "description": "Describe what you ate"}
            ],
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
                        text="""Let's do a daily check-in! Please help me log:

1. **Meals**: What have you eaten today? I'll help estimate calories and protein.

2. **Activity**: Did you work out or do any physical activity?

3. **Wellness**: How are you feeling? (mood and energy level)

4. **Weight**: Did you weigh yourself today?

Let's start with meals - what did you have for breakfast?"""
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
                        text="""Please give me a comprehensive weekly review:

1. First, get my weekly summary
2. Then show me calorie trends
3. Show workout trends
4. Show any weight changes
5. Give me personalized insights

I want to understand how I did this week and what I can improve."""
                    )
                )
            ]
        )

    elif name == "log-meal-helper":
        meal_desc = arguments.get("meal_description", "my meal") if arguments else "my meal"
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""I want to log this meal: {meal_desc}

Please help me:
1. Estimate the calories
2. Estimate the protein content
3. Suggest appropriate tags (healthy, high protein, etc.)
4. Log it using the log_meal tool

Be reasonable with estimates based on typical portions."""
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
