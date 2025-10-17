"""
AI-powered report generation for point cloud analysis.
"""
import os
from typing import Dict, Any, Optional
import google.generativeai as genai

from utils.logger import get_logger
from utils.exceptions import PointCloudAnalysisError

logger = get_logger(__name__)


class AIReportGenerator:
    """AI-powered report generator for point cloud analysis results."""
    
    def __init__(self):
        """Initialize the AI report generator."""
        self._configure_api()
    
    def _configure_api(self):
        """Configure the Google Generative AI API."""
        try:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set.")
            genai.configure(api_key=api_key)
            logger.info("Google Generative AI configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Google AI: {e}")
            raise PointCloudAnalysisError(f"Could not configure AI service: {e}")
    
    def generate_analysis_report(self, analysis_data: Dict[str, Any]) -> str:
        """
        Generate a comprehensive analysis report.
        
        Args:
            analysis_data: Dictionary containing analysis results and metadata
            
        Returns:
            Generated report text
            
        Raises:
            PointCloudAnalysisError: If report generation fails
        """
        try:
            model = genai.GenerativeModel('models/gemini-flash-latest')
            
            prompt = self._create_report_prompt(analysis_data)
            response = model.generate_content(prompt)
            
            logger.info("AI report generated successfully")
            return response.text
            
        except Exception as e:
            logger.error(f"Failed to generate AI report: {e}")
            raise PointCloudAnalysisError(f"Report generation failed: {e}")
    
    def _create_report_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """Create the prompt for AI report generation."""
        file_info = analysis_data.get('file_info', {})
        analysis_params = analysis_data.get('analysis_params', {})
        results = analysis_data.get('results', {})
        
        prompt = f"""
As a professional engineering assistant, write a comprehensive technical summary report based on the following point cloud analysis data:

**Project Information:**
- File Name: {file_info.get('name', 'N/A')}
- Total Points: {file_info.get('point_count', 'N/A'):,}
- File Size: {file_info.get('size_mb', 'N/A')} MB
- Y-Axis Range: [{file_info.get('y_min', 'N/A'):.2f}m, {file_info.get('y_max', 'N/A'):.2f}m]

**Analysis Parameters Used:**
- Minimum Wall Height: {analysis_params.get('min_wall_height', 'N/A')} m
- RANSAC Distance: {analysis_params.get('ransac_distance', 'N/A')} m
- Ground Angle Threshold: {analysis_params.get('ground_angle', 'N/A')} degrees
- Wall Angle Threshold: {analysis_params.get('wall_angle', 'N/A')} degrees

**Analysis Results:**
- Ground Points: {results.get('ground_points', 'N/A'):,}
- Wall 1 Points: {results.get('wall1_points', 'N/A'):,}
- Wall 2 Points: {results.get('wall2_points', 'N/A'):,}
- Analysis Status: {results.get('status', 'N/A')}

**Instructions:**
- Structure the report with clear headings (Summary, Analysis Parameters, Results, Interpretation, Recommendations)
- Use a formal and technical tone appropriate for engineering documentation
- Include quantitative analysis where possible
- Conclude with practical recommendations for further analysis or design considerations
- Keep the report concise but comprehensive (approximately 300-500 words)
- Focus on the technical significance of the findings
"""

        return prompt
    
    def generate_cross_section_report(self, cross_section_data: Dict[str, Any]) -> str:
        """
        Generate a report for cross-section analysis.
        
        Args:
            cross_section_data: Dictionary containing cross-section analysis data
            
        Returns:
            Generated report text
        """
        try:
            model = genai.GenerativeModel('models/gemini-flash-latest')
            
            prompt = f"""
As a civil engineering specialist, analyze the following tunnel cross-section data and provide a technical assessment:

**Cross-Section Information:**
- Y Position: {cross_section_data.get('y_position', 'N/A')} m
- Ground Points: {cross_section_data.get('ground_count', 'N/A'):,}
- Wall Points: {cross_section_data.get('wall_count', 'N/A'):,}
- Profile Type: {cross_section_data.get('profile_type', 'N/A')}

**Measurements:**
{cross_section_data.get('measurements', 'No measurements available')}

**Instructions:**
- Provide a brief technical assessment of the cross-section geometry
- Comment on the tunnel profile and any notable features
- Suggest any potential issues or areas of concern
- Keep the report concise (150-250 words)
- Use professional engineering terminology
"""

            response = model.generate_content(prompt)
            logger.info("Cross-section report generated successfully")
            return response.text
            
        except Exception as e:
            logger.error(f"Failed to generate cross-section report: {e}")
            raise PointCloudAnalysisError(f"Cross-section report generation failed: {e}")


def create_report_generator() -> AIReportGenerator:
    """Create and return a new AI report generator instance."""
    return AIReportGenerator()
