"""
Core AI agent functionality for point cloud analysis.
"""
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from analysis.point_cloud_processor import (
    load_las_file, run_analysis, reconstruct_and_save_3d_mesh,
    set_global_processor, PointCloudProcessor
)
from config import ModelConfig
from utils.logger import get_logger
from utils.exceptions import AgentExecutionError

logger = get_logger(__name__)


class PointCloudAnalysisAgent:
    """AI Agent for point cloud analysis tasks."""
    
    def __init__(self, config: ModelConfig, parent_window=None):
        """
        Initialize the point cloud analysis agent.
        
        Args:
            config: Model configuration parameters
            parent_window: Parent window for file dialogs
        """
        self.config = config
        self.parent_window = parent_window
        self.llm = self._create_llm()
        self.processor = self._create_processor()
        self.tools = self._create_tools()
        self.agent_executor = self._create_agent_executor()
        
    def _create_llm(self) -> ChatGoogleGenerativeAI:
        """Create the language model instance."""
        try:
            llm = ChatGoogleGenerativeAI(
                model=self.config.model_name,
                temperature=self.config.temperature
            )
            logger.info(f"Created LLM with model: {self.config.model_name}")
            return llm
        except Exception as e:
            logger.error(f"Failed to create LLM: {e}")
            raise AgentExecutionError(f"Failed to initialize language model: {e}")
    
    def _create_processor(self):
        """Create the point cloud processor."""
        from config import AnalysisConfig
        from analysis.point_cloud_processor import PointCloudProcessor
        return PointCloudProcessor(AnalysisConfig(), self.parent_window)
    
    def _create_tools(self) -> List:
        """Create the list of available tools."""
        # Set the global processor for tool functions
        set_global_processor(self.processor)
        return [load_las_file, run_analysis, reconstruct_and_save_3d_mesh]
    
    def _create_prompt_template(self) -> PromptTemplate:
        """Create the prompt template for the agent."""
        prompt_template = """
You are a professional engineer specializing in LiDAR data analysis. Complete the user's objective by thinking step by step and using the available tools.

MANDATORY RULES:
1. Always start by calling `load_las_file` to load the data.
2. Then use `run_analysis` to process the data.
3. If a step fails, stop and report the error.
4. You MUST write 'Action:' after each 'Thought:'.
5. Use the exact tool names provided in the tool list.

AVAILABLE TOOLS:
{tools}

USE THIS FORMAT:

Objective: the objective you must complete
Thought: you must always think about what to do and evaluate the results of the previous step.
Action: the action to take, must be one of the following tools [{tool_names}]
Action Input: the input for the action, in JSON format if needed.
Observation: the result of the action
(this Thought/Action/Action Input/Observation loop can repeat multiple times)
Thought: Now I have the final answer.
Final Answer: the final detailed answer for the user.

BEGIN!

Objective: {input}
Thought:{agent_scratchpad}
"""
        return PromptTemplate.from_template(prompt_template)
    
    def _create_agent_executor(self) -> AgentExecutor:
        """Create the agent executor."""
        try:
            prompt = self._create_prompt_template()
            agent = create_react_agent(self.llm, self.tools, prompt)
            
            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=self.config.max_iterations
            )
            
            logger.info("Created agent executor successfully")
            return agent_executor
            
        except Exception as e:
            logger.error(f"Failed to create agent executor: {e}")
            raise AgentExecutionError(f"Failed to create agent executor: {e}")
    
    def execute(self, objective: str) -> str:
        """
        Execute the agent with the given objective.
        
        Args:
            objective: The task objective for the agent
            
        Returns:
            The agent's response
            
        Raises:
            AgentExecutionError: If agent execution fails
        """
        try:
            logger.info(f"Executing agent with objective: {objective}")
            result = self.agent_executor.invoke({"input": objective})
            response = result.get('output', 'No output generated.')
            logger.info("Agent execution completed successfully")
            return response
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            raise AgentExecutionError(f"Agent execution failed: {e}")


def create_agent_executor() -> AgentExecutor:
    """
    Create an agent executor with default configuration.
    This function maintains backward compatibility.
    
    Returns:
        Configured AgentExecutor instance
    """
    config = ModelConfig()
    agent = PointCloudAnalysisAgent(config, parent_window=None)
    return agent.agent_executor
