"""
Fine-tune GPT-2 on homebrew recipe data.
This will create a model that can generate new recipes based on prompts.

Usage:
    python train_recipe_model.py

Requirements:
    pip install transformers torch datasets accelerate
"""
import os
from transformers import (
    GPT2LMHeadModel,
    GPT2Tokenizer,
    GPT2Config,
    TextDataset,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

def train_model(
    train_file='training_data.txt',
    output_dir='recipe_model',
    num_epochs=20,
    batch_size=4,
    learning_rate=3e-5
):
    """Fine-tune GPT-2 on recipe data."""
    
    print("Loading GPT-2 tokenizer and model...")
    
    # Load pre-trained model and tokenizer
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    model = GPT2LMHeadModel.from_pretrained('gpt2')
    
    # Add special tokens for recipe structure
    special_tokens = {
        'additional_special_tokens': ['<|startofrecipe|>', '<|endofrecipe|>']
    }
    tokenizer.add_special_tokens(special_tokens)
    model.resize_token_embeddings(len(tokenizer))
    
    # Set padding token
    tokenizer.pad_token = tokenizer.eos_token
    
    print(f"Loading training data from {train_file}...")
    
    # Load dataset
    train_dataset = TextDataset(
        tokenizer=tokenizer,
        file_path=train_file,
        block_size=512  # Max sequence length
    )
    
    # Data collator for language modeling
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False  # We're doing causal language modeling, not masked
    )
    
    print(f"Training dataset size: {len(train_dataset)} examples")
    print(f"Starting training for {num_epochs} epochs...")
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=True,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        save_steps=1000,
        save_total_limit=2,
        learning_rate=learning_rate,
        warmup_steps=200,
        logging_steps=100,
        logging_dir=f'{output_dir}/logs',
        prediction_loss_only=True,
        report_to='none',  # Disable wandb logging
        weight_decay=0.01,
        lr_scheduler_type='cosine',
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=train_dataset,
    )
    
    # Train the model
    print("\n🍺 Training started...")
    trainer.train()
    
    # Save the final model
    print(f"\n✅ Training complete! Saving model to {output_dir}/")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    print(f"\n📦 Model saved successfully!")
    print(f"   Model directory: {output_dir}/")
    print(f"   Model size: ~500MB")
    print(f"\n🚀 Next steps:")
    print(f"   1. Test generation: python test_model.py")
    print(f"   2. Upload to HuggingFace: python upload_to_huggingface.py")
    
    return model, tokenizer

if __name__ == "__main__":
    # Check if training data exists
    if not os.path.exists('training_data.txt'):
        print("Error: training_data.txt not found!")
        print("Please run: python utils/prepare_training_data.py")
        exit(1)
    
    train_model()
