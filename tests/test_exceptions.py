"""
Tests for custom exceptions.
"""
import pytest
from utils.exceptions import (
    PointCloudAnalysisError,
    FileNotFoundError,
    InvalidFileFormatError,
    AnalysisError,
    MeshReconstructionError,
    AgentExecutionError
)


def test_point_cloud_analysis_error():
    """Test base exception."""
    with pytest.raises(PointCloudAnalysisError):
        raise PointCloudAnalysisError("Test error")


def test_file_not_found_error():
    """Test file not found error."""
    with pytest.raises(FileNotFoundError):
        raise FileNotFoundError("File not found")


def test_invalid_file_format_error():
    """Test invalid file format error."""
    with pytest.raises(InvalidFileFormatError):
        raise InvalidFileFormatError("Invalid format")


def test_analysis_error():
    """Test analysis error."""
    with pytest.raises(AnalysisError):
        raise AnalysisError("Analysis failed")


def test_mesh_reconstruction_error():
    """Test mesh reconstruction error."""
    with pytest.raises(MeshReconstructionError):
        raise MeshReconstructionError("Mesh reconstruction failed")


def test_agent_execution_error():
    """Test agent execution error."""
    with pytest.raises(AgentExecutionError):
        raise AgentExecutionError("Agent execution failed")
