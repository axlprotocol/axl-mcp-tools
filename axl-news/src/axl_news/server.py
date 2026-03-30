from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("axl-news")

BRIDGE_URL = "https://bridge.axlprotocol.org"
MACHINEDEX_URL = "https://machinedex.io"
AGENTXCHANGE_URL = "https://agentxchange.io"


@mcp.tool()
async def get_crypto_news(symbol: str = "BTC") -> str:
    """Get latest crypto news from CryptoCompare API as AXL packets."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(
                "https://min-api.cryptocompare.com/data/v2/news/",
                params={"categories": symbol, "lang": "EN"},
            )
            data = r.json()
            raw = data.get("Data", [])
            articles = list(raw)[:5] if isinstance(raw, list) else []
            if not articles:
                return f"ID:AXL-NEWS|OBS.50|!news|~no_articles|^symbol:{symbol}|NOW"
            lines = []
            for a in articles:
                title = a.get("title", "")[:80]
                source = a.get("source", "unknown")
                lines.append(
                    f"ID:AXL-NEWS|OBS.85|!news|^src:{source}+^title:{title}|NOW"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"ID:AXL-NEWS|OBS.30|!news|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def get_bridge_feed(limit: int = 20) -> str:
    """Get all active topics and recent packets from the AXL Bridge."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{BRIDGE_URL}/v1/topics")
            data = r.json()
            topics = data.get("active_topics", [])
            if not topics:
                return "ID:AXL-NEWS|OBS.50|@bridge|~no_active_topics|NOW"
            lines = []
            for t in topics[:10]:
                name = t.get("topic", "?")
                count = t.get("packets", 0)
                ago = t.get("last_activity_seconds_ago", 0)
                lines.append(
                    f"ID:AXL-NEWS|OBS.90|@bridge|^topic:{name}+^packets:{count}+^age:{ago}s|NOW"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"ID:AXL-NEWS|OBS.30|@bridge|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def get_market_sentiment(symbol: str = "BTC") -> str:
    """Merge crypto news + bridge perspectives into a sentiment summary."""
    news = await get_crypto_news(symbol)
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{BRIDGE_URL}/v1/bus/${symbol}")
            bridge_data = r.json()
            perspectives = bridge_data.get("perspectives", [])
            bridge_count = len(perspectives)
        except Exception:
            bridge_count = 0
    news_count = news.count("OBS.85")
    return f"ID:AXL-NEWS|MRG.75|${symbol}|^news_articles:{news_count}+^bridge_packets:{bridge_count}|NOW\n{news}"


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
                return f"ID:AXL-NEWS|OBS.50|@machinedex|~no_agents|^capability:{capability}|NOW"
            lines = []
            for a in agents[:10]:
                name = a.get("name", "unknown")
                lines.append(
                    f"ID:AXL-NEWS|OBS.90|@{name}|^cap:{a.get('capabilities', '')}|NOW"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"ID:AXL-NEWS|OBS.30|@machinedex|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def post_to_bridge(topic: str, packet: str) -> str:
    """Post an AXL packet to the bridge."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.post(
                f"{BRIDGE_URL}/v1/bus/{topic}", json={"packet": packet}
            )
            data = r.json()
            return f"ID:AXL-NEWS|OBS.99|@bridge|^posted:true+^mid:{data.get('mid', '?')}|NOW"
        except Exception as e:
            return f"ID:AXL-NEWS|OBS.30|@bridge|~error:{str(e)[:80]}|NOW"


@mcp.tool()
async def get_economy_stats() -> str:
    """Get combined stats from machinedex.io and agentxchange.io."""
    async with httpx.AsyncClient(timeout=10) as client:
        lines = []
        try:
            r = await client.get(f"{MACHINEDEX_URL}/api/v1/stats")
            md = r.json()
            agents = md.get("agents_indexed", md.get("total", 0))
            lines.append(
                f"ID:AXL-NEWS|OBS.90|@machinedex|^agents_indexed:{agents}|NOW"
            )
        except Exception as e:
            lines.append(
                f"ID:AXL-NEWS|OBS.30|@machinedex|~error:{str(e)[:60]}|NOW"
            )
        try:
            r = await client.get(f"{AGENTXCHANGE_URL}/api/v1/stats")
            ax = r.json()
            tasks = ax.get("tasks_completed", ax.get("total", 0))
            vol = ax.get("volume_usdc", ax.get("volume", 0))
            lines.append(
                f"ID:AXL-NEWS|OBS.90|@agentxchange|^tasks:{tasks}+^volume:{vol}USDC|NOW"
            )
        except Exception as e:
            lines.append(
                f"ID:AXL-NEWS|OBS.30|@agentxchange|~error:{str(e)[:60]}|NOW"
            )
        return "\n".join(lines)


def main():
    mcp.run(transport="stdio")
