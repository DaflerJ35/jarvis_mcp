import os
import logging
import asyncio
import base64
import json
import tempfile
from typing import Dict, Any, List, Optional, Union, BinaryIO
import re

class MultiModalProcessor:
    """
    Multi-Modal Input Processor for J.A.R.V.I.S.
    Handles voice commands, images, and diagrams for more natural interaction.
    """
    
    def __init__(self, knowledge_enhancer):
        self.knowledge = knowledge_enhancer
        self.logger = logging.getLogger("JARVIS-MultiModal")
        
        # Available processing modes
        self.processors = {
            "voice": self._process_voice_internal,
            "image": self._process_image_internal,
            "diagram": self._process_diagram_internal,
            "screenshot": self._process_screenshot_internal
        }
        
        # Model settings
        self.settings = {
            "voice_model": "whisper-large-v3",
            "image_model": "clip-vit-large",
            "text_detection_model": "tesseract-v5",
            "diagram_model": "diagram-recognition-v1"
        }
        
        # Processing history
        self.processing_history = []
        
        # Cache for processed results
        self.cache = {}
        
        # Active flag
        self.active = False
    
    async def start(self):
        """Start the multi-modal processor."""
        self.active = True
        self.logger.info("Starting Multi-Modal Input Processor")
        
        # Add system knowledge
        self.knowledge.add_to_knowledge(
            text="The Multi-Modal Input Processor enables J.A.R.V.I.S. to understand voice commands, "
                 "images, diagrams, and screenshots for more natural interaction.",
            source="system_documentation",
            metadata={"component": "multimodal", "importance": "high"}
        )
        
        return True
    
    async def process_voice(self, voice_data: Union[str, BinaryIO]) -> Dict[str, Any]:
        """
        Process voice input data.
        
        Args:
            voice_data: Either a path to an audio file or binary audio data
            
        Returns:
            Dict containing the processing results
        """
        if not self.active:
            return {"error": "Multi-Modal Processor is not active"}
        
        try:
            # Check if we've processed this voice data before (using hash as key)
            if isinstance(voice_data, str) and os.path.exists(voice_data):
                # It's a file path
                with open(voice_data, "rb") as f:
                    data_hash = str(hash(f.read()))
            else:
                # It's binary data
                data_hash = str(hash(voice_data))
            
            # Check cache
            if data_hash in self.cache:
                self.logger.info("Returning cached voice processing result")
                return self.cache[data_hash]
            
            # Process the voice data
            result = await self._process_voice_internal(voice_data)
            
            # Add to processing history
            self.processing_history.append({
                "type": "voice",
                "timestamp": self._get_timestamp(),
                "result_summary": f"Processed voice: {result.get('text', '')[:50]}..."
            })
            
            # Cache the result
            self.cache[data_hash] = result
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error processing voice: {str(e)}")
            return {"error": str(e)}
    
    async def process_image(self, image_data: Union[str, BinaryIO], image_type: str = "general") -> Dict[str, Any]:
        """
        Process image input data.
        
        Args:
            image_data: Either a path to an image file or binary image data
            image_type: Type of image ("general", "diagram", "screenshot", "code")
            
        Returns:
            Dict containing the processing results
        """
        if not self.active:
            return {"error": "Multi-Modal Processor is not active"}
        
        try:
            # Check if we've processed this image before (using hash as key)
            if isinstance(image_data, str) and os.path.exists(image_data):
                # It's a file path
                with open(image_data, "rb") as f:
                    data_hash = str(hash(f.read()))
            else:
                # It's binary data
                data_hash = str(hash(image_data))
            
            # Add image type to the hash to differentiate processing modes
            cache_key = f"{data_hash}_{image_type}"
            
            # Check cache
            if cache_key in self.cache:
                self.logger.info("Returning cached image processing result")
                return self.cache[cache_key]
            
            # Process the image based on type
            if image_type == "diagram":
                result = await self._process_diagram_internal(image_data)
            elif image_type == "screenshot":
                result = await self._process_screenshot_internal(image_data)
            elif image_type == "code":
                result = await self._process_code_image_internal(image_data)
            else:
                result = await self._process_image_internal(image_data)
            
            # Add to processing history
            self.processing_history.append({
                "type": f"image_{image_type}",
                "timestamp": self._get_timestamp(),
                "result_summary": f"Processed {image_type} image: {result.get('description', '')[:50]}..."
            })
            
            # Cache the result
            self.cache[cache_key] = result
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error processing image: {str(e)}")
            return {"error": str(e)}
    
    async def _process_voice_internal(self, voice_data: Union[str, BinaryIO]) -> Dict[str, Any]:
        """Internal method to process voice data."""
        self.logger.info("Processing voice data")
        
        # In a real implementation, this would use a speech recognition model
        # Here, we'll simulate processing voice to text
        
        # Create a temp file if needed
        temp_file = None
        file_path = voice_data
        
        try:
            if not isinstance(voice_data, str):
                # Create a temporary file to save the binary data
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                temp_file.write(voice_data.read() if hasattr(voice_data, "read") else voice_data)
                temp_file.close()
                file_path = temp_file.name
            
            # Simulate voice recognition
            # In a real implementation, this would call a speech recognition API
            
            # Simulate some processing delay
            await asyncio.sleep(0.5)
            
            # Determine if this is a coding-related query
            # In a real implementation, this would analyze the transcribed text
            
            # Simulate some potential voice commands and their transcriptions
            potential_commands = {
                "create a function to process user input": {
                    "text": "Create a function to process user input",
                    "detected_task": "Create a function to process user input",
                    "detected_language": "python",
                    "confidence": 0.92
                },
                "show me the status of the jarvis system": {
                    "text": "Show me the status of the JARVIS system",
                    "intent": "system_status",
                    "confidence": 0.89
                },
                "explain how the voice recognition works": {
                    "text": "Explain how the voice recognition works",
                    "intent": "explanation",
                    "confidence": 0.95
                }
            }
            
            # Simulate picking one of the commands based on the file hash
            file_hash = hash(file_path)
            command_idx = file_hash % len(potential_commands)
            command_key = list(potential_commands.keys())[command_idx]
            result = potential_commands[command_key]
            
            # Add filename to result
            result["source"] = file_path
            
            # Add file analysis
            result["file_duration_seconds"] = 3.5  # Simulated duration
            
            # Add to knowledge base
            self.knowledge.add_to_knowledge(
                text=f"Voice command: {result['text']}",
                source="voice_processing",
                metadata={
                    "confidence": result.get("confidence", 0),
                    "intent": result.get("intent", "unknown"),
                    "task": result.get("detected_task", "")
                }
            )
            
            return result
        
        finally:
            # Clean up temp file if created
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    async def _process_image_internal(self, image_data: Union[str, BinaryIO]) -> Dict[str, Any]:
        """Internal method to process general image data."""
        self.logger.info("Processing general image data")
        
        # In a real implementation, this would use computer vision models
        # Here, we'll simulate image analysis
        
        # Create a temp file if needed
        temp_file = None
        file_path = image_data
        
        try:
            if not isinstance(image_data, str):
                # Create a temporary file to save the binary data
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                temp_file.write(image_data.read() if hasattr(image_data, "read") else image_data)
                temp_file.close()
                file_path = temp_file.name
            
            # Simulate image recognition
            # In a real implementation, this would call a computer vision API
            
            # Simulate some processing delay
            await asyncio.sleep(0.7)
            
            # Simulate different types of image content
            potential_descriptions = [
                {
                    "description": "A screenshot of code showing a Python class definition",
                    "contains_code": True,
                    "detected_language": "python",
                    "confidence": 0.87,
                    "extracted_text": "class ImageProcessor:\n    def __init__(self):\n        self.model = load_model()"
                },
                {
                    "description": "A system architecture diagram with components and connections",
                    "contains_diagram": True,
                    "diagram_type": "architecture",
                    "confidence": 0.93,
                    "components": ["API", "Database", "Frontend", "Backend"]
                },
                {
                    "description": "A user interface mockup for a dashboard",
                    "contains_ui": True,
                    "ui_type": "dashboard",
                    "confidence": 0.91,
                    "elements": ["Header", "Sidebar", "Main Content", "Footer"]
                }
            ]
            
            # Simulate picking one description based on the file hash
            file_hash = hash(file_path)
            desc_idx = file_hash % len(potential_descriptions)
            result = potential_descriptions[desc_idx]
            
            # Add filename to result
            result["source"] = file_path
            
            # Add to knowledge base
            self.knowledge.add_to_knowledge(
                text=f"Image analysis: {result['description']}",
                source="image_processing",
                metadata={
                    "confidence": result.get("confidence", 0),
                    "image_type": "code" if result.get("contains_code", False) else 
                                ("diagram" if result.get("contains_diagram", False) else 
                                 ("ui" if result.get("contains_ui", False) else "general"))
                }
            )
            
            return result
        
        finally:
            # Clean up temp file if created
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    async def _process_diagram_internal(self, image_data: Union[str, BinaryIO]) -> Dict[str, Any]:
        """Internal method to process diagram images."""
        self.logger.info("Processing diagram image")
        
        # First get general image analysis
        general_result = await self._process_image_internal(image_data)
        
        # Enhance with diagram-specific analysis
        diagram_result = {
            **general_result,
            "diagram_analysis": {
                "type": "architecture" if "architecture" in general_result.get("description", "").lower() else 
                        ("flowchart" if "flow" in general_result.get("description", "").lower() else 
                         ("entity_relationship" if "ER" in general_result.get("description", "").upper() else "unknown")),
                "components": general_result.get("components", ["Component A", "Component B", "Component C"]),
                "relationships": [
                    {"from": "Component A", "to": "Component B", "type": "depends_on"},
                    {"from": "Component B", "to": "Component C", "type": "contains"}
                ]
            }
        }
        
        # Add to knowledge base
        self.knowledge.add_to_knowledge(
            text=f"Diagram analysis: {diagram_result['description']}. " +
                 f"Type: {diagram_result['diagram_analysis']['type']}. " +
                 f"Contains {len(diagram_result['diagram_analysis']['components'])} components.",
            source="diagram_processing",
            metadata={
                "diagram_type": diagram_result['diagram_analysis']['type'],
                "components": diagram_result['diagram_analysis']['components'],
                "relationships": diagram_result['diagram_analysis']['relationships']
            }
        )
        
        return diagram_result
    
    async def _process_screenshot_internal(self, image_data: Union[str, BinaryIO]) -> Dict[str, Any]:
        """Internal method to process screenshots."""
        self.logger.info("Processing screenshot image")
        
        # First get general image analysis
        general_result = await self._process_image_internal(image_data)
        
        # Enhance with screenshot-specific analysis
        screenshot_result = {
            **general_result,
            "screenshot_analysis": {
                "contains_ui": True,
                "contains_text": True,
                "contains_code": "code" in general_result.get("description", "").lower(),
                "probable_application": "IDE" if "code" in general_result.get("description", "").lower() else 
                                       ("Browser" if "web" in general_result.get("description", "").lower() else "Unknown"),
                "extracted_text": general_result.get("extracted_text", "No text extracted")
            }
        }
        
        # If screenshot contains code, process it further
        if screenshot_result["screenshot_analysis"]["contains_code"]:
            code_text = screenshot_result.get("extracted_text", "")
            language = self._detect_code_language(code_text)
            screenshot_result["screenshot_analysis"]["code_language"] = language
            screenshot_result["screenshot_analysis"]["code_snippet"] = code_text
        
        # Add to knowledge base
        self.knowledge.add_to_knowledge(
            text=f"Screenshot analysis: {screenshot_result['description']}. " +
                 f"Contains code: {screenshot_result['screenshot_analysis']['contains_code']}. " +
                 f"Application: {screenshot_result['screenshot_analysis']['probable_application']}.",
            source="screenshot_processing",
            metadata={
                "contains_code": screenshot_result['screenshot_analysis']['contains_code'],
                "contains_ui": screenshot_result['screenshot_analysis']['contains_ui'],
                "application": screenshot_result['screenshot_analysis']['probable_application']
            }
        )
        
        return screenshot_result
    
    async def _process_code_image_internal(self, image_data: Union[str, BinaryIO]) -> Dict[str, Any]:
        """Internal method to process code images."""
        self.logger.info("Processing code image")
        
        # First get screenshot analysis
        screenshot_result = await self._process_screenshot_internal(image_data)
        
        # Enhance with code-specific analysis if code is detected
        if screenshot_result["screenshot_analysis"]["contains_code"]:
            code_text = screenshot_result["screenshot_analysis"].get("code_snippet", "")
            language = screenshot_result["screenshot_analysis"].get("code_language", "unknown")
            
            code_result = {
                **screenshot_result,
                "code_analysis": {
                    "language": language,
                    "complete_snippet": len(code_text.strip().split("\n")) > 3,  # Heuristic for "complete" snippet
                    "functionality": self._guess_code_functionality(code_text, language),
                    "extracted_code": code_text
                }
            }
            
            # Add to knowledge base
            self.knowledge.add_to_knowledge(
                text=f"Code image analysis: {code_result['description']}. " +
                     f"Language: {code_result['code_analysis']['language']}. " +
                     f"Functionality: {code_result['code_analysis']['functionality']}.",
                source="code_image_processing",
                metadata={
                    "language": code_result['code_analysis']['language'],
                    "functionality": code_result['code_analysis']['functionality'],
                    "code": code_text[:300] + "..." if len(code_text) > 300 else code_text
                }
            )
            
            return code_result
        else:
            # Not code, return screenshot result
            return screenshot_result
    
    def _detect_code_language(self, code_text: str) -> str:
        """Detect the programming language from code text."""
        # Simple language detection based on keywords and syntax
        if re.search(r'import\s+|from\s+\w+\s+import|def\s+\w+\s*\(|class\s+\w+:', code_text):
            return "python"
        elif re.search(r'function\s+|const\s+|let\s+|var\s+|import\s+from|export\s+', code_text):
            return "javascript"
        elif re.search(r'interface\s+|class\s+\w+\s+implements|extends|<\w+>|:\s*\w+', code_text):
            return "typescript"
        elif re.search(r'public\s+class|private\s+|protected\s+|void\s+|String|int|boolean', code_text):
            return "java"
        elif re.search(r'#include|std::|void\s+\w+\s*\(|int\s+main', code_text):
            return "c++"
        else:
            return "unknown"
    
    def _guess_code_functionality(self, code_text: str, language: str) -> str:
        """Guess the functionality of a code snippet."""
        # This is a very simple heuristic approach
        if "def test" in code_text or "@test" in code_text:
            return "unit test"
        elif "class" in code_text and "def __init__" in code_text:
            return "class definition"
        elif "function" in code_text or "def " in code_text:
            return "function definition"
        elif "import" in code_text or "require" in code_text:
            return "imports/dependencies"
        elif "=" in code_text and "{" in code_text and "}" in code_text:
            return "data structure definition"
        elif "if" in code_text and "else" in code_text:
            return "conditional logic"
        elif "for" in code_text or "while" in code_text:
            return "loop/iteration"
        elif "try" in code_text and "catch" in code_text:
            return "error handling"
        else:
            return "general code"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        import datetime
        return datetime.datetime.now().isoformat()
    
    async def shutdown(self):
        """Shut down the multi-modal processor."""
        self.logger.info("Shutting down Multi-Modal Input Processor")
        self.active = False
        
        # Clear cache
        self.cache.clear()
        
        return True 