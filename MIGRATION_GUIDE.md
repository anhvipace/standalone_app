# Migration Guide

This guide helps you transition from the old project structure to the new refactored version.

## What Changed

### 1. Project Structure
**Old Structure:**
```
├── agent_core.py
├── analysis_tools.py
├── main_gui.py
└── main_gui.pyproj
```

**New Structure:**
```
├── agent/                 # AI agent modules
│   ├── __init__.py
│   └── agent_core.py
├── analysis/              # Point cloud analysis modules
│   ├── __init__.py
│   └── point_cloud_processor.py
├── gui/                   # GUI modules
│   ├── __init__.py
│   └── main_window.py
├── utils/                 # Utility modules
│   ├── __init__.py
│   ├── exceptions.py
│   └── logger.py
├── tests/                 # Test modules
│   ├── __init__.py
│   ├── test_config.py
│   └── test_exceptions.py
├── config.py              # Configuration management
├── main.py               # New main entry point
├── requirements.txt      # Dependencies
├── setup.py             # Package setup
└── README.md            # Documentation
```

### 2. Entry Point
- **Old**: `python main_gui.py`
- **New**: `python main.py`

### 3. Configuration
- **Old**: Hardcoded values in code
- **New**: Centralized configuration system with environment variable support

### 4. Error Handling
- **Old**: Basic try-catch blocks
- **New**: Custom exception hierarchy with proper logging

### 5. File Handling
- **Old**: Basic file existence checks
- **New**: Comprehensive file validation with dialog support

### 6. Code Organization
- **Old**: Monolithic files with mixed concerns
- **New**: Separated concerns with clear module boundaries

## Migration Steps

### 1. Update Your Environment
```bash
# Install new dependencies
pip install -r requirements.txt
```

### 2. Update Your Scripts
If you have any scripts that import from the old modules, update them:

**Old imports:**
```python
from agent_core import create_agent_executor
from analysis_tools import load_las_file, run_analysis, reconstruct_and_save_3d_mesh
```

**New imports:**
```python
from agent.agent_core import create_agent_executor
from analysis.point_cloud_processor import load_las_file, run_analysis, reconstruct_and_save_3d_mesh
```

### 3. Configuration
You can now configure the application through environment variables:

```bash
# Set model configuration
export MODEL_NAME="models/gemini-pro-latest"
export TEMPERATURE="0.0"
export LOG_LEVEL="INFO"

# Run the application
python main.py
```

### 4. Backward Compatibility
The old `main_gui.py` file is still included for backward compatibility, but it's recommended to use the new `main.py` entry point.

## New Features

### 1. Better Error Handling
- Custom exception types for different error scenarios
- Comprehensive logging throughout the application
- User-friendly error messages in the GUI

### 2. Configuration Management
- Centralized configuration system
- Environment variable support
- Easy parameter tuning

### 3. Improved GUI
- File browser for LAS/LAZ file selection
- Better status indicators
- Clear output formatting
- Error message display
- File information display

### 4. Smart File Handling
- Automatic file validation
- Dialog-based file selection when files are not found
- Support for both LAS and LAZ formats
- File information display

### 5. Testing
- Unit tests for core functionality
- Test configuration validation
- Exception handling tests
- File handling tests

### 6. Documentation
- Comprehensive README
- Code documentation
- Migration guide

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're using the new import paths
2. **Missing Dependencies**: Run `pip install -r requirements.txt`
3. **Configuration Issues**: Check environment variables or use default configuration

### Getting Help

If you encounter issues during migration:
1. Check the logs for detailed error messages
2. Verify all dependencies are installed
3. Ensure you're using the correct import paths
4. Check the configuration settings

## Rollback Plan

If you need to rollback to the old version:
1. Use `main_gui.py` instead of `main.py`
2. The old files are still present and functional
3. Remove the new package directories if not needed

## Next Steps

After successful migration:
1. Explore the new configuration options
2. Try the new GUI features
3. Run the test suite to verify everything works
4. Consider contributing improvements to the codebase
