#!/bin/bash

# AI Recipe Generator - Quick Start Script
# This script automates the entire training and upload process

echo "🍺 Homebrew AI Recipe Generator Setup"
echo "======================================"
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python found"

# Step 1: Install dependencies
echo ""
echo "📦 Step 1/5: Installing dependencies..."
pip install -q transformers torch datasets accelerate huggingface_hub

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"

# Step 2: Prepare training data
echo ""
echo "📝 Step 2/5: Preparing training data..."
python utils/prepare_training_data.py

if [ $? -ne 0 ]; then
    echo "❌ Failed to prepare training data"
    exit 1
fi

echo "✅ Training data prepared"

# Step 3: Train model
echo ""
echo "🧠 Step 3/5: Training model (this may take 10-30 minutes)..."
echo "⏳ Grab a beer while you wait!"
python train_recipe_model.py

if [ $? -ne 0 ]; then
    echo "❌ Training failed"
    exit 1
fi

echo "✅ Model trained successfully"

# Step 4: Test model
echo ""
echo "🧪 Step 4/5: Testing model..."
python test_model.py

if [ $? -ne 0 ]; then
    echo "⚠️  Testing failed, but model might still work"
fi

# Step 5: Upload to Hugging Face
echo ""
echo "☁️  Step 5/5: Upload to Hugging Face"
echo ""
echo "Please ensure you're logged in to Hugging Face:"
echo "Run: huggingface-cli login"
echo ""
read -p "Are you logged in? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    python upload_to_huggingface.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 SUCCESS! Your model is ready!"
        echo ""
        echo "Next steps:"
        echo "1. Update app.py with your Hugging Face username"
        echo "2. Commit and push: git add . && git commit -m 'Add AI model' && git push"
        echo "3. Your Streamlit app will auto-deploy!"
    else
        echo "❌ Upload failed. Check your Hugging Face token."
    fi
else
    echo ""
    echo "Please login first:"
    echo "1. Run: huggingface-cli login"
    echo "2. Get token from: https://huggingface.co/settings/tokens"
    echo "3. Re-run this script"
fi
