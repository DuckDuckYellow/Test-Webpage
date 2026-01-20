#!/usr/bin/env python3
"""
Phase 2 Configuration Testing Script
Tests the new configuration management system.
"""

import os
import sys
from pathlib import Path


def test_config_file_exists():
    """Test that config.py exists."""
    if not Path('config.py').exists():
        return False, "config.py file not found"
    return True, "config.py exists"


def test_config_imports():
    """Test that config.py can be imported."""
    try:
        from config import Config, DevelopmentConfig, ProductionConfig, TestingConfig, get_config
        return True, "All config classes imported successfully"
    except ImportError as e:
        return False, f"Failed to import config: {str(e)}"


def test_env_example_exists():
    """Test that .env.example exists."""
    if not Path('.env.example').exists():
        return False, ".env.example file not found"
    return True, ".env.example exists"


def test_env_file_exists():
    """Test that .env file exists."""
    if not Path('.env').exists():
        return False, ".env file not found (should exist from Phase 1)"
    return True, ".env file exists"


def test_config_classes():
    """Test that all config classes are defined correctly."""
    try:
        from config import Config, DevelopmentConfig, ProductionConfig, TestingConfig

        # Check base Config
        if not hasattr(Config, 'SECRET_KEY'):
            return False, "Config class missing SECRET_KEY"

        if not hasattr(Config, 'MAX_CONTENT_LENGTH'):
            return False, "Config class missing MAX_CONTENT_LENGTH"

        if not hasattr(Config, 'ARTICLES_DIR'):
            return False, "Config class missing ARTICLES_DIR"

        # Check DevelopmentConfig
        if not hasattr(DevelopmentConfig, 'DEBUG'):
            return False, "DevelopmentConfig missing DEBUG"

        if DevelopmentConfig.DEBUG is not True:
            return False, "DevelopmentConfig.DEBUG should be True"

        # Check ProductionConfig
        if ProductionConfig.DEBUG is not False:
            return False, "ProductionConfig.DEBUG should be False"

        # Check TestingConfig
        if not hasattr(TestingConfig, 'TESTING'):
            return False, "TestingConfig missing TESTING"

        return True, "All config classes have required attributes"
    except Exception as e:
        return False, f"Error checking config classes: {str(e)}"


def test_get_config_function():
    """Test the get_config() function."""
    try:
        from config import get_config

        # Test getting default config
        default_config = get_config()
        if default_config is None:
            return False, "get_config() returned None"

        # Test getting development config
        dev_config = get_config('development')
        if dev_config.__name__ != 'DevelopmentConfig':
            return False, f"Expected DevelopmentConfig, got {dev_config.__name__}"

        # Test getting production config
        prod_config = get_config('production')
        if prod_config.__name__ != 'ProductionConfig':
            return False, f"Expected ProductionConfig, got {prod_config.__name__}"

        # Test getting testing config
        test_config = get_config('testing')
        if test_config.__name__ != 'TestingConfig':
            return False, f"Expected TestingConfig, got {test_config.__name__}"

        return True, "get_config() function works correctly"
    except Exception as e:
        return False, f"Error testing get_config(): {str(e)}"


def test_app_py_imports():
    """Test that app.py has correct imports."""
    try:
        with open('app.py', 'r') as f:
            content = f.read()

        # Check for config import
        if 'from config import get_config' not in content:
            return False, "app.py missing 'from config import get_config'"

        # Check that old imports are removed
        if 'import secrets' in content:
            return False, "app.py still has 'import secrets' (should be removed)"

        if 'from dotenv import load_dotenv' in content:
            return False, "app.py still has 'from dotenv import load_dotenv' (should be removed)"

        # Check that old Config class is removed
        if 'class Config:' in content and 'Security configuration' in content:
            return False, "app.py still has old Config class (should be removed)"

        # Check app initialization
        if 'app.config.from_object(get_config())' not in content:
            return False, "app.py missing 'app.config.from_object(get_config())'"

        return True, "app.py has correct imports and initialization"
    except Exception as e:
        return False, f"Error checking app.py: {str(e)}"


