#!/usr/bin/env python3
"""
Command Line Interface for the Fitness & Diet Logger.
Provides interactive commands for logging and viewing data.
"""
import click
from datetime import date, datetime
from pathlib import Path
from typing import Optional
import json

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.markdown import Markdown
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from .logger import FitnessDietLogger
from .analytics import LogAnalytics


console = Console() if HAS_RICH else None


def print_output(text: str, style: str = None):
    """Print output with optional styling."""
    if console:
        console.print(text, style=style)
    else:
        print(text)


def print_success(text: str):
    """Print success message."""
    print_output(f"✅ {text}", style="green")


def print_error(text: str):
    """Print error message."""
    print_output(f"❌ {text}", style="red")


def print_table(title: str, data: list, columns: list):
    """Print data as a table."""
    if console:
        table = Table(title=title)
        for col in columns:
            table.add_column(col)
        for row in data:
            table.add_row(*[str(v) for v in row])
        console.print(table)
    else:
        print(f"\n{title}")
        print("-" * 50)
        for row in data:
            print(" | ".join(str(v) for v in row))


@click.group()
@click.pass_context
def cli(ctx):
    """Fitness & Diet Logger - Track your health journey."""
    ctx.ensure_object(dict)
    try:
        ctx.obj['logger'] = FitnessDietLogger()
        ctx.obj['analytics'] = LogAnalytics(ctx.obj['logger'].notion)
    except ValueError as e:
        print_error(f"Configuration error: {e}")
        print_output("Set NOTION_API_KEY and NOTION_DATABASE_ID environment variables.")
        ctx.exit(1)


@cli.command()
@click.argument('name')
@click.option('--category', '-c', type=click.Choice(['Breakfast', 'Lunch', 'Dinner', 'Snack']),
              help='Meal category')
@click.option('--calories', '-cal', type=int, help='Calorie count')
@click.option('--protein', '-p', type=float, help='Protein in grams')
@click.option('--description', '-d', help='Meal description')
@click.option('--photo', type=click.Path(exists=True), help='Path to meal photo')
@click.option('--tags', '-t', multiple=True, help='Tags (can be used multiple times)')
@click.pass_context
def meal(ctx, name, category, calories, protein, description, photo, tags):
    """Log a meal."""
    try:
        logger = ctx.obj['logger']
        result = logger.log_meal(
            name=name,
            categories=[category] if category else None,
            calories=calories,
            protein=protein,
            description=description,
            photo_path=photo,
            tags=list(tags) if tags else None,
        )
        print_success(f"Logged meal: {name}")
        if calories:
            print_output(f"  Calories: {calories}")
        if protein:
            print_output(f"  Protein: {protein}g")
    except Exception as e:
        print_error(f"Failed to log meal: {e}")


@cli.command()
@click.argument('name')
@click.option('--category', '-c', type=click.Choice(['Cardio', 'Strength', 'Flexibility']),
              help='Workout category')
@click.option('--duration', '-dur', type=int, help='Duration in minutes')
@click.option('--calories', '-cal', type=int, help='Calories burned')
@click.option('--description', '-d', help='Workout description')
@click.option('--mood', type=click.Choice(['1 - Very Low', '2 - Low', '3 - Neutral', '4 - Good', '5 - Excellent']),
              help='Mood after workout')
@click.pass_context
def workout(ctx, name, category, duration, calories, description, mood):
    """Log a workout."""
    try:
        logger = ctx.obj['logger']
        result = logger.log_workout(
            name=name,
            categories=[category] if category else None,
            duration=duration,
            calories_burned=calories,
            description=description,
            mood_score=mood,
        )
        print_success(f"Logged workout: {name}")
        if duration:
            print_output(f"  Duration: {duration} minutes")
    except Exception as e:
        print_error(f"Failed to log workout: {e}")


@cli.command()
@click.argument('weight', type=float)
@click.option('--notes', '-n', help='Optional notes')
@click.option('--mood', type=click.Choice(['1 - Very Low', '2 - Low', '3 - Neutral', '4 - Good', '5 - Excellent']),
              help='Current mood')
