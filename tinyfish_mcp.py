import os
import json
import requests

def search_with_tinyfish_mcp(query: str) -> str:
    """
    Connects to TinyFish via stateless HTTP MCP transport (JSON-RPC).
    """
    api_key = os.getenv("TINYFISH_API_KEY", "")
    if not api_key:
        return json.dumps([{"title": "Error", "body": "TinyFish API Key is missing."}])
        
    mcp_url = "https://agent.tinyfish.ai/mcp"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # 1. Initialize MCP connection
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "gid-bot", "version": "1.0"}
            }
        }
        r_init = requests.post(mcp_url, headers=headers, json=init_payload, timeout=10)
        if r_init.status_code != 200:
            return json.dumps([{"title": "TinyFish Error", "body": f"Failed to initialize: {r_init.status_code}"}])
            
        # Extract Session ID to keep the stateless HTTP context
        session_id = r_init.headers.get("mcp-session-id")
        if session_id:
            headers["Mcp-Session-Id"] = session_id
            
        # 2. Automatically notify initialized (MCP spec)
        requests.post(mcp_url, headers=headers, json={"jsonrpc": "2.0", "method": "notifications/initialized"}, timeout=5)

        # 3. Call the actual TinyFish Search Tool
        tool_payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "mcp__tinyfish__search",
                "arguments": {"query": query}
            }
        }
        r_tool = requests.post(mcp_url, headers=headers, json=tool_payload, timeout=30)
        if r_tool.status_code == 200:
            result_data = r_tool.json()
            if "result" in result_data and "content" in result_data["result"]:
                # Extract text content from MCP array
                content = result_data["result"]["content"]
                text_results = [item["text"] for item in content if item.get("type") == "text"]
                combined_text = "\n".join(text_results)
                return json.dumps([{"title": "TinyFish Live Search", "body": combined_text}])
            else:
                return json.dumps([{"title": "TinyFish Agent", "body": "Search executed but returned no content."}])
        else:
            return json.dumps([{"title": "TinyFish Error", "body": f"Tool call failed: {r_tool.status_code}"}])

    except Exception as e:
        return json.dumps([{"title": "TinyFish MCP Error", "body": f"Failed to execute: {str(e)}"}])
