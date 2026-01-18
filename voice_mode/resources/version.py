from voice_mode.mcp_instance import mcp

@mcp.resource("voice-mode:version")
async def get_version_info():
    return "Version info"
