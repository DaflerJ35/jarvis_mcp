import os
import sys
import json
import asyncio
import logging
import datetime
import argparse
from typing import Dict, Any, Optional

# Import JARVIS components
from claude_jarvis_coding_bridge import ClaudeJARVISCodingBridge, init_coding_bridge
from jarvis_enhanced_system import JARVISEnhancedSystem

# Global instances
bridge = None
enhanced_system = None
desktop_assistant_connected = False
desktop_assistant_details = {}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("connect_claude.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Claude-JARVIS-Connector")

async def initialize_bridge(use_enhanced_system=True):
    """Initialize the connection to the JARVIS MCP."""
    global bridge, enhanced_system
    
    if use_enhanced_system:
        logger.info("🚀 Initializing Enhanced JARVIS System...")
        enhanced_system = JARVISEnhancedSystem()
        success = await enhanced_system.setup()
        
        if not success:
            logger.error("❌ Failed to initialize Enhanced JARVIS System")
            return False
        
        # Get the coding bridge from the enhanced system
        bridge = enhanced_system.coding_bridge
        
        logger.info("✅ Enhanced JARVIS System initialized successfully!")
        return True
    else:
        logger.info("🔄 Connecting Claude to the basic JARVIS MCP...")
        bridge = await init_coding_bridge()
        
        # Check if bridge was properly initialized
        if not bridge:
            logger.error("❌ Failed to initialize Claude-JARVIS bridge.")
            return False
        
        logger.info("✅ Claude is now connected to the JARVIS knowledge system!")
        logger.info("   Claude can now access all JARVIS architecture knowledge when coding")
        
        return True

async def get_code_for_task(task: str, language: str = None, use_enhanced: bool = True):
    """Generate code for a specified task using the JARVIS knowledge."""
    global bridge, enhanced_system
    
    if not bridge:
        logger.warning("⚠️ Claude-JARVIS bridge not initialized. Initializing now...")
        success = await initialize_bridge(use_enhanced_system=use_enhanced)
        if not success:
            return "Failed to connect to JARVIS MCP. Cannot generate code."
    
    try:
        if use_enhanced and enhanced_system:
            # Use the enhanced system for code generation
            result = await enhanced_system.process_request("code", {
                "task": task,
                "language": language,
                "simulate": True,
                "version_check": True
            })
            
            # Extract code from result
            if isinstance(result, dict) and "code" in result:
                return result["code"]
            elif isinstance(result, dict) and "error" in result:
                return f"Error: {result['error']}"
            else:
                return "Error: Unexpected response format"
        else:
            # Use the basic coding bridge
            result = await bridge.generate_code(task, language)
            return result["code"]
    except Exception as e:
        logger.error(f"Error generating code: {str(e)}")
        return f"Error generating code: {str(e)}"

async def query_jarvis_knowledge(query: str, use_enhanced: bool = True):
    """Query the JARVIS knowledge base."""
    global bridge, enhanced_system
    
    if not bridge:
        logger.warning("⚠️ Claude-JARVIS bridge not initialized. Initializing now...")
        success = await initialize_bridge(use_enhanced_system=use_enhanced)
        if not success:
            return "Failed to connect to JARVIS MCP. Cannot query knowledge base."
    
    try:
        if use_enhanced and enhanced_system:
            # Use the enhanced system's predictive engine
            result = await enhanced_system.process_request("predict", {
                "context": {"query": query},
                "scope": "knowledge"
            })
            
            # Format results
            if isinstance(result, dict) and "predictions" in result:
                predictions = result.get("predictions", [])
                return "\n\n".join([f"- {p}" for p in predictions])
            elif isinstance(result, dict) and "error" in result:
                # Fall back to basic knowledge query
                context = await bridge.get_code_context(query)
                results = []
                for item in context.get("knowledge_results", []):
                    results.append(f"- {item.get('text', '')[:300]}...")
                return "\n\n".join(results) if results else "No knowledge found for this query."
            else:
                return "No relevant knowledge found."
        else:
            # Use the basic knowledge query
            context = await bridge.get_code_context(query)
            results = []
            for item in context.get("knowledge_results", []):
                results.append(f"- {item.get('text', '')[:300]}...")
            return "\n\n".join(results) if results else "No knowledge found for this query."
    except Exception as e:
        logger.error(f"Error querying knowledge base: {str(e)}")
        return f"Error querying knowledge base: {str(e)}"

async def update_jarvis_knowledge(text: str, source: str = "claude_update", use_enhanced: bool = True):
    """Add new knowledge to the JARVIS knowledge base."""
    global bridge, enhanced_system
    
    if not bridge:
        logger.warning("⚠️ Claude-JARVIS bridge not initialized. Initializing now...")
        success = await initialize_bridge(use_enhanced_system=use_enhanced)
        if not success:
            return "Failed to connect to JARVIS MCP. Cannot update knowledge base."
    
    try:
        # Add to knowledge base (same for both enhanced and basic)
        success = bridge.knowledge.add_to_knowledge(
            text=text,
            source=source,
            metadata={"type": "claude_update", "added_via": "connect_script"}
        )
        
        if success:
            return "✅ Successfully added to JARVIS knowledge base."
        else:
            return "❌ Failed to add to knowledge base."
    except Exception as e:
        logger.error(f"Error updating knowledge base: {str(e)}")
        return f"Error updating knowledge base: {str(e)}"

