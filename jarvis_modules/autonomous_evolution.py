import os
import re
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
import datetime
import ast
import difflib

class CodeEvolutionSystem:
    """
    Autonomous Code Evolution System that continuously improves codebase quality
    by analyzing patterns, suggesting refactorings, and implementing improvements.
    """
    
    def __init__(self, coding_bridge, knowledge_enhancer):
        self.coding_bridge = coding_bridge
        self.knowledge = knowledge_enhancer
        self.logger = logging.getLogger("JARVIS-Evolution")
        
        # Code quality metrics
        self.metrics = {
            "complexity": {},  # Cyclomatic complexity by file
            "duplication": {},  # Duplicate code percentages
            "test_coverage": {},  # Test coverage by file
            "maintainability": {}  # Maintainability index by file
        }
        
        # Evolution history
        self.evolution_history = []
        
        # Refactoring suggestions queue
        self.refactoring_queue = []
        
        # Settings
        self.settings = {
            "auto_refactor_threshold": 0.8,  # Confidence threshold for automatic refactoring
            "scan_interval_hours": 24,  # How often to scan the codebase
            "ignored_directories": ["venv", "node_modules", ".git"],
            "max_suggestions_per_scan": 5
        }
        
        # Active flag
        self.active = False
    
    async def start(self):
        """Start the autonomous evolution system."""
        self.active = True
        self.logger.info("Starting Autonomous Code Evolution System")
        
        # Start background tasks
        asyncio.create_task(self._periodic_codebase_scan())
        
        # Add system knowledge
        self.knowledge.add_to_knowledge(
            text="The Autonomous Code Evolution System continuously analyzes and improves code quality "
                 "by identifying patterns, suggesting refactorings, and implementing improvements.",
            source="system_documentation",
            metadata={"component": "evolution", "importance": "high"}
        )
        
        return True
    
    async def _periodic_codebase_scan(self):
        """Periodically scan codebase for improvement opportunities."""
        while self.active:
            try:
                self.logger.info("Starting periodic codebase scan")
                
                # Get all Python files in the project
                python_files = await self._get_project_files(".py")
                
                # Analyze each file
                for file_path in python_files:
                    await self._analyze_file(file_path)
                
                # Generate refactoring suggestions
                suggestions = await self._generate_refactoring_suggestions()
                
                # Queue top suggestions
                max_suggestions = self.settings["max_suggestions_per_scan"]
                self.refactoring_queue.extend(suggestions[:max_suggestions])
                
                # Apply high-confidence automatic refactorings
                await self._apply_automatic_refactorings()
                
                self.logger.info(f"Codebase scan complete. Generated {len(suggestions)} suggestions.")
                
                # Store scan in history
                self.evolution_history.append({
                    "timestamp": datetime.datetime.now().isoformat(),
                    "files_analyzed": len(python_files),
                    "suggestions_generated": len(suggestions),
                    "suggestions_queued": min(len(suggestions), max_suggestions)
                })
                
                # Sleep until next scan
                hours = self.settings["scan_interval_hours"]
                self.logger.info(f"Next scan scheduled in {hours} hours")
                await asyncio.sleep(hours * 3600)
            
            except Exception as e:
                self.logger.error(f"Error in periodic codebase scan: {str(e)}")
                await asyncio.sleep(3600)  # Retry in an hour
    
    async def _get_project_files(self, extension):
        """Get all files with the specified extension in the project."""
        project_files = []
        for root, dirs, files in os.walk("."):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.settings["ignored_directories"]]
            
            for file in files:
                if file.endswith(extension):
                    project_files.append(os.path.join(root, file))
        
        return project_files
    
    async def _analyze_file(self, file_path):
        """Analyze a single file for code quality metrics."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Calculate metrics
            complexity = self._calculate_complexity(content)
            duplication = self._detect_duplication(content, file_path)
            maintainability = self._calculate_maintainability(content)
            
            # Update metrics
            self.metrics["complexity"][file_path] = complexity
            self.metrics["duplication"][file_path] = duplication
            self.metrics["maintainability"][file_path] = maintainability
            
            self.logger.debug(f"Analyzed {file_path}: complexity={complexity}, duplication={duplication}%, maintainability={maintainability}")
            
            # Add to knowledge base
            file_metrics = {
                "complexity": complexity,
                "duplication": duplication,
                "maintainability": maintainability,
                "analyzed_at": datetime.datetime.now().isoformat()
            }
            
            self.knowledge.add_to_knowledge(
                text=f"File {file_path} has complexity {complexity}, code duplication {duplication}%, "
                     f"and maintainability index {maintainability}.",
                source="code_analysis",
                metadata={"file": file_path, "metrics": file_metrics, "type": "analysis"}
            )
            
            return file_metrics
        
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {str(e)}")
            return None
    
    def _calculate_complexity(self, code_content):
        """Calculate cyclomatic complexity of code."""
        # Simple approximation using control structures
        control_structures = len(re.findall(r'\b(if|for|while|elif|else|try|except|with)\b', code_content))
        functions = len(re.findall(r'\bdef\s+\w+\s*\(', code_content))
        classes = len(re.findall(r'\bclass\s+\w+\s*(\(|:)', code_content))
        
        # Base complexity of 1 per function/class + control structures
        base_complexity = max(1, functions + classes)
        return base_complexity + control_structures
    
    def _detect_duplication(self, code_content, file_path):
        """Detect code duplication percentage."""
        # Simple line-based duplication detection
        lines = code_content.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
        
        if not non_empty_lines:
            return 0
        
        # Count duplicate lines (very simple approach)
        unique_lines = set(non_empty_lines)
        duplication_percentage = 100 * (1 - len(unique_lines) / len(non_empty_lines))
        
        return round(duplication_percentage, 2)
    
    def _calculate_maintainability(self, code_content):
        """Calculate maintainability index for code."""
        # Simplified maintainability index calculation
        lines = code_content.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
        
        if not non_empty_lines:
            return 100  # Perfect maintainability for empty files
        
        # Factors that reduce maintainability
        complexity = self._calculate_complexity(code_content)
        avg_line_length = sum(len(line) for line in non_empty_lines) / len(non_empty_lines)
        comment_ratio = len([line for line in lines if line.strip().startswith('#')]) / max(1, len(lines))
        
        # Calculate maintainability index (0-100, higher is better)
        maintainability = 100
        maintainability -= min(50, complexity * 0.5)  # Higher complexity reduces maintainability
        maintainability -= min(20, (avg_line_length - 50) * 0.2) if avg_line_length > 50 else 0  # Long lines reduce maintainability
        maintainability += min(20, comment_ratio * 50)  # Comments improve maintainability
        
        return max(0, min(100, round(maintainability, 2)))
    
    async def _generate_refactoring_suggestions(self):
        """Generate refactoring suggestions based on code metrics."""
        suggestions = []
        
        # Look for high complexity files
        for file_path, complexity in sorted(self.metrics["complexity"].items(), key=lambda x: x[1], reverse=True):
            if complexity > 20:  # High complexity threshold
                suggestion = {
                    "file": file_path,
                    "type": "complexity",
                    "confidence": min(1.0, complexity / 40),  # Higher complexity = higher confidence
                    "description": f"High cyclomatic complexity ({complexity}). Consider refactoring into smaller functions.",
                    "severity": "high" if complexity > 30 else "medium"
                }
                suggestions.append(suggestion)
        
        # Look for high duplication files
        for file_path, duplication in sorted(self.metrics["duplication"].items(), key=lambda x: x[1], reverse=True):
            if duplication > 15:  # High duplication threshold
                suggestion = {
                    "file": file_path,
                    "type": "duplication",
                    "confidence": min(1.0, duplication / 30),
                    "description": f"High code duplication ({duplication}%). Consider extracting common functionality.",
                    "severity": "high" if duplication > 25 else "medium"
                }
                suggestions.append(suggestion)
        
        # Look for low maintainability files
        for file_path, maintainability in sorted(self.metrics["maintainability"].items(), key=lambda x: x[1]):
            if maintainability < 50:  # Low maintainability threshold
                suggestion = {
                    "file": file_path,
                    "type": "maintainability",
                    "confidence": min(1.0, (50 - maintainability) / 50),
                    "description": f"Low maintainability index ({maintainability}). Consider restructuring and adding documentation.",
                    "severity": "high" if maintainability < 30 else "medium"
                }
                suggestions.append(suggestion)
        
        # Add suggestions to knowledge base
        if suggestions:
            self.knowledge.add_to_knowledge(
                text=f"Generated {len(suggestions)} refactoring suggestions. " + 
                     f"Top suggestion: {suggestions[0]['description']} for file {suggestions[0]['file']}",
                source="code_evolution",
                metadata={"suggestions": suggestions[:3], "type": "refactoring"}
            )
        
        return suggestions
    
    async def _apply_automatic_refactorings(self):
        """Apply high-confidence automatic refactorings."""
        applied_count = 0
        threshold = self.settings["auto_refactor_threshold"]
        
        for suggestion in list(self.refactoring_queue):
            if suggestion["confidence"] >= threshold:
                success = await self._apply_refactoring(suggestion)
                if success:
                    applied_count += 1
                    self.refactoring_queue.remove(suggestion)
                    
                    # Log the applied refactoring
                    self.logger.info(f"Applied automatic refactoring: {suggestion['description']} to {suggestion['file']}")
                    
                    # Add to knowledge base
                    self.knowledge.add_to_knowledge(
                        text=f"Applied refactoring to {suggestion['file']}: {suggestion['description']}",
                        source="code_evolution",
                        metadata={"suggestion": suggestion, "type": "applied_refactoring"}
                    )
        
        if applied_count > 0:
            self.logger.info(f"Applied {applied_count} automatic refactorings")
        
        return applied_count
    
    async def _apply_refactoring(self, suggestion):
        """Apply a specific refactoring suggestion."""
        try:
            file_path = suggestion["file"]
            refactoring_type = suggestion["type"]
            
            with open(file_path, "r", encoding="utf-8") as f:
                original_content = f.read()
            
            # Apply appropriate refactoring based on type
            if refactoring_type == "complexity":
                new_content = await self._refactor_complexity(original_content, file_path)
            elif refactoring_type == "duplication":
                new_content = await self._refactor_duplication(original_content, file_path)
            elif refactoring_type == "maintainability":
                new_content = await self._refactor_maintainability(original_content, file_path)
            else:
                self.logger.warning(f"Unknown refactoring type: {refactoring_type}")
                return False
            
            # Check if refactoring made changes
            if new_content == original_content:
                self.logger.info(f"Refactoring didn't change file: {file_path}")
                return False
            
            # Backup original file
            backup_path = f"{file_path}.bak"
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(original_content)
            
            # Write refactored content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            self.logger.info(f"Successfully applied refactoring to {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error applying refactoring to {suggestion['file']}: {str(e)}")
            return False
    
    async def _refactor_complexity(self, content, file_path):
        """Refactor code to reduce complexity."""
        try:
            # Use the coding bridge to generate refactored code
            result = await self.coding_bridge.generate_code(
                f"Refactor this Python code to reduce complexity by breaking down complex functions:\n{content}",
                "python"
            )
            
            if result and "code" in result:
                return result["code"]
            
            return content  # Return original if refactoring failed
        except Exception as e:
            self.logger.error(f"Error in complexity refactoring: {str(e)}")
            return content
    
    async def _refactor_duplication(self, content, file_path):
        """Refactor code to reduce duplication."""
        try:
            # Use the coding bridge to generate refactored code
            result = await self.coding_bridge.generate_code(
                f"Refactor this Python code to reduce duplication by extracting common functionality:\n{content}",
                "python"
            )
            
            if result and "code" in result:
                return result["code"]
            
            return content  # Return original if refactoring failed
        except Exception as e:
            self.logger.error(f"Error in duplication refactoring: {str(e)}")
            return content
    
    async def _refactor_maintainability(self, content, file_path):
        """Refactor code to improve maintainability."""
        try:
            # Use the coding bridge to generate refactored code
            result = await self.coding_bridge.generate_code(
                f"Refactor this Python code to improve maintainability by adding documentation, "
                f"improving structure, and using better naming:\n{content}",
                "python"
            )
            
            if result and "code" in result:
                return result["code"]
            
            return content  # Return original if refactoring failed
        except Exception as e:
            self.logger.error(f"Error in maintainability refactoring: {str(e)}")
            return content
    
    async def analyze_code(self, code, language="python") -> Dict[str, Any]:
        """Analyze a piece of code for quality metrics."""
        if language.lower() != "python":
            return {"error": f"Code analysis for {language} is not yet supported"}
        
        try:
            # Calculate metrics
            complexity = self._calculate_complexity(code)
            duplication = self._detect_duplication(code, "snippet")
            maintainability = self._calculate_maintainability(code)
            
            # Generate improvement suggestions
            suggestions = []
            if complexity > 10:
                suggestions.append({
                    "type": "complexity",
                    "message": f"Reduce complexity by breaking down functions. Current complexity: {complexity}"
                })
            
            if duplication > 10:
                suggestions.append({
                    "type": "duplication",
                    "message": f"Extract common code to reduce {duplication}% duplication"
                })
            
            if maintainability < 60:
                suggestions.append({
                    "type": "maintainability",
                    "message": f"Improve maintainability (currently {maintainability}/100) by adding documentation and improving structure"
                })
            
            return {
                "metrics": {
                    "complexity": complexity,
                    "duplication": duplication,
                    "maintainability": maintainability
                },
                "suggestions": suggestions,
                "overall_quality": self._calculate_overall_quality(complexity, duplication, maintainability)
            }
        
        except Exception as e:
            self.logger.error(f"Error analyzing code: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_overall_quality(self, complexity, duplication, maintainability):
        """Calculate overall code quality score (0-100)."""
        # Invert complexity (higher complexity = lower quality)
        max_expected_complexity = 40
        complexity_score = max(0, 100 - (complexity / max_expected_complexity * 100))
        
        # Invert duplication (higher duplication = lower quality)
        duplication_score = max(0, 100 - duplication)
        
        # Maintainability is already 0-100
        maintainability_score = maintainability
        
        # Weight the scores
        overall_score = (complexity_score * 0.4 + duplication_score * 0.3 + maintainability_score * 0.3)
        
        return round(overall_score, 2)
    
    async def evolve_code(self, code, language="python", goals=None) -> Dict[str, Any]:
        """Evolve a piece of code to improve it based on specified goals."""
        if not goals:
            goals = ["readability", "maintainability", "performance"]
        
        try:
            # First analyze the code
            analysis = await self.analyze_code(code, language)
            
            if "error" in analysis:
                return analysis
            
            # Generate appropriate prompt based on goals and analysis
            prompt = f"Improve this {language} code"
            
            for goal in goals:
                if goal == "readability":
                    prompt += ", making it more readable"
                elif goal == "maintainability":
                    prompt += ", improving its maintainability"
                elif goal == "performance":
                    prompt += ", optimizing for performance"
                elif goal == "security":
                    prompt += ", enhancing security"
                elif goal == "testing":
                    prompt += ", adding proper tests"
            
            # Add specific improvement suggestions based on analysis
            if "suggestions" in analysis and analysis["suggestions"]:
                prompt += ". Specifically:\n"
                for suggestion in analysis["suggestions"]:
                    prompt += f"- {suggestion['message']}\n"
            
            prompt += f"\nCode to improve:\n{code}"
            
            # Use the coding bridge to generate evolved code
            result = await self.coding_bridge.generate_code(prompt, language)
            
            if not result or "code" not in result:
                return {"error": "Failed to evolve code"}
            
            evolved_code = result["code"]
            
            # Analyze the evolved code
            evolved_analysis = await self.analyze_code(evolved_code, language)
            
            # Calculate diff
            diff = list(difflib.unified_diff(
                code.splitlines(),
                evolved_code.splitlines(),
                lineterm='',
                fromfile='original',
                tofile='evolved'
            ))
            
            # Add to knowledge base
            self.knowledge.add_to_knowledge(
                text=f"Evolved code with goals: {', '.join(goals)}. "
                     f"Improved quality from {analysis.get('overall_quality', 'unknown')} "
                     f"to {evolved_analysis.get('overall_quality', 'unknown')}.",
                source="code_evolution",
                metadata={
                    "original_code": code[:500] + "..." if len(code) > 500 else code,
                    "evolved_code": evolved_code[:500] + "..." if len(evolved_code) > 500 else evolved_code,
                    "goals": goals,
                    "improvement": evolved_analysis.get('overall_quality', 0) - analysis.get('overall_quality', 0)
                }
            )
            
            return {
                "original_code": code,
                "evolved_code": evolved_code,
                "diff": diff,
                "original_analysis": analysis,
                "evolved_analysis": evolved_analysis,
                "improvement": evolved_analysis.get('overall_quality', 0) - analysis.get('overall_quality', 0)
            }
        
        except Exception as e:
            self.logger.error(f"Error evolving code: {str(e)}")
            return {"error": str(e)}
    
    async def shutdown(self):
        """Shut down the autonomous evolution system."""
        self.logger.info("Shutting down Autonomous Code Evolution System")
        self.active = False
        return True 