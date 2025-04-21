from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn
from starlette.responses import Response, StreamingResponse
import json
import asyncio
import os
import glob
import re
import random
import time
import subprocess
import sys
import logging
from typing import List, Dict, Any, Optional, Union
import datetime
from dataclasses import dataclass, asdict

# Create a very simple FastAPI app
app = FastAPI(title="JARVIS Integrated Server")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("jarvis_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("JARVIS")

# ==================== Knowledge Base ====================
class KnowledgeBase:
    def __init__(self):
        self.documents = []
        self.last_updated = datetime.datetime.now()
    
    def add_document(self, text: str, source: str, metadata: Optional[Dict[str, Any]] = None):
        doc = {
            "id": len(self.documents) + 1,
            "text": text,
            "source": source,
            "metadata": metadata or {},
            "created_at": datetime.datetime.now().isoformat()
        }
        self.documents.append(doc)
        self.last_updated = datetime.datetime.now()
        return doc["id"]
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        # Simple keyword search (in a real app, use vector embeddings)
        results = []
        for doc in self.documents:
            if query.lower() in doc["text"].lower():
                results.append(doc)
                if len(results) >= limit:
                    break
        return results

# ==================== Autonomous Agent ====================
@dataclass
class AgentState:
    """State of an autonomous agent task"""
    task_id: str
    status: str  # 'running', 'completed', 'error'
    current_step: str
    steps_completed: List[str]
    collected_data: Dict[str, Any]
    error: Optional[str] = None

class AutonomousAgent:
    """
    Simplified autonomous agent for task execution
    """
    def __init__(self):
        self.tasks = {}  # Store task states
    
    def start_task(self, task_description: str) -> str:
        """Start a new task and return its ID"""
        task_id = f"task_{int(time.time())}_{random.randint(1000, 9999)}"
        
        self.tasks[task_id] = AgentState(
            task_id=task_id,
            status="running",
            current_step="initializing",
            steps_completed=[],
            collected_data={},
            error=None
        )
        
        # Start background task execution
        asyncio.create_task(self._execute_task(task_id, task_description))
        
        return task_id
    
    async def _execute_task(self, task_id: str, task_description: str):
        """Execute a task in steps"""
        task = self.tasks[task_id]
        
        try:
            # Simulate task execution steps
            steps = [
                "analyzing_task",
                "gathering_information",
                "executing_actions",
                "finalizing_results"
            ]
            
            for step in steps:
                # Update state
                task.current_step = step
                
                # Simulate work
                await asyncio.sleep(2)
                
                # Add to completed steps
                task.steps_completed.append(step)
                
                # Add some simulated data
                task.collected_data[step] = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "result": f"Completed {step} for task: {task_description}"
                }
            
            # Mark as completed
            task.status = "completed"
            task.current_step = "completed"
            
        except Exception as e:
            # Handle errors
            task.status = "error"
            task.error = str(e)
    
    def get_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the current state of a task"""
        if task_id in self.tasks:
            return asdict(self.tasks[task_id])
        return None

# ==================== Code Execution ====================
class CodeExecution:
    """
    Simple code execution system
    """
    SUPPORTED_LANGUAGES = ["python", "javascript"]
    
    @staticmethod
    async def execute_code(code: str, language: str = "python") -> Dict[str, Any]:
        """Execute code in the specified language"""
        if language not in CodeExecution.SUPPORTED_LANGUAGES:
            return {
                "success": False,
                "error": f"Unsupported language: {language}. Supported languages: {CodeExecution.SUPPORTED_LANGUAGES}"
            }
        
        result = {
            "success": False,
            "output": "",
            "error": None,
            "execution_time": 0
        }
        
        try:
            start_time = time.time()
            
            if language == "python":
                # Create a temporary file
                temp_file = f"temp_code_{int(time.time())}.py"
                with open(temp_file, "w") as f:
                    f.write(code)
                
                # Execute the code and capture output
                process = subprocess.Popen(
                    [sys.executable, temp_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Set a timeout of 10 seconds
                try:
                    stdout, stderr = process.communicate(timeout=10)
                    
                    result["output"] = stdout
                    result["error"] = stderr if stderr else None
                    result["success"] = process.returncode == 0
                except subprocess.TimeoutExpired:
                    process.kill()
                    result["error"] = "Execution timed out after 10 seconds"
                
                # Clean up
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            elif language == "javascript":
                # For JavaScript, we could use Node.js
                temp_file = f"temp_code_{int(time.time())}.js"
                with open(temp_file, "w") as f:
                    f.write(code)
                
                # Check if Node.js is installed
                try:
                    # Execute the code and capture output
                    process = subprocess.Popen(
                        ["node", temp_file],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    stdout, stderr = process.communicate(timeout=10)
                    
                    result["output"] = stdout
                    result["error"] = stderr if stderr else None
                    result["success"] = process.returncode == 0
                except Exception as e:
                    result["error"] = f"Failed to execute JavaScript: {str(e)}"
                
                # Clean up
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            result["execution_time"] = time.time() - start_time
            
        except Exception as e:
            result["error"] = f"Execution error: {str(e)}"
        
        return result

# ==================== Initialize System Components ====================
# Initialize knowledge base
kb = KnowledgeBase()

# Add some initial knowledge
kb.add_document(
    "JARVIS (Just A Rather Very Intelligent System) is an AI assistant designed to help with coding and other tasks.",
    "system",
    {"category": "definition"}
)
kb.add_document(
    "The JARVIS MCP (Multi-Channel Processor) allows for integration with various tools and services.",
    "system",
    {"category": "architecture"}
)

# Initialize autonomous agent
autonomous_agent = AutonomousAgent()

# ==================== API Endpoints ====================
@app.get("/")
async def root():
    """Root endpoint, returns server info."""
    return {
        "name": "J.A.R.V.I.S. Integrated System",
        "status": "online",
        "version": "2.0.0",
        "features": [
            "file_search",
            "knowledge_base",
            "code_generation",
            "code_execution",
            "autonomous_agent",
            "sse_streaming"
        ]
    }

@app.post("/")
async def process_request(request: Request, background_tasks: BackgroundTasks):
    """Main endpoint for processing MCP requests."""
    try:
        data = await request.json()
        method = data.get("method", "")
        params = data.get("params", {})
        
        # Core MCP functions
        if method == "search_files":
            return await search_files(params.get("query", ""), params.get("path", "."))
        elif method == "generate_voice":
            return {"voice_output": f"Voice generated: {params.get('text', '')}"}
        elif method == "automate_task":
            return {"status": "success", "output": f"Task automated: {params.get('command', '')}"}
        
        # Knowledge base functions
        elif method == "search_knowledge":
            return await search_knowledge(params.get("query", ""), params.get("limit", 5))
        elif method == "add_knowledge":
            return await add_knowledge(
                params.get("text", ""), 
                params.get("source", "user"),
                params.get("metadata", {})
            )
        
        # Code functions
        elif method == "generate_code":
            return await generate_code(
                params.get("spec", ""), 
                params.get("language", "python")
            )
        elif method == "execute_code":
            return await CodeExecution.execute_code(
                params.get("code", ""),
                params.get("language", "python")
            )
        
        # Autonomous agent functions
        elif method == "start_task":
            task_id = autonomous_agent.start_task(params.get("description", ""))
            return {"task_id": task_id, "status": "started"}
        elif method == "get_task_state":
            task_state = autonomous_agent.get_task_state(params.get("task_id", ""))
            if task_state:
                return task_state
            return {"error": "Task not found"}
        
        else:
            return {"error": f"Unknown method: {method}"}
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {"error": f"Error processing request: {str(e)}"}

# ==================== SSE Streaming ====================
async def sse_generator():
    """Generate SSE events."""
    # Initial connection event
    yield f"data: {json.dumps({'type': 'connection', 'message': 'Connected to JARVIS Integrated Server'})}\n\n"
    
    # Keep the connection alive with periodic messages
    while True:
        # Include system status in ping messages
        status = {
            "type": "ping",
            "timestamp": str(asyncio.get_event_loop().time()),
            "server_status": "online",
            "active_tasks": len(autonomous_agent.tasks),
            "knowledge_count": len(kb.documents)
        }
        
        yield f"data: {json.dumps(status)}\n\n"
        await asyncio.sleep(5)

@app.get("/stream")
async def stream_endpoint():
    """SSE endpoint for event streaming."""
    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

@app.get("/mcp/sse")
async def mcp_sse():
    """MCP SSE endpoint for Cursor integration."""
    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

# ==================== Utility Functions ====================
async def search_files(query: str, path: str = ".") -> Dict[str, Any]:
    """
    Search for files containing the specified query string.
    Searches both file names and content.
    """
    try:
        results = []
        pattern = re.compile(query, re.IGNORECASE)
        
        # Recursively search for files
        for root, dirs, files in os.walk(path):
            # Skip hidden directories and files
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                # Skip binary and hidden files
                if file.startswith('.') or file.endswith(('.exe', '.dll', '.zip', '.bin')):
                    continue
                
                file_path = os.path.join(root, file)
                
                # Check if the file name matches
                name_match = pattern.search(file)
                
                # Try to read the file content
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    content_match = pattern.search(content)
                except:
                    content = ""
                    content_match = None
                
                # Add to results if there's a match
                if name_match or content_match:
                    results.append({
                        "file": file_path,
                        "name_match": bool(name_match),
                        "content_match": bool(content_match),
                        "content": content[:500] + "..." if len(content) > 500 else content
                    })
        
        return {
            "query": query,
            "path": path,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching files: {str(e)}")
        return {"error": f"Error searching files: {str(e)}"}

async def search_knowledge(query: str, limit: int = 5) -> Dict[str, Any]:
    """Search the knowledge base."""
    try:
        results = kb.search(query, limit)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching knowledge: {str(e)}")
        return {"error": f"Error searching knowledge: {str(e)}"}

async def add_knowledge(text: str, source: str = "user", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Add a document to the knowledge base."""
    try:
        if not text:
            return {"error": "Text cannot be empty"}
        
        doc_id = kb.add_document(text, source, metadata)
        return {
            "success": True,
            "id": doc_id,
            "message": "Knowledge added successfully"
        }
    except Exception as e:
        logger.error(f"Error adding knowledge: {str(e)}")
        return {"error": f"Error adding knowledge: {str(e)}"}

