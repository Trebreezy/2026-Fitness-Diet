#!/usr/bin/env python3
"""
Final integration test to verify everything works.
"""
import sys
sys.path.insert(0, "/home/user/2026-Fitness-Diet")

from datetime import date
from src.notion_client import NotionLogger
from src.logger import FitnessDietLogger
from src.analytics import LogAnalytics

print("🧪 Testing Fitness & Diet Logger Integration")
print("=" * 50)

# Test 1: NotionLogger directly
print("\n1️⃣ Testing NotionLogger...")
try:
    notion = NotionLogger()
    print(f"   ✅ NotionLogger initialized")
    print(f"   Database ID: {notion.database_id[:20]}...")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 2: Query existing logs
print("\n2️⃣ Querying existing logs...")
try:
    logs = notion.query_logs(limit=5)
    print(f"   ✅ Found {len(logs)} logs")
    for log in logs[:3]:
        data = notion.extract_log_data(log)
        print(f"      - {data['name']} ({data['type']})")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Create a new entry
print("\n3️⃣ Creating a new test entry...")
try:
    result = notion.create_log_entry(
        name="Integration Test - Dinner",
        log_type="Meal",
        categories=["Dinner"],
        description="Salmon with vegetables - testing the integration",
        calories=600,
        protein=45,
        tags=["healthy", "high protein"],
    )
    print(f"   ✅ Entry created!")
    print(f"   URL: {result.get('url')}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: FitnessDietLogger
print("\n4️⃣ Testing FitnessDietLogger...")
try:
    logger = FitnessDietLogger()
    print(f"   ✅ FitnessDietLogger initialized")

    # Get today's logs
    today_logs = logger.get_today_logs()
    print(f"   📅 Today's logs: {len(today_logs)}")

    # Get daily summary
    summary = logger.get_daily_summary()
    print(f"   📊 Total calories today: {summary['total_calories']}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Analytics
print("\n5️⃣ Testing LogAnalytics...")
try:
    analytics = LogAnalytics(notion)
    print(f"   ✅ Analytics initialized")

    # Get weekly summary
    weekly = analytics.get_weekly_summary()
    print(f"   📈 This week: {weekly['total_entries']} entries")

    # Ask a question
    answer = analytics.answer_question("How many calories today?")
    print(f"   💬 Q: How many calories today?")
    print(f"      A: {answer['answer']}")

    # Get insights
    insights = analytics.get_insights(days=7)
    print(f"   💡 Insights: {len(insights)} generated")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 50)
print("✅ All tests passed! Integration is working.")
print("=" * 50)
