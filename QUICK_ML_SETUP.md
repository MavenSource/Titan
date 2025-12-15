# Quick ML Setup Guide

**Quick reference for getting AI/ML models working in 2 minutes**

## ⚡ Quick Start (Built-in Q-Learning)

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Set training flag (already true by default)
# ENABLE_REALTIME_TRAINING=true

# 3. Start system
python mainnet_orchestrator.py

# ✅ Done! Q-learning works out-of-the-box
```

## 🔍 Verify Setup

```bash
python verify_ml_setup.py
```

Expected: **8/8 checks pass** ✅

## 📋 What's Included

All these environment variables are already configured in `.env.example`:

```env
CATBOOST_MODEL_PATH=models/catboost_profit_predictor.cbm
HF_MODEL_PATH=models/huggingface/market-sentiment
ML_MODEL_PATH=models/ml_ensemble_model.pkl
SELF_LEARNING_DATA_PATH=data/self_learning
MODEL_CACHE_DIR=models/cache
```

## 🎯 Expected Behavior

When you start the system, you'll see:

```
🔧 Initializing system components...
   [0/4] Loading AI/ML models...
⚠️  CatBoost model is a stub/placeholder: models/catboost_profit_predictor.cbm
   System will continue without CatBoost predictions
⚠️  HuggingFace model directory incomplete: models/huggingface/market-sentiment
   System will continue without HuggingFace models
⚠️  ML ensemble model is a stub/placeholder: models/ml_ensemble_model.pkl
   System will continue without ensemble predictions
✅ Self-learning data directory found: data/self_learning
✅ Model cache directory found: models/cache
📊 Model Validation Summary: 2/5 available
ℹ️  Some models missing - system will use available models only
💡 To add missing models, see: models/README.md
   ✅ Model validation complete
```

**This is normal!** The stub files are placeholders. The system uses built-in Q-learning.

## 🚀 Advanced: Train Your Own Models

Want to train custom models? See:
- **Full guide**: `models/README.md`
- **Examples**: Training CatBoost, scikit-learn, HuggingFace
- **Summary**: `ML_INTEGRATION_SUMMARY.md`

## ❓ Troubleshooting

### Models not loading?

```bash
# Check what's configured
python verify_ml_setup.py

# View environment variables
cat .env | grep MODEL
```

### Want to disable ML entirely?

```bash
# In .env, set:
ENABLE_REALTIME_TRAINING=false

# System will skip all model loading
```

### Need help?

1. Run: `python verify_ml_setup.py`
2. Check: `models/README.md`
3. Review: `ML_INTEGRATION_SUMMARY.md`

## 📚 Documentation

| File | Purpose |
|------|---------|
| `QUICK_ML_SETUP.md` | This file - 2-minute quickstart |
| `models/README.md` | Complete model training guide (6KB) |
| `ML_INTEGRATION_SUMMARY.md` | Full implementation details |
| `README.md` | Main documentation (see AI/ML section) |

## ✅ Status Check

To verify everything is working:

```bash
# Full verification (recommended)
python verify_ml_setup.py

# Quick test
python ml/model_loader.py

# Integration tests
python tests/test_model_integration.py
```

All should complete without errors (warnings are expected for stub files).

---

**That's it!** The system is ready to use with built-in Q-learning. Train custom models when you're ready to optimize further.
