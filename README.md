# Fitness & Diet Logger

A comprehensive system for tracking fitness and diet data through photos, voice notes, and text entries - all synced to a Notion calendar database with Claude Code integration.

## Features

- **Photo Logging**: Take photos of meals, progress pics, or workouts and log them to Notion
- **Voice Notes**: Record voice memos that get transcribed and saved
- **Text Notes**: Quick text entries for any observations
- **Notion Calendar**: All logs land on their recording date in a calendar view
- **Trend Analysis**: See patterns in calories, workouts, weight, and mood
- **Natural Language Queries**: Ask questions about your data
- **Claude Code Integration**: Use Claude to log entries conversationally via MCP

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Notion

1. Go to [Notion Integrations](https://www.notion.so/my-integrations) and create a new integration
2. Copy the API key
3. Create a new page in Notion where your database will live
4. Share the page with your integration (click Share → Invite → select your integration)
5. Copy the `.env.example` to `.env` and add your credentials:

```bash
cp .env.example .env
# Edit .env with your API key and page ID
```

### 3. Create the Database

The system will create the database automatically on first use, or you can create it manually with these properties:

| Property | Type | Description |
|----------|------|-------------|
| Name | Title | Entry name |
| Date | Date | Log date (used for calendar view) |
| Type | Select | Photo, Voice Note, Text Note, Meal, Workout, Weight, Mood |
| Category | Multi-select | Breakfast, Lunch, Dinner, Snack, Cardio, Strength, Flexibility, Progress |
| Description | Rich Text | Detailed description |
| Calories | Number | Calorie count |
| Protein (g) | Number | Protein in grams |
| Duration (min) | Number | Workout duration |
| Weight (lbs) | Number | Body weight |
| Mood Score | Select | 1-5 scale |
| Energy Level | Select | 1-5 scale |
| Image URL | URL | Link to photo |
| Transcription | Rich Text | Voice note transcription |
| Tags | Multi-select | Custom tags |

**Important**: Set your Notion database to **Calendar View** for the best experience!

## Usage

### Claude Code Integration (MCP Server)

The most powerful way to use this system is through Claude Code. Add the MCP server to your Claude Code configuration:

**~/.claude/settings.json:**
```json
{
  "mcpServers": {
    "fitness-diet-logger": {
      "command": "python",
      "args": ["/path/to/2026-Fitness-Diet/mcp_server/server.py"],
      "env": {
        "NOTION_API_KEY": "your-notion-api-key",
        "NOTION_DATABASE_ID": "your-database-id"
      }
    }
  }
}
```

Then just talk to Claude naturally:

```
"Log my breakfast - I had scrambled eggs with avocado toast, about 450 calories"

"I just did a 30-minute run, feeling great!"

"How many calories did I eat this week?"

"Show me my workout trends"

"Log my weight: 175 lbs"
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `log_meal` | Log a meal with calories, protein, photo |
| `log_workout` | Log exercise with duration and intensity |
| `log_weight` | Record your weight |
| `log_mood` | Track mood and energy levels |
| `log_photo` | Log a photo to your calendar |
| `log_voice_note` | Record and transcribe a voice note |
| `log_note` | Quick text note |
| `get_today_logs` | View all entries for today |
| `get_weekly_summary` | Get weekly statistics |
| `get_calorie_trends` | Analyze calorie patterns |
| `get_workout_trends` | Analyze exercise habits |
| `get_weight_trends` | Track weight changes |
| `ask_database` | Natural language queries |
| `get_insights` | Get personalized recommendations |
| `search_logs` | Search with filters |

### Command Line Interface

You can also use the CLI directly:

```bash
# Log a meal
fitness-log meal "Chicken Salad" --category Lunch --calories 450 --protein 35

# Log a workout
fitness-log workout "Morning Run" --category Cardio --duration 30

# Log your weight
fitness-log weight 175

# Log your mood
fitness-log mood --mood "4 - Good" --energy "4 - Energetic"

# View today's logs
fitness-log today

# Get weekly summary
fitness-log summary

# View trends
fitness-log trends --days 30

# Ask a question
fitness-log ask "How many workouts did I do this week?"

# Get insights
fitness-log insights
```

### Python API

```python
from src import FitnessDietLogger, LogAnalytics

# Initialize
logger = FitnessDietLogger()

# Log a meal
logger.log_meal(
    name="Grilled Salmon",
    categories=["Dinner"],
    calories=520,
    protein=45,
    tags=["healthy", "high protein"]
)

# Log a workout
logger.log_workout(
    name="Upper Body Strength",
    categories=["Strength"],
    duration=45,
    description="Bench press, rows, shoulder press"
)

# Log a voice note
logger.log_voice_note(
    audio_path="/path/to/voice_note.wav",
    transcribe=True
)

# Get analytics
analytics = LogAnalytics(logger.notion)

# Check trends
calories = analytics.get_calorie_trends(days=30)
print(f"Average daily calories: {calories['average_daily']}")

# Ask questions
result = analytics.answer_question("How many workouts did I do this week?")
print(result['answer'])
```

## Notion Calendar Setup

For the best experience, set up your Notion database with a **Calendar View**:

1. Open your database in Notion
2. Click **+ Add a view** → **Calendar**
3. Set the **Date** property as the calendar date field
4. Customize the card preview to show Type, Calories, etc.

Now all your logs will appear on the calendar on the day they were recorded!

## Trends and Analytics

The system provides comprehensive analytics:

### Calorie Trends
- Daily averages
- Trend direction (increasing/decreasing/stable)
- High and low days

### Workout Trends
- Total workouts and frequency
- Workouts per week
- Category breakdown (Cardio, Strength, Flexibility)
- Consistency score

### Weight Trends
- Current vs starting weight
- Total change over time
- Trend direction

### Mood & Energy
- Average mood and energy scores
- Daily patterns

### Insights
The system generates personalized insights like:
- "Great workout consistency! Keep it up!"
- "Your calorie intake has been increasing lately."
- "Excellent! You're working out 5+ times per week!"

## Project Structure

```
2026-Fitness-Diet/
├── src/
│   ├── __init__.py
│   ├── notion_client.py    # Notion API wrapper
│   ├── logger.py           # Main logging interface
│   ├── photo_handler.py    # Photo processing
│   ├── voice_handler.py    # Voice note handling
│   ├── analytics.py        # Trends and insights
│   └── cli.py              # Command line interface
├── mcp_server/
│   ├── __init__.py
│   └── server.py           # MCP server for Claude Code
├── config/
│   ├── __init__.py
│   └── settings.py         # Configuration
├── data/                   # Local data storage
│   ├── uploads/            # Processed photos
│   └── voice_notes/        # Voice recordings
├── requirements.txt
├── setup.py
├── .env.example
└── README.md
```

## Requirements

- Python 3.9+
- Notion account with API access
- For voice transcription: microphone and internet connection

## Optional Dependencies

- **Pillow**: For image processing and optimization
- **SpeechRecognition + pydub**: For voice note transcription
- **pandas**: For data export to DataFrames
- **rich**: For beautiful CLI output

## Troubleshooting

### "Notion API key is required"
Make sure you've set the `NOTION_API_KEY` environment variable or created a `.env` file.

### "Database ID is required"
Set the `NOTION_DATABASE_ID` environment variable. You can find this in your Notion database URL.

### "Failed to create log entry"
- Make sure your integration has access to the database (Share → Invite integration)
- Check that all required properties exist in the database

### Voice transcription not working
- Install: `pip install SpeechRecognition pydub`
- For non-WAV files, you may need ffmpeg: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux)

## License

MIT License - Feel free to use and modify!
