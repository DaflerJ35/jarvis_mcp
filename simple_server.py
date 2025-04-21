from fastapi import FastAPI, Request
import uvicorn
import os
import glob
import json
from typing import Dict, Any, List, Optional
from knowledge_enhancer import JARVISKnowledgeEnhancer

# Create FastAPI app directly
app = FastAPI(title="JARVIS MCP Server")

# Directory for J.A.R.V.I.S. project files
PROJECT_DIR = os.path.join(os.path.dirname(__file__), "project_files")
os.makedirs(PROJECT_DIR, exist_ok=True)

# Initialize knowledge enhancer
knowledge_enhancer = JARVISKnowledgeEnhancer()

@app.get("/")
async def root():
    """Root endpoint, returns server info."""
    return {
        "name": "J.A.R.V.I.S. Multi-Channel Processor",
        "status": "online",
        "version": "1.0.0",
    }

@app.post("/")
async def process_request(request: Request):
    """Main endpoint for processing MCP requests."""
    try:
        data = await request.json()
        method = data.get("method", "")
        params = data.get("params", {})
        
        if method == "search_files":
            return await search_files(params.get("query", ""))
        elif method == "generate_voice":
            return {"voice_output": f"Voice generated: {params.get('text', '')}"}
        elif method == "automate_task":
            return {"status": "success", "output": f"Task automated: {params.get('command', '')}"}
        elif method == "semantic_search":
            results = knowledge_enhancer.semantic_search(
                params.get("query", ""), 
                top_k=params.get("top_k", 5)
            )
            return {"results": results}
        else:
            return {"error": f"Unknown method: {method}"}
    except Exception as e:
        return {"error": f"Error processing request: {str(e)}"}

@app.get("/jarvis://overview")
async def get_project_overview():
    """Get an overview of the J.A.R.V.I.S. MCP project."""
    return {
        "name": "J.A.R.V.I.S. Multi-Channel Processor",
        "description": "An advanced AI assistant system inspired by Iron Man's J.A.R.V.I.S.",
        "version": "1.0.0",
        "components": [
            {
                "name": "Knowledge Enhancer",
                "description": "Manages and retrieves knowledge for the system",
                "status": "active"
            },
            {
                "name": "API Server",
                "description": "Handles API requests",
                "status": "active"
            }
        ],
        "capabilities": [
            "Knowledge management",
            "Voice response generation",
            "Task automation",
            "Web search",
            "File search"
        ]
    }

async def search_files(query: str) -> Dict[str, Any]:
    """Search J.A.R.V.I.S. project files for code or docs matching the query."""
    try:
        files = glob.glob(f"{PROJECT_DIR}/**/*.[py,js,md]", recursive=True)
        results = []
        for file in files:
            if query.lower() in os.path.basename(file).lower():
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                results.append({
                    "file": file,
                    "content": content
                })
        return {"results": results, "count": len(results)}
    except Exception as e:
        return {"error": f"Error searching files: {str(e)}"}

if __name__ == "__main__":
    print(f"J.A.R.V.I.S. MCP Server starting on http://0.0.0.0:8000")
    print(f"Project files directory: {PROJECT_DIR}")
    print(f"Knowledge base directory: {knowledge_enhancer.knowledge_dir}")
    uvicorn.run(app, host="0.0.0.0", port=8000) 