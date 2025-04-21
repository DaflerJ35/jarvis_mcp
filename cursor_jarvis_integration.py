import asyncio
import json
import os
import sys
import argparse
from typing import Dict, Any, List, Optional
from claude_mcp_connector import ClaudeMCPConnector

class CursorJARVISBridge:
    """Bridge to integrate Cursor IDE with J.A.R.V.I.S. MCP capabilities."""
    
    def __init__(self, mcp_url: str = "http://localhost:8000"):
        self.connector = ClaudeMCPConnector(mcp_url)
        self.project_context = {}
        self.initialized = False
    
    async def initialize(self):
        """Initialize the J.A.R.V.I.S. MCP connection."""
        self.initialized = await self.connector.initialize()
        if self.initialized:
            print("Cursor is now enhanced with J.A.R.V.I.S. capabilities!")
            # Set up environment variables
            os.environ["JARVIS_MCP_CONNECTED"] = "true"
        return self.initialized
    
    async def update_context(self, current_file: str = None, cursor_position: tuple = None, 
                            visible_files: List[str] = None, project_dir: str = None):
        """Update the project context."""
        self.project_context = {
            "current_file": current_file,
            "cursor_position": cursor_position,
            "visible_files": visible_files or [],
            "project_dir": project_dir or os.getcwd()
        }
    
    async def process_command(self, command: str) -> Dict[str, Any]:
        """Process a command from Cursor/Claude."""
        if not self.initialized:
            return {"error": "J.A.R.V.I.S. MCP not initialized"}
        
        # Enhance command with current context
        enhanced_command = self._enhance_command_with_context(command)
        
        # Process through connector
        response = await self.connector.process_message(enhanced_command)
        
        return {
            "response": response,
            "context": self.project_context
        }
    
    def _enhance_command_with_context(self, command: str) -> str:
        """Enhance a command with current IDE context."""
        if not command.startswith("/jarvis"):
            # Only add context to non-jarvis commands
            context_prefix = ""
            if self.project_context.get("current_file"):
                context_prefix += f"[Current file: {self.project_context['current_file']}] "
            
            # Only prepend context if it exists
            if context_prefix:
                return f"{context_prefix}{command}"
        
        return command
    
    async def shutdown(self):
        """Shut down the J.A.R.V.I.S. MCP connection."""
        if self.initialized:
            await self.connector.shutdown()
            print("Cursor J.A.R.V.I.S. integration shut down.")
            os.environ.pop("JARVIS_MCP_CONNECTED", None)

async def main():
    """Main function for standalone usage."""
    parser = argparse.ArgumentParser(description="Cursor J.A.R.V.I.S. Integration")
    parser.add_argument("--mcp-url", default="http://localhost:8000", help="URL of the J.A.R.V.I.S. MCP server")
    parser.add_argument("--project-dir", default=None, help="Project directory path")
    args = parser.parse_args()
    
    bridge = CursorJARVISBridge(args.mcp_url)
    
    try:
        # Initialize
        initialized = await bridge.initialize()
        if not initialized:
            print("Failed to initialize J.A.R.V.I.S. MCP connection. Exiting.")
            return
        
        # Update context
        await bridge.update_context(project_dir=args.project_dir or os.getcwd())
        
        # Interactive mode
        print("\nCursor J.A.R.V.I.S. Integration")
        print("Type '/jarvis help' for available commands or 'exit' to quit.\n")
        
        while True:
            user_input = input("Cursor> ")
            
            if user_input.lower() == "exit":
                break
            
            response = await bridge.process_command(user_input)
            print(f"J.A.R.V.I.S.> {response.get('response', 'No response')}")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        # Shutdown
        await bridge.shutdown()

def setup_cursor_jarvis():
    """Function to be imported by Cursor to set up J.A.R.V.I.S. integration."""
    bridge = CursorJARVISBridge()
    
    async def initialize_async():
        await bridge.initialize()
    
    # Run initialization in a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(initialize_async())
    
    # Return the bridge for Cursor to use
    return bridge

if __name__ == "__main__":
    asyncio.run(main()) 