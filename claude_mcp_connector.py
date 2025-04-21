import asyncio
import json
import os
import sys
from typing import Dict, Any, List, Optional, Callable
from jarvis_mcp_client import JarvisMCPClient

class ClaudeMCPConnector:
    """Connects Claude/Cursor to the J.A.R.V.I.S. MCP for enhanced capabilities."""
    
    def __init__(self, mcp_url: str = "http://localhost:8000"):
        self.client = JarvisMCPClient(mcp_url)
        self.available_tools = {}
        self.conversation_history = []
    
    async def initialize(self):
        """Initialize the connection to the MCP."""
        print("Initializing connection to J.A.R.V.I.S. MCP...")
        connected = await self.client.connect()
        
        if not connected:
            print("Failed to connect to J.A.R.V.I.S. MCP. Exiting.")
            return False
        
        print("Connection established. Claude is now enhanced with J.A.R.V.I.S. capabilities!")
        return True
    
    async def process_message(self, message: str) -> str:
        """Process a message from Claude/Cursor."""
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Check if the message is a tool invocation
        if message.startswith("/jarvis"):
            response = await self._handle_jarvis_command(message[8:].strip())
        else:
            # Just send the message to the MCP for processing
            await self.client.send_message(message)
            response = "Message sent to J.A.R.V.I.S. MCP."
        
        # Add to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})
        return response
    
    async def _handle_jarvis_command(self, command: str) -> str:
        """Handle a /jarvis command."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""
        
        try:
            if cmd == "help":
                return self._get_help()
            elif cmd == "search":
                result = await self.client.call_tool("search_files", query=args)
                return f"Search results for '{args}':\n{result}"
            elif cmd == "voice":
                result = await self.client.call_tool("generate_voice", text=args)
                return f"Voice generation result: {result}"
            elif cmd == "task":
                result = await self.client.call_tool("automate_task", command=args)
                return f"Task automation result: {result}"
            elif cmd == "overview":
                overview = await self.client.get_resource("jarvis://overview")
                return f"J.A.R.V.I.S. Project Overview:\n{overview}"
            # NEW COMMANDS FOR KNOWLEDGE ENHANCEMENT
            elif cmd == "semantic" or cmd == "semantic_search" or cmd == "ask":
                # Use semantic search for knowledge retrieval
                result = await self.client.call_tool("semantic_search", query=args)
                
                if isinstance(result, dict) and result.get("status") == "success":
                    search_results = result.get("results", [])
                    
                    if not search_results:
                        return f"No results found for '{args}' in knowledge base."
                    
                    response = f"Knowledge base results for '{args}':\n\n"
                    for i, item in enumerate(search_results, 1):
                        score = item.get("score", 0) * 100  # Convert score to percentage
                        response += f"{i}. {item.get('text', '')[:300]}...\n"
                        response += f"   Source: {item.get('source', 'Unknown')} (Relevance: {score:.1f}%)\n\n"
                    
                    return response
                else:
                    return f"Error searching knowledge base: {result.get('message', 'Unknown error')}"
            elif cmd == "web" or cmd == "web_search":
                # Search the web and add to knowledge base
                result = await self.client.call_tool("web_search", query=args)
                
                if isinstance(result, dict) and "error" not in result:
                    web_results = result.get("results", [])
                    
                    if not web_results:
                        return f"No web results found for '{args}'."
                    
                    response = f"Web search results for '{args}':\n\n"
                    for i, item in enumerate(web_results, 1):
                        response += f"{i}. {item.get('title', 'No title')}\n"
                        response += f"   {item.get('snippet', 'No snippet')}\n"
                        response += f"   Link: {item.get('link', 'No link')}\n\n"
                    
                    response += "These results have been added to the knowledge base."
                    return response
                else:
                    return f"Error searching the web: {result.get('error', 'Unknown error')}"
            elif cmd == "news":
                # Fetch news
                topic = args if args else None
                result = await self.client.call_tool("fetch_news", topic=topic)
                
                if isinstance(result, dict) and "error" not in result:
                    articles = result.get("articles", [])
                    
                    if not articles:
                        return f"No news found{' for ' + args if args else ''}."
                    
                    response = f"Latest news{' about ' + args if args else ''}:\n\n"
                    for i, article in enumerate(articles, 1):
                        response += f"{i}. {article.get('title', 'No title')}\n"
                        response += f"   {article.get('description', 'No description')}\n"
                        response += f"   Source: {article.get('source', 'Unknown')} | {article.get('published_at', 'No date')}\n\n"
                    
                    response += "These news articles have been added to the knowledge base."
                    return response
                else:
                    return f"Error fetching news: {result.get('error', 'Unknown error')}"
            elif cmd == "learn" or cmd == "website":
                # Learn from a website
                if not args.startswith("http"):
                    return "Please provide a valid URL starting with http:// or https://"
                
                result = await self.client.call_tool("learn_from_website", url=args)
                
                if isinstance(result, dict) and result.get("success"):
                    return f"Successfully learned from website: {result.get('title', 'No title')}\nThe content has been added to the knowledge base."
                else:
                    return f"Error learning from website: {result.get('error', 'Unknown error')}"
            elif cmd == "youtube":
                # Extract video ID from URL or use directly
                video_id = args
                if "youtube.com" in args or "youtu.be" in args:
                    if "v=" in args:
                        video_id = args.split("v=")[1].split("&")[0]
                    elif "youtu.be/" in args:
                        video_id = args.split("youtu.be/")[1].split("?")[0]
                
                result = await self.client.call_tool("learn_from_youtube", video_id=video_id)
                
                if isinstance(result, dict) and result.get("success"):
                    return f"Successfully learned from YouTube video: {result.get('title', 'No title')}\nThe content has been added to the knowledge base."
                else:
                    return f"Error learning from YouTube video: {result.get('error', 'Unknown error')}"
            elif cmd == "add" or cmd == "knowledge":
                # Manually add knowledge
                if not args:
                    return "Please provide text to add to the knowledge base."
                
                result = await self.client.call_tool("add_knowledge", 
                    text=args, 
                    source="manual_claude_entry",
                    metadata={"type": "manual_entry"}
                )
                
                if isinstance(result, dict) and result.get("status") == "success":
                    return "Knowledge added successfully to the J.A.R.V.I.S. knowledge base."
                else:
                    return f"Error adding knowledge: {result.get('message', 'Unknown error')}"
            elif cmd == "memory":
                # Get conversation memory
                limit = 10
                if args and args.isdigit():
                    limit = int(args)
                
                result = await self.client.call_tool("get_memory", limit=limit)
                
                if isinstance(result, dict) and result.get("status") == "success":
                    memory = result.get("memory", [])
                    
                    if not memory:
                        return "No memory entries available."
                    
                    response = f"Last {len(memory)} memory entries:\n\n"
                    for i, entry in enumerate(memory, 1):
                        role = entry.get("role", "unknown")
                        content = entry.get("content", "")
                        timestamp = entry.get("timestamp", "")
                        
                        if isinstance(content, dict):
                            content = json.dumps(content, indent=2)
                        elif isinstance(content, str) and len(content) > 100:
                            content = content[:100] + "..."
                        
                        response += f"{i}. [{role}] {content}\n"
                        response += f"   Timestamp: {timestamp}\n\n"
                    
                    return response
                else:
                    return f"Error retrieving memory: {result.get('message', 'Unknown error')}"
            elif cmd == "stats" or cmd == "knowledge_stats":
                # Get knowledge base stats
                stats = await self.client.get_resource("jarvis://knowledge_stats")
                return f"J.A.R.V.I.S. Knowledge Base Statistics:\n{stats}"
            else:
                return f"Unknown command: {cmd}. Type /jarvis help for available commands."
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    def _get_help(self) -> str:
        """Get help information for J.A.R.V.I.S. commands."""
        return """
