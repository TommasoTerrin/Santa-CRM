import sys
from pathlib import Path
import os

# Add current dir to sys.path
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent))

print(f"📂 Added paths: {current_dir}, {current_dir.parent}")

try:
    from agent import metabase_mcp
    print("✅ Successfully imported metabase_mcp from agent.py")
except ImportError as e:
    print(f"❌ Failed to import agent: {e}")
    sys.exit(1)

def test_connection():
    print("🔌 Testing MCP Connection (may take a moment to spin up container)...")
    try:
        # The list_tools method is synchronous based on usage in agent.py
        tools = metabase_mcp.list_tools()
        
        print(f"\n✅ Connection Successful! Found {len(tools)} tools:")
        for tool in tools:
            # Assuming tool object structure, adjusting if print looks weird
            name = getattr(tool, 'name', None)
            if name is None:
                 # fallback if it's a pydantic model or dict
                 name = tool.get('name') if isinstance(tool, dict) else str(tool)
            
            print(f" - {name}")
            
    except Exception as e:
        print(f"\n❌ Connection Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()