async def generate_code(spec: str, language: str = "python") -> Dict[str, Any]:
    """Generate code based on a specification."""
    try:
        if not spec:
            return {"error": "Specification cannot be empty"}
        
        # Simple code generation examples based on language
        # In a real implementation, this would call a language model
        code_samples = {
            "python": [
                "def hello_world():\n    print('Hello, world!')\n\nhello_world()",
                "import math\n\ndef calculate_area(radius):\n    return math.pi * radius * radius\n\nprint(calculate_area(5))",
                "class Person:\n    def __init__(self, name, age):\n        self.name = name\n        self.age = age\n\n    def greet(self):\n        return f'Hello, my name is {self.name} and I am {self.age} years old.'\n\nperson = Person('Alice', 30)\nprint(person.greet())"
            ],
            "javascript": [
                "function helloWorld() {\n    console.log('Hello, world!');\n}\n\nhelloWorld();",
                "function calculateArea(radius) {\n    return Math.PI * radius * radius;\n}\n\nconsole.log(calculateArea(5));",
                "class Person {\n    constructor(name, age) {\n        this.name = name;\n        this.age = age;\n    }\n\n    greet() {\n        return `Hello, my name is ${this.name} and I am ${this.age} years old.`;\n    }\n}\n\nconst person = new Person('Alice', 30);\nconsole.log(person.greet());"
            ],
            "html": [
                "<!DOCTYPE html>\n<html>\n<head>\n    <title>Hello World</title>\n</head>\n<body>\n    <h1>Hello, world!</h1>\n</body>\n</html>"
            ]
        }
        
        # Default to Python if the language is not supported
        if language.lower() not in code_samples:
            language = "python"
        
        # Choose a random code sample for the specified language
        code = random.choice(code_samples[language.lower()])
        
        return {
            "success": True,
            "language": language,
            "specification": spec,
            "code": code
        }
    except Exception as e:
        logger.error(f"Error generating code: {str(e)}")
        return {"error": f"Error generating code: {str(e)}"}

# ==================== Main Entry Point ====================
if __name__ == "__main__":
    print("JARVIS Integrated Server starting on http://0.0.0.0:8000")
    print("Features: file search, knowledge base, code generation/execution, autonomous agent")
    print("SSE endpoints available at /stream and /mcp/sse")
    uvicorn.run(app, host="0.0.0.0", port=8000) 