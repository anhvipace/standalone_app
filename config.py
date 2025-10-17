"""
Configuration management for the Point Cloud Analysis Agent application.
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelConfig:
    """Configuration for the AI model."""
    model_name: str = "models/gemini-pro-latest"
    temperature: float = 0.0
    max_iterations: int = 30


@dataclass
class AnalysisConfig:
    """Configuration for point cloud analysis parameters."""
    min_wall_height: float = 2.0
    ransac_distance: float = 0.1
    ground_angle: float = 15.0
    wall_angle: float = 60.0
    voxel_size: float = 0.1
    alpha_shape_alpha: float = 0.5


@dataclass
class UIConfig:
    """Configuration for the user interface."""
    window_title: str = "AI Agent - Point Cloud Processor"
    window_size: str = "800x600"
    theme: str = "dark"
    font_family: str = "Segoe UI"
    font_size: int = 10
    monospace_font: str = "Consolas"


@dataclass
class AppConfig:
    """Main application configuration."""
    model: ModelConfig
    analysis: AnalysisConfig
    ui: UIConfig
    log_level: str = "INFO"
    working_directory: Optional[str] = None

    def __post_init__(self):
        """Set working directory if not provided."""
        if self.working_directory is None:
            self.working_directory = os.getcwd()


def get_default_config() -> AppConfig:
    """Get the default application configuration."""
    return AppConfig(
        model=ModelConfig(),
        analysis=AnalysisConfig(),
        ui=UIConfig()
    )


def load_config_from_env() -> AppConfig:
    """Load configuration from environment variables."""
    config = get_default_config()
    
    # Override with environment variables if present
    if os.getenv("MODEL_NAME"):
        config.model.model_name = os.getenv("MODEL_NAME")
    if os.getenv("TEMPERATURE"):
        config.model.temperature = float(os.getenv("TEMPERATURE"))
    if os.getenv("LOG_LEVEL"):
        config.log_level = os.getenv("LOG_LEVEL")
    
    return config
