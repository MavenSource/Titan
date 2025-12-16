"""
Test AI/ML Model Integration
==============================

Tests that AI/ML models are properly integrated into the system:
- Environment variables are read correctly
- Model paths are validated
- System handles missing models gracefully
- Model loader integrates with orchestrator
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import pytest, but make it optional
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Mock pytest.fail for non-pytest runs
    class pytest:
        @staticmethod
        def fail(msg):
            raise AssertionError(msg)


class TestModelEnvironmentVariables:
    """Test that model environment variables are properly configured"""
    
    def test_env_example_has_model_paths(self):
        """Verify .env.example contains all required model path variables"""
        env_example = Path(__file__).parent.parent / '.env.example'
        assert env_example.exists(), ".env.example file not found"
        
        content = env_example.read_text()
        
        required_vars = [
            'CATBOOST_MODEL_PATH',
            'HF_MODEL_PATH',
            'ML_MODEL_PATH',
            'SELF_LEARNING_DATA_PATH',
            'MODEL_CACHE_DIR'
        ]
        
        for var in required_vars:
            assert var in content, f"Missing {var} in .env.example"
    
    def test_model_paths_have_defaults(self):
        """Verify model paths have sensible default values"""
        env_example = Path(__file__).parent.parent / '.env.example'
        content = env_example.read_text()
        
        # Check that defaults point to models/ directory
        assert 'models/catboost_profit_predictor.cbm' in content
        assert 'models/huggingface/market-sentiment' in content
        assert 'models/ml_ensemble_model.pkl' in content
        assert 'data/self_learning' in content
        assert 'models/cache' in content


class TestModelDirectories:
    """Test that model directories are properly set up"""
    
    def test_models_directory_exists(self):
        """Verify models/ directory exists"""
        models_dir = Path(__file__).parent.parent / 'models'
        assert models_dir.exists(), "models/ directory not found"
        assert models_dir.is_dir(), "models/ is not a directory"
    
    def test_models_readme_exists(self):
        """Verify models/README.md exists with documentation"""
        readme = Path(__file__).parent.parent / 'models' / 'README.md'
        assert readme.exists(), "models/README.md not found"
        
        content = readme.read_text()
        assert 'CatBoost' in content
        assert 'HuggingFace' in content
        assert 'ML Ensemble' in content
    
    def test_stub_files_exist(self):
        """Verify stub model files exist"""
        models_dir = Path(__file__).parent.parent / 'models'
        
        # Check stub files
        catboost_stub = models_dir / 'catboost_profit_predictor.cbm'
        ml_stub = models_dir / 'ml_ensemble_model.pkl'
        
        assert catboost_stub.exists(), "CatBoost stub file not found"
        assert ml_stub.exists(), "ML ensemble stub file not found"
        
        # Verify they are stubs (small files)
        assert catboost_stub.stat().st_size < 1024, "CatBoost file too large to be stub"
        assert ml_stub.stat().st_size < 1024, "ML file too large to be stub"
    
    def test_self_learning_directory_exists(self):
        """Verify self-learning data directory exists"""
        data_dir = Path(__file__).parent.parent / 'data' / 'self_learning'
        assert data_dir.exists(), "data/self_learning directory not found"
        assert data_dir.is_dir(), "data/self_learning is not a directory"
    
    def test_cache_directory_exists(self):
        """Verify model cache directory exists"""
        cache_dir = Path(__file__).parent.parent / 'models' / 'cache'
        assert cache_dir.exists(), "models/cache directory not found"
        assert cache_dir.is_dir(), "models/cache is not a directory"


class TestModelLoader:
    """Test the ModelLoader class functionality"""
    
    def test_model_loader_imports(self):
        """Test that ModelLoader can be imported"""
        try:
            from ml.model_loader import ModelLoader, initialize_models
            assert ModelLoader is not None
            assert initialize_models is not None
        except ImportError as e:
            pytest.fail(f"Failed to import ModelLoader: {e}")
    
    def test_model_loader_instantiation(self):
        """Test that ModelLoader can be instantiated"""
        from ml.model_loader import ModelLoader
        
        loader = ModelLoader()
        assert loader is not None
        assert hasattr(loader, 'models')
        assert hasattr(loader, 'validate_paths')
        assert hasattr(loader, 'load_models')
    
    def test_model_loader_validates_paths(self):
        """Test that ModelLoader validates paths correctly"""
        from ml.model_loader import ModelLoader
        
        loader = ModelLoader()
        results = loader.validate_paths()
        
        # Should return a dict
        assert isinstance(results, dict)
        
        # If training is enabled, should have validation results
        if loader.enable_training:
            assert len(results) > 0
    
    def test_model_loader_handles_missing_models_gracefully(self):
        """Test that missing models don't crash the loader"""
        from ml.model_loader import ModelLoader
        
        # Set paths to non-existent files
        os.environ['CATBOOST_MODEL_PATH'] = 'models/nonexistent.cbm'
        os.environ['ML_MODEL_PATH'] = 'models/nonexistent.pkl'
        
        try:
            loader = ModelLoader()
            results = loader.validate_paths()
            
            # Should not crash, just log warnings
            assert loader.get_warnings() is not None
            
        finally:
            # Clean up environment
            os.environ.pop('CATBOOST_MODEL_PATH', None)
            os.environ.pop('ML_MODEL_PATH', None)
    
    def test_model_loader_respects_training_flag(self):
        """Test that loader skips when ENABLE_REALTIME_TRAINING=false"""
        from ml.model_loader import ModelLoader
        
        # Disable training
        os.environ['ENABLE_REALTIME_TRAINING'] = 'false'
        
        try:
            loader = ModelLoader()
            assert not loader.enable_training
            
            results = loader.validate_paths()
            assert len(results) == 0  # Should skip validation
            
        finally:
            os.environ.pop('ENABLE_REALTIME_TRAINING', None)


