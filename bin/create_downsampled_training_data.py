"""
Create downsampled training dataset with top 100 recipes per style, formatted for training.
"""
import json
import os
from collections import defaultdict

def format_recipe_for_training(recipe):
    """Convert a recipe dict into formatted training text."""
    text = "<|startofrecipe|>\n"
    
    # Add metadata
    text += f"Recipe: {recipe['name']}\n"
    text += f"Style: {recipe.get('style', 'Unknown')}\n"
    text += f"Method: {recipe.get('method', 'All Grain')}\n"
    text += f"Batch Size: {recipe.get('batch_size', 10)} litres\n"
    text += f"OG: {recipe.get('og', 1.050)}\n"
    text += f"FG: {recipe.get('fg', 1.010)}\n"
    text += f"ABV: {recipe.get('abv', 5)}%\n\n"
    
    # Add grain bill
    text += "<|grainbill|>\n"
    text += "Grain Bill:\n"
    grain_bill = (recipe.get('grain_bill') or 
                  recipe.get('malts') or 
                  recipe.get('grains') or 
                  recipe.get('fermentables') or [])
    for grain in grain_bill:
        if isinstance(grain, dict):
            weight = grain.get('weight', grain.get('amount', 0))
            try:
                weight = float(weight)
            except (ValueError, TypeError):
                weight = 0
            grain_type = (grain.get('type') or 
                         grain.get('name') or 
                         grain.get('grain_type', 'Unknown'))
            ppg = grain.get('ppg', grain.get('potential', 'N/A'))
            lovibond = grain.get('lovibond', grain.get('color', 'N/A'))
            # Convert to grams if weight is in kg
            if weight < 50:  # Likely in kg
                weight_str = f"{weight}kg"
            else:  # Likely in grams
                weight_str = f"{weight}g"
            text += f"  - {weight_str} {grain_type}\n"
        elif isinstance(grain, list) and len(grain) >= 4:
            # Handle list format: [weight, type, ppg, lovibond] - try this order
            weight, grain_type, ppg, lovibond = grain[:4]
            try:
                weight = float(weight)
            except (ValueError, TypeError):
                weight = 0
            if weight < 50:
                weight_str = f"{weight}kg"
            else:
                weight_str = f"{weight}g"
            text += f"  - {weight_str} {grain_type}\n"
        else:
            # Skip malformed grain entries
            continue
    
    # Add hop schedule
    text += "\n<|hopschedule|>\n"
    text += "Hop Schedule:\n"
    hop_schedule = (recipe.get('hop_schedule') or 
                   recipe.get('hops') or 
                   recipe.get('hop_additions') or [])
    for hop in hop_schedule:
        if isinstance(hop, dict):
            weight = hop.get('weight', hop.get('amount', 0))
            try:
                weight = float(weight)
            except (ValueError, TypeError):
                weight = 0
            variety = hop.get('variety', hop.get('name', 'Unknown'))
            time = hop.get('time', hop.get('addition_time', 0))
            try:
                time = int(float(time))
            except (ValueError, TypeError):
                time = 60  # default to 60 min if not a number
            alpha_acid = hop.get('alpha_acid', hop.get('aa', 'N/A'))
            text += f"  - {weight}g {variety} at {time} min\n"
        elif isinstance(hop, list) and len(hop) >= 4:
            # Handle list format: [weight, variety, time, alpha_acid] - try this order
            weight, variety, time, alpha_acid = hop[:4]
            try:
                weight = float(weight)
                time = int(float(time)) if time.replace('.', '').isdigit() else 60
            except (ValueError, TypeError, AttributeError):
                weight = 0
                time = 60
            text += f"  - {weight}g {variety} at {time} min\n"
        else:
            # Skip malformed hop entries
            continue
    
    # Add yeast
    text += f"\n<|yeast|>\n"
    yeast = (recipe.get('yeast') or 
            recipe.get('yeast_strain') or 
            recipe.get('fermentation', {}).get('yeast', 'Unknown'))
    
    if isinstance(yeast, list):
        yeast_str = ' '.join(str(y) for y in yeast)
    elif isinstance(yeast, dict):
        yeast_str = f"{yeast.get('name', 'Unknown')} - {yeast.get('code', '')}".strip(' -')
    else:
        yeast_str = str(yeast) if yeast else 'Unknown'
    
    # Clean up yeast string to remove extra parameters
    if yeast_str != 'Unknown':
        words = yeast_str.split()
        # Find yeast code (WLP, US-, etc.)
        code_idx = -1
        for i, word in enumerate(words):
            if ('WLP' in word or 'US-' in word or 'DIPA' in word or 
                word.startswith('S-') or word.startswith('K-')):
                code_idx = i
                break
        if code_idx >= 0:
            # Take up to and including the code
            yeast_str = ' '.join(words[:code_idx + 1])
        else:
            # If no code found, take first few words
            yeast_str = ' '.join(words[:4]) if len(words) > 4 else yeast_str
    
    text += f"Yeast: {yeast_str}\n"
    
    # Add notes if present
    if recipe.get('notes'):
        text += f"\n<|notes|>\n"
        text += f"Notes: {recipe['notes']}\n"
    
    text += "<|endofrecipe|>\n\n"
    
    return text