@click.pass_context
def weight(ctx, weight, notes, mood):
    """Log your weight."""
    try:
        logger = ctx.obj['logger']
        result = logger.log_weight(
            weight=weight,
            description=notes,
            mood_score=mood,
        )
        print_success(f"Logged weight: {weight} lbs")
    except Exception as e:
        print_error(f"Failed to log weight: {e}")


@cli.command()
@click.option('--mood', '-m', type=click.Choice(['1 - Very Low', '2 - Low', '3 - Neutral', '4 - Good', '5 - Excellent']),
              required=True, help='Mood score')
@click.option('--energy', '-e', type=click.Choice(['1 - Exhausted', '2 - Tired', '3 - Normal', '4 - Energetic', '5 - Peak']),
              help='Energy level')
@click.option('--notes', '-n', help='How you\'re feeling')
@click.pass_context
def mood(ctx, mood, energy, notes):
    """Log your mood and energy."""
    try:
        logger = ctx.obj['logger']
        result = logger.log_mood(
            mood_score=mood,
            energy_level=energy,
            description=notes,
        )
        print_success(f"Logged mood: {mood}")
        if energy:
            print_output(f"  Energy: {energy}")
    except Exception as e:
        print_error(f"Failed to log mood: {e}")


@cli.command()
@click.argument('photo_path', type=click.Path(exists=True))
@click.option('--name', '-n', help='Name for the photo')
@click.option('--description', '-d', help='Description')
@click.option('--category', '-c', type=click.Choice(['Progress', 'Meal', 'Workout']),
              help='Photo category')
@click.pass_context
def photo(ctx, photo_path, name, description, category):
    """Log a photo."""
    try:
        logger = ctx.obj['logger']
        result = logger.log_photo(
            photo_path=photo_path,
            name=name,
            description=description,
            categories=[category] if category else None,
        )
        print_success(f"Logged photo: {photo_path}")
    except Exception as e:
        print_error(f"Failed to log photo: {e}")


@cli.command()
@click.argument('audio_path', type=click.Path(exists=True))
@click.option('--name', '-n', help='Name for the voice note')
@click.option('--no-transcribe', is_flag=True, help='Skip transcription')
@click.pass_context
def voice(ctx, audio_path, name, no_transcribe):
    """Log a voice note."""
    try:
        logger = ctx.obj['logger']
        result = logger.log_voice_note(
            audio_path=audio_path,
            name=name,
            transcribe=not no_transcribe,
        )
        print_success(f"Logged voice note: {audio_path}")
    except Exception as e:
        print_error(f"Failed to log voice note: {e}")


@cli.command()
@click.argument('content')
@click.option('--name', '-n', help='Name for the note')
@click.option('--tags', '-t', multiple=True, help='Tags')
@click.pass_context
def note(ctx, content, name, tags):
    """Log a text note."""
    try:
        logger = ctx.obj['logger']
        result = logger.log_text_note(
            content=content,
            name=name,
            tags=list(tags) if tags else None,
        )
        print_success("Logged note")
    except Exception as e:
        print_error(f"Failed to log note: {e}")


@cli.command()
@click.pass_context
def today(ctx):
    """Show today's logs."""
    try:
        logger = ctx.obj['logger']
        logs = logger.get_today_logs()

        if not logs:
            print_output("No logs for today yet.")
            return

        print_output(f"\n📅 Today's Logs ({len(logs)} entries)\n")

        for log in logs:
            print_output(f"[{log['type']}] {log['name']}")
            if log.get('calories'):
                print_output(f"  🔥 Calories: {log['calories']}")
            if log.get('protein'):
                print_output(f"  🥩 Protein: {log['protein']}g")
            if log.get('duration'):
                print_output(f"  ⏱️ Duration: {log['duration']} min")
            if log.get('weight'):
                print_output(f"  ⚖️ Weight: {log['weight']} lbs")
            print_output("")

    except Exception as e:
        print_error(f"Failed to get today's logs: {e}")


