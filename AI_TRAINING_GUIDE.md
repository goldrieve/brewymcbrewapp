# AI Recipe Generator Setup Guide

This guide will help you train and deploy a GPT-2 model for generating homebrew recipes.

## 📋 Prerequisites

1. **Install dependencies** (for local training):
```bash
pip install transformers torch datasets accelerate huggingface_hub
```

2. **Create a Hugging Face account** (free):
   - Go to https://huggingface.co/join
   - Create your account

3. **Get a Hugging Face token**:
   - Visit https://huggingface.co/settings/tokens
   - Create a new token with "Write" permissions
   - Save it securely

## 🚀 Training Workflow

### Step 1: Prepare Training Data
```bash
python utils/prepare_training_data.py
```
This creates `training_data.txt` from `guys.json` (30 recipes).

### Step 2: Train the Model
```bash
python train_recipe_model.py
```

**Expected output:**
- Training time: ~1-2 hours on CPU (969 recipes, 20 epochs)
- Model saved to: `recipe_model/`
- Model size: ~500MB

**Training progress:**
- You'll see loss decreasing over 10 epochs
- Lower loss = better learning
- Final loss should be < 2.0

### Step 3: Test the Model
```bash
python test_model.py
```

This generates 3 sample recipes to verify the model works.

**What to look for:**
- ✅ Recipes have proper structure (grain bill, hops, yeast)
- ✅ Ingredients make sense for the style
- ✅ Quantities are reasonable
- ⚠️ Some creativity is expected - review and adjust!

### Step 4: Login to Hugging Face
```bash
huggingface-cli login
```
Paste your token when prompted.

### Step 5: Upload to Hugging Face
```bash
python upload_to_huggingface.py
```

This uploads your model to: `https://huggingface.co/YOUR_USERNAME/brew-recipe-generator`

### Step 6: Update Streamlit App

Edit `app.py` line ~1542:
```python
model_name = "YOUR_USERNAME/brew-recipe-generator"
```

Replace `YOUR_USERNAME` with your Hugging Face username.

### Step 7: Deploy to Streamlit Cloud

1. Commit and push changes:
```bash
git add .
git commit -m "Add AI recipe generator"
git push
```

2. Streamlit Cloud will automatically redeploy
3. First load takes ~30 seconds (downloading model)
4. Subsequent loads are instant (cached)

## 💡 Usage in App

1. Navigate to "Generate Recipe" page
2. Select style, ABV, batch size
3. Click "Generate Recipe"
4. Review and adjust the generated recipe
5. Copy to Recipe Builder to customize

## 🎛️ Tuning Parameters

**Temperature (Creativity)**:
- `0.6-0.8`: More consistent, traditional recipes
- `0.8-1.0`: Balanced creativity
- `1.0-1.5`: Experimental, creative recipes

**Max Length**:
- `300-500`: Standard recipes
- `500-800`: Detailed recipes with more ingredients

## 📊 Training on More Data

To train on all recipes (969 total):

Edit `utils/prepare_training_data.py`:
```python
# Load all recipe files
with open('data/recipes/guys.json') as f:
    recipes.extend(json.load(f))
with open('data/recipes/mathieu.json') as f:
    recipes.extend(json.load(f))
with open('data/recipes/precompiled_recipes.json') as f:
    recipes.extend(json.load(f))
```

Then re-run the training workflow.

**Benefits:**
- More diverse recipes
- Better style coverage
- More ingredient variety

**Tradeoffs:**
- Longer training time (~1-2 hours)
- Larger training file
- Still free!

## 🐛 Troubleshooting

**"Module not found: transformers"**
```bash
pip install transformers torch
```

**"Not logged in to Hugging Face"**
```bash
huggingface-cli login
```

**"Model generates nonsense"**
- Train for more epochs (15-20)
- Lower temperature (0.6-0.7)
- Add more training data

**"Streamlit app can't load model"**
- Verify model uploaded: Check Hugging Face profile
- Update model name in app.py
- Check requirements.txt includes transformers

**"Out of memory during training"**
- Reduce batch_size to 1
- Use CPU (slower but works)
- Train in Google Colab (free GPU)

## 💰 Costs

Everything is **FREE**:
- ✅ Training locally: Free
- ✅ Hugging Face hosting: Free
- ✅ Model downloads: Free (no bandwidth limits)
- ✅ Streamlit Cloud: Free

## 🎉 Next Steps

Once working:
- Experiment with different styles
- Train on more recipes
- Adjust temperature for your taste
- Share recipes with the community!
