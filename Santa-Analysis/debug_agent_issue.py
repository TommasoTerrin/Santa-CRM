import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Setup paths
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent))

# Load Env
load_dotenv(current_dir.parent / ".env")

try:
    from bot import is_dashboard_request
    print("✅ Successfully imported is_dashboard_request")
except ImportError as e:
    print(f"❌ Failed to import bot: {e}")
    sys.exit(1)

try:
    from agent import get_metabase_agent, ensure_metabase_connection
    print("✅ Successfully imported agent functions")
except ImportError as e:
    print(f"❌ Failed to import agent: {e}")
    sys.exit(1)

def test_trigger():
    print("\n🔍 Testing Trigger Logic...")
    test_queries = [
        "Creami report per vedere come cambia la quantità",
        "create dashboard",
        "Ciao come stai",
        "Dammi i bambini buoni"
    ]
    for q in test_queries:
        triggered = is_dashboard_request(q)
        print(f"  Query: '{q[:30]}...' -> Dashboard Request? {triggered}")

def test_connection_func():
    print("\n🔄 Testing ensure_metabase_connection()...")
    # We need to mock requests or just call it and see what happens
    # Since we are importing it from agent, we can't easily inject mocks without mocking sys.modules or using unittest.mock
    # But we can monkeypatch `requests.Session` if we firmly want to, or just call the function and debug the print output if we modify agent.py
    # Actually, let's just run it. The function in agent.py prints errors. 
    # To debug the "string indices" error, we should modify agent.py to print the response content on error, 
    # OR we can replicate the logic here to see what the API returns.
    
    # Replicating logic mainly to debug API response
    import requests
    import os
    
    username = os.getenv("METABASE_USERNAME", "")
    password = os.getenv("METABASE_PASSWORD", "")
    api_url = "http://localhost:3000/api"
    
    print(f"  Auth: {username} / {'*' * len(password) if password else 'EMPTY'}")
    
    try:
        session = requests.Session()
        res = session.post(f"{api_url}/session", json={"username": username, "password": password})
        print(f"  Login Status: {res.status_code}")
        if not res.ok:
            print(f"  Login Response: {res.text}")
            return
            
        token = res.json().get("id")
        headers = {"X-Metabase-Session": token}
        
        res = session.get(f"{api_url}/database", headers=headers)
        print(f"  List DB Status: {res.status_code}")
        try:
            data = res.json()
            print(f"  List DB Type: {type(data)}")
            print(f"  List DB Content (first 100 chars): {str(data)[:100]}")
        except Exception as e:
            print(f"  Failed to parse JSON: {e}")
            
    except Exception as e:
        print(f"  Error in manual test: {e}")
    
    # Also call the actual function
    print("  calling agent.ensure_metabase_connection()...")
    ensure_metabase_connection()

def test_get_agent():
    print("\n🤖 Testing get_metabase_agent()...")
    try:
        agent = get_metabase_agent()
        if agent:
            print(f"  ✅ Agent created successfully: {agent.name}")
        else:
            print("  ⚠️ Agent creation returned None")
    except Exception as e:
        print(f"  ❌ Error in get_metabase_agent: {e}")

if __name__ == "__main__":
    test_trigger()
    test_connection_func()
    test_get_agent()
