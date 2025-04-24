#!/usr/bin/env python3
"""
Test script for JARVIS knowledge base functionality
"""

import sys
import os
from pathlib import Path
import argparse
import json
import time

# Add project root to the path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Import the knowledge base
try:
    from src.tools.knowledge_base import KnowledgeBase
    print("Successfully imported Knowledge Base module")
except ImportError as e:
    print(f"Error importing Knowledge Base module: {e}")
    sys.exit(1)

def populate_sample_data(kb):
    """Populate the knowledge base with sample data"""
    print("\nPopulating knowledge base with sample data...")
    
    # Technology category
    kb.store_text(
        "Python is a high-level, interpreted programming language known for its readability and versatility. "
        "It supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
        "Python Programming Language",
        "technology"
    )
    
    kb.store_text(
        "JavaScript is a scripting language that enables interactive web pages. "
        "It is an essential part of web applications and all modern browsers have a dedicated JavaScript engine.",
        "JavaScript",
        "technology"
    )
    
    kb.store({
        "name": "Artificial Intelligence",
        "definition": "The simulation of human intelligence in machines",
        "subfields": ["Machine Learning", "Natural Language Processing", "Computer Vision", "Robotics"],
        "applications": ["Virtual Assistants", "Autonomous Vehicles", "Medical Diagnosis", "Smart Homes"],
        "type": "concept"
    }, "technology", "ai_overview")
    
    # Science category
    kb.store_text(
        "The Theory of Relativity, developed by Albert Einstein, consists of two related theories: Special Relativity (1905) "
        "and General Relativity (1915). It revolutionized our understanding of space, time, and gravity.",
        "Theory of Relativity",
        "science"
    )
    
    kb.store({
        "name": "Periodic Table of Elements",
        "description": "A tabular arrangement of chemical elements ordered by atomic number",
        "categories": ["Metals", "Nonmetals", "Metalloids"],
        "elements_count": 118,
        "type": "reference"
    }, "science", "periodic_table")
    
    # General category
    kb.store_text(
        "JARVIS (Just A Rather Very Intelligent System) is a fictional AI assistant created by Tony Stark in the Marvel Universe. "
        "In real-world applications, JARVIS-inspired systems aim to provide voice-controlled assistance and information access.",
        "About JARVIS",
        "general"
    )
    
    # Personal category (empty by default, user would fill this)
    
    print("Sample data populated successfully")

def list_entries(kb, args):
    """List entries in the knowledge base"""
    entries = kb.list_entries(args.category)
    
    if not entries:
        print(f"No entries found{' in category ' + args.category if args.category else ''}")
        return
    
    print(f"\nFound {len(entries)} entries{' in category ' + args.category if args.category else ''}:")
    for i, entry in enumerate(entries, 1):
        print(f"{i}. {entry['name']} ({entry['category']})")
        print(f"   Modified: {entry['modified']}")
        print(f"   Size: {entry['size']} bytes")
        if args.verbose:
            print(f"   Path: {entry['path']}")
        print()

def search_knowledge(kb, args):
    """Search the knowledge base"""
    if not args.query:
        print("Error: Search query is required")
        return
    
    print(f"\nSearching for '{args.query}'{' in category ' + args.category if args.category else ''}...")
    results = kb.search(args.query, args.category)
    
    if not results:
        print("No matching entries found")
        return
    
    print(f"Found {len(results)} matching entries:")
    for i, result in enumerate(results, 1):
        if 'title' in result:
            print(f"{i}. {result['title']} ({result.get('_category', 'unknown')})")
        else:
            print(f"{i}. {result.get('name', 'Unnamed')} ({result.get('_category', 'unknown')})")
        
        # Show a snippet of content if it's text
        if 'type' in result and result['type'] == 'text' and 'content' in result:
            content = result['content']
            # Show just a snippet
            if len(content) > 100:
                content = content[:100] + "..."
            print(f"   Content: {content}")
        elif args.verbose:
            # Show the structure for non-text entries
            print(f"   Type: {result.get('type', 'unknown')}")
            if 'name' in result:
                print(f"   Name: {result['name']}")
            for key, value in result.items():
                if not key.startswith('_') and key not in ['type', 'name', 'title', 'content']:
                    value_str = str(value)
                    if len(value_str) > 100:
                        value_str = value_str[:100] + "..."
                    print(f"   {key}: {value_str}")
        
        print()

