"""
Food database with keto/slow-carb approved foods.
Includes calorie, protein, carb, and fat estimates.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class FoodItem:
    name: str
    calories: int  # per serving
    protein: float  # grams
    carbs: float  # grams (net carbs for keto)
    fat: float  # grams
    serving_size: str
    keto_friendly: bool
    slow_carb_friendly: bool
    category: str  # protein, vegetable, fat, legume, dairy, etc.
    aliases: List[str] = None

    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []


# Comprehensive food database focused on keto and slow-carb approved foods
FOOD_DATABASE: Dict[str, FoodItem] = {
    # === PROTEINS ===
    "chicken breast": FoodItem(
        name="Chicken Breast (grilled)",
        calories=165, protein=31, carbs=0, fat=3.6,
        serving_size="4 oz (113g)",
        keto_friendly=True, slow_carb_friendly=True,
        category="protein",
        aliases=["grilled chicken", "chicken", "chicken breast"]
    ),
    "chicken thigh": FoodItem(
        name="Chicken Thigh",
        calories=209, protein=26, carbs=0, fat=11,
        serving_size="4 oz (113g)",
        keto_friendly=True, slow_carb_friendly=True,
        category="protein"
    ),
    "steak": FoodItem(
        name="Beef Steak (ribeye)",
        calories=291, protein=24, carbs=0, fat=21,
        serving_size="4 oz (113g)",
        keto_friendly=True, slow_carb_friendly=True,
        category="protein",
        aliases=["ribeye", "beef", "beef steak"]
    ),
    "ground beef": FoodItem(
        name="Ground Beef (80/20)",
        calories=287, protein=19, carbs=0, fat=23,
        serving_size="4 oz (113g)",
        keto_friendly=True, slow_carb_friendly=True,
        category="protein"
    ),
    "salmon": FoodItem(
        name="Salmon (Atlantic)",
        calories=208, protein=20, carbs=0, fat=13,
        serving_size="4 oz (113g)",
        keto_friendly=True, slow_carb_friendly=True,
        category="protein",
        aliases=["atlantic salmon", "grilled salmon"]
    ),
    "tuna": FoodItem(
        name="Tuna (canned in water)",
        calories=100, protein=22, carbs=0, fat=1,
        serving_size="4 oz (113g)",
        keto_friendly=True, slow_carb_friendly=True,
        category="protein"
    ),
    "shrimp": FoodItem(
        name="Shrimp",
        calories=99, protein=24, carbs=0, fat=0.3,
        serving_size="4 oz (113g)",
        keto_friendly=True, slow_carb_friendly=True,
        category="protein"
    ),
    "eggs": FoodItem(
        name="Eggs (whole)",
        calories=78, protein=6, carbs=0.6, fat=5,
        serving_size="1 large egg",
        keto_friendly=True, slow_carb_friendly=True,
        category="protein",
        aliases=["egg", "scrambled eggs", "fried eggs", "boiled eggs"]
    ),
    "pork chop": FoodItem(
        name="Pork Chop",
        calories=231, protein=25, carbs=0, fat=14,
        serving_size="4 oz (113g)",
        keto_friendly=True, slow_carb_friendly=True,
        category="protein"
    ),
    "bacon": FoodItem(
        name="Bacon",
        calories=161, protein=12, carbs=0.6, fat=12,
        serving_size="3 slices (35g)",
        keto_friendly=True, slow_carb_friendly=True,
        category="protein"
    ),
    "turkey": FoodItem(
        name="Turkey Breast",
        calories=135, protein=30, carbs=0, fat=1,
        serving_size="4 oz (113g)",
        keto_friendly=True, slow_carb_friendly=True,
        category="protein",
        aliases=["turkey breast", "sliced turkey"]
    ),

    # === VEGETABLES (Low-Carb) ===
    "spinach": FoodItem(
        name="Spinach",
        calories=7, protein=0.9, carbs=1.1, fat=0.1,
        serving_size="1 cup raw",
        keto_friendly=True, slow_carb_friendly=True,
        category="vegetable"
    ),
    "broccoli": FoodItem(
        name="Broccoli",
        calories=55, protein=3.7, carbs=6, fat=0.6,
        serving_size="1 cup chopped",
        keto_friendly=True, slow_carb_friendly=True,
        category="vegetable"
    ),
    "cauliflower": FoodItem(
        name="Cauliflower",
        calories=27, protein=2.1, carbs=3, fat=0.3,
        serving_size="1 cup",
        keto_friendly=True, slow_carb_friendly=True,
        category="vegetable"
    ),
    "asparagus": FoodItem(
        name="Asparagus",
        calories=27, protein=2.9, carbs=3, fat=0.2,
        serving_size="1 cup",
        keto_friendly=True, slow_carb_friendly=True,
        category="vegetable"
    ),
    "zucchini": FoodItem(
        name="Zucchini",
        calories=21, protein=1.5, carbs=3.9, fat=0.4,
        serving_size="1 cup sliced",
        keto_friendly=True, slow_carb_friendly=True,
        category="vegetable"
    ),
    "bell pepper": FoodItem(
        name="Bell Pepper",
        calories=31, protein=1, carbs=6, fat=0.3,
        serving_size="1 medium",
        keto_friendly=True, slow_carb_friendly=True,
        category="vegetable",
        aliases=["peppers", "red pepper", "green pepper"]
    ),
    "mushrooms": FoodItem(
        name="Mushrooms",
        calories=22, protein=3.1, carbs=3.3, fat=0.3,
        serving_size="1 cup sliced",
        keto_friendly=True, slow_carb_friendly=True,
        category="vegetable"
    ),
    "lettuce": FoodItem(
        name="Lettuce (Romaine)",
        calories=8, protein=0.6, carbs=1.5, fat=0.1,
        serving_size="1 cup shredded",
        keto_friendly=True, slow_carb_friendly=True,
        category="vegetable",
        aliases=["romaine", "salad greens", "mixed greens"]
    ),
    "kale": FoodItem(
        name="Kale",
        calories=33, protein=2.2, carbs=6, fat=0.5,
        serving_size="1 cup chopped",
        keto_friendly=True, slow_carb_friendly=True,
        category="vegetable"
    ),
    "cucumber": FoodItem(
        name="Cucumber",
        calories=16, protein=0.7, carbs=3.8, fat=0.1,
        serving_size="1 cup sliced",
        keto_friendly=True, slow_carb_friendly=True,
        category="vegetable"
    ),
    "tomato": FoodItem(
        name="Tomato",
        calories=22, protein=1.1, carbs=4.8, fat=0.2,
        serving_size="1 medium",
        keto_friendly=True, slow_carb_friendly=True,
        category="vegetable",
        aliases=["tomatoes", "cherry tomatoes"]
    ),
    "avocado": FoodItem(
        name="Avocado",
        calories=234, protein=2.9, carbs=3, fat=21,
        serving_size="1 medium",
        keto_friendly=True, slow_carb_friendly=True,
        category="vegetable",  # technically a fruit but fits here
        aliases=["guacamole", "guac"]
    ),
    "green beans": FoodItem(
        name="Green Beans",
        calories=31, protein=1.8, carbs=7, fat=0.2,
        serving_size="1 cup",
        keto_friendly=True, slow_carb_friendly=True,
        category="vegetable"
    ),

    # === LEGUMES (Slow-Carb Only) ===
    "black beans": FoodItem(
        name="Black Beans",
        calories=227, protein=15, carbs=41, fat=0.9,
        serving_size="1 cup cooked",
        keto_friendly=False, slow_carb_friendly=True,
        category="legume"
    ),
    "lentils": FoodItem(
        name="Lentils",
        calories=230, protein=18, carbs=40, fat=0.8,
        serving_size="1 cup cooked",
        keto_friendly=False, slow_carb_friendly=True,
        category="legume"
    ),
    "pinto beans": FoodItem(
        name="Pinto Beans",
        calories=245, protein=15, carbs=45, fat=1.1,
        serving_size="1 cup cooked",
        keto_friendly=False, slow_carb_friendly=True,
        category="legume"
    ),
    "kidney beans": FoodItem(
        name="Kidney Beans",
        calories=225, protein=15, carbs=40, fat=0.9,
        serving_size="1 cup cooked",
        keto_friendly=False, slow_carb_friendly=True,
        category="legume"
    ),

    # === DAIRY (Keto-Friendly) ===
    "cheese": FoodItem(
        name="Cheddar Cheese",
        calories=113, protein=7, carbs=0.4, fat=9,
        serving_size="1 oz (28g)",
        keto_friendly=True, slow_carb_friendly=False,
        category="dairy",
        aliases=["cheddar", "cheese slice"]
    ),
    "cream cheese": FoodItem(
        name="Cream Cheese",
        calories=99, protein=1.7, carbs=1.6, fat=10,
        serving_size="1 oz (28g)",
        keto_friendly=True, slow_carb_friendly=False,
        category="dairy"
    ),
    "butter": FoodItem(
        name="Butter",
        calories=102, protein=0.1, carbs=0, fat=12,
        serving_size="1 tbsp",
        keto_friendly=True, slow_carb_friendly=False,
        category="fat"
    ),
    "heavy cream": FoodItem(
        name="Heavy Cream",
        calories=52, protein=0.4, carbs=0.4, fat=5.5,
        serving_size="1 tbsp",
        keto_friendly=True, slow_carb_friendly=False,
        category="dairy"
    ),
    "greek yogurt": FoodItem(
        name="Greek Yogurt (plain, full-fat)",
        calories=100, protein=17, carbs=6, fat=0.7,
        serving_size="6 oz (170g)",
        keto_friendly=True, slow_carb_friendly=False,
        category="dairy"
    ),

    # === FATS & OILS ===
    "olive oil": FoodItem(
        name="Olive Oil",
        calories=119, protein=0, carbs=0, fat=14,
        serving_size="1 tbsp",
        keto_friendly=True, slow_carb_friendly=True,
        category="fat"
    ),
    "coconut oil": FoodItem(
        name="Coconut Oil",
        calories=121, protein=0, carbs=0, fat=13,
        serving_size="1 tbsp",
        keto_friendly=True, slow_carb_friendly=True,
        category="fat"
    ),
    "almonds": FoodItem(
        name="Almonds",
        calories=164, protein=6, carbs=3, fat=14,
        serving_size="1 oz (23 almonds)",
        keto_friendly=True, slow_carb_friendly=False,
        category="nuts"
    ),
    "walnuts": FoodItem(
        name="Walnuts",
        calories=185, protein=4.3, carbs=2, fat=18,
        serving_size="1 oz (14 halves)",
        keto_friendly=True, slow_carb_friendly=False,
        category="nuts"
    ),

    # === COMMON MEALS ===
    "salad": FoodItem(
        name="Garden Salad (no dressing)",
        calories=20, protein=1.5, carbs=4, fat=0.2,
        serving_size="2 cups mixed greens",
        keto_friendly=True, slow_carb_friendly=True,
        category="meal",
        aliases=["side salad", "house salad"]
    ),
    "chicken salad": FoodItem(
        name="Chicken Salad",
        calories=350, protein=35, carbs=8, fat=18,
        serving_size="1 bowl",
        keto_friendly=True, slow_carb_friendly=True,
        category="meal",
        aliases=["grilled chicken salad"]
    ),
    "steak salad": FoodItem(
        name="Steak Salad",
        calories=450, protein=38, carbs=10, fat=28,
        serving_size="1 bowl",
        keto_friendly=True, slow_carb_friendly=True,
        category="meal"
    ),
    "omelette": FoodItem(
        name="Omelette (3 eggs, cheese, veggies)",
        calories=350, protein=24, carbs=4, fat=26,
        serving_size="1 omelette",
        keto_friendly=True, slow_carb_friendly=True,
        category="meal",
        aliases=["omelet", "veggie omelette"]
    ),
    "burrito bowl": FoodItem(
        name="Burrito Bowl (no rice)",
        calories=550, protein=42, carbs=25, fat=28,
        serving_size="1 bowl",
        keto_friendly=False, slow_carb_friendly=True,
        category="meal",
        aliases=["chipotle bowl"]
    ),

    # === DRINKS ===
    "coffee": FoodItem(
        name="Coffee (black)",
        calories=2, protein=0.3, carbs=0, fat=0,
        serving_size="8 oz",
        keto_friendly=True, slow_carb_friendly=True,
        category="drink",
        aliases=["black coffee"]
    ),
    "bulletproof coffee": FoodItem(
        name="Bulletproof Coffee",
        calories=230, protein=0, carbs=0, fat=25,
        serving_size="12 oz",
        keto_friendly=True, slow_carb_friendly=False,
        category="drink"
    ),
    "water": FoodItem(
        name="Water",
        calories=0, protein=0, carbs=0, fat=0,
        serving_size="8 oz",
        keto_friendly=True, slow_carb_friendly=True,
        category="drink"
    ),
    "green tea": FoodItem(
        name="Green Tea",
        calories=0, protein=0, carbs=0, fat=0,
        serving_size="8 oz",
        keto_friendly=True, slow_carb_friendly=True,
        category="drink"
    ),

    # === FOODS TO AVOID (for reference) ===
    "bread": FoodItem(
        name="Bread (white)",
        calories=79, protein=2.7, carbs=15, fat=1,
        serving_size="1 slice",
        keto_friendly=False, slow_carb_friendly=False,
        category="avoid"
    ),
    "rice": FoodItem(
        name="Rice (white)",
        calories=206, protein=4.3, carbs=45, fat=0.4,
        serving_size="1 cup cooked",
        keto_friendly=False, slow_carb_friendly=False,
        category="avoid"
    ),
    "pasta": FoodItem(
        name="Pasta",
        calories=221, protein=8, carbs=43, fat=1.3,
        serving_size="1 cup cooked",
        keto_friendly=False, slow_carb_friendly=False,
        category="avoid"
    ),
    "potato": FoodItem(
        name="Potato",
        calories=161, protein=4.3, carbs=37, fat=0.2,
        serving_size="1 medium",
        keto_friendly=False, slow_carb_friendly=False,
        category="avoid",
        aliases=["potatoes", "mashed potatoes", "fries", "french fries"]
    ),
}


def find_food(query: str) -> Optional[FoodItem]:
    """
    Find a food item by name or alias.
    """
    query_lower = query.lower().strip()

    # Direct match
    if query_lower in FOOD_DATABASE:
        return FOOD_DATABASE[query_lower]

    # Check aliases
    for key, food in FOOD_DATABASE.items():
        if food.aliases and query_lower in [a.lower() for a in food.aliases]:
            return food

    # Partial match
    for key, food in FOOD_DATABASE.items():
        if query_lower in key or query_lower in food.name.lower():
            return food
        if food.aliases:
            for alias in food.aliases:
                if query_lower in alias.lower():
                    return food

    return None


def estimate_food(description: str) -> Dict[str, Any]:
    """
    Estimate nutritional info from a food description.
    Returns best guess with confidence level.
    """
    description_lower = description.lower()

    # Try to find matching foods
    found_foods = []
    for key, food in FOOD_DATABASE.items():
        if key in description_lower or food.name.lower() in description_lower:
            found_foods.append(food)
        elif food.aliases:
            for alias in food.aliases:
                if alias.lower() in description_lower:
                    found_foods.append(food)
                    break

    if not found_foods:
        # No match found - make rough estimate
        return {
            "found": False,
            "estimated_calories": 400,  # Default estimate
            "estimated_protein": 20,
            "estimated_carbs": 30,
            "estimated_fat": 15,
            "confidence": "low",
            "message": "Could not find specific food. Using rough estimate.",
            "follow_up_needed": True,
            "questions": [
                "What was the main protein source?",
                "Approximately how large was the portion?",
                "Were there any sauces, dressings, or toppings?"
            ]
        }

    # Calculate totals from found foods
    total_cal = sum(f.calories for f in found_foods)
    total_protein = sum(f.protein for f in found_foods)
    total_carbs = sum(f.carbs for f in found_foods)
    total_fat = sum(f.fat for f in found_foods)

    # Check portion modifiers
    multiplier = 1.0
    if any(word in description_lower for word in ["large", "big", "double"]):
        multiplier = 1.5
    elif any(word in description_lower for word in ["small", "half", "light"]):
        multiplier = 0.6
    elif any(word in description_lower for word in ["extra", "loaded"]):
        multiplier = 1.75

    return {
        "found": True,
        "matched_foods": [f.name for f in found_foods],
        "estimated_calories": int(total_cal * multiplier),
        "estimated_protein": round(total_protein * multiplier, 1),
        "estimated_carbs": round(total_carbs * multiplier, 1),
        "estimated_fat": round(total_fat * multiplier, 1),
        "confidence": "high" if len(found_foods) == 1 else "medium",
        "keto_friendly": all(f.keto_friendly for f in found_foods),
        "slow_carb_friendly": all(f.slow_carb_friendly for f in found_foods),
        "follow_up_needed": len(found_foods) > 1 or multiplier != 1.0,
        "questions": []
    }


def get_keto_suggestions(meal_type: str = "any") -> List[FoodItem]:
    """Get keto-friendly food suggestions."""
    foods = [f for f in FOOD_DATABASE.values() if f.keto_friendly and f.category != "avoid"]
    if meal_type == "breakfast":
        return [f for f in foods if f.category in ["protein", "dairy", "fat", "vegetable"]]
    elif meal_type == "snack":
        return [f for f in foods if f.category in ["nuts", "dairy", "vegetable"]]
    return foods


def get_slow_carb_suggestions(meal_type: str = "any") -> List[FoodItem]:
    """Get slow-carb friendly food suggestions."""
    foods = [f for f in FOOD_DATABASE.values() if f.slow_carb_friendly and f.category != "avoid"]
    if meal_type == "breakfast":
        return [f for f in foods if f.category in ["protein", "legume", "vegetable"]]
    return foods