async def connect_desktop_assistant(assistant_url: str, api_key: Optional[str] = None):
    """Connect to an existing desktop JARVIS assistant."""
    global desktop_assistant_connected, desktop_assistant_details, enhanced_system
    
    try:
        logger.info(f"🔌 Connecting to desktop JARVIS assistant at {assistant_url}")
        
        # Validate URL
        if not assistant_url.startswith(("http://", "https://")):
            assistant_url = f"http://{assistant_url}"
        
        # If we have an enhanced system, use it to establish the connection
        if enhanced_system:
            connection_details = {
                "api_endpoint": assistant_url,
                "auth_token": api_key,
                "capabilities": ["voice", "knowledge", "automation"]
            }
            
            result = await enhanced_system.connect_external_assistant("desktop", connection_details)
            
            if isinstance(result, dict) and result.get("status") == "connected":
                desktop_assistant_connected = True
                desktop_assistant_details = {
                    "url": assistant_url,
                    "connection_id": result.get("connection_id", "unknown"),
                    "endpoints": result.get("available_endpoints", []),
                    "connected_at": datetime.datetime.now().isoformat()
                }
                
                return f"✅ Successfully connected to desktop JARVIS at {assistant_url}"
            else:
                error_msg = result.get("error", "Unknown error")
                return f"❌ Failed to connect to desktop JARVIS: {error_msg}"
        else:
            # Simulate a connection without the enhanced system
            # This would be replaced with actual API calls in a real implementation
            desktop_assistant_connected = True
            desktop_assistant_details = {
                "url": assistant_url,
                "connected_at": datetime.datetime.now().isoformat(),
                "capabilities": ["voice", "knowledge"]
            }
            
            # Add to knowledge base
            success = await update_jarvis_knowledge(
                f"Connected to desktop JARVIS assistant at {assistant_url}",
                "system_connection"
            )
            
            return f"✅ Basic connection established with desktop JARVIS at {assistant_url}"
    
    except Exception as e:
        logger.error(f"Error connecting to desktop JARVIS: {str(e)}")
        return f"❌ Error connecting to desktop JARVIS: {str(e)}"

async def send_to_desktop_assistant(command: str, data: Dict[str, Any] = None):
    """Send a command to the connected desktop JARVIS assistant."""
    global desktop_assistant_connected, desktop_assistant_details
    
    if not desktop_assistant_connected:
        return "❌ No desktop JARVIS assistant connected. Use 'connect' command first."
    
    try:
        assistant_url = desktop_assistant_details.get("url")
        logger.info(f"📤 Sending command '{command}' to desktop JARVIS at {assistant_url}")
        
        # This would be replaced with actual API calls in a real implementation
        # For now, simulate sending commands to the desktop assistant
        
        # Simulate response based on command
        if command == "status":
            return "📊 Desktop JARVIS Status: Online | CPU: 12% | Memory: 324MB | Uptime: 3h 42m"
        elif command == "voice":
            text = data.get("text", "Hello from Claude")
            return f"🔊 Voice command sent: '{text}'"
        elif command == "knowledge":
            query = data.get("query", "")
            # Use our knowledge base as a fallback
            knowledge_result = await query_jarvis_knowledge(query)
            return f"🧠 Knowledge from desktop JARVIS: {knowledge_result}"
        elif command == "task":
            task = data.get("task", "")
            return f"⚙️ Task sent to desktop JARVIS: '{task}'"
        else:
            return f"📝 Command '{command}' acknowledged by desktop JARVIS"
    
    except Exception as e:
        logger.error(f"Error sending command to desktop JARVIS: {str(e)}")
        return f"❌ Error sending command to desktop JARVIS: {str(e)}"

