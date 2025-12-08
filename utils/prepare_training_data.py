"""
Prepare training data from guys.json for GPT-2 fine-tuning.
Converts recipes into structured text format.
"""
import json
import os

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
    text += "Grain Bill:\n"
    for grain in recipe['grain_bill']:
        weight = grain['weight']
        # Convert to grams if weight is in kg
        if weight < 50:  # Likely in kg
            weight_str = f"{weight}kg"
        else:  # Likely in grams
            weight_str = f"{weight}g"
        text += f"  - {weight_str} {grain['type']} (PPG: {grain['ppg']}, Lovibond: {grain['lovibond']})\n"
    
    # Add hop schedule
    text += "\nHop Schedule:\n"
    for hop in recipe['hop_schedule']:
        text += f"  - {hop['weight']}g {hop['variety']} at {hop['time']}min (AA: {hop['alpha_acid']}%)\n"
    
    # Add yeast
    text += f"\nYeast: {recipe['yeast']}\n"
    
    # Add notes if present
    if recipe.get('notes'):
        text += f"\nNotes: {recipe['notes']}\n"
    
    text += "<|endofrecipe|>\n\n"
    
    return text

def prepare_training_data(output_file='training_data.txt'):
    """Load recipes from all sources and convert to training format."""
    
    # Load recipes from all files
    recipes = []
    
    recipe_files = [
        'data/recipes/guys.json',
        'data/recipes/mathieu.json',
        'data/recipes/precompiled_recipes.json'
    ]
    
    for input_file in recipe_files:
        if os.path.exists(input_file):
            with open(input_file, 'r') as f:
                file_recipes = json.load(f)
                recipes.extend(file_recipes)
                print(f"Loaded {len(file_recipes)} recipes from {input_file}")
        else:
            print(f"Warning: {input_file} not found, skipping...")
    
    print(f"\nTotal recipes loaded: {len(recipes)}")
    
    # Convert all recipes to text
    training_text = ""
    for recipe in recipes:
        training_text += format_recipe_for_training(recipe)
    
    # Save training data
    with open(output_file, 'w') as f:
        f.write(training_text)
    
    print(f"Saved training data to {output_file}")
    print(f"Total training text length: {len(training_text)} characters")
    
    return output_file

if __name__ == "__main__":
    prepare_training_data()
