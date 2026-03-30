from mcp.server.fastmcp import FastMCP
import httpx
import json

mcp = FastMCP("axl-directory")

BRIDGE_URL = "https://bridge.axlprotocol.org"
MACHINEDEX_URL = "https://machinedex.io"


@mcp.tool()
async def search_agents(capability: str) -> str:
    """Search machinedex.io for agents by capability."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{MACHINEDEX_URL}/api/v1/search", params={"capability": capability})
            data = r.json()
            agents = data.get("agents", [])
            if not agents:
                return f"ID:AXL-DIR|OBS.50|@machinedex|~no_results|^q:{capability}|NOW"
            lines = []
            for a in agents[:10]:
                name = a.get("name", "unknown")
                cap = a.get("capabilities", "")
                lines.append(f"ID:AXL-DIR|OBS.90|@{name}|^cap:{cap}|NOW")
            return "\n".join(lines)
        except Exception as e:
            return f"ID:AXL-DIR|OBS.30|@machinedex|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def get_agent_profile(agent_id: str) -> str:
    """Get detailed profile for a specific agent from machinedex.io."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{MACHINEDEX_URL}/api/v1/agent/{agent_id}")
            data = r.json()
            name = data.get("name", agent_id)
            cap = data.get("capabilities", "")
            status = data.get("status", "unknown")
            return f"ID:AXL-DIR|OBS.95|@{name}|^status:{status}+^cap:{cap}|NOW"
        except Exception as e:
            return f"ID:AXL-DIR|OBS.30|@{agent_id}|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def register_agent(name: str, capabilities: str, endpoint: str = "") -> str:
    """Register a new agent on machinedex.io."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            payload = {"name": name, "capabilities": capabilities}
            if endpoint:
                payload["endpoint"] = endpoint
            r = await client.post(f"{MACHINEDEX_URL}/api/v1/agent/register", json=payload)
            data = r.json()
            agent_id = data.get("agent_id", data.get("id", "pending"))
            return f"ID:AXL-DIR|OBS.99|@{name}|^registered:true+^id:{agent_id}+^cap:{capabilities}|NOW"
        except Exception as e:
            return f"ID:AXL-DIR|OBS.30|@{name}|~register_failed:{str(e)[:80]}|NOW"


@mcp.tool()
async def list_capabilities() -> str:
    """List all known capabilities from machinedex.io."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{MACHINEDEX_URL}/api/v1/capabilities")
            data = r.json()
            caps = data.get("capabilities", [])
            if not caps:
                return f"ID:AXL-DIR|OBS.50|@machinedex|~no_capabilities_listed|NOW"
            lines = []
            for c in caps[:20]:
                name = c if isinstance(c, str) else c.get("name", "?")
                lines.append(f"ID:AXL-DIR|OBS.90|#capability|^name:{name}|NOW")
            return "\n".join(lines)
        except Exception as e:
            return f"ID:AXL-DIR|OBS.30|@machinedex|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def get_stats() -> str:
    """Get machinedex.io registry statistics."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{MACHINEDEX_URL}/api/v1/stats")
            data = r.json()
            agents = data.get("agents_indexed", data.get("total", 0))
            return f"ID:AXL-DIR|OBS.95|@machinedex|^agents_indexed:{agents}|NOW"
        except Exception as e:
            return f"ID:AXL-DIR|OBS.30|@machinedex|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def get_trending() -> str:
    """Get trending/top agents from machinedex.io."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{MACHINEDEX_URL}/api/v1/trending")
            data = r.json()
            agents = data.get("agents", data.get("trending", []))
            if not agents:
                return f"ID:AXL-DIR|OBS.50|@machinedex|~no_trending|NOW"
            lines = []
            for a in agents[:10]:
                name = a.get("name", "unknown")
                citations = a.get("citations", 0)
                lines.append(f"ID:AXL-DIR|OBS.90|@{name}|^citations:{citations}|NOW")
            return "\n".join(lines)
        except Exception as e:
            return f"ID:AXL-DIR|OBS.30|@machinedex|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def post_to_bridge(topic: str, packet: str) -> str:
    """Post an AXL packet to the bridge."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.post(f"{BRIDGE_URL}/v1/bus/{topic}", json={"packet": packet})
            data = r.json()
            return f"ID:AXL-DIR|OBS.99|@bridge|^posted:true+^mid:{data.get('mid','?')}|NOW"
        except Exception as e:
            return f"ID:AXL-DIR|OBS.30|@bridge|~error:{str(e)[:80]}|NOW"


def main():
    mcp.run(transport="stdio")
