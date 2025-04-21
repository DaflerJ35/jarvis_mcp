import os
import importlib.util
import inspect
import sys
import json
import logging
import pkgutil
import re
import traceback
from typing import Dict, List, Any, Callable, Optional, Union, Tuple
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("jarvis_skills.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("JARVIS-Skills")

class JARVISSkill(ABC):
    """
    Base class for all JARVIS skills
    """
    def __init__(self, name: str, description: str, version: str = "1.0"):
        self.name = name
        self.description = description
        self.version = version
        self.enabled = True
        self.commands = []
        self._register_commands()
    
    def _register_commands(self):
        """
        Register all commands this skill can handle
        """
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, '_skill_command'):
                command_info = getattr(method, '_skill_command')
                self.commands.append(command_info)
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the skill. Must be implemented by skill classes.
        Returns True if initialization was successful, False otherwise.
        """
        pass
    
    def shutdown(self) -> bool:
        """
        Cleanup when skill is disabled or JARVIS is shutting down
        """
        return True
    
    def enable(self) -> bool:
        """
        Enable this skill
        """
        self.enabled = True
        return True
    
    def disable(self) -> bool:
        """
        Disable this skill
        """
        self.enabled = False
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this skill
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "commands": self.commands
        }
    
    def get_commands(self) -> List[Dict[str, Any]]:
        """
        Get all commands this skill can handle
        """
        return self.commands

# Decorator for skill commands
def skill_command(command_patterns: List[str], description: str, examples: List[str] = None):
    """
    Decorator to mark a method as a skill command handler
    
    Args:
        command_patterns: List of regex patterns that will trigger this command
        description: Description of what this command does
        examples: List of example phrases that would trigger this command
    """
    if examples is None:
        examples = []
        
    def decorator(func):
        func._skill_command = {
            "name": func.__name__,
            "patterns": command_patterns,
            "description": description,
            "examples": examples,
            "handler": func.__name__
        }
        return func
    
    return decorator

class SkillManager:
    """
    Manages all skills for JARVIS
    """
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = skills_dir
        self.skills: Dict[str, JARVISSkill] = {}
        self.command_patterns = []
        self.pattern_to_skill_map = {}
        
        # Create skills directory if it doesn't exist
        os.makedirs(self.skills_dir, exist_ok=True)
    
    def discover_skills(self) -> List[str]:
        """
        Discover available skills in the skills directory
        """
        skill_files = []
        
        # Check if the skills directory exists
        if not os.path.exists(self.skills_dir):
            logger.warning(f"Skills directory {self.skills_dir} doesn't exist!")
            return skill_files
        
        # Walk through the skills directory
        for root, dirs, files in os.walk(self.skills_dir):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    # Get the relative path to the skills directory
                    rel_path = os.path.relpath(os.path.join(root, file), self.skills_dir)
                    # Convert path to module name (e.g., weather/forecast.py -> weather.forecast)
                    module_name = os.path.splitext(rel_path.replace(os.sep, '.'))[0]
                    skill_files.append(os.path.join(root, file))
        
        return skill_files
    
    def load_skill(self, skill_path: str) -> Optional[str]:
        """
        Load a skill from a Python file
        
        Returns:
            The skill ID if successful, None otherwise
        """
        try:
            # Extract module name from path
            module_name = os.path.splitext(os.path.basename(skill_path))[0]
            
            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, skill_path)
            if spec is None or spec.loader is None:
                logger.error(f"Failed to load skill spec from {skill_path}")
                return None
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find skill classes in the module
            skill_classes = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, JARVISSkill) and 
                    obj != JARVISSkill):
                    skill_classes.append(obj)
            
            if not skill_classes:
                logger.warning(f"No skill classes found in {skill_path}")
                return None
            
            # Create an instance of the skill
            skill_class = skill_classes[0]  # Take the first skill class
            skill = skill_class()
            
            # Initialize the skill
            if not skill.initialize():
                logger.error(f"Failed to initialize skill {skill.name}")
                return None
            
            # Register the skill
            skill_id = skill.name.lower().replace(' ', '_')
            self.skills[skill_id] = skill
            
            # Register command patterns
            for command in skill.get_commands():
                for pattern in command["patterns"]:
                    self.command_patterns.append(pattern)
                    self.pattern_to_skill_map[pattern] = (skill_id, command["handler"])
            
            logger.info(f"Successfully loaded skill: {skill.name} (id: {skill_id})")
            return skill_id
            
        except Exception as e:
            logger.error(f"Error loading skill from {skill_path}: {str(e)}")
            traceback.print_exc()
            return None
    
    def load_all_skills(self) -> int:
        """
        Load all available skills
        
        Returns:
            Number of successfully loaded skills
        """
        skill_files = self.discover_skills()
        loaded_count = 0
        
        for skill_file in skill_files:
            if self.load_skill(skill_file) is not None:
                loaded_count += 1
        
        logger.info(f"Loaded {loaded_count} of {len(skill_files)} skills")
        return loaded_count
    
    def unload_skill(self, skill_id: str) -> bool:
        """
        Unload a skill
        
        Returns:
            True if successful, False otherwise
        """
        if skill_id not in self.skills:
            logger.warning(f"Skill {skill_id} not found")
            return False
        
        skill = self.skills[skill_id]
        
        # Shutdown the skill
        try:
            skill.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down skill {skill_id}: {str(e)}")
        
        # Remove command patterns
        to_remove = []
        for pattern, (sid, _) in self.pattern_to_skill_map.items():
            if sid == skill_id:
                to_remove.append(pattern)
        
        for pattern in to_remove:
            if pattern in self.pattern_to_skill_map:
                del self.pattern_to_skill_map[pattern]
                if pattern in self.command_patterns:
                    self.command_patterns.remove(pattern)
        
        # Remove the skill
        del self.skills[skill_id]
        
        logger.info(f"Unloaded skill: {skill_id}")
        return True
    
    def enable_skill(self, skill_id: str) -> bool:
        """
        Enable a skill
        
        Returns:
            True if successful, False otherwise
        """
        if skill_id not in self.skills:
            logger.warning(f"Skill {skill_id} not found")
            return False
        
        return self.skills[skill_id].enable()
    
    def disable_skill(self, skill_id: str) -> bool:
        """
        Disable a skill
        
        Returns:
            True if successful, False otherwise
        """
        if skill_id not in self.skills:
            logger.warning(f"Skill {skill_id} not found")
            return False
        
        return self.skills[skill_id].disable()
    
    def get_skill_info(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a skill
        
        Returns:
            Skill info dictionary or None if skill not found
        """
        if skill_id not in self.skills:
            logger.warning(f"Skill {skill_id} not found")
            return None
        
        return self.skills[skill_id].get_info()
    
    def get_all_skills_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all skills
        
        Returns:
            List of skill info dictionaries
        """
        return [skill.get_info() for skill in self.skills.values()]
    
    def get_all_commands(self) -> List[Dict[str, Any]]:
        """
        Get all commands from all skills
        
        Returns:
            List of command info dictionaries
        """
        all_commands = []
        for skill_id, skill in self.skills.items():
            if not skill.enabled:
                continue
            
            for command in skill.get_commands():
                command_copy = command.copy()
                command_copy["skill_id"] = skill_id
                all_commands.append(command_copy)
        
        return all_commands
    
    def match_command(self, text: str) -> Optional[Tuple[str, str, re.Match]]:
        """
        Match text against command patterns
        
        Returns:
            Tuple of (skill_id, handler_name, match_object) or None if no match
        """
        for pattern, (skill_id, handler) in self.pattern_to_skill_map.items():
            # Skip disabled skills
            if not self.skills[skill_id].enabled:
                continue
                
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                return (skill_id, handler, match)
        
        return None
    
    def execute_command(self, text: str) -> Tuple[bool, Any]:
        """
        Execute a command based on text input
        
        Returns:
            Tuple of (success, result)
        """
        match_result = self.match_command(text)
        
        if match_result is None:
            return (False, f"No matching command found for: {text}")
        
        skill_id, handler_name, match = match_result
        skill = self.skills[skill_id]
        
        try:
            # Get the method from the skill
            handler_method = getattr(skill, handler_name)
            
            # Call the handler with the match object
            result = handler_method(match)
            return (True, result)
            
        except Exception as e:
            logger.error(f"Error executing command {text} with skill {skill_id}: {str(e)}")
            traceback.print_exc()
            return (False, f"Error executing command: {str(e)}")
    
    def create_skill_template(self, skill_name: str) -> str:
        """
        Create a new skill template file
        
        Returns:
            Path to the created file or empty string if failed
        """
        # Create sanitized filename
        filename = skill_name.lower().replace(' ', '_') + '_skill.py'
        filepath = os.path.join(self.skills_dir, filename)
        
        # Check if file already exists
        if os.path.exists(filepath):
            logger.warning(f"Skill file {filepath} already exists")
            return ""
        
        # Create the template content
        template = f'''# {skill_name} Skill for JARVIS
# Created by JARVIS Skills Manager

from jarvis_skills_system import JARVISSkill, skill_command
import logging

logger = logging.getLogger("JARVIS-Skills.{filename}")

class {skill_name.replace(' ', '')}Skill(JARVISSkill):
    """
    {skill_name} Skill for JARVIS
    """
    
    def __init__(self):
        super().__init__(
            name="{skill_name}",
            description="A skill that provides {skill_name} functionality",
            version="1.0"
        )
        
    def initialize(self) -> bool:
        """
        Initialize the skill
        """
        logger.info("{skill_name} skill initialized")
        return True
    
    def shutdown(self) -> bool:
        """
        Clean up when skill is disabled or JARVIS is shutting down
        """
        logger.info("{skill_name} skill shutdown")
        return True
    
    @skill_command(
        command_patterns=[r"(?i)hello {skill_name.lower()}"],
        description="Responds to hello",
        examples=["hello {skill_name.lower()}"]
    )
    def hello_command(self, match):
        """
        Example command that responds to hello
        """
        return f"Hello from {skill_name} skill!"
    
    # Add more commands here using the @skill_command decorator
'''
        
        # Write the template to file
        try:
            with open(filepath, 'w') as f:
                f.write(template)
            logger.info(f"Created skill template at {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error creating skill template: {str(e)}")
            return ""

# Example weather skill
class WeatherSkill(JARVISSkill):
    """
    Example weather skill for JARVIS
    """
    
    def __init__(self):
        super().__init__(
            name="Weather",
            description="Get weather information",
            version="1.0"
        )
        self.api_key = None
    
    def initialize(self) -> bool:
        """
        Initialize the weather skill
        """
        # In a real implementation, you would load API keys from config
        self.api_key = "dummy_key"
        return True
    
    @skill_command(
        command_patterns=[
            r"(?i)what('s| is) the weather(?: like)?(?: in (.+))?",
            r"(?i)weather(?: (?:for|in) (.+))?"
        ],
        description="Get current weather",
        examples=["what's the weather like in New York", "weather in London"]
    )
    def get_weather(self, match):
        """
        Get current weather information
        """
        location = match.group(1) if match.lastindex and match.group(1) else "current location"
        return f"The weather in {location} is currently sunny with a temperature of 72°F."
    
    @skill_command(
        command_patterns=[
            r"(?i)what('s| is) the forecast(?: (?:for|in) (.+))?"
        ],
        description="Get weather forecast",
        examples=["what's the forecast for tomorrow", "forecast for New York"]
    )
    def get_forecast(self, match):
        """
        Get weather forecast
        """
        timeframe = match.group(1) if match.lastindex and match.group(1) else "today"
        return f"The forecast for {timeframe} is partly cloudy with a high of 75°F and a low of 60°F."

# Test function to demonstrate the skill system
def test_skill_system():
    # Create skills directory if it doesn't exist
    os.makedirs("skills", exist_ok=True)
    
    # Create a test skill file
    with open("skills/weather_skill.py", "w") as f:
        f.write(inspect.getsource(WeatherSkill))
    
    # Initialize the skill manager
    manager = SkillManager()
    
    print("Loading skills...")
    loaded = manager.load_all_skills()
    print(f"Loaded {loaded} skills")
    
    # Get info about all loaded skills
    skills_info = manager.get_all_skills_info()
    print("\nLoaded Skills:")
    for info in skills_info:
        print(f"  - {info['name']} v{info['version']}: {info['description']}")
        print(f"    Commands: {len(info['commands'])}")
    
    # Test some commands
    test_commands = [
        "what's the weather like in New York",
        "what's the forecast for tomorrow",
        "tell me a joke",  # This won't match any skill
        "weather in London"
    ]
    
    print("\nTesting commands:")
    for cmd in test_commands:
        print(f"\nCommand: '{cmd}'")
        success, result = manager.execute_command(cmd)
        if success:
            print(f"Result: {result}")
        else:
            print(f"Error: {result}")
    
    # Create a new skill template
    print("\nCreating a new skill template...")
    template_path = manager.create_skill_template("Timer")
    if template_path:
        print(f"Created template at: {template_path}")
    
    # Clean up test files
    print("\nCleaning up...")
    if os.path.exists("skills/weather_skill.py"):
        os.remove("skills/weather_skill.py")
    if template_path and os.path.exists(template_path):
        os.remove(template_path)

if __name__ == "__main__":
    test_skill_system() 