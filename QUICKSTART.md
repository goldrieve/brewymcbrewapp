# AI Recipe Generator - Quick Reference

## 🚀 One-Command Setup

```bash
./setup_ai_model.sh
```

This will:
1. ✅ Install dependencies
2. ✅ Prepare training data from guys.json
3. ✅ Train GPT-2 model (~10-30 min)
4. ✅ Test the model
5. ✅ Upload to Hugging Face

## 📝 Manual Steps (Alternative)

```bash
# 1. Prepare data
python utils/prepare_training_data.py

# 2. Train model
python train_recipe_model.py

# 3. Test model
python test_model.py

# 4. Login to Hugging Face
huggingface-cli login

# 5. Upload model
python upload_to_huggingface.py
```

## 🔧 Configure App

After uploading, edit `app.py` line ~1542:

```python
model_name = "YOUR_USERNAME/brew-recipe-generator"
```

Replace `YOUR_USERNAME` with your Hugging Face username.

## 📦 Deploy

```bash
git add .
git commit -m "Add AI recipe generator"
git push
```

Streamlit Cloud auto-deploys in ~2 minutes.

## 💡 Using the Generator

1. Open your app
2. Navigate to **"Generate Recipe"**
3. Select:
   - Beer style (IPA, Stout, etc.)
   - ABV target (3-10%)
   - Batch size (5-50 litres)
4. Click **"Generate Recipe"**
5. Review and customize!

## 🎛️ Tips

**For consistent recipes:**
- Temperature: 0.6-0.8
- Traditional styles (IPA, Stout)

**For creative recipes:**
- Temperature: 1.0-1.5
- Experimental styles

**The model learns from:**
- 30 recipes from guys.json
- Grain bill patterns
- Hop schedules
- Style-specific ingredients

## 📊 Costs

**Everything is FREE:**
- ✅ Local training: $0
- ✅ Hugging Face hosting: $0
- ✅ Model downloads: $0 (unlimited)
- ✅ Streamlit Cloud: $0

## 🔍 Files Created

| File | Purpose |
|------|---------|
| `utils/prepare_training_data.py` | Converts JSON → training text |
| `train_recipe_model.py` | Trains GPT-2 model |
| `test_model.py` | Tests model generation |
| `upload_to_huggingface.py` | Uploads to HF Hub |
| `setup_ai_model.sh` | One-click setup script |
| `AI_TRAINING_GUIDE.md` | Detailed documentation |

## 🐛 Troubleshooting

**Model not found in app:**
- Check model uploaded at `huggingface.co/YOUR_USERNAME/brew-recipe-generator`
- Update username in `app.py`
- Verify `requirements.txt` has transformers

**Training too slow:**
- Expected: 10-30 min on CPU
- Normal: Model saves every 500 steps
- Patience: Grab a homebrew! 🍺

**Generation quality issues:**
- Train longer (15-20 epochs)
- Lower temperature (0.6)
- Add more training data

## 📈 Next Steps

1. **Train on more data:**
   - Add mathieu.json (29 more recipes)
   - Add precompiled_recipes.json (910 more recipes)
   - Total: 969 recipes!

2. **Fine-tune parameters:**
   - Adjust epochs in `train_recipe_model.py`
   - Experiment with learning rates
   - Try different temperatures

3. **Enhance the UI:**
   - Add recipe comparison
   - Save generated recipes directly
   - Show multiple variations

## 🎉 Success Criteria

Your model is working if:
- ✅ Generates valid JSON-like recipe structure
- ✅ Ingredients match the style
- ✅ Quantities are reasonable (not 50kg of hops!)
- ✅ Includes grain bill, hops, and yeast

Some creativity is expected - always review recipes before brewing!

---

**Need help?** Check `AI_TRAINING_GUIDE.md` for detailed docs.