async def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Connect Claude to JARVIS Systems")
    parser.add_argument("--enhanced", action="store_true", help="Use enhanced JARVIS system")
    parser.add_argument("--desktop-url", help="URL of desktop JARVIS to connect to")
    parser.add_argument("--api-key", help="API key for desktop JARVIS (if required)")
    args = parser.parse_args()
    
    # Initialize bridge with specified mode
    success = await initialize_bridge(use_enhanced_system=args.enhanced)
    if not success:
        logger.error("❌ Failed to connect to JARVIS MCP. Exiting.")
        return
    
    # Connect to desktop JARVIS if specified
    if args.desktop_url:
        result = await connect_desktop_assistant(args.desktop_url, args.api_key)
        print(result)
    
    # Interactive mode
    system_type = "Enhanced" if args.enhanced and enhanced_system else "Basic"
    
    print(f"\n🤖 Claude-JARVIS Integration ({system_type} Mode)")
    print("--------------------------------------------------")
    print("Commands:")
    print("1. Type 'code:<task>' to generate code (e.g., 'code:Create a function to fetch weather data')")
    print("2. Type 'query:<question>' to search knowledge (e.g., 'query:What is the JARVIS architecture?')")
    print("3. Type 'add:<text>' to add knowledge (e.g., 'add:JARVIS uses a modular architecture')")
    if not desktop_assistant_connected and not args.desktop_url:
        print("4. Type 'connect:<url>' to connect to a desktop JARVIS assistant")
    if desktop_assistant_connected:
        print("5. Type 'desktop:<command>' to send commands to desktop JARVIS")
        print("   - 'desktop:status' - Get desktop JARVIS status")
        print("   - 'desktop:voice:<text>' - Send voice command")
        print("   - 'desktop:knowledge:<query>' - Query desktop JARVIS knowledge")
        print("   - 'desktop:task:<task>' - Send task to desktop JARVIS")
    print("6. Type 'exit' to quit\n")
    
    while True:
        try:
            user_input = input("Claude-JARVIS> ")
            
            if user_input.lower() == "exit":
                break
            
            elif user_input.lower().startswith("code:"):
                task = user_input[5:].strip()
                print(f"⚙️ Generating code for: {task}")
                
                # Detect language if specified
                language = None
                if "language:" in task:
                    parts = task.split("language:", 1)
                    task = parts[0].strip()
                    language = parts[1].strip()
                
                code = await get_code_for_task(task, language, args.enhanced)
                print("\n" + code + "\n")
            
            elif user_input.lower().startswith("query:"):
                query = user_input[6:].strip()
                print(f"🔍 Searching JARVIS knowledge for: {query}")
                
                results = await query_jarvis_knowledge(query, args.enhanced)
                print("\n" + results + "\n")
            
            elif user_input.lower().startswith("add:"):
                text = user_input[4:].strip()
                print(f"➕ Adding to JARVIS knowledge: {text[:50]}...")
                
                result = await update_jarvis_knowledge(text, use_enhanced=args.enhanced)
                print("\n" + result + "\n")
            
            elif user_input.lower().startswith("connect:"):
                assistant_url = user_input[8:].strip()
                
                # Check for API key format: connect:url:apikey
                parts = assistant_url.split(":", 1)
                api_key = None
                if len(parts) > 1:
                    assistant_url = parts[0].strip()
                    api_key = parts[1].strip()
                
                print(f"🔌 Connecting to desktop JARVIS at: {assistant_url}")
                result = await connect_desktop_assistant(assistant_url, api_key)
                print("\n" + result + "\n")
            
            elif user_input.lower().startswith("desktop:"):
                if not desktop_assistant_connected:
                    print("❌ No desktop JARVIS assistant connected. Use 'connect:<url>' first.")
                    continue
                
                command_parts = user_input[8:].strip().split(":", 1)
                command = command_parts[0].strip()
                
                data = {}
                if len(command_parts) > 1:
                    # Command has parameters
                    if command == "voice":
                        data["text"] = command_parts[1].strip()
                    elif command == "knowledge":
                        data["query"] = command_parts[1].strip()
                    elif command == "task":
                        data["task"] = command_parts[1].strip()
                
                print(f"📤 Sending '{command}' command to desktop JARVIS...")
                result = await send_to_desktop_assistant(command, data)
                print("\n" + result + "\n")
            
            else:
                print("⚠️ Unknown command format. Please use 'code:', 'query:', 'add:', 'connect:', or 'exit'.")
        
        except KeyboardInterrupt:
            print("\n👋 Interrupted by user.")
            break
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}")
            print(f"\n❌ Error: {str(e)}\n")
    
    # Shutdown
    print("👋 Shutting down...")
    if enhanced_system:
        await enhanced_system.shutdown()
    elif bridge:
        await bridge.shutdown()
    print("Claude-JARVIS connection closed.")

# Register as a module that can be imported by Claude
def enable_jarvis_knowledge(use_enhanced=True):
    """Function that can be called by Claude to access JARVIS knowledge."""
    # Set environment variable to indicate Claude has access to JARVIS knowledge
    os.environ["CLAUDE_JARVIS_ENABLED"] = "true"
    os.environ["CLAUDE_JARVIS_ENHANCED"] = str(use_enhanced).lower()
    
    # Initialize the bridge asynchronously
    async def _init():
        await initialize_bridge(use_enhanced_system=use_enhanced)
    
    # Run initialization in a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_init())
    
    # Return useful functions for Claude to use
    return {
        "generate_code": get_code_for_task,
        "query_knowledge": query_jarvis_knowledge,
        "update_knowledge": update_jarvis_knowledge,
        "connect_desktop_assistant": connect_desktop_assistant,
        "send_to_desktop_assistant": send_to_desktop_assistant
    }

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main()) 