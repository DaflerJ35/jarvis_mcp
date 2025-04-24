# JARVIS Knowledge Base

This directory contains the knowledge base for JARVIS, storing various types of information that JARVIS can access, search, and retrieve during operation.

## Structure

The knowledge base is organized into categories:

- **general/** - General knowledge, facts, and information about JARVIS itself
- **science/** - Scientific information, theories, formulas, and facts
- **technology/** - Information about programming, devices, software, and technological concepts
- **personal/** - Personal information, preferences, reminders, and user-specific data

Each category contains JSON files that store either structured data or text-based information.

## File Formats

Files in the knowledge base are stored in JSON format and follow these general structures:

### Text Entries

```json
{
  "title": "Title of the entry",
  "content": "The main text content goes here...",
  "type": "text",
  "_metadata": {
    "timestamp": "2023-04-23T22:19:45.123456",
    "category": "general"
  }
}
```

### Structured Data

```json
{
  "name": "Topic Name",
  "description": "Description of the topic",
  "type": "concept|person|system|reference",
  "additional_fields": "Depend on the entry type...",
  "_metadata": {
    "timestamp": "2023-04-23T22:19:45.123456",
    "category": "technology"
  }
}
```

## Using the Knowledge Base

### Command Line Tool

You can manage the knowledge base using the `test_knowledge_base.py` script:

```bash
# Initialize with sample data
python test_knowledge_base.py init

# List entries
python test_knowledge_base.py list
python test_knowledge_base.py list --category science

# Search for information
python test_knowledge_base.py search "python"
python test_knowledge_base.py search "solar system" --category science

# Add a new text entry
python test_knowledge_base.py add --text "This is some information to remember" --name "Important Note"

# Add from a file
python test_knowledge_base.py add --file data.json --category technology

# View a specific entry
python test_knowledge_base.py view "Important Note"

# Delete an entry
python test_knowledge_base.py delete "Entry Name"
```

### Programmatic Access

You can also access the knowledge base programmatically:

```python
from src.tools.knowledge_base import KnowledgeBase

# Initialize
kb = KnowledgeBase()

# Store text
kb.store_text("Python is a programming language.", "Python Info", "technology")

# Store structured data
kb.store({
    "name": "Albert Einstein",
    "birth_year": 1879,
    "theories": ["Relativity", "Photoelectric effect"],
    "type": "person"
}, "science", "einstein")

# Search
results = kb.search("python")
for result in results:
    print(result.get('title', 'Untitled'))

# Retrieve specific entry
data = kb.retrieve("Python_Info", "technology")
```

### Voice Integration

The knowledge base integrates with JARVIS voice recognition and synthesis through the Knowledge Integration module:

- Say "Jarvis, tell me about Python" to retrieve information
- Say "Jarvis, remember that my favorite color is blue" to store personal information
- Say "Jarvis, what is the solar system" to query scientific knowledge

## Adding New Knowledge

You can add new information to the knowledge base in several ways:

1. Use the command-line tool as described above
2. Directly create JSON files in the appropriate category directories
3. Use voice commands with JARVIS
4. Use the KnowledgeBase class in your Python code

For structured data, it's recommended to follow existing patterns and include at least the following fields:
- `name` - The name of the entity or concept
- `type` - The type of information (e.g., "person", "concept", "system")
- `description` - A brief description of the entity

## Extending the Knowledge Base

To add new categories, simply create a new directory in the knowledge base and update the code in `src/tools/knowledge_base.py` to include the new category in the `_ensure_directories` method.

For more advanced search capabilities, consider implementing a vector-based search using embeddings and a vector database. 