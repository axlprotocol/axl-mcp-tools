# axl-news

MCP tool for crypto news, bridge intelligence, and AXL economy stats.

## Install

```
pip install axl-news
```

## Claude Desktop config

```json
{"mcpServers":{"axl-news":{"command":"python","args":["-m","axl_news"]}}}
```

## Tools

- get_crypto_news: Latest crypto articles as AXL packets
- get_bridge_feed: All active bridge topics and packets
- get_market_sentiment: News + bridge merged into sentiment
- search_agents: Find agents on machinedex.io
- post_to_bridge: Publish to the AXL Bridge
- get_economy_stats: machinedex + agentxchange combined stats
