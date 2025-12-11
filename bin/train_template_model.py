"""
Train a template-based recipe generation model using a simple neural network.
Predicts recipe parameters (grains, hops, yeast) based on style and desired ABV,
then fills a strict template to ensure structured output.

Usage:
    python train_template_model.py

Requirements:
    pip install torch scikit-learn pandas numpy
"""
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np
from collections import defaultdict
import pickle

class RecipeDataset(Dataset):
    """Dataset where each example is a complete recipe with all its parameters."""
    
    def __init__(self, recipes, style_to_idx, grain_to_idx, hop_to_idx, yeast_to_idx):
        self.recipes = recipes
        self.style_to_idx = style_to_idx
        self.grain_to_idx = grain_to_idx
        self.hop_to_idx = hop_to_idx
        self.yeast_to_idx = yeast_to_idx
        self.max_yeast_idx = len(yeast_to_idx) - 1
        self.max_grain_idx = len(grain_to_idx) - 1
        self.max_hop_idx = len(hop_to_idx) - 1
        
    def __len__(self):
        return len(self.recipes)
    
    def __getitem__(self, idx):
        recipe = self.recipes[idx]
        
        # Input: style + target ABV + target OG
        style_idx = self.style_to_idx.get(recipe['style'], 0)
        abv = float(recipe.get('abv', 5.0))
        og = float(recipe.get('og', 1.050))
        fg = float(recipe.get('fg', 1.010))
        batch_size = float(recipe.get('batch_size', 10))
        
        # Encode grains (top 5)
        grain_bill = recipe.get('grain_bill', [])[:5]
        grain_indices = []
        grain_weights = []
        for grain in grain_bill:
            if isinstance(grain, dict):
                grain_type = grain.get('type') or grain.get('name', 'Unknown')
                weight = float(grain.get('weight', 0))
            elif isinstance(grain, list) and len(grain) >= 2:
                weight, grain_type = grain[0], grain[1]
                weight = float(weight)
            else:
                continue
            
            grain_idx = self.grain_to_idx.get(grain_type, 0)
            grain_indices.append(grain_idx)
            grain_weights.append(weight)
        
        # Pad to 5 grains
        while len(grain_indices) < 5:
            grain_indices.append(0)
            grain_weights.append(0.0)
        
        # Encode hops (top 4)
        hop_schedule = recipe.get('hop_schedule', [])[:4]
        hop_indices = []
        hop_weights = []
        hop_times = []
        for hop in hop_schedule:
            if isinstance(hop, dict):
                variety = hop.get('variety') or hop.get('name', 'Unknown')
                weight = float(hop.get('weight', 0))
                time = float(hop.get('time', 60))
            elif isinstance(hop, list) and len(hop) >= 3:
                weight, variety, time = hop[0], hop[1], hop[2]
                weight = float(weight)
                time = float(time)
            else:
                continue
            
            hop_idx = self.hop_to_idx.get(variety, 0)
            hop_indices.append(hop_idx)
            hop_weights.append(weight)
            hop_times.append(time)
        
        # Pad to 4 hops
        while len(hop_indices) < 4:
            hop_indices.append(0)
            hop_weights.append(0.0)
            hop_times.append(0.0)
        
        # Encode yeast
        yeast = recipe.get('yeast', 'Unknown')
        if isinstance(yeast, list):
            yeast = ' '.join(str(y) for y in yeast)
        elif isinstance(yeast, dict):
            yeast = yeast.get('name', 'Unknown')
        else:
            yeast = str(yeast)
        
        yeast_idx = self.yeast_to_idx.get(yeast, 0)
        
        # Input features: [style, abv, og, fg, batch_size]
        input_features = torch.tensor([style_idx, abv, og, fg, batch_size], dtype=torch.float32)
        
        # Output targets: grains, hops, yeast
        output = {
            'grain_indices': torch.tensor(grain_indices, dtype=torch.long),
            'grain_weights': torch.tensor(grain_weights, dtype=torch.float32),
            'hop_indices': torch.tensor(hop_indices, dtype=torch.long),
            'hop_weights': torch.tensor(hop_weights, dtype=torch.float32),
            'hop_times': torch.tensor(hop_times, dtype=torch.float32),
            'yeast_idx': torch.tensor(min(yeast_idx, len(self.yeast_to_idx) - 1), dtype=torch.long)
        }
        
        return input_features, output

