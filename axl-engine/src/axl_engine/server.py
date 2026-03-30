from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("axl-engine")

BRIDGE_URL = "https://bridge.axlprotocol.org"
AGENTXCHANGE_URL = "https://agentxchange.io"


@mcp.tool()
async def create_task(capability: str, description: str, budget_usdc: float = 5.0) -> str:
    """Create a new task on agentxchange.io. Hire an agent."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            payload = {
                "capability": capability,
                "description": description,
                "budget": budget_usdc,
                "currency": "USDC"
            }
            r = await client.post(f"{AGENTXCHANGE_URL}/api/v1/task/create", json=payload)
            data = r.json()
            task_id = data.get("task_id", data.get("id", "pending"))
            return f"ID:AXL-ENGINE|OBS.95|!task_created|^id:{task_id}+^cap:{capability}+^budget:{budget_usdc}USDC|NOW"
        except Exception as e:
            return f"ID:AXL-ENGINE|OBS.30|!task_create|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def claim_task(task_id: str, agent_id: str = "mcp-agent") -> str:
    """Claim an open task on agentxchange.io."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            payload = {"agent_id": agent_id}
            r = await client.post(f"{AGENTXCHANGE_URL}/api/v1/task/{task_id}/claim", json=payload)
            data = r.json()
            status = data.get("status", "claimed")
            return f"ID:AXL-ENGINE|OBS.95|!task_claimed|^id:{task_id}+^agent:{agent_id}+^status:{status}|NOW"
        except Exception as e:
            return f"ID:AXL-ENGINE|OBS.30|!task_claim|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def deliver_task(task_id: str, delivery: str) -> str:
    """Submit delivery for a claimed task."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            payload = {"delivery": delivery}
            r = await client.post(f"{AGENTXCHANGE_URL}/api/v1/task/{task_id}/deliver", json=payload)
            data = r.json()
            status = data.get("status", "delivered")
            return f"ID:AXL-ENGINE|OBS.95|!task_delivered|^id:{task_id}+^status:{status}|NOW"
        except Exception as e:
            return f"ID:AXL-ENGINE|OBS.30|!task_deliver|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def verify_task(task_id: str, approved: bool = True) -> str:
    """Verify (approve or reject) a delivered task. Releases payment if approved."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            payload = {"approved": approved}
            r = await client.post(f"{AGENTXCHANGE_URL}/api/v1/task/{task_id}/verify", json=payload)
            data = r.json()
            status = data.get("status", "verified" if approved else "rejected")
            return f"ID:AXL-ENGINE|OBS.95|!task_verified|^id:{task_id}+^approved:{approved}+^status:{status}|NOW"
        except Exception as e:
            return f"ID:AXL-ENGINE|OBS.30|!task_verify|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def get_task(task_id: str) -> str:
    """Get details of a specific task."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{AGENTXCHANGE_URL}/api/v1/task/{task_id}")
            data = r.json()
            status = data.get("status", "unknown")
            cap = data.get("capability", "?")
            budget = data.get("budget", "?")
            return f"ID:AXL-ENGINE|OBS.90|!task|^id:{task_id}+^status:{status}+^cap:{cap}+^budget:{budget}|NOW"
        except Exception as e:
            return f"ID:AXL-ENGINE|OBS.30|!task|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def list_available_tasks(capability: str = "") -> str:
    """List open tasks available for claiming."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            params = {"status": "open"}
            if capability:
                params["capability"] = capability
            r = await client.get(f"{AGENTXCHANGE_URL}/api/v1/tasks", params=params)
            data = r.json()
            tasks = data.get("tasks", [])
            if not tasks:
                return "ID:AXL-ENGINE|OBS.50|@agentxchange|~no_open_tasks|NOW"
            lines = []
            for t in tasks[:10]:
                tid = t.get("id", "?")
                cap = t.get("capability", "?")
                budget = t.get("budget", "?")
                lines.append(f"ID:AXL-ENGINE|OBS.90|!task_open|^id:{tid}+^cap:{cap}+^budget:{budget}|NOW")
            return "\n".join(lines)
        except Exception as e:
            return f"ID:AXL-ENGINE|OBS.30|@agentxchange|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def get_founding_status() -> str:
    """Check founding agent program status and commission rates."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{AGENTXCHANGE_URL}/api/v1/founding")
            data = r.json()
            slots = data.get("slots_remaining", "?")
            rate = data.get("commission_rate", "8%")
            return f"ID:AXL-ENGINE|OBS.90|@agentxchange|^founding_slots:{slots}+^commission:{rate}|NOW"
        except Exception as e:
            return f"ID:AXL-ENGINE|OBS.30|@agentxchange|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def post_to_bridge(topic: str, packet: str) -> str:
    """Post an AXL packet to the bridge."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.post(f"{BRIDGE_URL}/v1/bus/{topic}", json={"packet": packet})
            data = r.json()
            return f"ID:AXL-ENGINE|OBS.99|@bridge|^posted:true+^mid:{data.get('mid','?')}|NOW"
        except Exception as e:
            return f"ID:AXL-ENGINE|OBS.30|@bridge|~error:{str(e)[:80]}|NOW"


def main():
    mcp.run(transport="stdio")
