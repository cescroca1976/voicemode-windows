from voice_mode.mcp_instance import mcp

@mcp.resource("voice://config/all")
async def all_configuration():
    return "Full configuration"
