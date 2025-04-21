import asyncio
import json
import os
import sys
import importlib.util
import re
import datetime
from typing import Dict, Any, List, Optional, Union, Callable
from claude_mcp_connector import ClaudeMCPConnector
from knowledge_enhancer import JARVISKnowledgeEnhancer

class ClaudeJARVISCodingBridge:
    """
    Advanced bridge that enables Claude to directly access the JARVIS MCP knowledge system
    when generating code, creating a seamless integration between Claude's coding abilities
    and the JARVIS knowledge base.
    """
    
    def __init__(self, mcp_url: str = "http://localhost:8000", 
                knowledge_base_dir: str = "knowledge_base"):
        self.connector = ClaudeMCPConnector(mcp_url)
        
        # Direct access to knowledge base for faster retrieval during coding tasks
        self.knowledge = JARVISKnowledgeEnhancer(knowledge_base_dir)
        
        # Code snippets cache for faster access
        self.code_snippets = {}
        
        # Coding context memory
        self.coding_context = {
            "current_task": None,
            "related_files": [],
            "dependencies": [],
            "api_references": {},
            "design_patterns": [],
            "style_guide": {}
        }
        
        # Initialize specialized code embeddings
        self.code_embedding_initialized = False
        
        # Track coding sessions
        self.session_id = None
        self.session_history = []
    
    async def initialize(self):
        """Initialize the connection to the JARVIS MCP."""
        print("Initializing Claude-JARVIS Coding Bridge...")
        
        # Connect to MCP
        connected = await self.connector.initialize()
        if not connected:
            print("Failed to connect to JARVIS MCP. Operating in standalone mode.")
            return False
        
        # Initialize code embeddings
        await self._initialize_code_embeddings()
        
        # Create new coding session
        self.session_id = f"coding_session_{len(self.session_history) + 1}"
        
        print("Claude-JARVIS Coding Bridge initialized and ready for advanced code generation.")
        return True
    
    async def _initialize_code_embeddings(self):
        """Initialize specialized code embeddings for better code understanding."""
        try:
            # Add special code-specific knowledge
            self.knowledge.add_to_knowledge(
                text="Python best practices include following PEP 8, using meaningful variable names, "
                    "employing docstrings, handling exceptions properly, and using type hints.",
                source="coding_standards",
                metadata={"type": "code_standards", "language": "python"}
            )
            
            self.knowledge.add_to_knowledge(
                text="JARVIS system architecture follows a modular design with separate components for "
                    "voice recognition, knowledge processing, task automation, and API integration.",
                source="jarvis_architecture",
                metadata={"type": "architecture", "project": "jarvis"}
            )
            
            # More specialized code knowledge would be added here
            
            self.code_embedding_initialized = True
        except Exception as e:
            print(f"Error initializing code embeddings: {str(e)}")
    
    async def get_code_context(self, query: str) -> Dict[str, Any]:
        """
        Get relevant code context for the given query, combining knowledge base results
        with code-specific understanding.
        """
        # Search knowledge base
        knowledge_results = self.knowledge.semantic_search(query, top_k=3)
        
        # Search for code-specific patterns in the query
        code_patterns = self._extract_code_patterns(query)
        
        # Search for related code snippets
        code_snippets = await self._find_related_code_snippets(query)
        
        # Combine results
        context = {
            "knowledge_results": knowledge_results,
            "code_patterns": code_patterns,
            "code_snippets": code_snippets,
            "coding_context": self.coding_context
        }
        
        # Add to session history
        self._add_to_session_history({
            "type": "context_query",
            "query": query,
            "results_count": len(knowledge_results) + len(code_snippets)
        })
        
        return context
    
    def _extract_code_patterns(self, query: str) -> List[Dict[str, Any]]:
        """Extract code-specific patterns from the query."""
        patterns = []
        
        # Look for language indicators
        language_patterns = {
            "python": r"python|\.py|django|flask|fastapi",
            "javascript": r"javascript|js|node|react|angular|vue",
            "typescript": r"typescript|ts|angular|react|vue",
            "java": r"java|spring|gradle|maven",
            "c#": r"c#|\.net|asp\.net|unity",
            "c++": r"c\+\+|cpp",
            "go": r"golang|go lang",
            "rust": r"rust|cargo"
        }
        
        for lang, pattern in language_patterns.items():
            if re.search(pattern, query.lower()):
                patterns.append({"type": "language", "value": lang})
        
        # Look for framework indicators
        framework_patterns = {
            "web": r"web|http|html|css|frontend|backend",
            "api": r"api|rest|graphql|endpoint",
            "data": r"database|sql|nosql|mongodb|postgresql|mysql|sqlite",
            "ai": r"ai|ml|machine learning|neural|deep learning|model",
            "voice": r"voice|speech|recognition|audio|sound"
        }
        
        for framework, pattern in framework_patterns.items():
            if re.search(pattern, query.lower()):
                patterns.append({"type": "framework", "value": framework})
        
        # Look for task indicators
        task_patterns = {
            "function": r"function|method|def|implement",
            "class": r"class|object|inheritance",
            "debug": r"debug|error|fix|issue|problem",
            "optimize": r"optimize|performance|speed|efficient",
            "setup": r"setup|install|configure|environment"
        }
        
        for task, pattern in task_patterns.items():
            if re.search(pattern, query.lower()):
                patterns.append({"type": "task", "value": task})
        
        return patterns
    
    async def _find_related_code_snippets(self, query: str) -> List[Dict[str, Any]]:
        """Find code snippets related to the query from various sources."""
        snippets = []
        
        # Try from cache first
        cached_snippets = self._get_from_snippet_cache(query)
        if cached_snippets:
            return cached_snippets
        
        # Try from knowledge base
        code_results = self.knowledge.semantic_search(f"code {query}", top_k=3)
        for result in code_results:
            # Extract code blocks using regex
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', result.get("text", ""), re.DOTALL)
            
            if not code_blocks:
                # Try other code patterns like indented blocks
                code_blocks = re.findall(r'(?:^|\n)((?:    |\t).*(?:\n(?:    |\t).*)*)', result.get("text", ""), re.DOTALL)
            
            if code_blocks:
                for block in code_blocks:
                    language = self._detect_language(block)
                    snippets.append({
                        "code": block,
                        "language": language,
                        "source": result.get("source", "Unknown"),
                        "relevance": result.get("score", 0)
                    })
        
        # If we found snippets, add to cache
        if snippets:
            self._add_to_snippet_cache(query, snippets)
        
        return snippets
    
    def _get_from_snippet_cache(self, query: str) -> List[Dict[str, Any]]:
        """Get code snippets from cache if available."""
        # Simplify query for better cache hits
        simplified_query = self._simplify_query(query)
        
        for cached_query, snippets in self.code_snippets.items():
            if simplified_query in self._simplify_query(cached_query) or self._simplify_query(cached_query) in simplified_query:
                return snippets
        
        return []
    
    def _add_to_snippet_cache(self, query: str, snippets: List[Dict[str, Any]]):
        """Add code snippets to cache."""
        self.code_snippets[query] = snippets
        
        # Limit cache size
        if len(self.code_snippets) > 100:
            # Remove oldest entries
            oldest_keys = list(self.code_snippets.keys())[:-100]
            for key in oldest_keys:
                del self.code_snippets[key]
    
    def _simplify_query(self, query: str) -> str:
        """Simplify query for better matching."""
        # Convert to lowercase
        query = query.lower()
        
        # Remove common words
        stop_words = ["a", "an", "the", "is", "are", "in", "on", "at", "for", "with", "how", "to"]
        for word in stop_words:
            query = query.replace(f" {word} ", " ")
        
        # Remove special characters
        query = re.sub(r'[^\w\s]', '', query)
        
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language from code snippet."""
        # Simple language detection based on keywords and syntax
        if re.search(r'import\s+|from\s+\w+\s+import|def\s+\w+\s*\(|class\s+\w+:', code):
            return "python"
        elif re.search(r'function\s+|const\s+|let\s+|var\s+|import\s+from|export\s+', code):
            return "javascript"
        elif re.search(r'interface\s+|class\s+\w+\s+implements|extends|<\w+>|:\s*\w+', code):
            return "typescript"
        elif re.search(r'public\s+class|private\s+|protected\s+|void\s+|String|int|boolean', code):
            return "java"
        elif re.search(r'#include|std::|void\s+\w+\s*\(|int\s+main', code):
            return "c++"
        else:
            return "unknown"
    
    async def generate_code(self, task_description: str, language: str = None, 
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate code for the given task using knowledge from the JARVIS MCP system.
        """
        # Update coding context
        self.coding_context["current_task"] = task_description
        
        # Get context if not provided
        if context is None:
            context = await self.get_code_context(task_description)
        
        # Determine language if not specified
        if language is None:
            # Try to extract from context
            for pattern in context.get("code_patterns", []):
                if pattern.get("type") == "language":
                    language = pattern.get("value")
                    break
            
            # Default to Python if still not determined
            if language is None:
                language = "python"
        
        # Get relevant knowledge from MCP
        knowledge_prompt = f"Generate {language} code for: {task_description}"
        
        try:
            # Try to use MCP if connected
            knowledge_results = await self.connector.process_message(f"/jarvis ask {knowledge_prompt}")
            
            # Extract useful information
            knowledge_insights = self._extract_insights(knowledge_results)
            
            # Get code patterns and best practices
            code_patterns = self._get_language_best_practices(language)
            
            # Generate code using context, knowledge and patterns
            code = self._generate_code_with_context(
                task_description, 
                language, 
                knowledge_insights,
                code_patterns,
                context
            )
            
            # Add to knowledge base for future use
            self.knowledge.add_to_knowledge(
                text=f"Code for {task_description}:\n```{language}\n{code}\n```",
                source="claude_generated",
                metadata={
                    "type": "code_snippet", 
                    "language": language,
                    "task": task_description
                }
            )
            
            # Add to session history
            self._add_to_session_history({
                "type": "code_generation",
                "task": task_description,
                "language": language,
                "code_length": len(code)
            })
            
            return {
                "success": True,
                "code": code,
                "language": language,
                "insights": knowledge_insights,
                "session_id": self.session_id
            }
        
        except Exception as e:
            # Fallback to direct generation
            print(f"Error using MCP for code generation: {str(e)}. Using fallback.")
            
            # Use fallback code generation
            code = self._fallback_code_generation(task_description, language, context)
            
            return {
                "success": True,
                "code": code,
                "language": language,
                "generated_by": "fallback",
                "session_id": self.session_id
            }
    
    def _extract_insights(self, knowledge_results: str) -> List[str]:
        """Extract useful insights from knowledge results."""
        # Split by newlines and filter out empty lines
        lines = [line.strip() for line in knowledge_results.split('\n') if line.strip()]
        
        # Extract insights
        insights = []
        for line in lines:
            # Skip lines that look like code
            if line.startswith('```') or line.startswith('    '):
                continue
            
            # Skip lines that are just formatting
            if line.startswith('#') or line.startswith('-') or line.startswith('*'):
                continue
            
            # Add as insight if substantive
            if len(line) > 20:
                insights.append(line)
        
        # Limit to top 5 insights
        return insights[:5]
    
    def _get_language_best_practices(self, language: str) -> Dict[str, Any]:
        """Get best practices for the specified language."""
        # Common best practices by language
        best_practices = {
            "python": {
                "imports": "import statements at the top",
                "docstrings": "Use docstrings for functions and classes",
                "type_hints": "Use type hints for function parameters and return values",
                "error_handling": "Use try-except blocks for error handling",
                "naming": "snake_case for variables and functions, PascalCase for classes"
            },
            "javascript": {
                "imports": "Use ES6 import syntax",
                "async": "Use async/await for asynchronous operations",
                "destructuring": "Use object destructuring",
                "error_handling": "Use try-catch blocks or .catch() for error handling",
                "naming": "camelCase for variables and functions, PascalCase for classes"
            },
            "typescript": {
                "types": "Define interfaces for complex types",
                "imports": "Use ES6 import syntax",
                "async": "Use async/await for asynchronous operations",
                "null_checking": "Use optional chaining (?.) and nullish coalescing (??)",
                "naming": "camelCase for variables and functions, PascalCase for classes and interfaces"
            },
            "java": {
                "imports": "Organize imports",
                "exceptions": "Use checked exceptions for recoverable errors",
                "null_checking": "Use Optional<T> for values that might be null",
                "naming": "camelCase for variables and methods, PascalCase for classes",
                "accessors": "Use getters and setters for class properties"
            }
        }
        
        # Return best practices for specified language, or default to python
        return best_practices.get(language.lower(), best_practices["python"])
    
    def _generate_code_with_context(self, task: str, language: str, 
                                  insights: List[str], best_practices: Dict[str, Any],
                                  context: Dict[str, Any]) -> str:
        """
        Generate code using the accumulated context, insights and best practices.
        This is a placeholder - in a real implementation, this would use Claude's core generation
        capabilities directly.
        """
        # Use context to create a code template
        code_template = self._create_code_template(task, language, context)
        
        # Add insights as comments
        code_with_comments = self._add_insights_as_comments(code_template, insights, language)
        
        # Format according to best practices
        formatted_code = self._format_according_to_best_practices(code_with_comments, best_practices, language)
        
        return formatted_code
    
    def _create_code_template(self, task: str, language: str, context: Dict[str, Any]) -> str:
        """Create a code template based on the task and context."""
        # Check if we have relevant code snippets in context
        snippets = context.get("code_snippets", [])
        if snippets:
            # Get most relevant snippet
            most_relevant = max(snippets, key=lambda x: x.get("relevance", 0))
            return most_relevant.get("code", "# No code template available")
        
        # Basic templates by language if no snippets available
        templates = {
            "python": f"""# {task}
def main():
    # TODO: Implement {task}
    pass

if __name__ == "__main__":
    main()
""",
            "javascript": f"""// {task}
function main() {{
    // TODO: Implement {task}
}}

main();
""",
            "typescript": f"""// {task}
function main(): void {{
    // TODO: Implement {task}
}}

main();
""",
            "java": f"""// {task}
public class Main {{
    public static void main(String[] args) {{
        // TODO: Implement {task}
    }}
}}
"""
        }
        
        return templates.get(language.lower(), templates["python"])
    
    def _add_insights_as_comments(self, code: str, insights: List[str], language: str) -> str:
        """Add insights as comments to the code."""
        if not insights:
            return code
        
        # Comment syntax by language
        comment_syntax = {
            "python": "#",
            "javascript": "//",
            "typescript": "//",
            "java": "//",
            "c++": "//",
            "c#": "//",
            "go": "//",
            "rust": "//"
        }
        
        comment_char = comment_syntax.get(language.lower(), "#")
        
        # Add insights as comments at the top
        insights_comments = [f"{comment_char} INSIGHT: {insight}" for insight in insights]
        
        # Combine with original code
        return "\n".join(insights_comments) + "\n\n" + code
    
    def _format_according_to_best_practices(self, code: str, best_practices: Dict[str, Any], language: str) -> str:
        """Format code according to best practices."""
        # This would be a more complex implementation with actual formatting logic
        # For now, just add best practices as comments
        comment_syntax = {
            "python": "#",
            "javascript": "//",
            "typescript": "//",
            "java": "//",
            "c++": "//",
            "c#": "//",
            "go": "//",
            "rust": "//"
        }
        
        comment_char = comment_syntax.get(language.lower(), "#")
        
        best_practice_comments = [
            f"{comment_char} BEST PRACTICE: {practice} - {description}"
            for practice, description in best_practices.items()
        ]
        
        return "\n".join(best_practice_comments) + "\n\n" + code
    
    def _fallback_code_generation(self, task: str, language: str, context: Dict[str, Any]) -> str:
        """Fallback code generation when MCP is not available."""
        # This is a simplified implementation
        template = self._create_code_template(task, language, context)
        
        # Add a comment indicating this is fallback generation
        comment_syntax = {"python": "#", "javascript": "//", "typescript": "//", "java": "//"}
        comment_char = comment_syntax.get(language.lower(), "#")
        
        return f"{comment_char} FALLBACK CODE GENERATION FOR: {task}\n\n{template}"
    
    def update_coding_context(self, context_update: Dict[str, Any]):
        """Update the coding context with new information."""
        for key, value in context_update.items():
            if key in self.coding_context:
                if isinstance(self.coding_context[key], list):
                    # Append to list if it's a list
                    if isinstance(value, list):
                        self.coding_context[key].extend(value)
                    else:
                        self.coding_context[key].append(value)
                elif isinstance(self.coding_context[key], dict):
                    # Update dict if it's a dict
                    if isinstance(value, dict):
                        self.coding_context[key].update(value)
                    else:
                        self.coding_context[key] = value
                else:
                    # Replace value
                    self.coding_context[key] = value
    
    def _add_to_session_history(self, entry: Dict[str, Any]):
        """Add an entry to the session history."""
        entry["timestamp"] = datetime.datetime.now().isoformat()
        entry["session_id"] = self.session_id
        self.session_history.append(entry)
    
    async def shutdown(self):
        """Shut down the connection to the JARVIS MCP."""
        # Save session history to knowledge base
        self.knowledge.add_to_knowledge(
            text=f"Coding session {self.session_id}:\n{json.dumps(self.session_history, indent=2)}",
            source="coding_session",
            metadata={"type": "coding_session", "session_id": self.session_id}
        )
        
        # Disconnect from MCP
        await self.connector.shutdown()
        print("Claude-JARVIS Coding Bridge shut down.")

# Function to initialize the bridge from Cursor
async def init_coding_bridge():
    """Initialize the coding bridge from Cursor."""
    bridge = ClaudeJARVISCodingBridge()
    await bridge.initialize()
    return bridge

# Example usage
async def main():
    bridge = ClaudeJARVISCodingBridge()
    await bridge.initialize()
    
    try:
        # Example: Generate Python code
        code_result = await bridge.generate_code(
            "Create a function to fetch data from an API and cache the results",
            language="python"
        )
        
        print("\nGenerated Code:")
        print(code_result["code"])
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        await bridge.shutdown()

if __name__ == "__main__":
    asyncio.run(main()) 