J.A.R.V.I.S. MCP Commands:
--------------------------
Basic Commands:
/jarvis help - Show this help message
/jarvis search <query> - Search for files matching query
/jarvis voice <text> - Generate voice output for text
/jarvis task <command> - Execute a task (e.g., send email, open website)
/jarvis overview - Get J.A.R.V.I.S. project overview

Knowledge Commands:
/jarvis ask <query> - Search the knowledge base using semantic search
/jarvis web <query> - Search the web and add results to knowledge
/jarvis news [topic] - Get latest news, optionally on a specific topic
/jarvis learn <url> - Learn from a website by scraping its content
/jarvis youtube <video_id_or_url> - Learn from a YouTube video
/jarvis add <text> - Manually add text to the knowledge base
/jarvis memory [limit] - View recent memory entries (default: 10)
/jarvis stats - View knowledge base statistics

Example usage:
/jarvis search speech recognition
/jarvis ask What is JARVIS?
/jarvis web latest AI developments
/jarvis youtube https://youtu.be/_qH0ArjwBpE
"""
    
    async def shutdown(self):
        """Shut down the connection to the MCP."""
        await self.client.disconnect()
        print("Disconnected from J.A.R.V.I.S. MCP.")

async def main():
    """Main entry point for the Claude MCP connector."""
    connector = ClaudeMCPConnector()
    
    # Initialize connection
    initialized = await connector.initialize()
    if not initialized:
        return
    
    # Main interaction loop
    try:
        print("\nYou can now interact with J.A.R.V.I.S. Type /jarvis help for commands.")
        print("Type 'exit' to quit.\n")
        
        while True:
            user_input = input("You: ")
            
            if user_input.lower() == "exit":
                break
            
            response = await connector.process_message(user_input)
            print(f"Claude+J.A.R.V.I.S.: {response}")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        # Cleanup
        await connector.shutdown()

if __name__ == "__main__":
    asyncio.run(main()) 