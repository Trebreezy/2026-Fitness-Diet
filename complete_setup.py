#!/usr/bin/env python3
"""
Complete setup using direct Notion API with proper version header.
"""
import os
import json
import httpx
from datetime import date
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("NOTION_API_KEY")
parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

print("=" * 60)
print("🏋️ Fitness & Diet Logger - Complete Setup")
print("=" * 60)

# Create the full database
print("\n1️⃣ Creating Fitness & Diet database...")

db_payload = {
    "parent": {"type": "page_id", "page_id": parent_page_id},
    "title": [{"type": "text", "text": {"content": "Fitness & Diet Log"}}],
    "properties": {
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
                    {"name": "hydration", "color": "default"},
                    {"name": "sleep", "color": "purple"},
                ]
            }
        },
    }
}

response = httpx.post(
    "https://api.notion.com/v1/databases",
    headers=headers,
    json=db_payload,
    timeout=30
)

if response.status_code != 200:
    print(f"   ❌ Failed to create database: {response.text}")
    exit(1)

db_data = response.json()
database_id = db_data["id"]
print(f"   ✅ Database created!")
print(f"   ID: {database_id}")
print(f"   Properties: {list(db_data.get('properties', {}).keys())}")

# Update .env file
env_path = "/home/user/2026-Fitness-Diet/.env"
with open(env_path, "r") as f:
    content = f.read()

import re
content = re.sub(r'NOTION_DATABASE_ID=.*', f'NOTION_DATABASE_ID={database_id}', content)
with open(env_path, "w") as f:
    f.write(content)
print(f"   ✅ Updated .env with new database ID")

# Create sample entries
print("\n2️⃣ Creating sample entries...")
today = date.today()

entries = [
    {
        "name": "🎉 Welcome!",
        "props": {
            "Name": {"title": [{"text": {"content": "🎉 Welcome to Fitness & Diet Log!"}}]},
            "Date": {"date": {"start": today.isoformat()}},
            "Type": {"select": {"name": "Text Note"}},
            "Description": {"rich_text": [{"text": {"content": "Your Notion integration is working! This database tracks meals, workouts, weight, mood, photos, and voice notes. Try adding a Calendar view!"}}]},
        }
    },
    {
        "name": "Oatmeal with Berries (Breakfast)",
        "props": {
            "Name": {"title": [{"text": {"content": "Oatmeal with Berries"}}]},
            "Date": {"date": {"start": today.isoformat()}},
            "Type": {"select": {"name": "Meal"}},
            "Category": {"multi_select": [{"name": "Breakfast"}]},
            "Description": {"rich_text": [{"text": {"content": "Steel-cut oats with fresh blueberries, strawberries, and a drizzle of honey."}}]},
            "Calories": {"number": 350},
            "Protein (g)": {"number": 12},
            "Tags": {"multi_select": [{"name": "healthy"}]},
        }
    },
    {
        "name": "Grilled Chicken Salad (Lunch)",
        "props": {
            "Name": {"title": [{"text": {"content": "Grilled Chicken Salad"}}]},
            "Date": {"date": {"start": today.isoformat()}},
            "Type": {"select": {"name": "Meal"}},
            "Category": {"multi_select": [{"name": "Lunch"}]},
            "Description": {"rich_text": [{"text": {"content": "Mixed greens with grilled chicken breast, cherry tomatoes, cucumber, and balsamic vinaigrette."}}]},
            "Calories": {"number": 450},
            "Protein (g)": {"number": 42},
            "Tags": {"multi_select": [{"name": "healthy"}, {"name": "high protein"}]},
        }
    },
    {
        "name": "Morning Run - 5K",
        "props": {
            "Name": {"title": [{"text": {"content": "Morning Run - 5K"}}]},
            "Date": {"date": {"start": today.isoformat()}},
            "Type": {"select": {"name": "Workout"}},
            "Category": {"multi_select": [{"name": "Cardio"}]},
            "Description": {"rich_text": [{"text": {"content": "Easy 5K run around the neighborhood. Good pace, felt strong throughout."}}]},
            "Duration (min)": {"number": 30},
            "Calories": {"number": 320},
            "Mood Score": {"select": {"name": "4 - Good"}},
            "Energy Level": {"select": {"name": "4 - Energetic"}},
        }
    },
    {
        "name": "Voice Note - Motivation",
        "props": {
            "Name": {"title": [{"text": {"content": "Voice Note - Feeling motivated!"}}]},
            "Date": {"date": {"start": today.isoformat()}},
            "Type": {"select": {"name": "Voice Note"}},
            "Transcription": {"rich_text": [{"text": {"content": "Just finished my morning routine. Feeling really motivated today! Had a great workout and planning to eat clean. Let's keep this momentum going all week!"}}]},
            "Mood Score": {"select": {"name": "5 - Excellent"}},
            "Energy Level": {"select": {"name": "5 - Peak"}},
        }
    },
    {
        "name": "Weight Check",
        "props": {
            "Name": {"title": [{"text": {"content": f"Weight: 175 lbs - {today.strftime('%b %d')}"}}]},
            "Date": {"date": {"start": today.isoformat()}},
            "Type": {"select": {"name": "Weight"}},
            "Weight (lbs)": {"number": 175},
            "Mood Score": {"select": {"name": "4 - Good"}},
        }
    },
]

success_count = 0
for entry in entries:
    entry_response = httpx.post(
        "https://api.notion.com/v1/pages",
        headers=headers,
        json={"parent": {"database_id": database_id}, "properties": entry["props"]},
        timeout=30
    )
    if entry_response.status_code == 200:
        print(f"   ✅ {entry['name']}")
        success_count += 1
    else:
        print(f"   ❌ {entry['name']}: {entry_response.text[:100]}")

print(f"\n   Created {success_count}/{len(entries)} entries")

# Query the database to verify
print("\n3️⃣ Verifying database...")
query_response = httpx.post(
    f"https://api.notion.com/v1/databases/{database_id}/query",
    headers=headers,
    json={},
    timeout=30
)

if query_response.status_code == 200:
    results = query_response.json().get("results", [])
    print(f"   ✅ Found {len(results)} entries in database")
else:
    print(f"   ⚠️ Could not verify: {query_response.status_code}")

# Get the database URL
db_url = f"https://www.notion.so/{database_id.replace('-', '')}"

print("\n" + "=" * 60)
print("✅ SETUP COMPLETE!")
print("=" * 60)
print(f"""
Your Fitness & Diet Logger is ready!

📊 Database: Fitness & Diet Log
📝 Entries: {success_count} sample entries created
🔗 URL: {db_url}

📋 Database Properties:
   - Name (title)
   - Date (for calendar view)
   - Type (Meal, Workout, Weight, Mood, Photo, Voice Note, Text Note)
   - Category (Breakfast, Lunch, Dinner, Snack, Cardio, Strength, etc.)
   - Calories, Protein (g), Duration (min), Weight (lbs)
   - Mood Score, Energy Level
   - Tags, Description, Transcription, Image URL

🗓️ Next Steps:
   1. Open the database in Notion
   2. Click "+ Add a view" → "Calendar" to see the calendar view
   3. Start logging with Claude!

Example commands to try with Claude:
   • "Log my breakfast: eggs and toast, 400 calories"
   • "I just did a 45-minute strength workout"
   • "Log my weight: 180 lbs"
   • "How many calories have I eaten today?"

Database ID: {database_id}
""")