def create_downsampled_training_data(output_file='data/ml/downsampled_training_data.txt', include_full_recipes=False):
    """Create training data from top 100 recipes per style."""
    
    # Load recipes from all sources
    recipes = []
    guys_recipes = []
    mathieu_recipes = []
    
    recipe_files = [
        'data/recipes/guys.json',
        'data/recipes/mathieu.json'
    ]
    
    for input_file in recipe_files:
        if os.path.exists(input_file):
            with open(input_file, 'r') as f:
                file_recipes = json.load(f)
                recipes.extend(file_recipes)
                if 'guys' in input_file:
                    guys_recipes = file_recipes
                elif 'mathieu' in input_file:
                    mathieu_recipes = file_recipes
                print(f"Loaded {len(file_recipes)} recipes from {input_file}")
        else:
            print(f"Warning: {input_file} not found, skipping...")
    
    # Optionally include recipes from recipes_full.txt
    if include_full_recipes and os.path.exists('data/ml/recipes_full.txt'):
        with open('data/ml/recipes_full.txt', 'r') as f:
            full_data = json.load(f)
            full_recipes = list(full_data.values())  # Convert dict values to list
            recipes.extend(full_recipes)
            print(f"Loaded {len(full_recipes)} recipes from data/ml/recipes_full.txt")
    
    print(f"\nTotal recipes loaded: {len(recipes)}")
    
    # Always include all recipes from guys and mathieu
    selected_recipes = guys_recipes + mathieu_recipes
    print(f"Included all {len(guys_recipes)} Guy's recipes and {len(mathieu_recipes)} Mathieu's recipes")
    
    # Downsample recipes from recipes_full.txt: top 100 per style
    if include_full_recipes and os.path.exists('data/ml/recipes_full.txt'):
        with open('data/ml/recipes_full.txt', 'r') as f:
            full_data = json.load(f)
            full_recipes = list(full_data.values())
        
        # Filter for All Grain recipes from full dataset
        full_all_grain = [r for r in full_recipes if r.get('method') == 'All Grain']
        
        # Group by style and take top 100 per style
        from collections import defaultdict
        recipes_by_style = defaultdict(list)
        for recipe in full_all_grain:
            style = recipe.get('style', 'Unknown')
            recipes_by_style[style].append(recipe)
        
        top_recipes_full = []
        for style, style_recipes in recipes_by_style.items():
            # Sort by ABV descending
            sorted_recipes = sorted(style_recipes, key=lambda x: x.get('abv', 0), reverse=True)
            # Take top 100
            top_recipes_full.extend(sorted_recipes[:100])
        
        print(f"Selected {len(top_recipes_full)} top recipes from {len(recipes_by_style)} styles in recipes_full.txt")
        selected_recipes.extend(top_recipes_full)
    
    # Combine and deduplicate
    recipes = list({json.dumps(r, sort_keys=True): r for r in selected_recipes}.values())  # Remove duplicates
    
    print(f"Total unique recipes after deduplication: {len(recipes)}")
    
    # Convert all selected recipes to text
    training_text = ""
    for recipe in recipes:
        training_text += format_recipe_for_training(recipe)
    
    print(f"Formatted {len(recipes)} recipes for training")
    
    # Save training data
    with open(output_file, 'w') as f:
        f.write(training_text)
    
    print(f"Saved downsampled training data to {output_file}")
    print(f"Total training text length: {len(training_text)} characters")

if __name__ == "__main__":
    create_downsampled_training_data(include_full_recipes=True)
