from mcp.server.fastmcp import FastMCP
import httpx
import json

mcp = FastMCP("axl-research")

BRIDGE_URL = "https://bridge.axlprotocol.org"
MACHINEDEX_URL = "https://machinedex.io"
AGENTXCHANGE_URL = "https://agentxchange.io"


@mcp.tool()
async def search_agents(capability: str) -> str:
    """Search for agents on machinedex.io by capability."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(
                f"{MACHINEDEX_URL}/api/v1/search",
                params={"capability": capability},
            )
            data = r.json()
            agents = data.get("agents", [])
            if not agents:
                return f"ID:AXL-RESEARCH|OBS.50|@machinedex|~no_agents_found|^capability:{capability}|NOW"
            lines = []
            for a in agents[:10]:
                name = a.get("name", "unknown")
                cap = a.get("capabilities", "")
                lines.append(f"ID:AXL-RESEARCH|OBS.90|@{name}|^cap:{cap}|NOW")
            return "\n".join(lines)
        except Exception as e:
            return f"ID:AXL-RESEARCH|OBS.30|@machinedex|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def hire_researcher(
    topic: str, budget_usdc: float = 5.0, description: str = ""
) -> str:
    """Create a research task on agentxchange.io. Hire an agent researcher."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            payload = {
                "capability": "research",
                "topic": topic,
                "budget": budget_usdc,
                "currency": "USDC",
                "description": description or f"Research task: {topic}",
            }
            r = await client.post(
                f"{AGENTXCHANGE_URL}/api/v1/task/create", json=payload
            )
            data = r.json()
            task_id = data.get("task_id", "pending")
            return f"ID:AXL-RESEARCH|OBS.95|!task_created|^id:{task_id}+^topic:{topic}+^budget:{budget_usdc}USDC|NOW"
        except Exception as e:
            return f"ID:AXL-RESEARCH|OBS.30|!task_create_failed|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def check_task(task_id: str) -> str:
    """Check the status of a task on agentxchange.io."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{AGENTXCHANGE_URL}/api/v1/task/{task_id}")
            data = r.json()
            status = data.get("status", "unknown")
            return f"ID:AXL-RESEARCH|OBS.90|!task_status|^id:{task_id}+^status:{status}|NOW"
        except Exception as e:
            return f"ID:AXL-RESEARCH|OBS.30|!task_check_failed|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def get_bridge_perspectives(topic: str) -> str:
    """Read recent perspectives from the AXL Bridge on a topic."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{BRIDGE_URL}/v1/bus/{topic}")
            data = r.json()
            perspectives = data.get("perspectives", [])
            if not perspectives:
                return f"ID:AXL-RESEARCH|OBS.50|@bridge|~no_perspectives|^topic:{topic}|NOW"
            lines = []
            for p in perspectives[:20]:
                lines.append(p.get("packet", ""))
            return (
                "\n".join(lines)
                if lines
                else f"ID:AXL-RESEARCH|OBS.50|@bridge|~empty|^topic:{topic}|NOW"
            )
        except Exception as e:
            return f"ID:AXL-RESEARCH|OBS.30|@bridge|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def post_to_bridge(topic: str, packet: str) -> str:
    """Post an AXL packet to the bridge."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.post(
                f"{BRIDGE_URL}/v1/bus/{topic}", json={"packet": packet}
            )
            data = r.json()
            mid = data.get("mid", "unknown")
            return f"ID:AXL-RESEARCH|OBS.99|@bridge|^posted:true+^mid:{mid}+^topic:{topic}|NOW"
        except Exception as e:
            return f"ID:AXL-RESEARCH|OBS.30|@bridge|~post_failed:{str(e)[:80]}|NOW"


@mcp.tool()
async def get_available_tasks(capability: str = "research") -> str:
    """List available tasks on agentxchange.io that match a capability."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(
                f"{AGENTXCHANGE_URL}/api/v1/tasks",
                params={"capability": capability, "status": "open"},
            )
            data = r.json()
            tasks = data.get("tasks", [])
            if not tasks:
                return f"ID:AXL-RESEARCH|OBS.50|@agentxchange|~no_tasks|^capability:{capability}|NOW"
            lines = []
            for t in tasks[:10]:
                tid = t.get("id", "?")
                topic = t.get("topic", "?")
                budget = t.get("budget", "?")
                lines.append(
                    f"ID:AXL-RESEARCH|OBS.90|!task_available|^id:{tid}+^topic:{topic}+^budget:{budget}|NOW"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"ID:AXL-RESEARCH|OBS.30|@agentxchange|~error:{str(e)[:80]}|NOW"


def main():
    mcp.run(transport="stdio")
