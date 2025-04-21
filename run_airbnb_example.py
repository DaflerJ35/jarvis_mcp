import asyncio
import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from jarvis_mcp_agent import JARVISMCPAgent, JARVISMCPClient

async def run_airbnb_example():
    """Run the Airbnb example using the JARVIS MCP Agent"""
    # Load environment variables
    try:
        load_dotenv()
    except:
        # Continue even if dotenv is not available
        pass
    
    # Get OpenAI API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")
        return
    
    # Create the client
    client = JARVISMCPClient.from_config_file(
        os.path.join(os.path.dirname(__file__), "airbnb_mcp.json")
    )

    # Create the LLM
    llm = ChatOpenAI(model="gpt-4o", api_key=api_key)

    # Create the agent
    agent = JARVISMCPAgent(llm=llm, client=client, max_steps=30)

    print("\nJARVIS MCP Agent starting - Airbnb Example...")
    
    query = (
        "Find me a nice place to stay in Barcelona for 2 adults "
        "for a week in August. I prefer places with a pool and "
        "good reviews. Show me the top 3 options."
    )
    
    print(f"Query: {query}")
    print("=" * 50)

    try:
        # Run the agent
        result = await agent.run(query, max_steps=30)
        
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
    asyncio.run(run_airbnb_example()) 