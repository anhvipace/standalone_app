"""
Custom exceptions for the Point Cloud Analysis Agent application.
"""


class PointCloudAnalysisError(Exception):
    """Base exception for point cloud analysis errors."""
    pass


class FileNotFoundError(PointCloudAnalysisError):
    """Raised when a required file is not found."""
    pass


class InvalidFileFormatError(PointCloudAnalysisError):
    """Raised when a file format is invalid or unsupported."""
    pass


class AnalysisError(PointCloudAnalysisError):
    """Raised when analysis fails."""
    pass


class MeshReconstructionError(PointCloudAnalysisError):
    """Raised when mesh reconstruction fails."""
    pass


class AgentExecutionError(PointCloudAnalysisError):
    """Raised when agent execution fails."""
    pass
