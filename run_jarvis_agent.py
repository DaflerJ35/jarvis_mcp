import asyncio
import os
import argparse
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from jarvis_mcp_agent import JARVISMCPAgent, JARVISMCPClient

async def run_jarvis_agent(query: str, config_file: str = "jarvis_mcp_config.json", max_steps: int = 30):
    """Run the JARVIS MCP Agent with a query"""
    # Load environment variables
    try:
        load_dotenv()
    except:
        # Continue even if dotenv is not available
        pass
    
    # Create the client
    client = JARVISMCPClient.from_config_file(config_file)
    
    # Create the LLM
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("WARNING: No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")
        return
        
    llm = ChatOpenAI(model="gpt-4o", api_key=api_key)
    
    # Create the agent
    agent = JARVISMCPAgent(llm=llm, client=client, max_steps=max_steps)
    
    print("\nJARVIS MCP Agent starting...")
    print(f"Query: {query}")
    print("=" * 50)
    
    try:
        # Run the agent
        result = await agent.run(query, max_steps=max_steps)
        
        # Print the result
        print("\nFinal Result:")
        if result["success"]:
            print(result["result"])
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        print(f"\nSteps taken: {result['steps_taken']}")
    finally:
        # Close all sessions
        if client.sessions:
            await client.close_all_sessions()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the JARVIS MCP Agent")
    parser.add_argument("query", type=str, help="The query to send to the agent")
    parser.add_argument("--config", type=str, default="jarvis_mcp_config.json", help="Path to the config file")
    parser.add_argument("--max-steps", type=int, default=30, help="Maximum number of steps the agent can take")
    
    args = parser.parse_args()
    
    asyncio.run(run_jarvis_agent(args.query, args.config, args.max_steps)) 