# AI/ML Models Directory

This directory contains machine learning models used by the Titan arbitrage system for intelligent decision-making and profit optimization.

## 📁 Directory Structure

```
models/
├── README.md                           # This file
├── catboost_profit_predictor.cbm      # CatBoost profit prediction model (stub)
├── ml_ensemble_model.pkl              # Scikit-learn ensemble model (stub)
├── huggingface/                       # HuggingFace transformer models
│   └── market-sentiment/              # Market sentiment analysis model
│       └── README.md                  # Model information
└── cache/                             # Model cache directory
    └── .gitkeep                       # Keep directory in git
```

## 🤖 Model Descriptions

### 1. CatBoost Profit Predictor
- **File**: `catboost_profit_predictor.cbm`
- **Type**: Gradient Boosting Model (CatBoost)
- **Purpose**: Predicts profitability of arbitrage opportunities
- **Input Features**: 
  - Gas prices (gwei)
  - DEX liquidity depth
  - Bridge fees (USD)
  - Token volatility index
  - Time of day / network congestion
- **Output**: Probability of profitable execution (0.0 - 1.0)
- **Training Data**: Historical trade outcomes from production system
- **Status**: 🟡 Stub file - requires training with real data

### 2. ML Ensemble Model
- **File**: `ml_ensemble_model.pkl`
- **Type**: Scikit-learn Ensemble (Random Forest + XGBoost)
- **Purpose**: Multi-factor opportunity scoring
- **Input Features**:
  - DEX price spreads
  - Gas price trends (last 10 blocks)
  - Network congestion metrics
  - Historical success rates per token pair
- **Output**: Risk-adjusted profit score
- **Status**: 🟡 Stub file - requires training with real data

### 3. HuggingFace Market Sentiment Model
- **Path**: `huggingface/market-sentiment/`
- **Type**: Transformer-based NLP model
- **Purpose**: Analyze market sentiment from on-chain signals
- **Input**: Transaction patterns, volume changes, whale movements
- **Output**: Bullish/bearish sentiment scores
- **Status**: 🟡 Stub directory - model files not included (too large for git)

## 🔧 Environment Variables

Configure model paths in `.env`:

```bash
# CatBoost Model Path
CATBOOST_MODEL_PATH=models/catboost_profit_predictor.cbm

# HuggingFace Model Path
HF_MODEL_PATH=models/huggingface/market-sentiment

# General ML Model Path
ML_MODEL_PATH=models/ml_ensemble_model.pkl

# Self-Learning Data Path
SELF_LEARNING_DATA_PATH=data/self_learning

# Model Cache Directory (optional)
MODEL_CACHE_DIR=models/cache
```

## 📊 Training Your Own Models

### Option 1: Use Existing Q-Learning (Built-in)

The system includes a working Q-learning reinforcement learning agent:
- **Location**: `ml/cortex/rl_optimizer.py`
- **Data**: `data/q_table.json`
- **Status**: ✅ Fully functional
- **No additional setup required**

### Option 2: Train Custom Models

To train custom models with your own data:

1. **Collect Training Data**:
   ```bash
   # Run the system in PAPER mode to collect data without risk
   EXECUTION_MODE=PAPER python mainnet_orchestrator.py
   
   # Training data will be collected in:
   # - data/history.csv (market observations)
   # - data/q_table.json (RL outcomes)
   # - data/self_learning/ (custom training data)
   ```

2. **Train CatBoost Model**:
   ```python
   # Example training script (create your own)
   from catboost import CatBoostClassifier
   import pandas as pd
   import os
   
   # Get data path from environment variable
   data_path = os.getenv('SELF_LEARNING_DATA_PATH', 'data/self_learning')
   
   # Load training data
   df = pd.read_csv(f'{data_path}/history.csv')
   X = df[['gas_price_gwei', 'bridge_fee_usd', 'dex_price', 'volatility_index']]
   y = df['outcome_label']  # 1=profit, 0=loss
   
   # Train model
   model = CatBoostClassifier(iterations=1000)
   model.fit(X, y)
   
   # Save model
   model.save_model('models/catboost_profit_predictor.cbm')
   ```

3. **Train Scikit-learn Model**:
   ```python
   from sklearn.ensemble import RandomForestClassifier
   import joblib
   import pandas as pd
   import os
   
   # Get data path from environment variable
   data_path = os.getenv('SELF_LEARNING_DATA_PATH', 'data/self_learning')
   
   # Load and prepare data
   df = pd.read_csv(f'{data_path}/history.csv')
   # ... feature engineering ...
   
   # Train ensemble
   model = RandomForestClassifier(n_estimators=100)
   model.fit(X_train, y_train)
   
   # Save model
   joblib.dump(model, 'models/ml_ensemble_model.pkl')
   ```

## 🚀 Model Integration

Models are automatically loaded at startup if:
1. `ENABLE_REALTIME_TRAINING=true` in `.env`
2. Model files exist at configured paths
3. Model files have correct format

If models are missing:
- ✅ System logs a warning
- ✅ System continues with degraded functionality
- ✅ Built-in Q-learning still functions
- ⚠️ No crashes or failures

## 📝 Model File Formats

| Model Type | File Extension | Library | Size Limit |
|------------|---------------|---------|------------|
| CatBoost | `.cbm` | catboost | < 100 MB |
| Scikit-learn | `.pkl`, `.joblib` | sklearn | < 50 MB |
| HuggingFace | directory | transformers | < 500 MB |
| TensorFlow | `.h5`, `.pb` | tensorflow | < 200 MB |
| PyTorch | `.pt`, `.pth` | torch | < 200 MB |

## 🔒 Security Notes

- ⚠️ **Never commit trained models with sensitive data to public repos**
- ⚠️ **Models trained on private trading data should stay private**
- ✅ Use `.gitignore` to exclude large model files
- ✅ Stub files (< 1KB) are safe to commit

## 📚 Additional Resources

- **Feature Store**: `ml/cortex/feature_store.py` - Data collection for training
- **RL Optimizer**: `ml/cortex/rl_optimizer.py` - Working reinforcement learning
- **Market Forecaster**: `ml/cortex/forecaster.py` - Gas price prediction
- **Brain**: `ml/brain.py` - Main intelligence orchestrator

## 🆘 Troubleshooting

### Model not loading?
1. Check file path in `.env` is correct
2. Verify file exists: `ls -la models/`
3. Check file permissions: `chmod 644 models/*.cbm`
4. Review logs for specific error messages

### Want to disable ML models?
Set in `.env`:
```bash
ENABLE_REALTIME_TRAINING=false
```

System will use basic Q-learning only.

## 📦 Dependencies

Required Python packages for model training (not required for runtime):
```bash
pip install catboost scikit-learn transformers torch
```

Current runtime dependencies (already in requirements.txt):
- pandas
- numpy
- (Q-learning uses no external ML libs)
