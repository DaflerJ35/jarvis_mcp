#!/usr/bin/env python3
"""
JARVIS Knowledge Base Manager

This module provides functionality to store, retrieve, and search for information
in the JARVIS knowledge base.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import datetime
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("JarvisKnowledgeBase")

class KnowledgeBase:
    """Knowledge base component for JARVIS."""
    
    def __init__(self, base_path: Union[str, Path] = None):
        """
        Initialize the knowledge base.
        
        Args:
            base_path: Base path to the knowledge base directory
        """
        if base_path is None:
            # Default to a 'knowledge_base' directory in the project root
            self.base_path = Path(__file__).resolve().parents[2] / "knowledge_base"
        else:
            self.base_path = Path(base_path)
        
        # Create the knowledge base directory if it doesn't exist
        self._ensure_directories()
        
        logger.info(f"Knowledge base initialized at: {self.base_path}")
    
    def _ensure_directories(self):
        """Ensure that the knowledge base directories exist."""
        # Main directory
        os.makedirs(self.base_path, exist_ok=True)
        
        # Category subdirectories
        categories = ["general", "science", "technology", "personal"]
        for category in categories:
            os.makedirs(self.base_path / category, exist_ok=True)
    
    def store(self, data: Dict[str, Any], category: str = "general", name: str = None) -> str:
        """
        Store data in the knowledge base.
        
        Args:
            data: Data to store (must be JSON serializable)
            category: Category to store the data in
            name: Name for the file (if None, a timestamp will be used)
            
        Returns:
            str: Path to the stored file
        """
        # Validate category
        category_path = self.base_path / category
        if not category_path.exists():
            os.makedirs(category_path, exist_ok=True)
        
        # Generate filename if not provided
        if name is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"entry_{timestamp}"
        
        # Add .json extension if not present
        if not name.endswith('.json'):
            name += '.json'
        
        # Add metadata
        data['_metadata'] = {
            'timestamp': datetime.datetime.now().isoformat(),
            'category': category
        }
        
        # Write to file
        file_path = category_path / name
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Stored knowledge in {file_path}")
        return str(file_path)
    
    def retrieve(self, name: str, category: str = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from the knowledge base.
        
        Args:
            name: Name of the file to retrieve
            category: Category to look in (if None, will search all categories)
            
        Returns:
            dict: Retrieved data or None if not found
        """
        # Add .json extension if not present
        if not name.endswith('.json'):
            name += '.json'
        
        # If category is specified, look only there
        if category:
            file_path = self.base_path / category / name
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        
        # Otherwise search in all categories
        for category_dir in self.base_path.iterdir():
            if category_dir.is_dir():
                file_path = category_dir / name
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
        
        return None
    
    def search(self, query: str, category: str = None) -> List[Dict[str, Any]]:
        """
        Search for data in the knowledge base.
        
        Args:
            query: Search query
            category: Category to search in (if None, will search all categories)
            
        Returns:
            list: List of matching entries
        """
        results = []
        
        # Determine which categories to search
        categories = [category] if category else [d.name for d in self.base_path.iterdir() if d.is_dir()]
        
        # Simple search implementation (can be enhanced with better algorithms)
        query_lower = query.lower()
        for category_name in categories:
            category_path = self.base_path / category_name
            if not category_path.is_dir():
                continue
                
            for file_path in category_path.glob('*.json'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # Check if query appears in the content
                    content_str = json.dumps(data, ensure_ascii=False).lower()
                    if query_lower in content_str:
                        # Add filename and category info
                        data['_filename'] = file_path.name
                        data['_category'] = category_name
                        results.append(data)
                except Exception as e:
                    logger.error(f"Error reading {file_path}: {e}")
        
        return results
    
    def list_entries(self, category: str = None) -> List[Dict[str, str]]:
        """
        List all entries in the knowledge base.
        
        Args:
            category: Category to list (if None, will list all categories)
            
        Returns:
            list: List of entries with metadata
        """
        entries = []
        
        # Determine which categories to list
        categories = [category] if category else [d.name for d in self.base_path.iterdir() if d.is_dir()]
        
        for category_name in categories:
            category_path = self.base_path / category_name
            if not category_path.is_dir():
                continue
                
            for file_path in category_path.glob('*.json'):
                try:
                    # Get basic info without loading entire file
                    entry = {
                        'name': file_path.stem,
                        'category': category_name,
                        'path': str(file_path),
                        'size': file_path.stat().st_size,
                        'modified': datetime.datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat()
                    }
                    entries.append(entry)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
        
        # Sort by modified date, newest first
        entries.sort(key=lambda x: x['modified'], reverse=True)
        return entries
    
    def delete(self, name: str, category: str = None) -> bool:
        """
        Delete an entry from the knowledge base.
        
        Args:
            name: Name of the file to delete
            category: Category to look in (if None, will search all categories)
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        # Add .json extension if not present
        if not name.endswith('.json'):
            name += '.json'
        
        # If category is specified, look only there
        if category:
            file_path = self.base_path / category / name
            if file_path.exists():
                os.remove(file_path)
                logger.info(f"Deleted {file_path}")
                return True
            return False
        
        # Otherwise search in all categories
        for category_dir in self.base_path.iterdir():
            if category_dir.is_dir():
                file_path = category_dir / name
                if file_path.exists():
                    os.remove(file_path)
                    logger.info(f"Deleted {file_path}")
                    return True
        
        return False
    
    def store_text(self, text: str, title: str = None, category: str = "general") -> str:
        """
        Store text in the knowledge base.
        
        Args:
            text: Text to store
            title: Title for the text (if None, a timestamp will be used)
            category: Category to store the text in
            
        Returns:
            str: Path to the stored file
        """
        # Create a JSON object from the text
        data = {
            'title': title or f"Text entry {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'content': text,
            'type': 'text'
        }
        
        # Generate filename if not provided
        if title:
            # Create a filename-safe version of the title
            name = re.sub(r'[^\w\-_\. ]', '_', title).strip()
            name = re.sub(r'\s+', '_', name)
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"text_{timestamp}"
        
        return self.store(data, category, name)
    
    def get_text(self, title: str, category: str = None) -> Optional[str]:
        """
        Get text from the knowledge base.
        
        Args:
            title: Title of the text to retrieve
            category: Category to look in (if None, will search all categories)
            
        Returns:
            str: Retrieved text or None if not found
        """
        # Create a filename-safe version of the title
        name = re.sub(r'[^\w\-_\. ]', '_', title).strip()
        name = re.sub(r'\s+', '_', name)
        
        data = self.retrieve(name, category)
        if data and 'content' in data:
            return data['content']
        return None
    
    def search_text(self, query: str, category: str = None) -> List[Dict[str, str]]:
        """
        Search for text in the knowledge base.
        
        Args:
            query: Search query
            category: Category to search in (if None, will search all categories)
            
        Returns:
            list: List of matching text entries
        """
        results = []
        all_results = self.search(query, category)
        
        for entry in all_results:
            if 'type' in entry and entry['type'] == 'text' and 'content' in entry:
                results.append({
                    'title': entry.get('title', 'Untitled'),
                    'content': entry['content'],
                    'category': entry.get('_category', 'unknown'),
                    'filename': entry.get('_filename', 'unknown')
                })
        
        return results


# For testing
if __name__ == "__main__":
    # Test the knowledge base
    kb = KnowledgeBase()
    
    # Store some test data
    kb.store_text("Python is a programming language.", "Python Info", "technology")
    kb.store_text("The Earth orbits the Sun.", "Solar System", "science")
    
    # Store some structured data
    kb.store({
        "name": "Albert Einstein",
        "birth_year": 1879,
        "theories": ["Relativity", "Photoelectric effect"],
        "type": "person"
    }, "science", "einstein")
    
    # List all entries
    print("\nAll entries:")
    entries = kb.list_entries()
    for entry in entries:
        print(f"- {entry['name']} ({entry['category']})")
    
    # Search for entries
    print("\nSearch results for 'sun':")
    results = kb.search("sun")
    for result in results:
        print(f"- {result.get('title', 'Untitled')} ({result.get('_category', 'unknown')})")
    
    # Retrieve a specific text
    print("\nRetrieving 'Solar System':")
    text = kb.get_text("Solar System")
    print(text) 