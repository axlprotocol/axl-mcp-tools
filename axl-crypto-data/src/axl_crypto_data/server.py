import httpx
from mcp.server.fastmcp import FastMCP

mcp_server = FastMCP("axl-crypto-data")


async def get_price(symbol: str) -> str:
    """Fetch 24hr ticker price for a crypto symbol from Binance."""
    sym = symbol.upper().strip()
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}USDT"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    price = data.get("lastPrice", "N/A")
    volume = data.get("volume", "N/A")
    change = data.get("priceChangePercent", "N/A")
    return f"ID:AXL-CRYPTO|OBS.99|${sym}|^{price}|^vol:{volume}+^change:{change}%|NOW"


async def get_funding(symbol: str) -> str:
    """Fetch latest funding rate for a crypto symbol from Binance Futures."""
    sym = symbol.upper().strip()
    url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={sym}USDT&limit=1"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    if not data:
        return f"ID:AXL-CRYPTO|OBS.99|${sym}|^fund:N/A|^next:N/A|NOW"
    entry = data[0]
    rate = entry.get("fundingRate", "N/A")
    next_time = entry.get("fundingTime", "N/A")
    return f"ID:AXL-CRYPTO|OBS.99|${sym}|^fund:{rate}|^next:{next_time}|NOW"


async def get_market_summary(symbols: str) -> str:
    """Fetch price data for multiple symbols (comma separated) and return a bundle."""
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    lines = []
    for sym in sym_list:
        try:
            line = await get_price(sym)
            lines.append(line)
        except Exception as exc:
            lines.append(f"ID:AXL-CRYPTO|OBS.99|${sym}|^ERROR:{exc}|NOW")
    summary = ", ".join(sym_list)
    lines.append(f"ID:AXL-CRYPTO|MRG.00|SUMMARY|^symbols:{summary}|^count:{len(sym_list)}|NOW")
    return "\n".join(lines)


async def search_agents(capability: str) -> str:
    """Search for agents on Machinedex by capability."""
    url = f"https://machinedex.io/api/v1/search?capability={capability}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
        if not data:
            return f"ID:AXL-CRYPTO|OBS.99|AGENTS|^capability:{capability}|^found:0|NOW"
        lines = []
        agents = data if isinstance(data, list) else data.get("agents", data.get("results", []))
        for agent in agents:
            name = agent.get("name", "unknown")
            aid = agent.get("id", "unknown")
            lines.append(f"ID:AXL-CRYPTO|OBS.99|AGENT:{name}|^id:{aid}|^cap:{capability}|NOW")
        return "\n".join(lines) if lines else f"ID:AXL-CRYPTO|OBS.99|AGENTS|^capability:{capability}|^found:0|NOW"
    except Exception as exc:
        return f"ID:AXL-CRYPTO|OBS.99|AGENTS|^capability:{capability}|^status:machinedex unavailable, {exc}|NOW"


async def post_to_bridge(topic: str, packet: str) -> str:
    """Post an AXL packet to the bridge bus on a given topic."""
    url = f"https://bridge.axlprotocol.org/v1/bus/{topic}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json={"packet": packet})
            resp.raise_for_status()
            return f"ID:AXL-CRYPTO|ACK|BRIDGE|^topic:{topic}|^status:{resp.status_code}|^body:{resp.text}|NOW"
    except Exception as exc:
        return f"ID:AXL-CRYPTO|ACK|BRIDGE|^topic:{topic}|^status:error, {exc}|NOW"


@mcp_server.tool()
async def tool_get_price(symbol: str) -> str:
    """Fetch 24hr ticker price for a crypto symbol. Returns an AXL OBS packet with price, volume, and change."""
    return await get_price(symbol)


@mcp_server.tool()
async def tool_get_funding(symbol: str) -> str:
    """Fetch latest funding rate for a crypto symbol. Returns an AXL OBS packet with funding rate and next funding time."""
    return await get_funding(symbol)


@mcp_server.tool()
async def tool_get_market_summary(symbols: str) -> str:
    """Fetch price data for multiple symbols (comma separated like BTC,ETH,SOL). Returns bundled AXL OBS packets plus a MRG summary."""
    return await get_market_summary(symbols)


@mcp_server.tool()
async def tool_search_agents(capability: str) -> str:
    """Search for agents on Machinedex by capability. Returns AXL OBS packets for each agent found."""
    return await search_agents(capability)


@mcp_server.tool()
async def tool_post_to_bridge(topic: str, packet: str) -> str:
    """Post an AXL packet to the bridge bus on a given topic. Returns an ACK packet with the bridge response."""
    return await post_to_bridge(topic, packet)


def main():
    mcp_server.run()
