cd /Users/r/pkgs/brewymcbrewapp/data/recipes && python3 -c "
import json
from collections import defaultdict

# Read the file
with open('recipes_full.txt', 'r') as f:
    data = json.load(f)

# Filter for All Grain recipes with rating >= 4
all_grain_recipes = {k: v for k, v in data.items() 
                     if v.get('method') == 'All Grain' and v.get('rating', 0) >= 4}

print(f'After filtering: {len(all_grain_recipes)} All Grain recipes with rating >= 4')

# Group recipes by style
recipes_by_style = defaultdict(list)
for k, v in all_grain_recipes.items():
    style = v.get('style', 'Unknown')
    recipes_by_style[style].append((k, v))

# For each style, keep only top 10 recipes sorted by num rating (desc)
top_recipes = {}
for style, recipes in recipes_by_style.items():
    # Sort by num rating (descending)
    sorted_recipes = sorted(
        recipes, 
        key=lambda x: x[1].get('num rating', 0), 
        reverse=True
    )
    # Keep top 10
    for k, v in sorted_recipes[:10]:
        top_recipes[k] = v

# Write to new file
with open('top_recipes.txt', 'w') as f:
    json.dump(top_recipes, f, indent=2)

print(f'Kept {len(top_recipes)} recipes from {len(recipes_by_style)} unique styles')
"