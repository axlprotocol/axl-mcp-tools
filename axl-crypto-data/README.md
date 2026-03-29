# axl-crypto-data

MCP tool server for crypto market data in AXL packet format. Provides real-time price, funding rate, and market summary data from Binance, plus agent search via Machinedex and bridge posting.

## Tools

- **tool_get_price** - Fetch 24hr ticker for a symbol (price, volume, change)
- **tool_get_funding** - Fetch latest funding rate for a symbol
- **tool_get_market_summary** - Batch price fetch for multiple symbols
- **tool_search_agents** - Search Machinedex for agents by capability
- **tool_post_to_bridge** - Post an AXL packet to the bridge bus

## Install

```bash
pip install -e .
```

## Run standalone

```bash
python -m axl_crypto_data
```

## Claude Desktop config

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "axl-crypto-data": {
      "command": "python",
      "args": ["-m", "axl_crypto_data"],
      "cwd": "/home/cdev/axl-mcp-tools/axl-crypto-data"
    }
  }
}
```

## AXL Packet Format

All responses use the AXL wire format:

```
ID:AXL-CRYPTO|OBS.99|$SYMBOL|^value|^metadata|NOW
```

## License

Apache 2.0