def test_article_content_function():
    """Test that get_article_content uses config paths."""
    try:
        with open('app.py', 'r') as f:
            content = f.read()

        # Find get_article_content function
        if 'def get_article_content(filename):' not in content:
            return False, "get_article_content function not found"

        # Check it uses config path
        if "app.config['ARTICLES_DIR']" not in content:
            return False, "get_article_content not using app.config['ARTICLES_DIR']"

        # Check it doesn't use old path construction
        if 'Path(app.root_path) / "articles"' in content:
            return False, "get_article_content still using old path construction"

        return True, "get_article_content uses centralized config paths"
    except Exception as e:
        return False, f"Error checking get_article_content: {str(e)}"


def test_main_block():
    """Test that main block shows environment info."""
    try:
        with open('app.py', 'r') as f:
            content = f.read()

        # Check for environment info display
        if 'Flask Application Starting' not in content:
            return False, "Main block missing startup message"

        if 'Environment:' not in content:
            return False, "Main block not displaying environment"

        if 'Config:' not in content:
            return False, "Main block not displaying config class"

        # Check for host/port configuration
        if "os.environ.get('FLASK_HOST'" not in content:
            return False, "Main block missing FLASK_HOST configuration"

        if "os.environ.get('FLASK_PORT'" not in content:
            return False, "Main block missing FLASK_PORT configuration"

        return True, "Main block displays environment info and handles host/port"
    except Exception as e:
        return False, f"Error checking main block: {str(e)}"


def test_gitignore():
    """Test that .gitignore has environment patterns."""
    try:
        with open('.gitignore', 'r') as f:
            content = f.read()

        required_patterns = ['.env', '.env.local', '.env.*.local', '*.backup']

        for pattern in required_patterns:
            if pattern not in content:
                return False, f".gitignore missing pattern: {pattern}"

        return True, ".gitignore has all environment file patterns"
    except Exception as e:
        return False, f"Error checking .gitignore: {str(e)}"


def test_env_example_content():
    """Test that .env.example has required variables."""
    try:
        with open('.env.example', 'r') as f:
            content = f.read()

        required_vars = ['SECRET_KEY', 'FLASK_ENV', 'FLASK_DEBUG', 'MAX_UPLOAD_SIZE']

        for var in required_vars:
            if var not in content:
                return False, f".env.example missing variable: {var}"

        return True, ".env.example has all required variables"
    except Exception as e:
        return False, f"Error checking .env.example: {str(e)}"


def main():
    """Run all configuration tests."""
    tests = [
        ("Config file exists", test_config_file_exists),
        ("Config imports work", test_config_imports),
        (".env.example exists", test_env_example_exists),
        (".env file exists", test_env_file_exists),
        ("Config classes correct", test_config_classes),
        ("get_config() function", test_get_config_function),
        ("app.py imports", test_app_py_imports),
        ("Article content function", test_article_content_function),
        ("Main block updated", test_main_block),
        (".gitignore updated", test_gitignore),
        (".env.example content", test_env_example_content),
    ]

    print("=" * 70)
    print("PHASE 2: CONFIGURATION & ENVIRONMENT SETUP - TESTING")
    print("=" * 70)
    print()

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            success, message = test_func()
            if success:
                print(f"✓ PASS | {test_name}")
                print(f"   {message}")
                passed += 1
            else:
                print(f"✗ FAIL | {test_name}")
                print(f"   {message}")
                failed += 1
        except Exception as e:
            print(f"✗ ERROR | {test_name}")
            print(f"   Exception: {str(e)}")
            failed += 1
        print()

    print("=" * 70)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    if failed > 0:
        print(f"WARNING: {failed} test(s) failed!")
    else:
        print("ALL PHASE 2 TESTS PASSED ✓")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
