import asyncio
import aiohttp
import json
import sys
import os
from typing import Dict, Any, List, Optional, Callable

class JarvisMCPClient:
    """Client to connect Claude/Cursor to the J.A.R.V.I.S. MCP server."""
    
    def __init__(self, mcp_url: str = "http://localhost:8000"):
        self.mcp_url = mcp_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.websocket: Optional[aiohttp.ClientWebSocketResponse] = None
        self.tools_cache: Dict[str, Dict] = {}
        self.resources_cache: Dict[str, str] = {}
        self.callback: Optional[Callable[[str], None]] = None
    
    async def connect(self):
        """Connect to the MCP server."""
        self.session = aiohttp.ClientSession()
        try:
            # Connect to WebSocket endpoint
            self.websocket = await self.session.ws_connect(f"{self.mcp_url}/ws")
            print(f"Connected to J.A.R.V.I.S. MCP at {self.mcp_url}")
            
            # Fetch available tools
            await self._fetch_tools()
            
            # Display available tools
            self._display_available_tools()
            
            return True
        except Exception as e:
            print(f"Error connecting to MCP: {str(e)}")
            if self.session:
                await self.session.close()
                self.session = None
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _fetch_tools(self):
        """Fetch available tools from the MCP server."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            async with self.session.get(f"{self.mcp_url}/tools") as response:
                if response.status == 200:
                    tools_data = await response.json()
                    self.tools_cache = {tool["name"]: tool for tool in tools_data}
                else:
                    print(f"Error fetching tools: {response.status}")
        except Exception as e:
            print(f"Error fetching tools: {str(e)}")
    
    async def _fetch_resources(self):
        """Fetch available resources from the MCP server."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            async with self.session.get(f"{self.mcp_url}/resources") as response:
                if response.status == 200:
                    resources_data = await response.json()
                    self.resources_cache = resources_data
                else:
                    print(f"Error fetching resources: {response.status}")
        except Exception as e:
            print(f"Error fetching resources: {str(e)}")
    
    def _display_available_tools(self):
        """Display available tools to the user."""
        if not self.tools_cache:
            print("No tools available")
            return
        
        print("\nAvailable J.A.R.V.I.S. Tools:")
        print("=" * 50)
        for name, tool in self.tools_cache.items():
            print(f"📌 {name}: {tool.get('description', 'No description')}")
        print("=" * 50)
    
    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        if tool_name not in self.tools_cache:
            print(f"Tool '{tool_name}' not found. Refreshing tool list...")
            await self._fetch_tools()
            if tool_name not in self.tools_cache:
                raise ValueError(f"Tool '{tool_name}' not available")
        
        try:
            async with self.session.post(
                f"{self.mcp_url}/tools/{tool_name}",
                json=kwargs
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Error calling tool: {response.status} - {error_text}")
        except Exception as e:
            raise RuntimeError(f"Error calling tool '{tool_name}': {str(e)}")
    
    async def get_resource(self, resource_uri: str) -> str:
        """Get a resource from the MCP server."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            async with self.session.get(f"{self.mcp_url}/resources/{resource_uri}") as response:
                if response.status == 200:
                    return await response.text()
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Error getting resource: {response.status} - {error_text}")
        except Exception as e:
            raise RuntimeError(f"Error getting resource '{resource_uri}': {str(e)}")
    
    async def listen_for_messages(self):
        """Listen for incoming messages from the MCP server."""
        if not self.websocket:
            raise RuntimeError("WebSocket not connected")
        
        try:
            async for msg in self.websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if self.callback:
                        self.callback(data)
                    else:
                        print(f"Received: {data}")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break
        except Exception as e:
            print(f"Error in WebSocket connection: {str(e)}")
        finally:
            print("Disconnected from WebSocket")
    
    def set_message_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Set callback for incoming messages."""
        self.callback = callback
    
    async def send_message(self, message: str):
        """Send a message to the MCP server."""
        if not self.websocket:
            raise RuntimeError("WebSocket not connected")
        
        try:
            await self.websocket.send_str(json.dumps({"message": message}))
        except Exception as e:
            print(f"Error sending message: {str(e)}")

async def main():
    # Create client
    client = JarvisMCPClient()
    
    # Connect to MCP server
    connected = await client.connect()
    if not connected:
        print("Failed to connect to MCP server. Exiting.")
        return
    
    try:
        # Example: Call search_files tool
        result = await client.call_tool("search_files", query="jarvis")
        print(f"Search results: {result}")
        
        # Example: Get project overview resource
        overview = await client.get_resource("jarvis://overview")
        print(f"Project overview: {overview}")
        
        # Keep the connection alive and listen for messages
        await client.listen_for_messages()
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Disconnect
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 