"""
Generate new beer recipes using the trained template model.
Ensures structured, complete recipe output.

Usage:
    python generate_recipe.py --style "American IPA" --abv 6.5
"""
import torch
import argparse
from train_template_model import RecipeGeneratorModel

def generate_recipe(model, style, abv, og, fg, batch_size, 
                   style_to_idx, idx_to_grain, idx_to_hop, idx_to_yeast, characteristic=None):
    """Generate a complete recipe from style and parameters."""
    
    model.eval()
    
    # Prepare input
    style_idx = style_to_idx.get(style, 0)
    inputs = torch.tensor([[style_idx, abv, og, fg, batch_size]], dtype=torch.float32)
    
    # Generate predictions
    with torch.no_grad():
        outputs = model(inputs)
    
    # Extract predictions
    grain_weights = outputs['grain_weights'][0].tolist()
    hop_weights = outputs['hop_weights'][0].tolist()
    hop_times = outputs['hop_times'][0].tolist()
    yeast_idx = torch.argmax(outputs['yeast_logits'], dim=1).item()
    
    # Build structured recipe text
    recipe_text = "<|startofrecipe|>\n"
    if characteristic:
        recipe_text += f"Recipe: {characteristic} {style}\n"
    else:
        recipe_text += f"Recipe: {style} Recipe\n"
    recipe_text += f"Style: {style}\n"
    recipe_text += f"Method: All Grain\n"
    recipe_text += f"Batch Size: {batch_size} litres\n"
    recipe_text += f"OG: {og:.3f}\n"
    recipe_text += f"FG: {fg:.3f}\n"
    recipe_text += f"ABV: {abv:.1f}%\n\n"
    
    recipe_text += "<|grainbill|>\n"
    recipe_text += "Grain Bill:\n"
    
    # Get top 5 grain predictions
    grain_logits = outputs['grain_logits'][0]
    top_grains = torch.topk(grain_logits, k=min(5, len(idx_to_grain)))
    
    for i, (score, idx) in enumerate(zip(top_grains.values, top_grains.indices)):
        if i < len(grain_weights) and grain_weights[i] > 0:
            grain_name = idx_to_grain.get(idx.item(), 'Unknown')
            weight = grain_weights[i]
            # Convert grams to kg if weight is large (> 1000g)
            if weight > 1000:
                recipe_text += f"  - {weight/1000:.2f}kg {grain_name}\n"
            else:
                recipe_text += f"  - {weight:.0f}g {grain_name}\n"
    
    recipe_text += "\n<|hopschedule|>\n"
    recipe_text += "Hop Schedule:\n"
    
    # Get top 4 hop predictions
    hop_logits = outputs['hop_logits'][0]
    top_hops = torch.topk(hop_logits, k=min(4, len(idx_to_hop)))
    
    for i, (score, idx) in enumerate(zip(top_hops.values, top_hops.indices)):
        if i < len(hop_weights) and hop_weights[i] > 0:
            hop_name = idx_to_hop.get(idx.item(), 'Unknown')
            weight = hop_weights[i]
            time = max(0, hop_times[i])
            recipe_text += f"  - {weight:.0f}g {hop_name} at {time:.0f} min\n"
    
    recipe_text += f"\n<|yeast|>\n"
    yeast_name = idx_to_yeast.get(yeast_idx, 'Unknown')
    recipe_text += f"Yeast: {yeast_name}\n"
    
    # Add characteristic as notes if provided
    if characteristic:
        recipe_text += f"\n<|notes|>\n"
        recipe_text += f"Notes: This recipe emphasizes {characteristic.lower()} characteristics.\n"
    
    recipe_text += "<|endofrecipe|>\n"
    
    return recipe_text

def main():
    parser = argparse.ArgumentParser(description='Generate a beer recipe')
    parser.add_argument('--style', type=str, default='American IPA', help='Beer style')
    parser.add_argument('--abv', type=float, default=6.5, help='Target ABV')
    parser.add_argument('--og', type=float, default=1.065, help='Target OG')
    parser.add_argument('--fg', type=float, default=1.012, help='Target FG')
    parser.add_argument('--batch-size', type=float, default=20, help='Batch size in litres')
    parser.add_argument('--characteristic', type=str, help='Beer characteristic (e.g., "Hoppy", "Malty", "Roasty", "Fruity")')
    parser.add_argument('--model', type=str, default='data/model/recipe_template_model.pt', help='Model file')
    parser.add_argument('--output', type=str, help='Output file (optional)')
    
    args = parser.parse_args()
    
    # Load model
    print(f"Loading model from {args.model}...")
    checkpoint = torch.load(args.model, weights_only=False)
    
    model = RecipeGeneratorModel(
        num_styles=checkpoint['num_styles'],
        num_grains=checkpoint['num_grains'],
        num_hops=checkpoint['num_hops'],
        num_yeasts=checkpoint['num_yeasts']
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    
    # Generate recipe
    if args.characteristic:
        print(f"\nGenerating {args.characteristic} {args.style} recipe with {args.abv}% ABV...\n")
    else:
        print(f"\nGenerating {args.style} recipe with {args.abv}% ABV...\n")
    
    recipe = generate_recipe(
        model, 
        args.style, 
        args.abv, 
        args.og, 
        args.fg, 
        args.batch_size,
        checkpoint['style_to_idx'],
        checkpoint['idx_to_grain'],
        checkpoint['idx_to_hop'],
        checkpoint['idx_to_yeast'],
        args.characteristic
    )
    
    print(recipe)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(recipe)
        print(f"\n✅ Recipe saved to {args.output}")

if __name__ == "__main__":
    main()
