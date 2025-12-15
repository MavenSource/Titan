#!/usr/bin/env python3
"""
AI/ML Setup Verification Script
================================

Verifies that all AI/ML components are properly configured and integrated.
Run this after setup to ensure the ML infrastructure is ready.

Usage:
    python verify_ml_setup.py
"""

import os
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    """Print a section header"""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")


def print_warning(text):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_error(text):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")


def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")


def check_environment_variables():
    """Check that all required environment variables are configured"""
    print_header("1. Environment Variables Check")
    
    env_example = Path('.env.example')
    if not env_example.exists():
        print_error(".env.example not found")
        return False
    
    content = env_example.read_text()
    
    required_vars = [
        'CATBOOST_MODEL_PATH',
        'HF_MODEL_PATH',
        'ML_MODEL_PATH',
        'SELF_LEARNING_DATA_PATH',
        'MODEL_CACHE_DIR',
        'ENABLE_REALTIME_TRAINING'
    ]
    
    all_present = True
    for var in required_vars:
        if var in content:
            print_success(f"{var} found in .env.example")
        else:
            print_error(f"{var} missing from .env.example")
            all_present = False
    
    return all_present


def check_directory_structure():
    """Check that all required directories exist"""
    print_header("2. Directory Structure Check")
    
    required_dirs = [
        'models',
        'models/cache',
        'models/huggingface',
        'models/huggingface/market-sentiment',
        'data/self_learning',
        'ml',
        'ml/cortex'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print_success(f"Directory exists: {dir_path}")
        else:
            print_error(f"Directory missing: {dir_path}")
            all_exist = False
    
    return all_exist


def check_documentation():
    """Check that documentation files exist"""
    print_header("3. Documentation Check")
    
    required_docs = [
        'models/README.md',
        'models/huggingface/market-sentiment/README.md',
        'README.md'
    ]
    
    all_exist = True
    for doc_path in required_docs:
        path = Path(doc_path)
        if path.exists():
            print_success(f"Documentation exists: {doc_path}")
        else:
            print_error(f"Documentation missing: {doc_path}")
            all_exist = False
    
    return all_exist


def check_model_files():
    """Check that model stub files exist"""
    print_header("4. Model Files Check")
    
    stub_files = [
        'models/catboost_profit_predictor.cbm',
        'models/ml_ensemble_model.pkl'
    ]
    
    all_exist = True
    for file_path in stub_files:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            if size < 1024:
                print_info(f"Stub file exists: {file_path} ({size} bytes)")
            else:
                print_warning(f"File exists but may be trained model: {file_path} ({size} bytes)")
        else:
            print_warning(f"Stub file missing: {file_path}")
            all_exist = False
    
    return all_exist


def check_python_modules():
    """Check that Python modules can be imported"""
    print_header("5. Python Module Import Check")
    
    modules_to_check = [
        ('ml.model_loader', 'ModelLoader'),
        ('ml.cortex.rl_optimizer', 'QLearningAgent'),
        ('ml.cortex.forecaster', 'MarketForecaster'),
        ('ml.cortex.feature_store', 'FeatureStore')
    ]
    
    all_imported = True
    critical_failures = []
    optional_deps = {'numpy', 'pandas'}  # Dependencies that are optional for verification
    
    for module_name, class_name in modules_to_check:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print_success(f"Successfully imported: {module_name}.{class_name}")
        except ImportError as e:
            # Check if it's a missing optional dependency
            error_msg = str(e).lower()
            is_optional = any(dep in error_msg for dep in optional_deps)
            
            if is_optional:
                print_warning(f"Import warning for {module_name}.{class_name}: Missing optional dependency")
                print_info(f"  Install runtime dependencies with: pip install -r requirements.txt")
            else:
                print_error(f"Failed to import {module_name}.{class_name}: {e}")
                all_imported = False
                critical_failures.append(module_name)
        except Exception as e:
            print_error(f"Failed to import {module_name}.{class_name}: {e}")
            all_imported = False
            critical_failures.append(module_name)
    
    if critical_failures:
        print_error(f"Critical import failures: {', '.join(critical_failures)}")
    
    return all_imported


def check_model_loader_functionality():
    """Test the ModelLoader functionality"""
    print_header("6. ModelLoader Functionality Test")
    
    try:
        from ml.model_loader import ModelLoader
        
        # Test instantiation
        loader = ModelLoader()
        print_success("ModelLoader instantiated successfully")
        
        # Test path validation
        results = loader.validate_paths()
        print_success(f"Path validation completed: {len(results)} paths checked")
        
        # Report results
        for model_name, is_available in results.items():
            if is_available:
                print_success(f"  {model_name}: Available")
            else:
                print_info(f"  {model_name}: Not available (expected for stub files)")
        
        # Check warnings
        warnings = loader.get_warnings()
        if warnings:
            print_info(f"Warnings generated: {len(warnings)}")
            for warning in warnings[:3]:  # Show first 3
                print_info(f"  - {warning}")
        
        return True
        
    except Exception as e:
        print_error(f"ModelLoader test failed: {e}")
        return False


def check_integration():
    """Check that components are integrated"""
    print_header("7. Integration Check")
    
    # Check mainnet_orchestrator.py integration
    orchestrator_file = Path('mainnet_orchestrator.py')
    if not orchestrator_file.exists():
        print_error("mainnet_orchestrator.py not found")
        return False
    
    content = orchestrator_file.read_text()
    
    checks = [
        ('from ml.model_loader import ModelLoader', 'ModelLoader import'),
        ('self.model_loader', 'model_loader instance variable'),
        ('ModelLoader()', 'ModelLoader instantiation'),
        ('load_models()', 'load_models() call')
    ]
    
    all_integrated = True
    for check_string, description in checks:
        if check_string in content:
            print_success(f"{description} found in orchestrator")
        else:
            print_error(f"{description} missing from orchestrator")
            all_integrated = False
    
    # Check RL optimizer integration
    rl_file = Path('ml/cortex/rl_optimizer.py')
    if rl_file.exists():
        content = rl_file.read_text()
        if 'SELF_LEARNING_DATA_PATH' in content:
            print_success("QLearningAgent uses SELF_LEARNING_DATA_PATH")
        else:
            print_error("QLearningAgent missing SELF_LEARNING_DATA_PATH")
            all_integrated = False
    
    return all_integrated


def check_gitignore():
    """Check that .gitignore is properly configured"""
    print_header("8. Git Configuration Check")
    
    gitignore = Path('.gitignore')
    if not gitignore.exists():
        print_error(".gitignore not found")
        return False
    
    content = gitignore.read_text()
    
    patterns = [
        'models/*.cbm',
        'models/*.pkl',
        'models/*.h5',
        'models/*.pt',
        'models/cache/*',
        '!models/cache/.gitkeep',
        'data/self_learning/*',
        '!data/self_learning/.gitkeep'
    ]
    
    all_present = True
    for pattern in patterns:
        if pattern in content:
            print_success(f"Pattern found: {pattern}")
        else:
            print_error(f"Pattern missing: {pattern}")
            all_present = False
    
    return all_present


def main():
    """Run all verification checks"""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}   AI/ML SETUP VERIFICATION{RESET}")
    print(f"{BLUE}   Titan Arbitrage System{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}")
    
    results = []
    
    # Run all checks
    results.append(("Environment Variables", check_environment_variables()))
    results.append(("Directory Structure", check_directory_structure()))
    results.append(("Documentation", check_documentation()))
    results.append(("Model Files", check_model_files()))
    results.append(("Python Modules", check_python_modules()))
    results.append(("ModelLoader", check_model_loader_functionality()))
    results.append(("Integration", check_integration()))
    results.append(("Git Configuration", check_gitignore()))
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        if result:
            print_success(f"{check_name}: PASSED")
        else:
            print_error(f"{check_name}: FAILED")
    
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    if passed == total:
        print_success(f"All checks passed! ({passed}/{total})")
        print_info("\n🎉 AI/ML infrastructure is properly configured!")
        print_info("📖 See models/README.md for training instructions")
        print_info("🚀 You can now run the system with ENABLE_REALTIME_TRAINING=true")
    else:
        print_warning(f"Some checks failed ({passed}/{total} passed)")
        print_info("\n⚠️  Please review the errors above and fix any issues")
        print_info("📖 See models/README.md for setup instructions")
    print(f"{BLUE}{'=' * 70}{RESET}\n")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