@cli.command()
@click.pass_context
def summary(ctx):
    """Show weekly summary."""
    try:
        analytics = ctx.obj['analytics']
        summary = analytics.get_weekly_summary()

        print_output(f"\n📊 Weekly Summary")
        print_output(f"📅 {summary['week_start']} to {summary['week_end']}\n")
        print_output(f"Total entries: {summary['total_entries']}")
        print_output(f"🔥 Total calories: {summary['totals']['calories']}")
        print_output(f"🥩 Total protein: {summary['totals']['protein']}g")
        print_output(f"💪 Workouts: {summary['totals']['workouts']}")
        print_output(f"⏱️ Workout time: {summary['totals']['workout_minutes']} min")

        if summary['averages']:
            print_output(f"\n📈 Daily Averages:")
            print_output(f"  Calories: {summary['averages'].get('calories_per_day', 0)}")
            print_output(f"  Protein: {summary['averages'].get('protein_per_day', 0)}g")

    except Exception as e:
        print_error(f"Failed to get summary: {e}")


@cli.command()
@click.option('--days', '-d', type=int, default=30, help='Number of days to analyze')
@click.pass_context
def trends(ctx, days):
    """Show trends and analytics."""
    try:
        analytics = ctx.obj['analytics']

        print_output(f"\n📈 Trends (Last {days} days)\n")

        # Calories
        cal = analytics.get_calorie_trends(days=days)
        print_output("🔥 Calories:")
        print_output(f"  Average: {cal['average_daily']}/day")
        print_output(f"  Trend: {cal['trend']}")

        # Workouts
        work = analytics.get_workout_trends(days=days)
        print_output("\n💪 Workouts:")
        print_output(f"  Total: {work['total_workouts']}")
        print_output(f"  Per week: {work['workouts_per_week']}")
        print_output(f"  Consistency: {work['consistency_score']}%")

        # Weight
        wt = analytics.get_weight_trends(days=days)
        if wt['current_weight']:
            print_output("\n⚖️ Weight:")
            print_output(f"  Current: {wt['current_weight']} lbs")
            print_output(f"  Change: {wt['change']:+.1f} lbs")
            print_output(f"  Trend: {wt['trend']}")

    except Exception as e:
        print_error(f"Failed to get trends: {e}")


@cli.command()
@click.argument('question')
@click.pass_context
def ask(ctx, question):
    """Ask a question about your data."""
    try:
        analytics = ctx.obj['analytics']
        result = analytics.answer_question(question)

        print_output(f"\n❓ {question}\n")
        print_output(f"💬 {result['answer']}")

    except Exception as e:
        print_error(f"Failed to answer question: {e}")


@cli.command()
@click.option('--days', '-d', type=int, default=30, help='Number of days to analyze')
@click.pass_context
def insights(ctx, days):
    """Get personalized insights."""
    try:
        analytics = ctx.obj['analytics']
        insights = analytics.get_insights(days=days)

        print_output(f"\n💡 Insights (Last {days} days)\n")
        for insight in insights:
            print_output(insight)

    except Exception as e:
        print_error(f"Failed to get insights: {e}")


@cli.command()
@click.option('--type', '-t', 'log_type',
              type=click.Choice(['Meal', 'Workout', 'Weight', 'Mood', 'Photo', 'Voice Note', 'Text Note']),
              help='Filter by type')
@click.option('--start', '-s', help='Start date (YYYY-MM-DD)')
@click.option('--end', '-e', help='End date (YYYY-MM-DD)')
@click.option('--limit', '-l', type=int, default=20, help='Max results')
@click.pass_context
def search(ctx, log_type, start, end, limit):
    """Search logs."""
    try:
        logger = ctx.obj['logger']

        start_date = date.fromisoformat(start) if start else None
        end_date = date.fromisoformat(end) if end else None

        logs = logger.search_logs(
            log_type=log_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        if not logs:
            print_output("No logs found matching your criteria.")
            return

        print_output(f"\n🔍 Search Results ({len(logs)} found)\n")
        for log in logs:
            print_output(f"[{log['date']}] [{log['type']}] {log['name']}")

    except Exception as e:
        print_error(f"Search failed: {e}")


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == '__main__':
    main()