class RecipeGeneratorModel(nn.Module):
    """Neural network that predicts recipe components from style and target parameters."""
    
    def __init__(self, num_styles, num_grains, num_hops, num_yeasts):
        super().__init__()
        
        # Embedding for style
        self.style_embed = nn.Embedding(num_styles, 32)
        
        # Input: style embedding (32) + 4 numeric features (abv, og, fg, batch_size)
        self.input_fc = nn.Sequential(
            nn.Linear(32 + 4, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
        )
        
        # Grain prediction: 5 grains with types and weights
        self.grain_type_head = nn.Linear(512, num_grains)  # Classify grain types
        self.grain_weight_head = nn.Linear(512, 5)  # Predict 5 grain weights
        
        # Hop prediction: 4 hops with varieties, weights, and times
        self.hop_variety_head = nn.Linear(512, num_hops)
        self.hop_weight_head = nn.Linear(512, 4)
        self.hop_time_head = nn.Linear(512, 4)
        
        # Yeast prediction
        self.yeast_head = nn.Linear(512, num_yeasts)
        
    def forward(self, x):
        # x shape: [batch, 5] where first element is style index
        style_idx = x[:, 0].long()
        # Clamp style index to valid range
        style_idx = torch.clamp(style_idx, 0, self.style_embed.num_embeddings - 1)
        numeric_features = x[:, 1:]  # abv, og, fg, batch_size
        
        # Embed style
        style_emb = self.style_embed(style_idx)
        
        # Combine features
        combined = torch.cat([style_emb, numeric_features], dim=1)
        
        # Shared representation
        hidden = self.input_fc(combined)
        
        # Predict components
        grain_logits = self.grain_type_head(hidden)  # [batch, num_grains]
        grain_weights = self.grain_weight_head(hidden)  # [batch, 5]
        
        hop_logits = self.hop_variety_head(hidden)  # [batch, num_hops]
        hop_weights = self.hop_weight_head(hidden)  # [batch, 4]
        hop_times = self.hop_time_head(hidden)  # [batch, 4]
        
        yeast_logits = self.yeast_head(hidden)  # [batch, num_yeasts]
        
        return {
            'grain_logits': grain_logits,
            'grain_weights': grain_weights,
            'hop_logits': hop_logits,
            'hop_weights': hop_weights,
            'hop_times': hop_times,
            'yeast_logits': yeast_logits
        }

def load_and_preprocess_recipes(data_file='data/ml/downsampled_training_data.txt'):
    """Load recipes from formatted text file."""
    
    with open(data_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Split by end of recipe token
    recipe_texts = text.split('<|endofrecipe|>')
    
    recipes = []
    for recipe_text in recipe_texts:
        if not recipe_text.strip():
            continue
        
        recipe = {}
        lines = recipe_text.strip().split('\n')
        
        # Parse basic info
        for line in lines:
            if line.startswith('Recipe:'):
                recipe['name'] = line.replace('Recipe:', '').strip()
            elif line.startswith('Style:'):
                recipe['style'] = line.replace('Style:', '').strip()
            elif line.startswith('ABV:'):
                abv_str = line.replace('ABV:', '').replace('%', '').strip()
                try:
                    recipe['abv'] = float(abv_str)
                except:
                    recipe['abv'] = 5.0
            elif line.startswith('OG:'):
                try:
                    recipe['og'] = float(line.replace('OG:', '').strip())
                except:
                    recipe['og'] = 1.050
            elif line.startswith('FG:'):
                try:
                    recipe['fg'] = float(line.replace('FG:', '').strip())
                except:
                    recipe['fg'] = 1.010
            elif line.startswith('Batch Size:'):
                batch_str = line.replace('Batch Size:', '').replace('litres', '').strip()
                try:
                    recipe['batch_size'] = float(batch_str)
                except:
                    recipe['batch_size'] = 10.0
        
        # Parse grain bill
        grain_bill = []
        in_grains = False
        for line in lines:
            if '<|grainbill|>' in line:
                in_grains = True
                continue
            if '<|hopschedule|>' in line:
                in_grains = False
            if in_grains and line.strip().startswith('-'):
                # Parse grain line: "  - 4.5kg Pale Malt"
                parts = line.strip().lstrip('- ').split(maxsplit=1)
                if len(parts) >= 2:
                    weight_str = parts[0].replace('kg', '').replace('g', '')
                    try:
                        weight = float(weight_str)
                        if 'kg' in parts[0]:
                            weight = weight * 1000  # Convert to grams
                        grain_bill.append({'weight': weight, 'type': parts[1]})
                    except:
                        pass
        recipe['grain_bill'] = grain_bill
        
        # Parse hop schedule
        hop_schedule = []
        in_hops = False
        for line in lines:
            if '<|hopschedule|>' in line:
                in_hops = True
                continue
            if '<|yeast|>' in line:
                in_hops = False
            if in_hops and line.strip().startswith('-'):
                # Parse hop line: "  - 25g Cascade at 60 min"
                parts = line.strip().lstrip('- ').split()
                if len(parts) >= 4:
                    try:
                        weight = float(parts[0].replace('g', ''))
                        variety = parts[1]
                        time = float(parts[3])
                        hop_schedule.append({'weight': weight, 'variety': variety, 'time': time})
                    except:
                        pass
        recipe['hop_schedule'] = hop_schedule
        
        # Parse yeast
        for line in lines:
            if line.startswith('Yeast:'):
                recipe['yeast'] = line.replace('Yeast:', '').strip()
        
        if recipe.get('name'):
            recipes.append(recipe)
    
    print(f"Loaded {len(recipes)} recipes")
    return recipes

def build_vocabularies(recipes):
    """Build vocabularies for styles, grains, hops, and yeasts."""
    
    styles = set()
    grains = set()
    hops = set()
    yeasts = set()
    
    for recipe in recipes:
        if recipe.get('style'):
            styles.add(recipe['style'])
        
        for grain in recipe.get('grain_bill', []):
            if isinstance(grain, dict):
                grain_type = grain.get('type') or grain.get('name')
                if grain_type:
                    grains.add(grain_type)
        
        for hop in recipe.get('hop_schedule', []):
            if isinstance(hop, dict):
                variety = hop.get('variety') or hop.get('name')
                if variety:
                    hops.add(variety)
        
        yeast = recipe.get('yeast')
        if yeast:
            yeasts.add(yeast)
    
    style_to_idx = {s: i+1 for i, s in enumerate(sorted(styles))}
    style_to_idx['Unknown'] = 0
    
    grain_to_idx = {g: i+1 for i, g in enumerate(sorted(grains))}
    grain_to_idx['Unknown'] = 0
    
    hop_to_idx = {h: i+1 for i, h in enumerate(sorted(hops))}
    hop_to_idx['Unknown'] = 0
    
    yeast_to_idx = {y: i+1 for i, y in enumerate(sorted(yeasts))}
    yeast_to_idx['Unknown'] = 0
    
    print(f"Vocabularies: {len(style_to_idx)} styles, {len(grain_to_idx)} grains, {len(hop_to_idx)} hops, {len(yeast_to_idx)} yeasts")
    
    return style_to_idx, grain_to_idx, hop_to_idx, yeast_to_idx

def train_model(
    data_file='data/ml/downsampled_training_data.txt',
    output_file='data/model/recipe_template_model.pt',
    num_epochs=50,
    batch_size=32,
    learning_rate=0.001
):
    """Train the template-based recipe generation model."""
    
    print("Loading and preprocessing recipes...")
    recipes = load_and_preprocess_recipes(data_file)
    
    print("Building vocabularies...")
    style_to_idx, grain_to_idx, hop_to_idx, yeast_to_idx = build_vocabularies(recipes)
    
    # Create reverse mappings
    idx_to_style = {v: k for k, v in style_to_idx.items()}
    idx_to_grain = {v: k for k, v in grain_to_idx.items()}
    idx_to_hop = {v: k for k, v in hop_to_idx.items()}
    idx_to_yeast = {v: k for k, v in yeast_to_idx.items()}
    
    # Create dataset
    dataset = RecipeDataset(recipes, style_to_idx, grain_to_idx, hop_to_idx, yeast_to_idx)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # Initialize model
    model = RecipeGeneratorModel(
        num_styles=len(style_to_idx),
        num_grains=len(grain_to_idx),
        num_hops=len(hop_to_idx),
        num_yeasts=len(yeast_to_idx)
    )
    
    # Loss functions
    classification_loss = nn.CrossEntropyLoss()
    regression_loss = nn.MSELoss()
    
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    
    print(f"\n🍺 Training started for {num_epochs} epochs...")
    
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        
        for batch_idx, (inputs, targets) in enumerate(dataloader):
            optimizer.zero_grad()
            
            # Forward pass
            outputs = model(inputs)
            
            # Compute losses
            # Grain losses (predict grain type for each position)
            grain_loss = 0
            for i in range(5):
                grain_loss += classification_loss(outputs['grain_logits'], targets['grain_indices'][:, i])
            grain_loss /= 5
            
            # Grain weight loss
            weight_loss = regression_loss(outputs['grain_weights'], targets['grain_weights'])
            
            # Hop losses
            hop_loss = 0
            for i in range(4):
                hop_loss += classification_loss(outputs['hop_logits'], targets['hop_indices'][:, i])
            hop_loss /= 4
            
            hop_weight_loss = regression_loss(outputs['hop_weights'], targets['hop_weights'])
            hop_time_loss = regression_loss(outputs['hop_times'], targets['hop_times'])
            
            # Yeast loss
            yeast_loss = classification_loss(outputs['yeast_logits'], targets['yeast_idx'])
            
            # Total loss
            loss = grain_loss + weight_loss + hop_loss + hop_weight_loss + hop_time_loss + yeast_loss
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}")
    
    # Save model and vocabularies
    print(f"\n✅ Training complete! Saving model to {output_file}")
    torch.save({
        'model_state_dict': model.state_dict(),
        'style_to_idx': style_to_idx,
        'grain_to_idx': grain_to_idx,
        'hop_to_idx': hop_to_idx,
        'yeast_to_idx': yeast_to_idx,
        'idx_to_style': idx_to_style,
        'idx_to_grain': idx_to_grain,
        'idx_to_hop': idx_to_hop,
        'idx_to_yeast': idx_to_yeast,
        'num_styles': len(style_to_idx),
        'num_grains': len(grain_to_idx),
        'num_hops': len(hop_to_idx),
        'num_yeasts': len(yeast_to_idx)
    }, output_file)
    
    print(f"📦 Model saved successfully as single file: {output_file}")
    print(f"   File size: ~{torch.load(output_file, weights_only=False).__sizeof__() / 1024 / 1024:.2f} MB")
    
    return model

if __name__ == "__main__":
    import os
    if not os.path.exists('data/ml/downsampled_training_data.txt'):
        print("Error: downsampled_training_data.txt not found!")
        print("Please run: python bin/create_downsampled_training_data.py")
        exit(1)
    
    train_model()
