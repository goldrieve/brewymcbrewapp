"""
Upload the trained recipe model to Hugging Face Hub.

Requirements:
    pip install huggingface_hub
    huggingface-cli login

Usage:
    python upload_to_huggingface.py
"""
from huggingface_hub import HfApi, create_repo
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import os

def upload_model(
    model_dir='recipe_model',
    repo_name='brew-recipe-generator',
    username=None
):
    """Upload trained model to Hugging Face Hub."""
    
    print("🔐 Checking Hugging Face authentication...")
    
    api = HfApi()
    
    # Get username if not provided
    if username is None:
        try:
            user_info = api.whoami()
            username = user_info['name']
            print(f"✅ Logged in as: {username}")
        except Exception as e:
            print("❌ Not logged in to Hugging Face!")
            print("\nPlease run: huggingface-cli login")
            print("Get your token from: https://huggingface.co/settings/tokens")
            return
    
    repo_id = f"{username}/{repo_name}"
    
    print(f"\n📦 Creating repository: {repo_id}")
    
    # Create repository
    try:
        create_repo(repo_id, private=False, exist_ok=True)
        print(f"✅ Repository created/verified: https://huggingface.co/{repo_id}")
    except Exception as e:
        print(f"Error creating repository: {e}")
        return
    
    print(f"\n⬆️  Uploading model from {model_dir}/...")
    
    # Load and push model
    try:
        model = GPT2LMHeadModel.from_pretrained(model_dir)
        tokenizer = GPT2Tokenizer.from_pretrained(model_dir)
        
        print("Pushing model to hub (this may take a few minutes)...")
        model.push_to_hub(repo_id)
        
        print("Pushing tokenizer to hub...")
        tokenizer.push_to_hub(repo_id)
        
        print(f"\n✅ Upload complete!")
        print(f"\n📍 Model URL: https://huggingface.co/{repo_id}")
        print(f"\n🔧 To use in your app:")
        print(f'   model = GPT2LMHeadModel.from_pretrained("{repo_id}")')
        print(f'   tokenizer = GPT2Tokenizer.from_pretrained("{repo_id}")')
        
    except Exception as e:
        print(f"❌ Error uploading model: {e}")
        return
    
    # Create a model card
    model_card = f"""---
language: en
tags:
- homebrew
- beer
- recipe-generation
- gpt2
license: mit
---

# Brew Recipe Generator

A GPT-2 model fine-tuned on homebrew beer recipes from Guy's collection.

## Usage

```python
from transformers import GPT2LMHeadModel, GPT2Tokenizer

model = GPT2LMHeadModel.from_pretrained("{repo_id}")
tokenizer = GPT2Tokenizer.from_pretrained("{repo_id}")

# Generate a recipe
prompt = "<|startofrecipe|>\\nRecipe: My IPA\\nStyle: American IPA\\nABV: 6.5%\\n"
input_ids = tokenizer.encode(prompt, return_tensors='pt')
output = model.generate(input_ids, max_length=500, temperature=0.8)
recipe = tokenizer.decode(output[0])
print(recipe)
```

## Training Data

Trained on 30 homebrew recipes including:
- American IPAs
- Stouts
- Pale Ales
- And more!

## Model Details

- Base model: GPT-2 (124M parameters)
- Fine-tuned for: Recipe generation
- Training epochs: 10
- Batch size: 2
"""
    
    try:
        with open(os.path.join(model_dir, "README.md"), "w") as f:
            f.write(model_card)
        
        api.upload_file(
            path_or_fileobj=os.path.join(model_dir, "README.md"),
            path_in_repo="README.md",
            repo_id=repo_id,
        )
        print(f"\n📝 Model card uploaded!")
        
    except Exception as e:
        print(f"Note: Could not upload model card: {e}")
    
    print(f"\n🎉 All done! Your model is ready to use.")

if __name__ == "__main__":
    # Check if model exists
    if not os.path.exists('recipe_model'):
        print("❌ Error: recipe_model/ directory not found!")
        print("Please train the model first: python train_recipe_model.py")
        exit(1)
    
    upload_model()