def add_entry(kb, args):
    """Add a new entry to the knowledge base"""
    if args.file:
        # Load from file
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                if args.file.endswith('.json'):
                    # JSON file - structured data
                    data = json.load(f)
                    path = kb.store(data, args.category, args.name)
                else:
                    # Text file
                    text = f.read()
                    title = args.name or os.path.basename(args.file).split('.')[0]
                    path = kb.store_text(text, title, args.category)
                print(f"Added entry from file {args.file} to {path}")
        except Exception as e:
            print(f"Error adding entry from file: {e}")
    
    elif args.text:
        # Direct text input
        title = args.name or f"Manual entry {time.strftime('%Y-%m-%d %H:%M:%S')}"
        path = kb.store_text(args.text, title, args.category)
        print(f"Added text entry '{title}' to {path}")
    
    else:
        print("Error: Either --file or --text must be specified")

def view_entry(kb, args):
    """View a specific entry from the knowledge base"""
    if not args.name:
        print("Error: Entry name is required")
        return
    
    data = kb.retrieve(args.name, args.category)
    
    if not data:
        print(f"Entry '{args.name}' not found{' in category ' + args.category if args.category else ''}")
        return
    
    print(f"\nEntry: {args.name}")
    print(f"Category: {data.get('_metadata', {}).get('category', args.category or 'unknown')}")
    print(f"Timestamp: {data.get('_metadata', {}).get('timestamp', 'unknown')}")
    print("\nContent:")
    
    if 'type' in data and data['type'] == 'text' and 'content' in data:
        # Text content
        print(f"Title: {data.get('title', 'Untitled')}")
        print("-" * 50)
        print(data['content'])
        print("-" * 50)
    else:
        # Structured data
        for key, value in data.items():
            if not key.startswith('_'):
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, indent=2)
                print(f"{key}: {value}")

def delete_entry(kb, args):
    """Delete an entry from the knowledge base"""
    if not args.name:
        print("Error: Entry name is required")
        return
    
    if kb.delete(args.name, args.category):
        print(f"Entry '{args.name}' deleted successfully")
    else:
        print(f"Entry '{args.name}' not found{' in category ' + args.category if args.category else ''}")

def main():
    parser = argparse.ArgumentParser(description="Test JARVIS Knowledge Base")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Initialize parser
    init_parser = subparsers.add_parser("init", help="Initialize knowledge base with sample data")
    
    # List parser
    list_parser = subparsers.add_parser("list", help="List entries in the knowledge base")
    list_parser.add_argument("--category", "-c", help="Category to list entries from")
    list_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed information")
    
    # Search parser
    search_parser = subparsers.add_parser("search", help="Search the knowledge base")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--category", "-c", help="Category to search in")
    search_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed information")
    
    # Add parser
    add_parser = subparsers.add_parser("add", help="Add an entry to the knowledge base")
    add_parser.add_argument("--category", "-c", default="general", help="Category to add entry to")
    add_parser.add_argument("--name", "-n", help="Name for the entry")
    add_parser.add_argument("--file", "-f", help="File to read content from")
    add_parser.add_argument("--text", "-t", help="Text content to add")
    
    # View parser
    view_parser = subparsers.add_parser("view", help="View a specific entry")
    view_parser.add_argument("name", help="Name of the entry to view")
    view_parser.add_argument("--category", "-c", help="Category of the entry")
    
    # Delete parser
    delete_parser = subparsers.add_parser("delete", help="Delete an entry")
    delete_parser.add_argument("name", help="Name of the entry to delete")
    delete_parser.add_argument("--category", "-c", help="Category of the entry")
    
    args = parser.parse_args()
    
    # Create knowledge base instance
    kb = KnowledgeBase()
    print(f"Knowledge base initialized at: {kb.base_path}")
    
    # Execute command
    if args.command == "init":
        populate_sample_data(kb)
    elif args.command == "list":
        list_entries(kb, args)
    elif args.command == "search":
        search_knowledge(kb, args)
    elif args.command == "add":
        add_entry(kb, args)
    elif args.command == "view":
        view_entry(kb, args)
    elif args.command == "delete":
        delete_entry(kb, args)
    else:
        # Print usage information if no command is specified
        parser.print_help()

if __name__ == "__main__":
    main() 