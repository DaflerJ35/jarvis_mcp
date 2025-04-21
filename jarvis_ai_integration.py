import requests
import json
import asyncio
import aiohttp
import time
import os
import datetime
import logging
import re
import threading
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("jarvis_ai.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("JARVIS-AI")

class ClaudeConnector:
    """
    Connects JARVIS to Claude via MCP protocol for advanced AI capabilities
    """
    def __init__(self, mcp_url="http://localhost:8000/mcp/sse"):
        self.mcp_url = mcp_url
        self.session = None
        self.connected = False
        self.response_callback = None
        self.session_id = f"jarvis-{int(time.time())}"
        self.message_history = []
        self.system_context = """You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), the advanced AI assistant created by Tony Stark.
You have a helpful, knowledgeable, and slightly witty personality, similar to the JARVIS from the Iron Man movies.
Your responses should be concise, intelligent, and occasionally include subtle humor.
You assist with information, perform calculations, and provide analysis on various topics.
When responding to queries, try to be helpful while maintaining your JARVIS persona."""
    
    async def connect(self):
        """
        Connect to the MCP SSE endpoint
        """
        if self.connected:
            return True
        
        try:
            logger.info(f"Connecting to MCP at {self.mcp_url}")
            self.session = aiohttp.ClientSession()
            # Just do a GET request to test connection
            response = await self.session.get(self.mcp_url)
            if response.status == 200:
                self.connected = True
                logger.info("Connected to MCP successfully")
                return True
            else:
                logger.error(f"Failed to connect to MCP: {response.status}")
                return False
        except Exception as e:
            logger.error(f"Error connecting to MCP: {str(e)}")
            if self.session:
                await self.session.close()
                self.session = None
            return False
    
    async def disconnect(self):
        """
        Disconnect from the MCP SSE endpoint
        """
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False
        logger.info("Disconnected from MCP")
        return True

    async def send_jsonrpc_request(self, method, params):
        """
        Send a JSON-RPC request to the MCP endpoint
        """
        if not self.connected:
            success = await self.connect()
            if not success:
                return {"error": "Not connected to MCP"}
        
        try:
            request_data = {
                "jsonrpc": "2.0",
                "id": f"{self.session_id}-{int(time.time())}",
                "method": method,
                "params": params
            }
            
            async with self.session.post(self.mcp_url, json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"MCP request failed with status {response.status}: {error_text}")
                    return {"error": f"MCP request failed: {error_text}"}
        except Exception as e:
            logger.error(f"Error sending MCP request: {str(e)}")
            return {"error": f"Error sending MCP request: {str(e)}"}
    
    async def chat_with_claude(self, message, system_message=None, history=None):
        """
        Send a chat message to Claude via MCP
        """
        if not system_message:
            system_message = self.system_context
        
        if not history:
            history = self.message_history
        
        # Prepare the chat request
        method = "query_conversation"
        params = {
            "content": message,
            "system_message": system_message,
            "history": history,
            "model": "claude",  # Use Claude model
            "temperature": 0.7,
            "stream": False
        }
        
        # Send the request
        result = await self.send_jsonrpc_request(method, params)
        
        # Update message history with the user message and response
        if "result" in result and "response" in result["result"]:
            response_text = result["result"]["response"]
            
            # Add to history
            self.message_history.append({
                "role": "user",
                "content": message
            })
            self.message_history.append({
                "role": "assistant",
                "content": response_text
            })
            
            # Trim history if it gets too long (keep last 10 messages)
            if len(self.message_history) > 20:
                self.message_history = self.message_history[-20:]
            
            return response_text
        elif "error" in result:
            return f"Error: {result['error']}"
        else:
            return "Error: Unexpected response format"
    
    async def knowledge_query(self, query):
        """
        Query Claude for factual knowledge on a topic
        """
        # Add special system message for factual queries
        system_message = self.system_context + """
For this query, focus on providing accurate, factual information.
Your response should be concise but thorough.
If uncertain about any detail, acknowledge the uncertainty rather than speculating."""
        
        return await self.chat_with_claude(query, system_message=system_message)
    
    async def analyze_data(self, data, instructions=None):
        """
        Ask Claude to analyze provided data
        """
        if not instructions:
            instructions = "Please analyze this data and provide insights."
        
        prompt = f"{instructions}\n\nData:\n{data}"
        
        # Add special system message for data analysis
        system_message = self.system_context + """
For this analysis task, focus on extracting key insights from the provided data.
Organize your findings in a clear structure.
Highlight patterns, anomalies, and important points."""
        
        return await self.chat_with_claude(prompt, system_message=system_message)
    
    def set_persona(self, persona="jarvis"):
        """
        Set the AI's persona/personality
        """
        personas = {
            "jarvis": """You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), the advanced AI assistant created by Tony Stark.
You have a helpful, knowledgeable, and slightly witty personality, similar to the JARVIS from the Iron Man movies.
Your responses should be concise, intelligent, and occasionally include subtle humor.
You assist with information, perform calculations, and provide analysis on various topics.""",
            
            "friday": """You are F.R.I.D.A.Y., the AI assistant that succeeded J.A.R.V.I.S. in the Iron Man universe.
You are efficient, helpful, and have a slightly feminine personality.
Your responses should be clear, direct, and occasionally informal.""",
            
            "jarvis_professional": """You are J.A.R.V.I.S., an advanced AI assistant designed for professional environments.
Your responses should be formal, precise, and comprehensive.
Focus on delivering accurate information with minimal embellishment.""",
            
            "jarvis_friendly": """You are J.A.R.V.I.S., a friendly and approachable AI assistant.
Your responses should be warm, helpful, and conversational.
Use a more casual tone while still providing accurate information."""
        }
        
        if persona.lower() in personas:
            self.system_context = personas[persona.lower()]
            return f"Persona set to {persona}"
        else:
            return f"Unknown persona: {persona}. Using default JARVIS persona."
    
    def reset_conversation(self):
        """
        Reset the conversation history
        """
        self.message_history = []
        return "Conversation history has been reset."
    
    def get_memory_snapshot(self):
        """
        Get a snapshot of the current conversation memory
        """
        return {
            "message_count": len(self.message_history),
            "messages": self.message_history
        }

class JARVISAIBrain:
    """
    JARVIS AI Brain that uses Claude for advanced intelligence
    """
    def __init__(self, mcp_url="http://localhost:8000/mcp/sse"):
        self.claude = ClaudeConnector(mcp_url)
        self.response_callbacks = []  # Callbacks for when responses are received
        self.memory = {}  # Memory storage
        
    async def initialize(self):
        """
        Initialize the AI brain and connect to Claude
        """
        return await self.claude.connect()
    
    async def shutdown(self):
        """
        Shutdown the AI brain and disconnect from Claude
        """
        return await self.claude.disconnect()
    
    async def ask(self, question):
        """
        Ask a question to the AI
        """
        return await self.claude.chat_with_claude(question)
    
    async def get_knowledge(self, query):
        """
        Query for factual knowledge
        """
        return await self.claude.knowledge_query(query)
    
    async def analyze(self, data, instructions=None):
        """
        Analyze data
        """
        return await self.claude.analyze_data(data, instructions)
    
    def change_personality(self, persona="jarvis"):
        """
        Change the AI personality
        """
        return self.claude.set_persona(persona)
    
    def clear_memory(self):
        """
        Clear conversation memory
        """
        return self.claude.reset_conversation()
    
    def memorize(self, key, value):
        """
        Store information in memory
        """
        self.memory[key] = {
            "value": value,
            "timestamp": datetime.datetime.now().isoformat()
        }
        return f"I've memorized this information under '{key}'"
    
    def recall(self, key):
        """
        Recall information from memory
        """
        if key in self.memory:
            return self.memory[key]["value"]
        return f"I don't have any information stored under '{key}'"
    
    def list_memories(self):
        """
        List all stored memories
        """
        if not self.memory:
            return "My memory is currently empty."
        
        keys = list(self.memory.keys())
        return f"I have {len(keys)} memories stored: {', '.join(keys)}"
    
    def forget(self, key):
        """
        Forget a specific memory
        """
        if key in self.memory:
            del self.memory[key]
            return f"I've forgotten the information stored under '{key}'"
        return f"I don't have any information stored under '{key}'"
    
    async def process_command(self, command):
        """
        Process a natural language command
        """
        # Extract command type using regex patterns
        patterns = [
            (r"(?i)what\s+(?:is|are|was|were).*", "knowledge"),
            (r"(?i)tell\s+me\s+about.*", "knowledge"),
            (r"(?i)how\s+(?:to|do|does|did).*", "knowledge"),
            (r"(?i)who\s+(?:is|are|was|were).*", "knowledge"),
            (r"(?i)where\s+(?:is|are|was|were).*", "knowledge"),
            (r"(?i)when\s+(?:is|are|was|were).*", "knowledge"),
            (r"(?i)why\s+(?:is|are|was|were).*", "knowledge"),
            (r"(?i)analyze\s+.*", "analyze"),
            (r"(?i)examine\s+.*", "analyze"),
            (r"(?i)review\s+.*", "analyze"),
            (r"(?i)(?:memorize|remember|store)\s+(.*?)\s+as\s+(.*)", "memorize"),
            (r"(?i)(?:recall|retrieve|get)\s+(.*)", "recall"),
            (r"(?i)(?:list|show)\s+(?:all\s+)?memories", "list_memories"),
            (r"(?i)(?:forget|delete|remove)\s+(.*)", "forget"),
            (r"(?i)(?:change|switch|set)\s+(?:your\s+)?(?:personality|persona).*", "change_personality"),
            (r"(?i)(?:reset|clear|restart)\s+(?:conversation|memory|chat)", "clear_memory"),
        ]
        
        command_type = "general"
        
        for pattern, cmd_type in patterns:
            if re.match(pattern, command):
                command_type = cmd_type
                break
        
        # Handle different command types
        if command_type == "knowledge":
            return await self.get_knowledge(command)
        elif command_type == "analyze":
            # Extract what to analyze
            analysis_text = re.sub(r"(?i)(?:analyze|examine|review)\s+", "", command, 1)
            return await self.analyze(analysis_text)
        elif command_type == "memorize":
            match = re.match(r"(?i)(?:memorize|remember|store)\s+(.*?)\s+as\s+(.*)", command)
            if match:
                value = match.group(1).strip()
                key = match.group(2).strip()
                return self.memorize(key, value)
        elif command_type == "recall":
            match = re.match(r"(?i)(?:recall|retrieve|get)\s+(.*)", command)
            if match:
                key = match.group(1).strip()
                return self.recall(key)
        elif command_type == "list_memories":
            return self.list_memories()
        elif command_type == "forget":
            match = re.match(r"(?i)(?:forget|delete|remove)\s+(.*)", command)
            if match:
                key = match.group(1).strip()
                return self.forget(key)
        elif command_type == "change_personality":
            # Try to extract desired personality
            match = re.search(r"(?i)(?:to|as)\s+(\w+)", command)
            persona = "jarvis"
            if match:
                persona = match.group(1).lower()
            return self.change_personality(persona)
        elif command_type == "clear_memory":
            return self.clear_memory()
            
        # Default to general chat
        return await self.ask(command)
    
    def register_response_callback(self, callback):
        """
        Register a callback for when responses are received
        """
        if callback not in self.response_callbacks:
            self.response_callbacks.append(callback)
    
    def remove_response_callback(self, callback):
        """
        Remove a response callback
        """
        if callback in self.response_callbacks:
            self.response_callbacks.remove(callback)

# Test function
async def test_jarvis_ai():
    print("Initializing JARVIS AI Brain...")
    brain = JARVISAIBrain()
    
    if await brain.initialize():
        print("Connected to Claude via MCP!")
        
        # Test basic questions
        question = "What is the meaning of life?"
        print(f"\nQuestion: {question}")
        answer = await brain.ask(question)
        print(f"Answer: {answer}")
        
        # Test knowledge query
        query = "Tell me about quantum computing in simple terms"
        print(f"\nQuery: {query}")
        knowledge = await brain.get_knowledge(query)
        print(f"Knowledge: {knowledge}")
        
        # Test memory
        print("\nTesting memory...")
        memorize = brain.memorize("location", "Tony's workshop")
        print(memorize)
        
        recall = brain.recall("location")
        print(f"Recalling location: {recall}")
        
        # Test command processing
        command = "analyze the recent trends in artificial intelligence"
        print(f"\nCommand: {command}")
        result = await brain.process_command(command)
        print(f"Result: {result}")
        
        # Cleanup
        await brain.shutdown()
        print("\nJARVIS AI Brain shutdown complete")
    else:
        print("Failed to connect to Claude via MCP")

if __name__ == "__main__":
    asyncio.run(test_jarvis_ai()) 