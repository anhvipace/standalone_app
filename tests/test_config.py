"""
Tests for configuration management.
"""
import pytest
from config import ModelConfig, AnalysisConfig, UIConfig, AppConfig, get_default_config


def test_model_config_defaults():
    """Test default model configuration."""
    config = ModelConfig()
    assert config.model_name == "models/gemini-pro-latest"
    assert config.temperature == 0.0
    assert config.max_iterations == 30


def test_analysis_config_defaults():
    """Test default analysis configuration."""
    config = AnalysisConfig()
    assert config.min_wall_height == 2.0
    assert config.ransac_distance == 0.1
    assert config.ground_angle == 15.0
    assert config.wall_angle == 60.0
    assert config.voxel_size == 0.1
    assert config.alpha_shape_alpha == 0.5


def test_ui_config_defaults():
    """Test default UI configuration."""
    config = UIConfig()
    assert config.window_title == "AI Agent - Point Cloud Processor"
    assert config.window_size == "800x600"
    assert config.theme == "dark"
    assert config.font_family == "Segoe UI"
    assert config.font_size == 10
    assert config.monospace_font == "Consolas"


def test_app_config_defaults():
    """Test default application configuration."""
    config = get_default_config()
    assert isinstance(config.model, ModelConfig)
    assert isinstance(config.analysis, AnalysisConfig)
    assert isinstance(config.ui, UIConfig)
    assert config.log_level == "INFO"
    assert config.working_directory is not None
