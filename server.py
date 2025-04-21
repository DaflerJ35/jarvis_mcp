from mcp.server.fastmcp import FastMCP
import aiohttp
import os
import glob
import asyncio
from typing import Dict, Any, List, Optional
from knowledge_enhancer import JARVISKnowledgeEnhancer

# Initialize MCP server with WebSocket support
mcp = FastMCP("JARVIS_MCP")

# Directory for J.A.R.V.I.S. project files
PROJECT_DIR = os.path.join(os.path.dirname(__file__), "project_files")
os.makedirs(PROJECT_DIR, exist_ok=True)

# Initialize knowledge enhancer
knowledge_enhancer = JARVISKnowledgeEnhancer()

# Store connected clients
connected_clients = []

# Tool: Search project files for relevant code
@mcp.tool()
async def search_files(query: str) -> str:
    """Search J.A.R.V.I.S. project files for code or docs matching the query."""
    try:
        files = glob.glob(f"{PROJECT_DIR}/**/*.[py,js,md]", recursive=True)
        results = ""
        for file in files:
            if query.lower() in os.path.basename(file).lower():
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                results += f"File: {file}\n{content}\n\n"
        return results or "No matching files found."
    except Exception as e:
        return f"Error searching files: {str(e)}"

# Tool: Generate voice response
@mcp.tool()
async def generate_voice(text: str) -> str:
    """Generate a J.A.R.V.I.S. voice response from text."""
    # This is a placeholder. In a real implementation, would use TTS.
    return f"Voice generated: {text}"

# Tool: Task automation (e.g., send email or open website)
@mcp.tool()
async def automate_task(command: str) -> str:
    """Execute J.A.R.V.I.S.-style tasks like sending emails or opening websites."""
    try:
        if "send email" in command.lower():
            async with aiohttp.ClientSession() as session:
                response = await session.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={"Authorization": "Bearer YOUR_SENDGRID_API_KEY"},
                    json={
                        "personalizations": [{"to": [{"email": "recipient@example.com"}]}],
                        "from": {"email": "jarvis@example.com"},
                        "subject": "J.A.R.V.I.S. Task",
                        "content": [{"type": "text/plain", "value": "Task executed!"}]
                    }
                )
                return "Email sent successfully" if response.status == 202 else f"Email error: {response.status}"
        elif "open website" in command.lower():
            return f"Opening website: {command.split('open website')[-1].strip()}"
        return "Command not recognized"
    except Exception as e:
        return f"Error automating task: {str(e)}"

# Knowledge-related tools
@mcp.tool()
async def semantic_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search J.A.R.V.I.S. knowledge base semantically."""
    try:
        results = knowledge_enhancer.semantic_search(query, top_k=top_k)
        return results
    except Exception as e:
        return [{"error": f"Error in semantic search: {str(e)}"}]

@mcp.tool()
async def web_search(query: str) -> Dict[str, Any]:
    """Search the web for information."""
    # Placeholder - in a real implementation, would use a search API
    return {
        "results": [
            {
                "title": f"Web search result for: {query}",
                "snippet": "This is a simulated web search result. In a real implementation, this would connect to a search engine API.",
                "url": "https://example.com/search"
            }
        ]
    }

@mcp.tool()
async def fetch_news(topic: Optional[str] = None) -> Dict[str, Any]:
    """Fetch latest news, optionally filtered by topic."""
    # Placeholder - in a real implementation, would use a news API
    return {
        "news": [
            {
                "title": f"Latest news about {topic or 'technology'}",
                "summary": "This is a simulated news article. In a real implementation, this would connect to a news API.",
                "source": "J.A.R.V.I.S. News",
                "published_at": "2023-04-20T12:00:00Z",
                "url": "https://example.com/news"
            }
        ]
    }

@mcp.tool()
async def learn_from_website(url: str) -> str:
    """Learn information from a website and add it to knowledge base."""
    try:
        # Placeholder - in a real implementation, would scrape and process the website
        text = f"Simulated content extracted from {url}"
        metadata = {"source": url, "extraction_method": "web_scraping"}
        success = knowledge_enhancer.add_to_knowledge(text, url, metadata)
        return f"Successfully learned information from {url}" if success else f"Failed to learn from {url}"
    except Exception as e:
        return f"Error learning from website: {str(e)}"

@mcp.tool()
async def learn_from_youtube(video_id: str) -> str:
    """Learn information from a YouTube video and add it to knowledge base."""
    try:
        # Placeholder - in a real implementation, would extract and process video transcript
        text = f"Simulated transcript from YouTube video {video_id}"
        metadata = {"source": f"youtube:{video_id}", "extraction_method": "youtube_transcript"}
        success = knowledge_enhancer.add_to_knowledge(
            text, 
            f"https://www.youtube.com/watch?v={video_id}", 
            metadata
        )
        return f"Successfully learned from YouTube video {video_id}" if success else f"Failed to learn from video {video_id}"
    except Exception as e:
        return f"Error learning from YouTube: {str(e)}"

@mcp.tool()
async def add_knowledge(text: str, source: str = "user_input", metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Add information to the J.A.R.V.I.S. knowledge base."""
    return knowledge_enhancer.add_to_knowledge(text, source, metadata or {})

@mcp.tool()
async def get_memory(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent items from J.A.R.V.I.S. memory."""
    return knowledge_enhancer.get_memory(limit)

@mcp.tool()
async def get_project_overview() -> Dict[str, Any]:
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
                "name": "Tool System",
                "description": "Provides various capabilities to the assistant",
                "status": "active"
            }
        ],
        "capabilities": [
            "Knowledge management",
            "Voice response generation",
            "Task automation",
            "Web search",
            "News fetching",
            "Learning from websites and videos"
        ]
    }

@mcp.tool()
async def get_knowledge_stats() -> Dict[str, Any]:
    """Get statistics about the J.A.R.V.I.S. knowledge base."""
    return {
        "total_documents": len(knowledge_enhancer.documents),
        "total_memory_items": len(knowledge_enhancer.memory),
        "last_updated": "None"
    }

# Try to retrieve the FastAPI app from the MCP instance
try:
    app = mcp.app
except AttributeError:
    # If app is not available, try other potential attributes
    app = getattr(mcp, 'fastapi_app', None)
    if app is None:
        app = getattr(mcp, 'router', None)

# Start the MCP server
if __name__ == "__main__":
    import uvicorn
    # Create project_files directory if it doesn't exist
    os.makedirs(PROJECT_DIR, exist_ok=True)
    print(f"J.A.R.V.I.S. MCP Server starting on http://0.0.0.0:8000")
    print(f"Project files directory: {PROJECT_DIR}")
    print(f"Knowledge base directory: {knowledge_enhancer.knowledge_dir}")
    
    # Print information about available attributes to help debugging
    print(f"MCP object has these attributes: {dir(mcp)}")
    print(f"Using app object: {app}")
    
    if app:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        print("Unable to access FastAPI app, falling back to built-in MCP runner")
        mcp.run() 