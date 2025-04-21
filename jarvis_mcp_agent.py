import asyncio
import json
import os
import time
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("JARVIS_MCP_Agent")

class JARVISAction(BaseModel):
    """An action that JARVIS can take during the agent execution"""
    action_type: str = Field(..., description="Type of action to take (search, query, execute, etc)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the action")
    
class JARVISActionResult(BaseModel):
    """Result of a JARVIS action"""
    success: bool = Field(..., description="Whether the action was successful")
    data: Any = Field(None, description="Data returned from the action")
    error: Optional[str] = Field(None, description="Error message if action failed")

class JARVISMCPClient:
    """Client for connecting to JARVIS MCP server"""
    def __init__(self, server_url: str = "http://localhost:8000", config_path: Optional[str] = None):
        self.server_url = server_url
        self.config = {}
        self.sessions = []
        self.connection_id = None
        
        if config_path:
            self.load_config(config_path)
            
    def load_config(self, config_path: str) -> None:
        """Load configuration from a JSON file"""
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
                
            # Update server URL if specified in config
            if "serverUrl" in self.config:
                self.server_url = self.config["serverUrl"]
                
            logger.info(f"Loaded config from {config_path}")
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
    
    @classmethod
    def from_config_file(cls, config_path: str) -> "JARVISMCPClient":
        """Create a client from a config file"""
        client = cls()
        client.load_config(config_path)
        return client
            
    async def connect(self) -> bool:
        """Connect to the JARVIS MCP server"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.server_url}/mcp/connect") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.connection_id = data.get("connection_id")
                        logger.info(f"Connected to JARVIS MCP server with ID: {self.connection_id}")
                        return True
                        
            logger.error("Failed to connect to JARVIS MCP server")
            return False
        except Exception as e:
            logger.error(f"Error connecting to JARVIS MCP server: {e}")
            return False
            
    async def execute_action(self, action: JARVISAction) -> JARVISActionResult:
        """Execute an action through the JARVIS MCP server"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "action_type": action.action_type,
                    "parameters": action.parameters,
                    "connection_id": self.connection_id
                }
                
                async with session.post(f"{self.server_url}/mcp/action", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return JARVISActionResult(
                            success=True,
                            data=data.get("result")
                        )
                    else:
                        error_text = await response.text()
                        return JARVISActionResult(
                            success=False,
                            error=f"Error: {response.status} - {error_text}"
                        )
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return JARVISActionResult(
                success=False,
                error=f"Exception: {str(e)}"
            )
            
    async def close_session(self, session_id: str) -> bool:
        """Close a specific session"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server_url}/mcp/close_session", 
                    json={"session_id": session_id}
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Error closing session {session_id}: {e}")
            return False
            
    async def close_all_sessions(self) -> bool:
        """Close all active sessions"""
        success = True
        for session_id in self.sessions:
            if not await self.close_session(session_id):
                success = False
        self.sessions = []
        return success

class JARVISMCPAgent:
    """Advanced JARVIS agent using the MCP pattern"""
    
    def __init__(
        self, 
        llm: Any,
        client: JARVISMCPClient,
        max_steps: int = 20,
        system_prompt: Optional[str] = None
    ):
        self.llm = llm
        self.client = client
        self.max_steps = max_steps
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.conversation_history = []
        self.step_results = []
        
    def _default_system_prompt(self) -> str:
        """Default system prompt for the agent"""
        return (
            "You are JARVIS, an advanced AI assistant with access to various tools and capabilities. "
            "You can use tools to search for information, execute code, control devices, and more. "
            "Always respond to the user's needs accurately and helpfully. "
            "When you need to use a tool, format your response as a JSON object with 'action_type' and 'parameters'."
        )
        
    async def _initialize_session(self) -> bool:
        """Initialize a new session with the MCP server"""
        if not self.client.connection_id:
            return await self.client.connect()
        return True
        
    async def _execute_step(self, user_query: str, conversation_history: List[dict]) -> JARVISActionResult:
        """Execute a single step in the agent's reasoning process"""
        
        # Prepare messages for the LLM
        messages = [SystemMessage(content=self.system_prompt)]
        
        # Add conversation history
        for msg in conversation_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add the current query if it's not already in history
        if not conversation_history or conversation_history[-1]["role"] != "user":
            messages.append(HumanMessage(content=user_query))
        
        # Get response from LLM
        response = await self.llm.ainvoke(messages)
        response_content = response.content
        
        # Check if the response contains an action to execute
        try:
            # Try to parse JSON from the response
            if "{" in response_content and "}" in response_content:
                json_part = response_content[response_content.find("{"):response_content.rfind("}")+1]
                action_data = json.loads(json_part)
                
                if "action_type" in action_data:
                    action = JARVISAction(
                        action_type=action_data["action_type"],
                        parameters=action_data.get("parameters", {})
                    )
                    
                    # Execute the action
                    result = await self.client.execute_action(action)
                    
                    # Add the result to the conversation
                    conversation_history.append({"role": "assistant", "content": response_content})
                    conversation_history.append({
                        "role": "system", 
                        "content": f"Action result: {json.dumps(result.dict())}"
                    })
                    
                    return result
            
            # If no action detected, just return the response
            conversation_history.append({"role": "assistant", "content": response_content})
            return JARVISActionResult(
                success=True,
                data=response_content
            )
            
        except Exception as e:
            logger.error(f"Error executing step: {e}")
            return JARVISActionResult(
                success=False,
                error=f"Error: {str(e)}"
            )
    
    async def run(
        self, 
        query: str, 
        conversation_history: Optional[List[dict]] = None,
        max_steps: Optional[int] = None
    ) -> Dict[str, Any]:
        """Run the agent on a query"""
        
        # Initialize or use provided conversation history
        history = conversation_history or []
        if not history:
            history.append({"role": "user", "content": query})
            
        # Initialize session if needed
        if not await self._initialize_session():
            return {
                "success": False,
                "error": "Failed to initialize MCP session",
                "result": None
            }
            
        steps_taken = 0
        max_steps_to_use = max_steps or self.max_steps
        final_result = None
        
        # Step through the agent's reasoning process
        while steps_taken < max_steps_to_use:
            step_result = await self._execute_step(query, history)
            steps_taken += 1
            
            self.step_results.append(step_result)
            
            # If the action result indicates completion, break the loop
            if step_result.success and not isinstance(step_result.data, dict):
                # This might be a final response rather than an action result
                final_result = step_result.data
                break
                
            # If there was an error, break the loop
            if not step_result.success:
                break
                
        # Compile the final response
        return {
            "success": True,
            "steps_taken": steps_taken,
            "conversation": history,
            "result": final_result or (self.step_results[-1].data if self.step_results else None)
        }
        
    async def chat(self, query: str) -> str:
        """Simple chat interface for direct interactions"""
        result = await self.run(query, self.conversation_history)
        
        if result["success"]:
            return result["result"]
        else:
            return f"Error: {result.get('error', 'Unknown error')}"

# Helper function to create a JARVIS MCP agent from a config file
async def create_jarvis_agent(
    config_path: str = "jarvis_mcp_config.json",
    openai_api_key: Optional[str] = None,
    model_name: str = "gpt-4o"
) -> JARVISMCPAgent:
    """Create a JARVIS MCP agent from a config file"""
    
    # Load API key from environment if not provided
    api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key must be provided or set as OPENAI_API_KEY environment variable")
    
    # Create LLM
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        temperature=0.7
    )
    
    # Create client
    client = JARVISMCPClient.from_config_file(config_path)
    
    # Create agent
    agent = JARVISMCPAgent(llm=llm, client=client)
    
    return agent 