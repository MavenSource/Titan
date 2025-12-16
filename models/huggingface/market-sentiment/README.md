# HuggingFace Market Sentiment Model

This directory should contain a HuggingFace transformer model for market sentiment analysis.

## Expected Files

A trained HuggingFace model directory should contain:
- `config.json` - Model configuration
- `pytorch_model.bin` or `model.safetensors` - Model weights
- `tokenizer_config.json` - Tokenizer configuration
- `vocab.txt` or `tokenizer.json` - Vocabulary file

## How to Add a Model

### Option 1: Download from HuggingFace Hub
```python
from transformers import AutoModel, AutoTokenizer

# Download a pre-trained model
model = AutoModel.from_pretrained("bert-base-uncased")
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

# Save to this directory
model.save_pretrained("models/huggingface/market-sentiment")
tokenizer.save_pretrained("models/huggingface/market-sentiment")
```

### Option 2: Train Your Own Model
```python
from transformers import AutoModelForSequenceClassification, Trainer

# Load base model
model = AutoModelForSequenceClassification.from_pretrained(
    "bert-base-uncased",
    num_labels=2  # Binary sentiment: bullish/bearish
)

# Train on your data
trainer = Trainer(model=model, args=training_args, train_dataset=train_data)
trainer.train()

# Save trained model
model.save_pretrained("models/huggingface/market-sentiment")
```

## Recommended Models

For DeFi market sentiment analysis:
- `ProsusAI/finbert` - Financial sentiment analysis
- `bert-base-uncased` - General purpose, fine-tune on crypto data
- `distilbert-base-uncased` - Smaller, faster alternative

## Current Status

🟡 **Stub Directory** - Model files not present. System will log warning and continue without HuggingFace models.

To use this model, populate this directory with model files and ensure:
```bash
HF_MODEL_PATH=models/huggingface/market-sentiment
```
is set in your `.env` file.
