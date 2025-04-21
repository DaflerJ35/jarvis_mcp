import os
import json
import aiohttp
import asyncio
import datetime
from typing import Dict, Any, List, Optional, Tuple
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from bs4 import BeautifulSoup
import requests

class JARVISKnowledgeEnhancer:
    """Advanced knowledge enhancement module for J.A.R.V.I.S. MCP."""
    
    def __init__(self, knowledge_dir: str = "knowledge_base"):
        # Create knowledge directory if it doesn't exist
        self.knowledge_dir = knowledge_dir
        os.makedirs(self.knowledge_dir, exist_ok=True)
        
        # Initialize vector database for semantic search
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.embeddings = []
        self.documents = []
        
        # Initialize sentence transformer for embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load existing knowledge if available
        self._load_knowledge()
        
        # Memory for conversation history
        self.memory = []
        
        # API keys (should be moved to secure environment variables)
        self.serpapi_key = os.environ.get("SERPAPI_KEY", "YOUR_SERPAPI_KEY") 
        self.news_api_key = os.environ.get("NEWS_API_KEY", "YOUR_NEWS_API_KEY")
        
        print(f"J.A.R.V.I.S. Knowledge Enhancer initialized with {len(self.documents)} documents")
    
    def _load_knowledge(self):
        """Load existing knowledge from disk."""
        embeddings_file = os.path.join(self.knowledge_dir, "embeddings.npy")
        documents_file = os.path.join(self.knowledge_dir, "documents.json")
        
        if os.path.exists(embeddings_file) and os.path.exists(documents_file):
            try:
                # Load embeddings
                embeddings = np.load(embeddings_file)
                self.embeddings = embeddings.tolist()
                
                # Rebuild the index
                self.index = faiss.IndexFlatL2(self.embedding_dim)
                if len(embeddings) > 0:
                    self.index.add(embeddings)
                
                # Load documents
                with open(documents_file, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
                
                print(f"Loaded {len(self.documents)} documents from knowledge base")
            except Exception as e:
                print(f"Error loading knowledge base: {str(e)}")
                # Initialize empty if loading fails
                self.embeddings = []
                self.documents = []
                self.index = faiss.IndexFlatL2(self.embedding_dim)
    
    def _save_knowledge(self):
        """Save knowledge to disk."""
        embeddings_file = os.path.join(self.knowledge_dir, "embeddings.npy")
        documents_file = os.path.join(self.knowledge_dir, "documents.json")
        
        try:
            # Save embeddings
            embeddings_array = np.array(self.embeddings, dtype=np.float32)
            np.save(embeddings_file, embeddings_array)
            
            # Save documents
            with open(documents_file, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
            
            print(f"Saved {len(self.documents)} documents to knowledge base")
        except Exception as e:
            print(f"Error saving knowledge base: {str(e)}")
    
    def add_to_knowledge(self, text: str, source: str, metadata: Dict[str, Any] = None):
        """Add new knowledge to the vector database."""
        if not text.strip():
            return False
        
        # Create embedding
        embedding = self.model.encode([text])[0]
        
        # Add to index
        self.index.add(np.array([embedding], dtype=np.float32))
        
        # Add to documents
        document = {
            "text": text,
            "source": source,
            "metadata": metadata or {},
            "added_at": datetime.datetime.now().isoformat()
        }
        self.documents.append(document)
        self.embeddings.append(embedding.tolist())
        
        # Save updated knowledge
        self._save_knowledge()
        
        return True
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base using semantic similarity."""
        if not self.documents:
            return []
        
        # Create query embedding
        query_embedding = self.model.encode([query])[0]
        
        # Search
        distances, indices = self.index.search(np.array([query_embedding], dtype=np.float32), min(top_k, len(self.documents)))
        
        # Get results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents) and idx >= 0:
                result = self.documents[idx].copy()
                result["score"] = float(1.0 / (1.0 + distances[0][i]))  # Convert distance to similarity score
                results.append(result)
        
        return results
    
    async def web_search(self, query: str) -> Dict[str, Any]:
        """Perform a web search using SerpAPI."""
        if not self.serpapi_key or self.serpapi_key == "YOUR_SERPAPI_KEY":
            return {"error": "SerpAPI key not configured"}
        
        async with aiohttp.ClientSession() as session:
            try:
                # Call SerpAPI
                params = {
                    "api_key": self.serpapi_key,
                    "q": query,
                    "engine": "google"
                }
                
                async with session.get("https://serpapi.com/search", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract organic results
                        results = []
                        if "organic_results" in data:
                            for result in data["organic_results"][:5]:  # Get top 5 results
                                results.append({
                                    "title": result.get("title", ""),
                                    "link": result.get("link", ""),
                                    "snippet": result.get("snippet", "")
                                })
                                
                                # Add to knowledge base
                                self.add_to_knowledge(
                                    text=f"{result.get('title', '')}\n{result.get('snippet', '')}",
                                    source=result.get('link', ''),
                                    metadata={"query": query, "type": "web_search"}
                                )
                        
                        return {
                            "query": query,
                            "results": results
                        }
                    else:
                        return {"error": f"Search API error: {response.status}"}
            except Exception as e:
                return {"error": f"Error in web search: {str(e)}"}
    
    async def fetch_news(self, topic: str = None) -> Dict[str, Any]:
        """Fetch the latest news on a given topic."""
        if not self.news_api_key or self.news_api_key == "YOUR_NEWS_API_KEY":
            return {"error": "News API key not configured"}
        
        async with aiohttp.ClientSession() as session:
            try:
                # Build API URL
                url = "https://newsapi.org/v2/top-headlines"
                params = {
                    "apiKey": self.news_api_key,
                    "language": "en",
                }
                
                if topic:
                    params["q"] = topic
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract articles
                        articles = []
                        if "articles" in data:
                            for article in data["articles"][:5]:  # Get top 5 articles
                                articles.append({
                                    "title": article.get("title", ""),
                                    "source": article.get("source", {}).get("name", ""),
                                    "url": article.get("url", ""),
                                    "published_at": article.get("publishedAt", ""),
                                    "description": article.get("description", "")
                                })
                                
                                # Add to knowledge base
                                self.add_to_knowledge(
                                    text=f"{article.get('title', '')}\n{article.get('description', '')}",
                                    source=article.get('url', ''),
                                    metadata={"topic": topic, "type": "news"}
                                )
                        
                        return {
                            "topic": topic,
                            "articles": articles
                        }
                    else:
                        return {"error": f"News API error: {response.status}"}
            except Exception as e:
                return {"error": f"Error fetching news: {str(e)}"}
    
    def add_to_memory(self, message: Dict[str, Any]):
        """Add a message to the conversation memory."""
        # Add timestamp
        message["timestamp"] = datetime.datetime.now().isoformat()
        
        # Add to memory
        self.memory.append(message)
        
        # Limit memory size (keep last 100 messages)
        if len(self.memory) > 100:
            self.memory = self.memory[-100:]
    
    def get_memory(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages from memory."""
        return self.memory[-limit:] if self.memory else []
    
    def clear_memory(self):
        """Clear conversation memory."""
        self.memory = []
    
    async def fetch_webpage_content(self, url: str) -> Dict[str, Any]:
        """Fetch content from a webpage and add to knowledge base."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.title.string if soup.title else "No title"
            
            # Extract main content (simplified approach)
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text
            text = soup.get_text(separator='\n')
            
            # Break into lines and remove leading and trailing space
            lines = (line.strip() for line in text.splitlines())
            
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            
            # Drop blank lines
            content = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Truncate to avoid very large texts
            content = content[:5000] + "..." if len(content) > 5000 else content
            
            # Add to knowledge base
            self.add_to_knowledge(
                text=f"{title}\n\n{content}",
                source=url,
                metadata={"type": "webpage"}
            )
            
            return {
                "url": url,
                "title": title,
                "content": content,
                "success": True
            }
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "success": False
            }
    
    async def learn_from_youtube(self, video_id: str) -> Dict[str, Any]:
        """Learn from a YouTube video by fetching its metadata and transcript."""
        try:
            # Fetch video metadata
            api_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=snippet&key={os.environ.get('YOUTUBE_API_KEY', 'YOUR_YOUTUBE_API_KEY')}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status != 200:
                        return {"error": f"YouTube API error: {response.status}"}
                    
                    data = await response.json()
                    
                    if not data.get("items"):
                        return {"error": "Video not found"}
                    
                    video_data = data["items"][0]["snippet"]
                    title = video_data.get("title", "No title")
                    description = video_data.get("description", "No description")
                    
                    # Add video metadata to knowledge base
                    self.add_to_knowledge(
                        text=f"YouTube Video: {title}\n\nDescription: {description}",
                        source=f"https://www.youtube.com/watch?v={video_id}",
                        metadata={"type": "youtube_video"}
                    )
                    
                    return {
                        "video_id": video_id,
                        "title": title,
                        "description": description,
                        "source": f"https://www.youtube.com/watch?v={video_id}",
                        "success": True
                    }
        except Exception as e:
            return {
                "video_id": video_id,
                "error": str(e),
                "success": False
            }
    
    def backup_knowledge(self) -> bool:
        """Backup the knowledge base."""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(self.knowledge_dir, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup embeddings
            embeddings_file = os.path.join(self.knowledge_dir, "embeddings.npy")
            backup_embeddings = os.path.join(backup_dir, f"embeddings_{timestamp}.npy")
            
            # Backup documents
            documents_file = os.path.join(self.knowledge_dir, "documents.json")
            backup_documents = os.path.join(backup_dir, f"documents_{timestamp}.json")
            
            if os.path.exists(embeddings_file):
                embeddings_array = np.load(embeddings_file)
                np.save(backup_embeddings, embeddings_array)
            
            if os.path.exists(documents_file):
                with open(documents_file, "r", encoding="utf-8") as f_in:
                    with open(backup_documents, "w", encoding="utf-8") as f_out:
                        f_out.write(f_in.read())
            
            print(f"Knowledge base backed up to {backup_dir}")
            return True
        except Exception as e:
            print(f"Error backing up knowledge base: {str(e)}")
            return False

# Example usage as standalone module
async def main():
    # Create knowledge enhancer
    enhancer = JARVISKnowledgeEnhancer()
    
    # Add some knowledge
    enhancer.add_to_knowledge(
        "J.A.R.V.I.S. is a sophisticated AI assistant inspired by the fictional AI in Iron Man.",
        "manual_entry",
        {"importance": "high"}
    )
    
    # Search the knowledge base
    results = enhancer.semantic_search("What is JARVIS?")
    print("\nSemantic Search Results:")
    for result in results:
        print(f"- {result['text'][:100]}... (Score: {result['score']:.2f})")
    
    # Demonstrate web search
    if enhancer.serpapi_key != "YOUR_SERPAPI_KEY":
        print("\nPerforming web search...")
        web_results = await enhancer.web_search("latest AI technology developments")
        if "error" not in web_results:
            print(f"Found {len(web_results.get('results', []))} results")
            for result in web_results.get("results", []):
                print(f"- {result.get('title')}")
    
    # Learn from YouTube video
    print("\nLearning from YouTube video...")
    video_result = await enhancer.learn_from_youtube("_qH0ArjwBpE")  # Example video ID
    if video_result.get("success"):
        print(f"Learned about: {video_result.get('title')}")
    else:
        print(f"Error: {video_result.get('error')}")
    
    # Backup knowledge
    enhancer.backup_knowledge()

if __name__ == "__main__":
    asyncio.run(main()) 