class TestMainnetOrchestratorIntegration:
    """Test that MainnetOrchestrator integrates ModelLoader"""
    
    def test_orchestrator_imports_model_loader(self):
        """Test that orchestrator can import ModelLoader"""
        orchestrator_file = Path(__file__).parent.parent / 'mainnet_orchestrator.py'
        content = orchestrator_file.read_text()
        
        assert 'from ml.model_loader import ModelLoader' in content
        assert 'self.model_loader' in content
    
    def test_orchestrator_initializes_model_loader(self):
        """Test that orchestrator initializes ModelLoader in __init__"""
        orchestrator_file = Path(__file__).parent.parent / 'mainnet_orchestrator.py'
        content = orchestrator_file.read_text()
        
        # Should have model_loader as instance variable
        assert 'self.model_loader = None' in content
        
        # Should initialize in initialize() method
        assert 'self.model_loader = ModelLoader()' in content
        assert 'self.model_loader.load_models()' in content


class TestQLearningIntegration:
    """Test that Q-learning agent uses environment variables"""
    
    def test_ql_agent_uses_env_variable(self):
        """Test that QLearningAgent reads SELF_LEARNING_DATA_PATH"""
        rl_file = Path(__file__).parent.parent / 'ml' / 'cortex' / 'rl_optimizer.py'
        content = rl_file.read_text()
        
        assert 'SELF_LEARNING_DATA_PATH' in content
        assert 'os.getenv' in content
    
    def test_feature_store_uses_env_variable(self):
        """Test that FeatureStore reads SELF_LEARNING_DATA_PATH"""
        fs_file = Path(__file__).parent.parent / 'ml' / 'cortex' / 'feature_store.py'
        content = fs_file.read_text()
        
        assert 'SELF_LEARNING_DATA_PATH' in content
        assert 'os.getenv' in content


class TestGitIgnore:
    """Test that .gitignore properly handles model files"""
    
    def test_gitignore_excludes_model_files(self):
        """Test that trained models are excluded from git"""
        gitignore = Path(__file__).parent.parent / '.gitignore'
        content = gitignore.read_text()
        
        # Should exclude common model file types
        assert 'models/*.cbm' in content
        assert 'models/*.pkl' in content
        assert 'models/*.h5' in content
        assert 'models/*.pt' in content
        assert 'models/*.pth' in content
        assert 'models/*.onnx' in content
    
    def test_gitignore_keeps_directories(self):
        """Test that directory structure is preserved"""
        gitignore = Path(__file__).parent.parent / '.gitignore'
        content = gitignore.read_text()
        
        # Should keep .gitkeep files
        assert '!models/cache/.gitkeep' in content
        assert '!data/self_learning/.gitkeep' in content


if __name__ == '__main__':
    # Run tests with pytest if available, otherwise run basic checks
    try:
        import pytest
        pytest.main([__file__, '-v'])
    except ImportError:
        print("pytest not available, running basic checks...")
        
        # Run basic checks without pytest
        test_env = TestModelEnvironmentVariables()
        test_env.test_env_example_has_model_paths()
        test_env.test_model_paths_have_defaults()
        
        test_dirs = TestModelDirectories()
        test_dirs.test_models_directory_exists()
        test_dirs.test_models_readme_exists()
        test_dirs.test_stub_files_exist()
        test_dirs.test_self_learning_directory_exists()
        test_dirs.test_cache_directory_exists()
        
        print("\n✅ All basic checks passed!")
