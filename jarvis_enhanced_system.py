import os
import sys
import asyncio
import logging
from typing import Dict, Any, List, Optional

# Import core components
from claude_jarvis_coding_bridge import ClaudeJARVISCodingBridge
from knowledge_enhancer import JARVISKnowledgeEnhancer

# Import enhanced modules
from jarvis_modules.autonomous_evolution import CodeEvolutionSystem
from jarvis_modules.multimodal import MultiModalProcessor
from jarvis_modules.agent_network import AgentNetwork
from jarvis_modules.real_world import RealWorldIntegration
from jarvis_modules.predictive_coding import PredictiveCodingEngine
from jarvis_modules.simulation import CodeSimulationEnvironment
from jarvis_modules.version_control import VersionControlIntelligence

class JARVISEnhancedSystem:
    """
    Master coordinator for the enhanced JARVIS system that integrates all advanced capabilities.
    This system combines autonomous code evolution, multimodal input, collaborative agents,
    real-world integration, predictive coding, code simulation, and version control intelligence.
    """
    
    def __init__(self, 
                mcp_url: str = "http://localhost:8000",
                knowledge_dir: str = "knowledge_base",
                modules_dir: str = "jarvis_modules",
                log_level: str = "INFO"):
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("jarvis_enhanced.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("JARVIS-Enhanced")
        
        # Initialize core components
        self.coding_bridge = None  # Will be initialized in setup()
        self.knowledge = None      # Will be initialized in setup()
        
        # Configuration
        self.mcp_url = mcp_url
        self.knowledge_dir = knowledge_dir
        self.modules_dir = modules_dir
        
        # Enhanced modules (will be initialized in setup())
        self.evolution_system = None
        self.multimodal = None
        self.agent_network = None
        self.real_world = None
        self.predictive_engine = None
        self.simulation_env = None
        self.version_control = None
        
        # System state
        self.initialized = False
        self.active_modules = []
        
        self.logger.info("JARVIS Enhanced System initialized but not yet setup")
    
    async def setup(self):
        """Set up the enhanced system and all its components."""
        try:
            self.logger.info("Setting up JARVIS Enhanced System...")
            
            # Create necessary directories
            os.makedirs(self.knowledge_dir, exist_ok=True)
            os.makedirs(self.modules_dir, exist_ok=True)
            
            # Initialize core components
            self.knowledge = JARVISKnowledgeEnhancer(self.knowledge_dir)
            self.coding_bridge = ClaudeJARVISCodingBridge(self.mcp_url, self.knowledge_dir)
            
            # Connect to MCP
            await self.coding_bridge.initialize()
            
            # Initialize enhanced modules
            self.evolution_system = CodeEvolutionSystem(self.coding_bridge, self.knowledge)
            self.multimodal = MultiModalProcessor(self.knowledge)
            self.agent_network = AgentNetwork(self.coding_bridge)
            self.real_world = RealWorldIntegration()
            self.predictive_engine = PredictiveCodingEngine(self.knowledge, self.coding_bridge)
            self.simulation_env = CodeSimulationEnvironment()
            self.version_control = VersionControlIntelligence(self.knowledge)
            
            # Start all enhanced modules
            await self._start_enhanced_modules()
            
            self.initialized = True
            self.logger.info("JARVIS Enhanced System setup complete!")
            
            return True
        except Exception as e:
            self.logger.error(f"Error setting up JARVIS Enhanced System: {str(e)}")
            return False
    
    async def _start_enhanced_modules(self):
        """Start all enhanced modules."""
        self.logger.info("Starting enhanced modules...")
        
        # Initialize and start each module
        modules_to_start = [
            (self.evolution_system, "Autonomous Code Evolution"),
            (self.multimodal, "Multi-Modal Input Processing"),
            (self.agent_network, "Collaborative Agent Network"),
            (self.real_world, "Real-World Integration"),
            (self.predictive_engine, "Predictive Coding"),
            (self.simulation_env, "Code Simulation Environment"),
            (self.version_control, "Version Control Intelligence")
        ]
        
        for module, name in modules_to_start:
            try:
                if hasattr(module, 'start') and callable(module.start):
                    await module.start()
                    self.active_modules.append(name)
                    self.logger.info(f"Started {name} module")
            except Exception as e:
                self.logger.error(f"Failed to start {name} module: {str(e)}")
    
    async def process_request(self, request_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request using the most appropriate module.
        
        Args:
            request_type: Type of request (code, voice, image, etc.)
            data: Request data
            
        Returns:
            Dict containing the response
        """
        if not self.initialized:
            return {"error": "JARVIS Enhanced System not initialized"}
        
        self.logger.info(f"Processing {request_type} request")
        
        try:
            # Route request to appropriate module
            if request_type == "code":
                return await self._process_code_request(data)
            elif request_type == "voice":
                return await self._process_voice_request(data)
            elif request_type == "image":
                return await self._process_image_request(data)
            elif request_type == "integrate":
                return await self._process_integration_request(data)
            elif request_type == "simulate":
                return await self._process_simulation_request(data)
            elif request_type == "evolve":
                return await self._process_evolution_request(data)
            elif request_type == "predict":
                return await self._process_prediction_request(data)
            else:
                return {"error": f"Unknown request type: {request_type}"}
        except Exception as e:
            self.logger.error(f"Error processing {request_type} request: {str(e)}")
            return {"error": str(e)}
    
    async def _process_code_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a code generation request."""
        task = data.get("task")
        language = data.get("language")
        context = data.get("context")
        
        # Enhance with predictive coding
        predicted_context = await self.predictive_engine.predict_context(task, language)
        if predicted_context and not context:
            context = predicted_context
        
        # Generate code with the coding bridge
        result = await self.coding_bridge.generate_code(task, language, context)
        
        # If requested, simulate the code
        if data.get("simulate", False) and self.simulation_env:
            simulation_result = await self.simulation_env.simulate_code(
                result["code"], language, task
            )
            result["simulation"] = simulation_result
        
        # If requested, check with version control
        if data.get("version_check", False) and self.version_control:
            vc_result = await self.version_control.analyze_code_history(
                result["code"], task
            )
            result["version_analysis"] = vc_result
        
        return result
    
    async def _process_voice_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a voice input request."""
        if not self.multimodal:
            return {"error": "Multimodal module not available"}
        
        voice_data = data.get("voice_data")
        result = await self.multimodal.process_voice(voice_data)
        
        # If voice contains a coding task, process it
        if result.get("detected_task"):
            code_result = await self._process_code_request({
                "task": result["detected_task"],
                "language": result.get("detected_language")
            })
            result["code_result"] = code_result
        
        return result
    
    async def _process_image_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process an image input request."""
        if not self.multimodal:
            return {"error": "Multimodal module not available"}
        
        image_data = data.get("image_data")
        image_type = data.get("image_type", "unknown")
        
        result = await self.multimodal.process_image(image_data, image_type)
        
        # If image contains code, extract and analyze it
        if result.get("contains_code", False):
            extracted_code = result.get("extracted_code", "")
            language = result.get("detected_language", "")
            
            # Analyze the extracted code
            if self.evolution_system:
                analysis = await self.evolution_system.analyze_code(extracted_code, language)
                result["code_analysis"] = analysis
        
        return result
    
    async def _process_integration_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a real-world integration request."""
        if not self.real_world:
            return {"error": "Real-world integration module not available"}
        
        integration_type = data.get("integration_type")
        integration_data = data.get("integration_data", {})
        
        return await self.real_world.process_integration(integration_type, integration_data)
    
    async def _process_simulation_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a code simulation request."""
        if not self.simulation_env:
            return {"error": "Simulation environment not available"}
        
        code = data.get("code")
        language = data.get("language")
        scenario = data.get("scenario", "default")
        
        return await self.simulation_env.simulate_code(code, language, scenario)
    
    async def _process_evolution_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a code evolution request."""
        if not self.evolution_system:
            return {"error": "Code evolution system not available"}
        
        code = data.get("code")
        language = data.get("language")
        goals = data.get("goals", [])
        
        return await self.evolution_system.evolve_code(code, language, goals)
    
    async def _process_prediction_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a predictive coding request."""
        if not self.predictive_engine:
            return {"error": "Predictive coding engine not available"}
        
        context = data.get("context", {})
        scope = data.get("scope", "function")
        
        return await self.predictive_engine.predict_code(context, scope)
    
    async def connect_external_assistant(self, assistant_type: str, connection_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Connect an external assistant (like a desktop Jarvis) to this enhanced system.
        
        Args:
            assistant_type: Type of assistant (e.g., "desktop", "mobile", "web")
            connection_details: Connection details specific to the assistant
            
        Returns:
            Dict containing connection status and information
        """
        self.logger.info(f"Connecting external {assistant_type} assistant")
        
        try:
            # Validate connection details
            if "api_endpoint" not in connection_details:
                return {"error": "Missing API endpoint in connection details"}
            
            # Create connection object for the external assistant
            connection = {
                "type": assistant_type,
                "endpoint": connection_details["api_endpoint"],
                "auth_token": connection_details.get("auth_token"),
                "connected_at": datetime.datetime.now().isoformat(),
                "capabilities": connection_details.get("capabilities", [])
            }
            
            # Register the connection with the knowledge system
            self.knowledge.add_to_knowledge(
                text=f"Connected to external {assistant_type} assistant at {connection['endpoint']}",
                source="system_connection",
                metadata={"connection": connection}
            )
            
            # If we have an agent network, register the assistant as an agent
            if self.agent_network:
                await self.agent_network.register_external_agent(
                    assistant_type, 
                    connection_details.get("capabilities", []),
                    connection_details["api_endpoint"]
                )
            
            return {
                "status": "connected",
                "connection_id": id(connection),
                "message": f"Successfully connected to {assistant_type} assistant",
                "available_endpoints": [
                    "/knowledge/query",
                    "/code/generate",
                    "/system/status",
                    "/evolution/suggest"
                ]
            }
        except Exception as e:
            self.logger.error(f"Error connecting external assistant: {str(e)}")
            return {"error": str(e)}
    
    async def shutdown(self):
        """Shutdown all system components."""
        self.logger.info("Shutting down JARVIS Enhanced System...")
        
        # Shutdown each module
        for module, name in zip(
            [self.evolution_system, self.multimodal, self.agent_network, 
             self.real_world, self.predictive_engine, self.simulation_env, 
             self.version_control],
            self.active_modules
        ):
            try:
                if hasattr(module, 'shutdown') and callable(module.shutdown):
                    await module.shutdown()
                    self.logger.info(f"Shut down {name} module")
            except Exception as e:
                self.logger.error(f"Error shutting down {name} module: {str(e)}")
        
        # Shutdown core components
        if self.coding_bridge:
            await self.coding_bridge.shutdown()
        
        self.initialized = False
        self.logger.info("JARVIS Enhanced System shutdown complete")

# Main entry point
async def main():
    """Main entry point for running the enhanced system."""
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="JARVIS Enhanced System")
    parser.add_argument("--mcp-url", default="http://localhost:8000", help="MCP server URL")
    parser.add_argument("--knowledge-dir", default="knowledge_base", help="Knowledge base directory")
    parser.add_argument("--modules-dir", default="jarvis_modules", help="Modules directory")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level")
    args = parser.parse_args()
    
    # Create and setup the enhanced system
    system = JARVISEnhancedSystem(
        mcp_url=args.mcp_url,
        knowledge_dir=args.knowledge_dir,
        modules_dir=args.modules_dir,
        log_level=args.log_level
    )
    
    success = await system.setup()
    if not success:
        print("Failed to setup JARVIS Enhanced System")
        return
    
    # Interactive mode
    print("\n🚀 JARVIS Enhanced System")
    print("========================")
    print("Available commands:")
    print("- code: <task> [language:<language>]")
    print("- voice: <voice_data_file>")
    print("- image: <image_file>")
    print("- integrate: <integration_type> <data>")
    print("- simulate: <code_file> <language>")
    print("- evolve: <code_file> <goals>")
    print("- predict: <context> <scope>")
    print("- connect: <assistant_type> <endpoint>")
    print("- exit")
    
    while True:
        command = input("\nJARVIS-Enhanced> ")
        
        if command.lower() == "exit":
            break
        
        parts = command.split(":", 1)
        if len(parts) != 2:
            print("Invalid command format. Use 'command: data'")
            continue
        
        cmd_type, data = parts
        cmd_type = cmd_type.strip().lower()
        data = data.strip()
        
        try:
            if cmd_type == "connect":
                # Parse connection command
                assistant_type, endpoint = data.split(" ", 1)
                result = await system.connect_external_assistant(
                    assistant_type,
                    {"api_endpoint": endpoint}
                )
            else:
                # Process regular command
                result = await system.process_request(cmd_type, {"task": data})
            
            # Display result
            if isinstance(result, dict) and "code" in result:
                print("\n" + "=" * 50)
                print(result["code"])
                print("=" * 50)
            else:
                print(result)
        except Exception as e:
            print(f"Error processing command: {str(e)}")
    
    # Shutdown system
    await system.shutdown()

if __name__ == "__main__":
    import datetime  # Required for assistant connection
    asyncio.run(main()) 