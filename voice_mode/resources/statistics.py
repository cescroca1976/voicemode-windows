from voice_mode.mcp_instance import mcp

@mcp.resource("voice://statistics/{type}")
async def current_statistics(type="current"):
    return "Current statistics"
