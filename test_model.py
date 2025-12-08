"""
Test the trained recipe generation model.
Generates sample recipes to verify the model works.

Usage:
    python test_model.py
"""
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch

def generate_recipe(
    prompt,
    model,
    tokenizer,
    max_length=500,
    temperature=0.8,
    top_p=0.9
):
    """Generate a recipe based on a prompt."""
    
    # Encode the prompt
    input_ids = tokenizer.encode(prompt, return_tensors='pt')
    
    # Generate
    output = model.generate(
        input_ids,
        max_length=max_length,
        temperature=temperature,
        top_p=top_p,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.encode('<|endofrecipe|>')[0],
    )
    
    # Decode and return
    generated_text = tokenizer.decode(output[0], skip_special_tokens=False)
    return generated_text

def main():
    print("Loading trained model...")
    
    # Load the model
    model = GPT2LMHeadModel.from_pretrained('recipe_model')
    tokenizer = GPT2Tokenizer.from_pretrained('recipe_model')
    
    print("Model loaded successfully!\n")
    
    # Test prompts
    prompts = [
        "<|startofrecipe|>\nRecipe: New IPA\nStyle: American IPA\nABV: 6.5%\n",
        "<|startofrecipe|>\nRecipe: Stout Recipe\nStyle: Irish Stout\nABV: 4.5%\n",
        "<|startofrecipe|>\nRecipe: Pale Ale\nStyle: English Pale Ale\nABV: 5%\n"
    ]
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/3")
        print(f"{'='*60}")
        print(f"Prompt: {prompt.strip()}\n")
        
        recipe = generate_recipe(prompt, model, tokenizer)
        
        # Extract just the recipe (between special tokens)
        if '<|endofrecipe|>' in recipe:
            recipe = recipe.split('<|endofrecipe|>')[0] + '<|endofrecipe|>'
        
        print("Generated Recipe:")
        print(recipe)
        print()
    
    print("\n✅ Model test complete!")
    print("If recipes look good, upload to HuggingFace: python upload_to_huggingface.py")

if __name__ == "__main__":
    main()
